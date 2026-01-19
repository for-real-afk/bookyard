"""User Rating database model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class UserRating(SQLModel, table=True):
    """User Rating model for database."""
    
    __tablename__ = "user_ratings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    rating: int = Field(ge=1, le=10)  # Rating scale 1-10
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)