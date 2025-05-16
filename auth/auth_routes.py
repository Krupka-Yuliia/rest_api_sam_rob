from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError

from .auth import (
    REFRESH_SECRET_KEY,
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    create_http_exception,
)
from database import get_db
from models import User
from schemas import UserDTO, Token, UserCreate
from ratelimiter import rate_limit

auth = APIRouter(prefix="/v1/api/auth", tags=["authentication"])
password_hasher = CryptContext(schemes=["bcrypt"])


@auth.post("/register", response_model=UserDTO)
async def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    await rate_limit(request, user_id=None)

    if db.query(User).filter(User.username == user.username).first():
        raise create_http_exception(status.HTTP_400_BAD_REQUEST, "Username already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise create_http_exception(status.HTTP_400_BAD_REQUEST, "Email already exists")

    new_user = User(
        username=user.username,
        email=str(user.email),
        hashed_password=password_hasher.hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth.post("/login", response_model=Token)
async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    await rate_limit(request, user_id=None)

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not password_hasher.verify(form_data.password, user.hashed_password):
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")

    return {
        "access_token": create_access_token({"sub": user.username}),
        "refresh_token": create_refresh_token({"sub": user.username}),
        "token_type": "bearer"
    }


@auth.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
        request: Request,
        body: dict,
        db: Session = Depends(get_db)
):
    await rate_limit(request, user_id=None)

    token_str = body.get("refresh_token")
    if not token_str:
        raise create_http_exception(status.HTTP_422_UNPROCESSABLE_ENTITY, "refresh_token is required")

    try:
        payload = jwt.decode(token_str, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    except JWTError:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "User not found")

    return {
        "access_token": create_access_token({"sub": username}),
        "refresh_token": create_refresh_token({"sub": username}),
        "token_type": "bearer"
    }
