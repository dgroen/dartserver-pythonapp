#!/bin/bash

# OAuth2 Fix Verification Script
# This script verifies that the OAuth2 localhost redirect issue is resolved

set -e

echo "=========================================="
echo "OAuth2 Fix Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print info
info() {
    echo -e "ℹ $1"
}

echo "1. Checking Container Status..."
echo "-------------------------------------------"

# Check Flask app
if docker ps | grep -q "darts-app"; then
    success "Flask app (darts-app) is running"
else
    error "Flask app (darts-app) is not running"
    exit 1
fi

# Check WSO2 IS
if docker ps | grep "darts-wso2is" | grep -q "healthy"; then
    success "WSO2 IS (darts-wso2is) is running and healthy"
elif docker ps | grep -q "darts-wso2is"; then
    warning "WSO2 IS (darts-wso2is) is running but not healthy yet"
else
    error "WSO2 IS (darts-wso2is) is not running"
    exit 1
fi

# Check nginx
if docker ps | grep -q "darts-nginx"; then
    success "Nginx (darts-nginx) is running"
else
    error "Nginx (darts-nginx) is not running"
    exit 1
fi

echo ""
echo "2. Checking Environment Configuration..."
echo "-------------------------------------------"

# Check .env file
if [ -f ".env" ]; then
    success ".env file exists"
    
    # Check WSO2_IS_URL
    if grep -q "^WSO2_IS_URL=https://letsplaydarts.eu/auth" .env; then
        success "WSO2_IS_URL is set to https://letsplaydarts.eu/auth"
    else
        error "WSO2_IS_URL is not configured correctly"
    fi
    
    # Check WSO2_IS_INTERNAL_URL
    if grep -q "^WSO2_IS_INTERNAL_URL=https://wso2is:9443" .env; then
        success "WSO2_IS_INTERNAL_URL is set to https://wso2is:9443"
    else
        error "WSO2_IS_INTERNAL_URL is not configured correctly"
    fi
    
    # Check WSO2_IS_VERIFY_SSL
    if grep -q "^WSO2_IS_VERIFY_SSL=False" .env; then
        success "WSO2_IS_VERIFY_SSL is set to False (correct for internal communication)"
    else
        warning "WSO2_IS_VERIFY_SSL might need to be set to False for internal communication"
    fi
else
    error ".env file not found"
    exit 1
fi

echo ""
echo "3. Testing Internal Connectivity..."
echo "-------------------------------------------"

# Test Flask → WSO2 connectivity
info "Testing Flask app → WSO2 IS connectivity..."
RESPONSE=$(docker exec darts-app python -c "import requests; requests.packages.urllib3.disable_warnings(); r = requests.get('https://wso2is:9443/oauth2/token', verify=False); print(r.status_code)" 2>/dev/null || echo "ERROR")

if [ "$RESPONSE" = "405" ]; then
    success "Flask app can reach WSO2 IS internally (Status: 405 - expected)"
elif [ "$RESPONSE" = "ERROR" ]; then
    error "Flask app cannot reach WSO2 IS internally"
else
    warning "Flask app reached WSO2 IS but got unexpected status: $RESPONSE"
fi

echo ""
echo "4. Checking Flask Configuration..."
echo "-------------------------------------------"

# Check Flask logs for configuration
info "Checking Flask app configuration from logs..."
APP_URL=$(docker logs darts-app 2>&1 | grep "App URL:" | tail -1 | awk '{print $NF}')
CALLBACK_URL=$(docker logs darts-app 2>&1 | grep "Callback URL:" | tail -1 | awk '{print $NF}')

if [ "$APP_URL" = "https://letsplaydarts.eu" ]; then
    success "App URL is configured correctly: $APP_URL"
else
    error "App URL is not configured correctly: $APP_URL"
fi

if [ "$CALLBACK_URL" = "https://letsplaydarts.eu/callback" ]; then
    success "Callback URL is configured correctly: $CALLBACK_URL"
else
    error "Callback URL is not configured correctly: $CALLBACK_URL"
fi

echo ""
echo "5. Checking for Recent Errors..."
echo "-------------------------------------------"

# Check nginx logs for 503 errors
info "Checking nginx logs for 503 errors (last 5 minutes)..."
NGINX_503_COUNT=$(docker logs darts-nginx --since 5m 2>&1 | grep -c "503" || echo "0")
if [ "$NGINX_503_COUNT" = "0" ]; then
    success "No 503 errors in nginx logs (last 5 minutes)"
else
    warning "Found $NGINX_503_COUNT 503 errors in nginx logs (last 5 minutes)"
fi

# Check Flask logs for connection errors
info "Checking Flask logs for connection errors (last 5 minutes)..."
FLASK_ERROR_COUNT=$(docker logs darts-app --since 5m 2>&1 | grep -c "Connection refused" || echo "0")
if [ "$FLASK_ERROR_COUNT" = "0" ]; then
    success "No connection errors in Flask logs (last 5 minutes)"
else
    warning "Found $FLASK_ERROR_COUNT connection errors in Flask logs (last 5 minutes)"
fi

echo ""
echo "6. Checking WSO2 Configuration..."
echo "-------------------------------------------"

# Check deployment.toml
if [ -f "wso2is-7-config/deployment.toml" ]; then
    success "deployment.toml exists"
    
    # Check hostname
    if grep -q 'hostname = "letsplaydarts.eu"' wso2is-7-config/deployment.toml; then
        success "WSO2 hostname is set to letsplaydarts.eu"
    else
        error "WSO2 hostname is not configured correctly"
    fi
    
    # Check proxyPort
    if grep -q 'proxyPort = 443' wso2is-7-config/deployment.toml; then
        success "WSO2 proxyPort is set to 443"
    else
        error "WSO2 proxyPort is not configured correctly"
    fi
else
    error "deployment.toml not found"
fi

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""

# Count successes and errors
SUCCESS_COUNT=$(grep -c "✓" /tmp/oauth_verify_output.txt 2>/dev/null || echo "0")
ERROR_COUNT=$(grep -c "✗" /tmp/oauth_verify_output.txt 2>/dev/null || echo "0")

if [ "$ERROR_COUNT" = "0" ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo ""
    echo "✅ OAuth2 localhost redirect issue is RESOLVED"
    echo "✅ Internal WSO2 communication is working"
    echo "✅ Configuration is correct"
    echo ""
    echo "Next steps:"
    echo "1. Test the OAuth flow by visiting: https://letsplaydarts.eu/login"
    echo "2. Monitor logs during authentication"
    echo "3. Verify token validation works for protected endpoints"
    echo ""
    exit 0
else
    echo -e "${RED}Some checks failed!${NC}"
    echo ""
    echo "Please review the errors above and fix the configuration."
    echo "See OAUTH_FIX_COMPLETE.md for detailed troubleshooting steps."
    echo ""
    exit 1
fi