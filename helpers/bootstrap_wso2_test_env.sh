#!/usr/bin/env bash
# bootstrap_wso2_test_env.sh
# Run WSO2 bootstrap steps for test deployment and update .env with client credentials
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

ENV_FILE=".env"

APP_CLIENT_ID="${WSO2_CLIENT_ID:-}"
APP_CLIENT_SECRET="${WSO2_CLIENT_SECRET:-}"
APP_CLIENT_NAME="${WSO2_CLIENT_NAME:-DartsTestServer}"

GATEWAY_CLIENT_ID="${WSO2_IS_CLIENT_ID:-${WSO2_GATEWAY_CLIENT_ID:-}}"
GATEWAY_CLIENT_SECRET="${WSO2_IS_CLIENT_SECRET:-${WSO2_GATEWAY_CLIENT_SECRET:-}}"
GATEWAY_CLIENT_NAME="${WSO2_IS_CLIENT_NAME:-DartsApiGateway}"

require_non_empty() {
  local key="$1"
  local value="$2"
  if [[ -z "$value" ]]; then
    echo "[WSO2 Bootstrap] Missing required value: $key"
    exit 1
  fi
}

ensure_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    touch "$ENV_FILE"
  fi
}

# 1. Register the test-server OAuth client and capture client_id/secret
echo "[WSO2 Bootstrap] Registering OAuth client..."
require_non_empty "WSO2_CLIENT_ID" "$APP_CLIENT_ID"
require_non_empty "WSO2_CLIENT_SECRET" "$APP_CLIENT_SECRET"
CLIENT_JSON=$(python3 helpers/register_wso2_test_client.py \
  --client-id "$APP_CLIENT_ID" \
  --client-secret "$APP_CLIENT_SECRET" \
  --client-name "$APP_CLIENT_NAME" \
  --json)
CLIENT_ID=$(echo "$CLIENT_JSON" | jq -r '.client_id')
CLIENT_SECRET=$(echo "$CLIENT_JSON" | jq -r '.client_secret')

# 2. Configure redirect URIs
echo "[WSO2 Bootstrap] Configuring redirect URIs..."
python3 helpers/configure_wso2_redirects.py

# 3. Provision users
echo "[WSO2 Bootstrap] Provisioning users..."
python3 helpers/test_wso2_provision_user.py --username player --password playerpass --role player --display-name Player
python3 helpers/test_wso2_provision_user.py --username master --password masterpass --role gamemaster --display-name Master
python3 helpers/test_wso2_provision_user.py --username Dennis --password 'DwvDG=8k' --role admin --display-name Dennis

# 4. Configure the gateway client and capture gateway client_id/secret
echo "[WSO2 Bootstrap] Configuring gateway client..."
require_non_empty "WSO2_IS_CLIENT_ID (or WSO2_GATEWAY_CLIENT_ID)" "$GATEWAY_CLIENT_ID"
require_non_empty "WSO2_IS_CLIENT_SECRET (or WSO2_GATEWAY_CLIENT_SECRET)" "$GATEWAY_CLIENT_SECRET"
GATEWAY_JSON=$(python3 helpers/configure_wso2_gateway_client.py \
  --client-id "$GATEWAY_CLIENT_ID" \
  --client-secret "$GATEWAY_CLIENT_SECRET" \
  --json)
GATEWAY_CLIENT_ID=$(echo "$GATEWAY_JSON" | jq -r '.client_id')
GATEWAY_CLIENT_SECRET=$(echo "$GATEWAY_JSON" | jq -r '.client_secret')

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

update_env_var "WSO2_CLIENT_ID" "$CLIENT_ID"
update_env_var "WSO2_CLIENT_SECRET" "$CLIENT_SECRET"
update_env_var "WSO2_IS_CLIENT_ID" "$GATEWAY_CLIENT_ID"
update_env_var "WSO2_IS_CLIENT_SECRET" "$GATEWAY_CLIENT_SECRET"

echo "[WSO2 Bootstrap] .env updated with client credentials."
