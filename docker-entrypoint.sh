#!/bin/bash
set -e

echo "=================================================="
echo "Darts Application Startup"
echo "Environment: ${ENVIRONMENT:-production}"
echo "Database: ${DATABASE_URL}"
echo "=================================================="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
timeout=30
counter=0
until pg_isready -h postgres -p 5432 -U postgres > /dev/null 2>&1; do
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo "ERROR: PostgreSQL not ready after ${timeout} seconds"
        exit 1
    fi
    echo "PostgreSQL not ready yet, waiting... (${counter}/${timeout})"
    sleep 1
done
echo "✓ PostgreSQL ready"

# Run Alembic migrations
echo "Applying database migrations..."

# Check for multiple heads and show helpful error
if alembic heads | grep -q "^[a-f0-9]"; then
    head_count=$(alembic heads | grep "^[a-f0-9]" | wc -l)
    if [ "$head_count" -gt 1 ]; then
        echo "WARNING: Multiple head revisions detected:"
        alembic heads
        echo ""
        echo "Attempting to upgrade all heads using 'alembic upgrade heads'..."
        if alembic upgrade heads; then
            echo "✓ All migration heads upgraded successfully"
        else
            echo "ERROR: Failed to upgrade migration heads"
            echo "Please resolve the migration branch manually:"
            echo "  1. Check migration history: docker exec darts-app alembic history"
            echo "  2. Merge heads: docker exec darts-app alembic merge heads -m 'merge migration branches'"
            echo "  3. Rebuild container"
            exit 1
        fi
    else
        # Single head, standard upgrade
        if alembic upgrade head; then
            echo "✓ Database migrations applied successfully"
        else
            echo "ERROR: Failed to apply database migrations"
            exit 1
        fi
    fi
else
    echo "ERROR: Could not determine migration heads"
    exit 1
fi

# Verify database schema
echo "Verifying database schema..."
python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    db_name = conn.execute(text('SELECT current_database()')).scalar()
    print(f'✓ Connected to database: {db_name}')
    col = conn.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'gameresults' AND column_name = 'reset_on_miss'\")).scalar()
    if col:
        print('✓ Schema verified: reset_on_miss column exists')
    else:
        print('⚠ Warning: reset_on_miss column not found')
" || echo "⚠ Schema verification failed (non-critical)"

# Start the application (Flask + Socket.IO + eventlet from run.py)
echo "Starting Flask + Socket.IO server..."
exec python run.py
