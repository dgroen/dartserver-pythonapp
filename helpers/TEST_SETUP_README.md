# Test Environment Setup

This directory contains helper scripts for setting up and configuring the test environment.

## Quick Setup

Run the automated test environment setup:

```bash
bash helpers/setup-test-environment.sh
```

This script will:
1. ✓ Check PostgreSQL connectivity
2. ✓ Create `dartsdbtest` database
3. ✓ Run database migrations
4. ✓ Verify SSL certificates
5. ✓ Provide WSO2 configuration instructions

## Configuration Files

### Test Environment
- **`.env.test`** - Test environment configuration file
  - Database: `dartsdbtest` (PostgreSQL)
  - SSL: Enabled with self-signed certificates
  - WSO2: Local test credentials
  - TTS: Disabled for tests
  - RabbitMQ: Test exchange

### SSL Certificates
Located in `ssl/` directory:
- `ssl/cert.pem` - SSL certificate (self-signed)
- `ssl/key.pem` - SSL private key
- `ssl/openssl.cnf` - OpenSSL configuration

Valid for: localhost, *.localhost, 127.0.0.1, letsplaydarts.eu

To regenerate:
```bash
bash helpers/generate_ssl_certs.sh localhost
```

### WSO2 Configuration
For integration tests with WSO2:

1. Start WSO2 Identity Server:
   ```bash
   docker-compose -f docker-compose-wso2.yml up -d wso2is
   ```

2. Configure OAuth2 client:
   ```bash
   bash helpers/configure-wso2.sh
   ```

3. Update credentials in `.env.test`:
   - `WSO2_CLIENT_ID`
   - `WSO2_CLIENT_SECRET`

## Running Tests

### Quick Test Run
```bash
# Load test environment
cp .env.test .env

# Run all tests
pytest tests/

# Run specific tests
pytest tests/unit/
pytest tests/integration/
```

### Using Tox (Recommended for CI)
```bash
# Run tests on all Python versions
tox

# Run specific version
tox -e py312

# Run linting
tox -e lint
```

### Manual Environment Setup
```bash
# Export test environment variables
export $(cat .env.test | grep -v '^#' | xargs)

# Run tests
pytest tests/
```

## Test Database

### Create Test Database
```bash
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE dartsdbtest;"
```

### Run Migrations
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head
```

### Reset Test Database
```bash
# Drop database
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "DROP DATABASE dartsdbtest;"

# Recreate and migrate
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE dartsdbtest;"
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head
```

## Troubleshooting

### PostgreSQL Not Running
```bash
# Check status
pg_isready -h localhost -p 5432

# Start with Docker
docker-compose -f docker-compose-wso2.yml up -d postgres
```

### WSO2 Connection Issues
```bash
# Start WSO2
docker-compose -f docker-compose-wso2.yml up -d wso2is

# Check logs
docker logs -f darts-wso2is

# Verify health
curl -k https://localhost:9443/api/health-check/v1.0/health
```

## Documentation

For complete documentation, see:
- **[docs/TEST_CONFIGURATION.md](../docs/TEST_CONFIGURATION.md)** - Comprehensive test environment guide
- **[docs/TESTING.md](../docs/TESTING.md)** - General testing documentation
- **[docs/SSL_CONFIGURATION.md](../docs/SSL_CONFIGURATION.md)** - SSL setup details
- **[docs/WSO2_SETUP_GUIDE.md](../docs/WSO2_SETUP_GUIDE.md)** - WSO2 configuration guide
