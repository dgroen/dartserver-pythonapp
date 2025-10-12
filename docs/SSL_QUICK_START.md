# SSL Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Generate SSL Certificates
```bash
./helpers/generate_ssl_certs.sh letsplaydarts.eu
```

### Step 2: Setup Local Domain
```bash
./helpers/setup_local_domain.sh letsplaydarts.eu
```

### Step 3: Enable SSL in Configuration
Edit `.env`:
```bash
FLASK_USE_SSL=True
WSO2_REDIRECT_URI=https://letsplaydarts.eu:5000/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu:5000/
```

### Step 4: Start the Server
```bash
python app.py
```

### Step 5: Access the Application
Open your browser and navigate to:
```
https://letsplaydarts.eu:5000
```

**Note:** You'll see a security warning because we're using a self-signed certificate. Click "Advanced" and "Proceed" to continue.

---

## 🔧 Common Issues

### Issue: "SSL: HTTP_REQUEST" Error
**Cause:** You're using `http://` instead of `https://`

**Fix:** Use the correct URL:
- ✅ Correct: `https://letsplaydarts.eu:5000`
- ❌ Wrong: `http://letsplaydarts.eu:5000`

### Issue: "Name or service not known"
**Cause:** Domain not in `/etc/hosts`

**Fix:**
```bash
./helpers/setup_local_domain.sh letsplaydarts.eu
```

### Issue: Browser Security Warning
**Cause:** Self-signed certificate (expected for development)

**Fix:** Click "Advanced" → "Proceed to letsplaydarts.eu (unsafe)"

Or trust the certificate system-wide:
```bash
# Linux
sudo cp ssl/cert.pem /usr/local/share/ca-certificates/letsplaydarts.eu.crt
sudo update-ca-certificates
```

---

## 🔄 Disable SSL (Development)

If you prefer to work without SSL:

1. Edit `.env`:
   ```bash
   FLASK_USE_SSL=False
   ```

2. Update redirect URIs:
   ```bash
   WSO2_REDIRECT_URI=http://localhost:5000/callback
   WSO2_POST_LOGOUT_REDIRECT_URI=http://localhost:5000/
   ```

3. Restart the server

4. Access via: `http://localhost:5000`

---

## 📚 Full Documentation

- [SSL_CONFIGURATION.md](SSL_CONFIGURATION.md) - Complete SSL setup and configuration
- [SSL_ERROR_HANDLING.md](SSL_ERROR_HANDLING.md) - SSL error handling and troubleshooting

---

## ✅ Verification Checklist

- [ ] SSL certificates generated (`ssl/cert.pem` and `ssl/key.pem` exist)
- [ ] Domain added to `/etc/hosts` (can ping `letsplaydarts.eu`)
- [ ] `.env` has `FLASK_USE_SSL=True`
- [ ] Redirect URIs use `https://letsplaydarts.eu:5000`
- [ ] Server starts without errors
- [ ] Can access `https://letsplaydarts.eu:5000` in browser

---

## 🆘 Still Having Issues?

1. Check server logs for detailed error messages
2. Verify certificate files:
   ```bash
   ls -la ssl/
   openssl x509 -in ssl/cert.pem -noout -text
   ```
3. Test SSL connection:
   ```bash
   curl -k https://letsplaydarts.eu:5000
   ```
4. Review [SSL_CONFIGURATION.md](SSL_CONFIGURATION.md) for troubleshooting

---

## 🎯 Production Deployment

For production, use Let's Encrypt instead of self-signed certificates:

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d letsplaydarts.eu

# Copy to project
sudo cp /etc/letsencrypt/live/letsplaydarts.eu/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/letsplaydarts.eu/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*.pem
```

See [SSL_CONFIGURATION.md](SSL_CONFIGURATION.md) for complete production setup guide.