# Deployment Pipeline Backup/Restore Implementation Summary

## Overview

The unified deployment pipeline (`deploy-unified.yml`) has been enhanced with comprehensive backup/restore capabilities to ensure production safety and enable quick recovery from deployment issues.

## Key Features

### 1. Pre-Deployment Backup
- **Automatic full backup** created before every production deployment
- Backs up all Docker volumes:
  - `postgres_data` - PostgreSQL database
  - `rabbitmq_data` - RabbitMQ message queues
  - `wso2is_data` - WSO2 Identity Server data
  - `wso2apim_data` - WSO2 API Manager data
- Creates SQL dump using `pg_dump` for database restore
- Stores backup path for later restore operations

### 2. Automatic Restore on Failure
- **Triggers automatically if deployment fails**
- No manual intervention required
- Restores all volumes and database from pre-deployment backup
- Verifies restoration success
- Ensures production returns to working state immediately

### 3. Post-Deployment Verification Gate
- **Manual verification step** after successful deployment
- Allows team to verify production is working correctly
- Options:
  - ✅ Approve - Confirms deployment success, completes pipeline
  - ❌ Reject - Triggers manual rollback to pre-deployment state

### 4. Manual Rollback on Request
- Triggers when post-deployment verification is rejected
- Requires manual approval via `production-rollback` environment
- Restores production to pre-deployment backup
- Verifies rollback success

## Workflow Stages

```
1. Deploy to Test
   ↓
2. Manual Approval Gate (production-approval)
   ↓
3. Backup Production (automatic)
   ↓
4. Deploy to Production
   ↓
5a. If FAILS → Automatic Restore (no approval needed)
5b. If SUCCESS → Post-Deployment Verification (manual)
   ↓
6. If Verification Rejected → Manual Rollback (requires approval)
7. If Verification Approved → Pipeline Complete
```

## GitHub Environments Required

| Environment | Purpose | Reviewers |
|------------|---------|-----------|
| `production-approval` | Pre-deployment approval gate | 1-2 team members |
| `production` | Production deployment target | Optional |
| `production-verification` | Post-deployment verification | 1-2 team members |
| `production-rollback` | Manual rollback confirmation | Senior team members |

## Scripts Created

### 1. Backup Script
**Location:** `helpers/backup_docker_volumes.sh`

**Features:**
- Creates timestamped backups in `docker-backups/YYYY-MM-DD_HH-MM-SS/`
- Backs up all Docker volumes using tar.gz compression
- Creates PostgreSQL dump with `pg_dump`
- Includes backup manifest with metadata and restore instructions
- Supports auto-confirm mode with `-y` flag

**Usage:**
```bash
# Interactive mode
./helpers/backup_docker_volumes.sh

# Auto-confirm mode (for CI/CD)
./helpers/backup_docker_volumes.sh -y
```

### 2. Restore Script
**Location:** `helpers/restore_docker_volumes.sh`

**Features:**
- Restores from timestamped backup directory
- Restores all Docker volumes from tar.gz archives
- Restores PostgreSQL database from SQL dump
- Stops containers before restore
- Starts containers after restore
- Verifies restoration success
- Supports auto-confirm mode with `-y` flag

**Usage:**
```bash
# Interactive mode
./helpers/restore_docker_volumes.sh -b docker-backups/2024-01-15_14-30-00/

# Auto-confirm mode (for CI/CD)
./helpers/restore_docker_volumes.sh -b docker-backups/2024-01-15_14-30-00/ -y

# Help
./helpers/restore_docker_volumes.sh --help
```

## Deployment Flow Examples

### Scenario 1: Successful Deployment

1. Push to `test` branch
2. Test deployment completes successfully
3. Team reviews test environment
4. **Approve production deployment** via GitHub Actions
5. Backup is created automatically
6. Production deployment executes
7. Health checks pass
8. **Verify production** via GitHub Actions
9. Team confirms production is working
10. **Approve verification** → Pipeline completes ✅

**Result:** Production updated successfully, backup available if needed later

### Scenario 2: Deployment Fails

1. Push to `test` branch
2. Test deployment completes successfully
3. Team reviews test environment
4. **Approve production deployment** via GitHub Actions
5. Backup is created automatically
6. Production deployment starts
7. ❌ **Health check fails**
8. **Automatic restore triggered** immediately
9. Backup is restored automatically
10. Production returns to previous working state ✅

**Result:** Production automatically restored, no data loss

### Scenario 3: Deployment Succeeds but Issues Discovered

1. Push to `test` branch
2. Test deployment completes successfully
3. Team reviews test environment
4. **Approve production deployment** via GitHub Actions
5. Backup is created automatically
6. Production deployment executes
7. Health checks pass
8. **Verify production** via GitHub Actions
9. Team discovers issue (e.g., performance problem, incorrect behavior)
10. **Reject verification** → Triggers rollback
11. **Approve rollback** via GitHub Actions
12. Backup is restored
13. Production returns to previous state ✅

**Result:** Production rolled back to previous working state

## Backup Management

### Backup Location
All backups stored in: `/opt/dartserver-pythonapp/docker-backups/`

### Backup Structure
```
docker-backups/
├── 2024-01-15_14-30-00/
│   ├── postgres_data.tar.gz
│   ├── postgres_dump.sql.gz
│   ├── rabbitmq_data.tar.gz
│   ├── wso2is_data.tar.gz
│   ├── wso2apim_data.tar.gz
│   ├── manifest.txt
│   └── config/
│       ├── wso2is-deployment.toml
│       ├── .env
│       └── nginx/
├── 2024-01-16_10-15-00/
└── ...
```

### Backup Retention

**Automatic cleanup** is NOT implemented to preserve all deployment backups.

**Manual cleanup** when disk space is limited:
```bash
# Keep only last 7 days of backups
find docker-backups/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;

# Keep only last 10 backups
ls -dt docker-backups/*/ | tail -n +11 | xargs rm -rf
```

## Testing the Backup/Restore

### Test Backup Script
```bash
# SSH to production server
ssh user@production-server
cd /opt/dartserver-pythonapp

# Run backup
./helpers/backup_docker_volumes.sh -y

# Verify backup created
ls -lh docker-backups/
```

### Test Restore Script
```bash
# CAUTION: This will restore data, test in non-production first!

# Find latest backup
BACKUP=$(ls -dt docker-backups/*/ | head -1)
echo "Testing restore from: $BACKUP"

# Run restore (use -y for auto-confirm)
./helpers/restore_docker_volumes.sh -b "$BACKUP" -y

# Verify containers are running
docker-compose -f docker-compose-wso2.yml ps
```

## Monitoring and Notifications

### During Deployment
- Monitor workflow in GitHub Actions **Actions** tab
- Each step shows real-time logs
- Failed steps highlighted in red
- Approval steps show pending status

### After Deployment
- Check deployment success notification in GitHub Actions
- Verify application health at https://letsplaydarts.eu
- Review backup creation in workflow logs
- Confirm all containers running: `docker-compose ps`

## Troubleshooting

### Backup Fails
**Symptoms:** Backup job fails in GitHub Actions

**Solutions:**
1. Check disk space on server: `df -h`
2. Verify backup script is executable: `chmod +x helpers/backup_docker_volumes.sh`
3. Check Docker volumes exist: `docker volume ls`
4. Review backup script logs in GitHub Actions

### Restore Fails
**Symptoms:** Restore doesn't complete or containers don't start

**Solutions:**
1. Check backup integrity: `tar -tzf docker-backups/*/postgres_data.tar.gz | head`
2. Verify Docker has permissions: `ls -l docker-backups/`
3. Check disk space: `df -h`
4. Manually restore volumes: Follow instructions in `manifest.txt`
5. Check restore script logs for specific error

### Automatic Restore Doesn't Trigger
**Symptoms:** Deployment fails but restore doesn't run

**Possible causes:**
1. Backup job didn't complete - Check `backup-production` job logs
2. GitHub Actions workflow syntax error - Validate YAML syntax
3. SSH connection lost - Check network connectivity

**Manual restore:**
```bash
ssh user@production-server
cd /opt/dartserver-pythonapp
./helpers/restore_docker_volumes.sh -b $(ls -dt docker-backups/*/ | head -1) -y
```

## Security Considerations

1. **Backup Permissions:** Backups contain sensitive data
   - Ensure backup directory has restricted permissions (700)
   - Limit SSH access to authorized users only

2. **Secrets in Backups:** Configuration backups include deployment.toml and .env
   - Do NOT commit backup directories to git
   - Add `docker-backups/` to `.gitignore`

3. **Backup Transfer:** If backing up to remote location
   - Use encrypted transfer (rsync over SSH)
   - Encrypt backup archives before transfer

## Future Enhancements

Potential improvements for consideration:

1. **Automated Backup Cleanup:** Add job to remove old backups (keep last 30 days)
2. **Remote Backup Storage:** Upload backups to S3/Azure Storage for disaster recovery
3. **Backup Notifications:** Slack/email notifications when backups are created
4. **Pre-deployment Smoke Tests:** Automated tests before production deployment
5. **Incremental Backups:** Use Docker volume diffs for faster backups
6. **Database-only Restore:** Option to restore only database without volumes

## Documentation References

- **Main Workflow:** `.github/workflows/deploy-unified.yml`
- **Workflows README:** `.github/workflows/README.md`
- **Backup Script:** `helpers/backup_docker_volumes.sh`
- **Restore Script:** `helpers/restore_docker_volumes.sh`
- **GitHub Environments:** Settings → Environments in GitHub repository

## Rollout Plan

### Step 1: Configure GitHub Environments
1. Create `production-approval` environment with reviewers
2. Create `production-verification` environment with reviewers
3. Create `production-rollback` environment with senior reviewers
4. Test approval flow with test deployment

### Step 2: Test Backup/Restore on Test Server
1. SSH to test server
2. Run backup script: `./helpers/backup_docker_volumes.sh -y`
3. Run restore script: `./helpers/restore_docker_volumes.sh -b <backup-path> -y`
4. Verify containers restart correctly

### Step 3: Deploy to Test Environment
1. Push to `test` branch
2. Monitor GitHub Actions workflow
3. Verify test deployment success

### Step 4: First Production Deployment with New Pipeline
1. **Announce maintenance window** (for safety)
2. Approve production deployment via GitHub Actions
3. Monitor backup creation
4. Monitor deployment progress
5. If successful, verify production manually
6. Approve verification to complete pipeline
7. **OR** if issues found, reject verification to trigger rollback

### Step 5: Validate Backup
1. Check backup was created: `ls -lh docker-backups/`
2. Verify backup contents: `tar -tzf docker-backups/*/postgres_data.tar.gz | head`
3. Confirm manifest file exists and is readable

## Success Criteria

The backup/restore implementation is successful when:

✅ Pre-deployment backup created automatically  
✅ Backup includes all volumes and database dump  
✅ Automatic restore works on deployment failure  
✅ Manual rollback works after verification rejection  
✅ All approval gates function correctly  
✅ Backups are complete and restorable  
✅ Documentation is clear and comprehensive  
✅ Team is trained on approval process  

## Support

For issues or questions:

1. Review this document and `.github/workflows/README.md`
2. Check GitHub Actions logs for detailed error messages
3. Test backup/restore scripts manually on test server
4. Escalate to senior team member if automatic restore fails

---

**Last Updated:** 2024-01-15  
**Pipeline Version:** 2.0 (with backup/restore)  
**Status:** ✅ Ready for production use
