# Test WSO2 Bootstrap

Use these scripts on the test server after the WSO2 databases and services are up. Run them one by one and verify the output after each step.

## 0. Load the test environment

```bash
cd /opt/dartserver-pythonapp
while IFS= read -r line; do
  line="${line#export }"
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  line="${line%%[[:space:]]#*}"
  key="${line%%=*}"
  value="${line#*=}"
  export "$key=$value"
done < .env
```

## 1. Register the test-server OAuth client

```bash
python3 helpers/register_wso2_test_client.py
```

Verify:
- The script reports that the client was found or registered.
- It prints a successful token request.

## 2. Configure redirect URIs on the application

```bash
python3 helpers/configure_wso2_redirects.py
```

Verify:
- The script reports the application was found.
- It shows the updated callback URLs.

## 3. Provision the player account

```bash
python3 helpers/test_wso2_provision_user.py \
  --username player \
  --password Playerpass1 \
  --role player \
  --display-name Player
```

## 4. Provision the game master account

```bash
python3 helpers/test_wso2_provision_user.py \
  --username master \
  --password Masterpass1 \
  --role gamemaster \
  --display-name Master
```

## 5. Provision the admin account

```bash
python3 helpers/test_wso2_provision_user.py \
  --username Dennis \
  --password 'DwvDG=8k' \
  --role admin \
  --display-name Dennis
```

Verify for each user:
- The user is created or updated successfully.
- The requested role appears in the final role list.

## 6. Configure the gateway client

```bash
python3 helpers/configure_wso2_gateway_client.py \
  --ws-url "$WSO2_IS_URL" \
  --admin-user "$WSO2_IS_INTROSPECT_USER" \
  --admin-pass "$WSO2_IS_INTROSPECT_PASSWORD" \
  --client-id "$WSO2_IS_CLIENT_ID" \
  --client-secret "$WSO2_IS_CLIENT_SECRET" \
  --redirect-uris "$WSO2_REDIRECT_URI"
```

Verify:
- The client lookup or update succeeds.
- The script prints a successful token request.

## 7. Optional validation

```bash
docker exec -i darts-postgres psql -U postgres -d wso2is_shared -c "
SELECT um_role_name FROM um_role WHERE um_role_name IN ('admin','everyone');
"

docker exec -i darts-postgres psql -U postgres -d wso2is_identity -c "
SELECT c.claim_uri, m.user_store_domain_name, m.attribute_name
FROM idn_claim c
LEFT JOIN idn_claim_mapped_attribute m
  ON m.local_claim_id = c.id AND m.tenant_id = c.tenant_id
WHERE c.claim_uri IN ('http://wso2.org/claims/username','http://wso2.org/claims/addresses');
"
```

## Troubleshooting: relation "um_domain" does not exist

If WSO2 fails during startup with an error like `ERROR: relation "um_domain" does not exist`, the shared WSO2 schema was not seeded (or was partially seeded) in PostgreSQL.

From the project root, run:

```bash
cd /opt/dartserver-pythonapp
ALLOW_WSO2_RESEED=true bash helpers/setup-test-environment.sh
```

What this does:
- Verifies `wso2is_shared` and `wso2is_identity` databases.
- Drops and recreates those two databases if the user store bootstrap is incomplete.
- Reimports `wso2is-7-config/postgresql-shared.sql` and `wso2is-7-config/postgresql-identity.sql`.

Then restart WSO2 services:

```bash
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml restart wso2is wso2apim
```

Quick checks:

```bash
docker exec -i darts-postgres psql -U postgres -d wso2is_shared -tAc "SELECT to_regclass('public.um_domain');"
docker exec -i darts-postgres psql -U postgres -d wso2is_shared -tAc "SELECT COUNT(*) FROM um_role WHERE um_role_name IN ('admin','everyone');"
```

Expected results:
- First query returns `um_domain`.
- Second query returns `2` or higher.

## Next step

These same checks are now suitable for the deployment pipeline as an idempotent bootstrap flow:

- Reseed WSO2 only when the shared or identity databases are incomplete.
- Verify each bootstrap element and create or update it only when missing or drifted.
- Start the public `darts-app` and `api-gateway` services only after bootstrap and migration complete, so they use the final OAuth configuration on first start.

The pipeline should therefore follow this order:

```bash
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d postgres rabbitmq wso2is wso2apim
ALLOW_WSO2_RESEED=true STRICT_WSO2_BOOTSTRAP=true bash helpers/setup-test-environment.sh
WSO2_POST_START_REPAIR=true bash helpers/setup-test-environment.sh
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml run --rm --no-deps darts-app alembic upgrade head
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d darts-app api-gateway nginx
```
