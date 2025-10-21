# WSO2 Identity Server Upgrade Guide

## From 5.11.0 to 7.1.0

---

## 📋 Overview

This guide will help you upgrade WSO2 Identity Server from **5.11.0** to **7.1.0** (latest version as of October 2025).

### Current Setup

- **Version**: WSO2 IS 5.11.0
- **Deployment**: Docker container
- **Configuration**: Custom `deployment.toml` mounted as volume
- **Data**: Stored in Docker volume `wso2is_data`
- **Integration**: Flask app, nginx reverse proxy, WSO2 API Manager

### Target Version

- **Version**: WSO2 IS 7.1.0
- **Major Changes**: New architecture, improved reverse proxy support, modern UI

---

## ⚠️ Important Considerations

### Breaking Changes from 5.11.0 to 7.x

1. **Configuration File Format**
   - `deployment.toml` structure has changed significantly
   - Some configuration parameters have been renamed or moved
   - New configuration options available

2. **Database Schema Changes**
   - Database migration required
   - Cannot directly use 5.11.0 database with 7.1.0

3. **API Changes**
   - Some REST APIs have been updated
   - SCIM2 endpoints may have changes
   - OAuth2/OIDC endpoints remain mostly compatible

4. **Management Console**
   - **NEW**: Modern web-based console (Asgardeo-style)
   - **REMOVED**: Old Carbon console (`/carbon`)
   - Better reverse proxy support

5. **Docker Image Changes**
   - Different directory structure
   - Volume mount paths changed
   - New environment variable options

---

## 🎯 Upgrade Strategy

### Option 1: Fresh Installation (RECOMMENDED)

**Best for**: Production environments, minimal downtime tolerance

**Steps**:

1. Export Service Provider configurations from 5.11.0
2. Export users (if using embedded LDAP)
3. Install WSO2 IS 7.1.0 in parallel
4. Reconfigure Service Providers
5. Import users
6. Test thoroughly
7. Switch traffic to new instance

**Pros**:

- ✅ Clean installation
- ✅ Easy rollback
- ✅ No migration tool issues
- ✅ Test before switching

**Cons**:

- ⚠️ Manual reconfiguration needed
- ⚠️ Requires parallel infrastructure

---

### Option 2: In-Place Upgrade with Migration Tool

**Best for**: Development/testing environments

**Steps**:

1. Backup current data
2. Run WSO2 migration tool
3. Update Docker image
4. Update configuration file
5. Restart container

**Pros**:

- ✅ Preserves all data
- ✅ Automated migration

**Cons**:

- ⚠️ More complex
- ⚠️ Harder to rollback
- ⚠️ Potential migration issues

---

## 📝 Pre-Upgrade Checklist

### 1. Backup Everything

```bash
# Backup current deployment.toml
cp wso2is-config/deployment.toml wso2is-config/deployment.toml.5.11.0.backup

# Backup Docker volume
docker run --rm -v wso2is_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/wso2is_data_backup_$(date +%Y%m%d).tar.gz /data

# Export Service Provider configuration (via Management Console)
# 1. Access: https://letsplaydarts.eu:9443/carbon
# 2. Navigate to: Service Providers → List
# 3. Export each Service Provider as XML
```

### 2. Document Current Configuration

```bash
# Save current Service Provider details
# - Client ID
# - Client Secret
# - Callback URLs
# - Scopes
# - Grant types
```

### 3. Test Current Setup

```bash
# Verify login/logout works
# Test OAuth2 flows
# Document expected behavior
```

---

## 🚀 Upgrade Steps - Option 1 (Fresh Installation)

### Step 1: Prepare New Configuration

Create a new configuration file for WSO2 IS 7.1.0:

```bash
# Create new config directory
mkdir -p wso2is-7-config
```

**File**: `wso2is-7-config/deployment.toml`

```toml
[server]
hostname = "letsplaydarts.eu"
base_path = "https://letsplaydarts.eu/auth"

[super_admin]
username = "admin"
password = "admin"  # pragma: allowlist secret
create_admin_account = true

# Reverse proxy configuration
[proxy]
host_name = "letsplaydarts.eu"
context_path = "/auth"
https_port = 443

# Database configuration (using H2 for simplicity)
[database.identity_db]
type = "h2"
url = "jdbc:h2:./repository/database/WSO2IDENTITY_DB;DB_CLOSE_ON_EXIT=FALSE;LOCK_TIMEOUT=60000"
username = "wso2carbon"
password = "wso2carbon"  # pragma: allowlist secret

[database.shared_db]
type = "h2"
url = "jdbc:h2:./repository/database/WSO2SHARED_DB;DB_CLOSE_ON_EXIT=FALSE;LOCK_TIMEOUT=60000"
username = "wso2carbon"
password = "wso2carbon"  # pragma: allowlist secret

# OAuth configurations
[oauth]
prompt_consent = false

# CORS configuration (if needed for modern apps)
[cors]
allow_generic_http_requests = true
allow_any_origin = false
allowed_origins = [
    "https://letsplaydarts.eu"
]
allow_subdomains = false
supported_methods = [
    "GET",
    "POST",
    "HEAD",
    "OPTIONS"
]
support_any_header = true
supported_headers = []
exposed_headers = []
supports_credentials = true
max_age = 3600
tag_requests = false
```

### Step 2: Update Docker Compose

**File**: `docker-compose-wso2.yml`

```yaml
services:
  # WSO2 Identity Server 7.1.0
  wso2is:
    image: wso2/wso2is:7.1.0 # Changed from 5.11.0
    container_name: darts-wso2is
    ports:
      - "9443:9443" # HTTPS port
      - "9763:9763" # HTTP port
    environment:
      - JAVA_OPTS=-Xms512m -Xmx1024m
    volumes:
      - wso2is_7_data:/home/wso2carbon/wso2is-7.1.0 # Changed path
      - ./wso2is-7-config/deployment.toml:/home/wso2carbon/wso2is-7.1.0/repository/conf/deployment.toml:rw
    healthcheck:
      test: [
          "CMD",
          "curl",
          "-k",
          "-f",
          "https://localhost:9443/api/health-check/v1.0/health", # Changed endpoint
        ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    networks:
      - darts-network
```

### Step 3: Start New WSO2 IS 7.1.0

```bash
# Stop old WSO2 IS 5.11.0
docker-compose -f docker-compose-wso2.yml stop wso2is

# Start new WSO2 IS 7.1.0
docker-compose -f docker-compose-wso2.yml up -d wso2is

# Monitor logs
docker logs -f darts-wso2is
```

Wait for: `WSO2 Identity Server started in X seconds`

### Step 4: Access New Management Console

**NEW Console URL**: `https://letsplaydarts.eu:9443/console`

**Credentials**:

- Username: `admin` <!-- pragma: allowlist secret -->
- Password: `admin` <!-- pragma: allowlist secret -->

**Note**: The old `/carbon` console is **removed** in 7.x. The new console is modern and web-based.

### Step 5: Recreate Service Provider

1. **Access Console**: `https://letsplaydarts.eu:9443/console`

2. **Navigate to**: Applications → New Application

3. **Create Application**:
   - Name: `DartsGameWebApp`
   - Protocol: `OAuth2/OpenID Connect`
   - Template: `Traditional Web Application`

4. **Configure OAuth2/OIDC**:
   - **Allowed Grant Types**:
     - ✅ Authorization Code
     - ✅ Refresh Token

   - **Authorized Redirect URLs**:

     ```
     https://letsplaydarts.eu/callback
     ```

   - **Allowed Origins** (for CORS):

     ```
     https://letsplaydarts.eu
     ```

   - **Access Token**:
     - Type: `JWT`
     - Expiry: `3600` seconds

   - **Refresh Token**:
     - Expiry: `86400` seconds
     - Renew: ✅ Enabled

   - **ID Token**:
     - Expiry: `3600` seconds

   - **PKCE**: `Mandatory` (recommended for security)

   - **Logout**:
     - **Post Logout Redirect URLs**:

       ```
       https://letsplaydarts.eu/
       ```

     - **Back Channel Logout**: ❌ Disabled (unless needed)

5. **User Attributes** (Scopes):
   - ✅ `openid`
   - ✅ `profile`
   - ✅ `email`
   - ✅ `groups` (if using role-based access)

6. **Save** and note the **Client ID** and **Client Secret**

### Step 6: Update Application Environment Variables

Update `.env` file:

```bash
# Update with new credentials from Step 5
WSO2_CLIENT_ID=<new_client_id>
WSO2_CLIENT_SECRET=<new_client_secret>
```

Update `docker-compose-wso2.yml` environment variables for `darts-app` and `api-gateway`:

```yaml
environment:
  WSO2_CLIENT_ID: ${WSO2_CLIENT_ID:-<new_client_id>}
  WSO2_CLIENT_SECRET: ${WSO2_CLIENT_SECRET:-<new_client_secret>}
```

### Step 7: Restart Application

```bash
# Restart Flask app and API gateway
docker-compose -f docker-compose-wso2.yml restart darts-app api-gateway
```

### Step 8: Test Everything

```bash
# Test login flow
1. Navigate to: https://letsplaydarts.eu
2. Click "Login"
3. Should redirect to: https://letsplaydarts.eu/auth/oauth2/authorize
4. Authenticate with admin/admin
5. Should redirect back successfully

# Test logout flow
1. Click "Logout"
2. Should redirect to: https://letsplaydarts.eu/auth/oidc/logout
3. Should redirect back to: https://letsplaydarts.eu/
4. ✅ No error message
```

---

## 🔧 Configuration Differences

### WSO2 IS 5.11.0 vs 7.1.0

| Feature              | 5.11.0                            | 7.1.0                            |
| -------------------- | --------------------------------- | -------------------------------- |
| **Console**          | `/carbon` (old UI)                | `/console` (modern UI)           |
| **Config Path**      | `/home/wso2carbon/wso2is-5.11.0/` | `/home/wso2carbon/wso2is-7.1.0/` |
| **Reverse Proxy**    | `base_path` + `proxyPort`         | `[proxy]` section                |
| **Health Check**     | `/carbon/admin/login.jsp`         | `/api/health-check/v1.0/health`  |
| **Service Provider** | XML-based export                  | JSON-based API                   |
| **User Management**  | SCIM 1.1 + 2.0                    | SCIM 2.0 (primary)               |

---

## 📊 Verification Checklist

After upgrade, verify:

- [ ] WSO2 IS 7.1.0 starts successfully
- [ ] Management console accessible at `/console`
- [ ] Service Provider created with correct settings
- [ ] Login flow works (OAuth2 authorization)
- [ ] Callback redirect works
- [ ] User authentication succeeds
- [ ] Token exchange works
- [ ] Logout flow works
- [ ] Post-logout redirect works
- [ ] No error messages in logs
- [ ] Flask app can introspect tokens
- [ ] API Gateway can validate tokens

---

## 🔄 Rollback Procedure

If upgrade fails:

```bash
# Stop new WSO2 IS 7.1.0
docker-compose -f docker-compose-wso2.yml stop wso2is

# Restore old configuration
cp wso2is-config/deployment.toml.5.11.0.backup wso2is-config/deployment.toml

# Update docker-compose to use 5.11.0
# Change image: wso2/wso2is:7.1.0 → wso2/wso2is:5.11.0
# Change volume path back to wso2is-5.11.0

# Restart old WSO2 IS 5.11.0
docker-compose -f docker-compose-wso2.yml up -d wso2is

# Restore old environment variables
# Revert .env changes
```

---

## 🆘 Troubleshooting

### Issue 1: Console Not Accessible

**Problem**: Cannot access `https://letsplaydarts.eu:9443/console`

**Solution**:

```bash
# Check if WSO2 IS is running
docker ps | grep wso2is

# Check logs
docker logs darts-wso2is | tail -50

# Verify port is exposed
docker port darts-wso2is
```

### Issue 2: Login Redirects to Wrong URL

**Problem**: Redirects to `/oauth2/authorize` instead of `/auth/oauth2/authorize`

**Solution**:

- Verify `[proxy]` configuration in `deployment.toml`
- Ensure `context_path = "/auth"` is set
- Restart WSO2 IS

### Issue 3: Post-Logout Redirect Fails

**Problem**: "Post logout URI does not match" error

**Solution**:

- Verify **Post Logout Redirect URLs** in Application settings
- Must include: `https://letsplaydarts.eu/`
- Save and test again

### Issue 4: Token Validation Fails

**Problem**: API Gateway cannot validate tokens

**Solution**:

- Verify introspection endpoint: `https://wso2is:9443/oauth2/introspect`
- Check introspection credentials (admin/admin)
- Verify SSL certificate trust

---

## 📚 Additional Resources

- **WSO2 IS 7.1.0 Documentation**: <https://is.docs.wso2.com/en/7.1.0>
- **Docker Hub**: <https://hub.docker.com/r/wso2/wso2is>
- **GitHub**: <https://github.com/wso2/docker-is>
- **Migration Guide**: <https://is.docs.wso2.com/en/latest/deploy/migrate/>
- **API Reference**: <https://is.docs.wso2.com/en/latest/apis/>

---

## 🎯 Next Steps

After successful upgrade:

1. **Update Documentation**: Document new Client ID/Secret
2. **Monitor Logs**: Watch for any errors or warnings
3. **Performance Testing**: Verify response times
4. **Security Audit**: Review new security features
5. **Explore New Features**:
   - Login Flow AI
   - Branding AI
   - App-native authentication
   - Improved MFA options
   - Modern console UI

---

## 💡 Tips

1. **Test in Development First**: Always test upgrade in dev environment
2. **Backup Before Upgrade**: Always backup data and configuration
3. **Read Release Notes**: Check WSO2 IS 7.1.0 release notes for breaking changes
4. **Use Fresh Installation**: Recommended over migration for major version jumps
5. **Monitor Closely**: Watch logs and metrics after upgrade
6. **Have Rollback Plan**: Always have a tested rollback procedure

---

## ⏱️ Estimated Time

- **Preparation**: 30 minutes
- **Fresh Installation**: 1-2 hours
- **Testing**: 1 hour
- **Total**: 2.5-3.5 hours

---

**Good luck with your upgrade! 🚀**
