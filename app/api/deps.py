import time

from fastapi import Depends, Response

from app.core.auth import AuthContext, require_api_key
from app.core.rate_limit import check_rate_limit


async def auth_and_rate_limit(resp: Response, ctx: AuthContext = Depends(require_api_key)) -> AuthContext:
    # Rate limit by API key
    remaining, reset, used = check_rate_limit(f"{ctx.api_key}")
    
    # Calculate seconds until reset
    now = int(time.time())
    seconds_until_reset = max(0, reset - now)
    
    resp.headers["X-RateLimit-Limit"] = str(used + remaining)
    resp.headers["X-RateLimit-Remaining"] = str(remaining)
    resp.headers["X-RateLimit-Reset"] = str(reset)
    resp.headers["X-RateLimit-Reset-After"] = str(seconds_until_reset)
    resp.headers["X-Tenant"] = ctx.tenant
    return ctx
