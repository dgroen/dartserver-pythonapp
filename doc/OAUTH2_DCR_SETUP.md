# WSO2 APIM OAuth2 Configuration via Dynamic Client Registration

## Overview

Successfully configured WSO2 API Manager (APIM) 4.0.0 with OAuth2 authentication using Dynamic Client Registration (DCR) endpoint from WSO2 Identity Server (IS) 7.1.0.

## What Was Implemented

### 1. DCR-Based Client Registration

The script `helpers/configure_wso2_oauth_apps.py` registers 4 OAuth2 clients using the DCR endpoint:
- **APIM_KeyManager**: For API token validation and client credentials flow
- **APIM_Publisher**: For Publisher portal OAuth2 callback
- **APIM_DevPortal**: For Developer Portal OAuth2 callback
- **APIM_Admin**: For Admin portal OAuth2 callback

### 2. Dynamic Client Registration Endpoint

**Endpoint**: `POST https://localhost:9443/api/identity/oauth2/dcr/v1.1/register`

**Authentication**: Basic Auth (admin:admin)

**Request Payload**:
```json
{
  "client_name": "APIM_Publisher",
  "redirect_uris": ["https://localhost:9444/publisher/services/auth/callback/login"],
  "grant_types": ["authorization_code", "refresh_token"],
  "token_endpoint_auth_method": "client_secret_basic"
}
```

**Response (201 Created)**:
```json
{
  "client_id": "3gIJQHMEfwOP07LPQWE77L96I4oa",
  "client_secret": "13LGugPmT1IpgRWN9PNgpKIKPwRdoInF1TybSNG7ROUa",
  ...
}
```

### 3. Configuration Updates

The script automatically updates `wso2apim-4-config/deployment.toml`:

#### [keymanager.default] Section
```toml
username = "zPOCcMwMP7_6hOqL88BUDIiU6x4a"      # APIM_KeyManager client_id
password = "BfUjEkRcfy52Nf8FzxhlzySMfNB6MbfNIqiQsTW9egMa"  # APIM_KeyManager client_secret
```

#### [oauth2.oidc] Section (Added)
```toml
[oauth2.oidc]
client_id = "3gIJQHMEfwOP07LPQWE77L96I4oa"       # APIM_Publisher client_id
client_secret = "13LGugPmT1IpgRWN9PNgpKIKPwRdoInF1TybSNG7ROUa"  # APIM_Publisher client_secret
server_url = "https://wso2is:9443"
authorize_endpoint = "https://wso2is:9443/oauth2/authorize"
token_endpoint = "https://wso2is:9443/oauth2/token"
revoke_endpoint = "https://wso2is:9443/oauth2/revoke"
userinfo_endpoint = "https://wso2is:9443/oauth2/userinfo"
oidc_logout_endpoint = "https://wso2is:9443/oidc/logout"
oidc_session_iframe_endpoint = "https://wso2is:9443/oidc/checksession"
scope = "openid profile email"
```

## Why DCR Over REST API OIDC Configuration

The original approach using Application Management REST API (`/api/server/v1/applications/{id}/inbound-protocols`) failed with:
- 400 Bad Request (invalid request format)
- 405 Method Not Allowed (endpoint doesn't support OIDC config)
- 500 Internal Server Error (server processing errors)
- 501 Not Implemented (multiple callback URLs not supported)

**DCR is superior because**:
1. ✅ Returns credentials immediately (no separate lookup needed)
2. ✅ RESTful and standardized (RFC 7591)
3. ✅ No template/console issues
4. ✅ Reliable across WSO2 versions
5. ✅ Built-in support for multiple callback URLs

## Usage

### Register New OAuth2 Clients
```bash
python3 helpers/configure_wso2_oauth_apps.py --update-toml wso2apim-4-config/deployment.toml
```

### Register with Cleanup (Delete Existing Clients First)
```bash
python3 helpers/configure_wso2_oauth_apps.py --cleanup --update-toml wso2apim-4-config/deployment.toml
```

### Custom WSO2 IS/APIM Hosts
```bash
python3 helpers/configure_wso2_oauth_apps.py \
  --is-host wso2is-prod.example.com \
  --is-port 9443 \
  --apim-host apim-prod.example.com \
  --apim-port 9444 \
  --username admin \
  --password securepassword \
  --update-toml /path/to/deployment.toml
```

## Result

✅ **APIM Publisher Portal**: Now accessible without OAuth2 errors
- URL: `https://localhost:9444/publisher`
- Status: HTTP 200 OK (previously returned oauth2_error.do)

✅ **APIM Admin Portal**: Working with OAuth2 authentication
- URL: `https://localhost:9444/admin`

✅ **APIM DevPortal**: OAuth2 callback configured
- URL: `https://localhost:9444/devportal`

## Troubleshooting

### "Application already exist" Error
If you get: `"Application with the name APIM_KeyManager already exist in the system"`

Run with cleanup flag:
```bash
python3 helpers/configure_wso2_oauth_apps.py --cleanup
```

### 401 Unauthorized
Check WSO2 IS admin credentials in the script:
- Default: `admin:admin`
- Update via `--username` and `--password` flags

### deployment.toml Not Updated
Manually verify the file exists and has write permissions:
```bash
ls -la wso2apim-4-config/deployment.toml
```

### APIM Still Shows OAuth2 Error After Restart
1. Clear APIM cache: `docker-compose down && docker volume prune`
2. Verify credentials in deployment.toml section [oauth2.oidc]
3. Restart APIM: `docker-compose restart wso2apim`

## Files Modified

- **Created**: `helpers/configure_wso2_oauth_apps.py` - DCR-based OAuth2 configuration script
- **Updated**: `wso2apim-4-config/deployment.toml` - Added [oauth2.oidc] section and credentials
- **Excluded**: `.gitignore` - deployment.toml excluded from version control (contains secrets)

## References

- WSO2 APIM OAuth2 Documentation: https://apim.docs.wso2.com/
- WSO2 IS DCR Documentation: https://is.docs.wso2.com/
- RFC 7591 - Dynamic Client Registration: https://tools.ietf.org/html/rfc7591
