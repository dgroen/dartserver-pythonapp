# APIM Integration - Quick Reference

## 🚀 Status: 95% Complete
All infrastructure ready. Only manual OAuth2 registration needed.

## ⏱️ Estimated Time to Completion: 15 minutes

## 📋 What You Need To Do

### 1️⃣ Register OAuth2 Application (5 min)

```
Go to: https://localhost:9443/myaccount
Login: admin / admin
Path: Security → OAuth Applications → Register

Fill in:
- App Name: APIM
- Redirect URIs: (Add all 4)
  https://localhost:9444/publisher/services/auth/callback
  https://localhost:9444/devportal/services/auth/callback
  https://localhost:9444/admin/services/auth/callback
  https://localhost:9444/analytics/services/auth/callback
- Grant Types: Code, Refresh Token, Implicit

✓ Save credentials (Client ID & Client Secret)
```

### 2️⃣ Update Configuration (3 min)

```bash
# Edit file:
nano wso2apim-4-config/deployment.toml

# Find [oauth2.oidc] section and add:
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
server_url = "https://wso2is:9443"
authorize_endpoint = "https://wso2is:9443/oauth2/authorize"
token_endpoint = "https://wso2is:9443/oauth2/token"
revoke_endpoint = "https://wso2is:9443/oauth2/revoke"
userinfo_endpoint = "https://wso2is:9443/oauth2/userinfo"
oidc_logout_endpoint = "https://wso2is:9443/oidc/logout"
oidc_session_iframe_endpoint = "https://wso2is:9443/oidc/checksession"
scope = "openid profile email"

# Save (Ctrl+X, Y, Enter if using nano)
```

### 3️⃣ Restart APIM (3 min)

```bash
docker-compose -f docker-compose-localhost.yml restart wso2apim

# Wait for healthy status:
docker-compose -f docker-compose-localhost.yml ps wso2apim
# Should show: Up (health: healthy)
```

### 4️⃣ Verify Access (2 min)

Test these portals - should show login screen and work:
```
https://localhost:9444/publisher    # Publisher Portal
https://localhost:9444/devportal    # Developer Portal
https://localhost:9444/admin        # Admin Portal
```

Login with: `admin` / `admin`

## 🧪 Test the Integration

```bash
# Get token
TOKEN=$(curl -k -s -X POST https://localhost:9443/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=admin&password=admin" \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Test API request through APIM
curl -k -H "Authorization: Bearer $TOKEN" \
  https://localhost:9443/api/v1/darts/board

# Should return game data
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `wso2apim-4-config/deployment.toml` | APIM configuration (needs OAuth2 creds) |
| `docker-compose-localhost.yml` | Service orchestration (already configured) |
| `nginx/nginx.conf` | API routing through APIM (already configured) |
| `doc/APIM_OAUTH2_SETUP.md` | Detailed step-by-step guide |
| `APIM_INTEGRATION_COMPLETION.md` | Full status report |

## 🔧 Services Status

```bash
docker-compose -f docker-compose-localhost.yml ps

# Should show all services Up:
✓ darts-postgres
✓ darts-rabbitmq
✓ darts-wso2is
✓ darts-wso2apim
✓ darts-api-gateway
✓ darts-nginx
```

## 🆘 Troubleshooting

**Portal shows "Cannot find an application" error**
→ OAuth2 client not registered yet (Step 1)

**Portal blank after login**
→ Restart APIM and clear browser cache (Step 3)

**Connection errors to localhost:9444**
→ Wait for APIM to fully start (health: healthy)

**Can't access WSO2 IS myaccount portal**
→ Check: `docker logs darts-wso2is`

## 📚 Documentation

- **Full Setup Guide:** `doc/APIM_OAUTH2_SETUP.md`
- **Architecture Details:** `doc/ARCHITECTURE.md`
- **Technical Reference:** `doc/WSO2_APIM_CONFIGURATION.md`
- **Completion Report:** `APIM_INTEGRATION_COMPLETION.md`

## ✅ What's Already Done

- ✅ APIM 4.0.0 running
- ✅ WSO2 IS 7.1.0 connected
- ✅ DartsGameAPI defined with throttling
- ✅ Nginx routed through APIM
- ✅ Docker networking configured
- ✅ deployment.toml ready
- ✅ Test suite created
- ✅ Documentation complete

## 🎯 Next: Complete OAuth2 Registration

All other work is done. Just need to register APIM in WSO2 IS (~15 minutes total).

---

**Questions?** See `doc/APIM_OAUTH2_SETUP.md` for detailed troubleshooting.
