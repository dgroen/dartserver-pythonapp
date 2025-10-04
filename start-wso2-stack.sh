#!/bin/bash

# Start WSO2 Stack for Darts Game System
# This script starts all services including WSO2 IS, WSO2 APIM, API Gateway, and RabbitMQ

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print header
print_header() {
    echo ""
    print_message "$BLUE" "=================================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=================================================="
    echo ""
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message "$RED" "Error: Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_message "$RED" "Error: docker-compose is not installed. Please install it and try again."
        exit 1
    fi
}

# Check system resources
check_resources() {
    print_message "$YELLOW" "Checking system resources..."
    
    # Check available memory (Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        available_mem=$(free -g | awk '/^Mem:/{print $7}')
        if [ "$available_mem" -lt 4 ]; then
            print_message "$YELLOW" "Warning: Less than 4GB of available memory. WSO2 services may not start properly."
            print_message "$YELLOW" "Recommended: At least 8GB of available memory."
        fi
    fi
}

# Create necessary directories
create_directories() {
    print_message "$YELLOW" "Creating necessary directories..."
    mkdir -p nginx/ssl
}

# Generate self-signed SSL certificates for development
generate_ssl_certs() {
    if [ ! -f "nginx/ssl/cert.pem" ]; then
        print_message "$YELLOW" "Generating self-signed SSL certificates for development..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
            2>/dev/null || print_message "$YELLOW" "Warning: Could not generate SSL certificates. Nginx may not start."
    fi
}

# Start services
start_services() {
    print_header "Starting Services"
    
    # Start RabbitMQ first
    print_message "$YELLOW" "Starting RabbitMQ..."
    docker-compose -f docker-compose-wso2.yml up -d rabbitmq
    
    # Wait for RabbitMQ to be healthy
    print_message "$YELLOW" "Waiting for RabbitMQ to be ready..."
    timeout=60
    elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if docker-compose -f docker-compose-wso2.yml ps rabbitmq | grep -q "healthy"; then
            print_message "$GREEN" "✓ RabbitMQ is ready"
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    # Start WSO2 Identity Server
    print_message "$YELLOW" "Starting WSO2 Identity Server (this may take 2-3 minutes)..."
    docker-compose -f docker-compose-wso2.yml up -d wso2is
    
    # Start WSO2 API Manager
    print_message "$YELLOW" "Starting WSO2 API Manager (this may take 3-4 minutes)..."
    docker-compose -f docker-compose-wso2.yml up -d wso2apim
    
    # Start API Gateway
    print_message "$YELLOW" "Starting API Gateway..."
    docker-compose -f docker-compose-wso2.yml up -d api-gateway
    
    # Start Darts Application
    print_message "$YELLOW" "Starting Darts Application..."
    docker-compose -f docker-compose-wso2.yml up -d darts-app
    
    # Optionally start Nginx
    if [ "$1" == "--with-nginx" ]; then
        print_message "$YELLOW" "Starting Nginx reverse proxy..."
        docker-compose -f docker-compose-wso2.yml up -d nginx
    fi
}

# Show service status
show_status() {
    print_header "Service Status"
    docker-compose -f docker-compose-wso2.yml ps
}

# Show access information
show_access_info() {
    print_header "Access Information"
    
    print_message "$GREEN" "Services are starting up. Please wait a few minutes for all services to be ready."
    echo ""
    
    print_message "$BLUE" "RabbitMQ Management:"
    echo "  URL: http://localhost:15672"
    echo "  Username: guest"
    echo "  Password: guest"
    echo ""
    
    print_message "$BLUE" "WSO2 Identity Server:"
    echo "  URL: https://localhost:9443/carbon"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    
    print_message "$BLUE" "WSO2 API Manager Publisher:"
    echo "  URL: https://localhost:9444/publisher"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    
    print_message "$BLUE" "WSO2 API Manager Developer Portal:"
    echo "  URL: https://localhost:9444/devportal"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    
    print_message "$BLUE" "API Gateway:"
    echo "  URL: http://localhost:8080"
    echo "  Health Check: http://localhost:8080/health"
    echo ""
    
    print_message "$BLUE" "Darts Application:"
    echo "  URL: http://localhost:5000"
    echo "  Game Board: http://localhost:5000"
    echo "  Control Panel: http://localhost:5000/control"
    echo ""
    
    print_message "$YELLOW" "Note: WSO2 services may take 5-10 minutes to fully start."
    print_message "$YELLOW" "You may see certificate warnings in your browser (this is normal for development)."
    echo ""
    
    print_message "$BLUE" "Next Steps:"
    echo "  1. Wait for all services to start (check with: docker-compose -f docker-compose-wso2.yml ps)"
    echo "  2. Follow the setup guide: docs/WSO2_SETUP_GUIDE.md"
    echo "  3. Configure WSO2 Identity Server and API Manager"
    echo "  4. Test the API Gateway"
    echo ""
    
    print_message "$BLUE" "Useful Commands:"
    echo "  View logs: docker-compose -f docker-compose-wso2.yml logs -f [service_name]"
    echo "  Stop services: docker-compose -f docker-compose-wso2.yml down"
    echo "  Restart service: docker-compose -f docker-compose-wso2.yml restart [service_name]"
    echo ""
}

# Main execution
main() {
    print_header "Darts Game System - WSO2 Stack Startup"
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    check_resources
    
    # Prepare environment
    create_directories
    generate_ssl_certs
    
    # Start services
    start_services "$1"
    
    # Wait a bit for services to initialize
    sleep 5
    
    # Show status
    show_status
    
    # Show access information
    show_access_info
    
    print_message "$GREEN" "Startup script completed!"
}

# Run main function
main "$@"