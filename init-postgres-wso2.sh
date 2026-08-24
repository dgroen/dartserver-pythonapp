#!/bin/sh
# Initialize PostgreSQL databases for WSO2 Identity Server / API Manager.
# Runs automatically via docker-entrypoint-initdb.d on first container start
# (empty data directory only).
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE wso2is_identity WITH ENCODING 'UTF8';
    CREATE DATABASE wso2is_shared WITH ENCODING 'UTF8';
    CREATE DATABASE wso2apim_shared WITH ENCODING 'UTF8';
EOSQL

# Load the official WSO2 PostgreSQL DDL, which covers tables WSO2IS's own
# JDBC auto-provisioning does not create (e.g. the CM_* consent-management
# tables - confirmed missing from an auto-provisioned instance during the
# WSO2 H2->PostgreSQL migration work). Optional: docker-compose-localhost.yml
# (local dev) doesn't mount these and relies on auto-provisioning alone;
# docker-compose-wso2.yml (test/production) does mount them, under a
# subdirectory so postgres's own init-script scanner doesn't also try to run
# them directly against the default database.
SCHEMA_DIR="/docker-entrypoint-initdb.d/wso2-schema"
if [ -f "${SCHEMA_DIR}/postgresql-shared.sql" ]; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname wso2is_shared -f "${SCHEMA_DIR}/postgresql-shared.sql"
else
    echo "init-postgres-wso2: ${SCHEMA_DIR}/postgresql-shared.sql not mounted, skipping (relying on WSO2 auto-provisioning)"
fi
if [ -f "${SCHEMA_DIR}/postgresql-identity.sql" ]; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname wso2is_identity -f "${SCHEMA_DIR}/postgresql-identity.sql"
else
    echo "init-postgres-wso2: ${SCHEMA_DIR}/postgresql-identity.sql not mounted, skipping (relying on WSO2 auto-provisioning)"
fi
