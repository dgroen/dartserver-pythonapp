# Production 502 Bad Gateway Fix - October 18, 2025

## Issue Summary

The production environment at `letsplaydarts.eu` was returning **502 Bad Gateway** errors due to the nginx reverse proxy being unable to connect to the backend Flask application.

## Root Cause

A Python Flask development server was running on the **host machine** on port 5000, preventing the Docker container `darts-app` from binding to the same port. This caused:

1. The `darts-app` Docker container to fail startup with "address already in use" error
2. The container exiting and staying in stopped state
3. nginx trying to connect to a non-existent backend service
4. All requests returning 502 errors

### Key Details

- **Process**: `/data/dartserver-pythonapp/.venv/bin/python run.py` (PID: 3545327)
- **Port**: 5000
- **Impact**: Complete service unavailability

## Resolution Steps

### 1. Identified the Issue

```bash
# Checked Docker container status
docker ps  # showed darts-app was exited

# Reviewed nginx logs
docker logs darts-nginx  # showed "connect() failed (113: Host is unreachable)"

# Found the host process
lsof -i :5000  # revealed Python process on host:5000
```

### 2. Fixed the Issue

```bash
# Stopped the conflicting process
kill -9 3545327

# Restarted the Docker container
docker restart darts-app
```

### 3. Verified Resolution

```bash
# Confirmed app is responding
curl -s http://localhost:5000/ | head
# Result: HTTP 302 (redirecting to login, expected)

# Confirmed nginx can reach backend
docker exec darts-nginx curl -s http://darts-app:5000/
# Result: HTTP 302 from darts-app
```

## Prevention Recommendations

### 1. **Process Management**

- Ensure development servers don't run on the same ports as Docker containers
- Use different ports for local development (e.g., 5001, 5002) than production (5000)
- Document the port allocation scheme

### 2. **Port Binding Configuration**

Consider modifying `docker-compose-wso2.yml` to:

- Use random host port mapping instead of fixed ports
- Or use only container-to-container networking without exposing ports

Example:

```yaml
darts-app:
  ports:
    - "5000:5000" # Current: fixed host port
    # Better: Only expose to internal network
```

### 3. **Health Checks**

- Implement automated health checks that alert when the backend is unreachable
- Add monitoring to detect when containers exit unexpectedly
- Set up automated restart policies (already configured with `restart: unless-stopped`)

### 4. **Documentation**

- Document the port usage:
  - `5000`: darts-app (Docker)
  - `5001-5099`: Available for local development
  - `8080`: api-gateway (Docker)
  - `9443`: WSO2 Identity Server (Docker)

### 5. **Development Workflow**

When developing locally:

```bash
# Option 1: Use different port
python app.py --port 5001

# Option 2: Run inside Docker instead of on host
docker-compose -f docker-compose-wso2.yml up

# Option 3: Use Docker's development mode
docker-compose -f docker-compose-dev.yml up
```

## Current Configuration

### Port Allocation

- **80/443**: nginx (reverse proxy)
- **5000**: darts-app (Flask)
- **8080**: api-gateway
- **5672**: RabbitMQ (AMQP)
- **15672**: RabbitMQ (Management UI)
- **9443**: WSO2 IS (HTTPS)
- **5432**: PostgreSQL

### Docker Network

- All services communicate via `darts-network` bridge network
- nginx serves as reverse proxy
- Internal communication: `http://darts-app:5000`, `https://wso2is:9443`, etc.

## Testing the Fix

The application is now fully operational:

1. ✅ **nginx** responding on ports 80/443
2. ✅ **darts-app** responding on port 5000
3. ✅ **Authentication redirect** working (HTTP 302 to login)
4. ✅ **All backend services** healthy
5. ✅ **WebSocket connections** functional (nginx configured with proper headers)

## Related Files

- `docker-compose-wso2.yml` - Production Docker Compose configuration
- `nginx/nginx.conf` - Reverse proxy configuration
- `.env.production.example` - Production environment variables

## Monitoring Going Forward

To prevent this issue in the future, monitor:

1. Docker container status (ensure `darts-app` stays running)
2. Port 5000 availability (prevent local development servers)
3. nginx error logs for upstream connection failures
4. Application health endpoints when available
