"""Recommendation service using collaborative filtering."""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import logging
from typing import Union

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Global variables to store loaded data
_books_data = None
_ratings_data = None
_users_data = None
_user_book_matrix = None
_user_similarity = None
_ratings_matrix = None
_user_means = None
_merged_df_filtered = None


def load_recommendation_data(
    books_path: str = "data/Books.csv",
    ratings_path: str = "data/Book-Ratings.csv",
    users_path: str = "data/Users.csv",
    nrows: int = 50000
):
    """
    Load and prepare data for the recommendation system.
    
    This should be called once during application startup.
    """
    global _books_data, _ratings_data, _users_data
    global _user_book_matrix, _user_similarity, _ratings_matrix
    global _user_means, _merged_df_filtered
    
    try:
        logger.info("Loading recommendation data...")
        
        # Load datasets
        _books_data = pd.read_csv(
            books_path, nrows=nrows, encoding='latin1',
            sep=';', on_bad_lines='skip'
        )
        _ratings_data = pd.read_csv(
            ratings_path, nrows=nrows, encoding='latin1',
            sep=';', on_bad_lines='skip'
        )
        _users_data = pd.read_csv(
            users_path, encoding='latin1', nrows=nrows,
            sep=';', on_bad_lines='skip'
        )
        
        logger.info(f"Loaded: {len(_books_data)} books, {len(_ratings_data)} ratings, {len(_users_data)} users")
        
        # Remove ratings with 0 values
        _ratings_data = _ratings_data[_ratings_data["Book-Rating"] > 0]
        logger.info(f"After removing zero ratings: {len(_ratings_data)} ratings")
        
        # Merge datasets
        merged_df = pd.merge(_ratings_data, _books_data, on="ISBN", how="inner")
        logger.info(f"After merging with books: {len(merged_df)} ratings")
        
        merged_df = pd.merge(merged_df, _users_data, on="User-ID", how="inner")
        logger.info(f"After merging with users: {len(merged_df)} ratings")
        
        if len(merged_df) < 10:
            logger.error(f"Not enough data after merging: {len(merged_df)} rows")
            return False
        
        # Filter data - use lenient criteria
        min_user_ratings = 2
        min_book_ratings = 1
        
        ratings_per_user = merged_df.groupby("User-ID")["Book-Rating"].count()
        users_with_enough_ratings = ratings_per_user[
            ratings_per_user >= min_user_ratings
        ].index
        
        if len(users_with_enough_ratings) == 0:
            logger.warning("No users meet minimum rating criteria, using all users")
            _merged_df_filtered = merged_df
        else:
            _merged_df_filtered = merged_df[
                merged_df["User-ID"].isin(users_with_enough_ratings)
            ]
            
            ratings_per_book = _merged_df_filtered.groupby("ISBN")["Book-Rating"].count()
            books_with_enough_ratings = ratings_per_book[
                ratings_per_book >= min_book_ratings
            ].index
            
            if len(books_with_enough_ratings) == 0:
                logger.warning("No books meet minimum rating criteria, using all books")
                _merged_df_filtered = merged_df
            else:
                _merged_df_filtered = _merged_df_filtered[
                    _merged_df_filtered["ISBN"].isin(books_with_enough_ratings)
                ]
        
        logger.info(f"After filtering: {len(_merged_df_filtered)} ratings")
        logger.info(f"Filtered users: {_merged_df_filtered['User-ID'].nunique()}")
        logger.info(f"Filtered books: {_merged_df_filtered['ISBN'].nunique()}")
        
        if len(_merged_df_filtered) < 10:
            logger.warning(f"Very few ratings after filtering: {len(_merged_df_filtered)}")
            logger.warning("Using unfiltered data...")
            _merged_df_filtered = merged_df
        
        # Create user-book matrix
        _user_book_matrix = _merged_df_filtered.pivot_table(
            index="User-ID",
            columns="ISBN",
            values="Book-Rating",
            fill_value=0
        )
        
        logger.info(f"User-book matrix shape: {_user_book_matrix.shape}")
        
        _ratings_matrix = _user_book_matrix.to_numpy()
        
        # Check if matrix is empty
        if _ratings_matrix.size == 0 or _ratings_matrix.shape[0] == 0:
            logger.error("Rating matrix is empty")
            return False
        
        # Normalize ratings
        _user_means = np.zeros(_ratings_matrix.shape[0])
        ratings_matrix_normalized = _ratings_matrix.copy()
        
        for i in range(_ratings_matrix.shape[0]):
            user_ratings = _ratings_matrix[i][_ratings_matrix[i] > 0]
            if len(user_ratings) > 0:
                _user_means[i] = np.mean(user_ratings)
                mask = _ratings_matrix[i] > 0
                ratings_matrix_normalized[i][mask] -= _user_means[i]
        
        # Compute user similarity
        if _ratings_matrix.shape[0] < 2:
            logger.warning("Not enough users for similarity computation")
            _user_similarity = np.array([[1.0]])
        else:
            logger.info("Computing user similarity matrix...")
            _user_similarity = cosine_similarity(ratings_matrix_normalized)
        
        # Calculate sparsity
        non_zero_count = np.count_nonzero(_ratings_matrix)
        sparsity = 1 - (non_zero_count / _ratings_matrix.size)
        
        logger.info(f"Matrix sparsity: {sparsity:.2%}")
        logger.info(f"Non-zero ratings: {non_zero_count}")
        logger.info("Recommendation data loaded successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading recommendation data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_book_recommendations(
    book_title: str,
    k: int = 10,
    top_n: int = 10
) -> Union[pd.DataFrame, str]:
    """
    Get book recommendations based on a book title using collaborative filtering.
    
    Parameters:
    -----------
    book_title : str
        The book title to base recommendations on
    k : int
        Number of similar users to consider (default: 10)
    top_n : int
        Number of top books to recommend (default: 10)
    
    Returns:
    --------
    pd.DataFrame or str
        DataFrame with recommended books or error message
    """
    global _books_data, _user_book_matrix, _user_similarity, _ratings_matrix
    
    # Check if data is loaded
    if _user_book_matrix is None or _books_data is None:
        return "Recommendation system not initialized. Please load data first."
    
    try:
        # Find books matching the title (case-insensitive partial match)
        matching_books = _books_data[
            _books_data["Book-Title"].str.contains(
                book_title, case=False, na=False, regex=False
            )
        ]
        
        if matching_books.empty:
            return f"No books found matching title: '{book_title}'"
        
        logger.info(f"Found {len(matching_books)} books matching '{book_title}'")
        
        # Get the first matching book's ISBN
        target_isbn = matching_books.iloc[0]["ISBN"]
        target_title = matching_books.iloc[0]["Book-Title"]
        
        logger.info(f"Using book: '{target_title}' (ISBN: {target_isbn})")
        
        # Check if this book is in our user-book matrix
        if target_isbn not in _user_book_matrix.columns:
            return f"Book '{target_title}' found but not enough ratings for recommendations"
        
        # Find users who rated this book
        book_col_idx = _user_book_matrix.columns.get_loc(target_isbn)
        users_who_rated = _ratings_matrix[:, book_col_idx] > 0
        
        if not np.any(users_who_rated):
            return f"No users have rated '{target_title}'"
        
        logger.info(f"{np.sum(users_who_rated)} users rated this book")
        
        # Use the first user who rated this book highly
        user_ratings = _ratings_matrix[users_who_rated, book_col_idx]
        best_user_idx = np.where(users_who_rated)[0][np.argmax(user_ratings)]
        
        # Adjust k if needed
        k = min(k, len(_user_book_matrix) - 1)
        
        # Get similarity scores
        similarity_scores = _user_similarity[best_user_idx].copy()
        similarity_scores[similarity_scores <= 0] = 0
        
        # Find k most similar users
        similar_users_indices = np.argsort(similarity_scores)[::-1][1:k+1]
        similar_users_indices = similar_users_indices[
            similarity_scores[similar_users_indices] > 0
        ]
        
        if len(similar_users_indices) == 0:
            return "No similar users found for recommendations"
        
        logger.info(f"Found {len(similar_users_indices)} similar users")
        
        # Calculate weighted ratings
        weights = similarity_scores[similar_users_indices]
        weights = weights / np.sum(weights)
        
        avg_book_ratings = np.zeros(_ratings_matrix.shape[1])
        for idx, user_idx in enumerate(similar_users_indices):
            user_ratings = _ratings_matrix[user_idx]
            avg_book_ratings += user_ratings * weights[idx]
        
        # Exclude already rated books
        user_rated_mask = _ratings_matrix[best_user_idx] > 0
        avg_book_ratings[user_rated_mask] = -1
        
        # Get top recommendations
        top_book_indices = np.argsort(avg_book_ratings)[::-1]
        top_book_indices = top_book_indices[
            avg_book_ratings[top_book_indices] >= 0
        ][:top_n]
        
        if len(top_book_indices) == 0:
            return "No new books to recommend"
        
        recommended_isbns = _user_book_matrix.columns[top_book_indices]
        
        # Get book details
        recommended_books = _books_data[
            _books_data["ISBN"].isin(recommended_isbns)
        ][[
            "ISBN", "Book-Title", "Book-Author",
            "Year-Of-Publication", "Publisher"
        ]].copy()
        
        # Add predicted ratings
        predicted_ratings = []
        for isbn in recommended_books["ISBN"]:
            col_idx = _user_book_matrix.columns.get_loc(isbn)
            predicted_ratings.append(avg_book_ratings[col_idx])
        
        recommended_books["Predicted-Rating"] = predicted_ratings
        recommended_books = recommended_books.sort_values(
            "Predicted-Rating", ascending=False
        )
        
        logger.info(f"Generated {len(recommended_books)} recommendations")
        
        return recommended_books
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error generating recommendations: {str(e)}"