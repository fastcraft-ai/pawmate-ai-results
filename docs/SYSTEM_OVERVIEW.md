# PawMate AI Results System - System Overview

## Introduction

The PawMate AI Results system is an automated workflow for collecting, validating, storing, aggregating, and visualizing benchmark results from the PawMate AI Challenge. This system replaces the previous email-based submission process with a fully automated GitHub Issues-based workflow that provides real-time validation, organized storage, and interactive visualization.

## System Architecture

### High-Level Workflow

The system follows a complete automated pipeline:

```
GitHub Issue Creation → Ingestion → Validation → Storage → Aggregation → Visualization
```

1. **Submission**: Developers submit results via GitHub Issues using `submit_result.sh`
2. **Ingestion**: GitHub Actions workflow automatically extracts JSON from issue body
3. **Validation**: JSON is validated against Schema v3.0
4. **Storage**: Validated results are stored in time-partitioned directories
5. **Aggregation**: Results are aggregated into leaderboards and CSV exports
6. **Visualization**: Interactive dashboard deployed to GitHub Pages

### Key Components

#### 1. Schema v3.0
- **Purpose**: Standardized JSON schema for result submissions
- **Location**: `pawmate-ai-results/schemas/result-schema-v3.0.json`
- **Features**:
  - Extends v2.0 with GitHub Issue tracking
  - Supports automated processing metadata
  - Time-partitioned storage metadata
  - Validation and aggregation tracking
- **Documentation**: See `schemas/schema-v3.0-design.md` and `schemas/schema-v3.0-field-reference.md`

#### 2. GitHub Issue Template
- **Purpose**: Standardized submission format for GitHub Issues
- **Location**: `pawmate-ai-results/.github/ISSUE_TEMPLATE/submission.yml`
- **Features**:
  - Automatic label application (`submission`, `results`)
  - Structured JSON submission field
  - Clear instructions for submitters

#### 3. Submission Script (`submit_result.sh`)
- **Purpose**: Command-line tool for submitting results
- **Location**: `pawmate-ai-challenge/scripts/submit_result.sh`
- **Features**:
  - Validates result JSON format
  - Creates GitHub Issues programmatically via REST API
  - Handles GitHub token authentication
  - Provides clear error messages

#### 4. Ingestion Pipeline
- **Workflow**: `.github/workflows/ingest-submission.yml`
- **Trigger**: Issues with `submission` label are opened
- **Process**:
  1. **Ingestion** (`ingest-issue.py`): Extracts JSON from issue body
  2. **Validation** (`validate-result-v3.py`): Validates against Schema v3.0
  3. **Storage** (`store-result.py`): Stores in time-partitioned structure
- **Error Handling**: Comments on issues with validation errors, auto-closes successful submissions

#### 5. Time-Partitioned Storage
- **Structure**: `submissions/YYYY/MM/{run_id}.json`
- **Benefits**:
  - Organized by submission date
  - Efficient retrieval for aggregation
  - Prevents directory bloat
- **Duplicate Handling**: Latest submission replaces older files with same `run_id`

#### 6. Aggregation System
- **Script**: `scripts/aggregate_results.py`
- **Workflow**: `.github/workflows/aggregate.yml`
- **Trigger**: Automatically runs when new submissions are stored
- **Outputs**:
  - **CSV Export**: `aggregates/results.csv` - Flat data export for analysis
  - **Leaderboard JSON**: `aggregates/leaderboard.json` - Structured data with multiple sort views
  - **HTML Reports**: `results/compiled/*.html` - Detailed comparison reports

#### 7. Visualization Dashboard
- **Site Generator**: `scripts/generate-site.py`
- **Deployment Workflow**: `.github/workflows/deploy-pages.yml`
- **Trigger**: Automatically deploys when `aggregates/leaderboard.json` is updated
- **Features**:
  - Interactive charts (Pass Rate, Duration, Composite Score)
  - Multiple sort options (Quality, Speed, Composite)
  - Real-time data updates
  - CSV download capability
  - Responsive design

## System Flow Diagram

```
┌─────────────────┐
│  Developer      │
│  Runs Benchmark │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ submit_result.sh│
│ Creates GitHub  │
│ Issue           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ ingest-submission│
│ Workflow        │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│Ingest  │ │Validate │
│JSON    │ │Schema   │
│        │ │v3.0     │
└───┬────┘ └────┬─────┘
    │          │
    └────┬─────┘
         │
         ▼
┌─────────────────┐
│ Store Result    │
│ submissions/    │
│ YYYY/MM/        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ aggregate.yml   │
│ Workflow        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │
│ - CSV Export    │
│ - Leaderboard   │
│ - HTML Reports  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ deploy-pages.yml│
│ Workflow        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Pages    │
│ Dashboard       │
└─────────────────┘
```

## Key Features

### Automated Submission
- **GitHub Issues Integration**: Submissions are created as GitHub Issues with structured JSON
- **Automatic Processing**: No manual intervention required for valid submissions
- **Real-time Feedback**: Validation errors are immediately posted as issue comments

### Validation
- **Schema v3.0 Compliance**: All submissions validated against comprehensive JSON Schema
- **Detailed Error Messages**: Clear, actionable feedback for validation failures
- **Email Notifications**: Administrators notified of validation failures

### Time-Partitioned Storage
- **Organized Structure**: Results stored by year/month for efficient management
- **Duplicate Prevention**: Latest submission replaces older versions
- **Scalable**: Handles large volumes of submissions without performance degradation

### CSV Export
- **Flat Data Format**: Easy import into spreadsheet applications
- **Comprehensive Fields**: Includes tool name, version, model, API style, pass rate, duration, LLM model, submission timestamp
- **Regular Updates**: Automatically regenerated when new submissions arrive

### Leaderboard
- **Multiple Sort Views**: 
  - By Quality (Pass Rate)
  - By Speed (Duration)
  - By Composite Score (Fast + Quality)
- **Complete Data**: Shows all results, not just top N
- **Structured JSON**: Easy to consume programmatically

### Interactive Dashboard
- **Visual Charts**: Bar charts for Pass Rate, Duration, and Composite Score
- **Dynamic Sorting**: Switch between sort views with one click
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: Dashboard updates automatically when new data is aggregated

## Enhancements from Previous System

### Previous Email-Based System
- Manual email submission process
- Manual validation and storage
- No automated aggregation
- No visualization dashboard
- Limited error feedback

### Current GitHub Issues-Based System
- ✅ **Automated Submission**: Programmatic GitHub Issue creation
- ✅ **Automated Validation**: Real-time schema validation with detailed errors
- ✅ **Automated Storage**: Time-partitioned organization
- ✅ **Automated Aggregation**: Automatic leaderboard and CSV generation
- ✅ **Automated Visualization**: Interactive dashboard on GitHub Pages
- ✅ **Better Error Handling**: Issue comments with actionable feedback
- ✅ **Email Notifications**: Administrators notified of validation failures
- ✅ **Scalable Architecture**: Handles high submission volumes

## System Benefits

1. **Reduced Manual Work**: Fully automated pipeline eliminates manual processing
2. **Faster Feedback**: Real-time validation and error reporting
3. **Better Organization**: Time-partitioned storage and structured data
4. **Enhanced Visibility**: Interactive dashboard with multiple visualization options
5. **Improved Developer Experience**: Clear submission process and immediate feedback
6. **Scalability**: Handles growing submission volumes efficiently
7. **Audit Trail**: Complete tracking of submissions, validation, and processing

## Directory Structure

```
pawmate-ai-results/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── submission.yml          # GitHub Issue template
│   └── workflows/
│       ├── ingest-submission.yml   # Ingestion pipeline
│       ├── aggregate.yml           # Aggregation workflow
│       └── deploy-pages.yml        # Pages deployment
├── scripts/
│   ├── ingest-issue.py             # Extract JSON from issues
│   ├── validate-result-v3.py       # Schema validation
│   ├── store-result.py             # Time-partitioned storage
│   ├── aggregate_results.py        # Generate leaderboards/CSV
│   └── generate-site.py            # Generate dashboard HTML
├── schemas/
│   ├── result-schema-v3.0.json     # JSON Schema definition
│   ├── schema-v3.0-design.md        # Schema design documentation
│   └── schema-v3.0-field-reference.md  # Field reference
├── submissions/
│   └── YYYY/
│       └── MM/
│           └── {run_id}.json       # Time-partitioned storage
├── aggregates/
│   ├── results.csv                 # CSV export
│   └── leaderboard.json            # Leaderboard data
├── results/
│   └── compiled/
│       └── *.html                  # HTML comparison reports
└── site/
    └── index.html                  # Dashboard HTML (generated)
```

## Related Documentation

- [Administrator Setup Guide](ADMINISTRATOR_SETUP.md) - Setup and enablement instructions
- [Developer Guide](DEVELOPER_GUIDE.md) - How to submit results and use the dashboard
- [GitHub Pages Setup](GITHUB_PAGES_SETUP.md) - Detailed Pages configuration
- [Schema v3.0 Design](schemas/schema-v3.0-design.md) - Schema architecture
- [Schema v3.0 Field Reference](schemas/schema-v3.0-field-reference.md) - Complete field documentation

