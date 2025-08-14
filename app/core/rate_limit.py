import os
import time
from typing import Tuple

from fastapi import HTTPException, status

from app.core.redis_client import get_redis

REQS = int(os.getenv("RATE_LIMIT_REQS", "60"))
WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

def _now_window() -> Tuple[int, int]:
    now = int(time.time())
    win_start = now - (now % WINDOW)
    return now, win_start

def check_rate_limit(key: str) -> Tuple[int, int, int]:
    """
    Increment counter for (key, current window). Return (remaining, reset_epoch, used).
    Raises HTTPException 429 if exceeded.
    """
    redis = get_redis()
    now, win_start = _now_window()
    rate_key = f"rate_limit:{key}:{win_start}"
    
    pipe = redis.pipeline()
    pipe.incr(rate_key, 1)
    pipe.expire(rate_key, WINDOW + 1)
    used, _ = pipe.execute()
    
    remaining = max(0, REQS - int(used))
    reset = win_start + WINDOW
    
    if used > REQS:
        # Calculate seconds until reset
        seconds_until_reset = max(0, reset - now)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(REQS),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset),
                "X-RateLimit-Reset-After": str(seconds_until_reset),
            }
        )
    return remaining, reset, int(used)
