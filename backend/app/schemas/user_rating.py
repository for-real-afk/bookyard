"""User Rating Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class UserRatingBase(BaseModel):
    """Base user rating schema."""
    book_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=10, description="Rating from 1 to 10")


class UserRatingCreate(UserRatingBase):
    """Schema for creating a user rating."""
    user_id: UUID


class UserRatingUpdate(BaseModel):
    """Schema for updating a user rating."""
    rating: int = Field(..., ge=1, le=10, description="Rating from 1 to 10")


class UserRatingResponse(UserRatingBase):
    """Schema for user rating response."""
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BookRecommendationRequest(BaseModel):
    """Schema for book recommendation request."""
    book_title: str = Field(..., min_length=1, description="Book title to base recommendations on")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of recommendations to return")


class BookRecommendationResponse(BaseModel):
    """Schema for book recommendation response."""
    isbn: str
    title: str
    author: str
    year: Optional[str] = None
    publisher: Optional[str] = None
    predicted_rating: Optional[float] = None