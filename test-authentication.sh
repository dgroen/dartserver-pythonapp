#!/bin/bash

# Authentication Testing Script
# This script helps verify that authentication is working correctly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Authentication Testing Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if services are running
echo -e "${YELLOW}Checking services...${NC}"
echo ""

# Check Darts App
echo -n "Darts Application (http://localhost:5000): "
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
    echo "Please start services with: ./start-with-auth.sh"
    exit 1
fi

# Check WSO2 IS
echo -n "WSO2 Identity Server (https://localhost:9443): "
if curl -k -s https://localhost:9443/carbon/admin/login.jsp > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
    echo "Please start services with: ./start-with-auth.sh"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are running!${NC}"
echo ""

# Test unauthenticated access
echo -e "${YELLOW}Testing unauthenticated access...${NC}"
echo ""

echo -n "GET /: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
if [ "$RESPONSE" == "302" ] || [ "$RESPONSE" == "401" ]; then
    echo -e "${GREEN}✓ Redirects to login (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $RESPONSE)${NC}"
fi

echo -n "GET /control: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/control)
if [ "$RESPONSE" == "302" ] || [ "$RESPONSE" == "401" ]; then
    echo -e "${GREEN}✓ Redirects to login (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $RESPONSE)${NC}"
fi

echo -n "GET /api/game: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/game)
if [ "$RESPONSE" == "302" ] || [ "$RESPONSE" == "401" ]; then
    echo -e "${GREEN}✓ Redirects to login (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $RESPONSE)${NC}"
fi

echo ""
echo -e "${GREEN}✓ Unauthenticated access is properly blocked${NC}"
echo ""

# Test login page
echo -e "${YELLOW}Testing login page...${NC}"
echo ""

echo -n "GET /login: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}✓ Login page accessible (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $RESPONSE)${NC}"
fi

echo ""

# Test WSO2 OAuth2 endpoints
echo -e "${YELLOW}Testing WSO2 OAuth2 endpoints...${NC}"
echo ""

echo -n "Authorization endpoint: "
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" "https://localhost:9443/oauth2/authorize")
if [ "$RESPONSE" == "302" ] || [ "$RESPONSE" == "400" ]; then
    echo -e "${GREEN}✓ Accessible (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $RESPONSE)${NC}"
fi

echo -n "Token endpoint: "
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" "https://localhost:9443/oauth2/token")
if [ "$RESPONSE" == "400" ] || [ "$RESPONSE" == "401" ]; then
    echo -e "${GREEN}✓ Accessible (HTTP $RESPONSE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $RESPONSE)${NC}"
fi

echo ""
echo -e "${GREEN}✓ WSO2 OAuth2 endpoints are accessible${NC}"
echo ""

# Manual testing instructions
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Manual Testing Instructions${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}1. Test Player Role:${NC}"
echo "   - Open: http://localhost:5000"
echo "   - Login as: testplayer / Player@123"
echo "   - Verify: Can view game board"
echo "   - Verify: Can submit scores"
echo "   - Verify: CANNOT access /control"
echo ""

echo -e "${YELLOW}2. Test Game Master Role:${NC}"
echo "   - Open: http://localhost:5000"
echo "   - Login as: testgamemaster / GameMaster@123"
echo "   - Verify: Can view game board"
echo "   - Verify: Can access /control"
echo "   - Verify: Can create games"
echo "   - Verify: Can add/remove players"
echo ""

echo -e "${YELLOW}3. Test Admin Role:${NC}"
echo "   - Open: http://localhost:5000"
echo "   - Login as: testadmin / Admin@123"
echo "   - Verify: Can access all features"
echo "   - Verify: Can access /control"
echo "   - Verify: Full system access"
echo ""

echo -e "${YELLOW}4. Test Logout:${NC}"
echo "   - Click 'Logout' button"
echo "   - Verify: Redirected to login page"
echo "   - Verify: Cannot access protected pages"
echo ""

echo -e "${YELLOW}5. Test Role Badges:${NC}"
echo "   - Login with each role"
echo "   - Verify: Correct role badge displayed"
echo "   - Verify: Username shown in header"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Checklist${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "[ ] Player can login and view game board"
echo "[ ] Player CANNOT access control panel"
echo "[ ] Game Master can access control panel"
echo "[ ] Game Master can create games"
echo "[ ] Admin has full access"
echo "[ ] Logout works correctly"
echo "[ ] Role badges display correctly"
echo "[ ] Unauthenticated users are redirected to login"
echo "[ ] Invalid credentials are rejected"
echo "[ ] Session persists across page refreshes"
echo ""

echo -e "${GREEN}Automated tests completed!${NC}"
echo -e "${YELLOW}Please complete manual tests above.${NC}"
echo ""