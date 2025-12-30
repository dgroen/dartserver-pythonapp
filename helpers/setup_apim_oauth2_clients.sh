#!/bin/bash

# Setup WSO2 APIM OAuth2 clients in WSO2 IS for versions 7.x
# This script uses the Service Provider API to register APIM

set -e

# Configuration
APIM_HOST="${APIM_HOST:-localhost}"
APIM_PORT="${APIM_PORT:-9444}"
IS_HOST="${IS_HOST:-localhost}"
IS_PORT="${IS_PORT:-9443}"
IS_ADMIN_USER="${IS_ADMIN_USER:-admin}"
IS_ADMIN_PASSWORD="${IS_ADMIN_PASSWORD:-admin}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

log_info "Setting up APIM OAuth2 clients in WSO2 IS 7.x..."
log_info "APIM Host: https://$APIM_HOST:$APIM_PORT"
log_info "IS Host: https://$IS_HOST:$IS_PORT"
echo ""

# Wait for IS to be ready
log_info "Waiting for WSO2 IS to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while ! curl -k -s https://$IS_HOST:$IS_PORT/identity/ > /dev/null 2>&1; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    log_error "WSO2 IS did not become ready in time"
    exit 1
  fi
  echo "  Attempt $RETRY_COUNT/$MAX_RETRIES..."
  sleep 2
done
log_success "WSO2 IS is ready"
echo ""

# Try to get OAuth2 token using admin credentials
log_info "Attempting to get OAuth2 token from WSO2 IS..."

TOKEN_RESPONSE=$(curl -k -s -X POST \
  "https://$IS_HOST:$IS_PORT/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=$IS_ADMIN_USER&password=$IS_ADMIN_PASSWORD&scope=internal_manage_applications" \
  --user admin:admin)

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$ACCESS_TOKEN" ]; then
  log_success "Got access token from WSO2 IS"
  
  # Try to register via Service Provider API
  log_info "Registering APIM as service provider in WSO2 IS..."
  
  SP_RESPONSE=$(curl -k -s -X POST \
    "https://$IS_HOST:$IS_PORT/api/server/v1/applications" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "name": "APIM",
      "description": "WSO2 API Manager Portal",
      "accessUrl": "https://'"$APIM_HOST:$APIM_PORT"'/publisher",
      "inboundProtocols": [
        "oauth2"
      ]
    }')
  
  APP_ID=$(echo "$SP_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
  
  if [ ! -z "$APP_ID" ]; then
    log_success "Service provider created: $APP_ID"
    echo ""
  fi
fi

# Manual registration instructions
log_warn "OAuth2 registration requires manual setup in WSO2 IS admin console"
echo ""
log_info "Steps to complete APIM OAuth2 integration:"
echo ""
echo "  1. Open WSO2 IS Console: https://$IS_HOST:$IS_PORT/console"
echo "  2. Login with credentials:"
echo "     Username: $IS_ADMIN_USER"
echo "     Password: $IS_ADMIN_PASSWORD"
echo ""
echo "  3. Navigate to: Applications → New Application"
echo ""
echo "  4. Select protocol and fill in:"
echo ""
echo "     Protocol: OAuth 2.0 OpenID Connect"
echo "     Application Name: APIM"
echo ""
echo "     Authorized Redirect URLs (add all):"
echo "       • https://$APIM_HOST:$APIM_PORT/publisher/services/auth/callback"
echo "       • https://$APIM_HOST:$APIM_PORT/devportal/services/auth/callback"
echo "       • https://$APIM_HOST:$APIM_PORT/admin/services/auth/callback"
echo "       • https://$APIM_HOST:$APIM_PORT/analytics/services/auth/callback"
echo ""
echo "     Allowed Grant Types:"
echo "       • Code"
echo "       • Refresh Token"
echo "       • Implicit"
echo ""
echo "     Public Client: No (keep unchecked)"
echo ""
echo "  5. Register the application"
echo ""
echo "  6. Go to Protocol tab and copy the credentials:"
echo "     • Client ID"
echo "     • Client Secret"
echo ""
echo "  7. Update /wso2apim-4-config/deployment.toml [oauth2.oidc] section:"
echo ""
cat << 'TOML'
[oauth2.oidc]
client_id = "<CLIENT_ID_FROM_STEP_5>"
client_secret = "<CLIENT_SECRET_FROM_STEP_5>"
server_url = "https://wso2is:9443"
authorize_endpoint = "https://wso2is:9443/oauth2/authorize"
token_endpoint = "https://wso2is:9443/oauth2/token"
revoke_endpoint = "https://wso2is:9443/oauth2/revoke"
userinfo_endpoint = "https://wso2is:9443/oauth2/userinfo"
TOML
echo ""
echo "  7. Restart APIM container:"
echo "     docker-compose -f docker-compose-localhost.yml restart wso2apim"
echo ""
echo "  8. Wait for APIM to fully start (check: docker ps)"
echo ""
echo "  9. Test portal access:"
echo "     https://$APIM_HOST:$APIM_PORT/publisher"
echo "     https://$APIM_HOST:$APIM_PORT/devportal"
echo "     https://$APIM_HOST:$APIM_PORT/admin"
echo ""
