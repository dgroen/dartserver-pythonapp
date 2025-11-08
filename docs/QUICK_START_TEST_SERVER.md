# Quick Start: Fix "Cannot find an application" Login Error

## What to Do RIGHT NOW

### Step 1: Start Containers (if not already running)

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d
```

### Step 2: Wait for WSO2 to Initialize

```bash
# Wait about 2-3 minutes for WSO2 to fully start
sleep 120

# Verify WSO2 is ready
docker logs darts-wso2is | grep "Server started successfully"
```

### Step 3: Register the OAuth2 Client in WSO2

**Option A: Automatic (Recommended)**

From inside the darts-app container:

```bash
docker exec -it darts-app bash
cd /app
python3 helpers/register_wso2_test_client.py
exit
```

**Option B: From Host**

```bash
cd /data/dartserver-pythonapp
# Install requests if needed
pip install requests urllib3

# Run the registration script
python3 helpers/register_wso2_test_client.py
```

### Step 4: Verify Registration

You should see output like:

```
✅ SUCCESS - Test Server OAuth2 Client is configured!
```

If you see errors, check **Troubleshooting** section below.

### Step 5: Clear Browser Cache and Login

1. Press `Ctrl+Shift+Delete` to open browser cache settings
2. Clear all cache/cookies
3. Go to: `https://test.letsplaydarts.eu`
4. Login with: `admin` / `admin`
5. ✅ Dashboard should now show your games!

---

## Troubleshooting

### Error: "Connection refused" or "Cannot connect to WSO2"

WSO2 isn't fully initialized yet.

**Fix:**

```bash
# Wait longer
sleep 180

# Check if it's running
docker ps | grep wso2is

# Check logs
docker logs darts-wso2is | tail -30
```

### Error: "Cannot find an application"

OAuth2 client wasn't registered.

**Fix:**

1. Make sure you ran Step 3 above
2. If script showed errors, check:

   ```bash
   docker logs darts-wso2is | grep -i "error\|exception" | tail -20
   ```

3. Try running the script again:

   ```bash
   docker exec -it darts-app python3 /app/helpers/register_wso2_test_client.py
   ```

### Error: "Invalid redirect URI"

Redirect URI mismatch in WSO2.

**Fix:**
Make sure `docker-compose-test.yml` has:

```yaml
WSO2_REDIRECT_URI: https://test.letsplaydarts.eu/callback
```

Then re-run the registration script.

### Error: "Failed to get access token"

Usually means the login was successful but something else is broken.

**Fix:**

1. Check CORS is configured (already done in our fix)
2. Clear browser cookies and try again
3. Check browser console for errors (F12)

---

## What Was Fixed

We already fixed two things:

1. **CORS Configuration** - Backend now accepts session cookies with API requests
   - Modified: `src/app/app.py` and `src/api_gateway/app.py`

2. **Frontend Credentials** - JavaScript now sends session cookies
   - Modified: All JavaScript files with fetch requests

3. **This Step** - Now we need to register the OAuth2 client in WSO2

---

## Full Documentation

For more detailed information, see: `docs/WSO2_TEST_SERVER_SETUP.md`

---

## Still Having Issues?

Here's the complete diagnostic command:

```bash
# 1. Check all containers are running
docker ps | grep -E "darts-wso2is|darts-app|darts-postgres"

# 2. Check WSO2 logs for errors
docker logs darts-wso2is | tail -50

# 3. Check app logs for errors
docker logs darts-app | tail -50

# 4. Verify WSO2 is responding
docker exec darts-wso2is curl -k https://localhost:9443/carbon/admin/login.jsp

# 5. Try to manually register a client
docker exec -it darts-app python3 /app/helpers/register_wso2_test_client.py

# 6. Share the output with debugging info
```

---

## Next Steps After Successful Login

1. ✅ Create some test games
2. ✅ Verify dashboard shows game statistics
3. ✅ Check history page shows your games
4. ✅ Verify mobile results page works
5. ✅ Test replay functionality

All should now work with the CORS and session cookie fixes!
