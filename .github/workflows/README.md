# GitHub Actions Deployment Workflows

This directory contains GitHub Actions workflows for automated deployment of the Darts Server application to test and production environments.

## Workflows

### 1. Unified Deployment Pipeline (`deploy-unified.yml`) - **RECOMMENDED**

**Trigger:** Automatic when code is pushed to the `test` branch

**Purpose:** Orchestrated deployment from test to production with manual approval gate

**Process:**
1. **Deploy to Test:**
   - Checks out the code
   - Connects to test server via SSH (through jumphost)
   - Stops containers, pulls latest changes from `test` branch
   - Creates config files from secrets (base64-encoded)
   - Rebuilds and starts containers
   - Verifies deployment

2. **Approval Gate:**
   - Waits for manual approval via GitHub Environments
   - Only proceeds after authorized reviewer approves

3. **Deploy to Production:**
   - Merges `test` branch to `prod` branch
   - Connects to production server via SSH (through jumphost)
   - Creates timestamped backup
   - Deploys using same process as test
   - Runs health checks

**Benefits:**
- Single workflow ensures test and production deploy the same code
- Manual approval gate prevents accidental production deployments
- Automatic merge from test to prod after approval
- Built-in rollback information in backups

### 2. Deploy to Test Environment (`deploy-test.yml`)

**Trigger:** Automatic deployment when code is merged to the `test` branch

**Purpose:** Deploys the application to the test server at `test.letsplaydarts.eu`

**Process:**
1. Checks out the code
2. Connects to test server via SSH
3. Pulls latest changes from `test` branch
4. Stops existing containers
5. Rebuilds all containers with no cache
6. Starts containers using `docker-compose-test.yml` configuration
7. Verifies containers are running

**Note:** This workflow is standalone. Use the unified pipeline for test→prod deployments.

### 3. Deploy to Production Environment (`deploy-production.yml`)

**Trigger:** Automatic deployment when code is merged to the `prod` branch

**Purpose:** Deploys the application to the production server at `letsplaydarts.eu`

**Process:**
1. Checks out the code
2. Connects to production server via SSH (through jumphost if configured)
3. Creates a backup of the current state (commit hash, deployment.toml, .env)
4. Stops existing containers
5. Pulls latest changes from `prod` branch
6. Creates `deployment.toml` and `.env` files from GitHub secrets (base64-encoded)
7. Rebuilds all containers with no cache
8. Starts containers using `docker-compose-wso2.yml` configuration
9. Verifies containers are running
10. Runs health checks on the application

**Note:** This workflow is standalone. Use the unified pipeline for automated test→prod deployments.

## Recommended Deployment Strategy

**Use the Unified Pipeline (`deploy-unified.yml`)** for most deployments:

1. Push to `test` branch → automatic test deployment
2. Review test environment
3. Approve in GitHub Actions → automatic production deployment
4. Production branch (`prod`) is automatically updated

**Use standalone workflows** only for:
- Emergency production hotfixes (deploy-production.yml)
- Testing deployment pipeline changes (deploy-test.yml)

## Prerequisites

### Server Setup

Both test and production servers must have:

1. **Git repository cloned** in one of these locations:
   - `/opt/dartserver-pythonapp` (recommended)
   - `~/dartserver-pythonapp` (alternative)

2. **Docker and Docker Compose installed**
   - Docker version 20.10 or higher
   - Docker Compose version 2.0 or higher

3. **SSH access configured** for the deployment user
   - User must have permissions to run Docker commands
   - SSH key authentication enabled

4. **Required files present on server:**
   - `docker-compose-wso2.yml` (base configuration)
   - `docker-compose-test.yml` (test environment overrides)
   - `.env` files with proper environment-specific configurations
   - SSL certificates in `nginx/` directory (if using HTTPS)

### GitHub Secrets Configuration

The following secrets must be configured in the GitHub repository:

#### Jumphost Secrets (for servers behind a jumphost/bastion)

| Secret Name | Description | Example |
|------------|-------------|---------|
| `JUMPHOST_HOST` | Hostname or IP of jumphost/bastion server | `strato.vdi.prd` |
| `JUMPHOST_USER` | SSH username for jumphost | `vagrant` or `ubuntu` |
| `JUMPHOST_SSH_KEY` | Private SSH key for jumphost authentication | Contents of `~/.ssh/id_rsa` |

#### Test Environment Secrets

| Secret Name | Description | Example |
|------------|-------------|---------|
| `TEST_SERVER_HOST` | Hostname or IP of test server (behind jumphost if configured) | `127.0.0.1` or `test.letsplaydarts.eu` |
| `TEST_SERVER_PORT` | SSH port on test server | `22` or `4423` |
| `TEST_SERVER_USER` | SSH username for test server | `deploy` or `vagrant` |
| `TEST_SERVER_SSH_KEY` | Private SSH key for test server authentication | Contents of `~/.ssh/id_rsa` |
| `TEST_WSO2IS_DEPLOYMENT_TOML` | Complete deployment.toml configuration for WSO2 IS test instance | File contents of `wso2is-7-config/deployment.toml` |
| `TEST_ENV` | Environment variables for test deployment (e.g., database URL, API keys) | Contents of `.env` file for test environment |

#### Production Environment Secrets

| Secret Name | Description | Example |
|------------|-------------|---------|
| `PROD_SERVER_HOST` | Hostname or IP of production server (behind jumphost if configured) | `letsplaydarts.eu` or `192.168.1.101` |
| `PROD_SERVER_PORT` | SSH port on production server | `22` or `4422` |
| `PROD_SERVER_USER` | SSH username for production server | `deploy` or `ubuntu` |
| `PROD_SERVER_SSH_KEY` | Private SSH key for production server authentication | Contents of `~/.ssh/id_rsa` |
| `PROD_WSO2IS_DEPLOYMENT_TOML` | Complete deployment.toml configuration for WSO2 IS production instance | File contents of `wso2is-7-config/deployment.toml` |
| `PROD_ENV` | Environment variables for production deployment (e.g., database URL, API keys) | Contents of `.env` file for production environment |

### Setting Up GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its name and value

### Setting Up GitHub Environments for Approval

The unified pipeline requires GitHub Environments to be configured for the approval gate:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Click **New environment**
4. Create an environment named `production-approval`
5. Configure **Required reviewers**:
   - Check "Required reviewers"
   - Add yourself and/or team members who can approve production deployments
   - Recommended: Add at least 2 reviewers for critical production changes
6. Optionally set **Wait timer** (e.g., 5 minutes minimum before approval can be given)
7. Click **Save protection rules**
8. Create another environment named `production` (for the final deployment step):
   - This can have the same or different reviewers
   - Or leave it without protection if approval gate is sufficient

**How the approval works:**
1. Test deployment completes successfully
2. Workflow pauses at the approval gate
3. Designated reviewers receive a notification
4. Reviewers can inspect the test environment
5. Reviewer approves or rejects the deployment
6. If approved, production deployment proceeds automatically
7. If rejected, workflow stops

#### Generating SSH Keys

If you don't have SSH keys set up:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-deploy-key" -f ~/.ssh/github_deploy_key

# Copy the public key to the server
ssh-copy-id -i ~/.ssh/github_deploy_key.pub user@server-host

# Test the connection
ssh -i ~/.ssh/github_deploy_key user@server-host

# Copy the PRIVATE key content for GitHub secrets
cat ~/.ssh/github_deploy_key
# Copy the entire output including BEGIN and END lines
```

#### Preparing Configuration File Secrets

The deployment workflow creates configuration files from GitHub secrets. You need to prepare these secrets:

**1. Preparing TEST_WSO2IS_DEPLOYMENT_TOML**

This secret should contain the complete contents of the WSO2 IS `deployment.toml` configuration file:

```bash
# If you have the file locally
cat wso2is-7-config/deployment.toml

# Copy the entire output and paste into GitHub secret TEST_WSO2IS_DEPLOYMENT_TOML
```

**2. Preparing TEST_ENV**

This secret should contain the environment variables for your test deployment:

```bash
# Create or edit your test .env file with necessary variables:
# Example content:
# WSO2_CLIENT_ID=your_client_id
# WSO2_CLIENT_SECRET=your_secret
# DATABASE_URL=postgresql://user:pass@host:5432/db
# RABBITMQ_PASSWORD=guest
# WSO2_IS_INTROSPECT_PASSWORD=admin_password
# etc.

# Copy the entire contents and paste into GitHub secret TEST_ENV
```

**Important:** Store sensitive values in these secrets, not in your repository files.

## Usage

### Using the Unified Pipeline (Recommended)

1. **Deploy to Test and trigger approval workflow:**
   ```bash
   git checkout test
   git merge your-feature-branch
   git push origin test
   ```

2. **Monitor test deployment** in the **Actions** tab

3. **Review the test environment** at `test.letsplaydarts.eu`

4. **Approve production deployment:**
   - Go to the **Actions** tab
   - Click on the running workflow
   - Click **Review deployments**
   - Select `production-approval` environment
   - Click **Approve and deploy**

5. **Monitor production deployment** - it will proceed automatically after approval

### Deploying to Test Only

**If using standalone workflow:**

1. Merge your changes to the `test` branch:
   ```bash
   git checkout test
   git merge your-feature-branch
   git push origin test
   ```

2. The workflow will automatically trigger and deploy to the test server

3. Monitor the deployment in the **Actions** tab of your GitHub repository

**Note:** When using the unified pipeline, test deployments happen automatically as part of the approval workflow.

### Deploying to Production Only (Emergency Hotfix)

**Only use this for emergency hotfixes that bypass test:**

1. Merge your changes directly to the `prod` branch:
   ```bash
   git checkout prod
   git merge test  # Merge from test after verification
   git push origin prod
   ```

2. The workflow will automatically trigger and deploy to the production server

3. Monitor the deployment in the **Actions** tab

## Monitoring Deployments

### Via GitHub Actions UI

1. Go to the **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. View the step-by-step execution logs
4. Check for any errors or warnings

### Via Server Logs

SSH into the server and check logs:

```bash
# View container logs
docker-compose -f docker-compose-wso2.yml logs -f

# View specific service logs
docker-compose -f docker-compose-wso2.yml logs -f darts-app

# Check container status
docker-compose -f docker-compose-wso2.yml ps
```

## Troubleshooting

### Jumphost SSH Configuration

If your deployment server is behind a jumphost/bastion server, ensure:

1. Both jumphost and target server SSH keys are configured as separate secrets
2. The SSH config in the workflow file uses `ProxyJump` to tunnel through the jumphost
3. Verify connectivity from your local machine first:
   ```bash
   # Test jumphost connection
   ssh -i ~/.ssh/jumphost_key jumphost_user@jumphost_host
   
   # Test target server through jumphost
   ssh -i ~/.ssh/target_key -J jumphost_user@jumphost_host target_user@target_host:target_port
   ```

### Deployment Fails with SSH Connection Error

**Problem:** Cannot connect to server via SSH

**Solutions:**
1. Verify the server is accessible: `ping $SERVER_HOST`
2. Check SSH key is correct in GitHub secrets
3. Ensure SSH key has correct permissions (600)
4. Verify user has access to the server
5. Check firewall rules allow SSH (port 22)

### Deployment Fails with "Directory Not Found"

**Problem:** Application directory doesn't exist on server

**Solutions:**
1. Clone the repository to the server:
   ```bash
   sudo git clone https://github.com/dgroen/dartserver-pythonapp.git /opt/dartserver-pythonapp
   ```
2. Ensure the path matches what's in the workflow file

### Containers Fail to Start

**Problem:** Docker containers don't start after deployment

**Solutions:**
1. Check Docker logs: `docker-compose logs`
2. Verify environment variables are set correctly
3. Check if required ports are available
4. Ensure Docker daemon is running: `sudo systemctl status docker`
5. Check disk space: `df -h`

### Health Check Fails

**Problem:** Application health endpoint returns non-200 status

**Solutions:**
1. Check application logs: `docker-compose logs darts-app`
2. Verify database connection
3. Ensure RabbitMQ is running
4. Check WSO2 services are healthy

### Build Takes Too Long or Times Out

**Problem:** Docker build step times out

**Solutions:**
1. Increase timeout in workflow (add `timeout-minutes: 30` to job)
2. Check server resources (CPU, RAM, disk)
3. Consider using Docker layer caching
4. Clean up old images: `docker system prune -a`

## Rollback Procedure

### Test Environment

If a test deployment fails or introduces issues:

```bash
# SSH into test server
ssh user@test-server

# Navigate to app directory
cd /opt/dartserver-pythonapp

# Checkout previous commit
git log --oneline  # Find the previous working commit
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml down
docker-compose -f docker-compose-wso2.yml -f docker-compose-test.yml up -d --build
```

### Production Environment

Production deployments create automatic backups:

```bash
# SSH into production server
ssh user@production-server

# Navigate to app directory
cd /opt/dartserver-pythonapp

# View available backups
ls -la backups/

# Restore from backup
git checkout <commit-from-backup>

# Rebuild and restart
docker-compose -f docker-compose-wso2.yml down
docker-compose -f docker-compose-wso2.yml up -d --build
```

## Security Considerations

1. **SSH Keys**: Store private keys only in GitHub secrets, never commit to repository
2. **Environment Variables**: Sensitive values should be in `.env` files on servers, not in repository
3. **Access Control**: Use GitHub environments and required reviewers for production
4. **Audit Trail**: All deployments are logged in GitHub Actions history
5. **Secrets Rotation**: Regularly rotate SSH keys and update GitHub secrets

## Customization

### Changing Deployment Paths

Edit the workflows to use different paths:

```yaml
# In deploy-test.yml or deploy-production.yml
cd /your/custom/path || { echo "❌ Application directory not found"; exit 1; }
```

### Adding Deployment Notifications

Add notification steps to workflows:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Adding Pre-deployment Tests

Add test steps before deployment:

```yaml
- name: Run Tests
  run: |
    python -m pytest tests/
```

## Maintenance

### Regular Tasks

1. **Weekly:** Review deployment logs for errors or warnings
2. **Monthly:** Update Docker images and rebuild
3. **Quarterly:** Rotate SSH keys and update secrets
4. **As Needed:** Clean up old Docker images and backups

### Updating Workflows

To modify the deployment process:

1. Create a feature branch
2. Update workflow files
3. Test changes on test environment first
4. Merge to main after verification

## Support

For issues with the deployment pipeline:

1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Check server logs via SSH
4. Create an issue in the repository with:
   - Workflow run link
   - Error messages
   - Steps to reproduce

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SSH Key Authentication](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
