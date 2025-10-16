# Quick Fix: Post-Login and Post-Logout Redirects

## Problem
❌ Error: **"Post logout URI does not match with registered callback URI"**

## Root Cause
WSO2 Identity Server only has the **callback URI** registered, but not the **post-logout redirect URI**.

## Solution (5 Minutes)

### Step 1: Access WSO2 IS Console
Open in your browser:
```
https://letsplaydarts.eu/auth/carbon
```

Login:
- **Username**: `admin`
- **Password**: `admin`

### Step 2: Navigate to Service Providers
```
Main → Identity → Service Providers → List
```

### Step 3: Edit Your Application
Find your OAuth2 application and click **Edit**

### Step 4: Update Callback URLs
1. Expand **"Inbound Authentication Configuration"**
2. Click **"Configure"** under **"OAuth/OpenID Connect Configuration"**
3. Find the **"Callback Url"** field

**Current value:**
```
https://letsplaydarts.eu/callback
```

**Change to (use regex pattern):**
```
regexp=https://letsplaydarts\.eu(/callback|/)
```

**OR (use comma-separated list):**
```
https://letsplaydarts.eu/callback,https://letsplaydarts.eu/
```

### Step 5: Save
1. Click **"Update"** (in OAuth dialog)
2. Click **"Update"** again (in Service Provider page)

### Step 6: Test
1. Go to: https://letsplaydarts.eu
2. Click **"Login"** → Should work ✅
3. Click **"Logout"** → Should work ✅

## What This Does

The regex pattern allows **both** redirect URIs:
- ✅ `https://letsplaydarts.eu/callback` (for login)
- ✅ `https://letsplaydarts.eu/` (for logout)

## Visual Guide

```
Before:
┌─────────────────────────────────────┐
│ Registered Callback URLs:          │
│ ✅ /callback (login works)         │
│ ❌ / (logout fails)                 │
└─────────────────────────────────────┘

After:
┌─────────────────────────────────────┐
│ Registered Callback URLs:          │
│ ✅ /callback (login works)         │
│ ✅ / (logout works)                 │
└─────────────────────────────────────┘
```

## Troubleshooting

### Still Getting Error?
1. Make sure you clicked **"Update" twice**
2. Clear browser cache/cookies
3. Try in incognito window

### Can't Access Console?
```bash
# Check if WSO2 IS is running
docker ps | grep wso2is

# Restart if needed
docker-compose -f docker-compose-wso2.yml restart wso2is
```

## More Information

- **Detailed Guide**: `FIX_REDIRECT_URIS.md`
- **Flow Explanation**: `REDIRECT_FLOW_EXPLAINED.md`
- **Configuration Script**: `./update_wso2_callback_urls.sh`

## Summary

| Action | Status |
|--------|--------|
| Login Flow | ✅ Works |
| Logout Flow | ✅ Works (after fix) |
| Time to Fix | ⏱️ 5 minutes |
| Code Changes | ❌ None needed |
| Restart Required | ❌ No |

The issue is purely in WSO2 IS configuration, not in your application code!