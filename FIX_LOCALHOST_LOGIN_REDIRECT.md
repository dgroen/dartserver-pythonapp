# 🔧 Fix: Login Redirects to letsplaydarts.eu

## ⚠️ Problem

When you click "Login with WSO2" on `http://localhost:5000`, the redirect goes to `https://letsplaydarts.eu/callback` instead of `http://localhost:5000/callback`.

## 🎯 Root Cause

The OAuth2 client in WSO2 Identity Server is only registered with production domain callbacks. It doesn't know localhost is allowed.

```
❌ What's happening now:
    http://localhost:5000/login
         ↓ (click login)
    WSO2 checks: Is http://localhost:5000/callback allowed?
         ↓ (NO! Only letsplaydarts.eu is allowed)
    Redirect to: https://letsplaydarts.eu/callback
         ↓ (can't connect, login fails)

✅ What should happen:
    http://localhost:5000/login
         ↓ (click login)
    WSO2 checks: Is http://localhost:5000/callback allowed?
         ↓ (YES! Localhost is registered)
    Login success! ✓
```

## 🚀 Quick Fix Options

### Option 1: Automatic Fix (Recommended)

```bash
cd /data/dartserver-pythonapp
python3 helpers/fix-wso2-localhost-callback.py
```

This script will:

- Connect to WSO2
- Find the Darts application
- Add `http://localhost:5000/callback` to allowed URLs
- Verify success

### Option 2: Manual Fix via WSO2 UI

1. **Open WSO2 Admin Console**
   - URL: <https://localhost:9443/carbon>
   - Username: `admin`
   - Password: `admin`

2. **Navigate to Service Providers**
   - Click: Main → Identity → Service Providers

3. **Find and Edit Your App**
   - Look for your application (likely "darts_app" or similar)
   - Click: Edit

4. **Update OAuth/OpenID Connect Configuration**
   - Find: "OAuth/OpenID Connect Configuration" section
   - Look for: "Callback URL" or "Authorized Redirect URIs" field
   - Add: `http://localhost:5000/callback`

   It should look like one of these:

   ```
   # Option A: Multiple URLs
   http://localhost:5000/callback
   https://letsplaydarts.eu/callback

   # Option B: Regex pattern
   regexp=http://localhost:5000(/callback|/)|https://letsplaydarts.eu/callback

   # Option C: As-is (if it shows)
   ["http://localhost:5000/callback", "https://letsplaydarts.eu/callback"]
   ```

5. **Save Changes**
   - Click: Update or Save

### Option 3: CLI Fix via Docker

```bash
# Get WSO2 container ID
docker-compose -f docker-compose-wso2.yml ps

# Access WSO2 database directly
docker exec -it <wso2_container_id> bash

# Find the app ID
curl -k -u admin:admin https://localhost:9443/api/server/v1/service-providers | jq

# Update callback URLs (requires more complex curl)
# See: https://is.docs.wso2.com/en/latest/references/oauth-2-0-rest-api/
```

## ✅ Verify the Fix

After applying the fix:

1. **Clear browser cache/cookies**
   - Press: `Ctrl+Shift+Delete` (or Cmd+Shift+Delete on Mac)
   - Clear: All cookies and cache
   - Close browser completely

2. **Test the login**
   - Visit: <http://localhost:5000>
   - Click: "🔐 Login with WSO2"
   - Expected: Redirect to WSO2 login at `https://localhost:9443`
   - Enter: WSO2 credentials
   - Expected: Redirect back to `http://localhost:5000` ✅

3. **Check server logs for confirmation**
   - Look for: `"Localhost redirect URI: http://localhost:5000/callback"`
   - This confirms the redirect is being generated correctly

## 🐛 Still Not Working?

### Issue: Still redirecting to letsplaydarts.eu

- **Check**: Is the fix actually applied? (Restart browser, clear cache)
- **Check**: WSO2 container is running: `docker ps | grep wso2`
- **Try**: Restarting WSO2: `docker-compose -f docker-compose-wso2.yml restart`

### Issue: "Invalid redirect_uri" error

- **Problem**: The `redirect_uri` parameter doesn't match exactly
- **Fix**: Make sure it's exactly: `http://localhost:5000/callback` (not https, correct port)

### Issue: "Invalid state parameter" or session lost

- **Problem**: Cookies aren't working properly
- **Fix**: Check that `.env` has `SESSION_COOKIE_SECURE=False` for localhost HTTP
- **Check**: Look at logs for: `SESSION_COOKIE_SECURE forced to False`

### Issue: Can't connect to <https://localhost:9443>

- **Problem**: SSL certificate issue or WSO2 not running
- **Fix 1**: Make sure WSO2 is running:

  ```bash
  docker-compose -f docker-compose-wso2.yml up -d
  docker-compose -f docker-compose-wso2.yml logs wso2is
  ```

- **Fix 2**: For `requests` library, SSL verification is disabled (safe for localhost)

## 📋 Configuration Checklist

- [ ] `.env` file has `APP_DOMAIN=localhost:5000`
- [ ] `.env` file has `APP_SCHEME=http`
- [ ] `.env` file has `SESSION_COOKIE_SECURE=False`
- [ ] WSO2 callback URL includes `http://localhost:5000/callback`
- [ ] Browser cookies cleared
- [ ] WSO2 container is running
- [ ] App container is running (or running locally)

## 📚 Related Documentation

- See: `LOCALHOST_QUICKSTART.md` - Quick start guide
- See: `docs/LOCALHOST_LOGIN_FIX.md` - Detailed troubleshooting
- See: `WSO2_LOCALHOST_CALLBACK_FIX.md` - WSO2-specific fixes

## 🆘 Need More Help?

1. **Check logs:**

   ```bash
   # Flask app logs
   docker-compose logs app

   # WSO2 logs
   docker-compose logs wso2is
   ```

2. **Enable debug logging:**
   - Add to `.env`: `FLASK_DEBUG=True`
   - Look for lines like: "Dynamic redirect URI: ..."

3. **Test redirect URI generation:**

   ```bash
   python3 -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   from src.core.config import Config
   from src.core.auth import get_dynamic_redirect_uri
   print(f'Config CALLBACK_URL: {Config.CALLBACK_URL}')
   "
   ```

---

✨ Once this is fixed, localhost login will work perfectly!
