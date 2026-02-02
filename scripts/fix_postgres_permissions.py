#!/usr/bin/env python
"""
Fix PostgreSQL permissions for scamshield user.
This script grants necessary permissions to create tables.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

def fix_permissions():
    """Grant necessary permissions to scamshield user."""
    print("=" * 60)
    print("Fixing PostgreSQL Permissions")
    print("=" * 60)
    print()
    
    # Get connection string
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("[ERROR] POSTGRES_URL not found in environment")
        return False
    
    # Connect as superuser (modify URL to use postgres user)
    # Extract parts from URL
    if "postgresql://" in postgres_url:
        # Replace user in URL with 'postgres'
        if "@" in postgres_url:
            parts = postgres_url.split("@")
            # Try to connect as postgres user
            superuser_url = postgres_url.replace("scamshield:password", "postgres:postgres")
        else:
            superuser_url = postgres_url.replace("scamshield", "postgres")
    else:
        print("[ERROR] Invalid POSTGRES_URL format")
        return False
    
    print("Attempting to connect as superuser to grant permissions...")
    print("(You may need to enter postgres password)")
    print()
    
    try:
        # Try to connect as postgres user
        engine = create_engine(superuser_url)
        
        permissions_sql = [
            "GRANT USAGE ON SCHEMA public TO scamshield",
            "GRANT CREATE ON SCHEMA public TO scamshield",
            "GRANT ALL PRIVILEGES ON DATABASE scamshield TO scamshield",
            "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scamshield",
            "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scamshield",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scamshield",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scamshield",
        ]
        
        with engine.connect() as conn:
            for sql in permissions_sql:
                try:
                    conn.execute(text(sql))
                    print(f"  [OK] {sql[:50]}...")
                except Exception as e:
                    error_str = str(e).lower()
                    if "already" in error_str or "duplicate" in error_str:
                        print(f"  [SKIP] {sql[:50]}... (already granted)")
                    else:
                        print(f"  [WARNING] {sql[:50]}... - {e}")
            conn.commit()
        
        print()
        print("=" * 60)
        print("[SUCCESS] Permissions granted!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[ERROR] Failed to grant permissions")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Manual fix:")
        print("1. Connect to PostgreSQL as superuser:")
        print("   psql -U postgres -d scamshield")
        print()
        print("2. Run these commands:")
        print("   GRANT USAGE ON SCHEMA public TO scamshield;")
        print("   GRANT CREATE ON SCHEMA public TO scamshield;")
        print("   GRANT ALL PRIVILEGES ON DATABASE scamshield TO scamshield;")
        print("   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scamshield;")
        print("   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scamshield;")
        return False

if __name__ == "__main__":
    success = fix_permissions()
    sys.exit(0 if success else 1)
