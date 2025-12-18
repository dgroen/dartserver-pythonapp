#!/bin/bash

################################################################################
# Docker Volumes Backup Script
#
# This script backs up all Docker volumes used by the application:
# - postgres_data (PostgreSQL database)
# - rabbitmq_data (RabbitMQ message broker)
# - wso2is_data (WSO2 Identity Server)
# - wso2apim_data (WSO2 API Manager)
#
# Backups are stored in: ./docker-backups/YYYY-MM-DD_HH-MM-SS/
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
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
PROJECT_NAME="dartserver-pythonapp"
AUTO_CONFIRM=false

# Volume names (from docker-compose files)
VOLUMES=(
    "postgres_data"
    "rabbitmq_data"
    "wso2is_data"
    "wso2apim_data"
)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -y, --yes    Automatically confirm backup without prompting"
            echo "  -h, --help   Show this help message"
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
    echo -e "${BLUE}║${NC}          ${GREEN}Docker Volumes Backup Script${NC}                      ${BLUE}║${NC}"
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

check_docker() {
    print_step "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    print_success "Docker is installed"
}

check_volumes_exist() {
    print_step "Checking if volumes exist..."
    local missing_volumes=()

    for volume in "${VOLUMES[@]}"; do
        local full_volume_name="${PROJECT_NAME}_${volume}"
        if ! docker volume inspect "$full_volume_name" &> /dev/null; then
            missing_volumes+=("$full_volume_name")
        fi
    done

    if [ ${#missing_volumes[@]} -gt 0 ]; then
        print_warning "The following volumes do not exist:"
        for vol in "${missing_volumes[@]}"; do
            echo "  - $vol"
        done
        echo ""
        read -p "Continue with backup of existing volumes? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Backup cancelled"
            exit 1
        fi
    else
        print_success "All volumes exist"
    fi
}

create_backup_directory() {
    print_step "Creating backup directory: ${BACKUP_PATH}"
    mkdir -p "${BACKUP_PATH}"
    print_success "Backup directory created"
}

get_volume_size() {
    local volume_name=$1
    docker run --rm -v "${volume_name}:/data" alpine du -sh /data 2>/dev/null | awk '{print $1}' || echo "unknown"
}

backup_postgres_database() {
    print_step "Backing up PostgreSQL database using pg_dump..."

    # Find postgres container (handle different naming patterns)
    local postgres_container=$(docker ps --format '{{.Names}}' | grep -E "postgres|darts-postgres" | head -n 1)

    if [ -z "$postgres_container" ]; then
        print_warning "PostgreSQL container is not running. Skipping pg_dump backup."
        print_warning "Volume backup will still be performed."
        return
    fi

    print_step "Found PostgreSQL container: ${postgres_container}"

    local sql_backup_file="${BACKUP_PATH}/postgres_dump.sql"
    local sql_backup_gz="${BACKUP_PATH}/postgres_dump.sql.gz"

    # Create SQL dump
    docker exec "$postgres_container" pg_dump -U postgres dartsdb > "${sql_backup_file}" 2>/dev/null

    if [ $? -eq 0 ]; then
        # Compress the SQL dump
        gzip "${sql_backup_file}"
        local backup_size=$(du -sh "${sql_backup_gz}" | awk '{print $1}')
        print_success "PostgreSQL database dumped → postgres_dump.sql.gz (${backup_size})"
    else
        print_warning "Failed to create PostgreSQL dump"
        # Clean up failed dump file if it exists
        [ -f "${sql_backup_file}" ] && rm -f "${sql_backup_file}"
    fi
}

backup_volume() {
    local volume=$1
    local full_volume_name="${PROJECT_NAME}_${volume}"

    # Check if volume exists
    if ! docker volume inspect "$full_volume_name" &> /dev/null; then
        print_warning "Volume ${full_volume_name} does not exist, skipping..."
        return
    fi

    local backup_file="${BACKUP_PATH}/${volume}.tar.gz"
    local volume_size=$(get_volume_size "$full_volume_name")

    print_step "Backing up ${full_volume_name} (size: ${volume_size})..."

    # Create backup using a temporary container
    docker run --rm \
        -v "${full_volume_name}:/data:ro" \
        -v "$(pwd)/${BACKUP_PATH}:/backup" \
        alpine \
        tar czf "/backup/${volume}.tar.gz" -C /data .

    if [ $? -eq 0 ]; then
        local backup_size=$(du -sh "${backup_file}" | awk '{print $1}')
        print_success "Backed up ${volume} → ${backup_file} (${backup_size})"
    else
        print_error "Failed to backup ${volume}"
        return 1
    fi
}

create_backup_manifest() {
    print_step "Creating backup manifest..."

    local manifest_file="${BACKUP_PATH}/BACKUP_MANIFEST.txt"

    cat > "$manifest_file" << EOF
================================================================================
Docker Volumes Backup Manifest
================================================================================

Backup Date: $(date)
Backup Location: ${BACKUP_PATH}
Project: ${PROJECT_NAME}

================================================================================
Database Backups:
================================================================================

EOF

    # Check for PostgreSQL dump
    if [ -f "${BACKUP_PATH}/postgres_dump.sql.gz" ]; then
        local size=$(du -sh "${BACKUP_PATH}/postgres_dump.sql.gz" | awk '{print $1}')
        echo "✓ PostgreSQL Database (pg_dump)" >> "$manifest_file"
        echo "  File: postgres_dump.sql.gz" >> "$manifest_file"
        echo "  Size: ${size}" >> "$manifest_file"
        echo "  Database: dartsdb" >> "$manifest_file"
        echo "" >> "$manifest_file"
    else
        echo "✗ PostgreSQL Database (pg_dump not available)" >> "$manifest_file"
        echo "" >> "$manifest_file"
    fi

    cat >> "$manifest_file" << EOF
================================================================================
Volumes Backed Up:
================================================================================

EOF

    for volume in "${VOLUMES[@]}"; do
        local full_volume_name="${PROJECT_NAME}_${volume}"
        if docker volume inspect "$full_volume_name" &> /dev/null; then
            local backup_file="${volume}.tar.gz"
            if [ -f "${BACKUP_PATH}/${backup_file}" ]; then
                local size=$(du -sh "${BACKUP_PATH}/${backup_file}" | awk '{print $1}')
                echo "✓ ${volume}" >> "$manifest_file"
                echo "  File: ${backup_file}" >> "$manifest_file"
                echo "  Size: ${size}" >> "$manifest_file"
                echo "" >> "$manifest_file"
            fi
        else
            echo "✗ ${volume} (volume does not exist)" >> "$manifest_file"
            echo "" >> "$manifest_file"
        fi
    done

    cat >> "$manifest_file" << EOF
================================================================================
Restore Instructions:
================================================================================

OPTION 1: Restore PostgreSQL Database from SQL Dump (RECOMMENDED)
------------------------------------------------------------------

1. Stop the containers:
   docker-compose -f docker-compose.yml down
   # or
   docker-compose -f docker-compose-wso2.yml down

2. Start only PostgreSQL:
   docker-compose -f docker-compose.yml up -d postgres

3. Restore the database:
   gunzip -c ${BACKUP_PATH}/postgres_dump.sql.gz | \\
     docker exec -i darts-postgres psql -U postgres dartsdb

4. Start all containers:
   docker-compose -f docker-compose.yml up -d
   # or
   docker-compose -f docker-compose-wso2.yml up -d

OPTION 2: Restore Docker Volume from Backup
--------------------------------------------

To restore a volume from backup:

1. Stop the containers:
   docker-compose -f docker-compose.yml down
   # or
   docker-compose -f docker-compose-wso2.yml down

2. Remove the old volume (CAUTION: This deletes data!):
   docker volume rm ${PROJECT_NAME}_<volume_name>

3. Create a new volume:
   docker volume create ${PROJECT_NAME}_<volume_name>

4. Restore from backup:
   docker run --rm \\
     -v ${PROJECT_NAME}_<volume_name>:/data \\
     -v \$(pwd)/${BACKUP_PATH}:/backup \\
     alpine \\
     tar xzf /backup/<volume_name>.tar.gz -C /data

5. Start the containers:
   docker-compose -f docker-compose.yml up -d
   # or
   docker-compose -f docker-compose-wso2.yml up -d

================================================================================
Example - Restore PostgreSQL Volume:
================================================================================

docker-compose -f docker-compose.yml down
docker volume rm ${PROJECT_NAME}_postgres_data
docker volume create ${PROJECT_NAME}_postgres_data
docker run --rm \\
  -v ${PROJECT_NAME}_postgres_data:/data \\
  -v \$(pwd)/${BACKUP_PATH}:/backup \\
  alpine \\
  tar xzf /backup/postgres_data.tar.gz -C /data
docker-compose -f docker-compose.yml up -d

================================================================================
Example - Restore WSO2 IS Volume:
================================================================================

docker-compose -f docker-compose-wso2.yml down
docker volume rm ${PROJECT_NAME}_wso2is_data
docker volume create ${PROJECT_NAME}_wso2is_data
docker run --rm \\
  -v ${PROJECT_NAME}_wso2is_data:/data \\
  -v \$(pwd)/${BACKUP_PATH}:/backup \\
  alpine \\
  tar xzf /backup/wso2is_data.tar.gz -C /data
docker-compose -f docker-compose-wso2.yml up -d

================================================================================
EOF

    print_success "Backup manifest created: ${manifest_file}"
}

backup_configuration_files() {
    print_step "Backing up configuration files..."

    local config_backup_dir="${BACKUP_PATH}/config"
    mkdir -p "$config_backup_dir"

    # Backup WSO2 IS configuration
    if [ -f "./wso2is-config/deployment.toml" ]; then
        cp "./wso2is-config/deployment.toml" "${config_backup_dir}/wso2is-deployment.toml"
        print_success "Backed up WSO2 IS deployment.toml"
    fi

    # Backup docker-compose files
    if [ -f "./docker-compose-wso2.yml" ]; then
        cp "./docker-compose-wso2.yml" "${config_backup_dir}/docker-compose-wso2.yml"
        print_success "Backed up docker-compose-wso2.yml"
    fi

    # Backup .env file if it exists
    if [ -f "./.env" ]; then
        cp "./.env" "${config_backup_dir}/.env"
        print_success "Backed up .env file"
    fi

    # Backup nginx configuration
    if [ -d "./nginx" ]; then
        cp -r "./nginx" "${config_backup_dir}/"
        print_success "Backed up nginx configuration"
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}                    ${GREEN}Backup Complete!${NC}                         ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Backup Location:${NC} ${BACKUP_PATH}"
    echo ""
    echo -e "${YELLOW}Backed up files:${NC}"
    ls -lh "${BACKUP_PATH}" | grep -v "^total" | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
    echo -e "${YELLOW}Total backup size:${NC}"
    du -sh "${BACKUP_PATH}" | awk '{print "  " $1}'
    echo ""
    echo -e "${BLUE}To view restore instructions:${NC}"
    echo "  cat ${BACKUP_PATH}/BACKUP_MANIFEST.txt"
    echo ""
}

################################################################################
# Main Script
################################################################################

main() {
    print_header

    # Pre-flight checks
    check_docker
    check_volumes_exist

    echo ""
    echo -e "${YELLOW}This will backup the following volumes:${NC}"
    for volume in "${VOLUMES[@]}"; do
        local full_volume_name="${PROJECT_NAME}_${volume}"
        if docker volume inspect "$full_volume_name" &> /dev/null; then
            local size=$(get_volume_size "$full_volume_name")
            echo "  - ${full_volume_name} (${size})"
        fi
    done
    echo ""
    echo -e "${YELLOW}Backup will be saved to:${NC} ${BACKUP_PATH}"
    echo ""

    if [ "$AUTO_CONFIRM" = false ]; then
        read -p "Continue with backup? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Backup cancelled"
            exit 1
        fi
    else
        print_success "Auto-confirm enabled, proceeding with backup..."
    fi

    echo ""

    # Create backup directory
    create_backup_directory

    # Backup PostgreSQL database using pg_dump (if container is running)
    echo ""
    backup_postgres_database

    # Backup each volume
    echo ""
    for volume in "${VOLUMES[@]}"; do
        backup_volume "$volume"
    done

    # Backup configuration files
    echo ""
    backup_configuration_files

    # Create manifest
    echo ""
    create_backup_manifest

    # Print summary
    print_summary
}

# Run main function
main
