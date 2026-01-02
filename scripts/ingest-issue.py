#!/usr/bin/env python3
"""
ingest-issue.py — Extract and validate JSON from GitHub Issue body

This script processes GitHub issue event data to extract JSON submission data
from the issue body. It handles JSON in markdown code blocks or direct content,
validates JSON syntax, and outputs structured data for downstream processing.

Usage:
    # From GitHub Actions (github.event passed as JSON file)
    python3 scripts/ingest-issue.py < github_event.json
    
    # From command line with file
    python3 scripts/ingest-issue.py --file github_event.json
    
    # From STDIN
    echo '{"issue": {...}}' | python3 scripts/ingest-issue.py
    
    # From environment variable (GitHub Actions context)
    python3 scripts/ingest-issue.py --env GITHUB_EVENT_PATH
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, Optional, Tuple


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
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, body, re.DOTALL)
    
    if json_matches:
        # Try each match to find valid JSON
        for match in json_matches:
            json_candidate = match.strip()
            # Quick validation: check if it looks like JSON
            if json_candidate.startswith('{') and json_candidate.endswith('}'):
                try:
                    # Try parsing to ensure it's valid JSON
                    json.loads(json_candidate)
                    return json_candidate, "direct"
                except json.JSONDecodeError:
                    continue
    
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


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Extract and validate JSON from GitHub Issue body',
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
            'valid': False,
            'error': None
        },
        'result_data': None,
        'error': None
    }
    
    # Validate and parse JSON if extraction succeeded
    if extracted_json:
        is_valid, parsed_json, error_msg = validate_json(extracted_json)
        
        output['extraction']['success'] = True
        
        if is_valid:
            output['success'] = True
            output['validation']['valid'] = True
            output['result_data'] = parsed_json
        else:
            output['validation']['valid'] = False
            output['validation']['error'] = error_msg
            output['error'] = f"JSON validation failed: {error_msg}"
    else:
        output['error'] = f"Failed to extract JSON from issue body. Extraction method attempted: {extraction_method}"
        output['extraction']['success'] = False
    
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

