#!/bin/bash
# Configure WSO2 APIM Key Manager via REST API
# This script configures APIM to use WSO2 IS as the Key Manager using OAuth2 credentials

set -e

APIM_HOST="${APIM_HOST:-localhost}"
APIM_PORT="${APIM_PORT:-9444}"
APIM_ADMIN_USER="${APIM_ADMIN_USER:-admin}"
APIM_ADMIN_PASS="${APIM_ADMIN_PASS:-admin}"

IS_HOST="${IS_HOST:-wso2is}"
IS_PORT="${IS_PORT:-9443}"

# OAuth2 credentials from helpers/configure_wso2_oauth_apps.py output
# These should match the credentials in wso2apim-4-config/deployment.toml.oauth2-backup
KEYMANAGER_CLIENT_ID="${KEYMANAGER_CLIENT_ID}"
KEYMANAGER_CLIENT_SECRET="${KEYMANAGER_CLIENT_SECRET}"

if [ -z "$KEYMANAGER_CLIENT_ID" ] || [ -z "$KEYMANAGER_CLIENT_SECRET" ]; then
    echo "ERROR: KEYMANAGER_CLIENT_ID and KEYMANAGER_CLIENT_SECRET must be set"
    echo "Extract these from wso2apim-4-config/deployment.toml.oauth2-backup"
    echo "Example:"
    echo "  export KEYMANAGER_CLIENT_ID='your_client_id'"
    echo "  export KEYMANAGER_CLIENT_SECRET='your_client_secret'"
    exit 1
fi

echo "Configuring WSO2 APIM Key Manager via REST API..."
echo "APIM: https://${APIM_HOST}:${APIM_PORT}"
echo "IS: https://${IS_HOST}:${IS_PORT}"

# Get access token
echo "Getting admin access token..."
# Use basic auth to get token from default APIM
TOKEN_RESPONSE=$(curl -k -s -X POST \
    -u "${APIM_ADMIN_USER}:${APIM_ADMIN_PASS}" \
    "https://${APIM_HOST}:${APIM_PORT}/client-registration/v0.17/register" \
    -H "Content-Type: application/json" \
    -d '{
        "clientName": "admin_rest_api_client",
        "owner": "admin",
        "grantType": "password refresh_token",
        "saasApp": true
    }')

CLIENT_ID=$(echo "$TOKEN_RESPONSE" | grep -o '"clientId":"[^"]*' | cut -d'"' -f4)
CLIENT_SECRET=$(echo "$TOKEN_RESPONSE" | grep -o '"clientSecret":"[^"]*' | cut -d'"' -f4)

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "ERROR: Failed to register client"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "Client registered: $CLIENT_ID"

# Now get access token
TOKEN_RESPONSE=$(curl -k -s -X POST \
    "https://${APIM_HOST}:${APIM_PORT}/oauth2/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -u "${CLIENT_ID}:${CLIENT_SECRET}" \
    -d "grant_type=password&username=${APIM_ADMIN_USER}&password=${APIM_ADMIN_PASS}&scope=apim:admin")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "ERROR: Failed to get access token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "Access token obtained successfully"

# Configure Key Manager
echo "Configuring WSO2 IS as Key Manager..."
KM_CONFIG='{
  "name": "WSO2_IS",
  "displayName": "WSO2 Identity Server",
  "type": "WSO2-IS",
  "description": "WSO2 Identity Server as Key Manager",
  "enabled": true,
  "additionalProperties": {
    "Username": "'"${KEYMANAGER_CLIENT_ID}"'",
    "Password": "'"${KEYMANAGER_CLIENT_SECRET}"'",
    "client_registration_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/api/identity/oauth2/dcr/v1.1/register",
    "introspection_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/oauth2/introspect",
    "token_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/oauth2/token",
    "revoke_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/oauth2/revoke",
    "userinfo_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/oauth2/userinfo",
    "authorize_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/oauth2/authorize",
    "jwks_endpoint": "https://'"${IS_HOST}"':'"${IS_PORT}"'/oauth2/jwks"
  }
}'

KM_RESPONSE=$(curl -k -s -X POST \
    "https://${APIM_HOST}:${APIM_PORT}/api/am/admin/v4/key-managers" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$KM_CONFIG")

echo "Key Manager configuration response:"
echo "$KM_RESPONSE"

echo ""
echo "✅ Key Manager configuration complete!"
echo "You can verify in APIM Admin Portal: https://${APIM_HOST}:${APIM_PORT}/admin"
