# Schema v3.0 Field Reference

Complete field-by-field documentation for schema v3.0, including descriptions, types, required/optional status, and example values.

## Top-Level Fields

### `schema_version`
- **Type**: String
- **Required**: Yes
- **Enum Values**: `["3.0"]`
- **Description**: Version identifier for this schema specification
- **Example**: `"3.0"`

### `result_data`
- **Type**: Object
- **Required**: Yes
- **Description**: Main container for all result data
- **Properties**: See sections below

---

## `result_data.run_identity` (Required)

Complete run and tool identification information. All fields are required.

### `tool_name`
- **Type**: String
- **Required**: Yes
- **Description**: Name of the AI tool used (e.g., "Cursor", "GitHub Copilot")
- **Example**: `"Cursor"`

### `tool_version`
- **Type**: String
- **Required**: Yes
- **Description**: Version of the AI tool
- **Example**: `"v0.43"`

### `run_id`
- **Type**: String
- **Required**: Yes
- **Description**: Unique identifier for this run
- **Example**: `"cursor_modelA_REST_run1_20250101T1000"`

### `run_number`
- **Type**: Integer
- **Required**: Yes
- **Enum Values**: `[1, 2]`
- **Description**: Run number (1 or 2)
- **Example**: `1`

### `target_model`
- **Type**: String
- **Required**: Yes
- **Enum Values**: `["A", "B"]`
- **Description**: Target model identifier
- **Example**: `"A"`

### `api_style`
- **Type**: String
- **Required**: Yes
- **Enum Values**: `["REST", "GraphQL"]`
- **Description**: API style used for this run
- **Example**: `"REST"`

### `spec_reference`
- **Type**: String
- **Required**: Yes
- **Description**: Reference to specification version or identifier
- **Example**: `"SPEC_VERSION"`

### `workspace_path`
- **Type**: String
- **Required**: Yes
- **Description**: Path to the workspace where the run was executed
- **Example**: `"/path/to/workspace"`

### `run_environment`
- **Type**: String
- **Required**: Yes
- **Description**: Description of the runtime environment
- **Example**: `"macOS 14.6.0, Node.js 20.10.0"`

---

## `result_data.implementations` (Required)

Container for API and/or UI implementation data. At least one of `api` or `ui` must be present.

### `api` (Optional Object)

Backend/API implementation data.

#### `api.generation_metrics` (Required)

#### `api.generation_metrics.llm_model`
- **Type**: String
- **Required**: Yes
- **Description**: LLM model used for API implementation
- **Example**: `"claude-sonnet-4.5"`

#### `api.generation_metrics.start_timestamp`
- **Type**: String (ISO-8601 UTC)
- **Required**: Yes
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When API generation started
- **Example**: `"2025-01-01T10:00:00.000Z"`

#### `api.generation_metrics.end_timestamp`
- **Type**: String (ISO-8601 UTC)
- **Required**: Yes
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When API generation completed
- **Example**: `"2025-01-01T10:15:00.000Z"`

#### `api.generation_metrics.duration_minutes`
- **Type**: Number
- **Required**: Yes
- **Minimum**: 0
- **Description**: Duration of API generation in minutes
- **Example**: `15.5`

#### `api.generation_metrics.clarifications_count`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of clarification questions asked
- **Example**: `0`

#### `api.generation_metrics.interventions_count`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of manual interventions required
- **Example**: `0`

#### `api.generation_metrics.reruns_count`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of times the run was restarted
- **Example**: `1`

#### `api.generation_metrics.test_runs` (Optional Array)
- **Type**: Array of objects
- **Required**: No
- **Description**: Array of test run iterations
- **Items**: See test run object structure below

#### `api.generation_metrics.test_iterations_count` (Optional)
- **Type**: Integer
- **Required**: No
- **Minimum**: 1
- **Description**: Number of test iterations before all passed
- **Example**: `3`

#### `api.generation_metrics.llm_usage` (Optional Object)
- **Type**: Object
- **Required**: No
- **Description**: LLM usage metrics (tokens, requests, cost)
- **Properties**:
  - `input_tokens` (integer, minimum: 0)
  - `output_tokens` (integer, minimum: 0)
  - `total_tokens` (integer, minimum: 0)
  - `requests_count` (integer, minimum: 0)
  - `estimated_cost_usd` (number, minimum: 0)
  - `cost_currency` (string, default: "USD")
  - `usage_source` (string, enum: ["tool_reported", "operator_estimated", "unknown"])

#### `api.acceptance` (Required)

#### `api.acceptance.pass_count`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of acceptance tests passed
- **Example**: `45`

#### `api.acceptance.fail_count`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of acceptance tests failed
- **Example**: `2`

#### `api.acceptance.not_run_count`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of acceptance tests not run
- **Example**: `0`

#### `api.acceptance.passrate`
- **Type**: Number
- **Required**: Yes
- **Minimum**: 0
- **Maximum**: 1
- **Description**: Pass rate (0.0 to 1.0)
- **Example**: `0.957`

#### `api.quality_metrics` (Optional Object)
- **Type**: Object
- **Required**: No
- **Properties**:
  - `determinism_compliance` (string, enum: ["Pass", "Fail", "Unknown"])
  - `overreach_incidents_count` (integer, minimum: 0)
  - `contract_completeness_passrate` (number, 0-1)
  - `instructions_quality_rating` (integer, enum: [100, 70, 40, 0])
  - `reproducibility_rating` (string, enum: ["None", "Minor", "Major", "Unknown"])

#### `api.artifacts` (Required)

#### `api.artifacts.contract_artifact_path`
- **Type**: String
- **Required**: Yes
- **Description**: Path to contract artifact file
- **Example**: `"docs/API_Contract.md"`

#### `api.artifacts.run_instructions_path`
- **Type**: String
- **Required**: Yes
- **Description**: Path to run instructions file
- **Example**: `"docs/Run_Instructions.md"`

#### `api.artifacts.source_code_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to source code directory
- **Example**: `"backend/"`

#### `api.artifacts.acceptance_checklist_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to acceptance checklist
- **Example**: `"benchmark/acceptance_checklist.md"`

#### `api.artifacts.acceptance_evidence_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to acceptance evidence
- **Example**: `"benchmark/acceptance_evidence.md"`

#### `api.artifacts.determinism_evidence_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to determinism evidence
- **Example**: `"benchmark/determinism_evidence.md"`

#### `api.artifacts.overreach_evidence_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to overreach evidence
- **Example**: `"benchmark/overreach_evidence.md"`

#### `api.artifacts.ai_run_report_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to AI run report
- **Example**: `"benchmark/ai_run_report.md"`

#### `api.artifacts.automated_tests_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to automated tests
- **Example**: `"backend/tests/"`

#### `api.scores` (Optional Object)
- **Type**: Object
- **Required**: No
- **Properties**:
  - `correctness_C` (number, 0-100)
  - `reproducibility_R` (number, 0-100)
  - `determinism_D` (number, 0-100)
  - `effort_E` (number, 0-100)
  - `speed_S` (number, 0-100)
  - `contract_docs_K` (number, 0-100)
  - `penalty_overreach_PO` (number, 0-40)
  - `overall_score` (number, 0-100)

### `ui` (Optional Object)

Frontend/UI implementation data.

#### `ui.generation_metrics` (Required)

All fields same as `api.generation_metrics` with one addition:

#### `ui.generation_metrics.backend_changes_required` (Optional)
- **Type**: Boolean
- **Required**: No
- **Description**: Whether UI build required backend changes
- **Example**: `false`

#### `ui.build_success` (Required)
- **Type**: Boolean
- **Required**: Yes
- **Description**: Whether UI builds and runs without errors
- **Example**: `true`

#### `ui.artifacts` (Required)

#### `ui.artifacts.ui_source_path`
- **Type**: String
- **Required**: Yes
- **Description**: Path to UI source code
- **Example**: `"ui/"`

#### `ui.artifacts.ui_run_summary_path`
- **Type**: String
- **Required**: Yes
- **Description**: Path to UI run summary
- **Example**: `"benchmark/ui_run_summary.md"`

#### `ui.artifacts.run_instructions_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Path to run instructions
- **Example**: `"docs/Run_Instructions.md"`

---

## `result_data.submission` (Required)

Submission metadata. Enhanced in v3.0 with GitHub Issue tracking.

### `submitted_timestamp`
- **Type**: String (ISO-8601 UTC)
- **Required**: Yes
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When the result was submitted
- **Example**: `"2025-01-01T10:00:00.000Z"`

### `submitted_by`
- **Type**: String
- **Required**: Yes
- **Description**: Identifier of submitter (username, email, or tool name)
- **Example**: `"username"`

### `submission_method`
- **Type**: String
- **Required**: Yes
- **Enum Values**: `["automated", "manual"]`
- **Description**: How the result was submitted
- **Example**: `"automated"`

### `notes` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Optional notes about the submission
- **Example**: `"First run with new model"`

### `submission.github_issue` (Optional Object) - **NEW in v3.0**

GitHub Issue tracking for automated submission workflow.

#### `github_issue.issue_number`
- **Type**: Integer
- **Required**: Yes (if `github_issue` is present)
- **Description**: GitHub Issue number
- **Example**: `123`

#### `github_issue.issue_url`
- **Type**: String
- **Required**: Yes (if `github_issue` is present)
- **Description**: Full URL to the GitHub Issue
- **Example**: `"https://github.com/org/pawmate-ai-results/issues/123"`

#### `github_issue.issue_created_at`
- **Type**: String (ISO-8601 UTC)
- **Required**: Yes (if `github_issue` is present)
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When the GitHub Issue was created
- **Example**: `"2025-01-01T10:00:00.000Z"`

#### `github_issue.issue_closed_at` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When the GitHub Issue was closed (if applicable)
- **Example**: `"2025-01-01T10:05:00.000Z"`

---

## `result_data.processing` (Optional Object) - **NEW in v3.0**

Automated ingestion and processing pipeline status.

### `ingested_timestamp` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When the submission was ingested from GitHub Issue
- **Example**: `"2025-01-01T10:01:00.000Z"`

### `processed_timestamp` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When processing completed successfully
- **Example**: `"2025-01-01T10:02:00.000Z"`

### `validation_status` (Optional)
- **Type**: String
- **Required**: No
- **Enum Values**: `["pending", "valid", "invalid", "error"]`
- **Description**: Status of validation
- **Example**: `"valid"`

### `validation_errors` (Optional)
- **Type**: Array of strings
- **Required**: No
- **Description**: List of validation error messages (if validation failed)
- **Example**: `["Field 'run_id' is required", "Invalid timestamp format"]`

### `storage_status` (Optional)
- **Type**: String
- **Required**: No
- **Enum Values**: `["pending", "stored", "failed", "duplicate_replaced"]`
- **Description**: Status of storage operation
- **Example**: `"stored"`

---

## `result_data.storage_metadata` (Optional Object) - **NEW in v3.0**

Time-partitioned storage and file management information.

### `storage_path` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Relative path where file is stored
- **Example**: `"submissions/2025/01/cursor_modelA_REST_run1_20250101T1000.json"`

### `partition_year` (Optional)
- **Type**: Integer
- **Required**: No
- **Description**: Year component for time-partitioned directory
- **Example**: `2025`

### `partition_month` (Optional)
- **Type**: Integer
- **Required**: No
- **Minimum**: 1
- **Maximum**: 12
- **Description**: Month component for time-partitioned directory
- **Example**: `1`

### `file_name` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Final stored filename (typically `{run_id}.json`)
- **Example**: `"cursor_modelA_REST_run1_20250101T1000.json"`

### `stored_at` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: Timestamp when file was stored
- **Example**: `"2025-01-01T10:02:00.000Z"`

---

## `result_data.validation_metadata` (Optional Object) - **NEW in v3.0**

Detailed validation tracking and audit trail.

### `validated_at` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When validation was performed
- **Example**: `"2025-01-01T10:01:30.000Z"`

### `validator_version` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Version of validation script/schema used
- **Example**: `"1.0.0"`

### `schema_version_validated` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Schema version that was validated against
- **Example**: `"3.0"`

### `validation_passed` (Optional)
- **Type**: Boolean
- **Required**: No
- **Description**: Whether validation passed
- **Example**: `true`

### `validation_errors_detail` (Optional)
- **Type**: Array of objects
- **Required**: No
- **Description**: Detailed validation errors
- **Item Properties**:
  - `field_path` (string): JSON path to the field with error
  - `error_message` (string): Human-readable error message
  - `error_code` (string, optional): Machine-readable error code
- **Example**:
  ```json
  [
    {
      "field_path": "result_data.run_identity.run_id",
      "error_message": "Field 'run_id' is required",
      "error_code": "REQUIRED_FIELD_MISSING"
    }
  ]
  ```

---

## `result_data.aggregation_metadata` (Optional Object) - **NEW in v3.0**

Leaderboard inclusion and aggregation status tracking.

### `last_aggregated_at` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: Timestamp of last successful aggregation run
- **Example**: `"2025-01-01T10:10:00.000Z"`

### `included_in_leaderboard` (Optional)
- **Type**: Boolean
- **Required**: No
- **Description**: Whether this result is included in current leaderboard
- **Example**: `true`

### `aggregation_version` (Optional)
- **Type**: String
- **Required**: No
- **Description**: Version of aggregation script that last processed this result
- **Example**: `"2.0.0"`

### `csv_exported` (Optional)
- **Type**: Boolean
- **Required**: No
- **Description**: Whether this result was included in CSV export
- **Example**: `true`

### `csv_export_timestamp` (Optional)
- **Type**: String (ISO-8601 UTC)
- **Required**: No
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When CSV export last included this result
- **Example**: `"2025-01-01T10:10:00.000Z"`

---

## Test Run Object Structure

Used in `api.generation_metrics.test_runs` array:

### `run_number`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 1
- **Description**: Test run iteration number
- **Example**: `1`

### `start_timestamp`
- **Type**: String (ISO-8601 UTC)
- **Required**: Yes
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When test run started
- **Example**: `"2025-01-01T10:15:00.000Z"`

### `end_timestamp`
- **Type**: String (ISO-8601 UTC)
- **Required**: Yes
- **Pattern**: `^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$`
- **Description**: When test run completed
- **Example**: `"2025-01-01T10:16:00.000Z"`

### `duration_minutes`
- **Type**: Number
- **Required**: Yes
- **Minimum**: 0
- **Description**: Duration of test run in minutes
- **Example**: `1.0`

### `total_tests`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Total number of tests
- **Example**: `47`

### `passed`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of tests passed
- **Example**: `45`

### `failed`
- **Type**: Integer
- **Required**: Yes
- **Minimum**: 0
- **Description**: Number of tests failed
- **Example**: `2`

### `pass_rate`
- **Type**: Number
- **Required**: Yes
- **Minimum**: 0
- **Maximum**: 1
- **Description**: Pass rate (0.0 to 1.0)
- **Example**: `0.957`

