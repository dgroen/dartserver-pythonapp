# WSO2 APIM Configuration

## Setup Instructions

The `deployment.toml` file contains sensitive OAuth2 credentials and is **not tracked by git** for security reasons.

### Initial Setup

1. **Copy the template:**
   ```bash
   cp deployment.toml.template deployment.toml
   ```

2. **Create OAuth2 applications in WSO2 IS Console** (https://localhost:9443/console):

   #### Application 1: APIM_KeyManager (M2M/Service Account)
   - **Type:** M2M Application or Traditional Web Application
   - **Name:** `APIM_KeyManager`
   - **Grant Types:** Client Credentials, Password, Refresh Token
   - **Redirect URL:** `https://localhost:9444/commonauth`

   After creation, copy **Client ID** and **Client Secret** from Protocol tab.

   #### Application 2: APIM (Portal Authentication)
   - **Type:** Traditional Web Application
   - **Name:** `APIM`
   - **Grant Types:** Code, Refresh Token, Implicit
   - **Redirect URLs:**
     - `https://localhost:9444/publisher/services/auth/callback`
     - `https://localhost:9444/devportal/services/auth/callback`
     - `https://localhost:9444/admin/services/auth/callback`
     - `https://localhost:9444/analytics/services/auth/callback`

   After creation, copy **Client ID** and **Client Secret** from Protocol tab.

3. **Update deployment.toml with credentials:**

   Edit `deployment.toml` and replace the placeholders:

   ```toml
   [keymanager.default]
   username = "PASTE_KEY_MANAGER_CLIENT_ID_HERE"  # From APIM_KeyManager app
   password = "PASTE_KEY_MANAGER_CLIENT_SECRET_HERE"

   [oauth2.oidc]
   client_id = "PASTE_PORTAL_CLIENT_ID_HERE"  # From APIM app
   client_secret = "PASTE_PORTAL_CLIENT_SECRET_HERE"
   ```

4. **Restart APIM:**
   ```bash
   docker-compose -f docker-compose-localhost.yml restart wso2apim
   ```

## Security Notes

- `deployment.toml` is in `.gitignore` and will **not be committed**
- `deployment.toml.template` is the version-controlled template without credentials
- Never commit actual OAuth2 client secrets to version control
- Each environment (dev/staging/prod) should have its own OAuth2 applications

## Files

- `deployment.toml.template` - Template file (tracked by git)
- `deployment.toml` - Active config with credentials (ignored by git)

## Troubleshooting

If you see "Cannot find an application associated with the given consumer key":
- Verify both OAuth2 applications are created in WSO2 IS
- Check that credentials in `deployment.toml` match those in WSO2 IS console
- Ensure APIM container has been restarted after config changes
