#!/bin/bash

# WSO2 Identity Server Upgrade Script
# From 5.11.0 to 7.1.0

set -e

echo "========================================="
echo "WSO2 IS Upgrade Script: 5.11.0 → 7.1.0"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "docker-compose-wso2.yml" ]; then
    print_error "docker-compose-wso2.yml not found!"
    print_error "Please run this script from /data/dartserver-pythonapp directory"
    exit 1
fi

echo "This script will help you upgrade WSO2 IS from 5.11.0 to 7.1.0"
echo ""
print_warning "⚠️  IMPORTANT: This is a MAJOR version upgrade!"
print_warning "⚠️  Please read WSO2_IS_UPGRADE_GUIDE.md before proceeding"
echo ""

# Ask for confirmation
read -p "Have you read the upgrade guide and backed up your data? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    print_error "Please read the upgrade guide and backup your data first!"
    exit 1
fi

echo ""
print_info "Starting upgrade process..."
echo ""

# Step 1: Backup current configuration
print_info "Step 1: Backing up current configuration..."
if [ -f "wso2is-config/deployment.toml" ]; then
    cp wso2is-config/deployment.toml "wso2is-config/deployment.toml.5.11.0.backup.$(date +%Y%m%d_%H%M%S)"
    print_info "✅ Configuration backed up"
else
    print_warning "No existing deployment.toml found"
fi

# Step 2: Backup Docker volume
print_info "Step 2: Backing up Docker volume..."
read -p "Do you want to backup the WSO2 IS data volume? (yes/no): " backup_volume
if [ "$backup_volume" = "yes" ]; then
    backup_file="wso2is_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    print_info "Creating backup: $backup_file (this may take a few minutes)..."
    docker run --rm -v wso2is_data:/data -v $(pwd):/backup \
        alpine tar czf /backup/$backup_file /data 2>/dev/null || true
    if [ -f "$backup_file" ]; then
        print_info "✅ Volume backed up to: $backup_file"
    else
        print_warning "Backup may have failed, but continuing..."
    fi
fi

# Step 3: Create new configuration directory
print_info "Step 3: Creating new configuration directory..."
mkdir -p wso2is-7-config
print_info "✅ Directory created: wso2is-7-config/"

# Step 4: Create new deployment.toml for 7.1.0
print_info "Step 4: Creating new deployment.toml for WSO2 IS 7.1.0..."
cat > wso2is-7-config/deployment.toml << 'EOF'
[server]
hostname = "letsplaydarts.eu"
base_path = "https://letsplaydarts.eu/auth"

[super_admin]
username = "admin"
password = "admin"
create_admin_account = true

# Reverse proxy configuration
[proxy]
host_name = "letsplaydarts.eu"
context_path = "/auth"
https_port = 443

# Database configuration (using H2 for simplicity)
[database.identity_db]
type = "h2"
url = "jdbc:h2:./repository/database/WSO2IDENTITY_DB;DB_CLOSE_ON_EXIT=FALSE;LOCK_TIMEOUT=60000"
username = "wso2carbon"
password = "wso2carbon"

[database.shared_db]
type = "h2"
url = "jdbc:h2:./repository/database/WSO2SHARED_DB;DB_CLOSE_ON_EXIT=FALSE;LOCK_TIMEOUT=60000"
username = "wso2carbon"
password = "wso2carbon"

# User store configuration
[user_store]
type = "read_write_ldap_unique_id"
connection_url = "ldap://localhost:${Ports.EmbeddedLDAP.LDAPServerPort}"
connection_name = "uid=admin,ou=system"
connection_password = "admin"
base_dn = "dc=wso2,dc=org"

# OAuth configurations
[oauth]
prompt_consent = false

# CORS configuration
[cors]
allow_generic_http_requests = true
allow_any_origin = false
allowed_origins = [
    "https://letsplaydarts.eu"
]
allow_subdomains = false
supported_methods = [
    "GET",
    "POST",
    "HEAD",
    "OPTIONS"
]
support_any_header = true
supported_headers = []
exposed_headers = []
supports_credentials = true
max_age = 3600
tag_requests = false
EOF

print_info "✅ New deployment.toml created"

# Step 5: Show next steps
echo ""
print_info "========================================="
print_info "Backup Complete! Next Steps:"
print_info "========================================="
echo ""
echo "1. Review the new configuration file:"
echo "   cat wso2is-7-config/deployment.toml"
echo ""
echo "2. Update docker-compose-wso2.yml:"
echo "   - Change image: wso2/wso2is:5.11.0 → wso2/wso2is:7.1.0"
echo "   - Change volume path: wso2is-5.11.0 → wso2is-7.1.0"
echo "   - Update config mount: wso2is-config → wso2is-7-config"
echo "   - Update health check endpoint"
echo ""
echo "3. Stop current WSO2 IS:"
echo "   docker-compose -f docker-compose-wso2.yml stop wso2is"
echo ""
echo "4. Start new WSO2 IS 7.1.0:"
echo "   docker-compose -f docker-compose-wso2.yml up -d wso2is"
echo ""
echo "5. Monitor startup:"
echo "   docker logs -f darts-wso2is"
echo ""
echo "6. Access new console:"
echo "   https://letsplaydarts.eu:9443/console"
echo "   (Note: /carbon is removed in 7.x)"
echo ""
echo "7. Recreate Service Provider in new console"
echo ""
echo "8. Update .env with new Client ID and Secret"
echo ""
echo "9. Restart application:"
echo "   docker-compose -f docker-compose-wso2.yml restart darts-app api-gateway"
echo ""
echo "10. Test login and logout flows"
echo ""
print_warning "📖 For detailed instructions, see: WSO2_IS_UPGRADE_GUIDE.md"
echo ""

# Ask if user wants to see the docker-compose changes needed
read -p "Would you like to see the required docker-compose.yml changes? (yes/no): " show_changes
if [ "$show_changes" = "yes" ]; then
    echo ""
    print_info "========================================="
    print_info "Required docker-compose-wso2.yml Changes"
    print_info "========================================="
    echo ""
    cat << 'EOF'
  wso2is:
    image: wso2/wso2is:7.1.0  # ← CHANGED from 5.11.0
    container_name: darts-wso2is
    ports:
      - "9443:9443"
      - "9763:9763"
    environment:
      - JAVA_OPTS=-Xms512m -Xmx1024m
    volumes:
      - wso2is_7_data:/home/wso2carbon/wso2is-7.1.0  # ← CHANGED path
      - ./wso2is-7-config/deployment.toml:/home/wso2carbon/wso2is-7.1.0/repository/conf/deployment.toml:rw  # ← CHANGED
    healthcheck:
      test:
        [
          "CMD",
          "curl",
          "-k",
          "-f",
          "https://localhost:9443/api/health-check/v1.0/health",  # ← CHANGED endpoint
        ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    networks:
      - darts-network

volumes:
  wso2is_7_data:  # ← ADD new volume
  # ... other volumes
EOF
    echo ""
fi

# Ask if user wants to proceed with docker-compose update
read -p "Would you like me to create a backup of docker-compose-wso2.yml and update it? (yes/no): " update_compose
if [ "$update_compose" = "yes" ]; then
    print_info "Backing up docker-compose-wso2.yml..."
    cp docker-compose-wso2.yml "docker-compose-wso2.yml.backup.$(date +%Y%m%d_%H%M%S)"

    print_info "Updating docker-compose-wso2.yml..."

    # Update the image version
    sed -i 's|image: wso2/wso2is:5\.11\.0|image: wso2/wso2is:7.1.0|g' docker-compose-wso2.yml

    # Update volume paths
    sed -i 's|wso2is-5\.11\.0|wso2is-7.1.0|g' docker-compose-wso2.yml

    # Update config path
    sed -i 's|./wso2is-config/deployment\.toml|./wso2is-7-config/deployment.toml|g' docker-compose-wso2.yml

    # Update health check
    sed -i 's|https://localhost:9443/carbon/admin/login\.jsp|https://localhost:9443/api/health-check/v1.0/health|g' docker-compose-wso2.yml

    # Add new volume (if not exists)
    if ! grep -q "wso2is_7_data:" docker-compose-wso2.yml; then
        sed -i '/^volumes:/a\  wso2is_7_data:' docker-compose-wso2.yml
    fi

    print_info "✅ docker-compose-wso2.yml updated"
    print_warning "⚠️  Please review the changes before proceeding!"
    echo ""
    read -p "Would you like to view the diff? (yes/no): " view_diff
    if [ "$view_diff" = "yes" ]; then
        diff "docker-compose-wso2.yml.backup.$(date +%Y%m%d)_"* docker-compose-wso2.yml || true
    fi
fi

echo ""
print_info "========================================="
print_info "Preparation Complete!"
print_info "========================================="
echo ""
print_warning "Next: Review changes and start the upgrade"
print_warning "See WSO2_IS_UPGRADE_GUIDE.md for detailed steps"
echo ""
