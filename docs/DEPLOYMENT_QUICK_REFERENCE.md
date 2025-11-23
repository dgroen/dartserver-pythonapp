# Deployment Quick Reference Card

## Standard Deployment Process

### 1️⃣ Deploy to Test
```bash
git checkout test
git merge your-feature-branch
git push origin test
```
**→ Automatic test deployment starts**

### 2️⃣ Review Test
- Check https://test.letsplaydarts.eu
- Verify functionality
- Review logs if needed

### 3️⃣ Approve Production Deployment
- Go to GitHub **Actions** tab
- Click running workflow
- Click **Review deployments**
- Select `production-approval`
- Click **Approve and deploy**

**→ Automatic backup + production deployment starts**

### 4️⃣ Verify Production
- Check https://letsplaydarts.eu
- Verify all features working
- Monitor for any issues

### 5️⃣ Confirm Success
- Go to GitHub **Actions** tab
- Click **Review deployments** at verification step
- Select `production-verification`
- Click **Approve** ✅

**→ Deployment complete!**

---

## If Something Goes Wrong

### ❌ Deployment Fails Automatically
**→ Automatic restore runs** (no action needed)
- Volumes restored from backup
- Database restored
- Containers restarted
- Production back to previous state

### ⚠️ Issues Found After Deployment
1. Go to GitHub **Actions** tab
2. Click **Review deployments** at verification step
3. Select `production-verification`
4. Click **Reject** ❌
5. At rollback step, click **Review deployments** again
6. Select `production-rollback`
7. Click **Approve** to confirm rollback

**→ Production restored to pre-deployment state**

---

## Manual Backup/Restore

### Create Backup Manually
```bash
ssh user@production-server
cd /opt/dartserver-pythonapp
./helpers/backup_docker_volumes.sh -y
```

### Restore from Backup Manually
```bash
ssh user@production-server
cd /opt/dartserver-pythonapp

# List available backups
ls -lt docker-backups/

# Restore specific backup
./helpers/restore_docker_volumes.sh -b docker-backups/2024-01-15_14-30-00/ -y
```

---

## Approval Gate Decision Tree

```
Test Deployment Success?
├─ Yes → Review test environment
│   ├─ Everything OK?
│   │   ├─ Yes → Approve production deployment ✅
│   │   └─ No → Fix issues, re-deploy to test
│   └─ 
└─ No → Check logs, fix issues, re-deploy

Production Deployment Success?
├─ Yes → Verify production manually
│   ├─ Everything working?
│   │   ├─ Yes → Approve verification ✅ → Done!
│   │   └─ No → Reject verification ❌ → Approve rollback
│   └─
└─ No → Automatic restore triggered → Production restored
```

---

## Monitoring Commands

### Check Container Status
```bash
ssh user@production-server
docker-compose -f docker-compose-wso2.yml ps
```

### View Application Logs
```bash
ssh user@production-server
cd /opt/dartserver-pythonapp
docker-compose -f docker-compose-wso2.yml logs -f darts-app
```

### View All Logs
```bash
docker-compose -f docker-compose-wso2.yml logs -f
```

### Check Disk Space
```bash
df -h
du -sh docker-backups/
```

---

## Common Issues

### Issue: Approval not appearing
**Solution:** Refresh GitHub Actions page, check environment reviewers are configured

### Issue: Backup taking too long
**Solution:** Check disk space: `df -h`, may need to clean old backups

### Issue: Containers not starting after restore
**Solution:** Check logs: `docker-compose logs`, verify backup integrity

### Issue: Health check failing
**Solution:** 
```bash
# Check app logs
docker-compose logs darts-app

# Check database
docker-compose logs postgres

# Verify services
docker-compose ps
```

---

## Emergency Contacts

- **Primary:** [Your team lead]
- **Secondary:** [Senior DevOps engineer]
- **Escalation:** [CTO/Engineering manager]

---

## Important Links

- **GitHub Actions:** https://github.com/[org]/[repo]/actions
- **Production:** https://letsplaydarts.eu
- **Test:** https://test.letsplaydarts.eu
- **Docs:** `docs/DEPLOYMENT_BACKUP_RESTORE.md`

---

## Backup Locations

- **Production:** `/opt/dartserver-pythonapp/docker-backups/`
- **Format:** `YYYY-MM-DD_HH-MM-SS/`
- **Contents:** All volumes + PostgreSQL dump + config files

---

**Print this card and keep it handy! 📄**
