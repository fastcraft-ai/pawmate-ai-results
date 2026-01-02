# Developer Guide

This guide explains how developers can run benchmarks, submit results, and view reporting on the PawMate AI Challenge Results dashboard.

## Overview

The PawMate AI Challenge Results system allows you to:
1. Run benchmark tests using the challenge repository
2. Submit results via GitHub Issues using `submit_result.sh`
3. View results on an interactive dashboard with charts and leaderboards

## Running a Benchmark

### Prerequisites

Before running a benchmark, ensure you have:
- Access to the `pawmate-ai-challenge` repository
- An AI coding tool to test (Cursor, GitHub Copilot, etc.)
- Node.js and npm installed (for building the generated application)

### Step 1: Initialize a Benchmark Run

1. Clone or navigate to the challenge repository:
   ```bash
   cd pawmate-ai-challenge
   ```

2. Choose a profile and initialize a run:
   ```bash
   ./scripts/initialize_run.sh --profile model-a-rest --tool "YourTool" --tool-ver "1.0"
   ```

   Available profiles:
   - `model-a-rest` - Model A with REST API
   - `model-a-graphql` - Model A with GraphQL API
   - `model-b-rest` - Model B with REST API
   - `model-b-graphql` - Model B with GraphQL API

3. This creates a run folder at `runs/YYYYMMDDTHHmm/` containing:
   - `start_build_api_prompt.txt` - Prompt for building the API/backend
   - `start_build_ui_prompt.txt` - Prompt for building the UI (optional)
   - `run.config` - Run metadata
   - `PawMate/` - Workspace for the AI-generated implementation

### Step 2: Execute the Benchmark

1. Open a new agent session in your AI coding tool
2. Copy the entire contents of `start_build_api_prompt.txt`
3. Paste it as the first message to your AI tool
4. Monitor progress and send "continue" if the AI stops before completion
5. Ensure all requirements are met:
   - ✅ All code is written
   - ✅ Build completes successfully (`npm install` passes)
   - ✅ Database is seeded
   - ✅ Server starts successfully
   - ✅ All tests pass

### Step 3: Generate Result File

After the benchmark completes successfully:

1. The result file is automatically generated in the run folder
2. Result file naming convention: `{tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json`
   - Example: `cursor_modelA_REST_run1_20250101T1000.json`
3. Result file location: `runs/YYYYMMDDTHHmm/{result-file}.json`

### Result File Format

The result file follows Schema v3.0 and includes:
- **Run Identity**: Tool name, version, target model, API style, run number
- **Implementations**: API and/or UI implementation details
  - Acceptance test results (pass rate)
  - Generation metrics (duration, LLM model used)
  - Test iteration details
- **Submission**: Submission metadata and timestamps

For complete schema documentation, see:
- [Schema v3.0 Design](../schemas/schema-v3.0-design.md)
- [Schema v3.0 Field Reference](../schemas/schema-v3.0-field-reference.md)

## Submitting Results

### Prerequisites

Before submitting, you need:
- A GitHub personal access token with `repo` scope
- The result JSON file from your benchmark run
- Access to the `submit_result.sh` script

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Give it a descriptive name (e.g., "PawMate Result Submission")
4. Select the **`repo`** scope (required for creating issues)
5. Click **Generate token** and copy the token immediately
   - **Important**: You won't be able to see it again after leaving the page

### Step 2: Configure GitHub Token

You can configure your token in one of two ways:

**Method 1: Environment Variable** (recommended for temporary use)
```bash
export GITHUB_TOKEN=your-token-here
```

**Method 2: Configuration File** (recommended for persistent use)
1. Create or edit `.submission.config` in the challenge repository root:
   ```bash
   cd pawmate-ai-challenge
   nano .submission.config
   ```
2. Add your token:
   ```
   GITHUB_TOKEN=your-token-here
   ```
3. Save the file

**Priority**: Config file is checked first, then environment variable.

### Step 3: Submit Result Using submit_result.sh

1. Navigate to the challenge repository:
   ```bash
   cd pawmate-ai-challenge
   ```

2. Run the submission script:
   ```bash
   ./scripts/submit_result.sh runs/YYYYMMDDTHHmm/{result-file}.json
   ```

   Replace `YYYYMMDDTHHmm` with your actual run folder timestamp and `{result-file}.json` with your result filename.

3. The script will:
   - Validate the JSON file format
   - Prompt for attribution (your name or identifier)
   - Create a GitHub Issue in the `pawmate-ai-results` repository
   - Display the issue URL and number

### Step 4: Verify Submission

After submission:

1. **Check Script Output**: The script displays the issue URL and number
   ```
   ✓ GitHub Issue created successfully!
   Issue #123: https://github.com/rsdickerson/pawmate-ai-results/issues/123
   ```

2. **Check GitHub Issue**: Visit the issue URL to verify:
   - Issue has `submission` and `results` labels
   - JSON content is present in the issue body
   - Issue title follows format: `[Submission] Tool: {tool}, Model: {model}, API: {api}, Run: {run}`

3. **Monitor Processing**: The ingestion workflow will automatically:
   - Extract JSON from issue body
   - Validate against Schema v3.0
   - Store result in time-partitioned directory
   - Comment on issue with success or error messages

4. **Check Issue Comments**: After processing (usually within 1-2 minutes):
   - **Success**: Issue will have a success comment and be automatically closed
   - **Error**: Issue will have an error comment with detailed validation errors

### What Happens After Submission

1. **Immediate**: GitHub Issue is created with your JSON submission
2. **Within 1-2 minutes**: Ingestion workflow processes the submission
3. **If Valid**: Result is stored, issue is commented and closed
4. **If Invalid**: Error comment is posted with validation details
5. **After Storage**: Aggregation workflow runs automatically
6. **After Aggregation**: Dashboard is automatically updated

## Viewing Reporting

### Accessing the Dashboard

The dashboard is available at:
```
https://<username>.github.io/pawmate-ai-results/
```

For example: `https://rsdickerson.github.io/pawmate-ai-results/`

### Dashboard Features

#### Interactive Charts

The dashboard displays three interactive charts:

1. **Pass Rate Chart**: Shows quality metrics (pass rate percentage)
2. **Duration Chart**: Shows speed metrics (execution duration in minutes)
3. **Composite Metrics Chart**: Shows combined fast+quality score

#### Sort Options

Use the sort buttons to organize leaderboard data:

- **Quality (Pass Rate)**: Sorts by highest pass rate (best quality first)
- **Speed (Duration)**: Sorts by lowest duration (fastest first)
- **Composite (Fast + Quality Score)**: Sorts by composite score (default)

Click any sort button to update all charts with the selected sort order.

#### Understanding Metrics

- **Pass Rate**: Percentage of acceptance tests that passed (0-100%)
  - Higher is better (indicates better quality)
- **Duration**: Total execution time in minutes
  - Lower is better (indicates faster execution)
- **Composite Score**: Combined metric balancing quality and speed
  - Higher is better (indicates best overall performance)

### Downloading CSV Exports

1. Navigate to the repository: `https://github.com/<username>/pawmate-ai-results`
2. Go to the `aggregates/` directory
3. Click on `results.csv` to view or download
4. Open in Excel, Google Sheets, or any CSV-compatible application

The CSV includes:
- Tool name and version
- Target model (A or B)
- API style (REST or GraphQL)
- Pass rate
- Duration (minutes)
- LLM model used
- Submission timestamp

### Viewing Leaderboard Data

1. Navigate to the repository: `https://github.com/<username>/pawmate-ai-results`
2. Go to the `aggregates/` directory
3. Click on `leaderboard.json` to view raw JSON data

The leaderboard JSON includes:
- **Metadata**: Generation timestamp, total results count
- **Results**: Array of all submissions with complete metrics
- **Sorted Views**: Pre-sorted arrays by quality, speed, and composite score

### Viewing HTML Reports

1. Navigate to the repository: `https://github.com/<username>/pawmate-ai-results`
2. Go to the `results/compiled/` directory
3. Click on any HTML report file to view detailed comparison reports

HTML reports provide:
- Detailed test iteration results
- Side-by-side comparisons
- Comprehensive metrics breakdown

## Common Workflows

### Workflow 1: First-Time Submission

1. Run benchmark using challenge repository
2. Create GitHub personal access token
3. Configure token in `.submission.config`
4. Submit result using `submit_result.sh`
5. Verify issue creation and processing
6. View results on dashboard

### Workflow 2: Multiple Runs

1. Run multiple benchmarks with different configurations
2. Submit each result file separately
3. Each submission creates a new GitHub Issue
4. All results appear on dashboard after aggregation
5. Compare results using dashboard sort options

### Workflow 3: Resubmission After Error

1. If validation fails, review error comment on issue
2. Fix issues in result JSON file
3. Resubmit using `submit_result.sh` (creates new issue)
4. Verify successful processing
5. Check dashboard for updated results

## Troubleshooting

### Submission Errors

#### Token Issues

**Error**: "GitHub authentication token is required"

**Solutions**:
- Verify token is set in environment variable or config file
- Check token has `repo` scope
- Ensure token hasn't expired
- Try regenerating token if issues persist

#### Validation Failures

**Error**: Issue comment shows validation errors

**Solutions**:
- Review validation error messages in issue comment
- Check that all required fields are present
- Verify field types match schema requirements
- Ensure JSON is valid (no syntax errors)
- Reference [Schema v3.0 Field Reference](../schemas/schema-v3.0-field-reference.md)

#### Issue Creation Failures

**Error**: "Failed to create GitHub Issue"

**Solutions**:
- Verify repository exists: `rsdickerson/pawmate-ai-results`
- Check token has correct permissions (`repo` scope)
- Ensure token hasn't been revoked
- Check network connectivity
- Review script output for detailed error messages

### Dashboard Issues

#### Data Not Appearing

**Issue**: Dashboard shows "Error Loading Data" or no data

**Solutions**:
- Verify aggregation workflow has run (check Actions tab)
- Ensure `aggregates/leaderboard.json` exists in repository
- Check that your submission was processed successfully
- Wait a few minutes for aggregation to complete
- Try refreshing the dashboard page

#### Charts Not Updating

**Issue**: Charts don't update when changing sort options

**Solutions**:
- Check browser console for JavaScript errors
- Verify leaderboard JSON is valid
- Try hard refresh (Ctrl+F5 or Cmd+Shift+R)
- Clear browser cache
- Check that Chart.js library loaded correctly

### Workflow Issues

#### Submission Not Processing

**Issue**: Issue created but no workflow runs

**Solutions**:
- Verify issue has `submission` label (should be automatic)
- Check Actions tab for workflow runs
- Ensure workflows are enabled in repository settings
- Check workflow file exists: `.github/workflows/ingest-submission.yml`
- Try manually triggering workflow

#### Aggregation Not Running

**Issue**: Submission stored but not aggregated

**Solutions**:
- Check that result file was stored in `submissions/` directory
- Verify aggregation workflow exists: `.github/workflows/aggregate.yml`
- Check Actions tab for workflow runs
- Ensure workflow has `contents: write` permission
- Try manually triggering aggregation workflow

## FAQ

### Q: How long does it take for results to appear on the dashboard?

A: Typically 2-5 minutes after submission:
- 1-2 minutes for ingestion and storage
- 1-2 minutes for aggregation
- 1 minute for dashboard deployment

### Q: Can I submit multiple results from the same run?

A: Yes, but only the latest submission with the same `run_id` will be kept. Older submissions with the same `run_id` are replaced.

### Q: What if my submission has validation errors?

A: The issue will receive a detailed error comment. Fix the issues in your JSON file and resubmit (creates a new issue). The old issue can be left open or closed manually.

### Q: Can I view results before they're aggregated?

A: Yes, stored result files are in `submissions/YYYY/MM/` directories. However, the dashboard only shows aggregated data.

### Q: How do I update my submission?

A: Fix the JSON file and resubmit using `submit_result.sh`. This creates a new issue. The system will replace the old file if the `run_id` matches.

### Q: What permissions does my GitHub token need?

A: Only the `repo` scope is required. This allows creating issues in the repository.

### Q: Can I submit results manually without the script?

A: Yes, you can create a GitHub Issue manually using the submission template at `.github/ISSUE_TEMPLATE/submission.yml`. However, using `submit_result.sh` is recommended for proper formatting and validation.

## Reference Information

### File Locations

- **Submission Script**: `pawmate-ai-challenge/scripts/submit_result.sh`
- **Result Files**: `pawmate-ai-challenge/runs/YYYYMMDDTHHmm/*.json`
- **Schema Documentation**: `pawmate-ai-results/schemas/`
- **Dashboard**: `https://<username>.github.io/pawmate-ai-results/`
- **CSV Export**: `pawmate-ai-results/aggregates/results.csv`
- **Leaderboard**: `pawmate-ai-results/aggregates/leaderboard.json`

### Schema Reference

- [Schema v3.0 Design](../schemas/schema-v3.0-design.md) - Complete schema architecture
- [Schema v3.0 Field Reference](../schemas/schema-v3.0-field-reference.md) - Detailed field documentation
- [Schema v3.0 JSON Schema](../schemas/result-schema-v3.0.json) - JSON Schema definition

### Related Documentation

- [System Overview](SYSTEM_OVERVIEW.md) - Complete system architecture
- [Administrator Setup](ADMINISTRATOR_SETUP.md) - Setup instructions for administrators
- [GitHub Pages Setup](GITHUB_PAGES_SETUP.md) - Detailed Pages configuration

## Support

For issues or questions:
1. Check this guide and troubleshooting section
2. Review GitHub Issue comments for validation errors
3. Check workflow logs in Actions tab
4. Contact repository maintainers if issues persist

