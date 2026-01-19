"""
Diagnose CSV Data Issues
Checks the CSV files and shows why filtering might fail
"""

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("CSV DATA DIAGNOSIS")
print("=" * 80)
print()

# Load data
print("Loading CSV files...")
print("-" * 80)

try:
    books_data = pd.read_csv(
        'data/Books.csv', nrows=50000, encoding='latin1',
        sep=';', on_bad_lines='skip'
    )
    print(f"✓ Books loaded: {len(books_data)} rows")
    print(f"  Columns: {list(books_data.columns)}")
    
    ratings_data = pd.read_csv(
        'data/Book-Ratings.csv', nrows=50000, encoding='latin1',
        sep=';', on_bad_lines='skip'
    )
    print(f"✓ Ratings loaded: {len(ratings_data)} rows")
    print(f"  Columns: {list(ratings_data.columns)}")
    
    users_data = pd.read_csv(
        'data/Users.csv', encoding='latin1', nrows=50000,
        sep=';', on_bad_lines='skip'
    )
    print(f"✓ Users loaded: {len(users_data)} rows")
    print(f"  Columns: {list(users_data.columns)}")
    
except Exception as e:
    print(f"✗ Error loading CSV files: {e}")
    exit(1)

print()

# Analyze ratings
print("Analyzing ratings...")
print("-" * 80)

print(f"Rating distribution:")
print(ratings_data["Book-Rating"].value_counts().sort_index())
print()

zero_ratings = len(ratings_data[ratings_data["Book-Rating"] == 0])
non_zero_ratings = len(ratings_data[ratings_data["Book-Rating"] > 0])
print(f"Zero ratings: {zero_ratings} ({zero_ratings/len(ratings_data)*100:.1f}%)")
print(f"Non-zero ratings: {non_zero_ratings} ({non_zero_ratings/len(ratings_data)*100:.1f}%)")

print()

# Remove zero ratings
print("After removing zero ratings...")
print("-" * 80)
ratings_data_filtered = ratings_data[ratings_data["Book-Rating"] > 0]
print(f"Remaining ratings: {len(ratings_data_filtered)}")

print()

# Merge datasets
print("Merging datasets...")
print("-" * 80)

try:
    merged_df = pd.merge(ratings_data_filtered, books_data, on="ISBN")
    print(f"✓ After merging with books: {len(merged_df)} ratings")
    
    merged_df = pd.merge(merged_df, users_data, on="User-ID")
    print(f"✓ After merging with users: {len(merged_df)} ratings")
    
except Exception as e:
    print(f"✗ Error merging: {e}")
    exit(1)

print()

# Check ratings per user
print("User rating distribution...")
print("-" * 80)

ratings_per_user = merged_df.groupby("User-ID")["Book-Rating"].count()
print(f"Total unique users: {len(ratings_per_user)}")
print(f"Average ratings per user: {ratings_per_user.mean():.2f}")
print(f"Median ratings per user: {ratings_per_user.median():.0f}")
print()

print("Users by rating count:")
for min_ratings in [1, 2, 3, 5, 10]:
    users_with_min = len(ratings_per_user[ratings_per_user >= min_ratings])
    pct = users_with_min / len(ratings_per_user) * 100
    print(f"  Users with ≥{min_ratings:2d} ratings: {users_with_min:6d} ({pct:5.1f}%)")

print()

# Check ratings per book
print("Book rating distribution...")
print("-" * 80)

ratings_per_book = merged_df.groupby("ISBN")["Book-Rating"].count()
print(f"Total unique books: {len(ratings_per_book)}")
print(f"Average ratings per book: {ratings_per_book.mean():.2f}")
print(f"Median ratings per book: {ratings_per_book.median():.0f}")
print()

print("Books by rating count:")
for min_ratings in [1, 2, 3, 5, 10]:
    books_with_min = len(ratings_per_book[ratings_per_book >= min_ratings])
    pct = books_with_min / len(ratings_per_book) * 100
    print(f"  Books with ≥{min_ratings:2d} ratings: {books_with_min:6d} ({pct:5.1f}%)")

print()

# Test filtering
print("Testing filter criteria...")
print("-" * 80)

for min_user, min_book in [(3, 2), (2, 2), (2, 1), (1, 1)]:
    users_enough = ratings_per_user[ratings_per_user >= min_user].index
    temp_df = merged_df[merged_df["User-ID"].isin(users_enough)]
    
    books_ratings = temp_df.groupby("ISBN")["Book-Rating"].count()
    books_enough = books_ratings[books_ratings >= min_book].index
    temp_df = temp_df[temp_df["ISBN"].isin(books_enough)]
    
    users_final = temp_df["User-ID"].nunique()
    books_final = temp_df["ISBN"].nunique()
    ratings_final = len(temp_df)
    
    print(f"min_user={min_user}, min_book={min_book}:")
    print(f"  Users: {users_final:5d}, Books: {books_final:5d}, Ratings: {ratings_final:6d}")
    
    if ratings_final > 0:
        print(f"  ✓ This filter works!")
    else:
        print(f"  ✗ Too strict - no data left")

print()

# Recommendation
print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if len(merged_df) > 100:
    print("✓ You have enough data for recommendations")
    print("\nSuggested filter values:")
    print("  min_user_ratings = 2")
    print("  min_book_ratings = 2")
    print()
    print("Sample books you can test with:")
    sample_books = merged_df.groupby("Book-Title").size().sort_values(ascending=False).head(5)
    for i, (title, count) in enumerate(sample_books.items(), 1):
        print(f"  {i}. {title} ({count} ratings)")
else:
    print("⚠ Not enough data after filtering")
    print("  Try loading more rows (increase nrows parameter)")

print("=" * 80)