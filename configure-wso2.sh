#!/bin/bash

# WSO2 Configuration Script
# This script configures WSO2 Identity Server with OAuth2 client credentials

set -e

echo "=== WSO2 Identity Server Configuration ==="
echo ""

# Configuration variables
WSO2_IS_HOST="localhost"
WSO2_IS_PORT="9443"
WSO2_ADMIN_USER="admin"
WSO2_ADMIN_PASS="admin"
CLIENT_NAME="DartsAPIGatewayClient"
CALLBACK_URL="http://localhost:8080/callback"

echo "Step 1: Testing WSO2 IS connectivity..."
if curl -k -s -f "https://${WSO2_IS_HOST}:${WSO2_IS_PORT}/carbon/admin/login.jsp" > /dev/null 2>&1; then
    echo "✓ WSO2 Identity Server is accessible"
else
    echo "✗ WSO2 Identity Server is not accessible"
    exit 1
fi

echo ""
echo "Step 2: Creating OAuth2 Service Provider..."
echo ""
echo "To create an OAuth2 client in WSO2 Identity Server, follow these steps:"
echo ""
echo "1. Open your browser and navigate to:"
echo "   https://localhost:9443/carbon"
echo ""
echo "2. Login with credentials:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "3. Navigate to: Main > Identity > Service Providers > Add"
echo ""
echo "4. Create a new Service Provider:"
echo "   - Service Provider Name: ${CLIENT_NAME}"
echo "   - Description: OAuth2 client for Darts API Gateway"
echo "   - Click 'Register'"
echo ""
echo "5. Configure Inbound Authentication:"
echo "   - Expand 'Inbound Authentication Configuration'"
echo "   - Expand 'OAuth/OpenID Connect Configuration'"
echo "   - Click 'Configure'"
echo ""
echo "6. OAuth Configuration:"
echo "   - Callback Url: ${CALLBACK_URL}"
echo "   - Grant Types: Select 'Client Credentials' and 'Password'"
echo "   - Click 'Add'"
echo ""
echo "7. Save the generated credentials:"
echo "   - OAuth Client Key (Client ID)"
echo "   - OAuth Client Secret"
echo ""
echo "8. Update the docker-compose-wso2.yml file with these credentials:"
echo "   WSO2_IS_CLIENT_ID=<your_client_id>"
echo "   WSO2_IS_CLIENT_SECRET=<your_client_secret>"
echo ""
echo "9. Restart the API Gateway:"
echo "   docker-compose -f docker-compose-wso2.yml restart api-gateway"
echo ""
echo "=== Alternative: Use WSO2 REST API (Advanced) ==="
echo ""
echo "You can also use the WSO2 DCR (Dynamic Client Registration) API:"
echo ""
cat << 'EOF'
curl -k -X POST https://localhost:9443/api/identity/oauth2/dcr/v1.1/register \
  -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "DartsAPIGatewayClient",
    "grant_types": ["client_credentials", "password"],
    "redirect_uris": ["http://localhost:8080/callback"],
    "ext_param_client_id": "darts_api_gateway",
    "ext_param_client_secret": "darts_secret_123"
  }'
EOF
echo ""
echo ""
echo "This will return the client_id and client_secret in the response."
echo ""

# Try to use DCR API
echo "Attempting automatic registration via DCR API..."
echo ""

RESPONSE=$(curl -k -s -X POST "https://${WSO2_IS_HOST}:${WSO2_IS_PORT}/api/identity/oauth2/dcr/v1.1/register" \
  -u "${WSO2_ADMIN_USER}:${WSO2_ADMIN_PASS}" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "DartsAPIGatewayClient",
    "grant_types": ["client_credentials", "password"],
    "redirect_uris": ["http://localhost:8080/callback"]
  }' 2>&1)

if echo "$RESPONSE" | grep -q "client_id"; then
    echo "✓ OAuth2 client created successfully!"
    echo ""
    echo "Client Credentials:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""
    
    CLIENT_ID=$(echo "$RESPONSE" | grep -o '"client_id":"[^"]*"' | cut -d'"' -f4)
    CLIENT_SECRET=$(echo "$RESPONSE" | grep -o '"client_secret":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ]; then
        echo ""
        echo "=== Configuration Complete ==="
        echo "Client ID: $CLIENT_ID"
        echo "Client Secret: $CLIENT_SECRET"
        echo ""
        echo "To use these credentials, export them as environment variables:"
        echo "export WSO2_IS_CLIENT_ID='$CLIENT_ID'"
        echo "export WSO2_IS_CLIENT_SECRET='$CLIENT_SECRET'"
        echo ""
        echo "Then restart the API Gateway:"
        echo "docker-compose -f docker-compose-wso2.yml restart api-gateway"
    fi
else
    echo "✗ Failed to create OAuth2 client automatically"
    echo "Response: $RESPONSE"
    echo ""
    echo "Please follow the manual steps above."
fi

echo ""
echo "=== Testing OAuth2 Token Endpoint ==="
echo ""
echo "Once configured, test token generation with:"
echo ""
echo "curl -k -X POST https://localhost:9443/oauth2/token \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "  -d 'grant_type=client_credentials' \\"
echo "  -d 'client_id=YOUR_CLIENT_ID' \\"
echo "  -d 'client_secret=YOUR_CLIENT_SECRET' \\"
echo "  -d 'scope=score:write'"
echo ""