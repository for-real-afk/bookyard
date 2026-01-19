"""User Ratings API endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.db.session import get_session
from app.crud.crud_user_rating import crud_user_rating
from app.crud.crud_book import crud_book
from app.schemas.user_rating import (
    UserRatingCreate,
    UserRatingResponse,
    UserRatingUpdate
)
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=UserRatingResponse, status_code=status.HTTP_201_CREATED)
def create_rating(
    rating_in: UserRatingCreate,
    db: Session = Depends(get_session)
):
    """Create a new user rating for a book."""
    # Check if book exists
    book = crud_book.get(db, rating_in.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user already rated this book
    existing_rating = crud_user_rating.get_by_user_and_book(
        db, user_id=rating_in.user_id, book_id=rating_in.book_id
    )
    
    if existing_rating:
        raise HTTPException(
            status_code=400,
            detail="User has already rated this book. Use PUT to update the rating."
        )
    
    # Create rating
    rating = crud_user_rating.create(db, obj_in=rating_in)
    logger.info(f"Rating created: User {rating.user_id} rated book {rating.book_id} with {rating.rating}")
    return rating


@router.get("/user/{user_id}", response_model=PaginatedResponse[UserRatingResponse])
def get_user_ratings(
    user_id: UUID,
    db: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all ratings by a specific user."""
    ratings = crud_user_rating.get_user_ratings(
        db, user_id=user_id, skip=skip, limit=limit
    )
    total = crud_user_rating.count_user_ratings(db, user_id=user_id)
    
    return {"items": ratings, "total": total, "skip": skip, "limit": limit}


@router.get("/book/{book_id}", response_model=PaginatedResponse[UserRatingResponse])
def get_book_ratings(
    book_id: int,
    db: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all ratings for a specific book."""
    # Check if book exists
    book = crud_book.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    ratings = crud_user_rating.get_book_ratings(
        db, book_id=book_id, skip=skip, limit=limit
    )
    total = len(crud_user_rating.get_book_ratings(db, book_id=book_id, limit=10000))
    
    return {"items": ratings, "total": total, "skip": skip, "limit": limit}


@router.get("/book/{book_id}/average")
def get_book_average_rating(
    book_id: int,
    db: Session = Depends(get_session)
):
    """Get average rating for a book."""
    # Check if book exists
    book = crud_book.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    avg_rating = crud_user_rating.get_average_rating(db, book_id=book_id)
    
    if avg_rating is None:
        return {
            "book_id": book_id,
            "average_rating": None,
            "total_ratings": 0,
            "message": "No ratings yet for this book"
        }
    
    total = len(crud_user_rating.get_book_ratings(db, book_id=book_id, limit=10000))
    
    return {
        "book_id": book_id,
        "average_rating": round(avg_rating, 2),
        "total_ratings": total
    }


@router.put("/{rating_id}", response_model=UserRatingResponse)
def update_rating(
    rating_id: int,
    rating_in: UserRatingUpdate,
    db: Session = Depends(get_session)
):
    """Update an existing user rating."""
    rating = crud_user_rating.get(db, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    # Update timestamp
    rating_in_dict = rating_in.model_dump(exclude_unset=True)
    rating_in_dict['updated_at'] = datetime.utcnow()
    
    updated_rating = crud_user_rating.update(db, db_obj=rating, obj_in=rating_in_dict)
    logger.info(f"Rating updated: {rating_id}")
    return updated_rating


@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    rating_id: int,
    db: Session = Depends(get_session)
):
    """Delete a user rating."""
    rating = crud_user_rating.get(db, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    crud_user_rating.delete(db, id=rating_id)
    logger.info(f"Rating deleted: {rating_id}")
    return None