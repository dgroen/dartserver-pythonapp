#!/usr/bin/env bash
# Provision (or repair) the WSO2 IS OAuth2/OIDC application used by darts-app
# for browser login in local development (idempotent).
#
# This exists because the application is NOT created by any deployment.toml
# or database seed - it only lives in WSO2's own database (the wso2is_data /
# postgres_data Docker volumes). If those volumes are ever wiped
# (`docker-compose down -v`, a fresh checkout, a new dev machine), the
# application must be recreated with this exact client_id/secret and a
# callback URL that tolerates VS Code's dynamic port-forwarding, or login
# will fail with invalid_client / invalid_callback.
set -euo pipefail

SCRIPT_NAME=$(basename "$0")

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options]

Creates (or updates) the WSO2 IS application used for local browser login,
with a fixed client_id/secret and a callback URL regex that accepts any
localhost port (needed because VS Code/SSH port-forwarding of privileged
ports 80/443 lands on a random local port).

This script is idempotent and safe to run multiple times.

Options:
  -h, --help             Show this help
  --app NAME             Application name (default: DartsLocalClient)
  --client-id ID         OAuth2 client_id (default: \$WSO2_CLIENT_ID or qGUe7mARfB_rbEn09jWJtTyi9uMa)
  --client-secret SECRET OAuth2 client_secret (default: \$WSO2_CLIENT_SECRET, required if app doesn't exist)
  --callback-regex REGEX Callback URL regex body, without the "regexp=" prefix
                         (default: (https?://localhost(:[0-9]+)?/callback))
  --host URL             WSO2 base URL (default: https://localhost:9443)
  --admin USER:PASS      Admin credentials (default: admin:admin)
  --insecure             Use insecure TLS (curl -k)
  --wait-for-wso2        Wait for WSO2 to be ready before proceeding

Example (after a from-scratch rebuild):
  $SCRIPT_NAME --wait-for-wso2 --insecure

For container startup, use:
  $SCRIPT_NAME --wait-for-wso2 --insecure --host https://darts-wso2is:9443
EOF
}

APP_NAME="DartsLocalClient"
CLIENT_ID="${WSO2_CLIENT_ID:-qGUe7mARfB_rbEn09jWJtTyi9uMa}"
CLIENT_SECRET="${WSO2_CLIENT_SECRET:-}"
CALLBACK_REGEX='(https?://localhost(:[0-9]+)?/callback)'
WSO2_HOST="https://localhost:9443"
ADMIN="admin:admin"
INSECURE=false
WAIT_FOR_WSO2=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --app) APP_NAME="$2"; shift 2 ;;
    --client-id) CLIENT_ID="$2"; shift 2 ;;
    --client-secret) CLIENT_SECRET="$2"; shift 2 ;;
    --callback-regex) CALLBACK_REGEX="$2"; shift 2 ;;
    --host) WSO2_HOST="$2"; shift 2 ;;
    --admin) ADMIN="$2"; shift 2 ;;
    --insecure) INSECURE=true; shift ;;
    --wait-for-wso2) WAIT_FOR_WSO2=true; shift ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

echo "=== WSO2 Local OIDC Client Provisioning ==="
echo "  WSO2_HOST: $WSO2_HOST"
echo "  App name: $APP_NAME"
echo "  Client ID: $CLIENT_ID"
echo "  Callback regex: $CALLBACK_REGEX"

CURL_BASE=(curl -sS --max-time 10)
if [ "$INSECURE" = true ]; then
  CURL_BASE+=( -k )
fi
CURL_BASE+=( -u "$ADMIN" -H "Content-Type: application/json" )

APPS_ENDPOINT="$WSO2_HOST/api/server/v1/applications"

run_curl() {
  local out status body
  out=$("${CURL_BASE[@]}" "$@" --write-out "\n__HTTP_STATUS__:%{http_code}" 2>&1) || true
  status=$(echo "$out" | awk -F":" '/__HTTP_STATUS__:/ {print $2}' | tr -d '\r')
  body=$(echo "$out" | sed '/__HTTP_STATUS__:/d')
  printf "%s\n%s" "$status" "$body"
}

if [ "$WAIT_FOR_WSO2" = true ]; then
  echo
  echo "Waiting for WSO2 IS to be ready..."
  MAX_WAIT=120
  COUNT=0
  while [ $COUNT -lt $MAX_WAIT ]; do
    if "${CURL_BASE[@]}" -f "$WSO2_HOST/oauth2/token" -o /dev/null 2>&1; then
      echo "WSO2 IS is ready!"
      break
    fi
    COUNT=$((COUNT + 1))
    [ $COUNT -eq $MAX_WAIT ] && { echo "Timeout waiting for WSO2 IS"; exit 1; }
    sleep 2
  done
fi

echo
echo "1) Look up application by client_id=$CLIENT_ID"
resp=$(run_curl "$APPS_ENDPOINT?filter=clientId+eq+$CLIENT_ID")
http=$(echo "$resp" | sed -n '1p')
body=$(echo "$resp" | sed -n '2,$p')

APP_ID=""
if [ "$http" = "200" ]; then
  APP_ID=$(echo "$body" | jq -r '.applications[0].id // empty' 2>/dev/null) || true
fi

if [ -n "$APP_ID" ]; then
  echo "Application already exists (id=$APP_ID)"
else
  echo "Application not found by client_id, checking by name '$APP_NAME'..."
  resp=$(run_curl "$APPS_ENDPOINT?filter=name+eq+$APP_NAME")
  http=$(echo "$resp" | sed -n '1p')
  body=$(echo "$resp" | sed -n '2,$p')
  if [ "$http" = "200" ]; then
    APP_ID=$(echo "$body" | jq -r '.applications[0].id // empty' 2>/dev/null) || true
  fi

  if [ -n "$APP_ID" ]; then
    echo "Found existing application '$APP_NAME' (id=$APP_ID), will update its client_id/secret"
  else
    echo "Creating new application '$APP_NAME'..."
    if [ -z "$CLIENT_SECRET" ]; then
      echo "ERROR: --client-secret (or \$WSO2_CLIENT_SECRET) is required to create a new application" >&2
      exit 3
    fi
    create_payload=$(jq -n --arg name "$APP_NAME" \
      '{name: $name, description: ("Service Provider for application " + $name), templateId: null}')
    # The create endpoint returns 201 with an empty body; the new app's id is
    # only available in the Location header, so capture headers separately.
    create_headers=$(mktemp)
    http=$("${CURL_BASE[@]}" -D "$create_headers" -o /dev/null -w "%{http_code}" -X POST -d "$create_payload" "$APPS_ENDPOINT")
    if [ "$http" != "201" ]; then
      echo "Failed to create application (HTTP=$http)" >&2
      cat "$create_headers" >&2
      rm -f "$create_headers"
      exit 3
    fi
    APP_ID=$(grep -i '^Location:' "$create_headers" | sed 's#.*/##' | tr -d '\r')
    rm -f "$create_headers"
    echo "Application created (id=$APP_ID)"
  fi
fi

if [ -z "$CLIENT_SECRET" ]; then
  echo
  echo "2) --client-secret not given: fetching existing secret to preserve it"
  resp=$(run_curl "$APPS_ENDPOINT/$APP_ID/inbound-protocols/oidc")
  http=$(echo "$resp" | sed -n '1p')
  body=$(echo "$resp" | sed -n '2,$p')
  if [ "$http" = "200" ]; then
    CLIENT_SECRET=$(echo "$body" | jq -r '.clientSecret // empty')
  fi
  if [ -z "$CLIENT_SECRET" ]; then
    echo "ERROR: no existing client secret found and none provided via --client-secret" >&2
    exit 3
  fi
fi

echo
echo "3) Apply OIDC inbound protocol config (idempotent upsert)"
# WSO2 IS's PUT .../inbound-protocols/oidc throws an opaque 500 if required
# nested objects (accessToken, refreshToken, idToken, etc.) are missing from
# the payload - it does not accept a minimal partial object. So we start from
# the existing config if there is one (to preserve any other settings) and
# fall back to a known-good full default template for a brand new app.
resp=$(run_curl "$APPS_ENDPOINT/$APP_ID/inbound-protocols/oidc")
http=$(echo "$resp" | sed -n '1p')
body=$(echo "$resp" | sed -n '2,$p')

if [ "$http" = "200" ]; then
  BASE_TEMPLATE="$body"
else
  BASE_TEMPLATE='{
    "grantTypes": ["authorization_code", "refresh_token", "client_credentials", "password"],
    "allowedOrigins": [],
    "publicClient": false,
    "pkce": {"mandatory": false, "supportPlainTransformAlgorithm": false},
    "hybridFlow": {"enable": false, "responseType": "null"},
    "accessToken": {
      "type": "Default",
      "userAccessTokenExpiryInSeconds": 3600,
      "applicationAccessTokenExpiryInSeconds": 3600,
      "revokeTokensWhenIDPSessionTerminated": false,
      "validateTokenBinding": false,
      "accessTokenAttributes": []
    },
    "refreshToken": {"expiryInSeconds": 86400, "renewRefreshToken": false},
    "subjectToken": {"enable": false, "applicationSubjectTokenExpiryInSeconds": 180},
    "idToken": {"expiryInSeconds": 3600, "audience": [], "encryption": {"enabled": false, "algorithm": "", "method": ""}},
    "logout": {},
    "validateRequestObjectSignature": false,
    "scopeValidators": [],
    "clientAuthentication": {"tokenEndpointAuthMethod": "client_secret_basic"},
    "requestObject": {"encryption": {"algorithm": "", "method": ""}},
    "pushAuthorizationRequest": {"requirePushAuthorizationRequest": false},
    "subject": {"subjectType": "public"},
    "isFAPIApplication": false
  }'
fi

oidc_payload=$(echo "$BASE_TEMPLATE" | jq \
  --arg clientId "$CLIENT_ID" \
  --arg clientSecret "$CLIENT_SECRET" \
  --arg callback "regexp=$CALLBACK_REGEX" \
  '. + {
    clientId: $clientId,
    clientSecret: $clientSecret,
    grantTypes: ["authorization_code", "refresh_token", "client_credentials", "password"],
    callbackURLs: [$callback],
    publicClient: false
  }')

resp=$(run_curl -X PUT -d "$oidc_payload" "$APPS_ENDPOINT/$APP_ID/inbound-protocols/oidc")
http=$(echo "$resp" | sed -n '1p')
body=$(echo "$resp" | sed -n '2,$p')

if [ "$http" = "200" ]; then
  echo "OIDC configuration applied successfully"
else
  echo "Failed to apply OIDC configuration (HTTP=$http)" >&2
  echo "$body" >&2
  exit 4
fi

echo
echo "=== Provisioning Complete ==="
echo "  App ID: $APP_ID"
echo "  Client ID: $CLIENT_ID"
echo "  Callback: regexp=$CALLBACK_REGEX"
echo
echo "Make sure .env has matching values:"
echo "  WSO2_CLIENT_ID=$CLIENT_ID"
echo "  WSO2_CLIENT_SECRET=<same secret used here>"

exit 0
