#!/usr/bin/env bash
# Rebuild the database by downgrading to base and upgrading to head.
# If downgrade fails, drops and recreates the public schema before retrying.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Load .env file if it exists
if [ -f .env ]; then
  while IFS='=' read -r key value; do
    if [[ $key =~ ^[[:space:]]*# ]] || [[ -z $key ]]; then continue; fi
    # Remove inline comments and trailing spaces
    value="${value%%#*}"
    value="${value%%[[:space:]]*}"
    export "$key=$value"
  done < .env
fi

usage() {
  cat <<'EOF'
Usage: helpers/rebuild_database.sh [--yes] [--dry-run] [--database-url URL]

Options:
  --yes             Skip the confirmation prompt.
  --dry-run         Show the actions without executing them.
  --database-url    Database URL to use. Defaults to DATABASE_URL from .env
                    or postgresql://postgres:postgres@localhost:5432/dartsdb
EOF
}

AUTO_YES=false
DRY_RUN=false
DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/dartsdb}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes)
      AUTO_YES=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --database-url)
      DB_URL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic command not found. Install dependencies (pip install -r requirements.txt)." >&2
  exit 1
fi

echo "Project root: $PROJECT_ROOT"
echo "Database URL: $DB_URL"
echo "Dry run:      $DRY_RUN"

if ! $AUTO_YES; then
  read -r -p "This will rebuild the database schema. Continue? [y/N] " reply
  case "$reply" in
    [yY][eE][sS]|[yY]) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

export DATABASE_URL="$DB_URL"

# Function to drop and recreate public schema
drop_schema() {
  echo "Dropping and recreating public schema..."
  if $DRY_RUN; then
    echo "(dry-run) Would execute: DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  else
    python3 - <<'PY'
import os
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
engine = create_engine(url, isolation_level="AUTOCOMMIT")
with engine.begin() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
print("✓ public schema reset")
PY
  fi
}

# Attempt downgrade to base
echo "Downgrading to base..."
if $DRY_RUN; then
  echo "(dry-run) alembic downgrade base"
elif ! alembic downgrade base; then
  echo "Downgrade failed, attempting schema reset..."
  drop_schema
  echo "Retrying downgrade to base..."
  alembic downgrade base
fi

# Attempt upgrade to head
echo "Upgrading to head..."
if $DRY_RUN; then
  echo "(dry-run) alembic upgrade head"
elif ! alembic upgrade head; then
  echo "Upgrade failed, attempting full schema reset..."
  drop_schema
  echo "Retrying downgrade to base after reset..."
  alembic downgrade base
  echo "Retrying upgrade to head..."
  alembic upgrade head
fi

echo "Current migration head(s):"
if $DRY_RUN; then
  echo "(dry-run) alembic current"
else
  alembic current
fi

echo "Done."
