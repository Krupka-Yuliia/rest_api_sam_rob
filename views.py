from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth.auth import get_current_user
from models import BookModel
from schemas import Book, BookCreate
from fastapi.security import OAuth2PasswordBearer
from fastapi import Request
from ratelimiter import rate_limit

main = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_book_by_id(book_id: int, db: Session):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")
    return book


@main.get("/")
async def root(request: Request):
    await rate_limit(request, user_id=None)
    return {"message": "Main page of API"}


@main.get("/books", response_model=list[Book])
async def get_books(
        request: Request,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    await rate_limit(request, user_id=current_user.id)
    books = db.query(BookModel).all()
    return books


@main.post("/books", response_model=Book, status_code=201)
async def create_book(
        request: Request,
        book: BookCreate,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    await rate_limit(request, user_id=current_user.id)
    new_book = BookModel(**book.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@main.get("/books/{book_id}", response_model=Book)
async def get_book(
        request: Request,
        book_id: int,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    await rate_limit(request, user_id=current_user.id)
    return get_book_by_id(book_id, db)


@main.delete("/books/{book_id}", status_code=204)
async def delete_book(
        request: Request,
        book_id: int,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    await rate_limit(request, user_id=current_user.id)
    book = get_book_by_id(book_id, db)
    db.delete(book)
    db.commit()
    return {}
