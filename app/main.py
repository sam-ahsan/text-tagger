import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import REGISTRY
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from app.api.v1 import tag
from app.core.metrics import RedisCeleryCollector, _queue_len
from app.core.redis_client import get_redis
from app.workers.celery_app import celery_app

START_TS = time.time()
VERSION = os.getenv("VERSION", "0.1.0")

logger = logging.getLogger("text-tagger")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_startup begin")
    
    try:
        REGISTRY.register(RedisCeleryCollector())
    except ValueError:
        pass
    
    try:
        redis = get_redis()
        ok = redis.ping()
        logger.info(f"redis_ping ok={ok}")
    except Exception as e:
        logger.warning(f"redis_ping failed err={e}")
    
    try:
        replies = celery_app.control.ping(timeout=1)
        logger.info(f"celery_ping replies={replies}")
    except Exception as e:
        logger.warning(f"celery_ping failed err={e}")
    
    logger.info("api_startup ok")
    yield
    
    try:
        try:
            redis = get_redis()
            redis.close()
        except Exception:
            pass
        logger.info("api_shutdown ok")
    except Exception as e:
        logger.warning(f"api_shutdown error err={e}")

app = FastAPI(
    title="Text Tagger API",
    version="0.1.0",
    description="AI-powered text tagging API",
    lifespan=lifespan
)

app.include_router(tag.router, prefix="/v1", tags=["tagging"])

instr = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
)
instr.add(metrics.default())
instr.add(metrics.latency(buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2)))
if hasattr(metrics, "requests"):
    instr.add(metrics.requests())
if hasattr(metrics, "response_size"):
    instr.add(metrics.response_size())
if hasattr(metrics, "exceptions"):
    instr.add(metrics.exceptions())
instr.instrument(app).expose(app, endpoint="/metrics", tags=["ops"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    dur_ms = int((time.time() - start) * 1000)
    logger.info(
        f"rid={rid} method={request.method} path={request.url.path} status={response.status_code} duration={dur_ms}ms"
    )
    response.headers["x-request-id"] = rid
    return response

@app.get("/", tags=["root"])
def root():
    return {
        "message": "Welcome to the text-tagger-api. See /docs for API documentation."
    }

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return {
        "message": "This is the favicon endpoint."
    }

@app.get("/healthz", tags=["ops"])
def health_check():
    """
    Liveness: process is up and event loop is responsive.
    Redis ping is informational; failure does not flip to 503.
    """
    info = {
        "status": "up",
        "version": VERSION,
        "uptime_s": int(time.time() - START_TS),
        "redis": False
    }
    try:
        redis = get_redis()
        info["redis"] = bool(redis.ping())
    except Exception:
        pass
    
    if not info["redis"]:
        info["status"] = "degraded"
    return info

@app.get("/readyz", tags=["ops"])
def readiness_check():
    """
    Readiness = can this instance handle traffic right now?
    - Redis ping ok
    - Celery ping gets >= 1 reply
    - (Optional) Queue length not absurdly high
    """
    details = {"redis": False, "celery_replies": 0, "queue_length": None}
    ok = True
    
    # Redis ping
    try:
        redis = get_redis()
        details["redis"] = bool(redis.ping())
    except Exception as e:
        logger.warning(f"readyz: redis ping failed: {e}")
        ok = False
    
    # Celery ping
    try:
        replies = celery_app.control.ping(timeout=1) or []
        details["celery_replies"] = len(replies)
        if len(replies) == 0:
            ok = False
    except Exception as e:
        logger.warning(f"readyz: celery ping failed: {e}")
        ok = False
    
    # Queue length check
    try:
        queue_name = os.getenv("CELERY_TAGGING_QUEUE", "tagging")
        queue_len = _queue_len(get_redis(), queue_name)
        details["queue_length"] = queue_len
        if queue_len > 1000:
            ok = False
    except Exception as e:
        logger.warning(f"readyz: queue length check failed: {e}")
        ok = False
    
    if not ok:
        raise HTTPException(status_code=503, detail={"ready": False, **details})

    return {"ready": True, **details}
