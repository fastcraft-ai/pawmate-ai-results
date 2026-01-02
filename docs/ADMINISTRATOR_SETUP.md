# Administrator Setup Guide

This guide provides step-by-step instructions for administrators to set up and enable the PawMate AI Results system.

## Prerequisites

Before beginning setup, ensure you have:

- **Repository Admin Access**: Admin permissions on the `pawmate-ai-results` repository
- **GitHub Account**: Access to GitHub settings and repository configuration
- **SMTP Access**: Access to SMTP server credentials for email notifications (optional but recommended)

## Setup Steps

### Step 1: Enable GitHub Pages

The dashboard is deployed automatically to GitHub Pages. You need to enable Pages in repository settings.

#### 1.1 Navigate to Repository Settings

1. Go to your repository on GitHub: `https://github.com/<username>/pawmate-ai-results`
2. Click on **Settings** in the repository navigation bar
3. Scroll down to **Pages** in the left sidebar

#### 1.2 Configure GitHub Pages Source

1. Under **Source**, select **GitHub Actions** as the source
2. **Important**: Do NOT select a branch (like `main` or `gh-pages`) as the source
3. The workflow uses the GitHub Actions deployment method, which requires "GitHub Actions" to be selected

#### 1.3 Verify Deployment

After enabling GitHub Pages:

1. The deployment workflow will run automatically when triggered (after aggregation runs)
2. You can manually trigger it by:
   - Going to **Actions** tab
   - Selecting **Deploy to GitHub Pages** workflow
   - Clicking **Run workflow** button
   - Selecting the branch (usually `main`) and clicking **Run workflow**
3. Once the workflow completes, your site will be available at:
   ```
   https://<username>.github.io/pawmate-ai-results/
   ```
   For example: `https://rsdickerson.github.io/pawmate-ai-results/`

**Note**: The site will only be available after the first aggregation run generates `aggregates/leaderboard.json`. See Step 4 for initial data generation.

### Step 2: Configure SMTP for Email Notifications

The system sends email notifications to administrators when validation failures occur. Configure SMTP secrets in repository settings.

#### 2.1 Navigate to Repository Secrets

1. Go to your repository on GitHub
2. Click on **Settings** in the repository navigation bar
3. Scroll down to **Secrets and variables** → **Actions** in the left sidebar
4. Click on **New repository secret** for each required secret

#### 2.2 Configure Required SMTP Secrets

Create the following secrets (click "New repository secret" for each):

1. **`SMTP_SERVER`**
   - **Name**: `SMTP_SERVER`
   - **Value**: Your SMTP server address (e.g., `smtp.gmail.com`, `smtp.sendgrid.net`)
   - **Example**: `smtp.gmail.com`

2. **`SMTP_PORT`**
   - **Name**: `SMTP_PORT`
   - **Value**: SMTP server port (typically `587` for TLS, `465` for SSL, `25` for unencrypted)
   - **Example**: `587`

3. **`SMTP_USERNAME`**
   - **Name**: `SMTP_USERNAME`
   - **Value**: SMTP authentication username (usually your email address)
   - **Example**: `your-email@gmail.com`

4. **`SMTP_PASSWORD`**
   - **Name**: `SMTP_PASSWORD`
   - **Value**: SMTP authentication password or app-specific password
   - **Note**: For Gmail, you may need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password

5. **`SMTP_FROM`**
   - **Name**: `SMTP_FROM`
   - **Value**: Email address to send notifications from (usually same as SMTP_USERNAME)
   - **Example**: `your-email@gmail.com`

#### 2.3 Verify SMTP Configuration

After configuring secrets:

1. The ingestion workflow will use these secrets when validation failures occur
2. Test by creating a test submission with invalid JSON (see troubleshooting section)
3. Check that email notifications are received at `pawmate.ai.challenge@gmail.com` (configured in workflow)

**Note**: Email notifications are optional. The system will still function without SMTP configuration, but administrators won't receive email alerts for validation failures.

### Step 3: GitHub Token Setup (For Developers)

While administrators don't need personal tokens, developers submitting results will need GitHub personal access tokens. Provide these instructions to developers (or see [Developer Guide](DEVELOPER_GUIDE.md) for complete instructions).

#### 3.1 Create Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Give it a descriptive name (e.g., "PawMate Result Submission")
4. Select the **`repo`** scope (required for creating issues)
5. Click **Generate token** and copy the token immediately (you won't be able to see it again)

#### 3.2 Token Configuration

Developers can configure tokens in two ways:

**Method 1: Environment Variable** (recommended for temporary use)
```bash
export GITHUB_TOKEN=your-token-here
```

**Method 2: Configuration File** (recommended for persistent use)
Create or edit `.submission.config` in the challenge repository root:
```
GITHUB_TOKEN=your-token-here
```

**Priority**: Config file is checked first, then environment variable.

### Step 4: Initial Data Generation

Before the dashboard can be displayed, you need to generate initial leaderboard data.

#### 4.1 Run Aggregation Script

The aggregation script can be run manually or will run automatically when submissions are stored. For initial setup:

**Option A: Manual Run (Local)**
```bash
cd pawmate-ai-results
python3 scripts/aggregate_results.py --input-dir submissions --output-dir results/compiled
```

This will:
- Read all result files from `submissions/` directory
- Generate `aggregates/results.csv`
- Generate `aggregates/leaderboard.json`
- Generate HTML reports in `results/compiled/`

**Option B: Trigger Workflow (Recommended)**
1. Go to **Actions** tab in GitHub repository
2. Select **Aggregate Results** workflow
3. Click **Run workflow** button
4. Select branch (usually `main`) and click **Run workflow**

The workflow will:
- Run aggregation automatically
- Commit generated files to repository
- Trigger Pages deployment automatically

#### 4.2 Verify Initial Data

After running aggregation:

1. Check that `aggregates/leaderboard.json` exists in repository
2. Verify JSON is valid (can open in browser or validate with `jq`)
3. Check that `aggregates/results.csv` exists
4. Verify Pages deployment completed successfully

### Step 5: Workflow Verification

Verify all workflows are functioning correctly.

#### 5.1 Verify Ingestion Workflow

1. Go to **Actions** tab
2. Look for **Ingest Submission** workflow
3. Verify it triggers on issues with `submission` label
4. Test by creating a test issue with `submission` label (see troubleshooting)

#### 5.2 Verify Aggregation Workflow

1. Go to **Actions** tab
2. Look for **Aggregate Results** workflow
3. Verify it triggers on pushes to `submissions/**` paths
4. Check that it commits `aggregates/leaderboard.json` and `aggregates/results.csv`

#### 5.3 Verify Deployment Workflow

1. Go to **Actions** tab
2. Look for **Deploy to GitHub Pages** workflow
3. Verify it triggers on pushes to `aggregates/leaderboard.json`
4. Check that deployment completes successfully
5. Verify dashboard is accessible at GitHub Pages URL

#### 5.4 Test Complete Workflow

1. Create a test submission using `submit_result.sh` (see Developer Guide)
2. Verify issue is created with `submission` label
3. Check that ingestion workflow runs and processes submission
4. Verify aggregation workflow runs after storage
5. Check that deployment workflow runs after aggregation
6. Verify dashboard updates with new data

## Verification Checklist

Use this checklist to confirm setup is complete:

- [ ] GitHub Pages enabled with "GitHub Actions" as source
- [ ] SMTP secrets configured (SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM)
- [ ] Initial aggregation run completed successfully
- [ ] `aggregates/leaderboard.json` exists and is valid
- [ ] `aggregates/results.csv` exists
- [ ] Dashboard is accessible at GitHub Pages URL
- [ ] Ingestion workflow triggers on issues with `submission` label
- [ ] Aggregation workflow triggers on `submissions/**` pushes
- [ ] Deployment workflow triggers on `aggregates/leaderboard.json` updates
- [ ] Test submission processed successfully end-to-end

## Troubleshooting

### GitHub Pages Not Deploying

**Issue**: Workflow runs but site doesn't appear

**Solutions**:
- Verify "GitHub Actions" is selected as Pages source (not a branch)
- Check workflow completed successfully in Actions tab
- Ensure `aggregates/leaderboard.json` exists in repository
- Check workflow logs for errors
- Verify workflow has required permissions (`contents: read`, `pages: write`, `id-token: write`)

### SMTP Configuration Issues

**Issue**: Email notifications not working

**Solutions**:
- Verify all SMTP secrets are configured correctly
- Check SMTP server address and port are correct
- For Gmail, ensure you're using an App Password, not regular password
- Test SMTP credentials with a simple email client
- Check workflow logs for SMTP error messages
- Verify `SMTP_FROM` matches `SMTP_USERNAME` (some servers require this)

### Aggregation Not Running

**Issue**: Aggregation workflow doesn't trigger

**Solutions**:
- Verify workflow file exists at `.github/workflows/aggregate.yml`
- Check that submissions are being stored in `submissions/` directory
- Verify workflow trigger paths match actual file locations
- Try manually triggering workflow from Actions tab
- Check workflow logs for errors

### Leaderboard Data Missing

**Issue**: Dashboard shows "Error Loading Data"

**Solutions**:
- Ensure `aggregates/leaderboard.json` exists (run aggregation workflow first)
- Verify JSON file is valid (check for syntax errors)
- Check that aggregation workflow completed successfully
- Verify file path in dashboard matches actual location
- Check browser console for loading errors

### Workflow Permission Errors

**Issue**: Workflows fail with permission errors

**Solutions**:
- Verify repository has Pages enabled in Settings
- Check workflow permissions in workflow files:
  - Ingestion: `contents: read`, `issues: write`
  - Aggregation: `contents: write`
  - Deployment: `contents: read`, `pages: write`, `id-token: write`
- Ensure you have admin access to repository
- Check repository settings for workflow permissions

## Next Steps

After completing setup:

1. **Share Developer Guide**: Provide developers with [Developer Guide](DEVELOPER_GUIDE.md) for submitting results
2. **Monitor Workflows**: Regularly check Actions tab to ensure workflows are running successfully
3. **Review Submissions**: Monitor GitHub Issues for submission activity
4. **Check Dashboard**: Verify dashboard updates correctly with new submissions

## Related Documentation

- [System Overview](SYSTEM_OVERVIEW.md) - Complete system architecture
- [Developer Guide](DEVELOPER_GUIDE.md) - Developer submission workflow
- [GitHub Pages Setup](GITHUB_PAGES_SETUP.md) - Detailed Pages configuration

