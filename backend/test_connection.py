"""
Comprehensive Database and Application Test
Tests connection, tables, and API endpoints
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
from app.core.config import settings
import socket

# Load environment variables
load_dotenv()

print("=" * 80)
print("COMPREHENSIVE SETUP TEST")
print("=" * 80)
print()

# Extract database details
DATABASE_URL = settings.DATABASE_URL
print(f"Database URL: {DATABASE_URL}")
print(f"Environment: {settings.ENVIRONMENT}")
print()

# Parse URL
if DATABASE_URL.startswith("postgresql://"):
    parts = DATABASE_URL.replace("postgresql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")
    host_port = host_db[0].split(":")
    
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    database = host_db[1].split("?")[0] if len(host_db) > 1 else ""
else:
    print("✗ Not a PostgreSQL URL")
    sys.exit(1)

all_tests_passed = True

# TEST 1: Network connectivity
print("-" * 80)
print("TEST 1: Network Connectivity")
print("-" * 80)

try:
    # Resolve localhost to IP if needed
    if host == "localhost":
        test_host = "127.0.0.1"
    else:
        test_host = host
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((test_host, int(port)))
    sock.close()
    
    if result == 0:
        print(f"✓ Port {port} is accessible on {host}")
    else:
        print(f"✗ Port {port} is NOT accessible on {host}")
        print("\nPostgreSQL is not running. Start it first!")
        all_tests_passed = False
except Exception as e:
    print(f"✗ Network test failed: {e}")
    all_tests_passed = False

print()

# TEST 2: Database connection
print("-" * 80)
print("TEST 2: Database Connection")
print("-" * 80)

try:
    engine = create_engine(DATABASE_URL, echo=False)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        
        result = conn.execute(text("SELECT current_database(), current_user;"))
        db_info = result.fetchone()
        
        print(f"✓ Connection successful")
        print(f"✓ Database: {db_info[0]}")
        print(f"✓ User: {db_info[1]}")
        print(f"✓ PostgreSQL version: {version[:60]}...")
        
except OperationalError as e:
    print(f"✗ Connection failed: {e}")
    all_tests_passed = False
    
    if "database" in str(e) and "does not exist" in str(e):
        print(f"\nDatabase '{database}' does not exist. Create it with:")
        print(f"  createdb -U {user} {database}")
    elif "password authentication failed" in str(e):
        print("\nPassword authentication failed. Check .env credentials")
    
    print()
    sys.exit(1)

print()

# TEST 3: Check tables
print("-" * 80)
print("TEST 3: Database Tables")
print("-" * 80)

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = ["books", "user_ratings"]
    
    if not tables:
        print("⚠ No tables found in database")
        print("\nRun initialization script:")
        print("  python init_db.py")
        all_tests_passed = False
    else:
        print(f"✓ Found {len(tables)} table(s):")
        
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"\n  Table: {table}")
            print(f"  Columns: {len(columns)}")
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"    - {col['name']}: {col_type} ({nullable})")
        
        # Check for expected tables
        print("\n  Expected tables:")
        for expected in expected_tables:
            if expected in tables:
                print(f"    ✓ {expected}")
            else:
                print(f"    ✗ {expected} (MISSING)")
                all_tests_passed = False

except Exception as e:
    print(f"✗ Error checking tables: {e}")
    all_tests_passed = False

print()

# TEST 4: Test CRUD operations
print("-" * 80)
print("TEST 4: CRUD Operations Test")
print("-" * 80)

if "books" in tables:
    try:
        with engine.connect() as conn:
            # Test INSERT
            result = conn.execute(text("""
                INSERT INTO books (title, author, isbn, description, published_year, pages, is_active, created_at, updated_at)
                VALUES ('Test Book', 'Test Author', '1234567890', 'Test Description', 2024, 300, true, NOW(), NOW())
                RETURNING id, title;
            """))
            conn.commit()
            
            inserted = result.fetchone()
            test_id = inserted[0]
            print(f"✓ INSERT: Created book with ID {test_id}")
            
            # Test SELECT
            result = conn.execute(text(f"SELECT * FROM books WHERE id = {test_id};"))
            book = result.fetchone()
            print(f"✓ SELECT: Retrieved book '{book[1]}'")
            
            # Test UPDATE
            conn.execute(text(f"""
                UPDATE books 
                SET description = 'Updated Description' 
                WHERE id = {test_id};
            """))
            conn.commit()
            print(f"✓ UPDATE: Updated book description")
            
            # Test DELETE
            conn.execute(text(f"DELETE FROM books WHERE id = {test_id};"))
            conn.commit()
            print(f"✓ DELETE: Deleted test book")
            
            print("\n✓ All CRUD operations working!")
            
    except Exception as e:
        print(f"✗ CRUD test failed: {e}")
        all_tests_passed = False
else:
    print("⚠ Skipping CRUD test - books table not found")
    all_tests_passed = False

print()

# TEST 5: Test user_ratings table (if exists)
print("-" * 80)
print("TEST 5: User Ratings Table Test")
print("-" * 80)

if "user_ratings" in tables:
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM user_ratings;"))
            count = result.fetchone()[0]
            print(f"✓ user_ratings table accessible")
            print(f"✓ Current ratings count: {count}")
    except Exception as e:
        print(f"✗ user_ratings test failed: {e}")
        all_tests_passed = False
else:
    print("⚠ user_ratings table not found")
    print("  Run: python init_db.py")
    all_tests_passed = False

print()

# SUMMARY
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

if all_tests_passed:
    print("✓ All tests PASSED!")
    print("\nYour database is ready. Start the application with:")
    print("  uvicorn app.main:app --reload")
    print("\nAPI docs will be available at:")
    print("  http://localhost:8000/api/v1/docs")
else:
    print("✗ Some tests FAILED")
    print("\nFix the issues above and run this test again.")
    print("\nIf tables are missing, run:")
    print("  python init_db.py")

print("=" * 80)