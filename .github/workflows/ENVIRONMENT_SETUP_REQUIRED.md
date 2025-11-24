# ⚠️ REQUIRED: GitHub Environment Setup

## Critical: Approval Gate Not Working?

If the `approval-gate` job in the unified deployment pipeline **does not pause** and continues immediately to production, it means the GitHub Environment is not configured correctly.

## Quick Fix

### Step 1: Navigate to Environments Settings
1. Go to your GitHub repository: https://github.com/dgroen/dartserver-pythonapp
2. Click **Settings** tab (top right)
3. Click **Environments** in the left sidebar

### Step 2: Create `production-approval` Environment

**If the environment doesn't exist:**
1. Click **New environment**
2. Name: `production-approval` (exactly this name)
3. Click **Configure environment**

**If the environment already exists:**
1. Click on `production-approval` environment name

### Step 3: Enable Required Reviewers (THIS IS CRITICAL)

1. Check ☑️ **Required reviewers**
2. Click **Add reviewers** button
3. Add at least one GitHub username who should approve deployments
4. Click **Save protection rules**

**Without this step, the workflow will NOT wait for approval!**

### Step 4: Repeat for Other Environments

You need to create and configure these environments:

1. ✅ **`production-approval`** - Pre-deployment approval (add reviewers) - REQUIRED
2. ⚙️ **`production`** - Production deployment target (optional reviewers)
3. ✅ **`production-restore-approval`** - Approve/skip restore after deployment failure (add reviewers) - REQUIRED
4. ✅ **`production-verification`** - Post-deployment verification, can approve or skip (add reviewers) - REQUIRED
5. ✅ **`production-rollback`** - Manual rollback confirmation (add reviewers) - REQUIRED

## Verification

After setup:
1. Push to `test` branch to trigger deployment
2. Watch GitHub Actions workflow
3. The `approval-gate` job should show "Waiting for review" status
4. Designated reviewers should receive notification
5. Reviewer must click "Review deployments" button to approve/reject

## Visual Confirmation

When properly configured, you'll see:
- 🟡 Yellow "Waiting" badge on the `approval-gate` job
- 🔔 Notification sent to configured reviewers
- 🔘 "Review deployments" button appears for reviewers

When **NOT** configured:
- ✅ Green checkmark immediately (no waiting)
- Job completes in seconds
- No reviewer notification sent

## Full Setup Guide

See: `docs/GITHUB_ENVIRONMENTS_SETUP_CHECKLIST.md` for complete step-by-step instructions.

## Emergency Override

If you need to bypass approval temporarily (emergency only):
1. Go to Settings → Environments → `production-approval`
2. Uncheck "Required reviewers"
3. Save changes
4. **Remember to re-enable after emergency!**

---

**Bottom line:** The approval gate feature **requires** the GitHub Environment to be configured with "Required reviewers" enabled. Without it, GitHub Actions treats it as a regular job and continues immediately.
