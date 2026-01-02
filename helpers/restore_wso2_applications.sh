#!/bin/bash

# Restore WSO2 IS Applications and Configuration
# This script reconfigures WSO2 IS after database persistence is enabled

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "========================================="
echo "Restoring WSO2 IS Applications"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if WSO2 IS is running
log_info "Checking if WSO2 IS is running..."
if ! curl -k -s https://localhost:9443/api/health-check/v1.0/health > /dev/null 2>&1; then
    log_error "WSO2 IS is not running or not healthy"
    log_error "Please start WSO2 IS first:"
    log_error "  docker-compose -f docker-compose-wso2.yml up -d wso2is"
    exit 1
fi
log_info "WSO2 IS is running"

echo ""

# Step 1: Configure WSO2 roles
log_info "Step 1: Configuring WSO2 roles..."
if python3 helpers/setup_wso2_roles.py; then
    log_info "✓ Roles configured successfully"
else
    log_warn "⚠ Roles configuration failed (may already exist)"
fi

echo ""

# Step 2: Register test client
log_info "Step 2: Registering test OAuth2 client..."
if python3 helpers/register_wso2_test_client.py; then
    log_info "✓ Test client registered successfully"
else
    log_warn "⚠ Test client registration failed (may already exist)"
fi

echo ""

# Step 3: Register DartsApp OAuth2 client
log_info "Step 3: Registering DartsApp OAuth2 client..."
if python3 helpers/register_darts_app.py; then
    log_info "✓ DartsApp registered successfully"
else
    log_warn "⚠ DartsApp registration failed (may already exist)"
fi

echo ""

# Step 4: Configure APIM OAuth2 clients
log_info "Step 4: Configuring APIM OAuth2 clients..."
if python3 helpers/configure_wso2_oauth_apps.py; then
    log_info "✓ APIM clients configured successfully"
else
    log_warn "⚠ APIM clients configuration failed"
fi

echo ""

# Step 5: Setup APIM OAuth2 clients
log_info "Step 5: Setting up APIM OAuth2 clients..."
if bash helpers/setup_apim_oauth2_clients.sh; then
    log_info "✓ APIM OAuth2 clients setup successfully"
else
    log_warn "⚠ APIM OAuth2 clients setup failed"
fi

echo ""

# Step 6: Configure WSO2 IS for APIM
log_info "Step 6: Configuring WSO2 IS for APIM integration..."
if python3 helpers/configure_wso2_is_for_apim.py; then
    log_info "✓ WSO2 IS configured for APIM"
else
    log_warn "⚠ WSO2 IS APIM configuration failed"
fi

echo ""
log_info "========================================="
log_info "WSO2 IS Applications Restoration Complete"
log_info "========================================="
echo ""
log_info "You can now access:"
echo "  - WSO2 IS Console: https://localhost:9443/console"
echo "  - WSO2 IS Management: https://localhost:9443/carbon"
echo "  - APIM Publisher: https://localhost:9444/publisher"
echo "  - APIM DevPortal: https://localhost:9444/devportal"
echo ""
log_info "Default credentials: admin / admin"