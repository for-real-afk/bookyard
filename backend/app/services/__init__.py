"""Services module."""

# Import existing services if any
# from .recommendation import BookRecommendationService  # Comment out or remove if this doesn't exist

# Import new recommendation service functions
from app.services.recommendation_service import (
    load_recommendation_data,
    get_book_recommendations
)

__all__ = [
    "load_recommendation_data",
    "get_book_recommendations"
]