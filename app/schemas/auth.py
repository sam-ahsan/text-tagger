from typing import List, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    tenant_id: Optional[str] = None

class User(BaseModel):
    username: str
    tenant_id: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
