#!/usr/bin/env bash
#
# validate_result.sh — Validate a result file against the specification
#
# Usage:
#   ./scripts/validate_result.sh <result-file> [--strict]
#
# Options:
#   --strict    Treat warnings as errors
#

set -euo pipefail

# Resolve script and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

STRICT_MODE=false

# Parse arguments
RESULT_FILE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        -h|--help)
            sed -n '2,/^$/p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        *)
            if [[ -z "$RESULT_FILE" ]]; then
                RESULT_FILE="$1"
            else
                echo "Error: Unknown option or multiple files: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$RESULT_FILE" ]]; then
    echo "Error: Result file path is required" >&2
    exit 1
fi

# Resolve absolute path
RESULT_FILE="$(cd "$(dirname "$RESULT_FILE")" && pwd)/$(basename "$RESULT_FILE")"

# Check file exists
if [[ ! -f "$RESULT_FILE" ]]; then
    echo "Error: Result file does not exist: $RESULT_FILE" >&2
    exit 1
fi

# Track validation status
VALIDATION_PASSED=true
ERRORS=()
WARNINGS=()

# Check file extension
if [[ ! "$RESULT_FILE" =~ \.json$ ]]; then
    ERRORS+=("File must have .json extension")
    VALIDATION_PASSED=false
fi

# Check naming convention
FILENAME=$(basename "$RESULT_FILE")
if [[ ! "$FILENAME" =~ ^[a-z0-9-]+_(modelA|modelB)_(REST|GraphQL)_(run1|run2)_[0-9]{8}T[0-9]{4}\.json$ ]]; then
    ERRORS+=("Filename does not match naming convention: {tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json")
    ERRORS+=("  Example: cursor-v0-43_modelA_REST_run1_20241218T1430.json")
    VALIDATION_PASSED=false
fi

# Validate JSON format
if ! python3 -m json.tool "$RESULT_FILE" > /dev/null 2>&1; then
    ERRORS+=("File is not valid JSON")
    VALIDATION_PASSED=false
else
    # Parse JSON and validate structure
    # Only support v2.0 schema
    SCHEMA_FILE="$REPO_ROOT/schemas/result-schema-v2.0-proposed.json"
    
    if [[ -f "$SCHEMA_FILE" ]] && command -v python3 &> /dev/null; then
        # Use Python to validate against JSON schema
        VALIDATION_OUTPUT=$(python3 <<EOF
import sys
import json

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("WARNING: jsonschema not installed, skipping schema validation", file=sys.stderr)
    sys.exit(0)

# Read and parse JSON
try:
    with open("$RESULT_FILE", "r") as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
    sys.exit(1)

# Read schema
with open("$SCHEMA_FILE", "r") as sf:
    schema = json.load(sf)

# Validate
try:
    validate(instance=data, schema=schema)
    print("Schema validation passed")
except ValidationError as e:
    print(f"ERROR: Schema validation failed: {e.message}", file=sys.stderr)
    print(f"  Path: {' -> '.join(str(p) for p in e.path)}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Validation error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)
        VALIDATION_EXIT=$?
        
        if [[ $VALIDATION_EXIT -ne 0 ]]; then
            ERRORS+=("$VALIDATION_OUTPUT")
            VALIDATION_PASSED=false
        fi
    else
        if [[ ! -f "$SCHEMA_FILE" ]]; then
            WARNINGS+=("Schema file not found: $SCHEMA_FILE (skipping schema validation)")
        else
            WARNINGS+=("jsonschema Python package not installed (skipping schema validation)")
        fi
        
        # Basic field checks using jq or python (fallback if schema validation unavailable)
        if command -v jq &> /dev/null; then
            REQUIRED_FIELDS=(
                "schema_version"
                "result_data.run_identity.tool_name"
                "result_data.run_identity.run_number"
                "result_data.run_identity.target_model"
                "result_data.run_identity.api_style"
            )
            
            for field in "${REQUIRED_FIELDS[@]}"; do
                if ! jq -e ".$field" "$RESULT_FILE" > /dev/null 2>&1; then
                    ERRORS+=("Required field missing: $field")
                    VALIDATION_PASSED=false
                fi
            done
            
            # Validate enum values
            TARGET_MODEL=$(jq -r '.result_data.run_identity.target_model' "$RESULT_FILE" 2>/dev/null)
            if [[ -n "$TARGET_MODEL" && "$TARGET_MODEL" != "A" && "$TARGET_MODEL" != "B" ]]; then
                ERRORS+=("target_model must be 'A' or 'B', found: $TARGET_MODEL")
                VALIDATION_PASSED=false
            fi
            
            API_STYLE=$(jq -r '.result_data.run_identity.api_style' "$RESULT_FILE" 2>/dev/null)
            if [[ -n "$API_STYLE" && "$API_STYLE" != "REST" && "$API_STYLE" != "GraphQL" ]]; then
                ERRORS+=("api_style must be 'REST' or 'GraphQL', found: $API_STYLE")
                VALIDATION_PASSED=false
            fi
            
            RUN_NUMBER=$(jq -r '.result_data.run_identity.run_number' "$RESULT_FILE" 2>/dev/null)
            if [[ -n "$RUN_NUMBER" && "$RUN_NUMBER" != "1" && "$RUN_NUMBER" != "2" ]]; then
                ERRORS+=("run_number must be 1 or 2, found: $RUN_NUMBER")
                VALIDATION_PASSED=false
            fi
        elif command -v python3 &> /dev/null; then
            # Fallback to Python for field checks
            python3 <<EOF
import json
import sys

try:
    with open("$RESULT_FILE", "r") as f:
        data = json.load(f)
    
    # Check required top-level fields
    if "schema_version" not in data:
        print("ERROR: Required field missing: schema_version", file=sys.stderr)
        sys.exit(1)
    if "result_data" not in data:
        print("ERROR: Required field missing: result_data", file=sys.stderr)
        sys.exit(1)
    
    # Check run_identity
    ri = data.get("result_data", {}).get("run_identity", {})
    if not ri.get("tool_name"):
        print("ERROR: Required field missing: result_data.run_identity.tool_name", file=sys.stderr)
        sys.exit(1)
    
    # Validate enum values
    target_model = ri.get("target_model")
    if target_model not in ["A", "B"]:
        print(f"ERROR: target_model must be 'A' or 'B', found: {target_model}", file=sys.stderr)
        sys.exit(1)
    
    api_style = ri.get("api_style")
    if api_style not in ["REST", "GraphQL"]:
        print(f"ERROR: api_style must be 'REST' or 'GraphQL', found: {api_style}", file=sys.stderr)
        sys.exit(1)
    
    run_number = ri.get("run_number")
    if run_number not in [1, 2]:
        print(f"ERROR: run_number must be 1 or 2, found: {run_number}", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Validation error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
            if [[ $? -ne 0 ]]; then
                VALIDATION_PASSED=false
            fi
        fi
    fi
fi

# Print results
echo "Validating: $RESULT_FILE"
echo ""

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo "❌ Validation FAILED"
    echo ""
    echo "Errors:"
    for error in "${ERRORS[@]}"; do
        echo "  - $error"
    done
    echo ""
    VALIDATION_PASSED=false
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "⚠️  Warnings:"
    for warning in "${WARNINGS[@]}"; do
        echo "  - $warning"
    done
    echo ""
fi

if [[ "$VALIDATION_PASSED" == "true" ]]; then
    echo "✅ Validation PASSED"
    exit 0
else
    exit 1
fi

