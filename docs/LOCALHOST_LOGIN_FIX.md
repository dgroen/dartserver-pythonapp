# Localhost Login Configuration Fix

## Problem Diagnosis

When running the darts application on `http://localhost:5000` (without HTTPS), you may encounter login redirection issues because:

1. **SESSION_COOKIE_SECURE=True** - Flask is set to require HTTPS for secure cookies
2. **APP_SCHEME=https** - Configuration defaults to HTTPS scheme
3. **SSL Mismatch** - Local app runs on HTTP but configuration expects HTTPS
4. **Callback URI Mismatch** - WSO2 callback URLs don't match the request scheme

## Solutions

### Option 1: Run with HTTPS on Localhost (Recommended for Testing)

This is the most secure approach and matches production behavior:

```bash
# The application already has SSL certificates in ssl/
# Run with HTTPS support enabled:
python app.py --ssl
# or
export FLASK_USE_SSL=True
python app.py
```

Access via: `https://localhost:5000`

**Note**: You'll need to accept the self-signed certificate warning in your browser.

### Option 2: Run with HTTP on Localhost (Development Only)

For quick local development, configure for plain HTTP:

Edit `.env` to change:

```bash
APP_SCHEME=http
SESSION_COOKIE_SECURE=False
FLASK_USE_SSL=False
WSO2_REDIRECT_URI=http://localhost:5000/callback
WSO2_POST_LOGOUT_REDIRECT_URI=http://localhost:5000/
```

Or run with environment variables:

```bash
export APP_SCHEME=http
export SESSION_COOKIE_SECURE=False
export FLASK_USE_SSL=False
export WSO2_REDIRECT_URI=http://localhost:5000/callback
python app.py
```

Access via: `http://localhost:5000`

### Option 3: Use Dynamic Configuration (Most Flexible)

Let the app auto-detect the scheme from the request:

Create/update `.env` with:

```bash
ENVIRONMENT=development
APP_DOMAIN=localhost:5000
APP_SCHEME=http
FLASK_DEBUG=True
FLASK_USE_SSL=False
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_SAMESITE=Lax
```

The app will:
- Auto-detect if you access via `http://` or `https://`
- Generate correct callback URIs dynamically
- Set SESSION_COOKIE_SECURE based on the actual scheme used

## WSO2 Configuration Requirements

After changing schemes, you must also update WSO2 Identity Server:

1. **Login to WSO2 Admin Console**:
   ```
   https://localhost:9443/carbon
   Username: admin
   Password: admin
   ```

2. **Update Callback URLs** for the DartsApp OAuth2 application:
   - Main → Identity Providers → Registered OAuth/OIDC Applications → DartsApp
   - Callback URL patterns:
     - For HTTPS: `regexp=https://localhost:5000(/callback|/)`
     - For HTTP: `regexp=http://localhost:5000(/callback|/)`

3. **Or use the helper script**:
   ```bash
   # For HTTP localhost
   python helpers/fix_callback_urls.py --scheme http --domain localhost:5000
   
   # For HTTPS localhost
   python helpers/fix_callback_urls.py --scheme https --domain localhost:5000
   ```

## Troubleshooting

### Cookies Not Being Set
**Symptom**: Login redirects to `/` but session is lost immediately

**Solution**: Ensure `SESSION_COOKIE_SECURE` matches your scheme:
- Use `http://` → Set `SESSION_COOKIE_SECURE=False`
- Use `https://` → Set `SESSION_COOKIE_SECURE=True`

### Callback URL Mismatch
**Symptom**: "Callback URL mismatch" error from WSO2

**Solution**: 
1. Check what URL you're accessing (http:// or https://)
2. Update WSO2 callback URLs to match that scheme
3. Ensure APP_SCHEME environment variable matches

### State Parameter Mismatch
**Symptom**: "Invalid state parameter" error

**Solution**: 
- Clear browser cookies: `Ctrl+Shift+Delete` or `Cmd+Shift+Delete`
- Clear Flask session cache
- Try logging in again

### HTTPS Certificate Warnings
**Symptom**: "This site is not secure" warning

**Solution**: 
- The app uses self-signed certificates for localhost
- Click "Advanced" and proceed (safe for local development)
- Or import the certificate: `ssl/cert.pem` into your browser

## Environment Variables Reference

| Variable | HTTP Localhost | HTTPS Localhost |
|----------|---|---|
| APP_SCHEME | `http` | `https` |
| APP_DOMAIN | `localhost:5000` | `localhost:5000` |
| FLASK_USE_SSL | `False` | `True` |
| SESSION_COOKIE_SECURE | `False` | `True` |
| SESSION_COOKIE_SAMESITE | `Lax` | `Lax` |
| WSO2_REDIRECT_URI | `http://localhost:5000/callback` | `https://localhost:5000/callback` |

## Testing Login Flow

1. **Navigate to home page**
   - HTTP: `http://localhost:5000`
   - HTTPS: `https://localhost:5000`

2. **Click "Login" button**
   - Should redirect to WSO2 login

3. **Enter credentials**
   - Username: testplayer (or testgamemaster, testadmin)
   - Password: Player@123 (or GameMaster@123, Admin@123)

4. **Should redirect back to app**
   - Session should be preserved
   - Player should see game board or control panel

## Additional Resources

- Configuration Details: See `src/core/config.py`
- Authentication Code: See `src/core/auth.py`
- Flask App Setup: See `src/app/app.py`
- Test Configuration: See `tests/unit/test_config.py`