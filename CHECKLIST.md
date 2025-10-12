# WSO2 IS Redirect Fix - Action Checklist

## ✅ Completed (Automated)

- [x] Fixed `.env` file - removed port 5000 from redirect URIs
- [x] Updated `nginx/nginx.conf` - added X-Forwarded-Host header
- [x] Updated `docker-compose-wso2.yml` - fixed default redirect URIs
- [x] Verified `wso2is-config/deployment.toml` - configuration is correct
- [x] Created documentation and verification script

## ⚠️ Required Manual Actions

### 1. Update WSO2 IS OAuth Application

**Status**: ⏳ PENDING - YOU MUST DO THIS

**Steps**:
1. Open: https://letsplaydarts.eu/auth/carbon
2. Login: admin / admin
3. Navigate: Main Menu → Identity → Service Providers → List
4. Find your application (Client ID: `gKL8KC2FkWIz2r3553vraJ8pf8Ma`)
5. Edit → Inbound Authentication Configuration → OAuth/OpenID Connect Configuration → Edit
6. Update Callback URL to: `https://letsplaydarts.eu/callback`
7. Click "Update"

**Why**: WSO2 IS validates redirect URIs against registered callbacks. Without this, you'll get "invalid_redirect_uri" error.

### 2. Restart Docker Services

**Status**: ⏳ PENDING - YOU MUST DO THIS

**Command**:
```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d
```

**Wait**: ~2 minutes for WSO2 IS to fully start

### 3. Verify Configuration

**Status**: ⏳ PENDING - RECOMMENDED

**Command**:
```bash
./scripts/verify-redirect-config.sh
```

**Expected Output**:
- ✓ Nginx container is running
- ✓ Nginx configuration is valid
- ✓ X-Forwarded-Host header is configured
- ✓ X-Forwarded-Proto header is configured

### 4. Test Login Flow

**Status**: ⏳ PENDING - REQUIRED

**Steps**:
1. Open browser: https://letsplaydarts.eu/login
2. Open DevTools (F12) → Network tab
3. Click login button
4. Check the authorization request URL contains:
   - ✅ `redirect_uri=https://letsplaydarts.eu/callback`
   - ❌ NOT `redirect_uri=http://localhost:5000/callback`
   - ❌ NOT `redirect_uri=https://letsplaydarts.eu:5000/callback`
5. Complete login
6. Verify redirect to: `https://letsplaydarts.eu/callback?code=...`

## Quick Reference

### Current Configuration

**Environment Variables** (`.env`):
```
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_CLIENT_ID=gKL8KC2FkWIz2r3553vraJ8pf8Ma
WSO2_CLIENT_SECRET=c1nJheSbpiBxsQPKvdm_FLU3rssa
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu/
```

**Expected Flow**:
```
User → https://letsplaydarts.eu/login
     → Nginx (adds X-Forwarded headers)
     → Flask (ProxyFix processes headers)
     → Dynamic redirect URI: https://letsplaydarts.eu/callback
     → WSO2 IS authorization
     → Callback: https://letsplaydarts.eu/callback?code=...
     → Success!
```

### Troubleshooting Commands

**Check nginx headers**:
```bash
docker logs darts-app 2>&1 | grep "Request headers" | tail -1
```

**Check dynamic redirect URI**:
```bash
docker logs darts-app 2>&1 | grep "Dynamic redirect URI" | tail -5
```

**Check WSO2 IS logs**:
```bash
docker logs darts-wso2is 2>&1 | grep -i redirect | tail -10
```

**Restart specific service**:
```bash
docker-compose -f docker-compose-wso2.yml restart darts-app
docker-compose -f docker-compose-wso2.yml restart nginx
```

## Summary

**What was wrong**: 
- `.env` had redirect URIs with port 5000: `https://letsplaydarts.eu:5000/callback`
- Nginx wasn't passing `X-Forwarded-Host` header
- WSO2 IS OAuth app likely has old callback URL registered

**What was fixed**:
- ✅ Removed port from redirect URIs in `.env`
- ✅ Added `X-Forwarded-Host` header to nginx config
- ✅ Updated docker-compose defaults

**What you need to do**:
1. ⚠️ Update WSO2 IS OAuth application callback URL
2. ⚠️ Restart services
3. ⚠️ Test the login flow

## Need Help?

- Full documentation: `REDIRECT_FIX_SUMMARY.md`
- Detailed guide: `docs/wso2-redirect-fix.md`
- Verification script: `scripts/verify-redirect-config.sh`