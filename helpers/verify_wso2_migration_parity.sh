#!/usr/bin/env bash
# verify_wso2_migration_parity.sh
#
# Verifies a completed rehearsal migration (run_wso2_migration_rehearsal.sh):
# - row-count parity per table, H2 CSV export vs loaded PostgreSQL tables
# - functional checks against wso2is-target: admin login, seeded users via
#   SCIM, OAuth token issuance + introspection for the seeded client
set -uo pipefail
cd "$(dirname "$0")/.."

STATE_DIR="/tmp/wso2-migration-rehearsal"
TARGET_URL="https://localhost:29443"
FAIL=0

log() { echo "[verify] $*"; }
pass() { echo "[verify] PASS: $*"; }
fail() { echo "[verify] FAIL: $*"; FAIL=1; }

# --- Row count parity ---
WORKDIR=$(cat "$STATE_DIR/h2_export_workdir.txt" 2>/dev/null || true)
if [ -z "$WORKDIR" ] || [ ! -d "$WORKDIR" ]; then
  fail "H2 export workdir not found (${WORKDIR:-unset}); run the migration first."
else
  helpers/verify_wso2_migration_row_counts.sh "$WORKDIR" localhost 15432 postgres postgres
  [ $? -ne 0 ] && FAIL=1
fi

# --- Functional checks against wso2is-target ---
log "Checking admin SCIM user listing on target..."
SCIM_RESP=$(curl -k -s -o /dev/null -w "%{http_code}" -u admin:admin \
  -H "Accept: application/scim+json" "${TARGET_URL}/scim2/Users?startIndex=1&count=100")
if [ "$SCIM_RESP" = "200" ]; then
  pass "Admin SCIM credentials work on target (HTTP 200)"
else
  fail "Admin SCIM check returned HTTP ${SCIM_RESP}"
fi

for user in player master Dennis; do
  FOUND=$(curl -k -s -u admin:admin -H "Accept: application/scim+json" \
    "${TARGET_URL}/scim2/Users?filter=userName+eq+%22${user}%22" | grep -c "\"userName\":\"${user}\"" || true)
  if [ "$FOUND" -ge 1 ]; then
    pass "Seeded user '${user}' present on target"
  else
    fail "Seeded user '${user}' NOT found on target"
  fi
done

log "Checking OAuth token issuance for the seeded client..."
CLIENT_ID=$(cat "$STATE_DIR/client_id.txt" 2>/dev/null || true)
CLIENT_SECRET=$(python3 -c "import json;print(json.load(open('$STATE_DIR/client.json'))['client_secret'])" 2>/dev/null || true)
if [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ]; then
  TOKEN_RESP=$(curl -k -s -u "${CLIENT_ID}:${CLIENT_SECRET}" \
    -d "grant_type=client_credentials" "${TARGET_URL}/oauth2/token")
  ACCESS_TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || true)
  if [ -n "$ACCESS_TOKEN" ]; then
    pass "Token issuance succeeded for migrated OAuth client"
    INTROSPECT_RESP=$(curl -k -s -u admin:admin -d "token=${ACCESS_TOKEN}" "${TARGET_URL}/oauth2/introspect")
    ACTIVE=$(echo "$INTROSPECT_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('active', False))" 2>/dev/null || echo "false")
    if [ "$ACTIVE" = "True" ]; then
      pass "Introspection confirms migrated token is active"
    else
      fail "Introspection did not report token as active: ${INTROSPECT_RESP}"
    fi
  else
    fail "Token issuance failed: ${TOKEN_RESP}"
  fi
else
  fail "No seeded client credentials found at ${STATE_DIR} - was the seed step run?"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "[verify] ALL CHECKS PASSED"
else
  echo "[verify] ONE OR MORE CHECKS FAILED - see FAIL lines above"
fi
exit "$FAIL"
