#!/bin/bash
# Script to update WSO2 IS OAuth2 Application Callback URLs
# This script provides instructions and a curl command to update the callback URLs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================"
echo "WSO2 Identity Server - Update Callback URLs"
echo "================================================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Configuration
WSO2_IS_URL="${WSO2_IS_URL:-https://letsplaydarts.eu/auth}"
WSO2_CLIENT_ID="${WSO2_CLIENT_ID}"
CALLBACK_URI="${WSO2_REDIRECT_URI:-https://letsplaydarts.eu/callback}"
POST_LOGOUT_URI="${WSO2_POST_LOGOUT_REDIRECT_URI:-https://letsplaydarts.eu/}"

echo -e "${BLUE}Configuration:${NC}"
echo "  WSO2 IS URL: $WSO2_IS_URL"
echo "  Client ID: $WSO2_CLIENT_ID"
echo "  Callback URI: $CALLBACK_URI"
echo "  Post-Logout URI: $POST_LOGOUT_URI"
echo ""

echo -e "${YELLOW}⚠️  IMPORTANT: Manual Configuration Required${NC}"
echo ""
echo "The OAuth2 application in WSO2 IS needs to be updated to include"
echo "both the callback URI (for login) and post-logout redirect URI."
echo ""
echo -e "${GREEN}Follow these steps:${NC}"
echo ""
echo "1. Open WSO2 IS Management Console:"
echo "   ${BLUE}$WSO2_IS_URL/carbon${NC}"
echo ""
echo "2. Login with credentials:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "3. Navigate to:"
echo "   Main → Identity → Service Providers → List"
echo ""
echo "4. Find and click 'Edit' on your application"
echo ""
echo "5. Expand 'Inbound Authentication Configuration'"
echo ""
echo "6. Click 'Configure' under 'OAuth/OpenID Connect Configuration'"
echo ""
echo "7. Update the 'Callback Url' field with this regex pattern:"
echo ""
echo -e "${GREEN}   regexp=https://letsplaydarts\\.eu(/callback|/)${NC}"
echo ""
echo "   This pattern allows both:"
echo "   ✓ https://letsplaydarts.eu/callback (login redirect)"
echo "   ✓ https://letsplaydarts.eu/ (logout redirect)"
echo ""
echo "8. Click 'Update' to save OAuth configuration"
echo ""
echo "9. Click 'Update' again to save Service Provider configuration"
echo ""
echo "================================================================"
echo ""
echo -e "${GREEN}Alternative: Comma-Separated List${NC}"
echo ""
echo "If regex doesn't work, use comma-separated URLs:"
echo ""
echo -e "${GREEN}   https://letsplaydarts.eu/callback,https://letsplaydarts.eu/${NC}"
echo ""
echo "================================================================"
echo ""
echo -e "${BLUE}After updating, test the flow:${NC}"
echo ""
echo "1. Navigate to: https://letsplaydarts.eu"
echo "2. Click 'Login' - should redirect to WSO2 IS and back"
echo "3. Click 'Logout' - should redirect to home page without errors"
echo ""
echo "================================================================"
echo ""
echo "For detailed instructions, see: FIX_REDIRECT_URIS.md"
echo ""
