# Mobile App Deployment Guide

This guide covers deploying the mobile dartboard connectivity app to production.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- HTTPS certificate (required for PWA)
- Domain name (recommended)

## Deployment Steps

### 1. Database Migration

Apply the database migration to add mobile app tables:

```bash
cd /data/dartserver-pythonapp
source .venv/bin/activate
alembic upgrade head
```

Verify migration:
```bash
alembic current
# Should show: d55f29e75045 (head)
```

### 2. Generate PWA Icons

Create PNG icons from the SVG template:

```bash
cd static/icons

# Option 1: Using ImageMagick + librsvg
sudo apt-get install imagemagick librsvg2-bin
for size in 72 96 128 144 152 192 384 512; do
  rsvg-convert -w $size -h $size icon.svg -o icon-${size}x${size}.png
done

# Option 2: Use online tool
# Upload icon.svg to https://realfavicongenerator.net/
```

### 3. Configure HTTPS

PWA requires HTTPS. Options:

**Option A: Let's Encrypt (Recommended)**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**Option B: Self-signed (Development only)**
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365
```

Update `app.py` to use SSL:
```python
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        ssl_context=('cert.pem', 'key.pem')  # Add this
    )
```

### 4. Configure Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dartserver

# Security
SECRET_KEY=your-secret-key-here
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# CORS (if needed)
CORS_ORIGINS=https://yourdomain.com

# WSO2 OAuth2
WSO2_CLIENT_ID=your-client-id
WSO2_CLIENT_SECRET=your-client-secret
WSO2_AUTHORIZATION_URL=https://your-wso2/oauth2/authorize
WSO2_TOKEN_URL=https://your-wso2/oauth2/token
WSO2_USERINFO_URL=https://your-wso2/oauth2/userinfo

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

### 5. Update Session Management

Replace placeholder session code in `app.py`:

```python
# Find all instances of:
player_id = session.get("user_id", 1)  # TODO: Get from actual session

# Replace with:
player_id = session.get("user_id")
if not player_id:
    return jsonify({"success": False, "error": "Not authenticated"}), 401
```

### 6. Configure Production Server

**Option A: Gunicorn + Nginx**

Install Gunicorn:
```bash
pip install gunicorn eventlet
```

Create `gunicorn_config.py`:
```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "eventlet"
timeout = 120
accesslog = "/var/log/dartserver/access.log"
errorlog = "/var/log/dartserver/error.log"
loglevel = "info"
```

Run with Gunicorn:
```bash
gunicorn -c gunicorn_config.py app:app
```

Configure Nginx:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /data/dartserver-pythonapp/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Option B: Systemd Service**

Create `/etc/systemd/system/dartserver.service`:
```ini
[Unit]
Description=Dartboard Server
After=network.target postgresql.service rabbitmq-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/data/dartserver-pythonapp
Environment="PATH=/data/dartserver-pythonapp/.venv/bin"
ExecStart=/data/dartserver-pythonapp/.venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dartserver
sudo systemctl start dartserver
sudo systemctl status dartserver
```

### 7. Security Hardening

**Rate Limiting**

Install Flask-Limiter:
```bash
pip install Flask-Limiter
```

Add to `app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to API endpoints
@app.route("/api/mobile/apikeys", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def create_api_key():
    # ...
```

**CORS Configuration**

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
```

**Security Headers**

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 8. Monitoring and Logging

**Application Logging**

Update logging configuration:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        '/var/log/dartserver/app.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Dartserver startup')
```

**Error Tracking (Optional)**

Install Sentry:
```bash
pip install sentry-sdk[flask]
```

Configure:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 9. Database Backup

Create backup script `/usr/local/bin/backup-dartserver.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/dartserver"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump dartserver > $BACKUP_DIR/dartserver_$DATE.sql

# Compress
gzip $BACKUP_DIR/dartserver_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-dartserver.sh
```

### 10. Testing Deployment

Run the test suite:
```bash
python test_mobile_app.py
```

Test PWA installation:
1. Open https://yourdomain.com/mobile on mobile device
2. Look for "Add to Home Screen" prompt
3. Install and test offline functionality

Test API endpoints:
```bash
# Test API key creation
curl -X POST https://yourdomain.com/api/mobile/apikeys \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"key_name": "Test Key"}'

# Test dartboard registration
curl -X POST https://yourdomain.com/api/mobile/dartboards \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"dartboard_id": "DART-TEST123", "dartboard_key": "test-key-123"}'
```

## Post-Deployment Checklist

- [ ] Database migration applied
- [ ] PWA icons generated
- [ ] HTTPS configured
- [ ] Environment variables set
- [ ] Session management updated
- [ ] Production server configured
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Logging configured
- [ ] Backup script created
- [ ] Test suite passes
- [ ] PWA installs on mobile
- [ ] API endpoints tested
- [ ] WebSocket connections work
- [ ] Offline mode works
- [ ] Service worker caches correctly

## Troubleshooting

### PWA Not Installing

- Verify HTTPS is working
- Check manifest.json is accessible
- Verify service worker registers
- Check browser console for errors

### API Key Authentication Fails

- Check X-API-Key header is sent
- Verify API key is not expired
- Check database for hashed key
- Review logs for validation errors

### WebSocket Connection Fails

- Verify Socket.IO is running
- Check Nginx WebSocket configuration
- Test with direct connection (bypass proxy)
- Review firewall rules

### Session Issues

- Verify SECRET_KEY is set
- Check cookie settings (Secure, HttpOnly, SameSite)
- Test WSO2 OAuth2 flow
- Review session timeout settings

## Performance Optimization

### Database Indexes

Already created in migration:
- `dartboard_id` (unique)
- `api_key_hash` (indexed)
- `username` (unique)

### Caching

Consider adding Redis for session storage:
```bash
pip install redis flask-session
```

Configure:
```python
from flask_session import Session
import redis

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)
```

### CDN for Static Files

Upload static files to CDN and update URLs:
```python
app.config['CDN_DOMAIN'] = 'cdn.yourdomain.com'
```

## Maintenance

### Regular Tasks

- Monitor logs daily
- Review API key usage weekly
- Check database size monthly
- Update dependencies quarterly
- Review security advisories

### Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run migrations
alembic upgrade head

# Restart service
sudo systemctl restart dartserver
```

## Support

For issues or questions:
- Check logs: `/var/log/dartserver/`
- Review documentation: `/docs/`
- Test endpoints: `python test_mobile_app.py`