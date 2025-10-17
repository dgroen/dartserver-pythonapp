#!/bin/bash

# Configure Localhost Login for Darts Application
# Helps fix login/redirection issues on localhost by setting up correct scheme and SSL configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Display banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Localhost Login Configuration for Darts Application  ${NC}${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Ask user which scheme they want to use
echo -e "${YELLOW}Choose how to access the application:${NC}"
echo ""
echo -e "  ${GREEN}1)${NC} HTTP on localhost (http://localhost:5000)"
echo -e "     Pros: No SSL certificate warnings"
echo -e "     Cons: Less secure (dev only)"
echo ""
echo -e "  ${GREEN}2)${NC} HTTPS on localhost (https://localhost:5000)"
echo -e "     Pros: Matches production setup, more secure"
echo -e "     Cons: Self-signed certificate warnings in browser"
echo ""
echo -e "  ${GREEN}3)${NC} Auto-detect (recommended)"
echo -e "     Pros: Works with both HTTP and HTTPS automatically"
echo -e "     Cons: Requires browser cookies to be enabled"
echo ""
echo -n "Enter your choice (1-3): "
read -r choice

case "$choice" in
  1)
    echo ""
    echo -e "${YELLOW}Setting up for HTTP localhost...${NC}"
    SCHEME="http"
    FLASK_USE_SSL="False"
    SESSION_COOKIE_SECURE="False"
    SAMESITE="Lax"
    ;;
  2)
    echo ""
    echo -e "${YELLOW}Setting up for HTTPS localhost...${NC}"
    SCHEME="https"
    FLASK_USE_SSL="True"
    SESSION_COOKIE_SECURE="True"
    SAMESITE="Lax"
    ;;
  3)
    echo ""
    echo -e "${YELLOW}Setting up for auto-detect mode...${NC}"
    SCHEME="http"
    FLASK_USE_SSL="False"
    SESSION_COOKIE_SECURE="False"
    SAMESITE="Lax"
    echo -e "${BLUE}ℹ${NC} In auto-detect mode, you can access via http:// or https://"
    echo -e "${BLUE}ℹ${NC} The app will adjust SESSION_COOKIE_SECURE automatically"
    ;;
  *)
    echo -e "${RED}✗ Invalid choice${NC}"
    exit 1
    ;;
esac

echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env file created"
    echo ""
fi

# Backup current .env
cp .env .env.backup.$(date +%s)
echo -e "${YELLOW}Backing up current .env...${NC}"
echo ""

# Update .env with new configuration
echo -e "${YELLOW}Updating .env configuration...${NC}"
echo ""

# Function to update or add a configuration value
update_env() {
    local key=$1
    local value=$2
    if grep -q "^${key}=" .env; then
        # Key exists, update it
        sed -i "s|^${key}=.*|${key}=${value}|" .env
        echo -e "  ${GREEN}✓${NC} ${key}=${value}"
    else
        # Key doesn't exist, append it
        echo "${key}=${value}" >> .env
        echo -e "  ${GREEN}✓${NC} ${key}=${value} (added)"
    fi
}

# Update configuration values
update_env "ENVIRONMENT" "development"
update_env "APP_DOMAIN" "localhost:5000"
update_env "APP_SCHEME" "$SCHEME"
update_env "FLASK_USE_SSL" "$FLASK_USE_SSL"
update_env "SESSION_COOKIE_SECURE" "$SESSION_COOKIE_SECURE"
update_env "SESSION_COOKIE_SAMESITE" "$SAMESITE"
update_env "WSO2_REDIRECT_URI" "${SCHEME}://localhost:5000/callback"
update_env "WSO2_POST_LOGOUT_REDIRECT_URI" "${SCHEME}://localhost:5000/"

echo ""
echo -e "${YELLOW}Configuring WSO2 callback URLs...${NC}"
echo ""

# For HTTP scheme, update to http pattern
# For HTTPS scheme, update to https pattern
if [ "$SCHEME" = "http" ]; then
    CALLBACK_PATTERN="regexp=http://localhost:5000(/callback|/)"
else
    CALLBACK_PATTERN="regexp=https://localhost:5000(/callback|/)"
fi

echo -e "  ${BLUE}ℹ${NC} You'll need to manually update WSO2 callback URLs:"
echo ""
echo -e "     1. Login to ${GREEN}https://localhost:9443/carbon${NC}"
echo -e "        Username: admin"
echo -e "        Password: admin"
echo ""
echo -e "     2. Go to: Main → Identity Providers → Registered OAuth/OIDC Apps"
echo ""
echo -e "     3. Select: ${GREEN}DartsApp${NC}"
echo ""
echo -e "     4. Update Callback URL to:"
echo -e "        ${GREEN}${CALLBACK_PATTERN}${NC}"
echo ""
echo -e "     5. Click Save"
echo ""
echo -e "  Or run: ${GREEN}python helpers/fix_callback_urls.py${NC}"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Configuration complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Show access URL
if [ "$SCHEME" = "http" ]; then
    URL="http://localhost:5000"
    echo -e "Access your app at: ${GREEN}${URL}${NC}"
    echo ""
    echo -e "Start the app with: ${GREEN}python app.py${NC}"
else
    URL="https://localhost:5000"
    echo -e "Access your app at: ${GREEN}${URL}${NC}"
    echo ""
    echo -e "Start the app with: ${GREEN}export FLASK_USE_SSL=True && python app.py${NC}"
    echo -e "or: ${GREEN}python app.py --ssl${NC}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "  1. Update WSO2 callback URLs (see above)"
echo -e "  2. Create test users in WSO2 (if not already done)"
echo -e "  3. Start the Flask application"
echo -e "  4. Navigate to ${GREEN}${URL}${NC}"
echo -e "  5. Click 'Login' and enter your WSO2 credentials"
echo ""

if [ "$SCHEME" = "https" ]; then
    echo -e "${YELLOW}SSL Certificate Info:${NC}"
    echo ""
    echo -e "  If you see a certificate warning:"
    echo -e "  • Click ${GREEN}Advanced${NC}"
    echo -e "  • Click ${GREEN}Proceed to localhost (unsafe)${NC}"
    echo ""
    echo -e "  This is normal for self-signed certificates on localhost"
    echo ""
fi

echo -e "${GREEN}For more details, see: ${GREEN}docs/LOCALHOST_LOGIN_FIX.md${NC}"
echo ""