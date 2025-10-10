#!/bin/bash

# WSO2 Identity Server Role Configuration Script
# This script configures roles and OAuth2 application for the Darts Game System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WSO2_IS_URL="${WSO2_IS_URL:-https://localhost:9443}"
WSO2_ADMIN_USER="${WSO2_ADMIN_USER:-admin}"
WSO2_ADMIN_PASS="${WSO2_ADMIN_PASS:-admin}"
APP_NAME="DartsGameWebApp"
CALLBACK_URL="${CALLBACK_URL:-http://localhost:5000/callback}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WSO2 IS Role Configuration for Darts Game${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Wait for WSO2 IS to be ready
echo -e "${YELLOW}Waiting for WSO2 Identity Server to be ready...${NC}"
max_attempts=30
attempt=0
until curl -k -s "${WSO2_IS_URL}/carbon/admin/login.jsp" > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        print_error "WSO2 IS did not start in time"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_status "WSO2 Identity Server is ready"

echo ""
echo -e "${BLUE}Manual Configuration Steps:${NC}"
echo ""
echo "Please follow these steps in the WSO2 Identity Server Management Console:"
echo ""
echo -e "${YELLOW}1. Create Roles:${NC}"
echo "   a. Login to: ${WSO2_IS_URL}/carbon"
echo "   b. Go to: Main > Identity > Users and Roles > Add"
echo "   c. Click 'Add New Role'"
echo "   d. Create the following roles:"
echo "      - ${GREEN}player${NC}      (Basic player access)"
echo "      - ${GREEN}gamemaster${NC}  (Game management access)"
echo "      - ${GREEN}admin${NC}       (Full system access)"
echo ""

echo -e "${YELLOW}2. Create Users:${NC}"
echo "   a. Go to: Main > Identity > Users and Roles > Add"
echo "   b. Click 'Add New User'"
echo "   c. Create test users and assign roles:"
echo "      - Username: ${GREEN}testplayer${NC}     Role: player"
echo "      - Username: ${GREEN}testgamemaster${NC} Role: gamemaster"
echo "      - Username: ${GREEN}testadmin${NC}      Role: admin"
echo ""

echo -e "${YELLOW}3. Register OAuth2 Application:${NC}"
echo "   a. Go to: Main > Identity > Service Providers > Add"
echo "   b. Service Provider Name: ${GREEN}${APP_NAME}${NC}"
echo "   c. Click 'Register'"
echo "   d. Expand 'Inbound Authentication Configuration'"
echo "   e. Expand 'OAuth/OpenID Connect Configuration'"
echo "   f. Click 'Configure'"
echo "   g. Set the following:"
echo "      - Callback URL: ${GREEN}${CALLBACK_URL}${NC}"
echo "      - Allowed Grant Types: Check 'Code' and 'Refresh Token'"
echo "      - PKCE: Optional (Recommended: Plain)"
echo "   h. Click 'Add'"
echo "   i. Copy the generated Client ID and Client Secret"
echo ""

echo -e "${YELLOW}4. Configure Claims:${NC}"
echo "   a. In the same Service Provider configuration"
echo "   b. Expand 'Claim Configuration'"
echo "   c. Select 'Use Local Claim Dialect'"
echo "   d. Add the following Requested Claims:"
echo "      - http://wso2.org/claims/username"
echo "      - http://wso2.org/claims/emailaddress"
echo "      - http://wso2.org/claims/role"
echo "   e. Set Subject Claim URI: http://wso2.org/claims/username"
echo "   f. Click 'Update'"
echo ""

echo -e "${YELLOW}5. Update Environment Variables:${NC}"
echo "   Add the following to your .env file:"
echo ""
echo "   ${GREEN}# WSO2 Authentication Configuration${NC}"
echo "   WSO2_IS_URL=${WSO2_IS_URL}"
echo "   WSO2_CLIENT_ID=<your_client_id_from_step_3>"
echo "   WSO2_CLIENT_SECRET=<your_client_secret_from_step_3>"
echo "   WSO2_REDIRECT_URI=${CALLBACK_URL}"
echo "   JWT_VALIDATION_MODE=introspection"
echo "   WSO2_IS_INTROSPECT_USER=admin"
echo "   WSO2_IS_INTROSPECT_PASSWORD=admin"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Role Permissions Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Player Role:${NC}"
echo "  - View game board"
echo "  - Submit scores"
echo "  - View game state"
echo ""
echo -e "${YELLOW}Game Master Role:${NC}"
echo "  - All Player permissions"
echo "  - Access control panel"
echo "  - Create new games"
echo "  - Add/remove players"
echo "  - Manage game settings"
echo ""
echo -e "${RED}Admin Role:${NC}"
echo "  - All Game Master permissions"
echo "  - Full system access"
echo "  - User management"
echo "  - System configuration"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Authentication${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "After configuration, test the authentication:"
echo ""
echo "1. Start the application:"
echo "   ${GREEN}python app.py${NC}"
echo ""
echo "2. Open browser and navigate to:"
echo "   ${GREEN}http://localhost:5000${NC}"
echo ""
echo "3. You should be redirected to WSO2 IS login page"
echo ""
echo "4. Login with one of the test users:"
echo "   - testplayer / <password>"
echo "   - testgamemaster / <password>"
echo "   - testadmin / <password>"
echo ""
echo "5. After successful login, you should be redirected back to the application"
echo ""

echo -e "${GREEN}Configuration guide complete!${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} For production use, please:"
echo "  - Use proper SSL certificates"
echo "  - Create strong passwords for users"
echo "  - Use a dedicated service account for introspection"
echo "  - Enable additional security features (MFA, etc.)"
echo ""
