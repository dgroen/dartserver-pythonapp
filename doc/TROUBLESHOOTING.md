# Troubleshooting Guide

## Common Issues

### 1. Service Won't Start

**Problem**: `systemctl start dartserver` fails

**Solutions**:

```bash
# Check service logs
sudo journalctl -u dartserver -n 50

# Check if port is in use
lsof -i :5000

# Check permissions
ls -la /opt/dartserver/

# Verify Python installation
/opt/dartserver/venv/bin/python --version
```

### 2. Database Connection Error

**Problem**: `OperationalError: could not connect to server`

**Solutions**:

```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test connection
psql -U dartserver -d dartserver -c "SELECT 1"

# Check database URL
echo $DATABASE_URL

# Verify credentials
sudo -u postgres psql -l
```

### 3. SSL Certificate Error

**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:

```bash
# Regenerate certificates
./helpers/generate_ssl_certs.sh darts.example.com

# Check certificate
openssl s_client -connect darts.example.com:443

# Check expiration
certbot certificates
```

### 4. Memory Usage High

**Problem**: Service using excessive memory

**Solutions**:

```bash
# Monitor memory
watch -n 1 'ps aux | grep python'

# Check for memory leaks
pip install memory_profiler
python -m memory_profiler app.py

# Restart service
sudo systemctl restart dartserver
```

### 5. Slow Response Times

**Problem**: API requests taking too long

**Solutions**:

```bash
# Check database queries
# Enable slow query logging in PostgreSQL
log_min_duration_statement = 1000  # Log queries > 1s

# Check network latency
ping -c 10 database-server

# Profile application
pip install py-spy
py-spy record -o profile.svg -- python -m dartserver_app

# Add caching
pip install redis
```

### 6. WebSocket Connection Fails

**Problem**: Real-time features not working

**Solutions**:

```bash
# Check WebSocket support
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" https://darts.example.com/

# Verify nginx proxy
grep -A 5 "Upgrade" /etc/nginx/sites-enabled/dartserver

# Check firewall
sudo ufw allow 443
```

### 7. RabbitMQ Connection Error

**Problem**: `ConnectionError: Failed to connect to RabbitMQ`

**Solutions**:

```bash
# Check RabbitMQ service
sudo systemctl status rabbitmq-server

# Check RabbitMQ port
netstat -tlnp | grep 5672

# Test connection
rabbitmqctl -n rabbit status

# Check credentials
rabbitmqctl list_users
```

### 8. TTS Engine Not Working

**Problem**: Text-to-speech feature fails

**Solutions**:

```bash
# Check TTS engine
TTS_ENGINE=offline python -c "from dartserver_services import TTSService; t = TTSService(); print(t.get_voices())"

# Install audio libraries
sudo apt-get install espeak libespeak1

# Check internet (for gTTS)
curl -I https://api.gtts.io/
```

## Performance Diagnostics

### Check Service Status

```bash
# Full status
sudo systemctl status dartserver

# View recent logs (last 100 lines)
sudo journalctl -u dartserver -n 100

# Real-time logs
sudo journalctl -u dartserver -f

# Errors only
sudo journalctl -u dartserver -p err
```

### Monitor Resources

```bash
# CPU and Memory
top -p $(pgrep -f dartserver)

# Disk usage
df -h /opt/dartserver
df -h /var/lib/postgresql

# Network connections
netstat -tlnp | grep python
```

### Database Health

```bash
# Check database size
du -sh /var/lib/postgresql/

# Connection count
SELECT count(*) FROM pg_stat_activity;

# Cache hit ratio
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

## Getting Help

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Locally

```bash
# For testing issues locally
export FLASK_ENV=development
export FLASK_DEBUG=True
python -m dartserver_app
```

### Collect Logs

When reporting issues:

```bash
# Application logs
sudo journalctl -u dartserver -n 500 > dartserver.log

# System info
uname -a > system-info.txt
python --version >> system-info.txt
pip list >> system-info.txt

# Attachment: config (without secrets)
grep -v PASSWORD /etc/dartserver/.env > config-sample.env
```

## Contact Support

For issues not covered here:
1. Check [GitHub Issues](https://github.com/letsplaydarts/dartserver-pythonapp/issues)
2. Include: error message, logs, Python version, OS
3. Create new issue if needed
