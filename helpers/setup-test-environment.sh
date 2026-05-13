#!/bin/bash
# Setup Test Environment Script
# This script initializes the test environment with database and WSO2 configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WSO2_SCHEMA_RESEEDED=false
PRESERVE_DB_DATA="${PRESERVE_DB_DATA:-false}"

sync_test_env_file() {
    local env_test_file="$PROJECT_ROOT/.env.test"
    local env_file="$PROJECT_ROOT/.env"

    if [ "${APPLY_TEST_ENV_FILE:-false}" != "true" ]; then
        echo "ℹ Skipping .env.test -> .env sync (set APPLY_TEST_ENV_FILE=true to enable for local unit/integration tests)"
        return
    fi

    if [ ! -f "$env_test_file" ]; then
        echo "✗ Test environment file not found: .env.test"
        echo "Please create .env.test based on .env.example"
        return 1
    fi

    if [ -f "$env_file" ] && [ "${OVERWRITE_ENV_FILE:-false}" != "true" ]; then
        echo "ℹ Keeping existing .env (set OVERWRITE_ENV_FILE=true to replace it from .env.test)"
    else
        cp "$env_test_file" "$env_file"
        echo "✓ Applied .env.test to .env"
    fi

    # Export .env values so helper scripts can use them in this shell session.
    set -a
    # shellcheck disable=SC1091
    source "$env_file"
    set +a
}

run_wso2_bootstrap() {
    local bootstrap_script="$SCRIPT_DIR/bootstrap_wso2_test_env.sh"
    # Prefer direct localhost port for health checks so Docker-internal hostnames
    # (e.g. wso2is:9443) do not cause indefinite hangs when run from the host.
    local wso2_url="https://localhost:9443"
    local health_ready=false
    local attempt

    if [ "${SKIP_WSO2_BOOTSTRAP:-false}" = "true" ]; then
        echo "ℹ Skipping WSO2 bootstrap because SKIP_WSO2_BOOTSTRAP=true"
        return
    fi

    if [ ! -f "$bootstrap_script" ]; then
        echo "⚠ Warning: bootstrap script not found: $bootstrap_script"
        return
    fi

    if ! command -v docker &> /dev/null || ! docker ps --format '{{.Names}}' | grep -q '^darts-wso2is$'; then
        echo "⚠ Warning: darts-wso2is container is not running. Skipping automatic WSO2 bootstrap."
        echo "  Start it with: docker-compose -f docker-compose-wso2.yml up -d wso2is"
        return
    fi

    if [ "$WSO2_SCHEMA_RESEEDED" = "true" ]; then
        echo "ℹ WSO2 databases were reseeded; restarting WSO2 services to reload schema..."
        docker restart darts-wso2is >/dev/null
        if docker ps --format '{{.Names}}' | grep -q '^darts-wso2apim$'; then
            docker restart darts-wso2apim >/dev/null
        fi
    fi

    for attempt in $(seq 1 60); do
        if curl -k -s -f --connect-timeout 3 --max-time 8 "${wso2_url%/}/api/health-check/v1.0/health" > /dev/null 2>&1; then
            health_ready=true
            break
        fi
        sleep 2
    done

    if [ "$health_ready" != "true" ]; then
        echo "⚠ Warning: WSO2 health endpoint not ready at ${wso2_url}. Skipping automatic bootstrap."
        echo "  Re-run later, or set SKIP_WSO2_BOOTSTRAP=true to suppress this check."
        return
    fi

    echo "Running WSO2 bootstrap workflow..."
    (
        cd "$PROJECT_ROOT"
        if [ -f .env ]; then
            set -a
            # shellcheck disable=SC1091
            source .env
            set +a
        fi
        # Force localhost for management API calls so Docker-internal hostnames
        # (wso2is:9443) are not used when the script runs on the host.
        WSO2_IS_INTERNAL_URL=https://localhost:9443 bash "$bootstrap_script"
    )
    echo "✓ WSO2 bootstrap completed"
}

repair_wso2_claim_mappings() {
        local pg_container
        pg_container=$(docker ps --format '{{.Names}}' | grep -E '^darts-postgres$|postgres' | head -n 1)

        if [ -z "$pg_container" ]; then
                echo "⚠ Warning: PostgreSQL Docker container not found. Skipping WSO2 claim repair."
                return
        fi

        echo "Using PostgreSQL container for claim repair: $pg_container"

        echo "⏳ Waiting for WSO2 claim rows to become available..."
        local claim_wait_max=60
        local claim_wait_count=0
        local username_claim_ready=0
        local addresses_claim_ready=0

        while [ "$claim_wait_count" -lt "$claim_wait_max" ]; do
                username_claim_ready=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT COUNT(*) FROM idn_claim WHERE claim_uri = 'http://wso2.org/claims/username';" | tr -d '[:space:]')
                addresses_claim_ready=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT COUNT(*) FROM idn_claim WHERE claim_uri = 'http://wso2.org/claims/addresses';" | tr -d '[:space:]')
                if [ "$username_claim_ready" -ge 1 ] && [ "$addresses_claim_ready" -ge 1 ]; then
                        break
                fi
                claim_wait_count=$((claim_wait_count + 1))
                sleep 1
        done

        if [ "$username_claim_ready" -lt 1 ] || [ "$addresses_claim_ready" -lt 1 ]; then
                echo "✗ WSO2 claim rows did not become available in time"
                echo "  - username claim rows: $username_claim_ready"
                echo "  - addresses claim rows: $addresses_claim_ready"
                return 1
        fi

        echo "🛠️  Repairing WSO2 claim mappings..."
        docker exec -i "$pg_container" psql -U postgres -d wso2is_identity -v ON_ERROR_STOP=1 >/dev/null <<'SQL'
INSERT INTO idn_claim_mapped_attribute (local_claim_id, user_store_domain_name, attribute_name, tenant_id)
SELECT c.id, 'PRIMARY', 'uid', c.tenant_id
FROM idn_claim c
WHERE c.claim_uri = 'http://wso2.org/claims/username'
    AND NOT EXISTS (
        SELECT 1
        FROM idn_claim_mapped_attribute m
        WHERE m.local_claim_id = c.id
            AND m.user_store_domain_name = 'PRIMARY'
            AND m.tenant_id = c.tenant_id
    );

INSERT INTO idn_claim_mapped_attribute (local_claim_id, user_store_domain_name, attribute_name, tenant_id)
SELECT c.id, 'PRIMARY', 'addresses', c.tenant_id
FROM idn_claim c
WHERE c.claim_uri = 'http://wso2.org/claims/addresses'
    AND NOT EXISTS (
        SELECT 1
        FROM idn_claim_mapped_attribute m
        WHERE m.local_claim_id = c.id
            AND m.user_store_domain_name = 'PRIMARY'
            AND m.tenant_id = c.tenant_id
    );
SQL
        echo "✓ WSO2 claim mappings repaired"
}

ensure_wso2_schema() {
    local pg_container
    local shared_db_exists
    local identity_db_exists
    local shared_table_count
    local identity_table_count
    pg_container=$(docker ps --format '{{.Names}}' | grep -E '^darts-postgres$|postgres' | head -n 1)

    if [ -z "$pg_container" ]; then
        echo "⚠ Warning: PostgreSQL Docker container not found. Skipping WSO2 schema verification."
        return
    fi

    echo "Using PostgreSQL container: $pg_container"

    # Ensure required WSO2 databases exist (non-destructive).
    shared_db_exists=$(docker exec "$pg_container" psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='wso2is_shared';" | tr -d '[:space:]')
    identity_db_exists=$(docker exec "$pg_container" psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='wso2is_identity';" | tr -d '[:space:]')

    if [ "$shared_db_exists" != "1" ]; then
        echo "ℹ Creating missing database wso2is_shared"
        docker exec "$pg_container" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE wso2is_shared;" >/dev/null
    fi

    if [ "$identity_db_exists" != "1" ]; then
        echo "ℹ Creating missing database wso2is_identity"
        docker exec "$pg_container" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE wso2is_identity;" >/dev/null
    fi

    shared_table_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d '[:space:]')
    identity_table_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d '[:space:]')

    local um_domain_exists
    um_domain_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_domain');")

    local um_role_exists
    um_role_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_role');")

    local idn_claim_exists
    idn_claim_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT to_regclass('public.idn_claim');")

    local role_count
    role_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM um_role WHERE um_role_name IN ('admin', 'everyone');" 2>/dev/null || echo "0")

    if [ ! -f "$PROJECT_ROOT/wso2is-7-config/postgresql-shared.sql" ] || [ ! -f "$PROJECT_ROOT/wso2is-7-config/postgresql-identity.sql" ]; then
        echo "✗ Missing required SQL scripts in wso2is-7-config/."
        echo "  Expected files: postgresql-shared.sql and postgresql-identity.sql"
        return 1
    fi

    # Initialize schema only for EMPTY databases. If a database already contains
    # entities but required WSO2 tables are missing, fail safe and do not mutate.
    if [ "$um_domain_exists" != "um_domain" ]; then
        if [ "$shared_table_count" = "0" ]; then
            echo "ℹ Initializing empty wso2is_shared schema from postgresql-shared.sql"
            cat "$PROJECT_ROOT/wso2is-7-config/postgresql-shared.sql" | docker exec -i "$pg_container" psql -v ON_ERROR_STOP=1 -U postgres -d wso2is_shared >/dev/null
            um_domain_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_domain');")
            um_role_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_role');")
            role_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM um_role WHERE um_role_name IN ('admin', 'everyone');" 2>/dev/null || echo "0")
        else
            echo "⚠ Existing wso2is_shared database is partially initialized."
            echo "  - table count: $shared_table_count"
            echo "  - um_domain table: $um_domain_exists"
            echo "⚠ Skipping full SQL replay for safety (contains DROP statements)."
            um_domain_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_domain');")
            um_role_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_role');")
            role_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM um_role WHERE um_role_name IN ('admin', 'everyone');" 2>/dev/null || echo "0")
        fi
    fi

    if [ "$idn_claim_exists" != "idn_claim" ]; then
        if [ "$identity_table_count" = "0" ]; then
            echo "ℹ Initializing empty wso2is_identity schema from postgresql-identity.sql"
            cat "$PROJECT_ROOT/wso2is-7-config/postgresql-identity.sql" | docker exec -i "$pg_container" psql -v ON_ERROR_STOP=1 -U postgres -d wso2is_identity >/dev/null
            idn_claim_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT to_regclass('public.idn_claim');")
        else
            echo "⚠ Existing wso2is_identity database is partially initialized."
            echo "  - table count: $identity_table_count"
            echo "  - idn_claim table: $idn_claim_exists"
            echo "⚠ Skipping full SQL replay for safety (contains DROP statements)."
            idn_claim_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_identity -tAc "SELECT to_regclass('public.idn_claim');")
        fi
    fi

    # Non-destructive repair: ensure um_hybrid_role_audience has an entry for every
    # row in um_hybrid_role. WSO2 IS 7.x JOINs these tables to resolve role audiences;
    # if um_hybrid_role_audience is empty while um_hybrid_role has entries, WSO2 cannot
    # find the everyone role → AuthorizationHandler fails → all SCIM calls return 400.
    if [ "$um_role_exists" = "um_role" ]; then
        local hybrid_role_table_exists
        hybrid_role_table_exists=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_hybrid_role_audience');")
        if [ "$hybrid_role_table_exists" = "um_hybrid_role_audience" ]; then
            local audience_count
            audience_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM um_hybrid_role_audience;" | tr -d '[:space:]')
            local hybrid_role_count
            hybrid_role_count=$(docker exec "$pg_container" psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM um_hybrid_role;" | tr -d '[:space:]')
            if [ "$audience_count" = "0" ] && [ "$hybrid_role_count" -gt "0" ]; then
                echo "⚠ Detected empty um_hybrid_role_audience with $hybrid_role_count orphaned hybrid roles — repairing..."
                docker exec "$pg_container" psql -U postgres -d wso2is_shared -v ON_ERROR_STOP=1 <<'REPAIR_SQL'
DO $$
DECLARE
  v_org_id TEXT;
BEGIN
  SELECT um_id INTO v_org_id FROM um_org WHERE um_org_name = 'Super' AND um_org_type = 'TENANT' LIMIT 1;
  IF v_org_id IS NULL THEN
    RAISE WARNING 'Super org not found in um_org; skipping um_hybrid_role_audience repair';
  ELSE
    INSERT INTO um_hybrid_role_audience (um_id, um_audience, um_audience_id)
    SELECT r.um_audience_ref_id, 'organization', v_org_id
    FROM um_hybrid_role r
    WHERE NOT EXISTS (
      SELECT 1 FROM um_hybrid_role_audience a WHERE a.um_id = r.um_audience_ref_id
    )
    GROUP BY r.um_audience_ref_id;
    RAISE NOTICE 'um_hybrid_role_audience repair complete';
  END IF;
END $$;
REPAIR_SQL
                echo "✓ um_hybrid_role_audience repaired"
            fi
        fi
    fi

    if [ "$um_domain_exists" = "um_domain" ] && [ "$um_role_exists" = "um_role" ] && [ "$role_count" -ge 1 ] && [ "$idn_claim_exists" = "idn_claim" ]; then
        echo "✓ WSO2 user store schema is present and core roles exist"
    else
        echo "⚠ WSO2 schema/role bootstrap is incomplete"
        echo "  - um_domain table: $um_domain_exists"
        echo "  - um_role table: $um_role_exists"
        echo "  - idn_claim table: $idn_claim_exists"
        echo "  - core role count (admin/everyone): $role_count"
        echo "⚠ Continuing in non-destructive mode after best-effort repair attempt."
        echo "  Some schema entities are still missing; downstream bootstrap may repair additional data."
        return 0
    fi

    return
}

if [ "${WSO2_POST_START_REPAIR:-false}" = "true" ]; then
        repair_wso2_claim_mappings
        exit 0
fi

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

# Step 5: Environment file (optional, for local test runs)
echo ""
echo "Step 5: Applying test environment file (optional)..."
sync_test_env_file

# Step 6: WSO2 Configuration
echo ""
echo "Step 6: Applying WSO2 Identity Server bootstrap..."
run_wso2_bootstrap

echo ""
echo "=== Test Environment Setup Complete ==="
echo ""
echo "Summary:"
echo "  - Database: dartsdbtest (PostgreSQL)"
echo "  - SSL Certificates: ssl/ directory"
echo "  - WSO2 Config: bootstrap_wso2_test_env.sh (if WSO2 is reachable)"
echo "  - Environment File: .env.test is unit-test only; apply to .env only with APPLY_TEST_ENV_FILE=true"
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
