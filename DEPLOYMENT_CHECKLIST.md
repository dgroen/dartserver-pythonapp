# Deployment Checklist - letsplaydarts.eu

## Pre-Deployment

### ✅ Code Changes

- [x] SSL error handling implemented
- [x] Dynamic redirect URIs implemented
- [x] All tests passing (38/38)
- [x] Code linting passed
- [x] Documentation created

### ⬜ WSO2 Identity Server Configuration

- [ ] Log in to WSO2 IS Management Console: `https://your-wso2-server:9443/carbon`
- [ ] Navigate to: Main > Identity > Service Providers
- [ ] Select/Create your application
- [ ] Add redirect URIs (use regex pattern):

  ```
  regexp=(https://localhost:5000/callback|https://letsplaydarts\.eu:5001/callback|https://letsplaydarts\.eu/callback)
  ```

- [ ] Add post-logout redirect URIs:

  ```
  regexp=(https://localhost:5000/|https://letsplaydarts\.eu:5001/|https://letsplaydarts\.eu/)
  ```

- [ ] Save configuration
- [ ] Copy Client ID and Client Secret

### ⬜ Environment Configuration

- [ ] Update `.env` file with WSO2 credentials:

  ```bash
  WSO2_IS_URL=https://your-wso2-server:9443
  WSO2_CLIENT_ID=<from-wso2>
  WSO2_CLIENT_SECRET=<from-wso2>
  WSO2_IS_VERIFY_SSL=False  # or True if using valid cert
  ```

- [ ] Enable SSL:

  ```bash
  FLASK_USE_SSL=True
  FLASK_HOST=0.0.0.0
  FLASK_PORT=5000
  ```

- [ ] Set strong secret key:

  ```bash
  SECRET_KEY=$(openssl rand -hex 32)
  ```

- [ ] Configure token validation:

  ```bash
  JWT_VALIDATION_MODE=introspection
  WSO2_IS_INTROSPECT_USER=admin
  WSO2_IS_INTROSPECT_PASSWORD=<strong-password>
  ```

- [ ] Secure .env file:

  ```bash
  chmod 600 .env
  ```

### ⬜ SSL Certificates

**Option 1: Let's Encrypt (Recommended for Production)**

- [ ] Install Certbot:

  ```bash
  sudo apt-get install certbot python3-certbot-nginx
  ```

- [ ] Generate certificate:

  ```bash
  sudo certbot --nginx -d letsplaydarts.eu
  ```

- [ ] Verify auto-renewal:

  ```bash
  sudo certbot renew --dry-run
  ```

- [ ] Copy certificates to application:

  ```bash
  sudo cp /etc/letsencrypt/live/letsplaydarts.eu/fullchain.pem ssl/cert.pem
  sudo cp /etc/letsencrypt/live/letsplaydarts.eu/privkey.pem ssl/key.pem
  sudo chown $USER:$USER ssl/*.pem
  ```

**Option 2: Self-Signed (Development Only)**

- [ ] Generate self-signed certificate:

  ```bash
  mkdir -p ssl
  openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout ssl/key.pem -out ssl/cert.pem -days 365 \
    -subj "/CN=letsplaydarts.eu" \
    -addext "subjectAltName=DNS:letsplaydarts.eu,DNS:localhost"
  ```

### ⬜ Network Configuration

**DNS**

- [ ] Verify DNS A record:

  ```bash
  nslookup letsplaydarts.eu
  # Should return your public IP
  ```

**Firewall**

- [ ] Allow required ports:

  ```bash
  sudo ufw allow 5000/tcp
  sudo ufw allow 5001/tcp
  sudo ufw allow 443/tcp
  sudo ufw allow 22/tcp  # SSH
  ```

- [ ] Enable firewall:

  ```bash
  sudo ufw enable
  ```

- [ ] Verify status:

  ```bash
  sudo ufw status
  ```

**Router/Port Forwarding**

- [ ] Forward port 5000 → Internal server IP
- [ ] Forward port 5001 → Internal server IP
- [ ] Forward port 443 → Internal server IP
- [ ] Test from external network

---

## Deployment

### ⬜ Application Deployment

- [ ] Pull latest code:

  ```bash
  cd /data/dartserver-pythonapp
  git pull origin main
  ```

- [ ] Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

- [ ] Run tests:

  ```bash
  pytest tests/unit/test_auth.py -v
  ```

- [ ] Start application:

  ```bash
  python app.py
  ```

- [ ] Verify startup messages:

  ```
  ✅ SSL error handling patch applied
  🔒 Starting Darts Game Server with SSL/HTTPS
  ```

### ⬜ Reverse Proxy (Optional but Recommended)

**Nginx Configuration**

- [ ] Install Nginx:

  ```bash
  sudo apt-get install nginx
  ```

- [ ] Create configuration:

  ```bash
  sudo nano /etc/nginx/sites-available/letsplaydarts
  ```

- [ ] Add configuration (see docs/WSO2_MULTI_DOMAIN_SETUP.md)
- [ ] Enable site:

  ```bash
  sudo ln -s /etc/nginx/sites-available/letsplaydarts /etc/nginx/sites-enabled/
  ```

- [ ] Test configuration:

  ```bash
  sudo nginx -t
  ```

- [ ] Reload Nginx:

  ```bash
  sudo systemctl reload nginx
  ```

### ⬜ Process Management (Production)

**Systemd Service**

- [ ] Create service file:

  ```bash
  sudo nano /etc/systemd/system/darts-app.service
  ```

- [ ] Add service configuration:

  ```ini
  [Unit]
  Description=Darts Game Server
  After=network.target

  [Service]
  Type=simple
  User=your-user
  WorkingDirectory=/data/dartserver-pythonapp
  Environment="PATH=/data/dartserver-pythonapp/.venv/bin"
  ExecStart=/data/dartserver-pythonapp/.venv/bin/python app.py
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  ```

- [ ] Enable and start service:

  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable darts-app
  sudo systemctl start darts-app
  ```

- [ ] Check status:

  ```bash
  sudo systemctl status darts-app
  ```

---

## Testing

### ⬜ Local Testing

- [ ] Test HTTPS access:

  ```bash
  curl -k https://localhost:5000
  ```

- [ ] Test HTTP rejection (should see clean error):

  ```bash
  curl http://localhost:5000
  ```

- [ ] Verify error message in console:

  ```
  ⚠️  SSL Protocol Mismatch Detected
  ```

### ⬜ Public Domain Testing

**From External Network:**

- [ ] Test custom port: `https://letsplaydarts.eu:5001`
- [ ] Test standard HTTPS: `https://letsplaydarts.eu`
- [ ] Verify SSL certificate is valid (no browser warnings for Let's Encrypt)

### ⬜ WSO2 Login Testing

**Test from localhost:**

- [ ] Navigate to: `https://localhost:5000`
- [ ] Click "Login"
- [ ] Should redirect to WSO2 IS
- [ ] Enter credentials
- [ ] Should redirect back to application
- [ ] Verify logged in successfully
- [ ] Check logs for: `Dynamic redirect URI: https://localhost:5000/callback`

**Test from custom port:**

- [ ] Navigate to: `https://letsplaydarts.eu:5001`
- [ ] Click "Login"
- [ ] Complete login flow
- [ ] Verify success
- [ ] Check logs for: `Dynamic redirect URI: https://letsplaydarts.eu:5001/callback`

**Test from standard HTTPS:**

- [ ] Navigate to: `https://letsplaydarts.eu`
- [ ] Click "Login"
- [ ] Complete login flow
- [ ] Verify success
- [ ] Check logs for: `Dynamic redirect URI: https://letsplaydarts.eu/callback`

### ⬜ Logout Testing

- [ ] Click "Logout" from each domain
- [ ] Verify redirected to correct post-logout URI
- [ ] Verify session cleared

---

## Monitoring

### ⬜ Log Monitoring

- [ ] Set up log rotation:

  ```bash
  sudo nano /etc/logrotate.d/darts-app
  ```

- [ ] Monitor application logs:

  ```bash
  tail -f logs/app.log
  ```

- [ ] Monitor Nginx logs (if using):

  ```bash
  tail -f /var/log/nginx/access.log
  tail -f /var/log/nginx/error.log
  ```

### ⬜ Health Checks

- [ ] Create health check endpoint monitoring
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Configure alerts for downtime

---

## Security Hardening

### ⬜ Application Security

- [ ] Verify HTTPS enforced (no HTTP access)
- [ ] Check .env file permissions: `ls -la .env` (should be 600)
- [ ] Verify strong secrets in use
- [ ] Enable HSTS headers (if using Nginx)
- [ ] Configure rate limiting (if using Nginx)

### ⬜ Server Security

- [ ] Update system packages:

  ```bash
  sudo apt-get update && sudo apt-get upgrade
  ```

- [ ] Configure fail2ban:

  ```bash
  sudo apt-get install fail2ban
  sudo systemctl enable fail2ban
  ```

- [ ] Disable root SSH login
- [ ] Use SSH keys instead of passwords
- [ ] Keep only necessary ports open

---

## Backup

### ⬜ Backup Configuration

- [ ] Backup .env file (securely)
- [ ] Backup SSL certificates
- [ ] Backup database (if applicable)
- [ ] Document WSO2 IS configuration
- [ ] Create restore procedure documentation

---

## Documentation

### ⬜ Team Documentation

- [ ] Share access credentials (securely)
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document rollback procedure

---

## Post-Deployment

### ⬜ Verification

- [ ] All access methods working (localhost, custom port, standard HTTPS)
- [ ] WSO2 login working from all domains
- [ ] SSL error handling working (clean messages, no stack traces)
- [ ] Logs showing dynamic redirect URIs
- [ ] No errors in application logs
- [ ] Performance acceptable

### ⬜ User Acceptance Testing

- [ ] Test with real users
- [ ] Verify mobile access
- [ ] Test different browsers
- [ ] Verify WebSocket connections (if applicable)

---

## Rollback Plan

### ⬜ If Issues Occur

- [ ] Stop application:

  ```bash
  sudo systemctl stop darts-app
  ```

- [ ] Revert to previous version:

  ```bash
  git checkout <previous-commit>
  ```

- [ ] Restart application:

  ```bash
  sudo systemctl start darts-app
  ```

- [ ] Verify rollback successful
- [ ] Investigate issues
- [ ] Document problems

---

## Success Criteria

✅ Application starts without errors  
✅ SSL error handling active (clean messages)  
✅ Login works from all domains  
✅ Dynamic redirect URIs working  
✅ SSL certificates valid  
✅ All tests passing  
✅ No security warnings  
✅ Performance acceptable  
✅ Monitoring in place  
✅ Documentation complete

---

## Support Contacts

- **WSO2 IS Admin**: [contact info]
- **Server Admin**: [contact info]
- **DNS Provider**: [contact info]
- **SSL Certificate Provider**: [contact info]

---

## Notes

- Keep this checklist updated as deployment evolves
- Document any deviations from the plan
- Record any issues encountered and solutions
- Update documentation based on lessons learned

---

**Deployment Date**: **\*\***\_\_\_**\*\***  
**Deployed By**: **\*\***\_\_\_**\*\***  
**Status**: ⬜ In Progress / ⬜ Complete / ⬜ Rolled Back
