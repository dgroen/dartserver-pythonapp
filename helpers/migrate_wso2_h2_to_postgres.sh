#!/usr/bin/env bash
# migrate_wso2_h2_to_postgres.sh
#
# Generic WSO2IS H2 -> PostgreSQL data migration tool (Phase 2 of
# doc/WSO2_PROD_MIGRATION_PLAN.md). Designed to be sourced-agnostic: it reads
# H2 data from a backup_docker_volumes.sh tarball (never a live volume) and
# loads it into an already schema-provisioned PostgreSQL instance, so the
# exact same script can run against the rehearsal stack now and against a
# real backup-production artifact later.
#
# Usage:
#   helpers/migrate_wso2_h2_to_postgres.sh <backup-dir> <wso2is-image> <pg-host> <pg-port> <pg-user> <pg-password>
#
# <backup-dir> is a backup_docker_volumes.sh output directory (contains
# wso2is_data.tar.gz). <pg-host>/<pg-port> must be reachable from this host.
set -euo pipefail

BACKUP_DIR="${1:?Usage: $0 <backup-dir> <wso2is-image> <pg-host> <pg-port> <pg-user> <pg-password>}"
WSO2IS_IMAGE="${2:?wso2is image required}"
PG_HOST="${3:?postgres host required}"
PG_PORT="${4:?postgres port required}"
PG_USER="${5:?postgres user required}"
PG_PASSWORD="${6:?postgres password required}"

H2_JAR_IN_IMAGE="/home/wso2carbon/wso2is-7.1.0/repository/components/plugins/h2-engine_2.2.224.wso2v2.jar"
WORKDIR=$(mktemp -d /tmp/wso2-h2-export.XXXXXX)

log() { echo "[migrate-h2-to-pg] $*"; }

# --- 1. Extract H2 files from the backup tarball (never touch a live volume) ---
log "Extracting wso2is_data.tar.gz from ${BACKUP_DIR}..."
mkdir -p "$WORKDIR/wso2is_data"
tar xzf "${BACKUP_DIR}/wso2is_data.tar.gz" -C "$WORKDIR/wso2is_data"

IDENTITY_DB=$(find "$WORKDIR/wso2is_data" -name "WSO2IDENTITY_DB.mv.db" | head -1)
SHARED_DB=$(find "$WORKDIR/wso2is_data" -name "WSO2SHARED_DB.mv.db" | head -1)
[ -n "$IDENTITY_DB" ] || { echo "WSO2IDENTITY_DB.mv.db not found in backup" >&2; exit 1; }
[ -n "$SHARED_DB" ] || { echo "WSO2SHARED_DB.mv.db not found in backup" >&2; exit 1; }
IDENTITY_DIR=$(dirname "$IDENTITY_DB")
SHARED_DIR=$(dirname "$SHARED_DB")

mkdir -p "$WORKDIR/csv/identity" "$WORKDIR/csv/shared"
# The wso2is image runs as uid 802 (wso2carbon), not this host user, so both
# the extracted H2 files and the CSV output dirs need to be world-writable.
chmod -R 777 "$WORKDIR/wso2is_data" "$WORKDIR/csv"

# --- 2. Export every table from each H2 database to CSV, generically ---
# BLOB/CLOB columns are hex-encoded ('\x' + RAWTOHEX(...)) rather than
# selected raw: H2's default CSVWRITE stringifies binary content unsafely
# (found during rehearsal - a table with real BLOB data failed to load with
# "unquoted carriage return found in data"). The '\x' hex form is PostgreSQL's
# native bytea text representation, so the loader needs no special handling
# for these columns - a plain \copy parses it correctly.
build_export_script() {
  local columns_csv="$1" out_sql="$2"
  local prev_table="" collist="" table col type part
  : > "$out_sql"
  while IFS=',' read -r table col type; do
    table=$(echo "$table" | tr -d '"')
    col=$(echo "$col" | tr -d '"')
    type=$(echo "$type" | tr -d '"')
    [ "$table" = "TABLE_NAME" ] && continue
    [ -z "$table" ] && continue
    if [ "$table" != "$prev_table" ]; then
      if [ -n "$prev_table" ]; then
        echo "CALL CSVWRITE('/export/${prev_table}.csv', 'SELECT ${collist} FROM \"${prev_table}\"');" >> "$out_sql"
      fi
      collist=""
      prev_table="$table"
    fi
    case "$type" in
      BLOB|CLOB|"BINARY LARGE OBJECT"|"CHARACTER LARGE OBJECT")
        # Doubled quotes: this text is itself embedded inside CSVWRITE's
        # single-quoted SQL-string argument, so a literal ' must be '' there.
        part="CASE WHEN \"${col}\" IS NULL THEN NULL ELSE ''\\x''||RAWTOHEX(\"${col}\") END AS \"${col}\""
        ;;
      *)
        part="\"${col}\""
        ;;
    esac
    [ -z "$collist" ] && collist="$part" || collist="${collist}, ${part}"
  done < "$columns_csv"
  if [ -n "$prev_table" ]; then
    echo "CALL CSVWRITE('/export/${prev_table}.csv', 'SELECT ${collist} FROM \"${prev_table}\"');" >> "$out_sql"
  fi
}

export_h2_db() {
  local db_dir="$1" db_name="$2" out_csv_dir="$3"
  local url="jdbc:h2:/h2data/${db_name};IFEXISTS=TRUE;DB_CLOSE_ON_EXIT=TRUE"

  log "Reading ${db_name} schema..."
  docker run --rm \
    -v "${db_dir}:/h2data" \
    -v "${out_csv_dir}:/export" \
    --entrypoint /bin/bash \
    "$WSO2IS_IMAGE" -lc "java -cp ${H2_JAR_IN_IMAGE} org.h2.tools.Shell -url '${url}' -user wso2carbon -password wso2carbon -sql \"CALL CSVWRITE('/export/_columns.csv', 'SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=''PUBLIC'' ORDER BY TABLE_NAME, ORDINAL_POSITION')\""

  build_export_script "${out_csv_dir}/_columns.csv" "${out_csv_dir}/_export.sql"

  log "Exporting ${db_name} tables..."
  docker run --rm \
    -v "${db_dir}:/h2data" \
    -v "${out_csv_dir}:/export" \
    --entrypoint /bin/bash \
    "$WSO2IS_IMAGE" -lc "java -cp ${H2_JAR_IN_IMAGE} org.h2.tools.RunScript -url '${url}' -user wso2carbon -password wso2carbon -script /export/_export.sql"
}

export_h2_db "$IDENTITY_DIR" "WSO2IDENTITY_DB" "$WORKDIR/csv/identity"
export_h2_db "$SHARED_DIR" "WSO2SHARED_DB" "$WORKDIR/csv/shared"

# --- 3. Load CSVs into PostgreSQL ---
# One psql session per database (avoids the container-creation churn found
# during rehearsal to destabilize the target postgres server). Each table
# loads into an unconstrained TEMP staging table first, then
# INSERT ... ON CONFLICT DO NOTHING into the real table - WSO2's Postgres DDL
# inserts its own baseline seed rows (e.g. IDN_BASE_TABLE, UM_ORG) which
# collide with H2's identical seed rows; a plain \copy would abort the whole
# table's load on the first such collision and silently drop every row after
# it, not just the duplicate.
load_pg_db() {
  local csv_dir="$1" pg_db="$2"
  log "Loading tables into PostgreSQL database ${pg_db}..."
  local load_script="${csv_dir}/_load.sql"
  echo "SET session_replication_role = replica;" > "$load_script"
  local table_count=0
  for csv in "$csv_dir"/*.csv; do
    tbl=$(basename "$csv" .csv)
    case "$tbl" in _columns|_export) continue ;; esac
    rows=$(($(wc -l < "$csv") - 1))
    [ "$rows" -le 0 ] && continue
    {
      echo "DROP TABLE IF EXISTS _staging;"
      echo "CREATE TEMP TABLE _staging (LIKE ${tbl} INCLUDING DEFAULTS);"
      echo "\\copy _staging FROM '/csv/$(basename "$csv")' WITH (FORMAT csv, HEADER true);"
      echo "INSERT INTO ${tbl} SELECT * FROM _staging ON CONFLICT DO NOTHING;"
    } >> "$load_script"
    table_count=$((table_count + 1))
  done
  log "  loading ${table_count} non-empty tables..."
  PGPASSWORD="$PG_PASSWORD" docker run --rm -i \
    -e PGPASSWORD="$PG_PASSWORD" \
    --network host \
    -v "${csv_dir}:/csv:ro" \
    postgres:16-alpine \
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$pg_db" -v ON_ERROR_STOP=0 -f "/csv/_load.sql"
}

load_pg_db "$WORKDIR/csv/identity" wso2is_identity
load_pg_db "$WORKDIR/csv/shared" wso2is_shared

# --- 4. Resync sequences backing INTEGER DEFAULT NEXTVAL(...) columns ---
resync_sequences() {
  local pg_db="$1"
  log "Resyncing sequences in ${pg_db}..."
  PGPASSWORD="$PG_PASSWORD" docker run --rm -i \
    -e PGPASSWORD="$PG_PASSWORD" \
    --network host \
    postgres:16-alpine \
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$pg_db" -v ON_ERROR_STOP=1 -c "
      DO \$\$
      DECLARE
        r RECORD;
        seq_name TEXT;
        max_val BIGINT;
      BEGIN
        FOR r IN
          SELECT table_name, column_name, column_default
          FROM information_schema.columns
          WHERE column_default LIKE 'nextval(%'
        LOOP
          seq_name := substring(r.column_default FROM E'nextval\\\\(''([^'']+)''');
          EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', r.column_name, r.table_name) INTO max_val;
          IF max_val > 0 THEN
            EXECUTE format('SELECT setval(%L, %s)', seq_name, max_val);
          END IF;
        END LOOP;
      END \$\$;
    "
}

resync_sequences wso2is_identity
resync_sequences wso2is_shared

log "Migration complete. CSV export kept at: ${WORKDIR} (not auto-deleted - remove manually when done)."
log "Row counts by table are in the output above; compare against the source H2 export for parity."
echo "WORKDIR=${WORKDIR}"
