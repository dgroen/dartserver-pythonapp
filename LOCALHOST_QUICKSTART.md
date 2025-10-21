# 🚀 Localhost Login - Quick Start Guide

## Problem Solved ✅

Login redirection issues on localhost have been fixed with automatic configuration detection and new helper tools.

## Choose Your Path

### 🏃 **Fastest: Auto-Fix (1 minute)**

The app now automatically detects and fixes http+localhost configuration!

```bash
# Just copy the template and you're done
cp .env.localhost-http .env

# Then update WSO2 callback URL (see below)
```

---

### 🎯 **Interactive Setup (2 minutes)**

Get step-by-step guidance:

```bash
chmod +x helpers/configure-localhost-login.sh
./helpers/configure-localhost-login.sh
```

Choose option **1** for HTTP or **2** for HTTPS, and it will:

- ✅ Update your `.env` file
- ✅ Show you how to update WSO2
- ✅ Explain all the settings

---

### 🔧 **Manual Setup (5 minutes)**

#### For HTTP (easiest)

```bash
# 1. Copy configuration
cp .env.localhost-http .env

# 2. Update your WSO2 credentials if needed
# (Edit .env and set WSO2_CLIENT_ID and WSO2_CLIENT_SECRET)

# 3. Update WSO2 callback URL
```

#### For HTTPS (production-like)

```bash
# 1. Copy configuration
cp .env.localhost-https .env

# 2. Update your WSO2 credentials if needed

# 3. Update WSO2 callback URL

# 4. Run with SSL
export FLASK_USE_SSL=True
python app.py
```

---

## Step 2: Update WSO2 Callback URL

1. **Login to WSO2**

   ```
   https://localhost:9443/carbon
   Username: admin
   Password: admin
   ```

2. **Update DartsApp Configuration**
   - Main → Identity Providers → Registered OAuth/OIDC Apps → DartsApp
   - Edit Callback URL field

3. **Set Based on Your Scheme**
   - **For HTTP**: `regexp=http://localhost:5000(/callback|/)`
   - **For HTTPS**: `regexp=https://localhost:5000(/callback|/)`

4. **Click Save**

---

## Step 3: Run Your App

### For HTTP

```bash
python app.py
# Access: http://localhost:5000
```

### For HTTPS

```bash
export FLASK_USE_SSL=True
python app.py
# Access: https://localhost:5000
# Click "Advanced" → "Proceed to localhost"
```

---

## Test Your Login

1. Go to <http://localhost:5000> (or https:// if using HTTPS)
2. Click **Login**
3. Enter your WSO2 credentials:
   - Username: `testplayer` (or `testgamemaster`, `testadmin`)
   - Password: `Player@123` (or `GameMaster@123`, `Admin@123`) <!-- pragma: allowlist secret -->
4. You should be redirected back to the app! ✅

---

## Common Issues & Fixes

### ❌ "Callback URL mismatch" error

- Did you update WSO2 callback URL? (See Step 2)
- Is the URL pattern correct for your scheme?

### ❌ Session lost immediately after login

- Are you using http://? If yes, ensure `.env` has `SESSION_COOKIE_SECURE=False`
- The templates already have this - just use them!

### ❌ SSL certificate warning (HTTPS only)

- Click "Advanced" → "Proceed to localhost (unsafe)"
- This is normal for self-signed certs on localhost

### ❌ "Invalid state parameter"

- Clear browser cookies and try again
- This usually happens if browser settings block cookies

---

## Configuration Reference

| Setting                   | HTTP                             | HTTPS                             |
| ------------------------- | -------------------------------- | --------------------------------- |
| **APP_SCHEME**            | `http`                           | `https`                           |
| **FLASK_USE_SSL**         | `False`                          | `True`                            |
| **SESSION_COOKIE_SECURE** | `False`                          | `True`                            |
| **WSO2_REDIRECT_URI**     | `http://localhost:5000/callback` | `https://localhost:5000/callback` |

---

## What Changed Behind the Scenes

✅ **Smart Config Detection**

- App now auto-detects http+localhost and fixes cookie settings
- No more manual configuration frustration!

✅ **Better Logging**

- When running on localhost, app logs helpful debugging info
- Check console for redirect URI details

✅ **Easy Templates**

- `.env.localhost-http` - HTTP development setup
- `.env.localhost-https` - HTTPS development setup

✅ **Interactive Setup**

- `helpers/configure-localhost-login.sh` - Guided configuration

✅ **Comprehensive Tests**

- 6 new tests verify localhost redirect URIs work correctly

---

## Need More Help?

- **Detailed Guide**: See `docs/LOCALHOST_LOGIN_FIX.md`
- **Full Implementation Details**: See `docs/LOCALHOST_LOGIN_IMPLEMENTATION.md`
- **Check App Logs**: Look for "Localhost redirect URI" messages

---

## TL;DR - Just Get It Working

```bash
# 1. Use the template
cp .env.localhost-http .env

# 2. Update WSO2 (one-time setup)
# https://localhost:9443/carbon → DartsApp → Callback URL
# Set to: regexp=http://localhost:5000(/callback|/)

# 3. Run
python app.py

# 4. Visit
# http://localhost:5000
# Click Login
# Done! ✅
```

Happy coding! 🎯
