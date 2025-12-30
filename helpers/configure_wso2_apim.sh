#!/bin/bash
#
# WSO2 APIM Configuration Script
# Runs after APIM container starts to configure the Darts API
#
# This script waits for APIM to be ready, then runs the Python setup script
# to create throttling policies, define the API, and publish it.

set -e

echo "=========================================="
echo "WSO2 APIM Configuration for Darts System"
echo "=========================================="

# Configuration
APIM_URL="${WSO2_APIM_URL:-https://wso2apim:9443}"
API_GATEWAY_URL="${API_GATEWAY_INTERNAL_URL:-http://api-gateway:8080}"
ADMIN_USER="${WSO2_ADMIN_USERNAME:-admin}"
ADMIN_PASS="${WSO2_ADMIN_PASSWORD:-admin}"
MAX_WAIT_TIME="${APIM_WAIT_TIME:-300}"  # 5 minutes

# Wait for APIM to be ready
echo "Waiting for WSO2 APIM to be ready at $APIM_URL..."
ELAPSED=0
INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT_TIME ]; do
    if curl -k -s -f "${APIM_URL}/api/am/publisher/v4/apis?limit=1" > /dev/null 2>&1; then
        echo "✓ WSO2 APIM is responding"
        break
    fi
    
    echo "  Waiting... (${ELAPSED}s/${MAX_WAIT_TIME}s)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT_TIME ]; then
    echo "✗ Timeout waiting for WSO2 APIM to be ready"
    exit 1
fi

# Give APIM a few more seconds to fully initialize
echo "Waiting 10 more seconds for APIM to fully initialize..."
sleep 10

# Run the Python setup script
echo ""
echo "Running APIM configuration script..."
python3 /app/helpers/setup_wso2_apim.py \
    --apim-url "$APIM_URL" \
    --username "$ADMIN_USER" \
    --password "$ADMIN_PASS" \
    --api-gateway-url "$API_GATEWAY_URL" \
    --verbose

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ APIM configuration completed!"
    echo "=========================================="
    echo ""
    echo "APIM Gateway URLs:"
    echo "  HTTP:  http://localhost:8280/api/v1/"
    echo "  HTTPS: https://localhost:8243/api/v1/"
    echo ""
    echo "Publisher Portal:"
    echo "  $APIM_URL/publisher"
    echo ""
    echo "Developer Portal:"
    echo "  $APIM_URL/devportal"
    echo ""
else
    echo ""
    echo "✗ APIM configuration failed"
    exit 1
fi
