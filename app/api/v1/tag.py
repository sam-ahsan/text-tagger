import hashlib
import json
import time
import os

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from celery.result import AsyncResult

from app.schemas.tag import (
    TagRequest,
    TagResponse,
    BatchSubmitResponse,
    BatchStatusResponse,
    ErrorInfo
)
from app.services.tagging import TaggingService
from app.services.tasks import tag_batch_task
from app.workers.celery_app import celery_app
from app.core.redis_client import get_redis
from app.core.hash import normalize_payload, payload_hash
from app.api.deps import auth_and_rate_limit, AuthContext

router = APIRouter(dependencies=[Depends(auth_and_rate_limit)])
tagger = TaggingService()
redis = get_redis()

@router.post("/tag", response_model=TagResponse)
def tag_text(payload: TagRequest):
    if not payload.texts:
        raise HTTPException(status_code=400, detail="No input texts provided for tagging.")
    
    results = tagger.tag_texts(
        texts=payload.texts,
        language=payload.language,
        domain_dict=payload.domain_dict
    )
    
    return TagResponse(results=results)

@router.post("/tag/batch", response_model=BatchSubmitResponse)
def submit_batch(payload: TagRequest, request: Request):
    if not payload.texts:
        raise HTTPException(status_code=400, detail="No input texts provided for batch tagging.")
    
    normalized = normalize_payload( # added this
        texts=payload.texts,
        language=payload.language,
        domain_dict=payload.domain_dict
    )
    cache_key = payload_hash(normalized)
    
    inflight_key = f"inflight:{cache_key}"
    ttl = int(os.getenv("CACHE_TTL_SECONDS", "600"))
    
    # Return existing job if it is already enqueued/processing
    existing = redis.get(inflight_key)
    if existing:
        state = AsyncResult(existing, app=celery_app).state
        if state in ("PENDING", "STARTED", "RETRY"):
            return BatchSubmitResponse(job_id=existing)
    
    request_id = request.headers.get("x-request-id") or str(os.urandom(8).hex())
    async_result = tag_batch_task.apply_async(
        kwargs=dict(
            texts=payload.texts,
            language=payload.language,
            domain_dict=payload.domain_dict,
            request_id=request_id,
            cache_key=cache_key
        ),
        queue=os.getenv("CELERY_TAGGING_QUEUE", "tagging")
    )
    
    # Mark in-flight mapping with a short TTL; refreshed by the task on success
    redis.setex(inflight_key, ttl, async_result.id)

    return BatchSubmitResponse(job_id=async_result.id)

@router.get("/tag/batch/{job_id}", response_model=BatchStatusResponse)
def get_batch_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    state = result.state
    
    if state in ("PENDING", "STARTED", "RETRY"):
        return BatchStatusResponse(status=state)
    if state == "FAILURE":
        return BatchStatusResponse(
            status=state,
            error=ErrorInfo(code="TASK_FAILURE", message=str(result.info))
        )
    
    payload = result.get(timeout=10)
    if "error" in payload:
        return BatchStatusResponse(
            status="FAILURE",
            error=ErrorInfo(**payload["error"])
        )
    return BatchStatusResponse(status=state, result=TagResponse(**payload))
