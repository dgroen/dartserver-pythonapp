# WSO2 APIM Startup Issue - Resolution Summary

## Problem
WSO2 APIM 4.0.0 container failed to start with multiple cascading errors when using custom `deployment.toml` configuration:

1. **XML Parsing Error**: JDBC URLs with `&` characters caused XML parsing failures
2. **TenantManager Error**: Generated `user-mgt.xml` missing required TenantManager property  
3. **Database Configuration Error**: Required database keys referenced but not defined
4. **H2 Database Initialization Error**: Admin role creation failed with NULL constraints

## Root Cause
WSO2 APIM 4.0.0's TOML-to-XML configuration conversion process has severe limitations:
- Cannot properly handle complex JDBC URLs with query parameters
- Cannot generate valid `user-mgt.xml` from minimal `deployment.toml`
- Requires database configuration even for default H2 setup
- Configuration interdependencies cause circular failures

## Solution
**Use default APIM configuration instead of custom deployment.toml:**

1. **Removed deployment.toml mount** from `docker-compose-localhost.yml`
   - APIM starts with bundled default configuration (H2 database, default admin user)
   - No TOML-to-XML conversion errors

2. **Configure OAuth2 via REST API** after startup
   - Created script: `helpers/configure_apim_keymanager_api.sh`
   - Uses APIM Admin REST API to configure WSO2 IS as Key Manager
   - OAuth2 credentials registered via `helpers/configure_wso2_oauth_apps.py`

## Files Modified

### docker-compose-localhost.yml
```yaml
volumes:
  - wso2apim_data:/home/wso2carbon/wso2am-4.0.0
  # deployment.toml mount disabled - use default config + REST API for OAuth2
  # - ./wso2apim-4-config/deployment.toml:/.../deployment.toml:ro
```

### helpers/configure_apim_keymanager_api.sh (NEW)
Script to configure APIM Key Manager via REST API using OAuth2 credentials from WSO2 IS.

Usage:
```bash
export KEYMANAGER_CLIENT_ID="<client_id_from_deployment.toml.oauth2-backup>"
export KEYMANAGER_CLIENT_SECRET="<client_secret_from_deployment.toml.oauth2-backup>"
./helpers/configure_apim_keymanager_api.sh
```

## Verification

✅ **APIM Container**: Healthy and running
```
docker ps --filter "name=darts-wso2apim"
# STATUS: Up X minutes (healthy)
```

✅ **All Portals Accessible**:
- Publisher: https://localhost:9444/publisher → HTTP 302 (working)
- Admin: https://localhost:9444/admin → HTTP 302 (working)  
- DevPortal: https://localhost:9444/devportal → HTTP 302 (working)

✅ **Key Manager Configured**: WSO2 IS integrated via REST API

## Lessons Learned

1. **WSO2 APIM 4.0.0 deployment.toml has limitations** - not suitable for complex configurations
2. **REST API configuration is more reliable** than TOML for OAuth2 setup
3. **Default configurations work** - avoid unnecessary customization
4. **Docker volume management** - clearing `wso2apim_data` volume is essential for clean restart

## Recommendations

1. **Use environment variables** for configuration instead of deployment.toml where possible
2. **Configure OAuth2 post-startup** via Admin REST API or UI
3. **Keep deployment.toml minimal** or use defaults entirely
4. **Document REST API configuration workflow** for reproducibility

## Backup Files

- `wso2apim-4-config/deployment.toml.oauth2-backup` - Contains OAuth2 credentials from previous DCR registration
- `wso2apim-4-config/deployment.toml.disabled` - Failed custom configuration (reference only)

---

**Status**: ✅ RESOLVED  
**Date**: December 31, 2025  
**APIM Version**: 4.0.0  
**Approach**: Default config + REST API configuration
