#!/bin/bash
# Script to verify WSO2 IS redirect configuration

echo "=== WSO2 IS Redirect Configuration Verification ==="
echo ""

# Check if nginx is running
echo "1. Checking nginx configuration..."
if docker ps | grep -q darts-nginx; then
    echo "   ✓ Nginx container is running"
    docker exec darts-nginx nginx -t 2>&1 | grep -q "successful" && echo "   ✓ Nginx configuration is valid" || echo "   ✗ Nginx configuration has errors"
else
    echo "   ✗ Nginx container is not running"
fi
echo ""

# Check if darts-app is running
echo "2. Checking darts-app configuration..."
if docker ps | grep -q darts-app; then
    echo "   ✓ Darts-app container is running"

    # Check environment variables
    echo "   Checking environment variables..."
    docker exec darts-app printenv | grep WSO2_IS_URL | head -1
    docker exec darts-app printenv | grep WSO2_REDIRECT_URI
    docker exec darts-app printenv | grep SESSION_COOKIE_SECURE
else
    echo "   ✗ Darts-app container is not running"
fi
echo ""

# Check if WSO2 IS is running
echo "3. Checking WSO2 IS configuration..."
if docker ps | grep -q darts-wso2is; then
    echo "   ✓ WSO2 IS container is running"

    # Check if deployment.toml is mounted
    if docker exec darts-wso2is test -f /home/wso2carbon/wso2is-5.11.0/repository/conf/deployment.toml; then
        echo "   ✓ deployment.toml is present"

        # Check hostname configuration
        HOSTNAME=$(docker exec darts-wso2is grep "^hostname" /home/wso2carbon/wso2is-5.11.0/repository/conf/deployment.toml 2>/dev/null)
        if [ ! -z "$HOSTNAME" ]; then
            echo "   $HOSTNAME"
        fi

        # Check base_path configuration
        BASE_PATH=$(docker exec darts-wso2is grep "^base_path" /home/wso2carbon/wso2is-5.11.0/repository/conf/deployment.toml 2>/dev/null)
        if [ ! -z "$BASE_PATH" ]; then
            echo "   $BASE_PATH"
        fi
    else
        echo "   ✗ deployment.toml is not found"
    fi
else
    echo "   ✗ WSO2 IS container is not running"
fi
echo ""

# Check recent logs for redirect URI
echo "4. Checking recent logs for redirect URI..."
if docker ps | grep -q darts-app; then
    echo "   Recent redirect URI logs:"
    docker logs darts-app 2>&1 | grep -i "redirect" | tail -5
fi
echo ""

# Test the authorization URL generation
echo "5. Testing authorization URL generation..."
echo "   You can test by accessing: https://letsplaydarts.eu/login"
echo "   Expected redirect URI should be: https://letsplaydarts.eu/callback"
echo ""

# Check nginx X-Forwarded headers
echo "6. Checking nginx X-Forwarded headers configuration..."
if docker exec darts-nginx cat /etc/nginx/nginx.conf 2>/dev/null | grep -q "X-Forwarded-Host"; then
    echo "   ✓ X-Forwarded-Host header is configured"
else
    echo "   ✗ X-Forwarded-Host header is NOT configured"
fi

if docker exec darts-nginx cat /etc/nginx/nginx.conf 2>/dev/null | grep -q "X-Forwarded-Proto"; then
    echo "   ✓ X-Forwarded-Proto header is configured"
else
    echo "   ✗ X-Forwarded-Proto header is NOT configured"
fi
echo ""

echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. If any checks failed, restart the services:"
echo "   docker-compose -f docker-compose-wso2.yml down"
echo "   docker-compose -f docker-compose-wso2.yml up -d"
echo ""
echo "2. Configure OAuth application in WSO2 IS:"
echo "   - Access: https://letsplaydarts.eu/auth/carbon"
echo "   - Add callback URL: https://letsplaydarts.eu/callback"
echo ""
echo "3. Test the login flow:"
echo "   - Navigate to: https://letsplaydarts.eu/login"
echo "   - Check browser network tab for redirect_uri parameter"
echo ""
