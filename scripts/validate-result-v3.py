#!/usr/bin/env python3
"""
validate-result-v3.py — Validate result JSON against v3.0 schema with verbose error messages

This script validates JSON result data against the v3.0 schema, collecting all validation
errors and formatting them for GitHub Issue comments and downstream processing.

Usage:
    # From Task 3.1 output (STDIN)
    python3 scripts/ingest-issue.py | python3 scripts/validate-result-v3.py
    
    # From file containing Task 3.1 output
    python3 scripts/validate-result-v3.py --file ingestion_output.json
    
    # Direct JSON validation (for testing)
    python3 scripts/validate-result-v3.py --json-file result.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from jsonschema import validate, ValidationError, Draft7Validator
    from jsonschema.exceptions import SchemaError
except ImportError:
    print("Error: jsonschema library is required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)


def load_schema(schema_path: str) -> Dict:
    """
    Load JSON Schema from file.
    
    Args:
        schema_path: Path to schema JSON file
    
    Returns:
        Schema dictionary
    
    Raises:
        SystemExit: If schema file cannot be loaded or is invalid
    """
    schema_file = Path(schema_path)
    
    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Schema file is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load schema file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate schema itself
    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as e:
        print(f"Error: Schema file is invalid: {e}", file=sys.stderr)
        sys.exit(1)
    
    return schema


def extract_result_data(input_data: Dict) -> Optional[Dict]:
    """
    Extract result JSON from Task 3.1 output format.
    
    Task 3.1 outputs structured JSON with:
    - success: boolean
    - result_data: parsed JSON object (if extraction/validation succeeded)
    - issue_metadata: issue information
    - extraction: extraction metadata
    - validation: validation metadata
    
    Args:
        input_data: JSON data from Task 3.1 output
    
    Returns:
        Result data dictionary, or None if extraction failed
    """
    # Check if this is Task 3.1 output format
    if 'result_data' in input_data and isinstance(input_data['result_data'], dict):
        # This is Task 3.1 output - extract the result_data field
        return input_data['result_data']
    
    # Check if this is direct result JSON (for testing)
    if 'schema_version' in input_data and 'result_data' in input_data:
        # This is direct result JSON - return as-is
        return input_data
    
    # If neither format, assume it's the result JSON itself
    return input_data


def collect_all_errors(validator: Draft7Validator, instance: Dict) -> List[Dict]:
    """
    Collect all validation errors from schema validation.
    
    Args:
        validator: JSON Schema validator instance
        instance: JSON data to validate
    
    Returns:
        List of error dictionaries with field paths, messages, and types
    """
    errors = []
    
    for error in validator.iter_errors(instance):
        # Extract field path
        field_path = '/'.join(str(p) for p in error.absolute_path)
        if not field_path:
            # Root-level error
            field_path = '/'
        
        # Convert JSON pointer path to human-readable format
        human_path = field_path.replace('/', '.').lstrip('.')
        if not human_path:
            human_path = 'root'
        
        # Extract error message and context
        error_message = error.message
        error_type = error.validator
        
        # Add context from error
        error_context = {}
        if error.validator_value is not None:
            error_context['validator_value'] = error.validator_value
        if error.instance is not None:
            error_context['instance_value'] = error.instance
        
        # Enhance error messages with suggestions
        enhanced_message = enhance_error_message(error, human_path)
        
        errors.append({
            'field_path': field_path,
            'human_path': human_path,
            'error_message': enhanced_message,
            'error_type': error_type,
            'error_context': error_context
        })
    
    return errors


def enhance_error_message(error: ValidationError, human_path: str) -> str:
    """
    Enhance error message with actionable suggestions.
    
    Args:
        error: ValidationError object
        human_path: Human-readable field path
    
    Returns:
        Enhanced error message with suggestions
    """
    base_message = error.message
    validator = error.validator
    
    # Add specific suggestions based on error type
    if validator == 'required':
        missing_field = error.validator_value[0] if error.validator_value else 'field'
        return f"Missing required field '{missing_field}' at {human_path}"
    
    elif validator == 'enum':
        allowed_values = error.validator_value
        current_value = error.instance
        return f"Invalid value '{current_value}' at {human_path}. Allowed values: {', '.join(str(v) for v in allowed_values)}"
    
    elif validator == 'type':
        expected_type = error.validator_value
        actual_type = type(error.instance).__name__
        return f"Type mismatch at {human_path}: expected {expected_type}, got {actual_type}"
    
    elif validator == 'pattern':
        pattern = error.validator_value
        current_value = error.instance
        if 'timestamp' in human_path.lower() or 'timestamp' in base_message.lower():
            return f"Invalid timestamp format at {human_path}: '{current_value}'. Expected ISO-8601 format: YYYY-MM-DDTHH:MM:SS.sssZ"
        return f"Value '{current_value}' at {human_path} does not match required pattern"
    
    elif validator == 'minimum':
        minimum = error.validator_value
        current_value = error.instance
        return f"Value {current_value} at {human_path} is below minimum {minimum}"
    
    elif validator == 'maximum':
        maximum = error.validator_value
        current_value = error.instance
        return f"Value {current_value} at {human_path} exceeds maximum {maximum}"
    
    elif validator == 'minLength':
        min_length = error.validator_value
        current_value = error.instance
        return f"String at {human_path} is too short (minimum {min_length} characters), got {len(current_value)}"
    
    elif validator == 'maxLength':
        max_length = error.validator_value
        current_value = error.instance
        return f"String at {human_path} is too long (maximum {max_length} characters), got {len(current_value)}"
    
    else:
        # Generic error message
        return f"{base_message} at {human_path}"


def format_errors_for_github_comment(errors: List[Dict]) -> str:
    """
    Format validation errors as markdown for GitHub Issue comments.
    
    Args:
        errors: List of error dictionaries
    
    Returns:
        Markdown-formatted error message
    """
    if not errors:
        return "✅ **Validation passed!**"
    
    lines = ["❌ **Validation failed**\n"]
    lines.append(f"Found {len(errors)} validation error(s):\n")
    
    # Group errors by top-level field for better readability
    grouped_errors = {}
    for error in errors:
        top_level = error['human_path'].split('.')[0] if '.' in error['human_path'] else 'root'
        if top_level not in grouped_errors:
            grouped_errors[top_level] = []
        grouped_errors[top_level].append(error)
    
    for top_level, group_errors in grouped_errors.items():
        lines.append(f"### {top_level}")
        for error in group_errors:
            field_path = error['human_path']
            message = error['error_message']
            lines.append(f"- **`{field_path}`**: {message}")
        lines.append("")
    
    return "\n".join(lines)


def validate_result_data(result_data: Dict, schema: Dict) -> Dict:
    """
    Validate result data against schema and collect all errors.
    
    Args:
        result_data: JSON data to validate
        schema: JSON Schema to validate against
    
    Returns:
        Dictionary with validation results
    """
    validator = Draft7Validator(schema)
    
    # Collect all errors
    errors = collect_all_errors(validator, result_data)
    
    # Format errors for GitHub comment
    github_comment = format_errors_for_github_comment(errors)
    
    # Prepare output
    output = {
        'success': len(errors) == 0,
        'errors': errors,
        'error_count': len(errors),
        'github_comment': github_comment,
        'validated_data': result_data if len(errors) == 0 else None
    }
    
    return output


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Validate result JSON against v3.0 schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Path to JSON file containing Task 3.1 output or result JSON'
    )
    parser.add_argument(
        '--json-file', '-j',
        type=str,
        help='Path to direct result JSON file (for testing)'
    )
    parser.add_argument(
        '--schema', '-s',
        type=str,
        default=None,
        help='Path to schema file (default: schemas/result-schema-v3.0.json relative to script)'
    )
    
    args = parser.parse_args()
    
    # Determine schema path
    if args.schema:
        schema_path = args.schema
    else:
        # Default to schemas/result-schema-v3.0.json relative to script location
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent
        schema_path = repo_root / 'schemas' / 'result-schema-v3.0.json'
    
    # Load schema
    try:
        schema = load_schema(str(schema_path))
    except SystemExit:
        sys.exit(1)
    
    # Read input data
    if args.json_file:
        # Direct JSON file input (for testing)
        try:
            with open(args.json_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {args.json_file}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.json_file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.file:
        # File input
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # STDIN input
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON from STDIN: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Extract result data from input
    result_data = extract_result_data(input_data)
    
    if result_data is None:
        print("Error: Could not extract result data from input. Expected Task 3.1 output format or direct result JSON.", file=sys.stderr)
        sys.exit(1)
    
    # Validate result data
    validation_result = validate_result_data(result_data, schema)
    
    # Output structured JSON to STDOUT
    json.dump(validation_result, sys.stdout, indent=2)
    sys.stdout.write('\n')
    
    # Exit with appropriate code
    if validation_result['success']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

