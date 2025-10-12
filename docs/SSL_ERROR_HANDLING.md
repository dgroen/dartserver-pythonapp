# SSL Error Handling

## Overview

The Darts Game Server includes robust SSL error handling to prevent console spam from protocol mismatch errors. When SSL is enabled, the server gracefully handles situations where clients attempt to connect using HTTP instead of HTTPS.

## The Problem

When running an HTTPS server, clients that attempt to connect using plain HTTP will trigger SSL errors:

```
ssl.SSLError: [SSL: HTTP_REQUEST] http request (_ssl.c:2580)
```

Without proper handling, each failed connection attempt generates a full stack trace, flooding the console and making it difficult to monitor the application.

## The Solution

The server implements a custom error handler that:

1. **Detects SSL protocol errors** - Identifies when clients use HTTP instead of HTTPS
2. **Suppresses stack traces** - Prevents verbose error output from cluttering logs
3. **Provides concise feedback** - Shows user-friendly messages with rate limiting
4. **Counts occurrences** - Tracks how many errors occurred between log messages

## How It Works

### Monkey-Patching Eventlet

The `patch_eventlet_ssl_error_handling()` function modifies eventlet's WSGI error handler:

```python
def patch_eventlet_ssl_error_handling():
    """
    Monkey-patch eventlet's WSGI error handler to suppress SSL protocol errors

    This prevents stack traces from flooding the console when clients attempt
    to connect using HTTP to an HTTPS server.
    """
    # Custom error handler with SSL-specific logic
    # Rate-limited logging (every 10 seconds)
    # Suppresses stack traces for HTTP_REQUEST errors
```

### Rate Limiting

To prevent log spam, SSL errors are aggregated and reported every 10 seconds:

```
⚠️  SSL Protocol Mismatch Detected
   15 HTTP request(s) to HTTPS server (rejected)
   Clients must use HTTPS URLs to connect
```

### Automatic Activation

The error handler is automatically activated when:

- `FLASK_USE_SSL=True` in `.env`
- SSL certificates exist in the `ssl/` directory
- The server starts successfully with HTTPS

## Error Messages

### During Startup

When SSL is enabled, the server displays clear guidance:

```
================================================================================
🔒 Starting Darts Game Server with SSL/HTTPS
   URL: https://0.0.0.0:5000
================================================================================
⚠️  IMPORTANT: Using self-signed SSL certificate
   - Your browser will show a security warning
   - This is expected for self-signed certificates
   - Click 'Advanced' and 'Proceed' to continue

⚠️  SSL ERROR TROUBLESHOOTING:
   - If you see 'SSL: HTTP_REQUEST' errors, clients are
     using HTTP instead of HTTPS
   - Make sure to access the application using: https://
   - Correct URL: https://0.0.0.0:5000
   - Wrong URL:   http://0.0.0.0:5000

   To disable SSL for development:
   - Set FLASK_USE_SSL=False in .env file
================================================================================
```

### During Runtime

When HTTP requests are received by the HTTPS server:

```
⚠️  SSL Protocol Mismatch Detected
   5 HTTP request(s) to HTTPS server (rejected)
   Clients must use HTTPS URLs to connect
```

## Testing

### Manual Testing

1. Start the server with SSL enabled:

   ```bash
   # Ensure SSL is enabled in .env
   echo "FLASK_USE_SSL=True" >> .env

   # Start the server
   python app.py
   ```

2. In another terminal, run the test script:

   ```bash
   python test_ssl_error_handling.py
   ```

3. Observe the server console - you should see concise error messages instead of stack traces

### Using curl

Test HTTP to HTTPS connection:

```bash
# This will trigger an SSL error
curl http://localhost:5000

# This is the correct way
curl -k https://localhost:5000
```

### Using Browser

1. Try accessing `http://localhost:5000` (wrong protocol)
   - Modern browsers may auto-redirect to HTTPS
   - Direct HTTP requests will fail

2. Access `https://localhost:5000` (correct protocol)
   - Browser will show security warning (expected for self-signed certs)
   - Click "Advanced" → "Proceed to localhost"

## Common Scenarios

### Scenario 1: Browser Auto-Redirect

**Situation**: Browser automatically redirects HTTP to HTTPS

**Result**: No errors, connection succeeds

**Explanation**: Modern browsers detect HTTPS servers and auto-upgrade connections

### Scenario 2: API Client Using HTTP

**Situation**: API client (curl, Postman, Python requests) uses HTTP URL

**Result**: Connection fails, SSL error logged on server

**Solution**: Update client to use HTTPS URL

### Scenario 3: WebSocket Connection

**Situation**: WebSocket client connects using `ws://` instead of `wss://`

**Result**: Connection fails, SSL error logged

**Solution**: Use `wss://` protocol for WebSocket connections

### Scenario 4: Docker Container

**Situation**: Container-to-container communication uses HTTP

**Result**: SSL errors if main app uses HTTPS

**Solution**: Either:

- Use HTTPS URLs in container configuration
- Disable SSL for internal communication
- Use nginx as SSL termination proxy

## Configuration

### Enable SSL Error Handling

SSL error handling is automatically enabled when SSL is active. No additional configuration needed.

### Adjust Rate Limiting

To change how often SSL errors are logged, modify the timeout in `app.py`:

```python
# Current: Log every 10 seconds
if current_time - ssl_error_state["last_logged"] >= 10:

# Change to 30 seconds
if current_time - ssl_error_state["last_logged"] >= 30:
```

### Disable SSL Error Handling

To see full stack traces (for debugging):

1. Comment out the patch call in `app.py`:

   ```python
   # patch_eventlet_ssl_error_handling()
   ```

2. Or disable SSL entirely:

   ```bash
   # In .env file
   FLASK_USE_SSL=False
   ```

## Troubleshooting

### Still Seeing Stack Traces

**Problem**: Full stack traces still appear in console

**Possible Causes**:

1. SSL error handling patch not applied
2. Different type of SSL error (not HTTP_REQUEST)
3. Error occurring before patch is applied

**Solutions**:

1. Verify `patch_eventlet_ssl_error_handling()` is called
2. Check error message - may be different SSL issue
3. Ensure patch is applied before server starts

### No Error Messages at All

**Problem**: HTTP requests fail silently

**Possible Causes**:

1. Client not reaching server
2. Firewall blocking connections
3. Server not listening on expected interface

**Solutions**:

1. Check server is running: `netstat -tlnp | grep 5000`
2. Verify firewall rules: `sudo ufw status`
3. Check `FLASK_HOST` setting (use `0.0.0.0` for all interfaces)

### Too Many Error Messages

**Problem**: Error messages appear too frequently

**Solution**: Increase rate limiting timeout (see Configuration section)

## Best Practices

### Development

1. **Use self-signed certificates** for local development
2. **Enable SSL error handling** to keep logs clean
3. **Use HTTPS URLs** in all client code
4. **Trust certificates** in browser/OS for better UX

### Production

1. **Use Let's Encrypt** or commercial certificates
2. **Enable SSL error handling** to prevent log spam
3. **Use nginx** as reverse proxy for SSL termination
4. **Monitor logs** for unusual SSL error patterns
5. **Set up alerts** for high error rates

### Docker/Kubernetes

1. **SSL termination at ingress** - Let nginx/ingress handle SSL
2. **HTTP internally** - Use HTTP for container-to-container communication
3. **HTTPS externally** - Only expose HTTPS to outside world
4. **Certificate management** - Use cert-manager for automatic renewal

## Related Documentation

- [SSL Configuration Guide](SSL_CONFIGURATION.md) - Complete SSL setup guide
- [SSL Quick Start](SSL_QUICK_START.md) - 5-minute SSL setup
- [Docker Deployment](../README.md#docker-deployment) - Container deployment

## Technical Details

### Implementation

The error handler is implemented as a monkey-patch to `eventlet.wsgi.HttpProtocol.handle_error`:

```python
def custom_handle_error(self):
    """Handle errors with special treatment for SSL protocol errors"""
    exc_type, exc_value, _ = sys.exc_info()

    # Check if this is an SSL HTTP_REQUEST error
    if exc_type and issubclass(exc_type, ssl.SSLError):
        error_msg = str(exc_value)
        if "HTTP_REQUEST" in error_msg or "http request" in error_msg.lower():
            # Rate-limited logging
            # Suppress stack trace
            return

    # For all other errors, use the original handler
    original_handle_error(self)
```

### Why Monkey-Patching?

Eventlet's WSGI server handles SSL errors at a low level, before they reach Flask's error handlers. Monkey-patching is the only way to intercept these errors without modifying eventlet's source code.

### Thread Safety

The error handler uses a dictionary for state management, which is safe for this use case because:

1. Python's GIL ensures atomic dictionary operations
2. Only simple increment/assignment operations are performed
3. Race conditions would only affect error counting, not functionality

### Performance Impact

The error handler has minimal performance impact:

- Only executes when errors occur
- Simple type checking and string comparison
- No blocking operations
- Rate limiting prevents excessive logging

## Support

For issues or questions:

1. Check the [SSL Configuration Guide](SSL_CONFIGURATION.md)
2. Review server startup messages
3. Enable debug logging: `FLASK_DEBUG=True`
4. Check GitHub issues for similar problems
