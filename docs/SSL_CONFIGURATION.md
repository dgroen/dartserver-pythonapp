# SSL/HTTPS Configuration Guide

This guide explains how to configure and troubleshoot SSL/HTTPS for the Darts Game Server.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [SSL Certificate Generation](#ssl-certificate-generation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Overview

The Darts Game Server supports both HTTP and HTTPS modes. For production deployments, HTTPS is strongly recommended to encrypt communication between clients and the server.

### SSL Modes

1. **HTTP Mode** (Development)
   - No encryption
   - Simple setup
   - Not recommended for production

2. **HTTPS Mode** (Production)
   - Encrypted communication
   - Requires SSL certificates
   - Recommended for production

## Quick Start

### Enable SSL for Development

1. Generate self-signed certificates:

   ```bash
   ./helpers/generate_ssl_certs.sh letsplaydarts.eu
   ```

2. Enable SSL in `.env`:

   ```bash
   FLASK_USE_SSL=True
   ```

3. Start the server:

   ```bash
   python app.py
   ```

4. Access the application:

   ```
   https://letsplaydarts.eu:5000
   ```

### Disable SSL for Development

1. Update `.env`:

   ```bash
   FLASK_USE_SSL=False
   ```

2. Start the server:

   ```bash
   python app.py
   ```

3. Access the application:

   ```
   http://localhost:5000
   ```

## SSL Certificate Generation

### Self-Signed Certificates (Development)

The project includes a script to generate self-signed SSL certificates:

```bash
./helpers/generate_ssl_certs.sh [domain]
```

**Examples:**

```bash
# Generate for localhost
./helpers/generate_ssl_certs.sh localhost

# Generate for custom domain
./helpers/generate_ssl_certs.sh letsplaydarts.eu

# Generate for IP address (use localhost and add IP to hosts file)
./helpers/generate_ssl_certs.sh localhost
```

**Generated Files:**

- `ssl/cert.pem` - SSL certificate
- `ssl/key.pem` - Private key
- `ssl/openssl.cnf` - OpenSSL configuration

**Certificate Details:**

- **Algorithm:** RSA 4096-bit
- **Validity:** 365 days
- **Subject Alternative Names (SAN):**
  - Specified domain and wildcard (e.g., `letsplaydarts.eu`, `*.letsplaydarts.eu`)
  - `localhost` and `*.localhost`
  - IP addresses: `127.0.0.1`, `::1`

### Trust Self-Signed Certificates

To avoid browser security warnings, you can trust the self-signed certificate on your system:

**Linux:**

```bash
sudo cp ssl/cert.pem /usr/local/share/ca-certificates/letsplaydarts.eu.crt
sudo update-ca-certificates
```

**macOS:**

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ssl/cert.pem
```

**Windows:**

1. Double-click `ssl/cert.pem`
2. Click "Install Certificate"
3. Select "Local Machine"
4. Choose "Place all certificates in the following store"
5. Select "Trusted Root Certification Authorities"
6. Complete the wizard

### Production Certificates (Let's Encrypt)

For production deployments, use Let's Encrypt to obtain free, trusted SSL certificates:

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d letsplaydarts.eu

# Copy certificates to project
sudo cp /etc/letsencrypt/live/letsplaydarts.eu/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/letsplaydarts.eu/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*.pem
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem
```

## Configuration

### Environment Variables

Configure SSL behavior in `.env`:

```bash
# Enable/Disable SSL
FLASK_USE_SSL=True

# Flask server configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Session cookie security (auto-detected based on SSL)
SESSION_COOKIE_SECURE=True  # Set to True when using SSL
```

### WSO2 Authentication with SSL

When using SSL, update WSO2 redirect URIs:

```bash
# Use HTTPS in redirect URIs
WSO2_REDIRECT_URI=https://letsplaydarts.eu:5000/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu:5000/
```

### Docker Configuration

Update `docker-compose-wso2.yml` for SSL:

```yaml
darts-app:
  environment:
    FLASK_USE_SSL: "True"
    SESSION_COOKIE_SECURE: "True"
  volumes:
    - ./ssl:/app/ssl:ro # Mount SSL certificates
```

## Troubleshooting

### Common SSL Errors

#### 1. `ssl.SSLError: [SSL: HTTP_REQUEST] http request`

**Cause:** Client is using HTTP to connect to an HTTPS server.

**Solution:**

- Use `https://` instead of `http://` in the URL
- Correct: `https://letsplaydarts.eu:5000`
- Wrong: `http://letsplaydarts.eu:5000`

**Alternative:** Disable SSL for development:

```bash
# In .env
FLASK_USE_SSL=False
```

#### 2. `SSL certificates not found`

**Cause:** SSL is enabled but certificate files are missing.

**Solution:**

```bash
# Generate certificates
./helpers/generate_ssl_certs.sh letsplaydarts.eu

# Verify files exist
ls -la ssl/
# Should show: cert.pem and key.pem
```

#### 3. Browser Security Warning

**Cause:** Using self-signed certificates (expected for development).

**Solution:**

- Click "Advanced" in the browser
- Click "Proceed to [domain] (unsafe)"
- Or trust the certificate system-wide (see above)

#### 4. `Permission denied` on certificate files

**Cause:** Incorrect file permissions.

**Solution:**

```bash
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem
```

#### 5. `Name or service not known` for custom domain

**Cause:** Domain not configured in `/etc/hosts`.

**Solution:**

```bash
# Add to /etc/hosts
echo "127.0.0.1 letsplaydarts.eu" | sudo tee -a /etc/hosts
```

### Debug Mode

Enable debug logging to troubleshoot SSL issues:

```bash
# In .env
FLASK_DEBUG=True
```

The server will display detailed SSL configuration on startup:

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
   - If you see 'SSL: HTTP_REQUEST' errors, clients are using HTTP instead of HTTPS
   - Make sure to access the application using: https://
   - Correct URL: https://0.0.0.0:5000
   - Wrong URL:   http://0.0.0.0:5000

   To disable SSL for development:
   - Set FLASK_USE_SSL=False in .env file
================================================================================
```

### Verify SSL Configuration

Check certificate details:

```bash
# View certificate information
openssl x509 -in ssl/cert.pem -noout -text

# Check certificate validity
openssl x509 -in ssl/cert.pem -noout -dates

# Verify certificate and key match
openssl x509 -noout -modulus -in ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in ssl/key.pem | openssl md5
# Both should output the same hash
```

Test SSL connection:

```bash
# Test with curl (accept self-signed)
curl -k https://letsplaydarts.eu:5000

# Test with openssl
openssl s_client -connect letsplaydarts.eu:5000 -servername letsplaydarts.eu
```

## Production Deployment

### Best Practices

1. **Use Trusted Certificates**
   - Obtain certificates from Let's Encrypt or a commercial CA
   - Never use self-signed certificates in production

2. **Enable HTTPS Everywhere**

   ```bash
   FLASK_USE_SSL=True
   SESSION_COOKIE_SECURE=True
   ```

3. **Use Reverse Proxy**
   - Deploy nginx or Apache as a reverse proxy
   - Handle SSL termination at the proxy level
   - Benefits: Better performance, easier certificate management

4. **Automatic Certificate Renewal**

   ```bash
   # Add to crontab for Let's Encrypt
   0 0 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
   ```

5. **Security Headers**
   - Enable HSTS (HTTP Strict Transport Security)
   - Configure CSP (Content Security Policy)
   - Set secure cookie flags

### Nginx Reverse Proxy Example

```nginx
server {
    listen 443 ssl http2;
    server_name letsplaydarts.eu;

    ssl_certificate /etc/letsencrypt/live/letsplaydarts.eu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/letsplaydarts.eu/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name letsplaydarts.eu;
    return 301 https://$server_name$request_uri;
}
```

### Docker Production Setup

```yaml
version: "3.8"

services:
  darts-app:
    build: .
    environment:
      FLASK_USE_SSL: "False" # SSL handled by nginx
      FLASK_HOST: "0.0.0.0"
      FLASK_PORT: "5000"
    networks:
      - internal

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - darts-app
    networks:
      - internal

networks:
  internal:
    driver: bridge
```

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)

## Support

If you encounter issues not covered in this guide:

1. Check the server logs for detailed error messages
2. Verify your configuration matches the examples
3. Test with curl or openssl to isolate the issue
4. Review the [Troubleshooting](#troubleshooting) section

For additional help, please open an issue on the project repository.
