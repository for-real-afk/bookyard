"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import books, user_ratings, recommendations

api_router = APIRouter()

api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(user_ratings.router, prefix="/userratings", tags=["user-ratings"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])