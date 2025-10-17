# 📋 Summary: Localhost Login Redirect Issue

## Problem Statement
**When you click "Login with WSO2" on `http://localhost:5000`, the browser redirects to `https://letsplaydarts.eu/callback` instead of `http://localhost:5000/callback`.**

## Technical Analysis

### ✅ What We Verified is Working Correctly
1. **Flask Configuration** - The `.env` file is correctly set:
   ```
   APP_DOMAIN=localhost:5000
   APP_SCHEME=http
   SESSION_COOKIE_SECURE=False
   WSO2_REDIRECT_URI=http://localhost:5000/callback
   ```

2. **Dynamic Redirect URI Generation** - The app correctly generates:
   ```
   Config.CALLBACK_URL = http://localhost:5000/callback
   ```

3. **Frontend Template** - The login button correctly uses dynamic `{{ auth_url }}`:
   ```html
   <a href="{{ auth_url }}" class="login-btn">
       🔐 Login with WSO2
   </a>
   ```

4. **Authorization URL Function** - `get_authorization_url()` correctly:
   - Calls `get_dynamic_redirect_uri()`
   - Passes the correct localhost callback to WSO2
   - Generates proper OAuth2 parameters

### ❌ Root Cause: WSO2 OAuth2 Client Configuration
**WSO2 Identity Server has the OAuth2 client registered ONLY with:**
```
Allowed Callback URLs: https://letsplaydarts.eu/callback
```

**When the app requests to redirect to `http://localhost:5000/callback`, WSO2 says:**
```
"ERROR: Redirect URI http://localhost:5000/callback is not in the allowed list"
WSO2 then falls back to: https://letsplaydarts.eu/callback
```

## The Fix

You need to add `http://localhost:5000/callback` to WSO2's allowed callback URLs for your application.

### Quick Fix Command
```bash
cd /data/dartserver-pythonapp
python3 helpers/fix-wso2-localhost-callback.py
```

This script will:
- Connect to WSO2 at https://localhost:9443
- Find your Darts application
- Add http://localhost:5000/callback to allowed URLs
- Verify success

### Manual Fix (WSO2 Web UI)
1. Open: https://localhost:9443/carbon
2. Login: admin / admin
3. Go: Main → Identity → Service Providers
4. Edit your app
5. Find: OAuth/OpenID Connect Configuration
6. Update "Callback URL" field to include:
   ```
   http://localhost:5000/callback
   ```
7. Click: Update
8. Restart browser and try again

## Flow Diagram

### Before Fix ❌
```
You: Click "Login with WSO2"
     ↓
App:  GET https://localhost:9443/oauth2/authorize
      ?client_id=local_client_id
      &redirect_uri=http://localhost:5000/callback
      &response_type=code
     ↓
WSO2: Is http://localhost:5000/callback allowed?
      Checks registered URLs: [https://letsplaydarts.eu/callback]
      NO! Not found!
      Falls back to: https://letsplaydarts.eu/callback
     ↓
Browser: Redirect to https://letsplaydarts.eu/callback
         ERROR: Can't connect (wrong domain)
     ↓
Result: Login fails ❌
```

### After Fix ✅
```
You: Click "Login with WSO2"
     ↓
App:  GET https://localhost:9443/oauth2/authorize
      ?client_id=local_client_id
      &redirect_uri=http://localhost:5000/callback
      &response_type=code
     ↓
WSO2: Is http://localhost:5000/callback allowed?
      Checks registered URLs: [
        https://letsplaydarts.eu/callback,
        http://localhost:5000/callback  ← NEWLY ADDED
      ]
      YES! Found!
     ↓
Browser: After login → Redirect to http://localhost:5000/callback
         ✓ Local app receives authorization code
     ↓
App:  Exchanges code for tokens
     ↓
Result: Login succeeds ✅ You're logged in!
```

## Why This Wasn't Caught Earlier

1. **Default Configuration** - The app is designed for production (letsplaydarts.eu)
2. **WSO2 Setup** - Initial WSO2 setup registered only production URLs
3. **Multi-Environment Support** - Localhost development requires separate callback URL registration
4. **Auto-Detection** - While the app has auto-detection for `SESSION_COOKIE_SECURE`, it can't auto-register itself in WSO2

## What Makes This Tricky

WSO2's OAuth2 security model requires:
- Each "redirect_uri" to be **explicitly registered** in the OAuth client configuration
- This is a **security feature** (prevents open redirects)
- It's **separate from** the application's own routing
- The registration is in **WSO2's database**, not in the app's .env file

Think of it like:
- **App's `.env`**: "I want to redirect to localhost"
- **WSO2 Registration**: "Here are the places I'm allowed to redirect to"
- **OAuth2 Security**: "You can only redirect where you're registered"

## Files Created/Updated

1. **FIX_LOCALHOST_LOGIN_REDIRECT.md** - This guide with manual and automatic fixes
2. **WSO2_LOCALHOST_CALLBACK_FIX.md** - WSO2-specific troubleshooting
3. **helpers/fix-wso2-localhost-callback.py** - Automated fix script
4. **LOCALHOST_LOGIN_REDIRECT_ISSUE_SUMMARY.md** - This file

## Next Steps

1. **Apply the fix:**
   ```bash
   python3 helpers/fix-wso2-localhost-callback.py
   ```

2. **Clear browser cache/cookies:**
   - Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
   - Select: All time
   - Clear: Cookies and cached images/files

3. **Test the login:**
   - Visit: http://localhost:5000
   - Click: Login button
   - Should redirect to WSO2 login (not letsplaydarts.eu) ✅

4. **Check logs if it still doesn't work:**
   ```bash
   docker-compose logs app | grep -i redirect
   docker-compose logs app | grep -i callback
   ```

## Verification Checklist

After applying the fix:
- [ ] Can access http://localhost:5000/login
- [ ] Click "Login with WSO2" redirects to https://localhost:9443
- [ ] Can enter WSO2 credentials
- [ ] After login, redirected to http://localhost:5000 (not letsplaydarts.eu)
- [ ] You see "You are logged in" or similar message
- [ ] Session works and you can navigate the app

## Questions?

- **Configuration details**: See `LOCALHOST_QUICKSTART.md`
- **Troubleshooting**: See `docs/LOCALHOST_LOGIN_FIX.md`
- **Technical deep dive**: See `docs/LOCALHOST_LOGIN_IMPLEMENTATION.md`
- **Full documentation**: Check `docs/` directory