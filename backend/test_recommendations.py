"""
Test Recommendation Engine
Checks if recommendation data is loaded and working
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 80)
print("RECOMMENDATION ENGINE TEST")
print("=" * 80)
print()

# TEST 1: Check if CSV files exist
print("-" * 80)
print("TEST 1: Checking for CSV data files")
print("-" * 80)

data_dir = Path("data")
required_files = ["Books.csv", "Book-Ratings.csv", "Users.csv"]

csv_files_exist = True
for filename in required_files:
    filepath = data_dir / filename
    if filepath.exists():
        size = filepath.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"✓ {filename} found ({size:.2f} MB)")
    else:
        print(f"✗ {filename} NOT FOUND")
        csv_files_exist = False

if not csv_files_exist:
    print("\n⚠ CSV files are missing!")
    print("\nYou need to download the Book-Crossing dataset:")
    print("1. Create a 'data' folder in your backend directory")
    print("2. Download from: http://www2.informatik.uni-freiburg.de/~cziegler/BX/")
    print("3. Place these files in the data folder:")
    print("   - Books.csv")
    print("   - Book-Ratings.csv")
    print("   - Users.csv")
    print("\nAlternatively, you can use sample data for testing.")
    
print()

# TEST 2: Try to load recommendation service
print("-" * 80)
print("TEST 2: Loading Recommendation Service")
print("-" * 80)

try:
    from app.services.recommendation_service import (
        load_recommendation_data,
        get_book_recommendations,
        _books_data,
        _user_book_matrix
    )
    
    print("✓ Recommendation service imported successfully")
    
    # Check if data is already loaded
    if _books_data is not None:
        print(f"✓ Books data already loaded ({len(_books_data)} books)")
    else:
        print("⚠ Books data not loaded yet")
    
    if _user_book_matrix is not None:
        print(f"✓ User-book matrix loaded ({_user_book_matrix.shape})")
    else:
        print("⚠ User-book matrix not loaded yet")
    
except ImportError as e:
    print(f"✗ Failed to import recommendation service: {e}")
    sys.exit(1)

print()

# TEST 3: Try to load data manually
print("-" * 80)
print("TEST 3: Loading Recommendation Data")
print("-" * 80)

if csv_files_exist:
    try:
        success = load_recommendation_data(
            books_path="data/Books.csv",
            ratings_path="data/Book-Ratings.csv",
            users_path="data/Users.csv",
            nrows=5000  # Use fewer rows for faster testing
        )
        
        if success:
            print("✓ Recommendation data loaded successfully!")
        else:
            print("✗ Failed to load recommendation data")
            
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
else:
    print("⚠ Skipping data load - CSV files not found")

print()

# TEST 4: Test recommendation function
print("-" * 80)
print("TEST 4: Testing Recommendation Function")
print("-" * 80)

if csv_files_exist and _books_data is not None:
    try:
        # Get a sample book title from the loaded data
        if len(_books_data) > 0:
            sample_title = _books_data.iloc[0]["Book-Title"]
            print(f"Testing with book: '{sample_title}'")
            
            recommendations = get_book_recommendations(
                book_title=sample_title,
                top_n=5
            )
            
            if isinstance(recommendations, str):
                print(f"⚠ Got message: {recommendations}")
            elif recommendations is not None and not recommendations.empty:
                print(f"✓ Got {len(recommendations)} recommendations!")
                print("\nTop 3 recommendations:")
                for idx, row in recommendations.head(3).iterrows():
                    print(f"  {idx + 1}. {row['Book-Title']} by {row['Book-Author']}")
            else:
                print("✗ No recommendations returned")
        else:
            print("✗ No books in dataset")
            
    except Exception as e:
        print(f"✗ Recommendation test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠ Skipping - data not loaded")

print()

# TEST 5: Test via API (if server is running)
print("-" * 80)
print("TEST 5: Testing API Endpoint (optional)")
print("-" * 80)

try:
    import requests
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✓ Server is running")
            
            # Test recommendations endpoint
            if csv_files_exist and _books_data is not None and len(_books_data) > 0:
                sample_title = _books_data.iloc[0]["Book-Title"]
                
                api_response = requests.post(
                    "http://localhost:8000/api/v1/recommendations/",
                    json={"book_title": sample_title, "top_n": 3},
                    timeout=10
                )
                
                if api_response.status_code == 200:
                    data = api_response.json()
                    print(f"✓ API returned {len(data)} recommendations")
                else:
                    print(f"✗ API returned status {api_response.status_code}")
                    print(f"  Response: {api_response.text}")
            else:
                print("⚠ Skipping API test - no data available")
        else:
            print("⚠ Server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("⚠ Server not running (start with: uvicorn app.main:app --reload)")
    except requests.exceptions.Timeout:
        print("⚠ Server request timed out")
        
except ImportError:
    print("⚠ 'requests' library not installed (pip install requests)")

print()

# SUMMARY
print("=" * 80)
print("SUMMARY")
print("=" * 80)

if not csv_files_exist:
    print("✗ CSV files are missing - download the Book-Crossing dataset")
    print("\nCreate sample CSV files or download from:")
    print("http://www2.informatik.uni-freiburg.de/~cziegler/BX/")
elif _books_data is None:
    print("✗ Data not loaded - check for errors above")
    print("\nThe recommendation engine needs to load data on startup.")
    print("Make sure main.py calls load_recommendation_data()")
else:
    print("✓ Recommendation engine is working!")
    print(f"\n✓ Loaded {len(_books_data)} books")
    print(f"✓ User-book matrix shape: {_user_book_matrix.shape}")
    print("\nYou can now use the recommendations API!")

print("=" * 80)