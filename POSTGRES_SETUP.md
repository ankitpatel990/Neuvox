# PostgreSQL Setup Guide

## Current Status

✅ **Code is configured to use PostgreSQL** - The application will:
- Connect to PostgreSQL on startup
- Create tables automatically if they don't exist
- Save all conversations, messages, and extracted intelligence

❌ **Connection is failing** - Error: `password authentication failed for user "scamshield"`

## Quick Setup Options

### Option 1: Docker Compose (Easiest)

1. Make sure Docker Desktop is running
2. Start PostgreSQL:
   ```bash
   docker-compose up -d postgres
   ```
3. Wait for it to be ready (about 10 seconds)
4. Run the test script:
   ```bash
   python scripts/test_postgres_connection.py
   ```

### Option 2: Manual PostgreSQL Setup

1. **Install PostgreSQL** (if not installed):
   - Windows: Download from https://www.postgresql.org/download/windows/
   - Or use: `choco install postgresql` (if you have Chocolatey)

2. **Create database and user**:
   ```sql
   -- Connect to PostgreSQL as superuser (usually 'postgres')
   psql -U postgres
   
   -- Then run:
   CREATE DATABASE scamshield;
   CREATE USER scamshield WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE scamshield TO scamshield;
   \q
   ```

3. **Update .env file**:
   ```
   POSTGRES_URL=postgresql://scamshield:password@localhost:5432/scamshield
   ```

4. **Test connection**:
   ```bash
   python scripts/test_postgres_connection.py
   ```

### Option 3: Use Cloud PostgreSQL (For Deployment)

1. **Render PostgreSQL** (Free tier):
   - Go to https://render.com
   - Create new PostgreSQL service
   - Copy the connection string
   - Update `.env`:
     ```
     POSTGRES_URL=<your_render_postgres_url>
     ```

2. **Supabase** (Free tier):
   - Go to https://supabase.com
   - Create new project
   - Get connection string from Settings > Database
   - Update `.env`:
     ```
     POSTGRES_URL=<your_supabase_postgres_url>
     ```

## Verify Setup

After setting up PostgreSQL, run:

```bash
python scripts/test_postgres_connection.py
```

You should see:
```
[SUCCESS] PostgreSQL is configured and working!
```

## Tables Created Automatically

When the app starts, it will create:
- `conversations` - Session metadata
- `messages` - All conversation messages
- `extracted_intelligence` - UPI IDs, bank accounts, etc.

## Troubleshooting

### Error: "password authentication failed"
- Check if PostgreSQL is running: `pg_isready` or check services
- Verify username/password in `.env` matches your PostgreSQL setup
- Try connecting manually: `psql -U scamshield -d scamshield`

### Error: "database does not exist"
- Create the database: `CREATE DATABASE scamshield;`
- Or update `POSTGRES_URL` to use an existing database

### Error: "connection refused"
- PostgreSQL server is not running
- Start it: `pg_ctl start` or use Docker Compose

## Current Configuration

Your `.env` file should have:
```
POSTGRES_URL=postgresql://scamshield:password@localhost:5432/scamshield
```

Make sure this matches your actual PostgreSQL setup!
