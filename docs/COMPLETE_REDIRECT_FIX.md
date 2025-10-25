# Complete Redirect Fix - All Issues

## Overview

There are **TWO separate issues** with the redirect flow:

1. ✅ **Missing `/auth` prefix** - Fixed in configuration
2. ⚠️ **Post-logout redirect URI not registered** - Requires manual configuration

## Issue 1: Missing /auth Prefix ✅ FIXED

### Problem

Redirects go to `https://letsplaydarts.eu/oauth2/authorize` instead of `https://letsplaydarts.eu/auth/oauth2/authorize`

### Solution Applied

Added `proxy_context_path = "/auth"` to `deployment.toml`

### How to Apply

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml restart wso2is
```

Wait 2-3 minutes for WSO2 IS to start.

### Details

See: `FIX_MISSING_AUTH_PREFIX.md`

---

## Issue 2: Post-Logout Redirect URI ⚠️ REQUIRES ACTION

### Problem

Error: "Post logout URI does not match with registered callback URI"

### Solution Required

Register both callback and post-logout URIs in WSO2 IS Service Provider

### How to Apply

#### Step 1: Access WSO2 IS Console

```
URL: https://letsplaydarts.eu/auth/carbon
Username: admin
Password: admin
```

#### Step 2: Navigate to Service Providers

```
Main → Identity → Service Providers → List
```

#### Step 3: Edit Your Application

- Find your OAuth2 application
- Click "Edit"

#### Step 4: Update Callback URLs

1. Expand "Inbound Authentication Configuration"
2. Click "Configure" under "OAuth/OpenID Connect Configuration"
3. Update "Callback Url" field

**Change from:**

```
https://letsplaydarts.eu/callback
```

oregexp=(<https://localhost:5000/callback|https://letsplaydarts\.eu:5000/callback|https://letsplaydarts\.eu/callback>)
**Change to (regex pattern):**

```
regexp=https://letsplaydarts\.eu(/callback|/)
```

**OR (comma-separated):**

```
https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
```

#### Step 5: Save

1. Click "Update" (OAuth dialog)
2. Click "Update" (Service Provider page)

### Details

See: `FIX_REDIRECT_URIS.md` or `QUICK_FIX_REDIRECTS.md`

---

## Complete Fix Checklist

### Part 1: Configuration Fix (Done ✅)

- [x] Added `proxy_context_path = "/auth"` to deployment.toml
- [ ] Restart WSO2 IS container
- [ ] Wait for startup (2-3 minutes)
- [ ] Verify URLs include `/auth` prefix

### Part 2: Service Provider Fix (To Do ⚠️)

- [ ] Access WSO2 IS Management Console
- [ ] Navigate to Service Providers
- [ ] Edit OAuth2 application
- [ ] Update Callback URLs to include both URIs
- [ ] Save configuration
- [ ] Test login and logout flows

---

## Quick Start

### Step 1: Restart WSO2 IS (Apply Configuration Fix)

```bash
cd /data/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml restart wso2is
```

### Step 2: Wait for Startup

```bash
docker logs -f wso2is
# Wait for: "WSO2 Carbon started in X sec"
```

### Step 3: Update Service Provider (Manual)

```bash
# Run this script for instructions
./update_wso2_callback_urls.sh
```

Or follow the steps in `QUICK_FIX_REDIRECTS.md`

### Step 4: Test Everything

1. Navigate to: `https://letsplaydarts.eu`
2. Click "Login" → Should work ✅
3. Authenticate → Should redirect back ✅
4. Click "Logout" → Should work ✅
5. Should redirect to home page ✅

---

## What Each Fix Does

### Fix 1: proxy_context_path

**Before:**

```
WSO2 IS generates: /oauth2/authorize
Browser tries: https://letsplaydarts.eu/oauth2/authorize
Result: ❌ 404 Error (nginx doesn't route this)
```

**After:**

```
WSO2 IS generates: /auth/oauth2/authorize
Browser tries: https://letsplaydarts.eu/auth/oauth2/authorize
Result: ✅ Success (nginx routes to WSO2 IS)
```

### Fix 2: Callback URL Registration

**Before:**

```
Registered: https://letsplaydarts.eu/callback
Login redirect: /callback ✅ Works
Logout redirect: / ❌ Fails (not registered)
```

**After:**

```
Registered: regexp=https://letsplaydarts\.eu(/callback|/)
Login redirect: /callback ✅ Works
Logout redirect: / ✅ Works
```

---

## Architecture Overview

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ https://letsplaydarts.eu/auth/*
       ↓
┌─────────────┐
│    Nginx    │ ← Reverse Proxy
│  (Port 443) │    Routes /auth/* to WSO2 IS
└──────┬──────┘
       │
       │ /auth/* → wso2is:9443/*
       ↓
┌─────────────┐
│  WSO2 IS    │
│ (Port 9443) │ ← Needs to know about /auth prefix
└─────────────┘    via proxy_context_path
```

### URL Flow

**Login Flow:**

```
1. User clicks "Login"
2. Flask → Browser: Redirect to /auth/oauth2/authorize
3. Browser → Nginx: GET /auth/oauth2/authorize
4. Nginx → WSO2 IS: GET /oauth2/authorize (strips /auth)
5. WSO2 IS → Nginx: Redirect to /auth/authenticationendpoint/login.do
   (includes /auth because of proxy_context_path)
6. Nginx → Browser: Redirect to /auth/authenticationendpoint/login.do
7. Browser shows login page ✅
```

**Without proxy_context_path:**

```
5. WSO2 IS → Nginx: Redirect to /authenticationendpoint/login.do
   (missing /auth!)
6. Nginx → Browser: Redirect to /authenticationendpoint/login.do
7. Browser gets 404 ❌
```

---

## Configuration Files

### deployment.toml (Updated ✅)

```toml
[server]
hostname = "letsplaydarts.eu"
base_path = "https://letsplaydarts.eu/auth"
proxy_context_path = "/auth"  # ← Added this

[transport.https.properties]
proxyPort = 443

[authentication.endpoints]
login_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/login.do"
retry_url = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/retry.do"

[oauth.endpoints]
oauth2_consent_page = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/oauth2_consent.do"
oauth2_error_page = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/oauth2_error.do"
oidc_consent_page = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/oauth2_consent.do"
oidc_logout_consent_page = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/oauth2_logout_consent.do"
oidc_logout_page = "${carbon.protocol}://letsplaydarts.eu/auth/authenticationendpoint/oauth2_logout.do"
```

### Service Provider (Needs Update ⚠️)

```
Callback URLs: regexp=https://letsplaydarts\.eu(/callback|/)
```

---

## Testing

### Test 1: Login Flow

```bash
1. Navigate to: https://letsplaydarts.eu
2. Click "Login"
3. Check URL: Should be https://letsplaydarts.eu/auth/oauth2/authorize?...
4. Should see login page (not 404)
5. Enter credentials
6. Should redirect back to application
7. Should be logged in
```

### Test 2: Logout Flow

```bash
1. While logged in, click "Logout"
2. Check URL: Should be https://letsplaydarts.eu/auth/oidc/logout?...
3. Should redirect to home page
4. Should NOT see error message
5. Should be logged out
```

### Test 3: Direct URL Access

```bash
# Test OAuth2 authorize endpoint
curl -I https://letsplaydarts.eu/auth/oauth2/authorize
# Should return 302 or 400 (not 404)

# Test authentication endpoint
curl -I https://letsplaydarts.eu/auth/authenticationendpoint/login.do
# Should return 200 or 302 (not 404)
```

---

## Troubleshooting

### Issue: Still Getting 404 on /oauth2/authorize

**Cause**: WSO2 IS not restarted or configuration not loaded

**Solution**:

```bash
# Restart WSO2 IS
docker-compose -f docker-compose-wso2.yml restart wso2is

# Verify configuration
docker exec wso2is cat /home/wso2carbon/wso2is-6.1.0/repository/conf/deployment.toml | grep proxy_context_path

# Should output: proxy_context_path = "/auth"
```

### Issue: Still Getting "Post logout URI does not match"

**Cause**: Service Provider not updated

**Solution**: Follow Part 2 instructions to update callback URLs in WSO2 IS Management Console

### Issue: Can't Access Management Console

**Cause**: WSO2 IS not running

**Solution**:

```bash
docker ps | grep wso2is
docker logs wso2is 2>&1 | tail -50
docker-compose -f docker-compose-wso2.yml up -d wso2is
```

---

## Summary Table

| Issue                | Status   | Fix Type         | Time  | Restart Required |
| -------------------- | -------- | ---------------- | ----- | ---------------- |
| Missing /auth prefix | ✅ Fixed | Configuration    | 5 min | Yes (WSO2 IS)    |
| Post-logout URI      | ⚠️ To Do | Manual (Console) | 5 min | No               |

**Total Time**: ~10 minutes (plus 2-3 minutes for WSO2 IS restart)

---

## Documentation Reference

| Document                       | Purpose                                |
| ------------------------------ | -------------------------------------- |
| `COMPLETE_REDIRECT_FIX.md`     | This file - Complete overview          |
| `FIX_MISSING_AUTH_PREFIX.md`   | Detailed fix for /auth prefix issue    |
| `FIX_REDIRECT_URIS.md`         | Detailed fix for post-logout URI issue |
| `QUICK_FIX_REDIRECTS.md`       | Quick 5-minute guide for URI issue     |
| `REDIRECT_FLOW_EXPLAINED.md`   | Visual explanation of OAuth2 flow      |
| `REDIRECT_ISSUE_SUMMARY.md`    | Technical summary                      |
| `update_wso2_callback_urls.sh` | Helper script with instructions        |

---

## Next Steps

1. **Apply Configuration Fix** (5 minutes)

   ```bash
   docker-compose -f docker-compose-wso2.yml restart wso2is
   ```

2. **Wait for Startup** (2-3 minutes)

   ```bash
   docker logs -f wso2is
   ```

3. **Apply Service Provider Fix** (5 minutes)
   - Follow `QUICK_FIX_REDIRECTS.md`
   - Or run `./update_wso2_callback_urls.sh` for instructions

4. **Test Everything**
   - Test login flow
   - Test logout flow
   - Verify no errors

---

## Success Criteria

✅ Login redirects to: `https://letsplaydarts.eu/auth/oauth2/authorize`  
✅ Login page loads without 404  
✅ After authentication, redirects back to application  
✅ User is logged in successfully  
✅ Logout redirects to: `https://letsplaydarts.eu/auth/oidc/logout`  
✅ After logout, redirects to home page  
✅ No error messages appear  
✅ User is logged out successfully

---

**Status**: Configuration fix applied ✅ | Service Provider fix pending ⚠️  
**Last Updated**: Current  
**Ready to Apply**: Yes
