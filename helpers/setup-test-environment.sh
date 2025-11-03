#!/bin/bash
# Setup Test Environment Script
# This script initializes the test environment with database and WSO2 configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
