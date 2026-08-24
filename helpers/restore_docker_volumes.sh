#!/bin/bash

################################################################################
# Docker Volumes Restore Script
#
# This script restores Docker volumes from a backup created by backup_docker_volumes.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./docker-backups"
PROJECT_NAME="${PROJECT_NAME:-dartserver-pythonapp}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose-wso2.yml}"
AUTO_CONFIRM=false
RESTORE_PATH=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backup)
            RESTORE_PATH="$2"
            shift 2
            ;;
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 -b <backup-path> [OPTIONS]"
            echo ""
            echo "Required:"
            echo "  -b, --backup <path>   Path to backup directory to restore from"
            echo ""
            echo "Options:"
            echo "  -y, --yes            Automatically confirm restore without prompting"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 -b ./docker-backups/2024-11-23_14-30-00"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}          ${GREEN}Docker Volumes Restore Script${NC}                     ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_backup_exists() {
    if [ -z "$RESTORE_PATH" ]; then
        print_error "No backup path specified. Use -b <backup-path>"
        exit 1
    fi

    if [ ! -d "$RESTORE_PATH" ]; then
        print_error "Backup directory does not exist: $RESTORE_PATH"
        exit 1
    fi

    print_success "Backup directory found: $RESTORE_PATH"
}

check_docker() {
    print_step "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    print_success "Docker is installed"
}

stop_containers() {
    print_step "Stopping containers (project: ${PROJECT_NAME})..."
    docker-compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down 2>/dev/null || true
    print_success "Containers stopped"
}

restore_volume() {
    local volume=$1
    local full_volume_name="${PROJECT_NAME}_${volume}"
    local backup_file="${RESTORE_PATH}/${volume}.tar.gz"

    if [ ! -f "$backup_file" ]; then
        print_warning "Backup file not found: ${backup_file}, skipping..."
        return
    fi

    print_step "Restoring ${full_volume_name}..."

    # Remove old volume if it exists
    if docker volume inspect "$full_volume_name" &> /dev/null; then
        docker volume rm "$full_volume_name" 2>/dev/null || true
    fi

    # Create new volume
    docker volume create "$full_volume_name" > /dev/null

    # Restore from backup
    docker run --rm \
        -v "${full_volume_name}:/data" \
        -v "$(cd $(dirname $RESTORE_PATH) && pwd)/$(basename $RESTORE_PATH):/backup:ro" \
        alpine \
        tar xzf "/backup/${volume}.tar.gz" -C /data

    if [ $? -eq 0 ]; then
        print_success "Restored ${volume}"
    else
        print_error "Failed to restore ${volume}"
        return 1
    fi
}

restore_postgres_dump() {
    local sql_dump="${RESTORE_PATH}/postgres_dump.sql.gz"

    if [ ! -f "$sql_dump" ]; then
        print_warning "PostgreSQL dump not found, skipping SQL restore"
        return
    fi

    print_step "Restoring PostgreSQL database from SQL dump (project: ${PROJECT_NAME})..."

    # Start only postgres temporarily, scoped to PROJECT_NAME/COMPOSE_FILE so
    # this doesn't collide with an unrelated stack's own postgres container.
    docker-compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d postgres
    sleep 10

    # Find postgres container within this project specifically (COMPOSE_FILE
    # may hardcode container_name, so don't just grep for "postgres" - that
    # can ambiguously match an unrelated stack's container too).
    local postgres_container
    postgres_container=$(docker-compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps -q postgres)

    if [ -z "$postgres_container" ]; then
        print_error "PostgreSQL container not found"
        return 1
    fi

    # Restore database
    gunzip -c "$sql_dump" | docker exec -i "$postgres_container" psql -U postgres dartsdb

    if [ $? -eq 0 ]; then
        print_success "PostgreSQL database restored from dump"
    else
        print_error "Failed to restore PostgreSQL database"
        return 1
    fi

    # Stop postgres
    docker-compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down 2>/dev/null || true
}

restore_configuration() {
    local config_dir="${RESTORE_PATH}/config"

    if [ ! -d "$config_dir" ]; then
        print_warning "Configuration backup not found, skipping..."
        return
    fi

    print_step "Restoring configuration files..."

    local safety_backup="./docker-backups/pre-restore-config-$(date +%Y-%m-%d_%H-%M-%S)"

    # Restore WSO2 IS configuration
    if [ -f "${config_dir}/wso2is-deployment.toml" ]; then
        if [ -f "./wso2is-7-config/deployment.toml" ]; then
            mkdir -p "$safety_backup"
            cp "./wso2is-7-config/deployment.toml" "${safety_backup}/deployment.toml"
        fi
        mkdir -p ./wso2is-7-config
        cp "${config_dir}/wso2is-deployment.toml" ./wso2is-7-config/deployment.toml
        print_success "Restored WSO2 IS deployment.toml"
    fi

    # Restore .env file
    if [ -f "${config_dir}/.env" ]; then
        if [ -f "./.env" ]; then
            mkdir -p "$safety_backup"
            cp "./.env" "${safety_backup}/.env"
        fi
        cp "${config_dir}/.env" ./.env
        print_success "Restored .env file"
    fi

    # Restore nginx configuration
    if [ -d "${config_dir}/nginx" ]; then
        if [ -d "./nginx" ]; then
            mkdir -p "$safety_backup"
            cp -r "./nginx" "${safety_backup}/nginx"
        fi
        cp -r "${config_dir}/nginx" ./
        print_success "Restored nginx configuration"
    fi

    if [ -d "$safety_backup" ]; then
        print_warning "Pre-restore config files that were overwritten are saved at: ${safety_backup}"
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}                   ${GREEN}Restore Complete!${NC}                         ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Restored from:${NC} ${RESTORE_PATH}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Start the containers:"
    echo "     docker-compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} up -d"
    echo ""
    echo "  2. Verify services are healthy:"
    echo "     docker-compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} ps"
    echo ""
}

################################################################################
# Main Script
################################################################################

main() {
    print_header

    # Check backup exists
    check_backup_exists

    # Pre-flight checks
    check_docker

    echo ""
    echo -e "${YELLOW}⚠️  WARNING: This will restore data from backup${NC}"
    echo -e "${RED}Current data will be REPLACED!${NC}"
    echo ""
    echo -e "${YELLOW}Restore from:${NC} ${RESTORE_PATH}"
    echo ""

    if [ "$AUTO_CONFIRM" = false ]; then
        read -p "Are you sure you want to continue? (yes/no): " -r
        echo
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            print_error "Restore cancelled"
            exit 1
        fi
    else
        print_success "Auto-confirm enabled, proceeding with restore..."
    fi

    echo ""

    # Stop containers
    stop_containers

    # Restore volumes
    echo ""
    print_step "Restoring Docker volumes..."
    for volume in postgres_data rabbitmq_data wso2is_data wso2apim_data; do
        restore_volume "$volume"
    done

    # Restore PostgreSQL from SQL dump (recommended)
    echo ""
    restore_postgres_dump

    # Restore configuration files
    echo ""
    restore_configuration

    # Print summary
    print_summary
}

# Run main function
main
