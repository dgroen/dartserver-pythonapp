#!/bin/bash
# Start the Darts Game Server with HTTPS enabled

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Darts Game Server with HTTPS...${NC}"
echo ""

# Check if SSL certificates exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo -e "${YELLOW}SSL certificates not found. Generating them now...${NC}"
    ./helpers/generate_ssl_certs.sh
    echo ""
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Set FLASK_USE_SSL environment variable
export FLASK_USE_SSL=True

echo -e "${GREEN}Configuration:${NC}"
echo "  - Protocol: HTTPS"
echo "  - Host: ${FLASK_HOST:-0.0.0.0}"
echo "  - Port: ${FLASK_PORT:-5000}"
echo "  - Debug: ${FLASK_DEBUG:-True}"
echo ""
echo -e "${YELLOW}⚠️  Browser Security Warning:${NC}"
echo "  Your browser will show a security warning because we're using"
echo "  self-signed certificates. This is normal for local development."
echo "  Click 'Advanced' and 'Proceed to localhost' to continue."
echo ""
echo -e "${GREEN}Access the application at:${NC}"
echo "  https://localhost:${FLASK_PORT:-5000}"
echo ""
echo -e "${GREEN}WSO2 Configuration Reminder:${NC}"
echo "  Make sure your WSO2 IS OAuth application has the callback URL:"
echo "  https://localhost:${FLASK_PORT:-5000}/callback"
echo ""

# Start the application
python app.py
