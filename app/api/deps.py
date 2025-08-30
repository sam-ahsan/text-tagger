import time

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer

from app.core.auth import AuthContext
from app.core.rate_limit import check_rate_limit
from app.core.security import decode_token
from app.core.users import get_user
from app.schemas.auth import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise ValueError("no_sub")
        user = get_user(username)
        if not user or user.disabled:
            raise ValueError("user_invalid")
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

def get_auth_context(user: User = Depends(get_current_user)) -> AuthContext:
    """Convert User to AuthContext for backward compatibility with rate limiting"""
    return AuthContext(user_id=user.username, tenant=user.tenant_id or "default")

async def auth_and_rate_limit(resp: Response, ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    # Rate limit by user ID
    remaining, reset, used = check_rate_limit(f"user:{ctx.user_id}")
    
    # Calculate seconds until reset
    now = int(time.time())
    seconds_until_reset = max(0, reset - now)
    
    resp.headers["X-RateLimit-Limit"] = str(used + remaining)
    resp.headers["X-RateLimit-Remaining"] = str(remaining)
    resp.headers["X-RateLimit-Reset"] = str(reset)
    resp.headers["X-RateLimit-Reset-After"] = str(seconds_until_reset)
    resp.headers["X-Tenant"] = ctx.tenant
    return ctx

def require_role(role: str):
    def _inner(user: User = Depends(get_current_user)) -> User:
        if role not in (user.roles or []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _inner
