-- Fix PostgreSQL Permissions for scamshield user
-- Run this as PostgreSQL superuser (usually 'postgres')

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO scamshield;

-- Grant create privileges on schema
GRANT CREATE ON SCHEMA public TO scamshield;

-- Grant all privileges on database
GRANT ALL PRIVILEGES ON DATABASE scamshield TO scamshield;

-- Grant privileges on all existing tables (if any)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scamshield;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scamshield;

-- Grant privileges on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scamshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scamshield;
