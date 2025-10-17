# Fix: Login Redirects to letsplaydarts.eu Instead of Localhost

## Problem
When clicking the login button on `http://localhost:5000`, you're redirected to `https://letsplaydarts.eu/callback` instead of `http://localhost:5000/callback`.

## Root Cause
WSO2 Identity Server has the OAuth2 client registered with `https://letsplaydarts.eu/callback` as the only allowed callback URL. It doesn't know about your localhost callback URL.

## Solution

### Step 1: Access WSO2 Admin Console
1. Open browser: **https://localhost:9443/carbon**
2. Login with WSO2 admin credentials (usually `admin` / `admin`)

### Step 2: Find the OAuth Application
1. Navigate to: **Main > Identity > Service Providers**
2. Find your application (likely named something like `darts_app` or similar)
3. Click **Edit**

### Step 3: Update Callback URLs
1. Look for the **OAuth/OpenID Connect Configuration** section
2. Find the **Callback URL** or **Authorized Redirect URIs** field
3. Add your localhost URL(s). The field should support regex patterns like:
   ```
   regexp=http://localhost:5000(/callback|/)|https://letsplaydarts.eu/callback
   ```
   
   Or if it accepts multiple URLs, add them as separate entries:
   - `http://localhost:5000/callback`
   - `https://letsplaydarts.eu/callback`

### Step 4: Save Configuration
1. Click **Update** or **Save**
2. Return to login page at `http://localhost:5000`
3. Click **Login with WSO2** again

### If You Still See Issues

**Check these URLs in WSO2 config (via SSH to Docker):**
```bash
# Find the actual registered callback URLs
docker exec wso2is-container grep -r "Callback" /opt/wso2is/repository/conf/
```

**Or manually in WSO2 Database:**
- WSO2 stores the callback URLs in the database
- For testing, you may need to directly update the `oauth2_code_credential` table

### Quick Verification
Once fixed, the login flow should work like this:
1. Click "🔐 Login with WSO2" on http://localhost:5000/login
2. Redirected to https://localhost:9443/oauth2/authorize with `redirect_uri=http://localhost:5000/callback`
3. After entering credentials → Redirected back to http://localhost:5000/callback
4. Successfully logged in! ✅

## Alternative: Use Production Domain
If you want to test with the production domain:
```bash
cp .env.localhost-https .env
# Update with your prod domain in APP_DOMAIN and APP_SCHEME
```