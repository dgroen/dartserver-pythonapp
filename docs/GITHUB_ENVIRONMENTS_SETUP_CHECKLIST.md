# GitHub Environments Setup Checklist

Use this checklist to configure the required GitHub Environments for the unified deployment pipeline with backup/restore capabilities.

## Prerequisites

- [ ] You have admin access to the GitHub repository
- [ ] You know who should approve deployments (at least 1-2 team members)
- [ ] You have identified senior team members for rollback approvals

## Setup Instructions

### Step 1: Access Environments Settings

- [ ] Navigate to your GitHub repository
- [ ] Click **Settings** tab
- [ ] Click **Environments** in left sidebar

---

### Step 2: Create `production-approval` Environment

**Purpose:** Pre-deployment approval gate - review test before deploying to production

- [ ] Click **New environment**
- [ ] Name: `production-approval`
- [ ] Click **Configure environment**

**Configure Protection Rules:**
- [ ] Check ☑️ **Required reviewers**
- [ ] Click **Add reviewers**
- [ ] Add reviewer(s): _____________________ (fill in GitHub usernames)
- [ ] Recommended: Add 1-2 reviewers minimum
- [ ] Optional: Set **Wait timer**: _____ minutes (e.g., 5 minutes)
- [ ] Click **Save protection rules**

**Verification:**
- [ ] Environment `production-approval` appears in environments list
- [ ] Required reviewers are configured
- [ ] Protection rules are active

---

### Step 3: Create `production` Environment

**Purpose:** Production deployment target with optional URL tracking

- [ ] Click **New environment**
- [ ] Name: `production`
- [ ] Click **Configure environment**

**Configure Environment:**
- [ ] Set **Environment URL**: `https://letsplaydarts.eu`
- [ ] Optional: Add required reviewers (or leave unprotected if pre-approval is sufficient)
- [ ] Click **Save protection rules**

**Verification:**
- [ ] Environment `production` appears in environments list
- [ ] Environment URL is set correctly

---

### Step 4: Create `production-verification` Environment

**Purpose:** Post-deployment verification - confirm deployment is working

- [ ] Click **New environment**
- [ ] Name: `production-verification`
- [ ] Click **Configure environment**

**Configure Protection Rules:**
- [ ] Check ☑️ **Required reviewers**
- [ ] Click **Add reviewers**
- [ ] Add reviewer(s): _____________________ (fill in GitHub usernames)
- [ ] These can be same or different from pre-deployment reviewers
- [ ] Recommended: 1-2 reviewers who will test production
- [ ] Click **Save protection rules**

**Verification:**
- [ ] Environment `production-verification` appears in environments list
- [ ] Required reviewers are configured

---

### Step 5: Create `production-rollback` Environment

**Purpose:** Manual rollback confirmation - final approval to restore from backup

- [ ] Click **New environment**
- [ ] Name: `production-rollback`
- [ ] Click **Configure environment**

**Configure Protection Rules:**
- [ ] Check ☑️ **Required reviewers**
- [ ] Click **Add reviewers**
- [ ] Add reviewer(s): _____________________ (fill in GitHub usernames)
- [ ] Recommended: Use **senior team members** for rollback decisions
- [ ] At least 1 reviewer required
- [ ] Click **Save protection rules**

**Verification:**
- [ ] Environment `production-rollback` appears in environments list
- [ ] Senior reviewers are configured
- [ ] Protection rules are active

---

## Final Verification

### Check All Environments

- [ ] Navigate to **Settings** → **Environments**
- [ ] Verify all 4 environments exist:
  - [ ] `production-approval`
  - [ ] `production`
  - [ ] `production-verification`
  - [ ] `production-rollback`

### Test Approval Notification

- [ ] Trigger a test deployment (push to `test` branch)
- [ ] Monitor GitHub Actions workflow
- [ ] Verify reviewers receive notification at approval gate
- [ ] Test approving the deployment (or cancel if not ready)

---

## Environment Summary

| Environment | Purpose | Reviewers | Notes |
|-------------|---------|-----------|-------|
| `production-approval` | Pre-deployment gate | 1-2 team members | Reviews test before prod |
| `production` | Deployment target | Optional | URL: letsplaydarts.eu |
| `production-verification` | Post-deployment check | 1-2 team members | Verifies prod working |
| `production-rollback` | Rollback confirmation | Senior members | Final rollback approval |

---

## Troubleshooting

### Issue: Can't find Environments in Settings
**Solution:** You need admin access to the repository. Contact repository owner.

### Issue: Reviewers not receiving notifications
**Solutions:**
1. Check reviewer's GitHub notification settings
2. Verify reviewer has access to the repository
3. Ensure reviewer's email is verified in GitHub

### Issue: Workflow not triggering approval gate
**Solutions:**
1. Verify environment name matches exactly (case-sensitive)
2. Check workflow YAML syntax
3. Review GitHub Actions logs for errors

### Issue: Want to add/remove reviewers
**Solution:**
1. Go to Settings → Environments
2. Click environment name
3. Edit protection rules
4. Add/remove reviewers
5. Save changes

---

## Reviewer Responsibilities

### Pre-Deployment Approval (`production-approval`)
- Review test environment at https://test.letsplaydarts.eu
- Verify all features working correctly
- Check recent code changes in pull request
- Approve or reject production deployment

### Post-Deployment Verification (`production-verification`)
- Verify production at https://letsplaydarts.eu
- Test critical functionality
- Monitor for errors or performance issues
- Approve if working, reject if issues found

### Rollback Approval (`production-rollback`)
- Confirm rollback is necessary
- Understand rollback will restore from backup
- Approve rollback decision
- Monitor restoration process

---

## Best Practices

✅ **DO:**
- Add at least 2 reviewers for critical approvals
- Use senior team members for rollback approvals
- Document who reviewers are and how to reach them
- Test approval flow before first production deployment
- Review test environment thoroughly before approving

❌ **DON'T:**
- Approve production without reviewing test
- Use same person for all approval gates (avoid single point of failure)
- Skip verification step even if deployment looks successful
- Approve rollback without confirming necessity

---

## Emergency Override

If you need to bypass approval gates in an emergency:

1. **Disable environment protection rules temporarily:**
   - Go to Settings → Environments
   - Click environment name
   - Uncheck "Required reviewers"
   - Save changes

2. **After emergency, re-enable protection:**
   - Re-check "Required reviewers"
   - Add reviewers back
   - Save changes

⚠️ **WARNING:** Only use emergency override for critical production issues.

---

## Setup Complete! ✅

Once all checkboxes are marked:

- [ ] All 4 environments created
- [ ] All reviewers configured
- [ ] Protection rules active
- [ ] Test deployment verified
- [ ] Team trained on approval process

**Your deployment pipeline is ready for production use!**

---

**Questions?** See `docs/DEPLOYMENT_BACKUP_RESTORE.md` for detailed documentation.
