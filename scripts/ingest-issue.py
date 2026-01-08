#!/usr/bin/env python3
"""
ingest-issue.py — Extract and validate JSON from GitHub Issue body

This script processes GitHub issue event data to extract JSON submission data
from the issue body. It handles JSON in markdown code blocks or direct content,
validates JSON syntax, constructs/validates filenames, and saves results to
the results/submitted/ directory.

Usage:
    # From GitHub Actions (github.event passed as JSON file)
    python3 scripts/ingest-issue.py < github_event.json
    
    # From command line with file
    python3 scripts/ingest-issue.py --file github_event.json
    
    # From STDIN
    echo '{"issue": {...}}' | python3 scripts/ingest-issue.py
    
    # From environment variable (GitHub Actions context)
    python3 scripts/ingest-issue.py --env GITHUB_EVENT_PATH
    
    # Specify custom output directory (default: results/submitted)
    python3 scripts/ingest-issue.py --output-dir /path/to/output
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, List


def read_github_event(source: Optional[str] = None, env_var: Optional[str] = None) -> Dict:
    """
    Read GitHub issue event data from various sources.
    
    Args:
        source: File path to read from (or None for STDIN)
        env_var: Environment variable name containing file path (e.g., GITHUB_EVENT_PATH)
    
    Returns:
        Dictionary containing GitHub event data
    """
    if env_var and env_var in os.environ:
        file_path = os.environ[env_var]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    if source:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {source}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {source}: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Read from STDIN
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON from STDIN: {e}", file=sys.stderr)
        sys.exit(1)


def extract_json_from_body(body: str) -> Tuple[Optional[str], str]:
    """
    Extract JSON content from issue body.
    
    Handles multiple formats:
    1. JSON in markdown code blocks: ```json ... ```
    2. Direct JSON content (not in code blocks)
    3. JSON that might be embedded in markdown text
    
    Args:
        body: Issue body text
    
    Returns:
        Tuple of (extracted_json_string, extraction_method)
        extraction_method: "code_block", "direct", or "none"
    """
    if not body:
        return None, "none"
    
    # Method 1: Extract from markdown code blocks with json language tag
    # Pattern matches: ```json ... ``` or ```JSON ... ```
    code_block_pattern = r'```(?:json|JSON)\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, body, re.DOTALL)
    
    if matches:
        # Use the first valid JSON block found
        for match in matches:
            json_candidate = match.strip()
            if json_candidate:
                return json_candidate, "code_block"
    
    # Method 2: Try to find direct JSON content (not in code blocks)
    # Look for content that starts with { and ends with }
    # This handles cases where JSON is pasted directly without code block markers
    # Strategy: Find all positions with '{', try to parse JSON from each position
    # and keep the longest valid JSON found
    longest_json = None
    longest_length = 0
    
    # Find all occurrences of '{'
    for start_pos in range(len(body)):
        if body[start_pos] == '{':
            # Try progressively longer substrings from this position
            for end_pos in range(start_pos + 1, len(body) + 1):
                if body[end_pos - 1] == '}':
                    json_candidate = body[start_pos:end_pos].strip()
                    try:
                        # Try to parse this substring as JSON
                        parsed = json.loads(json_candidate)
                        # If successful and longer than previous finds, keep it
                        if len(json_candidate) > longest_length:
                            longest_json = json_candidate
                            longest_length = len(json_candidate)
                    except json.JSONDecodeError:
                        # Not valid JSON, continue trying
                        continue
    
    if longest_json:
        return longest_json, "direct"
    
    # Method 3: Try to extract JSON from textarea field format
    # GitHub renders textarea fields in the body, but the content might be
    # embedded in markdown. Look for the largest JSON-like structure.
    # This is a fallback for edge cases.
    lines = body.split('\n')
    json_lines = []
    in_json = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('{'):
            in_json = True
            json_lines = [stripped]
        elif in_json:
            json_lines.append(line)
            if stripped.endswith('}') and stripped.count('{') <= stripped.count('}'):
                # Potential JSON block complete
                json_candidate = '\n'.join(json_lines).strip()
                try:
                    json.loads(json_candidate)
                    return json_candidate, "direct"
                except json.JSONDecodeError:
                    json_lines = []
                    in_json = False
    
    return None, "none"


def validate_json(json_string: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate JSON syntax and parse it.
    
    Args:
        json_string: JSON string to validate
    
    Returns:
        Tuple of (is_valid, parsed_json, error_message)
    """
    if not json_string or not json_string.strip():
        return False, None, "Extracted content is empty"
    
    try:
        parsed = json.loads(json_string)
        return True, parsed, None
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON syntax: {e.msg} at line {e.lineno}, column {e.colno}"
        return False, None, error_msg


def extract_issue_metadata(event_data: Dict) -> Dict:
    """
    Extract relevant metadata from GitHub issue event.
    
    Args:
        event_data: GitHub event data dictionary
    
    Returns:
        Dictionary containing issue metadata
    """
    issue = event_data.get('issue', {})
    
    return {
        'issue_number': issue.get('number'),
        'issue_url': issue.get('html_url'),
        'issue_title': issue.get('title'),
        'submitter': issue.get('user', {}).get('login') if issue.get('user') else None,
        'created_at': issue.get('created_at'),
        'body': issue.get('body', '')
    }


def validate_required_fields(result_json: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that required fields exist in the result JSON.
    
    Args:
        result_json: Parsed result JSON dictionary
    
    Returns:
        Tuple of (all_valid, missing_fields_list)
    """
    missing_fields = []
    
    # Check for result_data
    if 'result_data' not in result_json:
        missing_fields.append('result_data')
        return False, missing_fields
    
    result_data = result_json['result_data']
    
    # Check for run_identity
    if 'run_identity' not in result_data:
        missing_fields.append('result_data.run_identity')
        return False, missing_fields
    
    run_identity = result_data['run_identity']
    
    # Check required fields for filename construction
    required_fields = {
        'tool_name': 'result_data.run_identity.tool_name',
        'target_model': 'result_data.run_identity.target_model',
        'api_style': 'result_data.run_identity.api_style',
        'run_number': 'result_data.run_identity.run_number'
    }
    
    for field, full_path in required_fields.items():
        if field not in run_identity or run_identity[field] is None:
            missing_fields.append(full_path)
    
    if missing_fields:
        return False, missing_fields
    
    return True, []


def extract_timestamp_from_json(result_json: Dict) -> Optional[str]:
    """
    Extract timestamp from result JSON for filename.
    
    Tries multiple sources:
    1. run_id field (e.g., "cursor-ModelA-20251226T1121")
    2. submitted_timestamp (convert to filename format)
    3. start_timestamp from generation_metrics
    
    Args:
        result_json: Parsed result JSON dictionary
    
    Returns:
        Timestamp string in format YYYYMMDDTHHMM or None
    """
    try:
        result_data = result_json.get('result_data', {})
        run_identity = result_data.get('run_identity', {})
        
        # Try extracting from run_id (format: tool-Model-20251226T1121)
        run_id = run_identity.get('run_id', '')
        if run_id:
            # Extract timestamp pattern YYYYMMDDTHHMM
            timestamp_match = re.search(r'(\d{8}T\d{4})', run_id)
            if timestamp_match:
                return timestamp_match.group(1)
        
        # Try submitted_timestamp (ISO format)
        submission = result_data.get('submission', {})
        submitted_timestamp = submission.get('submitted_timestamp', '')
        if submitted_timestamp:
            # Convert from ISO format to YYYYMMDDTHHMM
            # Example: "2025-12-26T18:13:57.000Z" -> "20251226T1813"
            timestamp_match = re.match(r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})', submitted_timestamp)
            if timestamp_match:
                year, month, day, hour, minute = timestamp_match.groups()
                return f"{year}{month}{day}T{hour}{minute}"
        
        # Try start_timestamp from API generation_metrics
        api_impl = result_data.get('implementations', {}).get('api', {})
        start_timestamp = api_impl.get('generation_metrics', {}).get('start_timestamp', '')
        if start_timestamp:
            timestamp_match = re.search(r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})', start_timestamp)
            if timestamp_match:
                year, month, day, hour, minute = timestamp_match.groups()
                return f"{year}{month}{day}T{hour}{minute}"
    
    except (KeyError, AttributeError):
        pass
    
    return None


def construct_filename(result_json: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Construct filename from result JSON fields.
    
    Format: {tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json
    Example: cursor_modelA_REST_run1_20251226T1121.json
    
    Args:
        result_json: Parsed result JSON dictionary
    
    Returns:
        Tuple of (filename, error_message)
        If successful, returns (filename_string, None)
        If failed, returns (None, error_description)
    """
    try:
        result_data = result_json.get('result_data', {})
        run_identity = result_data.get('run_identity', {})
        
        # Extract components
        tool_name = run_identity.get('tool_name', '').lower().strip()
        target_model = run_identity.get('target_model', '').strip()
        api_style = run_identity.get('api_style', '').strip()
        run_number = run_identity.get('run_number')
        
        # Validate components
        if not tool_name:
            return None, "tool_name is empty or missing"
        if not target_model:
            return None, "target_model is empty or missing"
        if not api_style:
            return None, "api_style is empty or missing"
        if run_number is None:
            return None, "run_number is missing"
        
        # Format model (A -> modelA, B -> modelB)
        if len(target_model) == 1 and target_model.upper() in ['A', 'B']:
            model_str = f"model{target_model.upper()}"
        else:
            model_str = target_model
        
        # Format run number (1 -> run1)
        run_str = f"run{run_number}"
        
        # Extract timestamp
        timestamp = extract_timestamp_from_json(result_json)
        if not timestamp:
            return None, "Could not extract timestamp from JSON (checked run_id, submitted_timestamp, start_timestamp)"
        
        # Validate timestamp format (YYYYMMDDTHHMM)
        if not re.match(r'^\d{8}T\d{4}$', timestamp):
            return None, f"Timestamp has invalid format: {timestamp} (expected YYYYMMDDTHHMM)"
        
        # Construct filename
        filename = f"{tool_name}_{model_str}_{api_style}_{run_str}_{timestamp}.json"
        
        return filename, None
    
    except (KeyError, AttributeError, TypeError) as e:
        return None, f"Error constructing filename: {str(e)}"


def validate_filename_format(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that filename matches the expected naming convention.
    
    Expected format: {tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json
    Example: cursor_modelA_REST_run1_20251226T1121.json
    
    Args:
        filename: Filename to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Pattern: {word}_{model[A-Z]}_{word}_{run\d+}_{YYYYMMDDTHHMM}.json
    pattern = r'^[a-z0-9_-]+_model[A-Z]_[a-zA-Z]+_run\d+_\d{8}T\d{4}\.json$'
    
    if not re.match(pattern, filename):
        return False, (
            f"Filename '{filename}' does not match expected format: "
            "{{tool-slug}}_{{model}}_{{api-type}}_{{run-number}}_{{timestamp}}.json\n"
            "Example: cursor_modelA_REST_run1_20251226T1121.json"
        )
    
    return True, None


def save_result_file(result_json: Dict, filename: str, output_dir: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Save result JSON to file in the specified output directory.
    
    Args:
        result_json: Parsed result JSON dictionary
        filename: Validated filename
        output_dir: Output directory path
    
    Returns:
        Tuple of (success, file_path, error_message)
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Construct full file path
        file_path = output_path / filename
        
        # Check if file already exists
        if file_path.exists():
            return False, None, f"File already exists: {file_path}"
        
        # Write JSON with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        
        return True, str(file_path), None
    
    except PermissionError:
        return False, None, f"Permission denied: Cannot write to {output_dir}"
    except OSError as e:
        return False, None, f"File system error: {str(e)}"
    except Exception as e:
        return False, None, f"Unexpected error saving file: {str(e)}"


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Extract and validate JSON from GitHub Issue body, validate filename, and save to results directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Path to JSON file containing GitHub event data'
    )
    parser.add_argument(
        '--env', '-e',
        type=str,
        help='Environment variable name containing path to GitHub event file (e.g., GITHUB_EVENT_PATH)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='results/submitted',
        help='Output directory for saved result files (default: results/submitted)'
    )
    
    args = parser.parse_args()
    
    # Read GitHub event data
    try:
        event_data = read_github_event(source=args.file, env_var=args.env)
    except Exception as e:
        print(f"Error reading GitHub event data: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract issue metadata
    issue_metadata = extract_issue_metadata(event_data)
    issue_body = issue_metadata.get('body', '')
    
    # Extract JSON from issue body
    extracted_json, extraction_method = extract_json_from_body(issue_body)
    
    # Prepare output structure
    output = {
        'success': False,
        'issue_metadata': {
            'issue_number': issue_metadata.get('issue_number'),
            'issue_url': issue_metadata.get('issue_url'),
            'issue_title': issue_metadata.get('issue_title'),
            'submitter': issue_metadata.get('submitter'),
            'created_at': issue_metadata.get('created_at')
        },
        'extraction': {
            'method': extraction_method,
            'success': False
        },
        'validation': {
            'json_valid': False,
            'json_error': None,
            'required_fields_valid': False,
            'missing_fields': []
        },
        'filename': {
            'constructed': None,
            'valid': False,
            'error': None
        },
        'file_save': {
            'success': False,
            'file_path': None,
            'error': None
        },
        'result_data': None,
        'error': None
    }
    
    # Validate and parse JSON if extraction succeeded
    if not extracted_json:
        output['error'] = f"Failed to extract JSON from issue body. Extraction method attempted: {extraction_method}"
        output['extraction']['success'] = False
    else:
        is_valid, parsed_json, error_msg = validate_json(extracted_json)
        
        output['extraction']['success'] = True
        
        if not is_valid:
            output['validation']['json_valid'] = False
            output['validation']['json_error'] = error_msg
            output['error'] = f"JSON validation failed: {error_msg}"
        else:
            output['validation']['json_valid'] = True
            output['result_data'] = parsed_json
            
            # Validate required fields
            fields_valid, missing_fields = validate_required_fields(parsed_json)
            output['validation']['required_fields_valid'] = fields_valid
            output['validation']['missing_fields'] = missing_fields
            
            if not fields_valid:
                output['error'] = f"Missing required fields: {', '.join(missing_fields)}"
            else:
                # Construct filename
                filename, filename_error = construct_filename(parsed_json)
                
                if filename_error:
                    output['filename']['error'] = filename_error
                    output['error'] = f"Filename construction failed: {filename_error}"
                else:
                    output['filename']['constructed'] = filename
                    
                    # Validate filename format
                    format_valid, format_error = validate_filename_format(filename)
                    output['filename']['valid'] = format_valid
                    
                    if not format_valid:
                        output['filename']['error'] = format_error
                        output['error'] = f"Filename validation failed: {format_error}"
                    else:
                        # Save file
                        save_success, file_path, save_error = save_result_file(
                            parsed_json, filename, args.output_dir
                        )
                        
                        output['file_save']['success'] = save_success
                        output['file_save']['file_path'] = file_path
                        output['file_save']['error'] = save_error
                        
                        if save_success:
                            output['success'] = True
                        else:
                            output['error'] = f"File save failed: {save_error}"
    
    # Output structured data as JSON to STDOUT
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write('\n')
    
    # Exit with appropriate code
    if output['success']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

