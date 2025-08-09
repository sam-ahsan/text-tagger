from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult

from app.schemas.tag import (
    TagRequest,
    TagResponse,
    BatchSubmitResponse,
    BatchStatusResponse
)
from app.services.tagging import TaggingService
from app.services.tasks import tag_batch_task
from app.workers.celery_app import celery_app

router = APIRouter()
tagger = TaggingService()

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
def submit_batch(payload: TagRequest):
    if not payload.texts:
        raise HTTPException(status_code=400, detail="No input texts provided for batch tagging.")
    
    async_result = tag_batch_task.apply_async(kwargs=dict(
        texts=payload.texts,
        language=payload.language,
        domain_dict=payload.domain_dict
    ))
    return BatchSubmitResponse(job_id=async_result.id)

@router.get("/tag/batch/{job_id}", response_model=BatchStatusResponse)
def get_batch_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    state = result.state
    
    if state in ("PENDING", "STARTED", "RETRY"):
        return BatchStatusResponse(status=state)
    if state == "FAILURE":
        return BatchStatusResponse(status=state, error=str(result.info))
    
    payload = result.get(timeout=10)
    return BatchStatusResponse(status=state, result=TagResponse(**payload))
