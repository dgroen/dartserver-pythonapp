# Localhost Login Implementation Summary

## Overview
This document describes the changes made to fix login and redirection issues on localhost for the Darts Game application.

## Problem Statement
When running the application on `http://localhost:5000` (without HTTPS), users encountered login redirection failures due to:

1. **SESSION_COOKIE_SECURE mismatch** - Flask was set to require HTTPS cookies even for HTTP connections
2. **SSL/Scheme configuration conflicts** - Configuration defaulted to HTTPS but app ran on HTTP
3. **WSO2 callback URL mismatches** - OAuth2 callback URLs didn't match request scheme
4. **Unclear error messages** - No helpful debugging information for localhost issues

## Solutions Implemented

### 1. Smart Configuration Detection (`src/core/config.py`)

**Changes:**
- Added automatic detection for localhost + HTTP scheme combinations
- When `APP_SCHEME=http` and `APP_DOMAIN` contains "localhost", automatically set `SESSION_COOKIE_SECURE=False`
- Added helpful logging to indicate when this auto-correction is applied
- Maintained backward compatibility with existing configurations

**Code Impact:**
```python
# Special handling for localhost to prevent cookie issues
# On localhost, if using http:// scheme, SESSION_COOKIE_SECURE must be False
if "localhost" in APP_DOMAIN and APP_SCHEME == "http":
    SESSION_COOKIE_SECURE = False
    logger.info(
        "Localhost detected with http:// scheme - "
        "SESSION_COOKIE_SECURE forced to False to allow cookies",
    )
```

**Benefits:**
- Users no longer need to manually fix cookie configuration
- Less confusion about session issues
- Works out-of-the-box for localhost development

### 2. Enhanced Redirect URI Logging (`src/core/auth.py`)

**Changes:**
- Added enhanced logging specifically for localhost redirect URIs
- Logs now include all relevant configuration parameters:
  - Actual redirect URI generated
  - Request scheme and host
  - Config domain and scheme
  - SESSION_COOKIE_SECURE status
- Helps developers quickly diagnose redirect issues

**Log Output Example:**
```
INFO: Localhost redirect URI: http://localhost:5000/callback 
      (scheme=http, host=localhost:5000, 
       config_domain=localhost:5000, 
       config_scheme=http, 
       session_secure=False)
```

**Benefits:**
- Easier debugging of redirect URL mismatches
- Clear visibility into what URLs are being generated
- Helps identify WSO2 configuration issues

### 3. Pre-built Environment Configuration Templates

**New Files:**
- `.env.localhost-http` - HTTP-only configuration for quick development
- `.env.localhost-https` - HTTPS configuration matching production behavior

**Contents:**
- Proper scheme settings (http/https)
- Correct SSL/cookie security settings
- WSO2 callback URLs matching the scheme
- All other development defaults

**Usage:**
```bash
# For HTTP localhost
cp .env.localhost-http .env

# For HTTPS localhost
cp .env.localhost-https .env
```

### 4. Interactive Configuration Helper (`helpers/configure-localhost-login.sh`)

**Purpose:**
Provides interactive setup for localhost login configuration

**Features:**
- Three configuration options:
  1. HTTP localhost (simple, dev-friendly)
  2. HTTPS localhost (production-like)
  3. Auto-detect mode (flexible)
- Automatically updates .env file
- Provides WSO2 configuration instructions
- Creates backups of previous .env

**Usage:**
```bash
chmod +x helpers/configure-localhost-login.sh
./helpers/configure-localhost-login.sh
```

### 5. Comprehensive Documentation (`docs/LOCALHOST_LOGIN_FIX.md`)

**Sections:**
- Problem diagnosis with specific symptoms
- Three solution approaches with pros/cons
- WSO2 configuration requirements
- Troubleshooting guide for common issues
- Environment variable reference table
- Testing checklist

## Testing

### New Unit Tests Added
**File:** `tests/unit/test_auth.py`

Added `TestDynamicRedirectUri` class with 6 tests covering:
- ✅ HTTP localhost redirect URI generation
- ✅ HTTPS localhost redirect URI generation  
- ✅ X-Forwarded headers handling
- ✅ Post-logout redirect URIs
- ✅ Remote domain redirect URIs
- ✅ 127.0.0.1 address handling

**Test Results:**
```
TestDynamicRedirectUri::test_localhost_http_redirect_uri PASSED
TestDynamicRedirectUri::test_localhost_https_redirect_uri PASSED
TestDynamicRedirectUri::test_localhost_with_forwarded_headers PASSED
TestDynamicRedirectUri::test_localhost_post_logout_redirect_uri PASSED
TestDynamicRedirectUri::test_remote_domain_redirect_uri PASSED
TestDynamicRedirectUri::test_localhost_127_0_0_1_redirect_uri PASSED
```

### Quality Checks

✅ **Linting:** All ruff checks pass (PEP 8, trailing commas, etc.)
✅ **Security:** Bandit security scan shows no issues
✅ **Tests:** All existing tests continue to pass
✅ **Coverage:** src/core/config.py has 89.36% coverage

## Files Modified

### Code Changes
1. **src/core/config.py**
   - Added localhost detection logic
   - Auto-correct SESSION_COOKIE_SECURE for http + localhost
   - Added logging for clarity

2. **src/core/auth.py**
   - Enhanced logging for localhost redirect URIs
   - Post-logout redirect URI logging

3. **tests/unit/test_auth.py**
   - Imported new functions to test
   - Added 6 new unit tests for dynamic redirect URIs

### New Files Created
1. **docs/LOCALHOST_LOGIN_FIX.md** - Comprehensive troubleshooting guide
2. **.env.localhost-http** - HTTP development configuration template
3. **.env.localhost-https** - HTTPS development configuration template
4. **helpers/configure-localhost-login.sh** - Interactive setup script

## Usage Guide

### Quick Start - HTTP Localhost (Simplest)

1. **Set environment:**
   ```bash
   cp .env.localhost-http .env
   ```

2. **Update WSO2 callback URL:**
   - Login to https://localhost:9443/carbon (admin/admin)
   - Go to: Main → Identity Providers → Registered OAuth/OIDC Apps → DartsApp
   - Set Callback URL to: `regexp=http://localhost:5000(/callback|/)`
   - Click Save

3. **Run application:**
   ```bash
   python app.py
   ```

4. **Access:**
   - Open http://localhost:5000
   - Click Login
   - Enter your WSO2 credentials

### Quick Start - HTTPS Localhost (Production-like)

1. **Set environment:**
   ```bash
   cp .env.localhost-https .env
   ```

2. **Update WSO2 callback URL:**
   - Set to: `regexp=https://localhost:5000(/callback|/)`

3. **Run application:**
   ```bash
   export FLASK_USE_SSL=True
   python app.py
   ```

4. **Access:**
   - Open https://localhost:5000
   - Accept self-signed certificate warning
   - Click Login

### Using Interactive Setup

1. **Run the configuration script:**
   ```bash
   chmod +x helpers/configure-localhost-login.sh
   ./helpers/configure-localhost-login.sh
   ```

2. **Select option (1, 2, or 3)**

3. **Follow the on-screen instructions**

4. **Update WSO2 as instructed**

5. **Start the app and test login**

## Backward Compatibility

✅ **No breaking changes**
- Existing production configurations continue to work
- Existing development configurations automatically benefit from new localhost detection
- All changes are additive/non-destructive

## Migration Guide

If you have an existing `.env`:

### For HTTP Localhost
No action required! The code now automatically detects and fixes the configuration.

But if you want to use the template:
```bash
cp .env .env.backup
cp .env.localhost-http .env
# Re-apply your WSO2 credentials to .env if needed
```

### For HTTPS Localhost
If you were having SSL issues:
```bash
cp .env .env.backup
cp .env.localhost-https .env
# Re-apply your WSO2 credentials to .env if needed
```

## Troubleshooting

### "Callback URL mismatch" Error
1. Check what URL you accessed (http:// or https://)
2. Verify WSO2 callback URL pattern matches that scheme
3. Check .env has correct APP_SCHEME and SESSION_COOKIE_SECURE

### Session Lost After Login
1. Check app logs for "SESSION_COOKIE_SECURE" messages
2. If using http://, ensure SESSION_COOKIE_SECURE=False
3. Run the configuration script: `./helpers/configure-localhost-login.sh`

### SSL Certificate Warnings (HTTPS)
This is normal for self-signed certificates on localhost:
1. Click Advanced
2. Click "Proceed to localhost (unsafe)"
3. This is safe for local development only

### Invalid State Parameter
1. Clear browser cookies (Ctrl+Shift+Delete)
2. Close and reopen browser
3. Try logging in again

## Documentation

For detailed information, see:
- **Configuration Details**: See `src/core/config.py`
- **Authentication Code**: See `src/core/auth.py`
- **Test Cases**: See `tests/unit/test_auth.py`
- **Full Troubleshooting**: See `docs/LOCALHOST_LOGIN_FIX.md`

## Support

If you encounter issues:

1. **Check the troubleshooting guide**: `docs/LOCALHOST_LOGIN_FIX.md`
2. **Review app logs**: Look for redirect URI and SESSION_COOKIE messages
3. **Verify WSO2 callback URLs**: Check main config is correct
4. **Run the setup script**: `helpers/configure-localhost-login.sh` (interactive help)

## Future Enhancements

Possible future improvements:
- [ ] Auto-detection and update of WSO2 callback URLs
- [ ] CLI tool to quickly test login flows
- [ ] Development proxy for handling multiple domains
- [ ] Docker Compose profile for localhost HTTPS with proper certificates