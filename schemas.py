from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class BookCreate(BaseModel):
    title: str = Field(max_length=200)
    author: str = Field(max_length=200)
    publisher: str = Field(max_length=200)
    year: int = Field(gt=1500, le=datetime.now().year)

    class Config:
        from_attributes = True


class Book(BookCreate):
    id: int

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserDTO(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None