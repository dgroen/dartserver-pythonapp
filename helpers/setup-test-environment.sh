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
    um_domain_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT to_regclass('public.um_domain');")

    if [ "$um_domain_exists" = "um_domain" ]; then
        echo "✓ WSO2 user store schema already present (um_domain exists)"
        return
    fi

    echo "⚠ WSO2 user store schema is missing; creating required tables..."

    docker exec -i "$pg_container" psql -U postgres -d wso2is_identity <<'SQL'
CREATE TABLE IF NOT EXISTS um_domain (
    UM_DOMAIN_ID SERIAL NOT NULL,
    UM_DOMAIN_NAME VARCHAR(255) NOT NULL UNIQUE,
    UM_CREATED_DATE BIGINT,
    PRIMARY KEY (UM_DOMAIN_ID)
);

CREATE TABLE IF NOT EXISTS um_tenant (
    UM_ID SERIAL NOT NULL,
    UM_DOMAIN_NAME VARCHAR(255) NOT NULL,
    UM_CREATED_DATE BIGINT,
    UM_EMAIL VARCHAR(255),
    UM_ACTIVE BOOLEAN,
    PRIMARY KEY (UM_ID),
    FOREIGN KEY (UM_DOMAIN_NAME) REFERENCES um_domain(UM_DOMAIN_NAME)
);

CREATE TABLE IF NOT EXISTS um_user (
    UM_ID INTEGER NOT NULL,
    UM_USER_ID VARCHAR(255) NOT NULL,
    UM_USER_NAME VARCHAR(255) NOT NULL,
    UM_DOMAIN_ID INTEGER,
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID),
    UNIQUE (UM_USER_NAME, UM_TENANT_ID)
);

CREATE TABLE IF NOT EXISTS um_user_password (
    UM_ID SERIAL NOT NULL,
    UM_USER_ID VARCHAR(255) NOT NULL,
    UM_PASSWORD VARCHAR(255),
    UM_SALT_VALUE VARCHAR(31),
    UM_REQUIRE_CHANGE BOOLEAN,
    UM_CHANGED_TIME BIGINT,
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID),
    UNIQUE (UM_USER_ID, UM_TENANT_ID)
);

CREATE TABLE IF NOT EXISTS um_role (
    UM_ID SERIAL NOT NULL,
    UM_ROLE_ID VARCHAR(255) NOT NULL,
    UM_ROLE_NAME VARCHAR(255) NOT NULL,
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID),
    UNIQUE (UM_ROLE_NAME, UM_TENANT_ID)
);

CREATE TABLE IF NOT EXISTS um_user_role (
    UM_ID SERIAL NOT NULL,
    UM_USER_ID VARCHAR(255),
    UM_ROLE_ID VARCHAR(255),
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID)
);

CREATE TABLE IF NOT EXISTS um_permission (
    UM_ID SERIAL NOT NULL,
    UM_RESOURCE_ID VARCHAR(255) NOT NULL,
    UM_ACTION VARCHAR(255) NOT NULL,
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID),
    UNIQUE (UM_RESOURCE_ID, UM_ACTION, UM_TENANT_ID)
);

CREATE TABLE IF NOT EXISTS um_role_permission (
    UM_ID SERIAL NOT NULL,
    UM_PERMISSION_ID INTEGER,
    UM_ROLE_ID VARCHAR(255),
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID)
);

CREATE TABLE IF NOT EXISTS um_user_attribute (
    UM_ID SERIAL NOT NULL,
    UM_USER_ID VARCHAR(255),
    UM_ATTR_NAME VARCHAR(255),
    UM_ATTR_VALUE TEXT,
    UM_PROFILE_ID VARCHAR(255),
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID)
);
SQL

    docker exec -i "$pg_container" psql -U postgres -d wso2is_shared <<'SQL'
CREATE TABLE IF NOT EXISTS shared_user (
    UM_ID SERIAL NOT NULL,
    UM_USER_ID VARCHAR(255) NOT NULL,
    UM_USER_NAME VARCHAR(255) NOT NULL,
    UM_TENANT_ID INTEGER,
    PRIMARY KEY (UM_ID)
);
SQL

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
