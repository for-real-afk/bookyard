"""
Database Initialization Script
Creates all tables in the database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, text
from app.core.config import settings

# Import all models so they're registered with SQLModel
from app.models.book import Book
from app.models.user_rating import UserRating

# Load environment variables
load_dotenv()

print("=" * 80)
print("DATABASE INITIALIZATION")
print("=" * 80)
print(f"\nDatabase URL: {settings.DATABASE_URL}")
print(f"Environment: {settings.ENVIRONMENT}")
print()

try:
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        echo=True  # Show SQL statements
    )
    
    print("-" * 80)
    print("Testing connection...")
    print("-" * 80)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), current_user;"))
        row = result.fetchone()
        print(f"✓ Connected to database: {row[0]}")
        print(f"✓ Connected as user: {row[1]}")
    
    print()
    print("-" * 80)
    print("Creating tables...")
    print("-" * 80)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    print()
    print("-" * 80)
    print("Verifying tables...")
    print("-" * 80)
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        
        if tables:
            print(f"\n✓ Successfully created {len(tables)} table(s):")
            for table in tables:
                # Get column count
                col_result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}';
                """))
                col_count = col_result.fetchone()[0]
                print(f"  ✓ {table} ({col_count} columns)")
        else:
            print("\n✗ No tables found!")
    
    print()
    print("=" * 80)
    print("✓ DATABASE INITIALIZATION COMPLETE!")
    print("=" * 80)
    print("\nYou can now start your application with:")
    print("  uvicorn app.main:app --reload")
    print("=" * 80)
    
except Exception as e:
    print()
    print("=" * 80)
    print("✗ ERROR DURING INITIALIZATION")
    print("=" * 80)
    print(f"\n{type(e).__name__}: {e}")
    print()
    
    if "could not connect" in str(e).lower() or "connection refused" in str(e).lower():
        print("PostgreSQL is not running. Start it with:")
        print("  Windows: net start postgresql-x64-15")
        print("  Linux: sudo service postgresql start")
        print("  macOS: brew services start postgresql")
        print("\nOr use Docker:")
        print("  docker run -d --name bookyard-db -p 5432:5432 \\")
        print("    -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=bookyard postgres:15")
    
    elif "does not exist" in str(e).lower():
        print("Database does not exist. Create it with:")
        print("  createdb -U postgres bookyard")
        print("  OR: psql -U postgres -c 'CREATE DATABASE bookyard;'")
    
    elif "password authentication failed" in str(e).lower():
        print("Check your database credentials in .env file")
    
    print()
    sys.exit(1)