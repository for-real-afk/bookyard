"""CRUD operations for UserRating."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.crud.base import CRUDBase
from app.models.user_rating import UserRating
from app.schemas.user_rating import UserRatingCreate, UserRatingUpdate


class CRUDUserRating(CRUDBase[UserRating, UserRatingCreate, UserRatingUpdate]):
    """CRUD operations for user ratings."""
    
    def get_by_user_and_book(
        self,
        db: Session,
        *,
        user_id: UUID,
        book_id: int
    ) -> Optional[UserRating]:
        """Get a user's rating for a specific book."""
        statement = select(UserRating).where(
            UserRating.user_id == user_id,
            UserRating.book_id == book_id
        )
        result = db.exec(statement).first()
        return result
    
    def get_user_ratings(
        self,
        db: Session,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRating]:
        """Get all ratings by a user."""
        statement = select(UserRating).where(
            UserRating.user_id == user_id
        ).offset(skip).limit(limit)
        results = db.exec(statement)
        return results.all()
    
    def get_book_ratings(
        self,
        db: Session,
        *,
        book_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRating]:
        """Get all ratings for a book."""
        statement = select(UserRating).where(
            UserRating.book_id == book_id
        ).offset(skip).limit(limit)
        results = db.exec(statement)
        return results.all()
    
    def count_user_ratings(
        self,
        db: Session,
        *,
        user_id: UUID
    ) -> int:
        """Count total ratings by a user."""
        statement = select(UserRating).where(UserRating.user_id == user_id)
        results = db.exec(statement)
        return len(results.all())
    
    def get_average_rating(
        self,
        db: Session,
        *,
        book_id: int
    ) -> Optional[float]:
        """Get average rating for a book."""
        ratings = self.get_book_ratings(db, book_id=book_id, limit=10000)
        if not ratings:
            return None
        total = sum(r.rating for r in ratings)
        return total / len(ratings)


crud_user_rating = CRUDUserRating(UserRating)