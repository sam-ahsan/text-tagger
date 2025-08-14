import hashlib
import json
import logging
import os
import time
from typing import List, Optional

from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_postrun, task_prerun, worker_process_init, worker_shutdown

from app.core.hash import normalize_payload, payload_hash
from app.core.redis_client import get_redis
from app.services.tagging import TaggingService
from app.workers.celery_app import celery_app

task_logger = logging.getLogger("text-tagger.task")
_tagger = TaggingService()
_redis = get_redis()
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "600"))
MAX_RETRIES = int(os.getenv("CELERY_MAX_RETRIES", "2"))

# Redis metric keys
METR_KEY_TASKS_SUCCESS = "metrics:tasks_total:success"
METR_KEY_TASKS_FAILURE = "metrics:tasks_total:failure"
METR_KEY_TASKS_TIMEOUT = "metrics:tasks_total:timeout"
METR_KEY_CACHE_HIT = "metrics:cache_hits_total"

# Histogram keys (per Prometheus exposition)
HIST_PREFIX = "metrics:task_duration_ms"
HIST_BUCKETS_MS = [50, 100, 250, 500, 1000, 2000, 5000] # +Inf is implicit

def _hist_observe_ms(ms: int):
    """
    Record one observation into Redis-backed histogram.
    """
    pipe = _redis.pipeline()
    pipe.incrbyfloat(f"{HIST_PREFIX}:sum", float(ms))
    pipe.incr(f"{HIST_PREFIX}:count", 1)
    
    placed = False
    for bucket in HIST_BUCKETS_MS:
        if ms <= bucket:
            pipe.incr(f"{HIST_PREFIX}:bucket:le_{bucket}", 1)
            placed = True
            break
    if not placed:
        pipe.incr(f"{HIST_PREFIX}:bucket:le_inf", 1)
    try:
        pipe.execute()
    except Exception:
        pass

def _hash_kwargs(texts, language, domain_dict) -> str:
    body = {"texts": texts, "language": language, "domain_dict": domain_dict}
    s = json.dumps(body, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": MAX_RETRIES}
)
def tag_batch_task(
    self,
    texts: List[str],
    language: Optional[str] = None,
    domain_dict: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    cache_key: Optional[str] = None
):
    """
    Run TaggingService on a batch and return JSON-serializable payload shaped for TagResponse.
    """
    start = time.time()
    
    if not cache_key:
        cache_key = payload_hash(normalize_payload(texts=texts, language=language, domain_dict=domain_dict))

    result_key = f"tagresp:{cache_key}"
    inflight_key = f"inflight:{cache_key}"
    
    # Cache read-through: return cached result if exists
    cached = _redis.get(result_key)
    if cached:
        _redis.incr(METR_KEY_CACHE_HIT, 1)
        dur_ms = int((time.time() - start) * 1000)
        _hist_observe_ms(dur_ms)
        return json.loads(cached)
    
    try:
        results = _tagger.tag_texts(
            texts=texts,
            language=language,
            domain_dict=domain_dict
        )
        payload = {"results": [result.model_dump() for result in results]}
        
        _redis.setex(result_key, CACHE_TTL, json.dumps(payload, ensure_ascii=False))
        _redis.setex(inflight_key, CACHE_TTL, self.request.id)
        _redis.incr(METR_KEY_TASKS_SUCCESS, 1)
        
        dur_ms = int((time.time() - start) * 1000)
        _hist_observe_ms(dur_ms)

        task_logger.info(
            f"job_id={self.request.id} request_id={request_id} batch_size={len(texts)} " \
            f"duration_ms={dur_ms} cached={bool(cached)}"
        )
        return payload
    
    except SoftTimeLimitExceeded:
        err = {"error": {"code": "TIMEOUT", "message": "Tagging timed out"}}
        _redis.setex(result_key, CACHE_TTL, json.dumps(err))
        _redis.incr(METR_KEY_TASKS_TIMEOUT, 1)
        
        dur_ms = int((time.time() - start) * 1000)
        _hist_observe_ms(dur_ms)
        
        task_logger.info(
            f"job_id={self.request.id} request_id={request_id} batch_size={len(texts)} " \
            f"duration_ms={dur_ms} cached={bool(cached)}"
        )
        return err

@task_prerun.connect
def _on_task_prerun(task_id, task, **kwargs):
    task_logger.info(f"task_prerun task={task.name} job_id={task_id}")

@task_postrun.connect
def _on_task_postrun(task_id, task, retval, state, **kwargs):
    ok = state == "SUCCESS"
    if state == "FAILURE":
        try:
            _redis.incr(METR_KEY_TASKS_FAILURE, 1)
        except Exception:
            task_logger.warning("Failed to increment failure counter")
    task_logger.info(f"task_postrun task={task.name} job_id={task_id} state={state} ok={ok}")

@worker_process_init.connect
def _warmup_models(sender=None, **kwargs):
    try:
        _ = _tagger.tag_texts(["Warmup"], language="en")
        task_logger.info("worker_warmup ok")
    except Exception:
        task_logger.exception("worker_warmup_failed")

@worker_shutdown.connect
def _on_worker_shutdown(sender=None, **kwargs):
    sig = kwargs.get("sig")
    how = kwargs.get("how")
    exitcode = kwargs.get("exitcode")
    task_logger.info(f"worker_shutdown sender={sender} sig={sig} how={how} exitcode={exitcode}")
