# Deployment Quick Reference

Quick reference for deploying to test and production environments.

## Quick Deploy Commands

### Deploy to Test

```bash
# Merge your changes to test branch
git checkout test
git merge your-feature-branch
git push origin test

# GitHub Actions automatically deploys to test.letsplaydarts.eu
```

### Deploy to Production

```bash
# Merge test to main (after verifying test works)
git checkout main
git merge test
git push origin main

# GitHub Actions automatically deploys to letsplaydarts.eu
```

## Monitoring Deployments

### Watch GitHub Actions

1. Go to https://github.com/dgroen/dartserver-pythonapp/actions
2. Click on the latest workflow run
3. Watch the deployment progress

### Check Server Status

```bash
# Test server
ssh deploy@test.letsplaydarts.eu "cd /opt/dartserver-pythonapp && docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml ps"

# Production server
ssh deploy@letsplaydarts.eu "cd /opt/dartserver-pythonapp && docker-compose -f docker-compose-wso2.yml ps"
```

## Quick Rollback

### Test Environment

```bash
ssh deploy@test.letsplaydarts.eu
cd /opt/dartserver-pythonapp
git log --oneline -5  # Find previous commit
git checkout <previous-commit>
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml down
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d --build
```

### Production Environment

```bash
ssh deploy@letsplaydarts.eu
cd /opt/dartserver-pythonapp
git log --oneline -5  # Find previous commit
git checkout <previous-commit>
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d --build
```

## Common Issues

### SSH Connection Failed
```bash
# Verify secrets are correct
# Check server is accessible
ping test.letsplaydarts.eu
ssh deploy@test.letsplaydarts.eu
```

### Containers Not Starting
```bash
# Check logs
ssh deploy@server
cd /opt/dartserver-pythonapp
docker-compose -f docker-compose-*.yml logs --tail=50
```

### Deployment Timeout
```bash
# Check server resources
ssh deploy@server
df -h  # Check disk space
free -h  # Check memory
docker system prune -a  # Clean up if needed
```

## Health Checks

### Test Environment
```bash
curl -I https://test.letsplaydarts.eu/health
# Should return: 200 OK
```

### Production Environment
```bash
curl -I https://letsplaydarts.eu/health
# Should return: 200 OK
```

## Emergency Contacts

- Repository: https://github.com/dgroen/dartserver-pythonapp
- Issues: https://github.com/dgroen/dartserver-pythonapp/issues
- Actions: https://github.com/dgroen/dartserver-pythonapp/actions

## Full Documentation

- [Deployment Setup Guide](DEPLOYMENT_SETUP.md) - Complete setup instructions
- [Workflow README](../.github/workflows/README.md) - Detailed workflow documentation
