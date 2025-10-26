# Production Fix: 502 Bad Gateway Error Resolution

## Problem

The production application at <https://letsplaydarts.eu> was responding with HTTP 502 Bad Gateway errors. The nginx reverse proxy could not connect to the Flask application.

### Root Cause

The Flask-SocketIO server was not binding to the correct interface. The `run.py` script was calling `socketio.run(app)` without specifying the host and port parameters, which caused the server to bind to `127.0.0.1:5000` (localhost only) instead of `0.0.0.0:5000` (all interfaces).

This made the Flask app inaccessible from the nginx container running on the Docker network, resulting in:

```
[error] connect() failed (111: Connection refused) while connecting to upstream
```

## Solution

Modified `/data/dartserver-pythonapp/run.py` to explicitly bind the Flask-SocketIO server to `0.0.0.0:5000`:

### Changes Made

#### File: `run.py`

- Added environment variable configuration for `FLASK_HOST`, `FLASK_PORT`, and `FLASK_DEBUG`
- Updated `socketio.run()` call to pass explicit host and port parameters
- Added proper error handling with logging
- Set default values:
  - `host`: `0.0.0.0` (listen on all interfaces)
  - `port`: `5000`
  - `debug`: `False` (production mode)
  - `allow_unsafe_werkzeug`: `True` (needed for eventlet)

### Code Changes

```python
# Before
socketio.run(app)

# After
host = os.getenv("FLASK_HOST", "0.0.0.0")
port = int(os.getenv("FLASK_PORT", 5000))
debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

socketio.run(
    app,
    host=host,
    port=port,
    debug=debug,
    allow_unsafe_werkzeug=True,
)
```

## Verification

### Pre-Fix Symptoms

- Nginx logs showed: `connect() failed (111: Connection refused)`
- HTTP responses: 502 Bad Gateway
- Flask app container was running but not accepting connections from nginx

### Post-Fix Results

- ✅ Nginx successfully connects to Flask app
- ✅ HTTP 302 redirects working (OAuth flow)
- ✅ HTTP 200 responses for valid requests
- ✅ No more 502 errors
- ✅ Application is accessible at <https://letsplaydarts.eu>

## Docker Compose Configuration

The fix respects the Docker Compose environment variables set in `docker-compose-wso2.yml`:

```yaml
environment:
  FLASK_HOST: 0.0.0.0
  FLASK_PORT: 5000
  FLASK_DEBUG: "False"
```

## Deployment Steps Taken

1. Modified `run.py` to explicitly bind to `0.0.0.0:5000`
2. Rebuilt Docker image with updated code
3. Stopped all containers with `docker-compose down`
4. Restarted all services with `docker-compose up -d`
5. Verified nginx can connect to Flask app
6. Confirmed HTTP requests return proper responses

## Testing

All services are now operational:

- darts-app: ✅ Running on 0.0.0.0:5000
- nginx: ✅ Successfully proxying requests
- WSO2 Identity Server: ✅ Healthy
- PostgreSQL: ✅ Healthy
- RabbitMQ: ✅ Healthy

## Future Improvements

- Consider adding health check endpoint logging
- Monitor Flask-SocketIO connection metrics
- Add startup/readiness probes to Docker Compose for better orchestration
