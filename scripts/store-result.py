#!/usr/bin/env python3
"""
store-result.py — Store validated result JSON in time-partitioned directory structure

This script stores validated result JSON files in a time-partitioned directory structure,
handling duplicate run_ids by removing older files.

Usage:
    # From Task 3.2 output (STDIN)
    python3 scripts/validate-result-v3.py | python3 scripts/store-result.py
    
    # From file containing Task 3.2 output
    python3 scripts/store-result.py --file validation_output.json
    
    # With custom submissions directory
    python3 scripts/store-result.py --submissions-dir custom/path
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_timestamp(timestamp_str: str) -> Tuple[int, int]:
    """
    Parse ISO-8601 timestamp and extract year and month.
    
    Args:
        timestamp_str: ISO-8601 timestamp string (e.g., "2025-01-15T10:30:00.000Z")
    
    Returns:
        Tuple of (year, month)
    
    Raises:
        ValueError: If timestamp cannot be parsed
    """
    try:
        # Handle both formats: with and without milliseconds
        # ISO-8601 format: YYYY-MM-DDTHH:MM:SS[.SSS]Z
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(timestamp_str)
        return dt.year, dt.month
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}. Expected ISO-8601 format (YYYY-MM-DDTHH:MM:SS[.SSS]Z): {e}")


def find_duplicate_files(submissions_dir: Path, run_id: str) -> List[Path]:
    """
    Find all files with the same run_id in the submissions directory structure.
    
    Args:
        submissions_dir: Root submissions directory
        run_id: Run ID to search for
    
    Returns:
        List of file paths with matching run_id
    """
    duplicate_files = []
    target_filename = f"{run_id}.json"
    
    if not submissions_dir.exists():
        return duplicate_files
    
    # Search recursively through all submissions/YYYY/MM/ directories
    for year_dir in submissions_dir.iterdir():
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
            file_path = month_dir / target_filename
            if file_path.exists():
                duplicate_files.append(file_path)
    
    return duplicate_files


def compare_timestamps(file1_path: Path, file2_path: Path, submitted_timestamp: str) -> Path:
    """
    Compare two files and determine which is older based on submitted_timestamp.
    
    Args:
        file1_path: Path to first file
        file2_path: Path to second file
        submitted_timestamp: Timestamp of the new submission (ISO-8601)
    
    Returns:
        Path to the older file (to be removed)
    """
    # Read submitted_timestamp from file1 if it exists
    try:
        with open(file1_path, 'r', encoding='utf-8') as f:
            file1_data = json.load(f)
        file1_timestamp = file1_data.get('result_data', {}).get('submission', {}).get('submitted_timestamp')
    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        # If we can't read file1, assume it's older
        return file1_path
    
    # Compare timestamps
    try:
        if file1_timestamp:
            dt1 = datetime.fromisoformat(file1_timestamp.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(submitted_timestamp.replace('Z', '+00:00'))
            if dt1 < dt2:
                return file1_path
            else:
                return file2_path
        else:
            # If file1 has no timestamp, assume it's older
            return file1_path
    except (ValueError, AttributeError):
        # If timestamp comparison fails, assume file1 is older
        return file1_path


def remove_duplicate_files(duplicate_files: List[Path], new_timestamp: str, run_id: str) -> Tuple[Optional[Path], bool]:
    """
    Remove older duplicate files, keeping the latest.
    
    Args:
        duplicate_files: List of file paths with same run_id
        new_timestamp: Timestamp of the new submission
        run_id: Run ID
    
    Returns:
        Tuple of (removed_file_path, should_store_new)
        - removed_file_path: Path to removed file (if any), or None
        - should_store_new: True if new file should be stored, False if existing is newer
    """
    if not duplicate_files:
        return None, True
    
    # Compare new timestamp with all existing files
    # If new is newer than all existing, remove all and store new
    # If any existing is newer, don't store new
    
    new_dt = None
    try:
        new_dt = datetime.fromisoformat(new_timestamp.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # If we can't parse new timestamp, assume it's valid and remove all duplicates
        removed_files = []
        for dup_file in duplicate_files:
            try:
                dup_file.unlink()
                removed_files.append(dup_file)
            except OSError as e:
                print(f"Warning: Failed to remove duplicate file {dup_file}: {e}", file=sys.stderr)
        return removed_files[0] if removed_files else None, True
    
    # Check if any existing file is newer than the new submission
    newest_existing = None
    newest_existing_dt = None
    
    for dup_file in duplicate_files:
        try:
            with open(dup_file, 'r', encoding='utf-8') as f:
                dup_data = json.load(f)
            dup_timestamp = dup_data.get('result_data', {}).get('submission', {}).get('submitted_timestamp')
            
            if dup_timestamp:
                dup_dt = datetime.fromisoformat(dup_timestamp.replace('Z', '+00:00'))
                if newest_existing_dt is None or dup_dt > newest_existing_dt:
                    newest_existing = dup_file
                    newest_existing_dt = dup_dt
        except (json.JSONDecodeError, KeyError, FileNotFoundError, ValueError):
            # If we can't read/parse, assume it's older
            continue
    
    # If newest existing is newer than new submission, don't store new
    if newest_existing_dt and newest_existing_dt > new_dt:
        return None, False
    
    # New submission is newer (or equal), remove all duplicates
    removed_files = []
    for dup_file in duplicate_files:
        try:
            dup_file.unlink()
            removed_files.append(dup_file)
        except OSError as e:
            print(f"Warning: Failed to remove duplicate file {dup_file}: {e}", file=sys.stderr)
    
    return removed_files[0] if removed_files else None, True


def store_result(validated_data: Dict, submissions_dir: Path) -> Dict:
    """
    Store validated result JSON in time-partitioned directory structure.
    
    Args:
        validated_data: Validated JSON data from Task 3.2 output
        submissions_dir: Root submissions directory
    
    Returns:
        Dictionary with storage results
    """
    # Extract run_id and submitted_timestamp
    try:
        run_id = validated_data['result_data']['run_identity']['run_id']
        submitted_timestamp = validated_data['result_data']['submission']['submitted_timestamp']
    except KeyError as e:
        return {
            'success': False,
            'error': f"Missing required field in validated data: {e}",
            'file_path': None
        }
    
    # Parse timestamp to get year and month
    try:
        year, month = parse_timestamp(submitted_timestamp)
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'file_path': None
        }
    
    # Construct directory path: submissions/YYYY/MM/
    partition_dir = submissions_dir / str(year) / f"{month:02d}"
    
    # Check for duplicate files
    duplicate_files = find_duplicate_files(submissions_dir, run_id)
    removed_file = None
    should_store = True
    
    if duplicate_files:
        # Remove older duplicate files
        removed_file, should_store = remove_duplicate_files(duplicate_files, submitted_timestamp, run_id)
        if not should_store:
            # New submission is not newer than existing, skip storage
            return {
                'success': False,
                'error': f"Submission timestamp is not newer than existing file(s) with run_id {run_id}",
                'file_path': None,
                'duplicate_removed': False
            }
    
    # Create directory structure if it doesn't exist
    try:
        partition_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {
            'success': False,
            'error': f"Failed to create directory {partition_dir}: {e}",
            'file_path': None
        }
    
    # Write validated JSON to file
    file_path = partition_dir / f"{run_id}.json"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(validated_data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        return {
            'success': False,
            'error': f"Failed to write file {file_path}: {e}",
            'file_path': None
        }
    
    # Prepare output
    output = {
        'success': True,
        'file_path': str(file_path.relative_to(submissions_dir.parent)) if submissions_dir.parent.exists() else str(file_path),
        'absolute_path': str(file_path),
        'run_id': run_id,
        'partition_year': year,
        'partition_month': month,
        'duplicate_removed': removed_file is not None
    }
    
    if removed_file:
        output['removed_file'] = str(removed_file)
    
    return output


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Store validated result JSON in time-partitioned directory structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Path to JSON file containing Task 3.2 validation output'
    )
    parser.add_argument(
        '--submissions-dir', '-d',
        type=str,
        default=None,
        help='Root submissions directory (default: submissions/ relative to script)'
    )
    
    args = parser.parse_args()
    
    # Determine submissions directory
    if args.submissions_dir:
        submissions_dir = Path(args.submissions_dir)
    else:
        # Default to submissions/ relative to script location
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent
        submissions_dir = repo_root / 'submissions'
    
    # Ensure submissions directory exists (will be created if needed)
    submissions_dir = submissions_dir.resolve()
    
    # Read input data
    if args.file:
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
    
    # Check validation success
    if not input_data.get('success', False):
        print("Error: Validation did not succeed. Cannot store invalid data.", file=sys.stderr)
        print(f"Validation errors: {input_data.get('error_count', 0)} error(s)", file=sys.stderr)
        sys.exit(1)
    
    # Extract validated_data
    validated_data = input_data.get('validated_data')
    if validated_data is None:
        print("Error: No validated_data in input. Cannot store.", file=sys.stderr)
        sys.exit(1)
    
    # Store result
    storage_result = store_result(validated_data, submissions_dir)
    
    # Output structured JSON to STDOUT
    json.dump(storage_result, sys.stdout, indent=2)
    sys.stdout.write('\n')
    
    # Exit with appropriate code
    if storage_result['success']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

