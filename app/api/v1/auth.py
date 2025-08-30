from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.core.users import authenticate_user, create_user
from app.schemas.auth import Token, User, UserCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")

@router.post("/signup", response_model=User, status_code=201)
def signup(payload: UserCreate):
    try:
        return create_user(payload.username, payload.password, tenant_id=payload.tenant_id)
    except ValueError as e:
        if str(e) == "user_exists":
            raise HTTPException(status_code=409, detail="Username already exists")
        raise

@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    extra = {"tenant_id": user.tenant_id or "", "roles": user.roles}
    token = create_access_token(subject=user.username, extra=extra)
    return Token(access_token=token)
