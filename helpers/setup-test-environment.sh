#!/bin/bash
# Setup Test Environment Script
# This script initializes the test environment with database and WSO2 configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

ensure_wso2_schema() {
    local pg_container
    pg_container=$(docker ps --format '{{.Names}}' | grep -E '^darts-postgres$|postgres' | head -n 1)

    if [ -z "$pg_container" ]; then
        echo "⚠ Warning: PostgreSQL Docker container not found. Skipping WSO2 schema verification."
        return
    fi

    echo "Using PostgreSQL container: $pg_container"

    # Ensure required WSO2 databases exist.
    docker exec "$pg_container" psql -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='wso2is_identity'" | grep -q 1 || \
    docker exec "$pg_container" psql -U postgres -d postgres -c "CREATE DATABASE wso2is_identity;" >/dev/null

    docker exec "$pg_container" psql -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='wso2is_shared'" | grep -q 1 || \
    docker exec "$pg_container" psql -U postgres -d postgres -c "CREATE DATABASE wso2is_shared;" >/dev/null

    local um_domain_exists
    um_domain_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_domain');")

    if [ "$um_domain_exists" = "um_domain" ]; then
        echo "✓ WSO2 user store schema already present (um_domain exists)"
        return
    fi

    echo "⚠ WSO2 user store schema is missing; applying official WSO2 PostgreSQL scripts..."

    if [ ! -f "$PROJECT_ROOT/wso2is-7-config/postgresql-shared.sql" ] || [ ! -f "$PROJECT_ROOT/wso2is-7-config/postgresql-identity.sql" ]; then
        echo "✗ Missing required SQL scripts in wso2is-7-config/."
        echo "  Expected files: postgresql-shared.sql and postgresql-identity.sql"
        return 1
    fi

    cat "$PROJECT_ROOT/wso2is-7-config/postgresql-shared.sql" | docker exec -i "$pg_container" psql -v ON_ERROR_STOP=1 -U postgres -d wso2is_shared >/dev/null
    cat "$PROJECT_ROOT/wso2is-7-config/postgresql-identity.sql" | docker exec -i "$pg_container" psql -v ON_ERROR_STOP=1 -U postgres -d wso2is_identity >/dev/null

    echo "✓ WSO2 schema repair completed"
}

echo "=== Setting up Test Environment ==="
echo ""

# Step 1: Check PostgreSQL connection
echo "Step 1: Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    echo "✓ psql command found"
else
    echo "✗ psql command not found. Please install PostgreSQL client."
    echo "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "  macOS: brew install postgresql"
    exit 1
fi

# Step 2: Create test database
echo ""
echo "Step 2: Creating test database 'dartsdbtest'..."
echo "This requires PostgreSQL to be running and accessible."
echo ""

# Check if PostgreSQL is running
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✓ PostgreSQL is running on localhost:5432"
else
    echo "✗ PostgreSQL is not accessible on localhost:5432"
    echo "  Please start PostgreSQL or configure DATABASE_URL in .env.test"
    echo "  To start PostgreSQL (if using Docker):"
    echo "    docker-compose -f docker-compose-wso2.yml up -d postgres"
    exit 1
fi

# Step 2b: Verify and repair WSO2 schema in PostgreSQL (if Docker PostgreSQL is present)
echo ""
echo "Step 2b: Verifying WSO2 schema (um_domain)..."
if command -v docker &> /dev/null; then
    ensure_wso2_schema
else
    echo "⚠ Warning: docker command not found. Skipping WSO2 schema verification."
fi

# Create test database
echo ""
echo "Creating database 'dartsdbtest'..."
echo "Using default credentials (postgres:postgres)"
echo ""

# Try to create the database (ignore error if it already exists)
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'dartsdbtest'" | grep -q 1 || \
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE dartsdbtest;" 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Database 'dartsdbtest' is ready"
else
    echo "⚠ Warning: Could not create database. It may already exist or credentials may be incorrect."
fi

# Step 3: Run database migrations for test database
echo ""
echo "Step 3: Running database migrations for test database..."
echo ""

# Export test database URL temporarily
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dartsdbtest"

# Check if alembic is available
if command -v alembic &> /dev/null; then
    echo "Running Alembic migrations..."
    cd "$PROJECT_ROOT"
    alembic upgrade head
    echo "✓ Database migrations completed"
else
    echo "⚠ Warning: alembic not found. Please install requirements and run migrations manually:"
    echo "  pip install -r requirements.txt"
    echo "  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head"
fi

# Step 4: SSL Certificates
echo ""
echo "Step 4: Checking SSL certificates..."
if [ -f "$PROJECT_ROOT/ssl/cert.pem" ] && [ -f "$PROJECT_ROOT/ssl/key.pem" ]; then
    echo "✓ SSL certificates found in ssl/ directory"
    echo "  Certificate: $PROJECT_ROOT/ssl/cert.pem"
    echo "  Private Key: $PROJECT_ROOT/ssl/key.pem"
    echo ""
    echo "Certificate details:"
    openssl x509 -in "$PROJECT_ROOT/ssl/cert.pem" -noout -subject -dates -ext subjectAltName 2>&1 | head -5
else
    echo "✗ SSL certificates not found. Generating new certificates..."
    bash "$SCRIPT_DIR/generate_ssl_certs.sh" localhost
fi

# Step 5: WSO2 Configuration
echo ""
echo "Step 5: WSO2 Identity Server Configuration (Optional)..."
echo ""
echo "For full integration testing with WSO2, you need to:"
echo "1. Start WSO2 Identity Server:"
echo "   docker-compose -f docker-compose-wso2.yml up -d wso2is"
echo ""
echo "2. Wait for WSO2 to start (may take 2-3 minutes)"
echo ""
echo "3. Configure OAuth2 client for testing:"
echo "   bash helpers/configure-wso2.sh"
echo ""
echo "4. Update WSO2_CLIENT_ID and WSO2_CLIENT_SECRET in .env.test with the generated credentials"
echo ""
echo "Note: For unit tests, WSO2 is typically mocked and this step can be skipped."
echo ""

# Step 6: Environment file
echo ""
echo "Step 6: Test environment file..."
if [ -f "$PROJECT_ROOT/.env.test" ]; then
    echo "✓ Test environment file found: .env.test"
    echo ""
    echo "To use this configuration, run:"
    echo "  cp .env.test .env"
    echo "  # or"
    echo "  export \$(cat .env.test | grep -v '^#' | xargs)"
else
    echo "✗ Test environment file not found: .env.test"
    echo "Please create .env.test based on .env.example"
fi

echo ""
echo "=== Test Environment Setup Complete ==="
echo ""
echo "Summary:"
echo "  - Database: dartsdbtest (PostgreSQL)"
echo "  - SSL Certificates: ssl/ directory"
echo "  - WSO2 Config: .env.test (client_id: test_client_id)"
echo "  - Environment File: .env.test"
echo ""
echo "To run tests:"
echo "  # Using pytest directly"
echo "  pytest tests/"
echo ""
echo "  # Using tox (recommended)"
echo "  tox -e py312"
echo ""
echo "  # With test environment loaded"
echo "  export \$(cat .env.test | grep -v '^#' | xargs)"
echo "  pytest tests/"
echo ""
