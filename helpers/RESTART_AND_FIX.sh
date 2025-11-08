#!/bin/bash
# Complete fix for redirect issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}       WSO2 Identity Server - Complete Redirect Fix${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

echo -e "${YELLOW}Two issues need to be fixed:${NC}"
echo ""
echo -e "${GREEN}✅ Issue 1: Missing /auth prefix in URLs${NC}"
echo "   Status: Configuration updated"
echo "   Action: Restart WSO2 IS container"
echo ""
echo -e "${YELLOW}⚠️  Issue 2: Post-logout redirect URI not registered${NC}"
echo "   Status: Requires manual configuration"
echo "   Action: Update Service Provider in WSO2 IS Console"
echo ""

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                    PART 1: Restart WSO2 IS${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

echo -e "${BLUE}The configuration file has been updated with:${NC}"
echo "  proxy_context_path = \"/auth\""
echo ""
echo "This tells WSO2 IS to include /auth in all generated URLs."
echo ""

read -p "Press Enter to restart WSO2 IS container..."
echo ""

echo -e "${YELLOW}Restarting WSO2 IS...${NC}"
docker-compose -f docker-compose-wso2.yml restart wso2is

echo ""
echo -e "${GREEN}✅ WSO2 IS container restarted${NC}"
echo ""
echo -e "${YELLOW}⏳ Waiting for WSO2 IS to start (this takes 2-3 minutes)...${NC}"
echo ""

# Wait for WSO2 IS to be ready
max_retries=60
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if docker logs wso2is 2>&1 | grep -q "WSO2 Carbon started"; then
        echo ""
        echo -e "${GREEN}✅ WSO2 IS is ready!${NC}"
        break
    fi

    echo -n "."
    sleep 3
    retry_count=$((retry_count + 1))

    if [ $retry_count -eq $max_retries ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Timeout waiting for WSO2 IS. Check logs:${NC}"
        echo "   docker logs wso2is"
    fi
done

echo ""
echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}              PART 2: Update Service Provider${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

echo -e "${YELLOW}⚠️  Manual configuration required${NC}"
echo ""
echo "You need to register both callback and post-logout URIs in WSO2 IS."
echo ""
echo -e "${BLUE}Follow these steps:${NC}"
echo ""
echo "1. Open WSO2 IS Management Console:"
echo -e "   ${GREEN}https://letsplaydarts.eu/auth/carbon${NC}"
echo ""
echo "2. Login with:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "3. Navigate to:"
echo "   Main → Identity → Service Providers → List"
echo ""
echo "4. Edit your application"
echo ""
echo "5. In OAuth/OpenID Connect Configuration, update Callback Url:"
echo ""
echo -e "${GREEN}   regexp=https://letsplaydarts\\.eu(/callback|/)${NC}"
echo ""
echo "   This allows both:"
echo "   ✓ https://letsplaydarts.eu/callback (login)"
echo "   ✓ https://letsplaydarts.eu/ (logout)"
echo ""
echo "6. Click 'Update' twice to save"
echo ""

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                         Testing${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

echo "After completing Part 2, test the flow:"
echo ""
echo "1. Navigate to: https://letsplaydarts.eu"
echo "2. Click 'Login'"
echo "   → Should redirect to: https://letsplaydarts.eu/auth/oauth2/authorize"
echo "   → Should show login page (not 404)"
echo ""
echo "3. Authenticate"
echo "   → Should redirect back to application"
echo "   → Should be logged in"
echo ""
echo "4. Click 'Logout'"
echo "   → Should redirect to: https://letsplaydarts.eu/auth/oidc/logout"
echo "   → Should redirect to home page"
echo "   → Should NOT show error message"
echo ""

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                    Documentation${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

echo "For detailed instructions, see:"
echo ""
echo "  📄 COMPLETE_REDIRECT_FIX.md      - Complete overview"
echo "  📄 FIX_MISSING_AUTH_PREFIX.md    - /auth prefix fix details"
echo "  📄 QUICK_FIX_REDIRECTS.md        - Quick 5-minute guide"
echo "  📄 REDIRECT_FLOW_EXPLAINED.md    - Visual explanation"
echo ""

echo -e "${CYAN}================================================================${NC}"
echo ""
echo -e "${GREEN}Part 1 Complete! ✅${NC}"
echo -e "${YELLOW}Part 2 Pending... ⚠️${NC}"
echo ""
echo "Please complete Part 2 (Service Provider configuration) to finish the fix."
echo ""
