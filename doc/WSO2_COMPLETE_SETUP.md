# WSO2 Complete Setup Script

Comprehensive setup orchestrator for WSO2 Identity Server deployments across all environments.

## Overview

The `setup_wso2_complete.py` script automates the complete WSO2 IS configuration process:

1. **Wait for WSO2 IS** - Ensures WSO2 is ready before proceeding
2. **Setup Roles & Users** - Creates required groups and users via SCIM2
3. **Configure APIM OAuth Clients** - Registers OAuth2 clients for APIM via DCR
4. **Register DartsApp** - Registers the main application OAuth2 client
5. **Configure Redirect URIs** - Updates callback and post-logout URLs
6. **Validate Setup** - Verifies all components are configured correctly

## Usage

### Basic Usage

```bash
# Development environment (default)
python3 helpers/setup_wso2_complete.py

# Test environment
python3 helpers/setup_wso2_complete.py --env test --env-file .env.test

# Production environment
python3 helpers/setup_wso2_complete.py --env production --env-file .env.production
```

### Advanced Options

```bash
# Skip specific steps
python3 helpers/setup_wso2_complete.py --skip-roles --skip-apim

# Run without validation
python3 helpers/setup_wso2_complete.py --no-validate

# Verbose output
python3 helpers/setup_wso2_complete.py --verbose

# Skip waiting for WSO2 (if already running)
python3 helpers/setup_wso2_complete.py --skip-wait
```

### All Available Flags

| Flag               | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| `--env`            | Target environment: development, test, staging, production |
| `--env-file`       | Path to environment file (auto-detected if not specified)  |
| `--skip-wait`      | Skip waiting for WSO2 to be ready                          |
| `--skip-roles`     | Skip roles and users setup                                 |
| `--skip-apim`      | Skip APIM OAuth clients setup                              |
| `--skip-darts-app` | Skip DartsApp registration                                 |
| `--skip-redirects` | Skip redirect URIs configuration                           |
| `--no-validate`    | Skip validation after setup                                |
| `--verbose`        | Enable verbose logging                                     |

## Environment Configuration

The script automatically detects environment files based on the `--env` flag:

- `development` → `.env`
- `test` → `.env.test`
- `staging` → `.env.staging`
- `production` → `.env.production`

### Required Environment Variables

```bash
# WSO2 IS Configuration
WSO2_IS_URL=https://localhost:9443
WSO2_IS_INTERNAL_URL=https://wso2is:9443  # For container-to-container
WSO2_ADMIN_USERNAME=admin
WSO2_ADMIN_PASSWORD=admin
WSO2_IS_VERIFY_SSL=False

# Application Configuration
WSO2_CLIENT_ID=your_client_id
WSO2_CLIENT_SECRET=your_client_secret
WSO2_REDIRECT_URI=https://localhost:5000/callback
WSO2_POST_LOGOUT_REDIRECT_URI=https://localhost:5000/
```

## GitHub Actions Integration

Use the provided workflow for automated deployments:

```yaml
# .github/workflows/deploy-wso2.yml
name: Deploy WSO2 Environment

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - test
          - staging
          - production
```

### Trigger Deployment

1. Go to GitHub Actions tab
2. Select "Deploy WSO2 Environment" workflow
3. Click "Run workflow"
4. Select target environment
5. Optionally skip APIM setup or validation

### Required GitHub Secrets

Configure these secrets per environment:

- `WSO2_IS_URL` - Public WSO2 IS URL
- `WSO2_IS_INTERNAL_URL` - Internal WSO2 IS URL (for containers)
- `WSO2_ADMIN_USERNAME` - WSO2 admin username
- `WSO2_ADMIN_PASSWORD` - WSO2 admin password
- `WSO2_CLIENT_ID` - OAuth2 client ID
- `WSO2_CLIENT_SECRET` - OAuth2 client secret
- `WSO2_REDIRECT_URI` - Application callback URL
- `WSO2_POST_LOGOUT_REDIRECT_URI` - Post-logout redirect URL
- `WSO2_IS_VERIFY_SSL` - SSL verification (true/false)
- `DEPLOY_SSH_KEY` - SSH private key for remote deployment
- `DEPLOY_SERVER_HOST` - Target server hostname
- `DEPLOY_SERVER_PORT` - SSH port (default: 22)
- `DEPLOY_SERVER_USER` - SSH user

## Exit Codes

- `0` - Success
- `1` - Failure (check logs for details)

## Validation Checks

The script validates:

✅ WSO2 IS is accessible  
✅ DartsApp exists and has OIDC configuration  
✅ All APIM OAuth clients exist (KeyManager, Publisher, DevPortal, Admin)  

## Troubleshooting

### WSO2 Not Ready

```bash
# Check WSO2 IS logs
docker-compose logs wso2is

# Verify WSO2 is accessible
curl -k https://localhost:9443/carbon/admin/login.jsp
```

### DartsApp Registration Failed

```bash
# Re-run only DartsApp registration
python3 helpers/setup_wso2_complete.py --skip-wait --skip-roles --skip-apim --skip-redirects
```

### APIM OAuth Clients Failed

```bash
# Re-run only APIM setup
python3 helpers/setup_wso2_complete.py --skip-wait --skip-roles --skip-darts-app --skip-redirects
```

### Validation Failed

```bash
# Run validation separately
python3 helpers/setup_wso2_complete.py --skip-wait --skip-roles --skip-apim --skip-darts-app --skip-redirects
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_setup_wso2_complete.py -v

# Run with coverage
pytest tests/test_setup_wso2_complete.py --cov=helpers.setup_wso2_complete --cov-report=html
```

## Pre-commit Integration

The script follows all repository guidelines:

```bash
# Run pre-commit checks
pre-commit run --all-files

# Run linting
ruff check helpers/setup_wso2_complete.py

# Run type checking
mypy helpers/setup_wso2_complete.py
```

## Integration with Existing Scripts

The orchestrator calls these existing helpers in sequence:

1. `helpers/setup_wso2_roles.py` - User/role management
2. `helpers/configure_wso2_oauth_apps.py` - APIM OAuth clients
3. `helpers/register_darts_app.py` - DartsApp registration
4. `helpers/configure_wso2_redirects.py` - Redirect URI configuration

Each can still be run independently if needed.

## Example: Full Deployment Flow

```bash
# 1. Start WSO2 stack
docker-compose -f docker-compose-wso2.yml up -d

# 2. Wait for services to be ready (30-60 seconds)
docker-compose logs -f wso2is

# 3. Run complete setup
python3 helpers/setup_wso2_complete.py --env production --env-file .env.production

# 4. Restart APIM to pick up new credentials
docker-compose restart wso2apim

# 5. Update DartsApp .env with client credentials
# (Client ID and Secret are printed by the script)

# 6. Restart application
docker-compose restart darts-app

# 7. Test login flow
open https://your-domain.com/login
```

## CI/CD Best Practices

### Pre-deployment Checklist

- ✅ All secrets configured in GitHub
- ✅ Environment file validated
- ✅ WSO2 IS accessible from deployment server
- ✅ Database initialized
- ✅ Network connectivity verified

### Post-deployment Verification

```bash
# Check all services are running
docker-compose ps

# Verify WSO2 applications
curl -k https://localhost:9443/api/server/v1/applications \
  -u admin:admin | jq '.applications[].name'

# Test login flow
curl -k https://your-domain.com/login
```

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review helper script documentation in `helpers/`
3. Check WSO2 IS logs: `docker-compose logs wso2is`
4. Review application logs: `docker-compose logs darts-app`
