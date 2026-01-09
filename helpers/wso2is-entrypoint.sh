#!/bin/bash
set -euo pipefail

ORIGINAL_ENTRYPOINT="/home/wso2carbon/docker-entrypoint.sh"

DB_HOST="${WSO2_DB_HOST:-postgres}"
DB_PORT="${WSO2_DB_PORT:-5432}"
DB_USER="${WSO2_DB_USER:-postgres}"
DB_PASSWORD="${WSO2_DB_PASSWORD:-postgres}"
IDENTITY_DB="${WSO2_IDENTITY_DB:-wso2is_identity}"
SHARED_DB="${WSO2_SHARED_DB:-wso2is_shared}"

SHARED_SCRIPT="/home/wso2carbon/wso2is-7.1.0/dbscripts/postgresql.sql"
IDENTITY_SCRIPT="/home/wso2carbon/wso2is-7.1.0/dbscripts/identity/postgresql.sql"
CONSENT_SCRIPT="/home/wso2carbon/wso2is-7.1.0/dbscripts/consent/postgresql.sql"

install_psql() {
    if command -v psql >/dev/null 2>&1; then
        return
    fi
    if [[ "$(id -u)" -ne 0 ]]; then
        echo "ERROR: PostgreSQL client not found and script is not running as root; cannot install psql."
        exit 1
    fi
    echo "Installing PostgreSQL client tools inside WSO2 IS container..."
    mkdir -p /var/lib/apt/lists/partial
    chmod 755 /var/lib/apt/lists /var/lib/apt/lists/partial
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql-client > /dev/null
    rm -rf /var/lib/apt/lists/*
}

wait_for_db() {
    echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    local retries=30
    local count=0
    until PGPASSWORD="${DB_PASSWORD}" pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" > /dev/null 2>&1; do
        count=$((count + 1))
        if [[ ${count} -ge ${retries} ]]; then
            echo "ERROR: PostgreSQL is not reachable after ${retries} attempts"
            exit 1
        fi
        sleep 2
    done
    echo "✓ PostgreSQL is reachable"
}

ensure_database() {
    local db_name="$1"
    local exists
    exists=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -tAc "SELECT 1 FROM pg_database WHERE datname='${db_name}'")
    if [[ "${exists}" != "1" ]]; then
        echo "Creating database ${db_name}..."
        PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${db_name}\""
    fi
}

apply_schema_if_missing() {
    local db_name="$1"
    local script_path="$2"
    local sentinel_table="$3"

    if [[ ! -f "${script_path}" ]]; then
        echo "ERROR: Schema script not found: ${script_path}"
        exit 1
    fi

    local table_exists
    table_exists=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${db_name}" -tAc "SELECT 1 FROM pg_class WHERE relname='${sentinel_table}' AND relkind='r'")

    if [[ "${table_exists}" == "1" ]]; then
        echo "✓ ${db_name} already has table ${sentinel_table}; skipping ${script_path}"
    else
        echo "Applying schema ${script_path} to ${db_name}..."
        PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${db_name}" -v ON_ERROR_STOP=1 -f "${script_path}"
    fi
}

main() {
    install_psql
    wait_for_db

    ensure_database "${SHARED_DB}"
    ensure_database "${IDENTITY_DB}"

    apply_schema_if_missing "${SHARED_DB}" "${SHARED_SCRIPT}" "reg_cluster_lock"
    apply_schema_if_missing "${IDENTITY_DB}" "${IDENTITY_SCRIPT}" "idn_base_table"
    apply_schema_if_missing "${IDENTITY_DB}" "${CONSENT_SCRIPT}" "cm_receipt"

    echo "Starting WSO2 Identity Server..."
    if command -v su >/dev/null 2>&1; then
        exec su -s /bin/sh wso2carbon -c "\"${ORIGINAL_ENTRYPOINT}\" $*"
    else
        exec "${ORIGINAL_ENTRYPOINT}" "$@"
    fi
}

main "$@"
