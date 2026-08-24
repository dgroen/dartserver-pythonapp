#!/usr/bin/env bash
# run_wso2_migration_rehearsal.sh
#
# Orchestrates a full, isolated rehearsal of the WSO2IS H2 -> PostgreSQL
# migration (doc/WSO2_PROD_MIGRATION_PLAN.md, Phase 2/6). Stands up a
# throwaway H2-backed WSO2IS, seeds it with representative data using the
# existing test-environment provisioning scripts, backs it up with the same
# helpers/backup_docker_volumes.sh mechanism production uses, migrates the
# backup into a fresh PostgreSQL-backed WSO2IS via
# helpers/migrate_wso2_h2_to_postgres.sh, and starts the migrated target.
#
# Does not touch the running darts-* dev stack, its volumes, or production.
#
# Usage: helpers/run_wso2_migration_rehearsal.sh [up|seed|freeze-backup|migrate|start-target|all|down]
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT_NAME="migration-rehearsal"
COMPOSE_FILE="docker-compose-migration-rehearsal.yml"
COMPOSE=(docker-compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE")
SOURCE_URL="https://localhost:19443"
TARGET_URL="https://localhost:29443"
STATE_DIR="/tmp/wso2-migration-rehearsal"
mkdir -p "$STATE_DIR"

log() { echo "[rehearsal] $*"; }

wait_healthy() {
  local service="$1" timeout_s="${2:-300}"
  log "Waiting for ${service} to be healthy (timeout ${timeout_s}s)..."
  local waited=0
  while true; do
    local cid status
    cid=$("${COMPOSE[@]}" ps -q "$service")
    status=$(docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo "starting")
    [ "$status" = "healthy" ] && { log "${service} is healthy."; return 0; }
    waited=$((waited + 5))
    if [ "$waited" -ge "$timeout_s" ]; then
      log "ERROR: ${service} did not become healthy within ${timeout_s}s (status: ${status})"
      "${COMPOSE[@]}" logs --tail 100 "$service"
      exit 1
    fi
    sleep 5
  done
}

cmd_up_source() {
  log "Starting wso2is-source (H2)..."
  "${COMPOSE[@]}" up -d wso2is-source
  wait_healthy wso2is-source
}

cmd_seed() {
  log "Seeding representative data into wso2is-source at ${SOURCE_URL}..."
  python3 helpers/register_wso2_test_client.py --json --ws-url "$SOURCE_URL" --admin-user admin --admin-pass admin > "$STATE_DIR/client.json"
  CLIENT_ID=$(python3 -c "import json;print(json.load(open('$STATE_DIR/client.json'))['client_id'])")
  echo "$CLIENT_ID" > "$STATE_DIR/client_id.txt"
  export WSO2_CLIENT_ID="$CLIENT_ID"

  python3 helpers/configure_wso2_redirects.py --ws-url "$SOURCE_URL" --admin-user admin --admin-pass admin

  python3 helpers/test_wso2_provision_user.py --ws-url "$SOURCE_URL" --admin-user admin --admin-pass admin \
    --username player --password 'Playerpass1!' --role player --display-name Player
  python3 helpers/test_wso2_provision_user.py --ws-url "$SOURCE_URL" --admin-user admin --admin-pass admin \
    --username master --password 'Masterpass1!' --role gamemaster --display-name Master
  python3 helpers/test_wso2_provision_user.py --ws-url "$SOURCE_URL" --admin-user admin --admin-pass admin \
    --username Dennis --password 'DwvDG=8k' --role admin --display-name Dennis

  # Non-fatal: this script has a pre-existing redirect-URI-format quirk against
  # the DCR-registered client above; the OAuth client from register_wso2_test_client.py
  # is already sufficient representative data for the rehearsal's parity checks.
  python3 helpers/configure_wso2_gateway_client.py --json --ws-url "$SOURCE_URL" --admin-user admin --admin-pass admin > "$STATE_DIR/gateway.json" \
    || log "WARNING: gateway client configuration failed (non-fatal for rehearsal purposes)"

  log "Seed data recorded at ${STATE_DIR} (client.json, client_id.txt) for later verification."
}

cmd_freeze_backup() {
  log "Stopping wso2is-source to flush H2 files (freeze writes)..."
  "${COMPOSE[@]}" stop wso2is-source

  log "Backing up migration-rehearsal_wso2is_data via helpers/backup_docker_volumes.sh..."
  PROJECT_NAME="$PROJECT_NAME" bash helpers/backup_docker_volumes.sh -y

  local latest_backup
  latest_backup=$(ls -td ./docker-backups/*/ | head -1)
  echo "$latest_backup" > "$STATE_DIR/backup_path.txt"
  log "Backup created at ${latest_backup}"
}

cmd_migrate() {
  log "Starting postgres target and running data migration..."
  "${COMPOSE[@]}" up -d postgres
  wait_healthy postgres 120

  local backup_dir
  backup_dir=$(cat "$STATE_DIR/backup_path.txt")
  bash helpers/migrate_wso2_h2_to_postgres.sh "$backup_dir" wso2/wso2is:7.1.0 localhost 15432 postgres postgres \
    | tee "$STATE_DIR/migrate.log"
  grep '^WORKDIR=' "$STATE_DIR/migrate.log" | tail -1 | cut -d= -f2- > "$STATE_DIR/h2_export_workdir.txt"
}

cmd_start_target() {
  log "Starting wso2is-target (PostgreSQL) at ${TARGET_URL}..."
  "${COMPOSE[@]}" up -d wso2is-target
  wait_healthy wso2is-target
}

cmd_down() {
  log "Tearing down rehearsal stack and volumes..."
  "${COMPOSE[@]}" down -v
}

case "${1:-all}" in
  up) cmd_up_source ;;
  seed) cmd_seed ;;
  freeze-backup) cmd_freeze_backup ;;
  migrate) cmd_migrate ;;
  start-target) cmd_start_target ;;
  down) cmd_down ;;
  all)
    cmd_up_source
    cmd_seed
    cmd_freeze_backup
    cmd_migrate
    cmd_start_target
    log "Rehearsal migration complete. Target console: ${TARGET_URL}/console (admin/admin)."
    log "Run helpers/verify_wso2_migration_parity.sh next."
    ;;
  *)
    echo "Usage: $0 [up|seed|freeze-backup|migrate|start-target|all|down]" >&2
    exit 1
    ;;
esac
