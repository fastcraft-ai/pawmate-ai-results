# PawMate Benchmark Result Schema Documentation

## Overview

This directory contains the JSON Schema specification and documentation for PawMate AI Challenge benchmark result files. The current schema version is **v3.0**, which extends v2.0 with optional metadata sections for automated GitHub Issues-based submission workflow, time-partitioned storage, validation tracking, and aggregation management.

### Schema Versions

- **v3.0** (Current): Extends v2.0 with optional metadata for automated workflows
- **v2.0**: Treats API and UI as independent implementations
- **v1.0**: Legacy schema (deprecated)

### Key Features of v3.0

- ✅ **Backward Compatible**: All v2.0 fields preserved unchanged
- ✅ **GitHub Issues Integration**: Track submissions via GitHub Issues
- ✅ **Automated Processing**: Track ingestion, validation, and storage status
- ✅ **Time-Partitioned Storage**: Organize files by submission date
- ✅ **Enhanced Validation**: Detailed validation error tracking
- ✅ **Aggregation Tracking**: Monitor leaderboard inclusion and CSV export status

## Quick Start

### Creating a Valid v3.0 Result File

A minimal valid v3.0 result file requires:

1. **Top-level fields**: `schema_version` and `result_data`
2. **Run identity**: All 9 required fields in `run_identity`
3. **At least one implementation**: Either `api` or `ui` (or both)
4. **Submission metadata**: `submitted_timestamp`, `submitted_by`, `submission_method`

All v3.0 metadata sections (`processing`, `storage_metadata`, `validation_metadata`, `aggregation_metadata`, `submission.github_issue`) are **optional** and typically added by automated processing pipelines.

### Minimal Example (API Only)

```json
{
  "schema_version": "3.0",
  "result_data": {
    "run_identity": {
      "tool_name": "Cursor",
      "tool_version": "v0.43",
      "run_id": "cursor_modelA_REST_run1_20250101T1000",
      "run_number": 1,
      "target_model": "A",
      "api_style": "REST",
      "spec_reference": "SPEC_VERSION",
      "workspace_path": "/path/to/workspace",
      "run_environment": "macOS 14.6.0, Node.js 20.10.0"
    },
    "implementations": {
      "api": {
        "generation_metrics": {
          "llm_model": "claude-sonnet-4.5",
          "start_timestamp": "2025-01-01T10:00:00.000Z",
          "end_timestamp": "2025-01-01T10:15:00.000Z",
          "duration_minutes": 15.0,
          "clarifications_count": 0,
          "interventions_count": 0,
          "reruns_count": 1
        },
        "acceptance": {
          "pass_count": 45,
          "fail_count": 2,
          "not_run_count": 0,
          "passrate": 0.957
        },
        "artifacts": {
          "contract_artifact_path": "docs/API_Contract.md",
          "run_instructions_path": "docs/Run_Instructions.md"
        }
      }
    },
    "submission": {
      "submitted_timestamp": "2025-01-01T10:20:00.000Z",
      "submitted_by": "username",
      "submission_method": "automated"
    }
  }
}
```

## Schema Structure

### Top-Level Structure

```json
{
  "schema_version": "3.0",
  "result_data": {
    "run_identity": { /* required */ },
    "implementations": { /* required */ },
    "submission": { /* required */ },
    "processing": { /* optional v3.0 */ },
    "storage_metadata": { /* optional v3.0 */ },
    "validation_metadata": { /* optional v3.0 */ },
    "aggregation_metadata": { /* optional v3.0 */ }
  }
}
```

### Core Required Sections

#### 1. `run_identity` (Required)

Tool and run identification information. All 9 fields are required:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `tool_name` | string | Name of the AI tool | `"Cursor"` |
| `tool_version` | string | Version of the tool | `"v0.43"` |
| `run_id` | string | Unique run identifier | `"cursor_modelA_REST_run1_20250101T1000"` |
| `run_number` | integer | Run number (1 or 2) | `1` |
| `target_model` | string | Target model ("A" or "B") | `"A"` |
| `api_style` | string | API style ("REST" or "GraphQL") | `"REST"` |
| `spec_reference` | string | Specification reference | `"SPEC_VERSION"` |
| `workspace_path` | string | Workspace path | `"/path/to/workspace"` |
| `run_environment` | string | Runtime environment description | `"macOS 14.6.0, Node.js 20.10.0"` |

#### 2. `implementations` (Required)

Container for API and/or UI implementation data. At least one of `api` or `ui` must be present.

**API Implementation** (`api` - optional but required fields if present):
- `generation_metrics` (required): LLM model, timestamps, duration, counts
- `acceptance` (required): Test results (pass_count, fail_count, passrate)
- `artifacts` (required): Paths to contract, instructions, evidence files
- `quality_metrics` (optional): Determinism, overreach, contract completeness
- `scores` (optional): Scoring metrics (correctness, reproducibility, etc.)

**UI Implementation** (`ui` - optional but required fields if present):
- `generation_metrics` (required): LLM model, timestamps, duration, counts
- `build_success` (required): Boolean indicating successful build
- `artifacts` (required): Paths to UI source and run summary

See [Field Reference](#field-reference-documentation) for complete field details.

#### 3. `submission` (Required)

Submission metadata with core fields (v2.0) and optional GitHub Issue tracking (v3.0):

**Required Fields:**
- `submitted_timestamp` (ISO-8601 UTC): When result was submitted
- `submitted_by` (string): Submitter identifier
- `submission_method` (enum): `"automated"` or `"manual"`

**Optional Fields:**
- `notes` (string): Optional submission notes
- `github_issue` (object, v3.0): GitHub Issue tracking (see below)

### v3.0 Optional Metadata Sections

#### `submission.github_issue` (Optional)

GitHub Issue tracking for automated submission workflow:

```json
"github_issue": {
  "issue_number": 123,
  "issue_url": "https://github.com/org/pawmate-ai-results/issues/123",
  "issue_created_at": "2025-01-01T10:00:00.000Z",
  "issue_closed_at": "2025-01-01T10:05:00.000Z"  // optional
}
```

#### `processing` (Optional)

Automated ingestion and processing pipeline status:

```json
"processing": {
  "ingested_timestamp": "2025-01-01T10:01:00.000Z",
  "processed_timestamp": "2025-01-01T10:02:00.000Z",
  "validation_status": "valid",  // enum: "pending", "valid", "invalid", "error"
  "validation_errors": [],  // array of error messages (if validation failed)
  "storage_status": "stored"  // enum: "pending", "stored", "failed", "duplicate_replaced"
}
```

#### `storage_metadata` (Optional)

Time-partitioned storage and file management:

```json
"storage_metadata": {
  "storage_path": "submissions/2025/01/cursor_modelA_REST_run1_20250101T1000.json",
  "partition_year": 2025,
  "partition_month": 1,  // 1-12
  "file_name": "cursor_modelA_REST_run1_20250101T1000.json",
  "stored_at": "2025-01-01T10:02:00.000Z"
}
```

#### `validation_metadata` (Optional)

Detailed validation tracking and audit trail:

```json
"validation_metadata": {
  "validated_at": "2025-01-01T10:01:30.000Z",
  "validator_version": "1.0.0",
  "schema_version_validated": "3.0",
  "validation_passed": true,
  "validation_errors_detail": [  // array of error objects
    {
      "field_path": "result_data.run_identity.run_id",
      "error_message": "Field 'run_id' is required",
      "error_code": "REQUIRED_FIELD_MISSING"  // optional
    }
  ]
}
```

#### `aggregation_metadata` (Optional)

Leaderboard inclusion and aggregation status:

```json
"aggregation_metadata": {
  "last_aggregated_at": "2025-01-01T10:10:00.000Z",
  "included_in_leaderboard": true,
  "aggregation_version": "2.0.0",
  "csv_exported": true,
  "csv_export_timestamp": "2025-01-01T10:10:00.000Z"
}
```

## Complete Examples

### Example 1: API + UI Implementation with v3.0 Metadata

```json
{
  "schema_version": "3.0",
  "result_data": {
    "run_identity": {
      "tool_name": "Cursor",
      "tool_version": "v0.43",
      "run_id": "cursor_modelA_REST_run1_20250101T1000",
      "run_number": 1,
      "target_model": "A",
      "api_style": "REST",
      "spec_reference": "SPEC_VERSION",
      "workspace_path": "/path/to/workspace",
      "run_environment": "macOS 14.6.0, Node.js 20.10.0"
    },
    "implementations": {
      "api": {
        "generation_metrics": {
          "llm_model": "claude-sonnet-4.5",
          "start_timestamp": "2025-01-01T10:00:00.000Z",
          "end_timestamp": "2025-01-01T10:15:00.000Z",
          "duration_minutes": 15.0,
          "clarifications_count": 0,
          "interventions_count": 0,
          "reruns_count": 1,
          "test_runs": [
            {
              "run_number": 1,
              "start_timestamp": "2025-01-01T10:15:00.000Z",
              "end_timestamp": "2025-01-01T10:16:00.000Z",
              "duration_minutes": 1.0,
              "total_tests": 47,
              "passed": 45,
              "failed": 2,
              "pass_rate": 0.957
            }
          ],
          "llm_usage": {
            "input_tokens": 50000,
            "output_tokens": 25000,
            "total_tokens": 75000,
            "requests_count": 150,
            "estimated_cost_usd": 2.50,
            "cost_currency": "USD",
            "usage_source": "tool_reported"
          }
        },
        "acceptance": {
          "pass_count": 45,
          "fail_count": 2,
          "not_run_count": 0,
          "passrate": 0.957
        },
        "quality_metrics": {
          "determinism_compliance": "Pass",
          "overreach_incidents_count": 0,
          "contract_completeness_passrate": 1.0,
          "instructions_quality_rating": 100,
          "reproducibility_rating": "None"
        },
        "artifacts": {
          "contract_artifact_path": "docs/API_Contract.md",
          "run_instructions_path": "docs/Run_Instructions.md",
          "source_code_path": "backend/",
          "acceptance_checklist_path": "benchmark/acceptance_checklist.md"
        },
        "scores": {
          "correctness_C": 95,
          "reproducibility_R": 100,
          "determinism_D": 100,
          "effort_E": 90,
          "speed_S": 85,
          "contract_docs_K": 100,
          "penalty_overreach_PO": 0,
          "overall_score": 94.5
        }
      },
      "ui": {
        "generation_metrics": {
          "llm_model": "claude-sonnet-4.5",
          "start_timestamp": "2025-01-01T20:30:00.000Z",
          "end_timestamp": "2025-01-01T21:10:00.000Z",
          "duration_minutes": 40.0,
          "clarifications_count": 0,
          "interventions_count": 1,
          "reruns_count": 0,
          "backend_changes_required": false
        },
        "build_success": true,
        "artifacts": {
          "ui_source_path": "ui/",
          "ui_run_summary_path": "benchmark/ui_run_summary.md"
        }
      }
    },
    "submission": {
      "submitted_timestamp": "2025-01-01T21:15:00.000Z",
      "submitted_by": "username",
      "submission_method": "automated",
      "notes": "Complete API + UI implementation",
      "github_issue": {
        "issue_number": 123,
        "issue_url": "https://github.com/org/pawmate-ai-results/issues/123",
        "issue_created_at": "2025-01-01T21:15:00.000Z",
        "issue_closed_at": "2025-01-01T21:20:00.000Z"
      }
    },
    "processing": {
      "ingested_timestamp": "2025-01-01T21:16:00.000Z",
      "processed_timestamp": "2025-01-01T21:17:00.000Z",
      "validation_status": "valid",
      "storage_status": "stored"
    },
    "storage_metadata": {
      "storage_path": "submissions/2025/01/cursor_modelA_REST_run1_20250101T1000.json",
      "partition_year": 2025,
      "partition_month": 1,
      "file_name": "cursor_modelA_REST_run1_20250101T1000.json",
      "stored_at": "2025-01-01T21:17:00.000Z"
    },
    "validation_metadata": {
      "validated_at": "2025-01-01T21:16:30.000Z",
      "validator_version": "1.0.0",
      "schema_version_validated": "3.0",
      "validation_passed": true
    },
    "aggregation_metadata": {
      "last_aggregated_at": "2025-01-01T21:30:00.000Z",
      "included_in_leaderboard": true,
      "aggregation_version": "2.0.0",
      "csv_exported": true,
      "csv_export_timestamp": "2025-01-01T21:30:00.000Z"
    }
  }
}
```

### Example 2: API Only (Minimal v3.0)

```json
{
  "schema_version": "3.0",
  "result_data": {
    "run_identity": {
      "tool_name": "Cursor",
      "tool_version": "v0.43",
      "run_id": "cursor_modelA_REST_run1_20250101T1000",
      "run_number": 1,
      "target_model": "A",
      "api_style": "REST",
      "spec_reference": "SPEC_VERSION",
      "workspace_path": "/path/to/workspace",
      "run_environment": "macOS 14.6.0, Node.js 20.10.0"
    },
    "implementations": {
      "api": {
        "generation_metrics": {
          "llm_model": "claude-sonnet-4.5",
          "start_timestamp": "2025-01-01T10:00:00.000Z",
          "end_timestamp": "2025-01-01T10:15:00.000Z",
          "duration_minutes": 15.0,
          "clarifications_count": 0,
          "interventions_count": 0,
          "reruns_count": 1
        },
        "acceptance": {
          "pass_count": 45,
          "fail_count": 2,
          "not_run_count": 0,
          "passrate": 0.957
        },
        "artifacts": {
          "contract_artifact_path": "docs/API_Contract.md",
          "run_instructions_path": "docs/Run_Instructions.md"
        }
      }
    },
    "submission": {
      "submitted_timestamp": "2025-01-01T10:20:00.000Z",
      "submitted_by": "username",
      "submission_method": "automated"
    }
  }
}
```

## Migration from v2.0 to v3.0

### Automatic Migration

To upgrade a v2.0 file to v3.0:

1. **Update schema version**: Change `"schema_version": "2.0"` to `"schema_version": "3.0"`
2. **All other fields remain unchanged**: v2.0 files are valid v3.0 files (backward compatible)
3. **Optionally add v3.0 sections**: New metadata sections can be added as needed

### Manual Migration Example

**v2.0 file:**
```json
{
  "schema_version": "2.0",
  "result_data": {
    "run_identity": { /* ... */ },
    "implementations": { /* ... */ },
    "submission": {
      "submitted_timestamp": "2025-01-01T10:00:00.000Z",
      "submitted_by": "username",
      "submission_method": "automated"
    }
  }
}
```

**v3.0 file (minimal upgrade):**
```json
{
  "schema_version": "3.0",  // Only change needed
  "result_data": {
    "run_identity": { /* ... unchanged ... */ },
    "implementations": { /* ... unchanged ... */ },
    "submission": {
      "submitted_timestamp": "2025-01-01T10:00:00.000Z",
      "submitted_by": "username",
      "submission_method": "automated"
      // v3.0 optional sections can be added later
    }
  }
}
```

### Backward Compatibility

- ✅ **v2.0 files are valid**: v3.0 validators accept v2.0 files (with migration path)
- ✅ **v3.0 files work with v2.0 tools**: New optional sections are ignored by v2.0 tools
- ✅ **Core functionality identical**: All v2.0 core fields preserved exactly

For detailed migration information, see [Schema Comparison Document](./schema-v2.0-to-v3.0-comparison.md).

## Validation

### Using the JSON Schema

The schema file `result-schema-v3.0.json` can be used with any JSON Schema Draft 7 validator:

**Python (jsonschema):**
```python
import json
import jsonschema

with open('result-schema-v3.0.json') as f:
    schema = json.load(f)

with open('my-result.json') as f:
    data = json.load(f)

jsonschema.validate(instance=data, schema=schema)
```

**Node.js (ajv):**
```javascript
const Ajv = require('ajv');
const ajv = new Ajv();
const validate = ajv.compile(require('./result-schema-v3.0.json'));

const valid = validate(myResultData);
if (!valid) console.log(validate.errors);
```

### Validation Rules

- **Required fields**: All fields in `required` arrays must be present
- **Type validation**: Fields must match specified types (string, integer, number, boolean, object, array)
- **Enum values**: Fields with `enum` must use one of the allowed values
- **Pattern matching**: Timestamp fields must match ISO-8601 UTC pattern: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Numeric constraints**: Numbers must satisfy minimum/maximum constraints (e.g., passrate 0-1, scores 0-100)

## Field Reference Documentation

For complete field-by-field documentation with types, required/optional status, descriptions, and examples, see:

📖 **[Schema v3.0 Field Reference](./schema-v3.0-field-reference.md)**

This document provides detailed specifications for every field in the schema.

## Additional Documentation

- **[Schema v3.0 Design Document](./schema-v3.0-design.md)**: Structure, rationale, and design decisions
- **[Schema v2.0 to v3.0 Comparison](./schema-v2.0-to-v3.0-comparison.md)**: Detailed migration guide and change documentation
- **[JSON Schema File](./result-schema-v3.0.json)**: The actual validation schema (JSON Schema Draft 7)

## Timestamp Format

All timestamp fields use **ISO-8601 UTC format**:

- **Pattern**: `YYYY-MM-DDTHH:mm:ss.sssZ`
- **Example**: `2025-01-01T10:00:00.000Z`
- **Optional milliseconds**: `.sss` is optional (e.g., `2025-01-01T10:00:00Z` is also valid)
- **Always UTC**: All timestamps must end with `Z` (UTC timezone)

## Common Patterns

### Run ID Format

Run IDs typically follow this pattern:
```
{tool-slug}_{model}_{api-type}_{run-number}_{timestamp}
```

Example: `cursor_modelA_REST_run1_20250101T1000`

### File Naming Convention

When stored, result files typically use the run_id as the filename:
```
{run_id}.json
```

Example: `cursor_modelA_REST_run1_20250101T1000.json`

## Support and Questions

For questions about the schema:
1. Review the [Field Reference](./schema-v3.0-field-reference.md) for detailed field specifications
2. Check the [Design Document](./schema-v3.0-design.md) for structure and rationale
3. See the [Comparison Document](./schema-v2.0-to-v3.0-comparison.md) for migration guidance
4. Validate your JSON against `result-schema-v3.0.json` using a JSON Schema validator

## Version History

- **v3.0** (Current): Added optional metadata sections for automated workflows
- **v2.0**: Independent API and UI implementations
- **v1.0**: Legacy schema (deprecated)

