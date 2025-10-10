#!/bin/bash

# Quick Start Script for Darts Game System with Authentication

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Display banner
if [ -f BANNER.txt ]; then
    cat BANNER.txt
    echo ""
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env file created"
    echo ""
    echo -e "${YELLOW}⚠ IMPORTANT:${NC} You need to configure WSO2 credentials in .env"
    echo "Please follow these steps:"
    echo ""
    echo "1. Run the WSO2 configuration script:"
    echo "   ${GREEN}./configure-wso2-roles.sh${NC}"
    echo ""
    echo "2. Follow the manual configuration steps"
    echo ""
    echo "3. Update .env with your Client ID and Client Secret"
    echo ""
    echo "4. Run this script again"
    echo ""
    exit 0
fi

# Check if WSO2 credentials are configured
WSO2_CLIENT_ID=$(grep "^WSO2_CLIENT_ID=" .env | cut -d '=' -f2)
if [ "$WSO2_CLIENT_ID" == "your_client_id_here" ] || [ -z "$WSO2_CLIENT_ID" ]; then
    echo -e "${RED}✗${NC} WSO2 Client ID not configured in .env"
    echo ""
    echo "Please:"
    echo "1. Run: ${GREEN}./configure-wso2-roles.sh${NC}"
    echo "2. Follow the configuration steps"
    echo "3. Update WSO2_CLIENT_ID and WSO2_CLIENT_SECRET in .env"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Configuration file found"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f docker-compose-wso2.yml up -d

echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
echo ""

# Wait for WSO2 IS
echo -n "WSO2 Identity Server: "
max_attempts=60
attempt=0
until curl -k -s https://localhost:9443/carbon/admin/login.jsp > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}✗ Timeout${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓ Ready${NC}"

# Wait for RabbitMQ
echo -n "RabbitMQ: "
attempt=0
until curl -s http://localhost:15672 > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq 30 ]; then
        echo -e "${RED}✗ Timeout${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓ Ready${NC}"

# Wait for Darts App
echo -n "Darts Application: "
attempt=0
until curl -s http://localhost:5000 > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq 30 ]; then
        echo -e "${RED}✗ Timeout${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓ Ready${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All services are ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${BLUE}Access URLs:${NC}"
echo ""
echo -e "  ${GREEN}Darts Game Application:${NC}"
echo -e "    http://localhost:5000"
echo ""
echo -e "  ${GREEN}WSO2 Identity Server:${NC}"
echo -e "    https://localhost:9443/carbon"
echo -e "    Username: admin"
echo -e "    Password: admin"
echo ""
echo -e "  ${GREEN}RabbitMQ Management:${NC}"
echo -e "    http://localhost:15672"
echo -e "    Username: guest"
echo -e "    Password: guest"
echo ""
echo -e "  ${GREEN}API Gateway:${NC}"
echo -e "    http://localhost:8080"
echo ""

echo -e "${BLUE}Test Users:${NC}"
echo ""
echo -e "  ${GREEN}Player:${NC}"
echo -e "    Username: testplayer"
echo -e "    Password: Player@123"
echo ""
echo -e "  ${YELLOW}Game Master:${NC}"
echo -e "    Username: testgamemaster"
echo -e "    Password: GameMaster@123"
echo ""
echo -e "  ${RED}Admin:${NC}"
echo -e "    Username: testadmin"
echo -e "    Password: Admin@123"
echo ""

echo -e "${YELLOW}Note:${NC} You need to create these users in WSO2 IS first!"
echo "See: ${GREEN}docs/AUTHENTICATION_SETUP.md${NC}"
echo ""

echo -e "${BLUE}Quick Commands:${NC}"
echo ""
echo -e "  View logs:"
echo -e "    ${GREEN}docker-compose -f docker-compose-wso2.yml logs -f${NC}"
echo ""
echo -e "  Stop services:"
echo -e "    ${GREEN}docker-compose -f docker-compose-wso2.yml down${NC}"
echo ""
echo -e "  Restart services:"
echo -e "    ${GREEN}docker-compose -f docker-compose-wso2.yml restart${NC}"
echo ""

echo -e "${GREEN}Ready to play darts! 🎯${NC}"
echo ""
