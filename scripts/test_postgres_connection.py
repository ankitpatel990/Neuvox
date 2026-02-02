#!/usr/bin/env python
"""
Simple script to test PostgreSQL connection and create tables.
Run this to verify your PostgreSQL setup.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

def test_connection():
    """Test PostgreSQL connection and create tables."""
    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    print()
    
    # Check POSTGRES_URL
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("[ERROR] POSTGRES_URL not found in environment")
        print("Please set it in your .env file:")
        print("POSTGRES_URL=postgresql://username:password@localhost:5432/database_name")
        return False
    
    # Mask password in output
    if "@" in postgres_url and ":" in postgres_url.split("@")[0]:
        parts = postgres_url.split("@")
        user_pass = parts[0].split("//")[1]
        if ":" in user_pass:
            user = user_pass.split(":")[0]
            masked_url = postgres_url.replace(user_pass, f"{user}:***")
        else:
            masked_url = postgres_url
    else:
        masked_url = postgres_url
    
    print(f"POSTGRES_URL: {masked_url}")
    print()
    
    try:
        from app.database.postgres import init_engine, init_database, verify_schema
        
        print("Step 1: Initializing engine...")
        init_engine()
        print("  [OK] Engine initialized")
        print()
        
        print("Step 2: Checking if tables exist...")
        tables_exist = verify_schema()
        if tables_exist:
            print("  [OK] Tables already exist")
        else:
            print("  [INFO] Tables not found, creating schema...")
            init_database()
            print("  [OK] Schema created successfully")
        print()
        
        print("Step 3: Verifying schema...")
        if verify_schema():
            print("  [OK] All tables and indexes verified")
        else:
            print("  [WARNING] Schema verification failed")
        print()
        
        print("Step 4: Testing connection...")
        from app.database.postgres import get_db_connection
        from sqlalchemy import text
        
        conn = get_db_connection()
        result = conn.execute(text("SELECT version()")).fetchone()
        conn.close()
        print(f"  [OK] Connected to: {result[0][:50]}...")
        print()
        
        print("Step 5: Checking tables...")
        conn = get_db_connection()
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        conn.close()
        
        if result:
            print("  [OK] Found tables:")
            for table in result:
                print(f"    - {table[0]}")
        else:
            print("  [WARNING] No tables found")
        print()
        
        print("=" * 60)
        print("[SUCCESS] PostgreSQL is configured and working!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[ERROR] Connection failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Common issues:")
        print("1. PostgreSQL server is not running")
        print("2. Database doesn't exist - create it first:")
        print("   CREATE DATABASE scamshield;")
        print("3. User doesn't exist or password is wrong")
        print("4. Connection string format is incorrect")
        print()
        print("Example connection string:")
        print("POSTGRES_URL=postgresql://username:password@localhost:5432/scamshield")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
