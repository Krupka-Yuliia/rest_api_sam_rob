from datetime import datetime, timedelta, UTC

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from database import get_db
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/api/auth/login")

SECRET_KEY = "secret"
REFRESH_SECRET_KEY = "refresh_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRE_DAYS = timedelta(days=7)


def create_access_token(data: dict):
    token_data = data.copy()
    expire_time = datetime.now(UTC) + ACCESS_TOKEN_EXPIRE_MINUTES
    token_data.update({"exp": expire_time})
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    token_data = data.copy()
    expire_time = datetime.now(UTC) + REFRESH_TOKEN_EXPIRE_DAYS
    token_data.update({"exp": expire_time})
    return jwt.encode(token_data, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def create_http_exception(status_code: int, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": detail, "status_code": status_code},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username or datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp", 0), UTC):
            raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise create_http_exception(status.HTTP_404_NOT_FOUND, "User not found")

        return user
    except JWTError:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")
