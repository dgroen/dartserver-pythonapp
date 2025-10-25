#!/bin/bash
# Generate self-signed SSL certificates for local development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_ROOT/ssl"

# Default domain
DOMAIN="${1:-localhost}"

echo "Generating self-signed SSL certificates for domain: $DOMAIN"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Create OpenSSL configuration file for SAN
cat > "$SSL_DIR/openssl.cnf" <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=EU
ST=Europe
L=Development
O=Darts Game Server
OU=Development
CN=$DOMAIN

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = localhost
DNS.4 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$SSL_DIR/cert.pem" \
    -keyout "$SSL_DIR/key.pem" \
    -days 365 \
    -config "$SSL_DIR/openssl.cnf" \
    -extensions v3_req

# Set proper permissions
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/key.pem"

echo "✓ SSL certificates generated successfully!"
echo "  Certificate: $SSL_DIR/cert.pem"
echo "  Private Key: $SSL_DIR/key.pem"
echo "  Domain: $DOMAIN"
echo ""
echo "Certificate Details:"
openssl x509 -in "$SSL_DIR/cert.pem" -noout -subject -dates -ext subjectAltName
echo ""
echo "Note: These are self-signed certificates for development only."
echo "Your browser will show a security warning - this is expected."
echo "You can safely proceed past the warning for local development."
echo ""
echo "To trust this certificate on your system:"
echo "  Linux: sudo cp $SSL_DIR/cert.pem /usr/local/share/ca-certificates/$DOMAIN.crt && sudo update-ca-certificates"
echo "  macOS: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $SSL_DIR/cert.pem"
echo "  Windows: Import $SSL_DIR/cert.pem into 'Trusted Root Certification Authorities'"
