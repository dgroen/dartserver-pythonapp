# Deployment Setup Guide

This guide walks you through setting up the automated deployment pipeline for the Darts Server application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [SSH Key Generation](#ssh-key-generation)
4. [GitHub Secrets Configuration](#github-secrets-configuration)
5. [Testing the Pipeline](#testing-the-pipeline)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before setting up the deployment pipeline, ensure you have:

- Administrator access to the GitHub repository
- SSH access to both test and production servers
- Docker and Docker Compose installed on both servers
- Git installed on both servers

## Server Setup

### 1. Clone Repository on Servers

On **both test and production servers**, clone the repository:

```bash
# Option 1: Clone to /opt (recommended, requires sudo)
sudo mkdir -p /opt
sudo git clone https://github.com/dgroen/dartserver-pythonapp.git /opt/dartserver-pythonapp
sudo chown -R $USER:$USER /opt/dartserver-pythonapp

# Option 2: Clone to home directory
git clone https://github.com/dgroen/dartserver-pythonapp.git ~/dartserver-pythonapp
```

### 2. Create Deployment User

Create a dedicated user for deployments (recommended for security):

```bash
# On each server
sudo adduser deploy
sudo usermod -aG docker deploy  # Add to docker group

# Allow the user to run docker without sudo
sudo usermod -aG docker deploy

# Test docker access
sudo -u deploy docker ps
```

### 3. Set Up Directory Permissions

```bash
# If using /opt
sudo chown -R deploy:deploy /opt/dartserver-pythonapp

# If using home directory
chown -R deploy:deploy ~/dartserver-pythonapp
```

### 4. Install Docker and Docker Compose

If not already installed:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose (if using older Docker version)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## SSH Key Generation

### 1. Generate SSH Keys for Deployment

On your **local machine**, generate SSH keys for each environment:

```bash
# For test environment
ssh-keygen -t ed25519 -C "github-deploy-test" -f ~/.ssh/github_deploy_test
# Press Enter for no passphrase (required for automated deployment)

# For production environment
ssh-keygen -t ed25519 -C "github-deploy-prod" -f ~/.ssh/github_deploy_prod
# Press Enter for no passphrase (required for automated deployment)
```

### 2. Copy Public Keys to Servers

Copy the public keys to the respective servers:

```bash
# For test server
ssh-copy-id -i ~/.ssh/github_deploy_test.pub deploy@test.letsplaydarts.eu
# Or if using IP:
ssh-copy-id -i ~/.ssh/github_deploy_test.pub deploy@<TEST_SERVER_IP>

# For production server
ssh-copy-id -i ~/.ssh/github_deploy_prod.pub deploy@letsplaydarts.eu
# Or if using IP:
ssh-copy-id -i ~/.ssh/github_deploy_prod.pub deploy@<PROD_SERVER_IP>
```

### 3. Test SSH Access

Verify you can connect without password:

```bash
# Test test server
ssh -i ~/.ssh/github_deploy_test deploy@test.letsplaydarts.eu

# Test production server
ssh -i ~/.ssh/github_deploy_prod deploy@letsplaydarts.eu
```

### 4. Get Private Key Contents

Get the private key contents to add to GitHub secrets:

```bash
# For test environment
cat ~/.ssh/github_deploy_test
# Copy the ENTIRE output including BEGIN and END lines

# For production environment
cat ~/.ssh/github_deploy_prod
# Copy the ENTIRE output including BEGIN and END lines
```

## GitHub Secrets Configuration

### 1. Navigate to Repository Secrets

1. Go to your GitHub repository: https://github.com/dgroen/dartserver-pythonapp
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 2. Add Test Environment Secrets

Add the following secrets for the test environment:

| Secret Name | Value | Example |
|------------|-------|---------|
| `TEST_SERVER_HOST` | Test server hostname or IP | `test.letsplaydarts.eu` or `192.168.1.100` |
| `TEST_SERVER_USER` | SSH username | `deploy` |
| `TEST_SERVER_SSH_KEY` | Contents of `~/.ssh/github_deploy_test` | (paste entire private key) |

**Steps to add each secret:**
1. Click **New repository secret**
2. Enter the **Name** (e.g., `TEST_SERVER_HOST`)
3. Enter the **Value**
4. Click **Add secret**

### 3. Add Production Environment Secrets

Add the following secrets for the production environment:

| Secret Name | Value | Example |
|------------|-------|---------|
| `PROD_SERVER_HOST` | Production server hostname or IP | `letsplaydarts.eu` or `192.168.1.101` |
| `PROD_SERVER_USER` | SSH username | `deploy` |
| `PROD_SERVER_SSH_KEY` | Contents of `~/.ssh/github_deploy_prod` | (paste entire private key) |

### 4. Verify Secrets

After adding all secrets, you should see:
- ✅ TEST_SERVER_HOST
- ✅ TEST_SERVER_USER
- ✅ TEST_SERVER_SSH_KEY
- ✅ PROD_SERVER_HOST
- ✅ PROD_SERVER_USER
- ✅ PROD_SERVER_SSH_KEY

## Testing the Pipeline

### Test Environment Deployment

1. Create a test branch if it doesn't exist:
   ```bash
   git checkout -b test
   git push origin test
   ```

2. Make a test change and push to test branch:
   ```bash
   git checkout test
   # Make a small change (e.g., update README)
   echo "Test deployment" >> README.md
   git add README.md
   git commit -m "Test deployment pipeline"
   git push origin test
   ```

3. Monitor the deployment:
   - Go to **Actions** tab in GitHub
   - Click on the "Deploy to Test Environment" workflow run
   - Watch the steps execute
   - Verify all steps complete successfully

4. Verify on test server:
   ```bash
   ssh deploy@test.letsplaydarts.eu
   cd /opt/dartserver-pythonapp
   git log -1  # Should show your test commit
   docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml ps
   # All containers should be running
   ```

### Production Environment Deployment

1. After verifying test deployment works:
   ```bash
   git checkout main
   git merge test
   git push origin main
   ```

2. Monitor the deployment:
   - Go to **Actions** tab in GitHub
   - Click on the "Deploy to Production Environment" workflow run
   - Watch the steps execute
   - Verify all steps complete successfully

3. Verify on production server:
   ```bash
   ssh deploy@letsplaydarts.eu
   cd /opt/dartserver-pythonapp
   git log -1  # Should show your commit
   docker-compose -f docker-compose-wso2.yml ps
   # All containers should be running
   ```

4. Test the application:
   - Visit https://letsplaydarts.eu
   - Verify the application is accessible
   - Test core functionality

## Troubleshooting

### Issue: SSH Connection Failed

**Error:** `Permission denied (publickey)`

**Solution:**
1. Verify SSH key was added to server:
   ```bash
   ssh deploy@server-host cat ~/.ssh/authorized_keys
   ```
2. Check GitHub secret contains the complete private key (including BEGIN/END lines)
3. Verify user has correct permissions on the server

### Issue: Directory Not Found

**Error:** `Application directory not found`

**Solution:**
1. Verify repository is cloned on server:
   ```bash
   ssh deploy@server-host ls -la /opt/dartserver-pythonapp
   ```
2. If not present, clone it:
   ```bash
   ssh deploy@server-host
   sudo git clone https://github.com/dgroen/dartserver-pythonapp.git /opt/dartserver-pythonapp
   sudo chown -R deploy:deploy /opt/dartserver-pythonapp
   ```

### Issue: Docker Permission Denied

**Error:** `permission denied while trying to connect to the Docker daemon`

**Solution:**
1. Add user to docker group:
   ```bash
   ssh deploy@server-host
   sudo usermod -aG docker $USER
   newgrp docker  # Or logout and login again
   ```
2. Verify docker access:
   ```bash
   docker ps
   ```

### Issue: Containers Fail to Start

**Error:** Containers exit immediately or don't start

**Solution:**
1. Check Docker logs:
   ```bash
   ssh deploy@server-host
   cd /opt/dartserver-pythonapp
   docker-compose -f docker-compose-wso2.yml logs --tail=100
   ```
2. Verify environment variables are set
3. Check required services (database, RabbitMQ) are running
4. Verify ports are available

### Issue: Workflow Times Out

**Error:** Workflow exceeds time limit

**Solution:**
1. Check server resources (CPU, RAM, disk space)
2. Clean up old Docker images:
   ```bash
   ssh deploy@server-host
   docker system prune -a -f
   ```
3. Consider increasing timeout in workflow:
   ```yaml
   jobs:
     deploy-test:
       timeout-minutes: 30  # Add this line
   ```

## Security Best Practices

1. **SSH Keys**
   - Use separate keys for test and production
   - Never commit private keys to repository
   - Rotate keys periodically (every 6 months)
   - Use passphrase-less keys only for automated deployments

2. **GitHub Secrets**
   - Limit repository access to necessary users
   - Use GitHub environments for production deployments
   - Require approvals for production deployments
   - Audit secret access regularly

3. **Server Security**
   - Keep servers updated: `sudo apt update && sudo apt upgrade`
   - Use firewall: `sudo ufw enable`
   - Disable password authentication: Edit `/etc/ssh/sshd_config`
   - Monitor server logs: `sudo journalctl -u ssh -f`

4. **Application Security**
   - Store sensitive values in `.env` files on servers
   - Never commit secrets to repository
   - Use HTTPS for all production traffic
   - Regularly update Docker images

## Maintenance

### Weekly

- Review deployment logs for errors
- Check server disk space
- Monitor application performance

### Monthly

- Update base Docker images
- Review and rotate logs
- Test rollback procedures

### Quarterly

- Rotate SSH keys
- Review and update secrets
- Test disaster recovery procedures
- Update documentation

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SSH Key Management](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Workflow README](.github/workflows/README.md)

## Support

If you encounter issues not covered in this guide:

1. Check the [workflow README](.github/workflows/README.md) for detailed troubleshooting
2. Review GitHub Actions logs for specific error messages
3. SSH into the server and check application logs
4. Create an issue in the repository with:
   - Workflow run link
   - Server logs
   - Steps to reproduce
   - Expected vs actual behavior
