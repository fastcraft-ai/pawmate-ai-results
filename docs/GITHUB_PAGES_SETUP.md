# GitHub Pages Setup Guide

This guide explains how to enable and configure GitHub Pages for the PawMate AI Results dashboard.

## Overview

The dashboard is automatically deployed to GitHub Pages whenever the leaderboard data is updated. The deployment workflow:

1. Triggers automatically when `aggregates/leaderboard.json` is updated (after aggregation runs)
2. Generates a static HTML site with embedded leaderboard data
3. Deploys the site to GitHub Pages

## Prerequisites

Before enabling GitHub Pages, ensure:

- The repository has the deployment workflow (`.github/workflows/deploy-pages.yml`)
- The aggregation workflow has run at least once to generate `aggregates/leaderboard.json`
- You have admin access to the repository settings

## Enabling GitHub Pages

### Step 1: Navigate to Repository Settings

1. Go to your repository on GitHub
2. Click on **Settings** (in the repository navigation bar)
3. Scroll down to **Pages** in the left sidebar

### Step 2: Configure GitHub Pages Source

1. Under **Source**, select **GitHub Actions** as the source
2. This enables the Pages deployment action to deploy your site

**Important**: Do NOT select a branch (like `main` or `gh-pages`) as the source. The workflow uses the GitHub Actions deployment method, which requires "GitHub Actions" to be selected as the source.

### Step 3: Verify Deployment

After enabling GitHub Pages:

1. The deployment workflow will run automatically when triggered
2. You can manually trigger it by going to **Actions** → **Deploy to GitHub Pages** → **Run workflow**
3. Once the workflow completes, your site will be available at:
   ```
   https://<username>.github.io/<repository-name>/
   ```
   For example: `https://fastcraft-ai.github.io/pawmate-ai-results/`

## Workflow Triggers

The deployment workflow triggers automatically in these scenarios:

1. **Automatic trigger**: When `aggregates/leaderboard.json` is updated (pushed to the repository)
   - This happens after the aggregation workflow (`aggregate.yml`) runs and commits the updated leaderboard

2. **Manual trigger**: You can manually trigger the workflow:
   - Go to **Actions** tab
   - Select **Deploy to GitHub Pages** workflow
   - Click **Run workflow** button
   - Select the branch (usually `main`) and click **Run workflow**

## Workflow Process

When the workflow runs, it:

1. **Checks out the repository** - Gets the latest code and data files
2. **Verifies leaderboard data** - Ensures `aggregates/leaderboard.json` exists
3. **Generates static site** - Runs `generate-site.py` to create HTML with embedded data
4. **Uploads artifact** - Prepares the site for deployment
5. **Deploys to Pages** - Publishes the site to GitHub Pages

## Troubleshooting

### Site Not Deploying

**Issue**: Workflow runs but site doesn't appear

**Solutions**:
- Check that "GitHub Actions" is selected as the Pages source (not a branch)
- Verify the workflow completed successfully (check Actions tab)
- Ensure `aggregates/leaderboard.json` exists in the repository
- Check workflow logs for errors

### Leaderboard Data Missing

**Issue**: Site loads but shows "Error Loading Data"

**Solutions**:
- Ensure `aggregates/leaderboard.json` exists (run aggregation workflow first)
- Verify the JSON file is valid (check for syntax errors)
- Check that the aggregation workflow (`aggregate.yml`) has run successfully

### Workflow Not Triggering

**Issue**: Workflow doesn't run when leaderboard is updated

**Solutions**:
- Verify the workflow file exists at `.github/workflows/deploy-pages.yml`
- Check that `aggregates/leaderboard.json` is being committed by the aggregation workflow
- Try manually triggering the workflow to test

### Permission Errors

**Issue**: Workflow fails with permission errors

**Solutions**:
- Ensure the repository has Pages enabled in Settings
- Check that the workflow has the required permissions:
  - `contents: read`
  - `pages: write`
  - `id-token: write`
- Verify you have admin access to the repository

## Manual Site Generation

If you need to generate the site locally for testing:

```bash
# Ensure leaderboard data exists
ls aggregates/leaderboard.json

# Generate the site
python3 scripts/generate-site.py

# The generated site will be at site/index.html
# Open it in a browser to test locally
```

## Updating the Site

The site automatically updates when:

1. New submissions are processed (ingestion workflow)
2. Aggregation runs (aggregate workflow)
3. Leaderboard is updated (aggregate workflow commits `aggregates/leaderboard.json`)
4. Deployment workflow triggers automatically

You can also manually trigger a deployment by running the "Deploy to GitHub Pages" workflow from the Actions tab.

## Site URL

Once deployed, your site will be available at:

```
https://<username>.github.io/<repository-name>/
```

The exact URL is shown in:
- Repository Settings → Pages
- Workflow run output (deployment step)
- Repository About section (if configured)

## Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions for Pages](https://github.com/actions/deploy-pages)
- [Workflow Configuration](.github/workflows/deploy-pages.yml)

