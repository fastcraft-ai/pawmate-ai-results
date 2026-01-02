# Schema v3.0 Design Document

## Overview

Schema v3.0 extends v2.0 to support automated GitHub Issues-based submission workflow, time-partitioned storage, enhanced validation tracking, and aggregation/leaderboard integration. All core functionality from v2.0 is preserved.

## Core Structure (Preserved from v2.0)

The schema maintains the same top-level structure:
- `schema_version`: "3.0" (updated enum)
- `result_data`: Main container object

### Core Required Sections (Unchanged)
1. **`run_identity`**: Tool and run identification (all fields preserved)
2. **`implementations`**: API and/or UI implementations (structure preserved)
3. **`submission`**: Submission metadata (enhanced with GitHub Issue fields)

## New Sections in v3.0

### 1. Enhanced `submission` Object

**New Fields Added:**
- `github_issue` (optional object): GitHub Issue tracking
  - `issue_number` (integer): GitHub Issue number
  - `issue_url` (string): Full URL to the GitHub Issue
  - `issue_created_at` (string, ISO-8601): When the issue was created
  - `issue_closed_at` (string, ISO-8601, optional): When the issue was closed (if applicable)

**Rationale**: Enables tracking of submissions via GitHub Issues workflow, linking result files to their source issues.

### 2. New `processing` Object (Optional)

**Purpose**: Track automated ingestion and processing pipeline status.

**Fields:**
- `ingested_timestamp` (string, ISO-8601, optional): When the submission was ingested from GitHub Issue
- `processed_timestamp` (string, ISO-8601, optional): When processing completed successfully
- `validation_status` (string, enum): Status of validation
  - Values: `"pending"`, `"valid"`, `"invalid"`, `"error"`
- `validation_errors` (array of strings, optional): List of validation error messages (if validation failed)
- `storage_status` (string, enum, optional): Status of storage operation
  - Values: `"pending"`, `"stored"`, `"failed"`, `"duplicate_replaced"`

**Rationale**: Enables tracking of automated pipeline processing, validation results, and storage operations for debugging and monitoring.

### 3. New `storage_metadata` Object (Optional)

**Purpose**: Support time-partitioned storage and file management.

**Fields:**
- `storage_path` (string, optional): Relative path where file is stored (e.g., `submissions/2025/01/run_id.json`)
- `partition_year` (integer, optional): Year component for time-partitioned directory
- `partition_month` (integer, optional): Month component for time-partitioned directory (1-12)
- `file_name` (string, optional): Final stored filename (typically `{run_id}.json`)
- `stored_at` (string, ISO-8601, optional): Timestamp when file was stored

**Rationale**: Enables time-partitioned storage structure (`submissions/YYYY/MM/`) and tracking of storage location for efficient retrieval and organization.

### 4. New `validation_metadata` Object (Optional)

**Purpose**: Detailed validation tracking and audit trail.

**Fields:**
- `validated_at` (string, ISO-8601, optional): When validation was performed
- `validator_version` (string, optional): Version of validation script/schema used
- `schema_version_validated` (string, optional): Schema version that was validated against (should match `schema_version`)
- `validation_passed` (boolean, optional): Whether validation passed
- `validation_errors_detail` (array of objects, optional): Detailed validation errors
  - Each object contains:
    - `field_path` (string): JSON path to the field with error
    - `error_message` (string): Human-readable error message
    - `error_code` (string, optional): Machine-readable error code

**Rationale**: Provides detailed validation audit trail for debugging submission issues and tracking validation improvements over time.

### 5. New `aggregation_metadata` Object (Optional)

**Purpose**: Track leaderboard inclusion and aggregation status.

**Fields:**
- `last_aggregated_at` (string, ISO-8601, optional): Timestamp of last successful aggregation run
- `included_in_leaderboard` (boolean, optional): Whether this result is included in current leaderboard
- `aggregation_version` (string, optional): Version of aggregation script that last processed this result
- `csv_exported` (boolean, optional): Whether this result was included in CSV export
- `csv_export_timestamp` (string, ISO-8601, optional): When CSV export last included this result

**Rationale**: Enables tracking of which results are included in leaderboards, when aggregation occurred, and CSV export status for data processing workflows.

## Field Requirements Summary

### Required Fields (Top Level)
- `schema_version`: "3.0"
- `result_data`: Object containing:
  - `run_identity`: Required (all fields preserved from v2.0)
  - `implementations`: Required (at least one of `api` or `ui` must be present)
  - `submission`: Required (enhanced with optional GitHub Issue fields)

### Optional Fields (New in v3.0)
- `result_data.processing`: Optional (added by ingestion pipeline)
- `result_data.storage_metadata`: Optional (added by storage script)
- `result_data.validation_metadata`: Optional (added by validation script)
- `result_data.aggregation_metadata`: Optional (added by aggregation script)
- `result_data.submission.github_issue`: Optional (added when submitted via GitHub Issue)

## Backward Compatibility

### v2.0 → v3.0 Migration
- All v2.0 fields are preserved and remain required/optional as before
- New v3.0 fields are all optional, ensuring v2.0 files can be upgraded without breaking changes
- Schema version field distinguishes v2.0 from v3.0 files
- Validation scripts should support both versions during transition period

### Compatibility Strategy
- v3.0 schema validator should accept v2.0 files (with migration path)
- Aggregation scripts should handle both v2.0 and v3.0 formats
- Storage scripts should add v3.0 metadata fields when processing files

## Design Decisions

1. **All new fields are optional**: Ensures backward compatibility and allows gradual adoption
2. **Separate metadata objects**: Keeps concerns separated (processing, storage, validation, aggregation)
3. **ISO-8601 timestamps**: Consistent with v2.0 timestamp format
4. **Enum values for status fields**: Provides clear state tracking for automation workflows
5. **Detailed error tracking**: Enables better debugging and user feedback in GitHub Issue comments

## Use Cases Enabled

1. **GitHub Issue Submission**: Track which issue a result came from
2. **Automated Ingestion**: Track when and how results were ingested
3. **Time-Partitioned Storage**: Organize files by submission date for efficient retrieval
4. **Validation Tracking**: Provide detailed feedback on validation failures
5. **Leaderboard Management**: Track which results are included in aggregations
6. **CSV Export**: Track which results have been exported to CSV

## Example v3.0 Structure

```json
{
  "schema_version": "3.0",
  "result_data": {
    "run_identity": { /* v2.0 structure preserved */ },
    "implementations": { /* v2.0 structure preserved */ },
    "submission": {
      "submitted_timestamp": "2025-01-01T10:00:00.000Z",
      "submitted_by": "username",
      "submission_method": "automated",
      "notes": "Optional notes",
      "github_issue": {
        "issue_number": 123,
        "issue_url": "https://github.com/org/repo/issues/123",
        "issue_created_at": "2025-01-01T10:00:00.000Z",
        "issue_closed_at": "2025-01-01T10:05:00.000Z"
      }
    },
    "processing": {
      "ingested_timestamp": "2025-01-01T10:01:00.000Z",
      "processed_timestamp": "2025-01-01T10:02:00.000Z",
      "validation_status": "valid",
      "storage_status": "stored"
    },
    "storage_metadata": {
      "storage_path": "submissions/2025/01/cursor_modelA_REST_run1_20250101T1000.json",
      "partition_year": 2025,
      "partition_month": 1,
      "file_name": "cursor_modelA_REST_run1_20250101T1000.json",
      "stored_at": "2025-01-01T10:02:00.000Z"
    },
    "validation_metadata": {
      "validated_at": "2025-01-01T10:01:30.000Z",
      "validator_version": "1.0.0",
      "schema_version_validated": "3.0",
      "validation_passed": true
    },
    "aggregation_metadata": {
      "last_aggregated_at": "2025-01-01T10:10:00.000Z",
      "included_in_leaderboard": true,
      "aggregation_version": "2.0.0",
      "csv_exported": true,
      "csv_export_timestamp": "2025-01-01T10:10:00.000Z"
    }
  }
}
```

