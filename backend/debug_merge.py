"""
Debug why merges are failing
"""

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("DEBUG CSV MERGE ISSUE")
print("=" * 80)
print()

# Load with different parameters
print("Testing different loading methods...")
print("-" * 80)

# Test 1: Load with default settings
print("\n1. Loading Books.csv...")
try:
    books = pd.read_csv('data/Books.csv', nrows=1000, encoding='latin1', sep=';', on_bad_lines='skip')
    print(f"   ✓ Loaded {len(books)} books")
    print(f"   Columns: {list(books.columns)}")
    print(f"   Sample ISBNs: {books['ISBN'].head(3).tolist()}")
    print(f"   ISBN dtype: {books['ISBN'].dtype}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print("\n2. Loading Book-Ratings.csv...")
try:
    ratings = pd.read_csv('data/Book-Ratings.csv', nrows=1000, encoding='latin1', sep=';', on_bad_lines='skip')
    print(f"   ✓ Loaded {len(ratings)} ratings")
    print(f"   Columns: {list(ratings.columns)}")
    print(f"   Sample ISBNs: {ratings['ISBN'].head(3).tolist()}")
    print(f"   ISBN dtype: {ratings['ISBN'].dtype}")
    print(f"   Non-zero ratings: {len(ratings[ratings['Book-Rating'] > 0])}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print("\n3. Loading Users.csv...")
try:
    users = pd.read_csv('data/Users.csv', nrows=1000, encoding='latin1', sep=';', on_bad_lines='skip')
    print(f"   ✓ Loaded {len(users)} users")
    print(f"   Columns: {list(users.columns)}")
    print(f"   Sample User-IDs: {users['User-ID'].head(3).tolist()}")
    print(f"   User-ID dtype: {users['User-ID'].dtype}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print()
print("-" * 80)
print("Testing merges...")
print("-" * 80)

# Remove zero ratings
ratings_filtered = ratings[ratings['Book-Rating'] > 0]
print(f"\n1. After removing zero ratings: {len(ratings_filtered)} ratings")

# Check ISBN overlap
print(f"\n2. Checking ISBN overlap...")
print(f"   Unique ISBNs in books: {books['ISBN'].nunique()}")
print(f"   Unique ISBNs in ratings: {ratings_filtered['ISBN'].nunique()}")

common_isbns = set(books['ISBN']) & set(ratings_filtered['ISBN'])
print(f"   Common ISBNs: {len(common_isbns)}")

if len(common_isbns) == 0:
    print("\n   ✗ NO COMMON ISBNs FOUND!")
    print("\n   Comparing sample ISBNs:")
    print(f"   Books ISBNs (first 5): {books['ISBN'].head(5).tolist()}")
    print(f"   Ratings ISBNs (first 5): {ratings_filtered['ISBN'].head(5).tolist()}")
    
    # Check for whitespace or formatting issues
    print("\n   Checking for formatting issues...")
    book_isbn_sample = str(books['ISBN'].iloc[0])
    rating_isbn_sample = str(ratings_filtered['ISBN'].iloc[0])
    print(f"   Book ISBN example: '{book_isbn_sample}' (len={len(book_isbn_sample)})")
    print(f"   Rating ISBN example: '{rating_isbn_sample}' (len={len(rating_isbn_sample)})")
else:
    print(f"   ✓ Found {len(common_isbns)} common ISBNs")

# Try merge
print(f"\n3. Attempting merge (ratings + books)...")
merged1 = pd.merge(ratings_filtered, books, on='ISBN', how='inner')
print(f"   Result: {len(merged1)} rows")

if len(merged1) > 0:
    print(f"   ✓ Merge successful!")
    
    # Check User-ID overlap
    print(f"\n4. Checking User-ID overlap...")
    print(f"   Unique User-IDs in merged data: {merged1['User-ID'].nunique()}")
    print(f"   Unique User-IDs in users: {users['User-ID'].nunique()}")
    
    common_users = set(merged1['User-ID']) & set(users['User-ID'])
    print(f"   Common User-IDs: {len(common_users)}")
    
    if len(common_users) == 0:
        print("\n   ✗ NO COMMON USER-IDs FOUND!")
        print(f"   Merged User-IDs (first 5): {merged1['User-ID'].head(5).tolist()}")
        print(f"   Users User-IDs (first 5): {users['User-ID'].head(5).tolist()}")
    else:
        print(f"   ✓ Found {len(common_users)} common User-IDs")
    
    # Try second merge
    print(f"\n5. Attempting merge (merged + users)...")
    merged2 = pd.merge(merged1, users, on='User-ID', how='inner')
    print(f"   Result: {len(merged2)} rows")
    
    if len(merged2) > 0:
        print(f"   ✓ Final merge successful!")
        print(f"\n   Final dataset:")
        print(f"   - Users: {merged2['User-ID'].nunique()}")
        print(f"   - Books: {merged2['ISBN'].nunique()}")
        print(f"   - Ratings: {len(merged2)}")
    else:
        print(f"   ✗ Final merge failed!")
else:
    print(f"   ✗ First merge failed!")

print()
print("=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if len(common_isbns) == 0:
    print("✗ Problem: No common ISBNs between books and ratings")
    print("\nPossible causes:")
    print("1. The nrows parameter is loading different sections of the files")
    print("2. ISBN formatting differences (quotes, whitespace)")
    print("3. Different encoding issues")
    print("\nSolution: Try loading MORE rows (nrows=50000 or higher)")
elif len(merged1) == 0:
    print("✗ Problem: Merge failed despite common ISBNs")
    print("Check for data type mismatches")
elif len(common_users) == 0:
    print("✗ Problem: No common User-IDs")
    print("Solution: Load more rows from Users.csv")
elif len(merged2) == 0:
    print("✗ Problem: User merge failed")
else:
    print("✓ Everything works! The issue is likely the nrows parameter.")
    print(f"\nWith nrows=1000, we get {len(merged2)} usable ratings")
    print("Try loading with nrows=100000 for better coverage")

print("=" * 80)