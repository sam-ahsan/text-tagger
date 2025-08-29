import json

from typing import Optional, Dict, Any, List
from app.core.redis_client import get_redis
from app.schemas.auth import User
from app.core.security import hash_password, verify_password

def _user_key(username: str) -> str:
    return f"user:{username.lower()}"

def create_user(
    username: str, password: str, tenant_id: Optional[str] = None, roles: Optional[List[str]] = None
) -> User:
    redis = get_redis()
    key = _user_key(username)
    if redis.exists(key):
        raise ValueError("user_exists")
    doc = {
        "password_hash": hash_password(password),
        "tenant_id": tenant_id or "",
        "disabled": "0",
        "roles": json.dumps(roles or [])
    }
    redis.hset(key, mapping=doc)
    return User(username=username, tenant_id=tenant_id, disabled=False, roles=roles or [])

def get_user(username: str) -> Optional[User]:
    redis = get_redis()
    data = redis.hgetall(_user_key(username))
    if not data:
        return None
    roles = json.loads(data.get("roles") or "[]")
    disabled = data.get("disabled") == "1"
    tenant_id = data.get("tenant_id") or None
    return User(username=username, tenant_id=tenant_id, disabled=disabled, roles=roles)

def authenticate_user(username: str, password: str) -> Optional[User]:
    redis = get_redis()
    data = redis.hgetall(_user_key(username))
    if not data:
        return None
    if not verify_password(password, data.get("password_hash", "")):
        return None
    roles = json.loads(data.get("roles") or "[]")
    disabled = data.get("disabled") == "1"
    tenant_id = data.get("tenant_id") or None
    return User(username=username, tenant_id=tenant_id, disabled=disabled, roles=roles)
