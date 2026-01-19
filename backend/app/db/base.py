"""Database base - imports all models for migrations."""

from sqlmodel import SQLModel

from app.models.book import Book
from app.models.user_rating import UserRating

__all__ = ["SQLModel", "Book", "UserRating"]