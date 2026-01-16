#!/usr/bin/env bash
# Configure WSO2 IS API Resources and scopes for applications (idempotent)
# This script creates API resources with scopes and authorizes them for applications
# using the WSO2 IS 7.x API Resources model.
set -euo pipefail

SCRIPT_NAME=$(basename "$0")

WINDENT() { sed 's/^/    /'; }

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options]

Configures WSO2 Identity Server API Resources and authorizes them for applications.
This script is idempotent and safe to run multiple times (e.g., on container startup).

Options:
  -h, --help             Show this help
  -s, --scope NAME       Scope name (default: dartboard:write)
  -a, --app NAME         Application name (default: DartsApp)
  --api-name NAME        API Resource name (default: Dartboard API)
  --api-id ID            API Resource identifier (default: dartboard)
  --host URL             WSO2 base URL (default: https://localhost:9443)
  --admin USER:PASS      Admin credentials (default: admin:admin)
  --insecure             Use insecure TLS (curl -k)
  --dry-run              Don't make changes, show actions
  --wait-for-wso2        Wait for WSO2 to be ready before proceeding

Example:
  $SCRIPT_NAME --scope dartboard:write --app DartsApp --host https://localhost:9443 --insecure
  
For container startup, use:
  $SCRIPT_NAME --wait-for-wso2 --insecure --host https://darts-wso2is:9443
EOF
}

SCOPE_NAME="dartboard:write"
APP_NAME="DartsApp"
API_RESOURCE_NAME="Dartboard API"
API_RESOURCE_ID="dartboard"
WSO2_HOST="https://localhost:9443"
ADMIN="admin:admin"
INSECURE=false
DRY_RUN=false
WAIT_FOR_WSO2=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -s|--scope) SCOPE_NAME="$2"; shift 2 ;;
    -a|--app) APP_NAME="$2"; shift 2 ;;
    --api-name) API_RESOURCE_NAME="$2"; shift 2 ;;
    --api-id) API_RESOURCE_ID="$2"; shift 2 ;;
    --host) WSO2_HOST="$2"; shift 2 ;;
    --admin) ADMIN="$2"; shift 2 ;;
    --insecure) INSECURE=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --wait-for-wso2) WAIT_FOR_WSO2=true; shift ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

echo "=== WSO2 API Resource & Scope Configuration ===" | WINDENT
echo "  WSO2_HOST: $WSO2_HOST" | WINDENT
echo "  ADMIN: ${ADMIN%%:*}:*******" | WINDENT
echo "  API Resource: $API_RESOURCE_NAME (id=$API_RESOURCE_ID)" | WINDENT
echo "  Scope: $SCOPE_NAME" | WINDENT
echo "  App: $APP_NAME" | WINDENT
echo "  Insecure TLS: $INSECURE" | WINDENT
echo "  Dry run: $DRY_RUN" | WINDENT

CURL_BASE=(curl -sS --max-time 10)
if [ "$INSECURE" = true ]; then
  CURL_BASE+=( -k )
fi
CURL_BASE+=( -u "$ADMIN" -H "Content-Type: application/json" )

API_RESOURCES_ENDPOINT="$WSO2_HOST/api/server/v1/api-resources"
API_APPS_ENDPOINT="$WSO2_HOST/api/server/v1/applications"

run_curl() {
  local out status body
  out=$("${CURL_BASE[@]}" "$@" --write-out "\n__HTTP_STATUS__:%{http_code}" 2>&1) || true
  status=$(echo "$out" | awk -F":" '/__HTTP_STATUS__:/ {print $2}' | tr -d '\r' )
  body=$(echo "$out" | sed '/__HTTP_STATUS__:/d')
  printf "%s\n%s" "$status" "$body"
}

# Wait for WSO2 to be ready
if [ "$WAIT_FOR_WSO2" = true ]; then
  echo "\nWaiting for WSO2 IS to be ready..." | WINDENT
  MAX_WAIT=60
  COUNT=0
  while [ $COUNT -lt $MAX_WAIT ]; do
    if "${CURL_BASE[@]}" -f "$WSO2_HOST/oauth2/token" -o /dev/null 2>&1; then
      echo "WSO2 IS is ready!" | WINDENT
      break
    fi
    COUNT=$((COUNT + 1))
    [ $COUNT -eq $MAX_WAIT ] && { echo "Timeout waiting for WSO2 IS" | WINDENT; exit 1; }
    sleep 1
  done
fi

echo "\n1) Ensure API Resource exists with scope (idempotent)" | WINDENT

# Try to find the API resource by identifier (search with filter)
# Note: WSO2 API resources endpoint is paginated, so we use filter
resp=$(run_curl "$API_RESOURCES_ENDPOINT?filter=identifier+eq+$API_RESOURCE_ID&limit=1")
http=$(echo "$resp" | sed -n '1p')
body=$(echo "$resp" | sed -n '2,$p')

API_RESOURCE_EXISTING_ID=""
if [ "$http" = "200" ]; then
  API_RESOURCE_EXISTING_ID=$(echo "$body" | jq -r '.apiResources[0].id // empty' 2>/dev/null) || true
fi

if [ -n "$API_RESOURCE_EXISTING_ID" ]; then
  echo "API Resource '$API_RESOURCE_NAME' already exists (id=$API_RESOURCE_EXISTING_ID)" | WINDENT
  
  # Fetch the full API resource to check scopes
  resp=$(run_curl "$API_RESOURCES_ENDPOINT/$API_RESOURCE_EXISTING_ID")
  http=$(echo "$resp" | sed -n '1p')
  body=$(echo "$resp" | sed -n '2,$p')
  
  if [ "$http" = "200" ]; then
    SCOPE_EXISTS=$(echo "$body" | jq -r --arg scope "$SCOPE_NAME" '.scopes[]? | select(.name == $scope) | .name // empty' 2>/dev/null) || true
    
    if [ -n "$SCOPE_EXISTS" ]; then
      echo "Scope '$SCOPE_NAME' already exists in API Resource" | WINDENT
    else
      echo "Warning: Scope '$SCOPE_NAME' not found in API Resource" | WINDENT
      echo "Note: WSO2 does not support adding scopes to existing API resources via API" | WINDENT
      echo "Please delete and recreate the API resource, or add the scope via console" | WINDENT
    fi
  fi
  API_RESOURCE_UUID="$API_RESOURCE_EXISTING_ID"
else
  # Create new API resource
  echo "Creating new API Resource '$API_RESOURCE_NAME'..." | WINDENT
  if [ "$DRY_RUN" = true ]; then
    echo "DRY-RUN: would create API Resource" | WINDENT
    API_RESOURCE_UUID="dry-run-uuid"
  else
    api_payload="{\"name\":\"$API_RESOURCE_NAME\",\"identifier\":\"$API_RESOURCE_ID\",\"scopes\":[{\"name\":\"$SCOPE_NAME\",\"displayName\":\"Write Dartboard Data\",\"description\":\"Permission to write dartboard throw data\"}]}"
    resp=$(run_curl -X POST -d "$api_payload" "$API_RESOURCES_ENDPOINT")
    http=$(echo "$resp" | sed -n '1p')
    body=$(echo "$resp" | sed -n '2,$p')
    
    if [ "$http" = "201" ] || [ "$http" = "200" ]; then
      API_RESOURCE_UUID=$(echo "$body" | jq -r '.id // empty')
      echo "API Resource created (id=$API_RESOURCE_UUID)" | WINDENT
    elif [ "$http" = "409" ]; then
      echo "API Resource already exists (HTTP=$http), re-querying..." | WINDENT
      # Try to fetch it again with filter
      resp=$(run_curl "$API_RESOURCES_ENDPOINT?filter=identifier+eq+$API_RESOURCE_ID&limit=1")
      http=$(echo "$resp" | sed -n '1p')
      body=$(echo "$resp" | sed -n '2,$p')
      API_RESOURCE_UUID=$(echo "$body" | jq -r '.apiResources[0].id // empty' 2>/dev/null) || true
      if [ -z "$API_RESOURCE_UUID" ]; then
        echo "Failed to find API Resource after 409 conflict" | WINDENT
        echo "This may be a caching issue. Try running the script again." | WINDENT
        exit 3
      fi
      echo "Found API Resource (id=$API_RESOURCE_UUID)" | WINDENT
    else
      echo "Failed to create API Resource (HTTP=$http)" | WINDENT
      echo "$body" | WINDENT
      exit 3
    fi
  fi
fi

echo "\n2) Find application ID for '$APP_NAME'" | WINDENT
resp=$(run_curl "$API_APPS_ENDPOINT?filter=name+eq+$APP_NAME")
http=$(echo "$resp" | sed -n '1p')
body=$(echo "$resp" | sed -n '2,$p')

if [ "$http" != "200" ]; then
  echo "Failed to query applications (HTTP=$http)" | WINDENT
  echo "$body" | WINDENT
  exit 4
fi

APP_ID=$(echo "$body" | jq -r '.applications[0].id // empty' 2>/dev/null) || true
if [ -z "$APP_ID" ]; then
  echo "Application '$APP_NAME' not found" | WINDENT
  exit 5
fi
echo "Found APP_ID=$APP_ID" | WINDENT

echo "\n3) Authorize API Resource for application (idempotent)" | WINDENT

# Check if already authorized
resp=$(run_curl "$API_APPS_ENDPOINT/$APP_ID/authorized-apis")
http=$(echo "$resp" | sed -n '1p')
body=$(echo "$resp" | sed -n '2,$p')

if [ "$http" = "200" ]; then
  ALREADY_AUTHORIZED=$(echo "$body" | jq -r --arg id "$API_RESOURCE_UUID" '.authorizedAPIs[]? | select(.id == $id) | .id // empty' 2>/dev/null) || true
  
  if [ -n "$ALREADY_AUTHORIZED" ]; then
    echo "API Resource already authorized for $APP_NAME" | WINDENT
  else
    echo "Authorizing API Resource for $APP_NAME..." | WINDENT
    if [ "$DRY_RUN" = true ]; then
      echo "DRY-RUN: would authorize API Resource" | WINDENT
    else
      auth_payload="{\"id\":\"$API_RESOURCE_UUID\",\"policyIdentifier\":\"RBAC\",\"scopes\":[\"$SCOPE_NAME\"]}"
      resp=$(run_curl -X POST -d "$auth_payload" "$API_APPS_ENDPOINT/$APP_ID/authorized-apis")
      http=$(echo "$resp" | sed -n '1p')
      
      if [ "$http" = "201" ] || [ "$http" = "200" ]; then
        echo "API Resource authorized successfully" | WINDENT
      elif [ "$http" = "409" ]; then
        echo "API Resource already authorized (HTTP=$http)" | WINDENT
      else
        body=$(echo "$resp" | sed -n '2,$p')
        echo "Warning: Failed to authorize (HTTP=$http)" | WINDENT
        echo "$body" | WINDENT
      fi
    fi
  fi
fi

echo "\n=== Configuration Complete ===" | WINDENT
echo "\nTest with:" | WINDENT
echo "  TOKEN=\$(curl -sS ${INSECURE:+-k} -u \"CLIENT_ID:CLIENT_SECRET\" \\" | WINDENT
echo "    -d 'grant_type=client_credentials&scope=$SCOPE_NAME' \\" | WINDENT
echo "    \"$WSO2_HOST/oauth2/token\" | jq -r .access_token)" | WINDENT
echo "  curl -sS ${INSECURE:+-k} -u admin:admin -d \"token=\$TOKEN\" \\" | WINDENT
echo "    \"$WSO2_HOST/oauth2/introspect\" | jq" | WINDENT

exit 0
