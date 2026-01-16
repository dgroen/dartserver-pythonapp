# Production Deployment Guide

## Overview

This guide covers deploying the Dartserver packages to production environments.

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- RabbitMQ 3.10+ (optional, for message queue)
- Redis (optional, for session caching)
- nginx or Apache (for reverse proxy)

## Installation

### 1. Create Virtual Environment

```bash
python3.11 -m venv /opt/dartserver/venv
source /opt/dartserver/venv/bin/activate
```

### 2. Install Packages from PyPI

```bash
pip install --upgrade pip wheel setuptools

# Install all packages
pip install dartserver-core dartserver-games dartserver-services dartserver-app

# Or specific versions
pip install dartserver-app==1.0.0
```

### 3. Database Setup

```bash
# Create database
createdb dartserver

# Run migrations
alembic upgrade head

# Create initial data
python -m dartserver_core.init_db
```

### 4. Environment Configuration

Create `.env` file:

```bash
# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Database
DATABASE_URL=postgresql://dartserver:password@localhost/dartserver

# Authentication
WSO2_IS_URL=https://wso2is.example.com
WSO2_IS_INTERNAL_URL=https://wso2is.internal:9443
OIDC_CLIENT_ID=dartserver-app
OIDC_CLIENT_SECRET=your-client-secret

# Application
APP_URL=https://darts.example.com
CALLBACK_URL=https://darts.example.com/callback
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_USE_SSL=True

# RabbitMQ (optional)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# TTS
TTS_ENGINE=gtts
TTS_DEFAULT_LANGUAGE=en

# SSL Certificates (if using FLASK_USE_SSL=True)
# Generate with: ./helpers/generate_ssl_certs.sh domain.com
```

### 5. Systemd Service File

Create `/etc/systemd/system/dartserver.service`:

```ini
[Unit]
Description=Dartserver Game Web Application
After=network.target postgresql.service

[Service]
User=dartserver
Group=dartserver
WorkingDirectory=/opt/dartserver
Environment="PATH=/opt/dartserver/venv/bin"
ExecStart=/opt/dartserver/venv/bin/python -m dartserver_app
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 6. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable dartserver
sudo systemctl start dartserver
sudo systemctl status dartserver
```

## Reverse Proxy Configuration

### nginx Configuration

```nginx
upstream dartserver {
    server 127.0.0.1:5000;
}

server {
    listen 443 ssl http2;
    server_name darts.example.com;

    ssl_certificate /etc/letsencrypt/live/darts.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/darts.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    location / {
        proxy_pass http://dartserver;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name darts.example.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring

### Health Check

```bash
curl -s https://darts.example.com/health
```

### Logs

```bash
# View service logs
sudo journalctl -u dartserver -f

# View application logs
tail -f /var/log/dartserver/app.log
```

### Metrics

Monitor with your preferred tool:
- Prometheus + Grafana
- New Relic
- Datadog
- CloudWatch (AWS)

### Alerting

Set up alerts for:
- Service down
- High error rate
- High response time
- Database connection errors
- RabbitMQ queue depth

## Backup & Recovery

### Database Backup

```bash
# Daily backup
pg_dump dartserver > /backups/dartserver-$(date +%Y%m%d).sql

# Automated backup with cron
0 2 * * * pg_dump dartserver | gzip > /backups/dartserver-$(date +\%Y\%m\%d).sql.gz
```

### Recovery

```bash
# Restore from backup
psql dartserver < /backups/dartserver-20240101.sql
```

## Updates

### Update Packages

```bash
pip install --upgrade dartserver-app dartserver-core dartserver-games dartserver-services
```

### Restart Service

```bash
sudo systemctl restart dartserver
```

## Performance Tuning

### PostgreSQL

```sql
-- Increase shared buffers (25% of RAM)
shared_buffers = 4GB

-- Increase work memory
work_mem = 16MB

-- Enable connection pooling
```

### Application

```python
# In app configuration
app.config['JSON_SORT_KEYS'] = False  # Faster JSON rendering
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache static files
```

### RabbitMQ

```bash
# Increase file descriptor limit
ulimit -n 65536

# Configure for high throughput
rabbitmq.conf:
vm_memory_high_watermark.relative = 0.6
```

## Troubleshooting

See TROUBLESHOOTING.md for common issues and solutions.
