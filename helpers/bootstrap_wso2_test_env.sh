#!/usr/bin/env bash
# bootstrap_wso2_test_env.sh
# Run WSO2 bootstrap steps for test deployment and update .env with client credentials
set -euo pipefail

cd "$(dirname "$0")/.."

# Capture caller-provided env vars BEFORE sourcing .env so .env cannot override them.
# This matters when the caller forces WSO2_IS_INTERNAL_URL=https://localhost:9443 to
# avoid Docker-internal hostnames that are unreachable from the host shell.
_CALLER_WSO2_IS_INTERNAL_URL="${WSO2_IS_INTERNAL_URL:-}"
_CALLER_STRICT="${STRICT_WSO2_BOOTSTRAP:-}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Restore caller overrides after .env source.
[[ -n "$_CALLER_WSO2_IS_INTERNAL_URL" ]] && WSO2_IS_INTERNAL_URL="$_CALLER_WSO2_IS_INTERNAL_URL"
[[ -n "$_CALLER_STRICT" ]] && STRICT_WSO2_BOOTSTRAP="$_CALLER_STRICT"

ENV_FILE=".env"
STRICT_WSO2_BOOTSTRAP="${STRICT_WSO2_BOOTSTRAP:-false}"

resolve_wso2_admin_credentials() {
  local base_url
  local primary_user
  local primary_pass
  local http_code

  # Prefer localhost (direct port mapping) over Docker-internal or public hostnames.
  base_url="${WSO2_IS_INTERNAL_URL:-https://localhost:9443}"
  primary_user="${WSO2_ADMIN_USER:-${WSO2_ADMIN_USERNAME:-${WSO2_IS_INTROSPECT_USER:-admin}}}"
  primary_pass="${WSO2_ADMIN_PASS:-${WSO2_ADMIN_PASSWORD:-${WSO2_IS_INTROSPECT_PASSWORD:-admin}}}"

  check_creds() {
    local user="$1"
    local pass="$2"
    curl -k -s -o /dev/null -w "%{http_code}" \
      --connect-timeout 3 --max-time 8 \
      -u "${user}:${pass}" \
      -H "Accept: application/scim+json" \
      "${base_url%/}/scim2/Users?startIndex=1&count=1"
  }

  echo "[WSO2 Bootstrap] Verifying admin credentials..."
  http_code=$(check_creds "$primary_user" "$primary_pass")
  if [[ "$http_code" == "200" ]]; then
    export BOOTSTRAP_ADMIN_USER="$primary_user"
    export BOOTSTRAP_ADMIN_PASS="$primary_pass"
    echo "[WSO2 Bootstrap] Using configured admin user: ${BOOTSTRAP_ADMIN_USER}"
    return
  fi

  echo "[WSO2 Bootstrap] Configured admin credentials returned HTTP ${http_code}."
  http_code=$(check_creds "admin" "admin")
  if [[ "$http_code" == "200" ]]; then
    export BOOTSTRAP_ADMIN_USER="admin"
    export BOOTSTRAP_ADMIN_PASS="admin"
    echo "[WSO2 Bootstrap] Falling back to default admin/admin credentials after reseed."
    return
  fi

  echo "[WSO2 Bootstrap] Could not validate admin credentials (configured and admin/admin failed)."
  echo "[WSO2 Bootstrap] Continuing with configured credentials so downstream error output is preserved."
  export BOOTSTRAP_ADMIN_USER="$primary_user"
  export BOOTSTRAP_ADMIN_PASS="$primary_pass"
}

ensure_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    touch "$ENV_FILE"
  fi
}

handle_step_failure() {
  local message="$1"
  if [[ "$STRICT_WSO2_BOOTSTRAP" == "true" ]]; then
    echo "[WSO2 Bootstrap] Error: ${message}"
    exit 1
  fi
  echo "[WSO2 Bootstrap] Warning: ${message}"
}

extract_json_field() {
  local json_payload="$1"
  local field_name="$2"

  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json_payload" | jq -r ".${field_name}"
    return
  fi

  printf '%s' "$json_payload" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('${field_name}', ''))"
}

resolve_wso2_admin_credentials

# Expose the resolved API URL for all downstream Python helpers.
# WSO2_IS_INTERNAL_URL is already forced to localhost:9443 by the caller;
# we export it so Python scripts that read env vars pick it up too.
export WSO2_IS_URL="${WSO2_IS_INTERNAL_URL:-https://localhost:9443}"

# 1. Register the test-server OAuth client and capture client_id/secret
echo "[WSO2 Bootstrap] Registering OAuth client..."
CLIENT_JSON=$(python3 helpers/register_wso2_test_client.py --json \
  --ws-url "$WSO2_IS_URL" \
  --admin-user "$BOOTSTRAP_ADMIN_USER" \
  --admin-pass "$BOOTSTRAP_ADMIN_PASS")
CLIENT_ID=$(extract_json_field "$CLIENT_JSON" "client_id")
CLIENT_SECRET=$(extract_json_field "$CLIENT_JSON" "client_secret")
if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
  handle_step_failure "test client registration did not return client credentials."
fi
export WSO2_CLIENT_ID="$CLIENT_ID"
export WSO2_CLIENT_SECRET="$CLIENT_SECRET"

# 2. Configure redirect URIs
echo "[WSO2 Bootstrap] Configuring redirect URIs..."
if ! python3 helpers/configure_wso2_redirects.py --ws-url "$WSO2_IS_URL" --admin-user "$BOOTSTRAP_ADMIN_USER" --admin-pass "$BOOTSTRAP_ADMIN_PASS"; then
  handle_step_failure "redirect URI configuration failed."
fi

# 3. Provision users
echo "[WSO2 Bootstrap] Provisioning users..."
PLAYER_PASSWORD="${WSO2_PLAYER_PASSWORD:-Playerpass1!}"
MASTER_PASSWORD="${WSO2_MASTER_PASSWORD:-Masterpass1!}"
DENNIS_PASSWORD="${WSO2_DENNIS_PASSWORD:-DwvDG=8k}"
if ! python3 helpers/test_wso2_provision_user.py --ws-url "$WSO2_IS_URL" --admin-user "$BOOTSTRAP_ADMIN_USER" --admin-pass "$BOOTSTRAP_ADMIN_PASS" --username player --password "$PLAYER_PASSWORD" --role player --display-name Player; then
  handle_step_failure "failed to provision user 'player'."
fi
if ! python3 helpers/test_wso2_provision_user.py --ws-url "$WSO2_IS_URL" --admin-user "$BOOTSTRAP_ADMIN_USER" --admin-pass "$BOOTSTRAP_ADMIN_PASS" --username master --password "$MASTER_PASSWORD" --role gamemaster --display-name Master; then
  handle_step_failure "failed to provision user 'master'."
fi
if ! python3 helpers/test_wso2_provision_user.py --ws-url "$WSO2_IS_URL" --admin-user "$BOOTSTRAP_ADMIN_USER" --admin-pass "$BOOTSTRAP_ADMIN_PASS" --username Dennis --password "$DENNIS_PASSWORD" --role admin --display-name Dennis; then
  handle_step_failure "failed to provision user 'Dennis'."
fi

# 4. Configure the gateway client and capture gateway client_id/secret
echo "[WSO2 Bootstrap] Configuring gateway client..."
if GATEWAY_JSON=$(python3 helpers/configure_wso2_gateway_client.py --json \
  --ws-url "$WSO2_IS_URL" \
  --admin-user "$BOOTSTRAP_ADMIN_USER" \
  --admin-pass "$BOOTSTRAP_ADMIN_PASS"); then
  GATEWAY_CLIENT_ID=$(extract_json_field "$GATEWAY_JSON" "client_id")
  GATEWAY_CLIENT_SECRET=$(extract_json_field "$GATEWAY_JSON" "client_secret")
else
  handle_step_failure "gateway client configuration failed."
  GATEWAY_CLIENT_ID="${WSO2_GATEWAY_CLIENT_ID:-}"
  GATEWAY_CLIENT_SECRET="${WSO2_GATEWAY_CLIENT_SECRET:-}"
fi

if [[ "$STRICT_WSO2_BOOTSTRAP" == "true" && ( -z "$GATEWAY_CLIENT_ID" || -z "$GATEWAY_CLIENT_SECRET" ) ]]; then
  handle_step_failure "gateway client credentials are missing after configuration."
fi

# 5. Update .env file with new client credentials
update_env_var() {
  local key="$1"
  local value="$2"
  local tmp_file

  ensure_env_file
  tmp_file=$(mktemp)

  awk -v key="$key" -v value="$value" '
    BEGIN { updated = 0 }
    $0 ~ "^" key "=" {
      if (!updated) {
        print key "=" value
        updated = 1
      }
      next
    }
    { print }
    END {
      if (!updated) {
        print key "=" value
      }
    }
  ' "$ENV_FILE" > "$tmp_file"

  mv "$tmp_file" "$ENV_FILE"
}

update_env_var "WSO2_IS_CLIENT_ID" "$CLIENT_ID"
update_env_var "WSO2_IS_CLIENT_SECRET" "$CLIENT_SECRET"
update_env_var "WSO2_ADMIN_USER" "$BOOTSTRAP_ADMIN_USER"
update_env_var "WSO2_ADMIN_USERNAME" "$BOOTSTRAP_ADMIN_USER"
update_env_var "WSO2_ADMIN_PASS" "$BOOTSTRAP_ADMIN_PASS"
update_env_var "WSO2_ADMIN_PASSWORD" "$BOOTSTRAP_ADMIN_PASS"
update_env_var "WSO2_IS_INTROSPECT_USER" "$BOOTSTRAP_ADMIN_USER"
update_env_var "WSO2_IS_INTROSPECT_PASSWORD" "$BOOTSTRAP_ADMIN_PASS"
if [[ -n "$GATEWAY_CLIENT_ID" ]]; then
  update_env_var "WSO2_GATEWAY_CLIENT_ID" "$GATEWAY_CLIENT_ID"
fi
if [[ -n "$GATEWAY_CLIENT_SECRET" ]]; then
  update_env_var "WSO2_GATEWAY_CLIENT_SECRET" "$GATEWAY_CLIENT_SECRET"
fi

echo "[WSO2 Bootstrap] .env updated with client credentials."
