# Test Server Setup - Complete

## ✅ Setup Summary

The test server at **test.letsplaydarts.eu** has been successfully configured and is now running.

### What Was Done

1. **Database Setup**
   - Created PostgreSQL database: `dartsdbtest`
   - Ran all Alembic migrations
   - Database is isolated from development and production data

2. **Environment Configuration**
   - Updated `.env.test` with test.letsplaydarts.eu domain
   - Configured WSO2 redirect URIs for test environment
   - Set proper session cookie and security settings

3. **Docker Configuration**
   - Created `docker-compose-test.yml` override file
   - Configured test-specific environment variables
   - Services running with test configuration

4. **SSL Certificates**
   - Verified existing certificates include `*.letsplaydarts.eu`
   - Certificates are valid and working for test.letsplaydarts.eu

5. **Services Status**
   - PostgreSQL: ✅ Running (port 5432)
   - RabbitMQ: ✅ Running (ports 5672, 15672)
   - WSO2 IS: ✅ Running (port 9443)
   - WSO2 APIM: ✅ Running (ports 8280, 8243, 9444)
   - Darts App: ✅ Running with test config
   - API Gateway: ✅ Running with test config
   - Nginx: ✅ Running (ports 80, 443)

## Access Points

- **Main Application**: https://test.letsplaydarts.eu/
- **WSO2 Identity Server**: https://test.letsplaydarts.eu/auth/
- **WSO2 Console**: https://test.letsplaydarts.eu/console/
- **API Gateway**: https://test.letsplaydarts.eu/api/v1/
- **RabbitMQ Management**: http://localhost:15672/ (guest/guest)

## Managing the Test Server

### Start/Stop Services

```bash
# Start all services with test configuration
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d

# Stop services
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml down

# Restart specific service (e.g., app)
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml restart darts-app

# View logs
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml logs -f darts-app
```

### Update Configuration

1. Edit `.env.test` with new values
2. Restart services:
   ```bash
   docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml restart darts-app api-gateway
   ```
3. If nginx needs to reload:
   ```bash
   docker exec darts-nginx nginx -s reload
   ```

### Database Management

```bash
# Access test database
docker exec -it darts-postgres psql -U postgres -d dartsdbtest

# Run migrations
. .venv-test/bin/activate
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head

# Reset test database
docker exec darts-postgres psql -U postgres -c "DROP DATABASE dartsdbtest;"
docker exec darts-postgres psql -U postgres -c "CREATE DATABASE dartsdbtest;"
. .venv-test/bin/activate
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdbtest alembic upgrade head
```

### Check Service Health

```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test app directly
docker exec darts-nginx curl -s http://darts-app:5000/ | head -10

# Test public access
curl -k https://test.letsplaydarts.eu/health

# Check app logs
docker logs --tail 50 darts-app

# Check nginx logs
docker logs --tail 50 darts-nginx
```

## Configuration Files

### Key Files

- `.env.test` - Test environment variables
- `docker-compose-test.yml` - Test-specific Docker overrides
- `docker-compose-wso2.yml` - Base Docker Compose configuration
- `nginx/nginx.conf` - Nginx reverse proxy configuration
- `ssl/cert.pem`, `ssl/key.pem` - SSL certificates

### Test Environment Variables

```bash
ENVIRONMENT=test
APP_DOMAIN=test.letsplaydarts.eu
APP_SCHEME=https
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dartsdbtest
RABBITMQ_EXCHANGE=darts_exchange_test
WSO2_IS_URL=https://test.letsplaydarts.eu/auth
WSO2_CLIENT_ID=z9tDR_MVfS_rHKBlqZ_6Re_TaJga
WSO2_CLIENT_SECRET=lQCbqtHliRy3j_POcCRxm9j7Cj7VqTx6ehRXnNaesUca
TTS_ENABLED=false
FLASK_DEBUG=True
```

## Troubleshooting

### 502 Bad Gateway

1. Check if app is running: `docker ps | grep darts-app`
2. Check app logs: `docker logs darts-app`
3. Reload nginx: `docker exec darts-nginx nginx -s reload`
4. Restart app: `docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml restart darts-app`

### Database Connection Issues

1. Check PostgreSQL: `docker ps | grep postgres`
2. Test connection:
   ```bash
   docker exec darts-postgres psql -U postgres -d dartsdbtest -c "SELECT 1;"
   ```
3. Verify database exists:
   ```bash
   docker exec darts-postgres psql -U postgres -lqt | grep dartsdbtest
   ```

### WSO2 Authentication Issues

1. Check WSO2 IS health:
   ```bash
   curl -k https://localhost:9443/api/health-check/v1.0/health
   ```
2. Verify client credentials in `.env.test`
3. Check WSO2 logs: `docker logs darts-wso2is`

### SSL Certificate Issues

1. Verify certificates:
   ```bash
   openssl x509 -in ssl/cert.pem -noout -text | grep -A 5 "Subject Alternative Name"
   ```
2. Should show: `DNS:*.letsplaydarts.eu`
3. Regenerate if needed:
   ```bash
   bash helpers/generate_ssl_certs.sh letsplaydarts.eu
   ```

## Testing the Configuration

### Quick Health Checks

```bash
# 1. Check main page
curl -k https://test.letsplaydarts.eu/ -I

# 2. Check health endpoint
curl -k https://test.letsplaydarts.eu/health

# 3. Check WSO2 auth redirect
curl -k -L https://test.letsplaydarts.eu/ 2>&1 | grep -i wso2

# 4. Check database
docker exec darts-app python -c "from src.core.database_service import db; print(db.engine.url)"

# 5. Check environment
docker exec darts-app env | grep ENVIRONMENT
```

### Expected Results

- Main page should redirect to `/login` (302)
- Login should redirect to WSO2 authorize endpoint
- Health endpoint should return "healthy"
- Database URL should show `dartsdbtest`
- Environment should be `test`

## Next Steps

1. **Configure WSO2 Client** (if not already done)
   - Log in to WSO2 console: https://test.letsplaydarts.eu/console/
   - Verify OAuth application settings
   - Ensure callback URLs are correct

2. **Test Authentication Flow**
   - Navigate to https://test.letsplaydarts.eu/
   - Should redirect to WSO2 login
   - After login, should redirect back to app

3. **Run Automated Tests**
   ```bash
   # Copy test environment
   cp .env.test .env
   
   # Run tests
   pytest tests/
   ```

4. **Monitor Logs**
   ```bash
   # Watch all logs
   docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml logs -f
   ```

## Documentation

For more information, see:
- [TEST_CONFIGURATION.md](TEST_CONFIGURATION.md) - Comprehensive test setup guide
- [helpers/TEST_SETUP_README.md](../helpers/TEST_SETUP_README.md) - Quick reference
- [TESTING.md](TESTING.md) - General testing documentation

## Status: ✅ READY

The test server is fully configured and ready for use!

**Created**: November 1, 2025  
**Server**: test.letsplaydarts.eu  
**Environment**: Test  
**Database**: dartsdbtest  
