# WSO2 API Resource & Scope Configuration

This script (`wso2_manage_scope.sh`) configures WSO2 Identity Server 7.x API Resources with OAuth2 scopes and authorizes them for applications.

## What It Does

1. **Creates/Checks API Resource**: Ensures the API Resource exists with the specified identifier and scope
2. **Authorizes Application**: Links the API Resource to the application so client_credentials tokens include the scope
3. **Idempotent**: Safe to run multiple times - won't duplicate resources or fail if already configured

## Usage

### Basic (localhost development)
```bash
bash scripts/wso2_manage_scope.sh \
  --scope dartboard:write \
  --app DartsApp \
  --host https://localhost:9443 \
  --admin admin:admin \
  --insecure
```

### Container Startup (internal WSO2 hostname)
```bash
bash scripts/wso2_manage_scope.sh \
  --scope dartboard:write \
  --app DartsApp \
  --host https://darts-wso2is:9443 \
  --admin admin:admin \
  --insecure \
  --wait-for-wso2
```

### Options

| Option              | Description                    | Default                  |
| ------------------- | ------------------------------ | ------------------------ |
| `--scope NAME`      | OAuth2 scope name              | `dartboard:write`        |
| `--app NAME`        | Application name in WSO2       | `DartsApp`               |
| `--api-name NAME`   | API Resource display name      | `Dartboard API`          |
| `--api-id ID`       | API Resource identifier        | `dartboard`              |
| `--host URL`        | WSO2 base URL                  | `https://localhost:9443` |
| `--admin USER:PASS` | Admin credentials              | `admin:admin`            |
| `--insecure`        | Use `-k` for self-signed certs | (not set)                |
| `--dry-run`         | Show what would be done        | (not set)                |
| `--wait-for-wso2`   | Wait for WSO2 to be ready      | (not set)                |

## Container Integration

Add to your docker-entrypoint.sh or docker-compose healthcheck/depends_on:

```bash
#!/bin/bash
# Wait for WSO2 and configure scopes
/app/scripts/wso2_manage_scope.sh \
  --host https://darts-wso2is:9443 \
  --insecure \
  --wait-for-wso2

# Then start your service
exec python run.py
```

## Verification

After running the script, test with:

```bash
# Get token with scope
TOKEN=$(curl -sS -k -u "local_client_id:local_client_secret" \
  -d "grant_type=client_credentials&scope=dartboard:write" \
  "https://localhost:9443/oauth2/token" | jq -r .access_token)

# Introspect to verify scope
curl -sS -k -u admin:admin -d "token=$TOKEN" \
  "https://localhost:9443/oauth2/introspect" | jq

# Expected: "scope": "dartboard:write"
```

## Troubleshooting

### "Failed to find API Resource after 409 conflict"
This is a caching/timing issue. Run the script again after a few seconds.

### "API Resource already authorized (HTTP=409)"
This is expected and means the configuration is already correct. The script is idempotent.

### "Scope 'dartboard:write' not found in API Resource"
WSO2 7.x doesn't support adding scopes to existing API resources via the REST API. Either:
- Delete and recreate the API resource (via console or API)
- Add the scope manually in the WSO2 admin console

## WSO2 IS 7.x Model

WSO2 Identity Server 7.x uses **API Resources** instead of direct scope attachment:

1. **API Resource**: A logical API with one or more scopes (e.g., "Dartboard API" with scope "dartboard:write")
2. **Authorization**: Applications must be authorized to use an API Resource
3. **Token Scopes**: When requesting a token, the scope comes from the authorized API Resource

This script handles all three steps automatically.
