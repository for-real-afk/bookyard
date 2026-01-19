"""Book Recommendations API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.user_rating import (
    BookRecommendationRequest,
    BookRecommendationResponse
)
from app.services.recommendation_service import get_book_recommendations

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=List[BookRecommendationResponse])
def recommend_books(
    request: BookRecommendationRequest,
    db: Session = Depends(get_session)
):
    """
    Get book recommendations based on a book title.
    
    This endpoint uses a collaborative filtering recommendation engine
    to suggest similar books based on the provided book title.
    """
    try:
        recommendations = get_book_recommendations(
            book_title=request.book_title,
            top_n=request.top_n
        )
        
        if isinstance(recommendations, str):
            # Error message returned
            raise HTTPException(status_code=404, detail=recommendations)
        
        if recommendations.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for book: {request.book_title}"
            )
        
        # Convert DataFrame to response models
        results = []
        for _, row in recommendations.iterrows():
            results.append(
                BookRecommendationResponse(
                    isbn=row.get("ISBN", ""),
                    title=row.get("Book-Title", ""),
                    author=row.get("Book-Author", ""),
                    year=str(row.get("Year-Of-Publication", "")) if row.get("Year-Of-Publication") else None,
                    publisher=row.get("Publisher"),
                    predicted_rating=float(row.get("Predicted-Rating")) if row.get("Predicted-Rating") else None
                )
            )
        
        logger.info(f"Generated {len(results)} recommendations for book: {request.book_title}")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/by-title", response_model=List[BookRecommendationResponse])
def recommend_books_by_title(
    book_title: str = Query(..., min_length=1, description="Book title to base recommendations on"),
    top_n: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    db: Session = Depends(get_session)
):
    """
    Get book recommendations based on a book title (GET version).
    
    This endpoint uses a collaborative filtering recommendation engine
    to suggest similar books based on the provided book title.
    """
    request = BookRecommendationRequest(book_title=book_title, top_n=top_n)
    return recommend_books(request, db)