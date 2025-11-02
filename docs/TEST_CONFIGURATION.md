# Test Environment Configuration Guide

This guide explains how to set up and use the test environment configuration for the Darts Game Server.

## Overview

The test environment is designed for:
- Automated testing (unit, integration, and end-to-end tests)
- Development testing without affecting production or development data
- CI/CD pipeline execution
- Manual testing with realistic configuration

## Quick Start

### 1. Set Up Test Environment

Run the setup script to create the test database and verify configuration:

```bash
bash helpers/setup-test-environment.sh
```

This script will:
- ✓ Check PostgreSQL connectivity
- ✓ Create `dartsdbtest` database
- ✓ Run database migrations
- ✓ Verify SSL certificates
- ✓ Provide WSO2 configuration instructions

### 2. Use Test Configuration

#### Option A: Copy to .env (for manual testing)
```bash
cp .env.test .env
```

#### Option B: Export environment variables (for current session)
```bash
export $(cat .env.test | grep -v '^#' | xargs)
```

#### Option C: Use in tests directly
Most test frameworks (pytest, tox) will load `.env.test` automatically if configured.

### 3. Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with tox (recommended for CI)
tox -e py312
```

## Configuration Details

### Database Configuration

The test environment uses a dedicated PostgreSQL database to prevent conflicts with development data:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest
```

**Key Features:**
- Separate test database (`dartsdbtest`) keeps test data isolated
- Uses default PostgreSQL credentials for local development
- Can be overridden for CI environments

**Database Setup:**

1. **Create the database:**
   ```bash
   # Manually create
   PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE dartsdbtest;"

   # Or use the setup script
   bash helpers/setup-test-environment.sh
   ```

2. **Run migrations:**
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head
   ```

3. **Reset test database (if needed):**
   ```bash
   # Drop and recreate
   PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "DROP DATABASE dartsdbtest;"
   PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE dartsdbtest;"
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head
   ```

### SSL Certificates

The test environment uses HTTPS with self-signed certificates from the `ssl/` directory:

```
FLASK_USE_SSL=True
APP_SCHEME=https
```

**Certificate Details:**
- Location: `ssl/cert.pem` and `ssl/key.pem`
- Valid for: localhost, *.localhost, 127.0.0.1, ::1, letsplaydarts.eu
- Self-signed (development/test only)

**Generate New Certificates:**
```bash
bash helpers/generate_ssl_certs.sh localhost
```

**Important:** Browsers will show security warnings for self-signed certificates. This is expected and safe for local testing.

### WSO2 Identity Server Configuration

The test environment includes WSO2 IS configuration for authentication testing:

```
WSO2_IS_URL=https://localhost:9443
WSO2_CLIENT_ID=test_client_id
WSO2_CLIENT_SECRET=test_client_secret
WSO2_IS_VERIFY_SSL=False
```

**Setup WSO2 for Testing:**

1. **Start WSO2 Identity Server:**
   ```bash
   docker-compose -f docker-compose-wso2.yml up -d wso2is
   ```

2. **Wait for startup (2-3 minutes):**
   ```bash
   # Check health
   curl -k https://localhost:9443/api/health-check/v1.0/health
   ```

3. **Configure OAuth2 client:**
   ```bash
   bash helpers/configure-wso2.sh
   ```

4. **Update credentials in `.env.test`:**
   - Copy the `client_id` and `client_secret` from the configuration output
   - Update `WSO2_CLIENT_ID` and `WSO2_CLIENT_SECRET` in `.env.test`

**Note:** For unit tests, WSO2 is typically mocked and this step can be skipped.

### Text-to-Speech (TTS)

TTS is disabled in the test environment to avoid timing issues and external dependencies:

```
TTS_ENABLED=false
TTS_VOLUME=0.0
```

This prevents audio playback during automated tests while maintaining compatibility with TTS-related code.

### RabbitMQ Configuration

The test environment uses a separate RabbitMQ exchange to isolate test messages:

```
RABBITMQ_EXCHANGE=darts_exchange_test
```

**Start RabbitMQ for testing:**
```bash
docker-compose -f docker-compose-wso2.yml up -d rabbitmq
```

**Access RabbitMQ Management UI:**
- URL: http://localhost:15672
- Username: guest
- Password: guest

## Environment Variables Reference

### Core Settings
| Variable | Value | Description |
|----------|-------|-------------|
| `ENVIRONMENT` | `development` | Environment type (test uses development settings) |
| `APP_DOMAIN` | `localhost:5000` | Application domain |
| `APP_SCHEME` | `https` | URL scheme (https for SSL) |
| `FLASK_DEBUG` | `True` | Enable debug mode for detailed error messages |

### Database
| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/dartsdbtest` | Test database connection string |

### SSL/Security
| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_USE_SSL` | `True` | Enable SSL |
| `SESSION_COOKIE_SECURE` | `False` | Allow cookies over self-signed HTTPS |
| `SECRET_KEY` | `test-secret-key-for-automated-testing` | Flask secret key (test only) |

### WSO2 Identity Server
| Variable | Value | Description |
|----------|-------|-------------|
| `WSO2_IS_URL` | `https://localhost:9443` | WSO2 Identity Server URL |
| `WSO2_CLIENT_ID` | `test_client_id` | OAuth2 client ID (update after WSO2 setup) |
| `WSO2_CLIENT_SECRET` | `test_client_secret` | OAuth2 client secret (update after WSO2 setup) |
| `WSO2_IS_VERIFY_SSL` | `False` | Disable SSL verification for self-signed certs |
| `AUTH_DISABLED` | `False` | Keep auth enabled to test decorators |

### RabbitMQ
| Variable | Value | Description |
|----------|-------|-------------|
| `RABBITMQ_HOST` | `localhost` | RabbitMQ host |
| `RABBITMQ_EXCHANGE` | `darts_exchange_test` | Dedicated test exchange |

### Text-to-Speech
| Variable | Value | Description |
|----------|-------|-------------|
| `TTS_ENABLED` | `false` | Disable TTS in tests |

## Testing Workflows

### Unit Tests
Unit tests use in-memory SQLite database (configured in `tests/conftest.py`):

```bash
pytest tests/unit/
```

### Integration Tests
Integration tests can use the PostgreSQL test database:

```bash
# Set test environment
export $(cat .env.test | grep -v '^#' | xargs)

# Run integration tests
pytest tests/integration/
```

### Full Test Suite with Tox
```bash
# Run tests on all supported Python versions
tox

# Run tests on specific Python version
tox -e py312

# Run linting
tox -e lint

# Run type checking
tox -e type

# Run security checks
tox -e security
```

### CI/CD Integration
In CI environments, set environment variables or use `.env.test` directly:

```yaml
# Example GitHub Actions
- name: Run tests
  env:
    DATABASE_URL: postgresql://postgres:postgres@localhost:5432/dartsdbtest
  run: |
    pytest tests/
```

## Troubleshooting

### Database Connection Issues

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL (Docker)
docker-compose -f docker-compose-wso2.yml up -d postgres

# Or start locally
sudo service postgresql start
```

### SSL Certificate Warnings

**Problem:** Browser shows SSL warning

**Solution:** This is expected for self-signed certificates. Click "Advanced" → "Proceed to localhost" to bypass the warning for testing.

### WSO2 Connection Issues

**Problem:** `Connection refused to https://localhost:9443`

**Solution:**
```bash
# Start WSO2 Identity Server
docker-compose -f docker-compose-wso2.yml up -d wso2is

# Wait for startup (check logs)
docker logs -f darts-wso2is

# Verify health
curl -k https://localhost:9443/api/health-check/v1.0/health
```

### Test Database Not Found

**Problem:** `database "dartsdbtest" does not exist`

**Solution:**
```bash
# Create the database
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE dartsdbtest;"

# Run migrations
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head
```

## Best Practices

1. **Isolate Test Data**: Always use the dedicated test database (`dartsdbtest`)
2. **Clean State**: Reset test database between major test runs if needed
3. **Mock External Services**: Mock WSO2, RabbitMQ for unit tests; use real services for integration tests
4. **CI Configuration**: Keep CI environment variables in sync with `.env.test`
5. **SSL Certificates**: Regenerate SSL certificates if expired (valid for 365 days)

## Related Files

- `.env.test` - Test environment configuration
- `helpers/setup-test-environment.sh` - Test environment setup script
- `helpers/generate_ssl_certs.sh` - SSL certificate generation
- `helpers/configure-wso2.sh` - WSO2 configuration script
- `tests/conftest.py` - Pytest configuration and fixtures
- `tox.ini` - Tox test configuration
- `docker-compose-wso2.yml` - Docker services for testing

## See Also

- [TESTING.md](TESTING.md) - General testing documentation
- [SSL_CONFIGURATION.md](SSL_CONFIGURATION.md) - SSL setup details
- [WSO2_SETUP_GUIDE.md](WSO2_SETUP_GUIDE.md) - WSO2 configuration guide
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup guide
