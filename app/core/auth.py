import os
from typing import Dict, Optional

from fastapi import Header, HTTPException, status


# Parse API_KEYS env into {key: tenant}
def _load_api_keys() -> Dict[str, str]:
    raw = os.getenv("API_KEYS", "")
    mapping: Dict[str, str] = {}
    for pair in filter(None, [p.strip() for p in raw.split(",")]):
        if ":" in pair:
            key, tenant = pair.split(":", 1)
            mapping[key.strip()] = tenant.strip()
        else:
            mapping[pair.strip()] = "default"
    return mapping

_API_KEYS = _load_api_keys()

class AuthContext:
    def __init__(self, api_key: str, tenant: str):
        self.api_key = api_key
        self.tenant = tenant

async def require_api_key(x_api_key: Optional[str] = Header(None)) -> AuthContext:
    if not _API_KEYS:
        return AuthContext(api_key="dev-open", tenant="dev")
    if not x_api_key or x_api_key not in _API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return AuthContext(api_key=x_api_key, tenant=_API_KEYS[x_api_key])
