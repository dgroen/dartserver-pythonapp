# Fix Post-Login and Post-Logout Redirect Issues

## Problem
Error: **"Post logout URI does not match with registered callback URI"**

This occurs because WSO2 Identity Server requires **both** the callback URI (for login) and the post-logout redirect URI to be registered in the OAuth2 application configuration.

## Root Cause
The OAuth2 application in WSO2 IS only has the callback URI registered (`https://letsplaydarts.eu/callback`), but not the post-logout redirect URI (`https://letsplaydarts.eu/`).

## Solution: Register Post-Logout Redirect URI in WSO2 IS

### Step 1: Access WSO2 IS Management Console

1. Open your browser and navigate to:
   ```
   https://letsplaydarts.eu/auth/carbon
   ```

2. Login with admin credentials:
   - **Username**: `admin`
   - **Password**: `admin`

### Step 2: Edit the Service Provider

1. In the left menu, navigate to:
   ```
   Main → Identity → Service Providers → List
   ```

2. Find your application (likely named something like `DartsApp` or similar) and click **Edit**

### Step 3: Configure OAuth/OpenID Connect

1. Scroll down to **Inbound Authentication Configuration**
2. Click on **OAuth/OpenID Connect Configuration**
3. Click **Edit**

### Step 4: Add Allowed Callback URLs

In the **Callback Url** field, you should see:
```
https://letsplaydarts.eu/callback
```

**Update it to include BOTH the callback and post-logout URIs** (comma-separated):
```
https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
```

**OR use a regex pattern (recommended for flexibility):**
```
regexp=https://letsplaydarts\.eu(/callback|/)
```

### Step 5: Save Configuration

1. Click **Update** to save the OAuth configuration
2. Click **Update** again to save the Service Provider configuration

### Step 6: Test the Flow

1. **Test Login**:
   - Navigate to `https://letsplaydarts.eu`
   - Click the login button
   - After successful authentication, you should be redirected back to `https://letsplaydarts.eu`

2. **Test Logout**:
   - Click the logout button
   - After logout, you should be redirected to `https://letsplaydarts.eu/`
   - No error message should appear

## Alternative Solution: Using Regex for Multiple URIs

If you want to support multiple redirect URIs (for development and production), use this regex pattern:

```
regexp=(https://localhost:5000/(callback|)|https://letsplaydarts\.eu/(callback|))
```

This allows:
- `https://localhost:5000/callback` (login - local dev)
- `https://localhost:5000/` (logout - local dev)
- `https://letsplaydarts.eu/callback` (login - production)
- `https://letsplaydarts.eu/` (logout - production)

## Verification

After making these changes, check the application logs:

```bash
# Check Flask app logs
docker logs darts-app 2>&1 | tail -50

# Check WSO2 IS logs
docker logs wso2is 2>&1 | tail -50
```

Look for successful redirects without errors.

## Common Issues

### Issue 1: Still Getting "Invalid Redirect URI" Error

**Solution**: Make sure you clicked **Update** twice:
1. Once in the OAuth/OpenID Connect Configuration dialog
2. Once more in the Service Provider edit page

### Issue 2: Changes Not Taking Effect

**Solution**: Clear your browser cache and cookies, or try in an incognito window.

### Issue 3: Can't Access Management Console

**Solution**: Check if WSO2 IS is running:
```bash
docker ps | grep wso2is
```

If not running, start it:
```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml up -d wso2is
```

## Technical Details

### Current Configuration

**Environment Variables** (`.env`):
```bash
WSO2_REDIRECT_URI=https://letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://letsplaydarts.eu/
```

**Dynamic URI Generation** (`auth.py`):
- Login callback: `get_dynamic_redirect_uri()` → `https://letsplaydarts.eu/callback`
- Logout redirect: `get_dynamic_post_logout_redirect_uri()` → `https://letsplaydarts.eu/`

### Why This Happens

WSO2 Identity Server validates all redirect URIs for security reasons:
1. **Authorization Code Flow**: Validates `redirect_uri` parameter against registered callbacks
2. **Logout Flow**: Validates `post_logout_redirect_uri` parameter against registered callbacks

Both URIs must be explicitly registered in the Service Provider configuration.

## Next Steps

After fixing the redirect URIs:
1. ✅ Test login flow
2. ✅ Test logout flow
3. ✅ Verify no error messages appear
4. ✅ Check that you're redirected to the correct pages

## Need Help?

If you're still experiencing issues:
1. Check the browser console for JavaScript errors
2. Check Flask app logs: `docker logs darts-app`
3. Check WSO2 IS logs: `docker logs wso2is`
4. Verify nginx is routing correctly: `docker logs nginx`