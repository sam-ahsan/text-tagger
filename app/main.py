import time
import uuid
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.api.v1 import tag
from app.core.redis_client import get_redis
from app.workers.celery_app import celery_app

logger = logging.getLogger("text-tagger")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan():
    logger.info("api_startup begin")
    
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
    description="AI-powered text tagging API"
)

app.include_router(tag.router, prefix="/v1", tags=["tagging"])

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

@app.get("/healthz")
def health_check():
    return {
        "status": "ok"
    }
