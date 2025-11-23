# GitHub Actions Deployment Workflows

This directory contains GitHub Actions workflows for automated deployment of the Darts Server application to test and production environments.

## Workflows

### Active Workflow

#### Unified Deployment Pipeline (`deploy-unified.yml`) - **ACTIVE**

**Trigger:** Automatic when code is pushed to the `test` branch

**Purpose:** Orchestrated deployment from test to production with manual approval gates and comprehensive backup/restore capabilities

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

3. **Backup Production:**
   - Creates full backup of all Docker volumes before deployment
   - Backs up: postgres_data, rabbitmq_data, wso2is_data, wso2apim_data
   - Creates PostgreSQL database dump (pg_dump)
   - Stores backup path for potential restore operations
   - Uses `helpers/backup_docker_volumes.sh` script

4. **Deploy to Production:**
   - Merges `test` branch to `prod` branch
   - Connects to production server via SSH (through jumphost)
   - Deploys using same process as test
   - Runs health checks

5. **Automatic Restore on Failure:**
   - **Triggers only if deployment fails**
   - Automatically restores from backup created in step 3
   - Uses `helpers/restore_docker_volumes.sh` script
   - Restores all volumes and database
   - Verifies restored deployment
   - No manual intervention required

6. **Post-Deployment Verification:**
   - **Requires manual verification** after successful deployment
   - Uses `production-verification` environment
   - Options:
     - ✅ **Approve:** Deployment is working properly → Pipeline completes
     - ❌ **Reject:** Needs rollback → Proceeds to manual rollback step

7. **Manual Rollback (if verification fails):**
   - Triggers if verification is rejected or cancelled
   - Requires confirmation via `production-rollback` environment
   - Restores production to backup created in step 3
   - Verifies rollback success

**Benefits:**
- Single workflow ensures test and production deploy the same code
- Manual approval gate prevents accidental production deployments
- **Automatic backup before every production deployment**
- **Automatic restore if deployment fails**
- **Post-deployment verification with manual rollback option**
- Comprehensive backup includes all volumes and database dumps
- Built-in restore scripts for easy recovery
- Automatic merge from test to prod after approval

---

### Disabled Workflows (Available for Reference)

The following workflows are **disabled** (renamed with `.disabled` extension) but kept for reference or emergency use:

#### Deploy to Test Environment (`deploy-test.yml.disabled`)

**Status:** DISABLED

**Original Trigger:** Automatic deployment when code is merged to the `test` branch

**Purpose:** Deploys the application to the test server at `test.letsplaydarts.eu`

**Note:** This workflow is disabled. Use the unified pipeline instead. To re-enable for emergency use, rename to `deploy-test.yml`.

#### Deploy to Production Environment (`deploy-production.yml.disabled`)

**Status:** DISABLED

**Original Trigger:** Automatic deployment when code is pushed to the `prod` branch

**Purpose:** Deploys the application to the production server at `letsplaydarts.eu`

**Note:** This workflow is disabled. Use the unified pipeline instead. To re-enable for emergency hotfix, rename to `deploy-production.yml`.

**How to re-enable disabled workflows (emergency only):**
```bash
# Re-enable test workflow
cd .github/workflows
mv deploy-test.yml.disabled deploy-test.yml

# Re-enable production workflow  
mv deploy-production.yml.disabled deploy-production.yml

# Push changes
git add .
git commit -m "Re-enable emergency workflow"
git push
```

---

## Recommended Deployment Strategy

**Use the Unified Pipeline (`deploy-unified.yml`)** for all deployments:

1. Push to `test` branch → automatic test deployment
2. Review test environment
3. Approve in GitHub Actions → automatic production deployment
4. Production branch (`prod`) is automatically updated

**Only re-enable standalone workflows for:**
- Emergency production hotfixes that must bypass test
- Debugging workflow issues
- Recovering from failed unified pipeline runs

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

The unified pipeline requires GitHub Environments to be configured for approval gates:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**

#### Environment 1: `production-approval` (Pre-Deployment Approval)

3. Click **New environment**
4. Create an environment named `production-approval`
5. Configure **Required reviewers**:
   - Check "Required reviewers"
   - Add yourself and/or team members who can approve production deployments
   - Recommended: Add at least 1-2 reviewers for critical production changes
6. Optionally set **Wait timer** (e.g., 5 minutes minimum before approval can be given)
7. Click **Save protection rules**

#### Environment 2: `production` (Deployment Target)

8. Create another environment named `production`
9. Configure environment URL: `https://letsplaydarts.eu`
10. Optionally add reviewers or leave without protection (pre-deployment approval is primary gate)

#### Environment 3: `production-verification` (Post-Deployment Verification)

11. Create environment named `production-verification`
12. Configure **Required reviewers**:
   - Add reviewers who will verify deployment success
   - These can be same or different from pre-deployment reviewers
13. Click **Save protection rules**

#### Environment 4: `production-rollback` (Manual Rollback Confirmation)

14. Create environment named `production-rollback`
15. Configure **Required reviewers**:
   - Add reviewers authorized to approve rollbacks
   - Recommended: Use senior team members for rollback decisions
16. Click **Save protection rules**

**How the approval gates work:**
1. **Pre-Deployment:** Test deployment completes → workflow pauses at `production-approval`
   - Reviewers inspect test environment
   - Approve or reject production deployment
   - If approved → backup is created → production deployment proceeds

2. **Automatic Restore:** If deployment **fails**
   - No approval needed
   - Automatically restores from backup
   - Verifies restoration

3. **Post-Deployment Verification:** If deployment **succeeds**
   - Workflow pauses at `production-verification`
   - Reviewers verify production is working correctly
   - Options:
     - ✅ Approve → Pipeline completes successfully
     - ❌ Reject → Proceeds to rollback step

4. **Manual Rollback:** If verification is rejected
   - Workflow pauses at `production-rollback`
   - Requires final confirmation to rollback
   - If approved → restores from backup
   - Verifies rollback success

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

### Using the Unified Pipeline (Standard Process)

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

### Emergency: Using Standalone Workflows

**Only use this if the unified pipeline is broken or for critical hotfixes.**

1. Re-enable the needed workflow (see instructions above)
2. Push to the appropriate branch (`test` or `prod`)
3. Monitor in Actions tab
4. **Remember to disable again after use**

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

### Automatic Rollback (Deployment Failure)

If a production deployment **fails** (containers don't start, health check fails, etc.):

- ✅ **Automatic restore is triggered immediately**
- No manual intervention required
- The workflow automatically:
  1. Retrieves the backup path created before deployment
  2. Runs `helpers/restore_docker_volumes.sh` with the backup
  3. Restores all volumes and database
  4. Starts containers
  5. Verifies restoration success

**You will receive a notification that automatic restore completed.**

### Manual Rollback (Post-Deployment Issues)

If a production deployment **succeeds technically** but has issues discovered during verification:

1. **During the verification step** in GitHub Actions:
   - Go to the running workflow in the **Actions** tab
   - Click **Review deployments** at the `production-verification` step
   - Click **Reject** to trigger manual rollback

2. **The workflow will pause** at `production-rollback` environment:
   - Click **Review deployments** again
   - Review the rollback confirmation message
   - Click **Approve** to confirm rollback

3. **Rollback will execute** automatically:
   - Restores from the backup created before deployment
   - Uses `helpers/restore_docker_volumes.sh`
   - Starts containers with previous state
   - Verifies rollback success

### Manual Rollback (Outside GitHub Actions)

If you need to rollback **outside the automated workflow**:

```bash
# SSH into production server
ssh user@production-server

# Navigate to app directory
cd /opt/dartserver-pythonapp

# View available backups
ls -lt docker-backups/

# The backup format is: docker-backups/YYYY-MM-DD_HH-MM-SS/
# Find the backup from before the problematic deployment

# Run restore script
chmod +x helpers/restore_docker_volumes.sh
./helpers/restore_docker_volumes.sh -b docker-backups/2024-01-15_14-30-00/

# The script will:
# - Stop containers
# - Restore all volumes
# - Restore PostgreSQL database
# - Start containers
# - Show status

# Verify restoration
docker-compose -f docker-compose-wso2.yml ps
```

### Backup Management

**Backup locations:**
- All backups are stored in: `/opt/dartserver-pythonapp/docker-backups/`
- Format: `YYYY-MM-DD_HH-MM-SS/`
- Each backup contains:
  - `postgres_data.tar.gz` - PostgreSQL volume
  - `postgres_dump.sql.gz` - Database SQL dump
  - `rabbitmq_data.tar.gz` - RabbitMQ volume
  - `wso2is_data.tar.gz` - WSO2 Identity Server volume
  - `wso2apim_data.tar.gz` - WSO2 API Manager volume
  - `manifest.txt` - Backup metadata and restore instructions
  - `config/` - Configuration files at backup time

**Backup retention:**
```bash
# List all backups with sizes
du -sh docker-backups/*/

# Remove old backups (keep last 7 days)
find docker-backups/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;

# Or manually remove specific backup
rm -rf docker-backups/2024-01-01_10-00-00/
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
