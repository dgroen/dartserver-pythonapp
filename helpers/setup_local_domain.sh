#!/bin/bash
# Setup local domain in /etc/hosts for development

set -e

DOMAIN="${1:-letsplaydarts.eu}"
IP="${2:-127.0.0.1}"

echo "Setting up local domain: $DOMAIN -> $IP"

# Check if domain already exists in /etc/hosts
if grep -q "$DOMAIN" /etc/hosts; then
    echo "⚠️  Domain '$DOMAIN' already exists in /etc/hosts"
    echo ""
    echo "Current entry:"
    grep "$DOMAIN" /etc/hosts
    echo ""
    read -p "Do you want to update it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping update."
        exit 0
    fi

    # Remove existing entry
    sudo sed -i "/$DOMAIN/d" /etc/hosts
fi

# Add new entry
echo "$IP $DOMAIN" | sudo tee -a /etc/hosts > /dev/null

echo "✓ Domain added successfully!"
echo ""
echo "Entry added to /etc/hosts:"
grep "$DOMAIN" /etc/hosts
echo ""
echo "You can now access the application at:"
echo "  http://$DOMAIN:5000 (if SSL disabled)"
echo "  https://$DOMAIN:5000 (if SSL enabled)"
echo ""
echo "To test DNS resolution:"
echo "  ping $DOMAIN"
echo "  nslookup $DOMAIN"
