#!/usr/bin/env bash
# Refresh dartsdb-dump.sql from the currently running darts-postgres container.
# This snapshot is loaded automatically into a fresh dartsdb on first boot via
# docker-compose-localhost.yml's postgres init scripts (only applies to an
# empty postgres_data volume - it has no effect on an already-initialized DB).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_FILE="$REPO_ROOT/data/postgres/dartsdb-dump.sql"
CONTAINER="${1:-darts-postgres}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' is not running" >&2
  exit 1
fi

echo "Dumping dartsdb from container '$CONTAINER' to $OUT_FILE ..."
docker exec "$CONTAINER" pg_dump -U postgres --no-owner --no-privileges --clean --if-exists dartsdb > "$OUT_FILE"

echo "Done ($(wc -l < "$OUT_FILE") lines, $(du -h "$OUT_FILE" | cut -f1))."
echo "This will be used the next time postgres_data is initialized from empty."
