# WSO2 Test Server OAuth2 Setup

## Problem

When logging in to test.letsplaydarts.eu, you get:

```
"Cannot find an application associated with the given consumer key."
```

This error means the OAuth2 application is **not registered in WSO2 Identity Server**.

## Solution

You need to register the test server's OAuth2 client in WSO2 before the first login attempt.

## Step-by-Step Setup

### 1. Start the Docker Containers

First, ensure all containers are running:

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d
```

**Wait for WSO2 to initialize** (this takes 2-3 minutes). Check status:

```bash
docker logs darts-wso2is | tail -20
```

Look for messages like:

```
[2024-XX-XX XX:XX:XX] INFO {org.wso2.carbon.core.init.CarbonServerManager}
- Server started successfully
```

### 2. Register the OAuth2 Client

Once WSO2 is ready, run the registration script **from inside a Docker container**:

```bash
docker exec darts-wso2is python3 << 'EOF'
# This will be run inside the container
# The script will connect to WSO2 using internal Docker DNS (wso2is:9443)
EOF
```

**Better approach - Run from the host using the helper script:**

```bash
cd /data/dartserver-pythonapp
python3 helpers/register_wso2_test_client.py
```

If running on Docker host, first enter the darts-app container to run the script:

```bash
docker exec -it darts-app python3 /app/helpers/register_wso2_test_client.py
```

### 3. Expected Output

Success output:

```
======================================================================
WSO2 Identity Server - Register Test Server OAuth2 Client
======================================================================

🔧 Configuration:
   WSO2 IS URL: https://wso2is:9443
   Client ID: QG32mHju2Gs5JJTh4RO60982cxsa
   Client Name: DartsTestServer

🔍 Checking if client already exists...
ℹ️  Client does not exist - will create new one

📤 Registering new OAuth2 client...
   Client ID: QG32mHju2Gs5JJTh4RO60982cxsa
   Client Name: DartsTestServer
   Redirect URIs:
      - https://test.letsplaydarts.eu/callback
      - https://test.letsplaydarts.eu/

✅ OAuth2 client registered successfully!

📋 Client Details:
{
  "client_id": "QG32mHju2Gs5JJTh4RO60982cxsa",
  "client_secret": "DZfn3qolUxKeXQbJ_7bwhmfZNLWm8wdVwS5_1oR12YAa",
  "client_name": "DartsTestServer",
  "redirect_uris": [
    "https://test.letsplaydarts.eu/callback",
    "https://test.letsplaydarts.eu/"
  ],
  ...
}

======================================================================
✅ SUCCESS - Test Server OAuth2 Client is configured!
======================================================================

🚀 You can now:
   - Deploy the Docker containers
   - Login at: https://test.letsplaydarts.eu/login
   - Access the dashboard at: https://test.letsplaydarts.eu/dashboard
```

### 4. Test the Login

1. Open browser and go to: `https://test.letsplaydarts.eu`
2. You should be redirected to login page
3. Enter credentials (default: admin/admin for WSO2)
4. You should be redirected back to the dashboard
5. Dashboard and History should now show your games ✅

## Troubleshooting

### Error: "Cannot connect to WSO2"

**Problem:** The WSO2 container is not running or not fully initialized

**Solution:**

```bash
# Check if container is running
docker ps | grep wso2is

# Check logs
docker logs darts-wso2is

# If not running, start it
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d wso2is

# Wait 2-3 minutes for initialization
sleep 120

# Check health
docker exec darts-wso2is curl -k https://localhost:9443/carbon/admin/login.jsp
```

### Error: "Cannot find application"

**Problem:** OAuth2 client was not successfully registered

**Solution:**

1. Verify WSO2 is fully initialized (check logs above)
2. Run the registration script again:

   ```bash
   docker exec -it darts-app python3 /app/helpers/register_wso2_test_client.py
   ```

3. Check for error messages in output
4. If script shows "FAILED", check WSO2 logs for details:

   ```bash
   docker logs darts-wso2is | grep -i "error\|exception" | tail -20
   ```

### Error: "Invalid redirect URI"

**Problem:** Redirect URI in WSO2 doesn't match the one configured in the app

**Solution:**
The redirect URIs configured are:

- `https://test.letsplaydarts.eu/callback`
- `https://test.letsplaydarts.eu/`

Ensure `docker-compose-test.yml` has:

```yaml
WSO2_REDIRECT_URI: https://test.letsplaydarts.eu/callback
WSO2_POST_LOGOUT_REDIRECT_URI: https://test.letsplaydarts.eu/
```

If changed, re-run the registration script and restart the app container.

### Error: "401 Unauthorized"

**Problem:** Admin credentials are incorrect

**Solution:**
Check WSO2 admin password:

```bash
# Default is "admin"
# Check docker-compose-wso2.yml for any overrides
grep -i "admin" docker-compose-wso2.yml
```

Update the registration script if password differs, or manually register via WSO2 Admin Console.

## Manual Registration (Alternative)

If the script doesn't work, manually register via WSO2 Admin Console:

### Access WSO2 Admin Console

1. Open: `https://wso2is:9443/carbon/`
2. Login: `admin` / `admin`
3. Navigate to: **Main > Identity > Service Providers > Add**

### Create Service Provider

1. Click **Add**
2. Enter **Service Provider Name**: `DartsTestServer`
3. Click **Register**

### Configure OAuth

1. Expand: **Inbound Authentication Configuration**
2. Expand: **OAuth/OpenID Connect Configuration**
3. Click: **Configure**
4. Set **Callback Url**:

   ```
   https://test.letsplaydarts.eu/callback
   ```

5. Set **Grant Types**: `Authorization Code`, `Refresh Token`
6. Click **Add**
7. Copy the generated:
   - **OAuth Client Key** (Client ID)
   - **OAuth Client Secret**

### Update Configuration

Update `docker-compose-test.yml`:

```yaml
WSO2_CLIENT_ID: <your_client_id>
WSO2_CLIENT_SECRET: <your_client_secret>
```

Restart the app:

```bash
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml restart darts-app
```

## Files Modified/Created

- `helpers/register_wso2_test_client.py` - OAuth2 registration script
- `docs/WSO2_TEST_SERVER_SETUP.md` - This documentation

## Related Documentation

- `CORS_CREDENTIALS_FIX.md` - Backend CORS configuration for session cookies
- `SESSION_COOKIES_FIX.md` - Frontend fetch API configuration
- `AUTHENTICATION_FLOW.md` - Overall authentication architecture
- `AUTHENTICATION_SETUP.md` - WSO2 configuration details
