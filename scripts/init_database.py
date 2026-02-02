#!/usr/bin/env python
"""
Database Initialization Script.

Creates PostgreSQL schema and initializes database:
- conversations table
- messages table
- extracted_intelligence table
- Required indexes

Run this script after setting up PostgreSQL connection.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text


# SQL schema definition
SCHEMA_SQL = """
-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(10) NOT NULL,
    persona VARCHAR(50),
    scam_detected BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    turn_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    sender VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create extracted_intelligence table
CREATE TABLE IF NOT EXISTS extracted_intelligence (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    upi_ids TEXT[],
    bank_accounts TEXT[],
    ifsc_codes TEXT[],
    phone_numbers TEXT[],
    phishing_links TEXT[],
    extraction_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_scam_detected ON conversations(scam_detected);
"""


def check_environment():
    """Check required environment variables."""
    postgres_url = os.getenv("POSTGRES_URL")
    
    if not postgres_url:
        print("[WARNING] POSTGRES_URL environment variable not set")
        print("Set it using: export POSTGRES_URL=postgresql://user:pass@host:5432/dbname")
        return False
    
    return True


def init_postgres():
    """Initialize PostgreSQL database with schema."""
    print("Initializing PostgreSQL database...")
    
    try:
        from app.database.postgres import init_database, verify_schema, get_db_connection
        
        # Initialize database schema
        init_database()
        print("  ✓ Schema created successfully")
        
        # Verify schema
        if verify_schema():
            print("  ✓ Schema verification passed")
        else:
            print("  ⚠ Schema verification found issues")
        
        # Test connection
        conn = get_db_connection()
        result = conn.execute(text("SELECT 1")).fetchone()
        conn.close()
        print(f"  ✓ Connection test: {result}")
        
    except ConnectionError as e:
        print(f"  ✗ Connection failed: {e}")
        print("  [INFO] Set POSTGRES_URL environment variable to enable database")
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()


def init_redis():
    """Initialize Redis connection and test."""
    print("Testing Redis connection...")
    
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        print("  [WARNING] REDIS_URL not set, skipping Redis test")
        return
    
    try:
        from app.database.redis_client import get_redis_client, health_check
        
        # Test connection
        client = get_redis_client()
        client.ping()
        print("  ✓ Connection successful")
        
        # Test read/write
        test_key = "test:init"
        test_value = "ok"
        client.set(test_key, test_value, ex=10)
        retrieved = client.get(test_key)
        client.delete(test_key)
        
        if retrieved == test_value:
            print("  ✓ Read/write test passed")
        else:
            print(f"  ⚠ Read/write test failed: expected '{test_value}', got '{retrieved}'")
        
        # Health check
        if health_check():
            print("  ✓ Health check passed")
        else:
            print("  ⚠ Health check failed")
            
    except ConnectionError as e:
        print(f"  ✗ Connection failed: {e}")
        print("  [INFO] Set REDIS_URL environment variable to enable Redis")
    except Exception as e:
        print(f"  ✗ Redis test failed: {e}")
        import traceback
        traceback.print_exc()


def verify_database():
    """Verify database tables exist."""
    print("\nVerifying database setup...")
    
    try:
        from app.database.postgres import verify_schema, get_db_connection
        from sqlalchemy import text
        
        if verify_schema():
            print("  ✓ All tables and indexes exist")
            
            # Additional verification: check table counts
            conn = get_db_connection()
            try:
                tables = ['conversations', 'messages', 'extracted_intelligence']
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                    print(f"  ✓ {table}: {result[0]} rows")
            finally:
                conn.close()
            
            return True
        else:
            print("  ✗ Schema verification failed")
            return False
    except ConnectionError:
        print("  [INFO] Database not configured, skipping verification")
        return False
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False


def main():
    """Main entry point for database initialization."""
    print("=" * 60)
    print("ScamShield AI - Database Initialization")
    print("=" * 60)
    print()
    
    # Check environment
    if not check_environment():
        print("\n[INFO] Running in stub mode - no actual database operations")
    
    print()
    
    # Initialize databases
    init_postgres()
    print()
    
    init_redis()
    print()
    
    # Verify
    if verify_database():
        print("\n" + "=" * 60)
        print("Database initialization complete!")
        print("=" * 60)
        print("\nSchema SQL for manual execution:")
        print("-" * 40)
        print(SCHEMA_SQL)


if __name__ == "__main__":
    main()
