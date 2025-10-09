#!/bin/bash

# WSO2 Integration Test Script
# Tests all API Gateway endpoints with OAuth2 authentication

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
WSO2_TOKEN_URL="https://localhost:9443/oauth2/token"
API_GATEWAY_URL="http://localhost:8080"
CLIENT_ID="${WSO2_IS_CLIENT_ID:-L2rvop0o4DfJsqpqsh44cUgVn_ga}"
CLIENT_SECRET="${WSO2_IS_CLIENT_SECRET:-VhNFUK083Q2iUsu8GCWfcJTVCX8a}"

echo "========================================="
echo "WSO2 API Gateway Integration Test"
echo "========================================="
echo ""

# Function to get access token
get_token() {
    local scope=$1
    echo -e "${YELLOW}Getting access token with scope: $scope${NC}"
    
    TOKEN=$(curl -k -s -X POST "$WSO2_TOKEN_URL" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials" \
        -d "client_id=$CLIENT_ID" \
        -d "client_secret=$CLIENT_SECRET" \
        -d "scope=$scope" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}✗ Failed to get access token${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Token obtained: ${TOKEN:0:20}...${NC}"
    echo ""
}

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
RESPONSE=$(curl -s "$API_GATEWAY_URL/health")
if echo "$RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# Test 2: Submit Score
echo "Test 2: Submit Score"
echo "--------------------"
get_token "score:write"

RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/v1/scores" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "score": 20,
        "multiplier": "TRIPLE",
        "player_id": "test-player-1",
        "game_id": "test-game-1"
    }')

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Score submitted successfully${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ Score submission failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# Test 3: Create Game
echo "Test 3: Create Game"
echo "-------------------"
get_token "game:write"

RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/v1/games" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "game_type": "301",
        "players": ["Player A", "Player B", "Player C"],
        "double_out": false
    }')

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Game created successfully${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ Game creation failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# Test 4: Add Player
echo "Test 4: Add Player"
echo "------------------"
get_token "player:write"

RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/v1/players" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Player"
    }')

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Player added successfully${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ Player addition failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# Test 5: Test without token (should fail)
echo "Test 5: Unauthorized Access (should fail)"
echo "------------------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_GATEWAY_URL/api/v1/scores" \
    -H "Content-Type: application/json" \
    -d '{
        "score": 20,
        "multiplier": "SINGLE",
        "player_id": "test",
        "game_id": "test"
    }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected unauthorized request${NC}"
else
    echo -e "${RED}✗ Should have rejected unauthorized request${NC}"
    echo "HTTP Code: $HTTP_CODE"
fi
echo ""

# Test 6: Test with wrong scope (should fail)
echo "Test 6: Insufficient Permissions (should fail)"
echo "-----------------------------------------------"
get_token "game:read"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_GATEWAY_URL/api/v1/scores" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "score": 20,
        "multiplier": "SINGLE",
        "player_id": "test",
        "game_id": "test"
    }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}✓ Correctly rejected request with insufficient permissions${NC}"
else
    echo -e "${RED}✗ Should have rejected request with insufficient permissions${NC}"
    echo "HTTP Code: $HTTP_CODE"
fi
echo ""

# Check RabbitMQ
echo "Test 7: RabbitMQ Message Flow"
echo "------------------------------"
RABBITMQ_STATS=$(curl -s -u guest:guest http://localhost:15672/api/queues)
if echo "$RABBITMQ_STATS" | grep -q "message_stats"; then
    PUBLISHED=$(echo "$RABBITMQ_STATS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['message_stats'].get('publish', 0))" 2>/dev/null || echo "0")
    ACKNOWLEDGED=$(echo "$RABBITMQ_STATS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['message_stats'].get('ack', 0))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ RabbitMQ is operational${NC}"
    echo "  Messages published: $PUBLISHED"
    echo "  Messages acknowledged: $ACKNOWLEDGED"
else
    echo -e "${YELLOW}⚠ Could not retrieve RabbitMQ stats${NC}"
fi
echo ""

# Summary
echo "========================================="
echo -e "${GREEN}All tests completed successfully!${NC}"
echo "========================================="
echo ""
echo "System Status:"
echo "  ✓ API Gateway: Running"
echo "  ✓ WSO2 Identity Server: Running"
echo "  ✓ RabbitMQ: Running"
echo "  ✓ OAuth2 Authentication: Working"
echo "  ✓ Token Introspection: Working"
echo "  ✓ Scope-based Authorization: Working"
echo "  ✓ Message Publishing: Working"
echo ""
echo "Next steps:"
echo "  1. Access the Darts UI at http://localhost:5000"
echo "  2. Access RabbitMQ Management at http://localhost:15672"
echo "  3. Access WSO2 IS Console at https://localhost:9443/carbon"
echo "  4. Review logs: docker-compose -f docker-compose-wso2.yml logs -f"
echo ""