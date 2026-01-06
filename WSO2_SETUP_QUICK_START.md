# WSO2 Setup - Quick Reference

## Quick Start

### Local Development
```bash
# 1. Start WSO2 stack
docker-compose -f docker-compose-localhost.yml up -d wso2is

# 2. Run complete setup
python3 helpers/setup_wso2_complete.py

# 3. Get client credentials (printed by script)
# Update .env with:
# WSO2_CLIENT_ID=<client_id_from_script>
# WSO2_CLIENT_SECRET=<client_secret_from_script>

# 4. Restart application
docker-compose restart darts-app
```

### Test/Production Deployment
```bash
# From GitHub Actions or deployment server
python3 helpers/setup_wso2_complete.py \
  --env production \
  --env-file .env.production \
  --verbose
```

## Manual Steps

If you need to run individual steps:

```bash
# 1. Setup roles and users
python3 helpers/setup_wso2_roles.py

# 2. Register APIM OAuth clients (if using APIM)
python3 helpers/configure_wso2_oauth_apps.py

# 3. Register DartsApp
python3 helpers/register_darts_app.py

# 4. Configure redirect URIs
python3 helpers/configure_wso2_redirects.py
```

## GitHub Actions Deployment

### Trigger Workflow
1. Go to repository → Actions
2. Select "Deploy WSO2 Environment"  
3. Click "Run workflow"
4. Choose environment (test/staging/production)
5. Optionally skip steps or validation

### Required Secrets (per environment)
- `WSO2_IS_URL`
- `WSO2_IS_INTERNAL_URL`
- `WSO2_ADMIN_USERNAME`
- `WSO2_ADMIN_PASSWORD`
- `WSO2_REDIRECT_URI`
- `WSO2_POST_LOGOUT_REDIRECT_URI`
- `DEPLOY_SSH_KEY` (for remote deployment)
- `DEPLOY_SERVER_HOST`
- `DEPLOY_SERVER_USER`

## Troubleshooting

### WSO2 Not Ready
```bash
# Check WSO2 logs
docker-compose logs wso2is | tail -100

# Test WSO2 accessibility
curl -k https://localhost:9443/carbon/admin/login.jsp
```

### Client Not Found Error
```bash
# Re-register DartsApp
python3 helpers/setup_wso2_complete.py \
  --skip-wait --skip-roles --skip-apim --skip-redirects
```

### Validation Failed
```bash
# Check all applications exist
curl -k https://localhost:9443/api/server/v1/applications \
  -u admin:admin | jq '.applications[].name'
```

### Reset and Start Fresh
```bash
# Stop all services
docker-compose down -v

# Restart WSO2
docker-compose -f docker-compose-localhost.yml up -d wso2is

# Wait 30-60 seconds, then run setup
python3 helpers/setup_wso2_complete.py
```

## Files Created/Updated

- `helpers/setup_wso2_complete.py` - Main orchestrator
- `tests/test_setup_wso2_complete.py` - Test suite
- `.github/workflows/deploy-wso2.yml` - GitHub Actions workflow
- `doc/WSO2_COMPLETE_SETUP.md` - Full documentation

## Next Steps

After successful setup:

1. **Update `.env`** with client credentials from script output
2. **Restart APIM** (if using): `docker-compose restart wso2apim`
3. **Restart app**: `docker-compose restart darts-app`
4. **Test login** at http://localhost:5000/login

## Support

- Full documentation: [`doc/WSO2_COMPLETE_SETUP.md`](doc/WSO2_COMPLETE_SETUP.md)
- Helper scripts: `helpers/` directory
- WSO2 IS docs: https://is.docs.wso2.com/
