# Schema v2.0 to v3.0 Comparison

This document details all changes, additions, and preserved elements when migrating from schema v2.0 to v3.0.

## Summary

Schema v3.0 extends v2.0 with new optional metadata sections to support:
- GitHub Issues-based submission workflow
- Automated ingestion and processing pipeline
- Time-partitioned storage
- Enhanced validation tracking
- Leaderboard and aggregation management

**Key Principle**: All v2.0 fields are preserved unchanged. All v3.0 additions are optional, ensuring backward compatibility.

---

## Preserved Elements (No Changes)

### Top-Level Structure
- ✅ `schema_version`: Enum updated from `["2.0"]` to `["3.0"]`, but structure unchanged
- ✅ `result_data`: Main container object structure unchanged

### `result_data.run_identity`
- ✅ **All fields preserved exactly as in v2.0**
- ✅ All 9 required fields: `tool_name`, `tool_version`, `run_id`, `run_number`, `target_model`, `api_style`, `spec_reference`, `workspace_path`, `run_environment`
- ✅ Field types, enums, and validation rules unchanged

### `result_data.implementations`
- ✅ **Structure completely preserved**
- ✅ `api` object: All fields and structure unchanged
  - ✅ `generation_metrics`: All fields preserved (llm_model, timestamps, durations, counts, test_runs, llm_usage)
  - ✅ `acceptance`: All fields preserved (pass_count, fail_count, not_run_count, passrate)
  - ✅ `quality_metrics`: Optional object preserved with all fields
  - ✅ `artifacts`: All required and optional fields preserved
  - ✅ `scores`: Optional object preserved with all fields
- ✅ `ui` object: All fields and structure unchanged
  - ✅ `generation_metrics`: All fields preserved (including backend_changes_required)
  - ✅ `build_success`: Required boolean preserved
  - ✅ `artifacts`: All required and optional fields preserved

### `result_data.submission` (Core Fields)
- ✅ **Core fields preserved exactly as in v2.0**
- ✅ `submitted_timestamp`: Required, ISO-8601 format, unchanged
- ✅ `submitted_by`: Required string, unchanged
- ✅ `submission_method`: Required enum `["automated", "manual"]`, unchanged
- ✅ `notes`: Optional string, unchanged

---

## Changes and Additions

### 1. Schema Version Enum Update

**v2.0:**
```json
"schema_version": {
  "type": "string",
  "enum": ["2.0"]
}
```

**v3.0:**
```json
"schema_version": {
  "type": "string",
  "enum": ["3.0"]
}
```

**Impact**: Breaking change for schema validation, but data structure remains compatible.

---

### 2. Enhanced `submission` Object

**Addition**: New optional `github_issue` object within `submission`

**v2.0:**
```json
"submission": {
  "submitted_timestamp": "...",
  "submitted_by": "...",
  "submission_method": "...",
  "notes": "..."  // optional
}
```

**v3.0:**
```json
"submission": {
  "submitted_timestamp": "...",  // preserved
  "submitted_by": "...",         // preserved
  "submission_method": "...",    // preserved
  "notes": "...",                // preserved
  "github_issue": {              // NEW - optional
    "issue_number": 123,
    "issue_url": "https://...",
    "issue_created_at": "...",
    "issue_closed_at": "..."     // optional
  }
}
```

**Rationale**: Enables tracking of GitHub Issue-based submissions, linking result files to their source issues for automated workflow support.

**Migration**: v2.0 files can be upgraded by adding `github_issue` object when submitted via GitHub Issues workflow.

---

### 3. New `processing` Object (Optional)

**v2.0**: Not present

**v3.0**: New optional top-level object in `result_data`

```json
"processing": {
  "ingested_timestamp": "...",      // optional
  "processed_timestamp": "...",     // optional
  "validation_status": "...",       // optional enum
  "validation_errors": [...],       // optional array
  "storage_status": "..."           // optional enum
}
```

**Fields:**
- `ingested_timestamp` (optional): When submission was ingested from GitHub Issue
- `processed_timestamp` (optional): When processing completed
- `validation_status` (optional): Enum `["pending", "valid", "invalid", "error"]`
- `validation_errors` (optional): Array of error messages
- `storage_status` (optional): Enum `["pending", "stored", "failed", "duplicate_replaced"]`

**Rationale**: Tracks automated ingestion pipeline status for monitoring, debugging, and workflow management.

**Migration**: v2.0 files don't have this section. It's added automatically by ingestion pipeline when processing v3.0 submissions.

---

### 4. New `storage_metadata` Object (Optional)

**v2.0**: Not present

**v3.0**: New optional top-level object in `result_data`

```json
"storage_metadata": {
  "storage_path": "...",        // optional
  "partition_year": 2025,       // optional
  "partition_month": 1,         // optional
  "file_name": "...",           // optional
  "stored_at": "..."            // optional
}
```

**Fields:**
- `storage_path` (optional): Relative path where file is stored (e.g., `submissions/2025/01/run_id.json`)
- `partition_year` (optional): Year for time-partitioned directory
- `partition_month` (optional): Month (1-12) for time-partitioned directory
- `file_name` (optional): Final stored filename
- `stored_at` (optional): ISO-8601 timestamp when file was stored

**Rationale**: Supports time-partitioned storage structure (`submissions/YYYY/MM/`) and enables efficient file organization and retrieval.

**Migration**: v2.0 files don't have this section. It's added automatically by storage script when files are stored in time-partitioned directories.

---

### 5. New `validation_metadata` Object (Optional)

**v2.0**: Not present

**v3.0**: New optional top-level object in `result_data`

```json
"validation_metadata": {
  "validated_at": "...",                    // optional
  "validator_version": "...",               // optional
  "schema_version_validated": "...",        // optional
  "validation_passed": true,                // optional
  "validation_errors_detail": [...]        // optional array
}
```

**Fields:**
- `validated_at` (optional): ISO-8601 timestamp when validation was performed
- `validator_version` (optional): Version of validation script used
- `schema_version_validated` (optional): Schema version validated against
- `validation_passed` (optional): Boolean indicating validation success
- `validation_errors_detail` (optional): Array of detailed error objects with `field_path`, `error_message`, `error_code`

**Rationale**: Provides detailed validation audit trail for debugging submission issues, tracking validation improvements, and providing verbose error feedback in GitHub Issue comments.

**Migration**: v2.0 files don't have this section. It's added automatically by validation script during processing.

---

### 6. New `aggregation_metadata` Object (Optional)

**v2.0**: Not present

**v3.0**: New optional top-level object in `result_data`

```json
"aggregation_metadata": {
  "last_aggregated_at": "...",        // optional
  "included_in_leaderboard": true,   // optional
  "aggregation_version": "...",       // optional
  "csv_exported": true,               // optional
  "csv_export_timestamp": "..."       // optional
}
```

**Fields:**
- `last_aggregated_at` (optional): ISO-8601 timestamp of last successful aggregation
- `included_in_leaderboard` (optional): Boolean indicating leaderboard inclusion
- `aggregation_version` (optional): Version of aggregation script used
- `csv_exported` (optional): Boolean indicating CSV export inclusion
- `csv_export_timestamp` (optional): ISO-8601 timestamp of CSV export

**Rationale**: Enables tracking of which results are included in leaderboards, when aggregation occurred, and CSV export status for data processing workflows.

**Migration**: v2.0 files don't have this section. It's added automatically by aggregation script when processing results.

---

## Migration Path

### v2.0 → v3.0 Upgrade

**Automatic Migration (Recommended):**
1. Update `schema_version` from `"2.0"` to `"3.0"`
2. All existing fields remain unchanged
3. New optional sections are added by automated pipeline:
   - `processing`: Added during ingestion
   - `storage_metadata`: Added during storage
   - `validation_metadata`: Added during validation
   - `aggregation_metadata`: Added during aggregation
   - `submission.github_issue`: Added if submitted via GitHub Issue

**Manual Migration (If Needed):**
- Simply update `schema_version` field
- All other fields can remain as-is
- New sections are optional and can be added later

### v3.0 → v2.0 Compatibility

**For Tools Supporting Both Versions:**
- Check `schema_version` field to determine version
- v2.0 files: Process normally, ignore v3.0-only sections (none exist in v2.0)
- v3.0 files: Process all sections, but v3.0-only sections are optional

**For Tools Only Supporting v2.0:**
- v3.0 files can be processed by ignoring new optional sections
- Core data (`run_identity`, `implementations`, `submission` core fields) is identical
- New sections don't affect core functionality

---

## Breaking Changes

### Schema Validation
- **Breaking**: Schema validators must recognize `"3.0"` as valid `schema_version`
- **Impact**: Validation scripts need update to accept v3.0 enum value

### No Data Structure Breaking Changes
- ✅ All v2.0 data structures preserved
- ✅ All v2.0 field types and validation rules unchanged
- ✅ All v2.0 required/optional field status unchanged
- ✅ New fields are all optional

---

## Non-Breaking Enhancements

### New Capabilities Enabled
1. **GitHub Issue Tracking**: Link submissions to GitHub Issues
2. **Processing Pipeline Tracking**: Monitor ingestion and processing status
3. **Time-Partitioned Storage**: Organize files by submission date
4. **Enhanced Validation**: Detailed error tracking and audit trail
5. **Aggregation Management**: Track leaderboard inclusion and CSV export status

### Backward Compatibility
- ✅ v2.0 files can be processed by v3.0 tools (new sections simply absent)
- ✅ v3.0 files can be processed by v2.0 tools (new sections ignored)
- ✅ Core functionality identical between versions

---

## Field Count Summary

| Section | v2.0 Fields | v3.0 Fields | Change |
|---------|------------|-------------|--------|
| Top-level | 2 | 2 | 0 |
| `run_identity` | 9 | 9 | 0 |
| `implementations.api` | ~30 | ~30 | 0 |
| `implementations.ui` | ~15 | ~15 | 0 |
| `submission` (core) | 4 | 4 | 0 |
| `submission.github_issue` | 0 | 4 | +4 |
| `processing` | 0 | 5 | +5 |
| `storage_metadata` | 0 | 5 | +5 |
| `validation_metadata` | 0 | 5 | +5 |
| `aggregation_metadata` | 0 | 5 | +5 |
| **Total** | **~60** | **~83** | **+23 (all optional)** |

---

## Validation Impact

### v2.0 Validators
- Can validate v3.0 files by:
  1. Checking `schema_version` is `"3.0"`
  2. Validating all v2.0 sections (unchanged)
  3. Optionally validating new v3.0 sections (all optional)

### v3.0 Validators
- Must validate:
  1. All v2.0 sections (preserved requirements)
  2. New v3.0 sections (all optional, but validate structure if present)
  3. Schema version enum includes `"3.0"`

---

## Conclusion

Schema v3.0 is a **non-breaking extension** of v2.0 that:
- ✅ Preserves all existing functionality
- ✅ Maintains backward compatibility
- ✅ Adds optional enhancements for automated workflows
- ✅ Enables new capabilities without disrupting existing tools

The migration path is straightforward: update `schema_version` and optionally add new sections as needed. All new fields are optional, ensuring existing tools continue to work without modification.

