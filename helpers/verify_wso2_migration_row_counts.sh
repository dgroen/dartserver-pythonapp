#!/usr/bin/env bash
# verify_wso2_migration_row_counts.sh
#
# Row-count parity check only (H2 CSV export vs loaded PostgreSQL tables) -
# no login/token/functional checks, so this is safe to run against a real
# production data migration where no synthetic seeded credentials exist.
# Prints only table names and counts, never row content.
#
# Usage:
#   helpers/verify_wso2_migration_row_counts.sh <h2-export-workdir> <pg-host> <pg-port> <pg-user> <pg-password>
set -uo pipefail

WORKDIR="${1:?Usage: $0 <h2-export-workdir> <pg-host> <pg-port> <pg-user> <pg-password>}"
PG_HOST="${2:?postgres host required}"
PG_PORT="${3:?postgres port required}"
PG_USER="${4:?postgres user required}"
PG_PASSWORD="${5:?postgres password required}"

FAIL=0
log() { echo "[verify-row-counts] $*"; }
pass() { echo "[verify-row-counts] PASS: $*"; }
fail() { echo "[verify-row-counts] FAIL: $*"; FAIL=1; }

if [ ! -d "$WORKDIR" ]; then
  fail "H2 export workdir not found: ${WORKDIR}"
  exit 1
fi

for pair in "identity:wso2is_identity" "shared:wso2is_shared"; do
  csv_subdir="${pair%%:*}"
  pg_db="${pair##*:}"
  declare -A h2_counts=()
  query=""
  for csv in "$WORKDIR/csv/${csv_subdir}"/*.csv; do
    tbl=$(basename "$csv" .csv)
    case "$tbl" in _columns) continue ;; esac
    h2_rows=$(($(wc -l < "$csv") - 1))
    [ "$h2_rows" -lt 0 ] && h2_rows=0
    h2_counts["$tbl"]="$h2_rows"
    clause="SELECT '${tbl}' AS t, (SELECT COUNT(*) FROM ${tbl}) AS n"
    [ -z "$query" ] && query="$clause" || query="${query} UNION ALL ${clause}"
  done
  pg_output=$(PGPASSWORD="$PG_PASSWORD" docker run --rm -e PGPASSWORD="$PG_PASSWORD" --network host postgres:16-alpine \
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$pg_db" -t -A -F'|' -c "$query" 2>&1)
  declare -A pg_counts=()
  while IFS='|' read -r t n; do
    [ -n "$t" ] && pg_counts["$t"]="$n"
  done <<< "$pg_output"
  mismatches=0
  for tbl in "${!h2_counts[@]}"; do
    h2_rows="${h2_counts[$tbl]}"
    pg_rows="${pg_counts[$tbl]:-}"
    if [ -z "$pg_rows" ]; then
      fail "${pg_db}.${tbl}: could not query PostgreSQL row count"
      mismatches=$((mismatches + 1))
    elif [ "$h2_rows" != "$pg_rows" ]; then
      fail "${pg_db}.${tbl}: H2 had ${h2_rows} rows, PostgreSQL has ${pg_rows}"
      mismatches=$((mismatches + 1))
    fi
  done
  pass "${pg_db}: ${#h2_counts[@]} tables checked, ${mismatches} mismatches"
  unset h2_counts pg_counts
done

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "[verify-row-counts] ALL TABLES MATCH"
else
  echo "[verify-row-counts] MISMATCHES FOUND - see FAIL lines above"
fi
exit "$FAIL"
