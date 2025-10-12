# WSO2 Identity Server Multi-Domain Setup Guide

## Overview

This guide explains how to configure the Darts Game Server to work with WSO2 Identity Server across multiple domains and ports. The application now supports **dynamic redirect URIs**, allowing seamless authentication regardless of how users access the application.

## Supported Access Methods

The application automatically detects and adapts to the following access methods:

1. **Local Development**: `https://localhost:5000`
2. **Public Domain with Custom Port**: `https://letsplaydarts.eu:5001`
3. **Public Domain with Standard HTTPS**: `https://letsplaydarts.eu` (port 443)

## How It Works

### Dynamic Redirect URI Generation

The authentication system now uses **dynamic redirect URIs** based on the incoming request:

```python
def get_dynamic_redirect_uri() -> str:
    """
    Dynamically build redirect URI based on the current request
    """
    scheme = request.scheme  # http or https
    host = request.host      # includes port if non-standard
    redirect_uri = f"{scheme}://{host}/callback"
    return redirect_uri
```

### Example Scenarios

| User Accesses | Dynamic Redirect URI Generated |
|--------------|-------------------------------|
| `https://localhost:5000` | `https://localhost:5000/callback` |
| `https://letsplaydarts.eu:5001` | `https://letsplaydarts.eu:5001/callback` |
| `https://letsplaydarts.eu` | `https://letsplaydarts.eu/callback` |

## WSO2 Identity Server Configuration

### Step 1: Register Multiple Redirect URIs

In WSO2 Identity Server, you need to register **all possible redirect URIs** for your application:

1. Log in to WSO2 IS Management Console: `https://your-wso2-server:9443/carbon`
2. Navigate to: **Main > Identity > Service Providers**
3. Select your application (or create a new one)
4. Expand **Inbound Authentication Configuration > OAuth/OpenID Connect Configuration**
5. Add all redirect URIs in the **Callback Url** field (comma-separated or regex pattern):

```
https://localhost:5000/callback,
https://letsplaydarts.eu:5001/callback,
https://letsplaydarts.eu/callback
```

**Or use a regex pattern:**
```
regexp=(https://localhost:5000/callback|https://letsplaydarts\.eu:5001/callback|https://letsplaydarts\.eu/callback)
```

### Step 2: Configure Logout URIs

Similarly, configure all possible post-logout redirect URIs:

1. In the same OAuth/OpenID Connect Configuration section
2. Add all logout URIs:

```
https://localhost:5000/,
https://letsplaydarts.eu:5001/,
https://letsplaydarts.eu/
```

**Or use a regex pattern:**
```
regexp=(https://localhost:5000/|https://letsplaydarts\.eu:5001/|https://letsplaydarts\.eu/)
```

### Step 3: Save Configuration

1. Click **Update** to save the configuration
2. Note down your **Client ID** and **Client Secret**

## Application Configuration

### Environment Variables

Configure the following environment variables in your `.env` file:

```bash
# WSO2 Identity Server URL
WSO2_IS_URL=https://your-wso2-server:9443

# OAuth2 Client Credentials
WSO2_CLIENT_ID=your_client_id_here
WSO2_CLIENT_SECRET=your_client_secret_here

# Default redirect URI (used as fallback)
# This is now optional - the app will auto-detect the correct URI
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback

# Introspection credentials (for token validation)
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=admin

# SSL verification (set to False for self-signed certificates)
WSO2_IS_VERIFY_SSL=False

# JWT validation mode
JWT_VALIDATION_MODE=introspection
```

### SSL Configuration

Enable SSL for the application:

```bash
# Enable SSL
FLASK_USE_SSL=True

# Host and port
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## Network Configuration

### Port Forwarding

If you're running the application behind a router/firewall, configure port forwarding:

1. **Port 5000** → Internal server IP (for development)
2. **Port 5001** → Internal server IP (for production with custom port)
3. **Port 443** → Internal server IP (for standard HTTPS)

### Reverse Proxy (Nginx)

For production deployments, use Nginx as a reverse proxy:

```nginx
# Standard HTTPS (port 443)
server {
    listen 443 ssl http2;
    server_name letsplaydarts.eu;

    ssl_certificate /etc/nginx/ssl/letsplaydarts.eu.crt;
    ssl_certificate_key /etc/nginx/ssl/letsplaydarts.eu.key;

    location / {
        proxy_pass https://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Custom port (5001)
server {
    listen 5001 ssl http2;
    server_name letsplaydarts.eu;

    ssl_certificate /etc/nginx/ssl/letsplaydarts.eu.crt;
    ssl_certificate_key /etc/nginx/ssl/letsplaydarts.eu.key;

    location / {
        proxy_pass https://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Compose Configuration

Update your `docker-compose.yml` to expose multiple ports:

```yaml
services:
  darts-app:
    build: .
    container_name: darts-app
    ports:
      - "5000:5000"  # Development
      - "5001:5000"  # Production custom port
      - "443:5000"   # Standard HTTPS
    environment:
      FLASK_USE_SSL: "True"
      WSO2_IS_URL: https://wso2is:9443
      WSO2_CLIENT_ID: ${WSO2_CLIENT_ID}
      WSO2_CLIENT_SECRET: ${WSO2_CLIENT_SECRET}
```

## DNS Configuration

Ensure your domain points to your server's public IP:

```
A Record: letsplaydarts.eu → Your Public IP
```

## SSL Certificates

### Let's Encrypt (Recommended for Production)

Generate SSL certificates using Certbot:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d letsplaydarts.eu

# Auto-renewal (already configured by Certbot)
sudo certbot renew --dry-run
```

### Self-Signed Certificates (Development)

Generate self-signed certificates:

```bash
# Create SSL directory
mkdir -p ssl

# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -days 365 \
  -subj "/CN=letsplaydarts.eu" \
  -addext "subjectAltName=DNS:letsplaydarts.eu,DNS:localhost"
```

## Testing the Setup

### Test Local Access

```bash
# Start the application
python app.py

# Access via browser
https://localhost:5000
```

### Test Public Domain Access

```bash
# Test custom port
https://letsplaydarts.eu:5001

# Test standard HTTPS
https://letsplaydarts.eu
```

### Verify Dynamic Redirect URIs

Check the application logs during login:

```
INFO:auth:Dynamic redirect URI: https://localhost:5000/callback
INFO:auth:Generating authorization URL with params: {...}
```

## Troubleshooting

### Issue: "Invalid redirect_uri"

**Cause**: The redirect URI is not registered in WSO2 IS

**Solution**:
1. Check WSO2 IS Service Provider configuration
2. Ensure all redirect URIs are registered
3. Use regex pattern for flexibility

### Issue: "SSL Certificate Verification Failed"

**Cause**: WSO2 IS uses self-signed certificate

**Solution**:
```bash
# In .env file
WSO2_IS_VERIFY_SSL=False
```

### Issue: "Connection Refused"

**Cause**: Port not accessible from public internet

**Solution**:
1. Check firewall rules: `sudo ufw status`
2. Allow ports: `sudo ufw allow 5001/tcp`
3. Check port forwarding on router

### Issue: "Mixed Content" Warnings

**Cause**: Application accessed via HTTP instead of HTTPS

**Solution**:
1. Always use HTTPS URLs
2. Configure HTTP to HTTPS redirect in Nginx
3. Set `FLASK_USE_SSL=True`

## Security Best Practices

### 1. Use Strong SSL Certificates

- **Production**: Use Let's Encrypt certificates
- **Development**: Use self-signed certificates
- Never use HTTP in production

### 2. Restrict Redirect URIs

Only register the redirect URIs you actually use:

```
# Good - Specific URIs
https://letsplaydarts.eu/callback,https://letsplaydarts.eu:5001/callback

# Bad - Too permissive
regexp=https://.*
```

### 3. Secure Environment Variables

```bash
# Use strong secrets
SECRET_KEY=$(openssl rand -hex 32)
WSO2_CLIENT_SECRET=<strong-secret-from-wso2>

# Restrict file permissions
chmod 600 .env
```

### 4. Enable HTTPS Strict Transport Security (HSTS)

In Nginx configuration:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 5. Use Introspection for Token Validation

```bash
# In .env file
JWT_VALIDATION_MODE=introspection
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=<strong-password>
```

## Advanced Configuration

### Custom Domain Mapping

If you need to map different domains to different WSO2 clients:

```python
# In auth.py, customize get_dynamic_redirect_uri()
def get_dynamic_redirect_uri() -> str:
    host = request.host
    
    # Map domains to specific redirect URIs
    domain_mapping = {
        "letsplaydarts.eu": "https://letsplaydarts.eu/callback",
        "letsplaydarts.eu:5001": "https://letsplaydarts.eu:5001/callback",
        "localhost:5000": "https://localhost:5000/callback",
    }
    
    return domain_mapping.get(host, f"{request.scheme}://{host}/callback")
```

### Load Balancer Configuration

If using a load balancer, ensure it preserves the original host header:

```nginx
# Nginx load balancer
upstream darts_backend {
    server 10.0.0.1:5000;
    server 10.0.0.2:5000;
}

server {
    listen 443 ssl;
    server_name letsplaydarts.eu;

    location / {
        proxy_pass https://darts_backend;
        proxy_set_header Host $host;  # Preserve original host
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Logging

### Enable Debug Logging

```bash
# In .env file
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

### Monitor Authentication Flow

Check logs for:
- Dynamic redirect URI generation
- OAuth2 authorization requests
- Token exchange responses
- User info retrieval

```bash
# Tail application logs
tail -f logs/app.log | grep -E "(redirect_uri|authorization|token)"
```

## Summary

✅ **Dynamic redirect URIs** automatically adapt to the access method  
✅ **Multiple domains** supported (localhost, custom port, standard HTTPS)  
✅ **WSO2 IS integration** works seamlessly across all domains  
✅ **SSL/TLS** properly configured for secure communication  
✅ **Production-ready** with proper security measures  

## Related Documentation

- [SSL Configuration Guide](SSL_CONFIGURATION.md)
- [SSL Quick Start](SSL_QUICK_START.md)
- [SSL Error Handling](SSL_ERROR_HANDLING.md)
- [WSO2 Integration Guide](WSO2_INTEGRATION.md)