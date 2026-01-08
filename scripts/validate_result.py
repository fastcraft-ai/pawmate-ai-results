#!/usr/bin/env python3
"""
validate_result.py — Result File Validation Module

A comprehensive validation module for PawMate AI Challenge result files. This module can be:
- Imported by other scripts for programmatic validation
- Used standalone via CLI for batch validation

Validates result files against v3.0 schema with comprehensive validation categories:
- Required field validation
- Data type validation  
- Enum value validation
- Format validation (timestamps, patterns)
- Range validation (numeric bounds)

Usage:
    # As a module (programmatic)
    from validate_result import validate_result_file, validate_result_json
    
    result = validate_result_file('/path/to/result.json')
    if result['valid']:
        print("Validation passed!")
    else:
        for error in result['errors']:
            print(f"Error: {error['message']}")
    
    # As CLI (single file)
    python3 validate_result.py result.json
    
    # As CLI (directory)
    python3 validate_result.py results/submitted/
    
    # With JSON output
    python3 validate_result.py result.json --output json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Version of this validator
VALIDATOR_VERSION = "1.0.0"

# Try to import jsonschema for full schema validation
try:
    from jsonschema import Draft7Validator, ValidationError
    from jsonschema.exceptions import SchemaError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema library not found. Install with: pip install jsonschema", file=sys.stderr)
    print("Falling back to basic validation only.", file=sys.stderr)


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.valid = True
        self.errors = []
        self.warnings = []
        self.categories = {
            'required_fields': [],
            'data_types': [],
            'enum_values': [],
            'formats': [],
            'ranges': []
        }
    
    def add_error(self, category: str, field_path: str, message: str, error_code: Optional[str] = None):
        """Add a validation error."""
        error = {
            'category': category,
            'field_path': field_path,
            'message': message,
            'error_code': error_code or category.upper()
        }
        self.errors.append(error)
        self.categories[category].append(error)
        self.valid = False
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            'valid': self.valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'errors_by_category': self.categories,
            'validator_version': VALIDATOR_VERSION
        }


def load_schema(schema_path: Optional[str] = None) -> Optional[Dict]:
    """
    Load JSON Schema from file.
    
    Args:
        schema_path: Path to schema file. If None, uses default path.
    
    Returns:
        Schema dictionary or None if schema cannot be loaded
    """
    if not JSONSCHEMA_AVAILABLE:
        return None
    
    if schema_path is None:
        # Default to schemas/result-schema-v3.0.json relative to script
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent
        schema_path = repo_root / 'schemas' / 'result-schema-v3.0.json'
    
    schema_file = Path(schema_path)
    
    if not schema_file.exists():
        print(f"Warning: Schema file not found: {schema_path}", file=sys.stderr)
        return None
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate schema itself
        Draft7Validator.check_schema(schema)
        return schema
    
    except Exception as e:
        print(f"Warning: Failed to load schema: {e}", file=sys.stderr)
        return None


def validate_required_fields(data: Dict, result: ValidationResult):
    """
    Validate all required fields are present.
    
    Checks:
    - Top-level: schema_version, result_data
    - run_identity: All 9 required fields
    - implementations: At least one of api or ui
    - submission: submitted_timestamp, submitted_by, submission_method
    - API/UI specific required fields if present
    """
    category = 'required_fields'
    
    # Top-level required fields
    if 'schema_version' not in data:
        result.add_error(category, 'schema_version', "Missing required field 'schema_version'", 'REQUIRED_FIELD_MISSING')
    
    if 'result_data' not in data:
        result.add_error(category, 'result_data', "Missing required field 'result_data'", 'REQUIRED_FIELD_MISSING')
        return  # Can't continue without result_data
    
    result_data = data['result_data']
    
    # run_identity required fields
    if 'run_identity' not in result_data:
        result.add_error(category, 'result_data.run_identity', "Missing required section 'run_identity'", 'REQUIRED_SECTION_MISSING')
    else:
        run_identity = result_data['run_identity']
        required_run_fields = [
            'tool_name', 'tool_version', 'run_id', 'run_number',
            'target_model', 'api_style', 'spec_reference', 
            'workspace_path', 'run_environment'
        ]
        for field in required_run_fields:
            if field not in run_identity or run_identity[field] is None:
                result.add_error(category, f'result_data.run_identity.{field}', 
                               f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')
    
    # implementations required
    if 'implementations' not in result_data:
        result.add_error(category, 'result_data.implementations', 
                       "Missing required section 'implementations'", 'REQUIRED_SECTION_MISSING')
    else:
        implementations = result_data['implementations']
        if 'api' not in implementations and 'ui' not in implementations:
            result.add_error(category, 'result_data.implementations', 
                           "At least one of 'api' or 'ui' must be present", 'REQUIRED_IMPLEMENTATION_MISSING')
        
        # API required fields if api is present
        if 'api' in implementations:
            api = implementations['api']
            
            # generation_metrics
            if 'generation_metrics' not in api:
                result.add_error(category, 'result_data.implementations.api.generation_metrics',
                               "Missing required section 'generation_metrics'", 'REQUIRED_SECTION_MISSING')
            else:
                metrics = api['generation_metrics']
                required_metrics = [
                    'llm_model', 'start_timestamp', 'end_timestamp', 'duration_minutes',
                    'clarifications_count', 'interventions_count', 'reruns_count'
                ]
                for field in required_metrics:
                    if field not in metrics or metrics[field] is None:
                        result.add_error(category, f'result_data.implementations.api.generation_metrics.{field}',
                                       f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')
            
            # acceptance
            if 'acceptance' not in api:
                result.add_error(category, 'result_data.implementations.api.acceptance',
                               "Missing required section 'acceptance'", 'REQUIRED_SECTION_MISSING')
            else:
                acceptance = api['acceptance']
                required_acceptance = ['pass_count', 'fail_count', 'not_run_count', 'passrate']
                for field in required_acceptance:
                    if field not in acceptance or acceptance[field] is None:
                        result.add_error(category, f'result_data.implementations.api.acceptance.{field}',
                                       f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')
            
            # artifacts
            if 'artifacts' not in api:
                result.add_error(category, 'result_data.implementations.api.artifacts',
                               "Missing required section 'artifacts'", 'REQUIRED_SECTION_MISSING')
            else:
                artifacts = api['artifacts']
                required_artifacts = ['contract_artifact_path', 'run_instructions_path']
                for field in required_artifacts:
                    if field not in artifacts or artifacts[field] is None:
                        result.add_error(category, f'result_data.implementations.api.artifacts.{field}',
                                       f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')
        
        # UI required fields if ui is present
        if 'ui' in implementations:
            ui = implementations['ui']
            
            # generation_metrics
            if 'generation_metrics' not in ui:
                result.add_error(category, 'result_data.implementations.ui.generation_metrics',
                               "Missing required section 'generation_metrics'", 'REQUIRED_SECTION_MISSING')
            else:
                metrics = ui['generation_metrics']
                required_metrics = [
                    'llm_model', 'start_timestamp', 'end_timestamp', 'duration_minutes',
                    'clarifications_count', 'interventions_count', 'reruns_count'
                ]
                for field in required_metrics:
                    if field not in metrics or metrics[field] is None:
                        result.add_error(category, f'result_data.implementations.ui.generation_metrics.{field}',
                                       f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')
            
            # build_success
            if 'build_success' not in ui or ui['build_success'] is None:
                result.add_error(category, 'result_data.implementations.ui.build_success',
                               "Missing required field 'build_success'", 'REQUIRED_FIELD_MISSING')
            
            # artifacts
            if 'artifacts' not in ui:
                result.add_error(category, 'result_data.implementations.ui.artifacts',
                               "Missing required section 'artifacts'", 'REQUIRED_SECTION_MISSING')
            else:
                artifacts = ui['artifacts']
                required_artifacts = ['ui_source_path', 'ui_run_summary_path']
                for field in required_artifacts:
                    if field not in artifacts or artifacts[field] is None:
                        result.add_error(category, f'result_data.implementations.ui.artifacts.{field}',
                                       f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')
    
    # submission required fields
    if 'submission' not in result_data:
        result.add_error(category, 'result_data.submission',
                       "Missing required section 'submission'", 'REQUIRED_SECTION_MISSING')
    else:
        submission = result_data['submission']
        required_submission = ['submitted_timestamp', 'submitted_by', 'submission_method']
        for field in required_submission:
            if field not in submission or submission[field] is None:
                result.add_error(category, f'result_data.submission.{field}',
                               f"Missing required field '{field}'", 'REQUIRED_FIELD_MISSING')


def validate_data_types(data: Dict, result: ValidationResult):
    """
    Validate field data types match schema expectations.
    
    Checks types for:
    - Strings (tool_name, api_style, etc.)
    - Numbers (duration_minutes, pass_rate, scores)
    - Integers (counts, run_number)
    - Booleans (build_success, flags)
    - Arrays (test_runs, validation_errors)
    - Objects (nested sections)
    """
    category = 'data_types'
    
    def check_type(path: str, value: Any, expected_type: type, type_name: str):
        """Helper to check a single value's type."""
        if value is not None and not isinstance(value, expected_type):
            actual_type = type(value).__name__
            result.add_error(category, path, 
                           f"Type mismatch: expected {type_name}, got {actual_type}",
                           'TYPE_MISMATCH')
    
    # schema_version must be string
    if 'schema_version' in data:
        check_type('schema_version', data['schema_version'], str, 'string')
    
    if 'result_data' not in data or not isinstance(data['result_data'], dict):
        return
    
    result_data = data['result_data']
    
    # run_identity string fields
    if 'run_identity' in result_data and isinstance(result_data['run_identity'], dict):
        run_identity = result_data['run_identity']
        string_fields = ['tool_name', 'tool_version', 'run_id', 'target_model', 
                        'api_style', 'spec_reference', 'workspace_path', 'run_environment']
        for field in string_fields:
            if field in run_identity:
                check_type(f'result_data.run_identity.{field}', run_identity[field], str, 'string')
        
        # run_number must be integer
        if 'run_number' in run_identity:
            check_type('result_data.run_identity.run_number', run_identity['run_number'], int, 'integer')
    
    # implementations type checking
    if 'implementations' in result_data and isinstance(result_data['implementations'], dict):
        implementations = result_data['implementations']
        
        # API types
        if 'api' in implementations and isinstance(implementations['api'], dict):
            api = implementations['api']
            
            # generation_metrics types
            if 'generation_metrics' in api and isinstance(api['generation_metrics'], dict):
                metrics = api['generation_metrics']
                check_type('result_data.implementations.api.generation_metrics.llm_model', 
                          metrics.get('llm_model'), str, 'string')
                check_type('result_data.implementations.api.generation_metrics.start_timestamp',
                          metrics.get('start_timestamp'), str, 'string')
                check_type('result_data.implementations.api.generation_metrics.end_timestamp',
                          metrics.get('end_timestamp'), str, 'string')
                check_type('result_data.implementations.api.generation_metrics.duration_minutes',
                          metrics.get('duration_minutes'), (int, float), 'number')
                check_type('result_data.implementations.api.generation_metrics.clarifications_count',
                          metrics.get('clarifications_count'), int, 'integer')
                check_type('result_data.implementations.api.generation_metrics.interventions_count',
                          metrics.get('interventions_count'), int, 'integer')
                check_type('result_data.implementations.api.generation_metrics.reruns_count',
                          metrics.get('reruns_count'), int, 'integer')
                
                # test_runs array
                if 'test_runs' in metrics:
                    check_type('result_data.implementations.api.generation_metrics.test_runs',
                              metrics['test_runs'], list, 'array')
                
                # test_iterations_count integer
                if 'test_iterations_count' in metrics:
                    check_type('result_data.implementations.api.generation_metrics.test_iterations_count',
                              metrics['test_iterations_count'], int, 'integer')
            
            # acceptance types
            if 'acceptance' in api and isinstance(api['acceptance'], dict):
                acceptance = api['acceptance']
                check_type('result_data.implementations.api.acceptance.pass_count',
                          acceptance.get('pass_count'), int, 'integer')
                check_type('result_data.implementations.api.acceptance.fail_count',
                          acceptance.get('fail_count'), int, 'integer')
                check_type('result_data.implementations.api.acceptance.not_run_count',
                          acceptance.get('not_run_count'), int, 'integer')
                check_type('result_data.implementations.api.acceptance.passrate',
                          acceptance.get('passrate'), (int, float), 'number')
            
            # quality_metrics types
            if 'quality_metrics' in api and isinstance(api['quality_metrics'], dict):
                quality = api['quality_metrics']
                if 'determinism_compliance' in quality:
                    check_type('result_data.implementations.api.quality_metrics.determinism_compliance',
                              quality['determinism_compliance'], str, 'string')
                if 'overreach_incidents_count' in quality:
                    check_type('result_data.implementations.api.quality_metrics.overreach_incidents_count',
                              quality['overreach_incidents_count'], int, 'integer')
                if 'contract_completeness_passrate' in quality:
                    check_type('result_data.implementations.api.quality_metrics.contract_completeness_passrate',
                              quality['contract_completeness_passrate'], (int, float), 'number')
                if 'instructions_quality_rating' in quality:
                    check_type('result_data.implementations.api.quality_metrics.instructions_quality_rating',
                              quality['instructions_quality_rating'], int, 'integer')
                if 'reproducibility_rating' in quality:
                    check_type('result_data.implementations.api.quality_metrics.reproducibility_rating',
                              quality['reproducibility_rating'], str, 'string')
        
        # UI types
        if 'ui' in implementations and isinstance(implementations['ui'], dict):
            ui = implementations['ui']
            
            # generation_metrics types (similar to API)
            if 'generation_metrics' in ui and isinstance(ui['generation_metrics'], dict):
                metrics = ui['generation_metrics']
                check_type('result_data.implementations.ui.generation_metrics.llm_model',
                          metrics.get('llm_model'), str, 'string')
                check_type('result_data.implementations.ui.generation_metrics.duration_minutes',
                          metrics.get('duration_minutes'), (int, float), 'number')
                check_type('result_data.implementations.ui.generation_metrics.clarifications_count',
                          metrics.get('clarifications_count'), int, 'integer')
                check_type('result_data.implementations.ui.generation_metrics.interventions_count',
                          metrics.get('interventions_count'), int, 'integer')
                check_type('result_data.implementations.ui.generation_metrics.reruns_count',
                          metrics.get('reruns_count'), int, 'integer')
                
                # backend_changes_required boolean
                if 'backend_changes_required' in metrics:
                    check_type('result_data.implementations.ui.generation_metrics.backend_changes_required',
                              metrics['backend_changes_required'], bool, 'boolean')
            
            # build_success boolean
            if 'build_success' in ui:
                check_type('result_data.implementations.ui.build_success',
                          ui['build_success'], bool, 'boolean')
    
    # submission types
    if 'submission' in result_data and isinstance(result_data['submission'], dict):
        submission = result_data['submission']
        check_type('result_data.submission.submitted_timestamp',
                  submission.get('submitted_timestamp'), str, 'string')
        check_type('result_data.submission.submitted_by',
                  submission.get('submitted_by'), str, 'string')
        check_type('result_data.submission.submission_method',
                  submission.get('submission_method'), str, 'string')


def validate_enum_values(data: Dict, result: ValidationResult):
    """
    Validate fields with restricted enum values.
    
    Checks:
    - schema_version: "3.0" (or "2.0" for backward compatibility)
    - target_model: "A" or "B"
    - api_style: "REST" or "GraphQL"
    - run_number: 1 or 2
    - submission_method: "automated" or "manual"
    - determinism_compliance: "Pass", "Fail", "Unknown"
    - instructions_quality_rating: 100, 70, 40, 0
    - reproducibility_rating: "None", "Minor", "Major", "Unknown"
    - usage_source: "tool_reported", "operator_estimated", "unknown"
    """
    category = 'enum_values'
    
    def check_enum(path: str, value: Any, allowed_values: List, field_name: str):
        """Helper to check enum value."""
        if value is not None and value not in allowed_values:
            result.add_error(category, path,
                           f"Invalid value '{value}' for {field_name}. Allowed values: {', '.join(str(v) for v in allowed_values)}",
                           'INVALID_ENUM_VALUE')
    
    # schema_version
    if 'schema_version' in data:
        check_enum('schema_version', data['schema_version'], ['3.0', '2.0'], 'schema_version')
    
    if 'result_data' not in data:
        return
    
    result_data = data['result_data']
    
    # run_identity enums
    if 'run_identity' in result_data and isinstance(result_data['run_identity'], dict):
        run_identity = result_data['run_identity']
        check_enum('result_data.run_identity.target_model', 
                  run_identity.get('target_model'), ['A', 'B'], 'target_model')
        check_enum('result_data.run_identity.api_style',
                  run_identity.get('api_style'), ['REST', 'GraphQL'], 'api_style')
        check_enum('result_data.run_identity.run_number',
                  run_identity.get('run_number'), [1, 2], 'run_number')
    
    # API quality_metrics enums
    if 'implementations' in result_data and isinstance(result_data['implementations'], dict):
        implementations = result_data['implementations']
        
        if 'api' in implementations and isinstance(implementations['api'], dict):
            api = implementations['api']
            
            if 'quality_metrics' in api and isinstance(api['quality_metrics'], dict):
                quality = api['quality_metrics']
                
                check_enum('result_data.implementations.api.quality_metrics.determinism_compliance',
                          quality.get('determinism_compliance'), 
                          ['Pass', 'Fail', 'Unknown'], 'determinism_compliance')
                
                check_enum('result_data.implementations.api.quality_metrics.instructions_quality_rating',
                          quality.get('instructions_quality_rating'),
                          [100, 70, 40, 0], 'instructions_quality_rating')
                
                check_enum('result_data.implementations.api.quality_metrics.reproducibility_rating',
                          quality.get('reproducibility_rating'),
                          ['None', 'Minor', 'Major', 'Unknown'], 'reproducibility_rating')
            
            # llm_usage.usage_source enum
            if 'generation_metrics' in api and isinstance(api['generation_metrics'], dict):
                metrics = api['generation_metrics']
                if 'llm_usage' in metrics and isinstance(metrics['llm_usage'], dict):
                    check_enum('result_data.implementations.api.generation_metrics.llm_usage.usage_source',
                              metrics['llm_usage'].get('usage_source'),
                              ['tool_reported', 'operator_estimated', 'unknown'], 'usage_source')
    
    # submission enum
    if 'submission' in result_data and isinstance(result_data['submission'], dict):
        submission = result_data['submission']
        check_enum('result_data.submission.submission_method',
                  submission.get('submission_method'),
                  ['automated', 'manual'], 'submission_method')
    
    # processing enums (v3.0)
    if 'processing' in result_data and isinstance(result_data['processing'], dict):
        processing = result_data['processing']
        check_enum('result_data.processing.validation_status',
                  processing.get('validation_status'),
                  ['pending', 'valid', 'invalid', 'error'], 'validation_status')
        check_enum('result_data.processing.storage_status',
                  processing.get('storage_status'),
                  ['pending', 'stored', 'failed', 'duplicate_replaced'], 'storage_status')


def validate_formats(data: Dict, result: ValidationResult):
    """
    Validate field formats, especially timestamps.
    
    Checks:
    - Timestamp format: ISO-8601 UTC (YYYY-MM-DDTHH:MM:SS.sssZ or YYYY-MM-DDTHH:MM:SSZ)
    - All *_timestamp fields throughout the structure
    """
    category = 'formats'
    
    # ISO-8601 UTC timestamp pattern (with optional milliseconds)
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$'
    
    def check_timestamp(path: str, value: Any, field_name: str):
        """Helper to check timestamp format."""
        if value is None:
            return
        
        if not isinstance(value, str):
            result.add_error(category, path,
                           f"{field_name} must be a string in ISO-8601 format",
                           'INVALID_FORMAT')
            return
        
        if not re.match(timestamp_pattern, value):
            result.add_error(category, path,
                           f"Invalid timestamp format for {field_name}: '{value}'. Expected ISO-8601 UTC format: YYYY-MM-DDTHH:MM:SS.sssZ",
                           'INVALID_TIMESTAMP_FORMAT')
    
    if 'result_data' not in data:
        return
    
    result_data = data['result_data']
    
    # API generation_metrics timestamps
    if 'implementations' in result_data and isinstance(result_data['implementations'], dict):
        implementations = result_data['implementations']
        
        if 'api' in implementations and isinstance(implementations['api'], dict):
            api = implementations['api']
            
            if 'generation_metrics' in api and isinstance(api['generation_metrics'], dict):
                metrics = api['generation_metrics']
                check_timestamp('result_data.implementations.api.generation_metrics.start_timestamp',
                              metrics.get('start_timestamp'), 'start_timestamp')
                check_timestamp('result_data.implementations.api.generation_metrics.end_timestamp',
                              metrics.get('end_timestamp'), 'end_timestamp')
                
                # test_runs timestamps
                if 'test_runs' in metrics and isinstance(metrics['test_runs'], list):
                    for i, test_run in enumerate(metrics['test_runs']):
                        if isinstance(test_run, dict):
                            check_timestamp(f'result_data.implementations.api.generation_metrics.test_runs[{i}].start_timestamp',
                                          test_run.get('start_timestamp'), 'start_timestamp')
                            check_timestamp(f'result_data.implementations.api.generation_metrics.test_runs[{i}].end_timestamp',
                                          test_run.get('end_timestamp'), 'end_timestamp')
        
        # UI generation_metrics timestamps
        if 'ui' in implementations and isinstance(implementations['ui'], dict):
            ui = implementations['ui']
            
            if 'generation_metrics' in ui and isinstance(ui['generation_metrics'], dict):
                metrics = ui['generation_metrics']
                check_timestamp('result_data.implementations.ui.generation_metrics.start_timestamp',
                              metrics.get('start_timestamp'), 'start_timestamp')
                check_timestamp('result_data.implementations.ui.generation_metrics.end_timestamp',
                              metrics.get('end_timestamp'), 'end_timestamp')
    
    # submission timestamps
    if 'submission' in result_data and isinstance(result_data['submission'], dict):
        submission = result_data['submission']
        check_timestamp('result_data.submission.submitted_timestamp',
                      submission.get('submitted_timestamp'), 'submitted_timestamp')
        
        # github_issue timestamps (v3.0)
        if 'github_issue' in submission and isinstance(submission['github_issue'], dict):
            github_issue = submission['github_issue']
            check_timestamp('result_data.submission.github_issue.issue_created_at',
                          github_issue.get('issue_created_at'), 'issue_created_at')
            check_timestamp('result_data.submission.github_issue.issue_closed_at',
                          github_issue.get('issue_closed_at'), 'issue_closed_at')
    
    # processing timestamps (v3.0)
    if 'processing' in result_data and isinstance(result_data['processing'], dict):
        processing = result_data['processing']
        check_timestamp('result_data.processing.ingested_timestamp',
                      processing.get('ingested_timestamp'), 'ingested_timestamp')
        check_timestamp('result_data.processing.processed_timestamp',
                      processing.get('processed_timestamp'), 'processed_timestamp')
    
    # storage_metadata timestamps (v3.0)
    if 'storage_metadata' in result_data and isinstance(result_data['storage_metadata'], dict):
        storage = result_data['storage_metadata']
        check_timestamp('result_data.storage_metadata.stored_at',
                      storage.get('stored_at'), 'stored_at')
    
    # validation_metadata timestamps (v3.0)
    if 'validation_metadata' in result_data and isinstance(result_data['validation_metadata'], dict):
        validation_meta = result_data['validation_metadata']
        check_timestamp('result_data.validation_metadata.validated_at',
                      validation_meta.get('validated_at'), 'validated_at')
    
    # aggregation_metadata timestamps (v3.0)
    if 'aggregation_metadata' in result_data and isinstance(result_data['aggregation_metadata'], dict):
        aggregation = result_data['aggregation_metadata']
        check_timestamp('result_data.aggregation_metadata.last_aggregated_at',
                      aggregation.get('last_aggregated_at'), 'last_aggregated_at')
        check_timestamp('result_data.aggregation_metadata.csv_export_timestamp',
                      aggregation.get('csv_export_timestamp'), 'csv_export_timestamp')


def validate_ranges(data: Dict, result: ValidationResult):
    """
    Validate numeric field ranges.
    
    Checks:
    - passrate: 0.0 to 1.0
    - pass_rate (test_runs): 0.0 to 1.0
    - contract_completeness_passrate: 0.0 to 1.0
    - scores (all): 0 to 100
    - penalty_overreach_PO: 0 to 40
    - duration_minutes: >= 0
    - All counts: >= 0
    - partition_month: 1 to 12
    - issue_number: >= 1
    """
    category = 'ranges'
    
    def check_range(path: str, value: Any, minimum: Optional[float], maximum: Optional[float], field_name: str):
        """Helper to check numeric range."""
        if value is None:
            return
        
        if not isinstance(value, (int, float)):
            return  # Type error will be caught by validate_data_types
        
        if minimum is not None and value < minimum:
            result.add_error(category, path,
                           f"{field_name} value {value} is below minimum {minimum}",
                           'VALUE_BELOW_MINIMUM')
        
        if maximum is not None and value > maximum:
            result.add_error(category, path,
                           f"{field_name} value {value} exceeds maximum {maximum}",
                           'VALUE_ABOVE_MAXIMUM')
    
    if 'result_data' not in data:
        return
    
    result_data = data['result_data']
    
    # API validation
    if 'implementations' in result_data and isinstance(result_data['implementations'], dict):
        implementations = result_data['implementations']
        
        if 'api' in implementations and isinstance(implementations['api'], dict):
            api = implementations['api']
            
            # generation_metrics ranges
            if 'generation_metrics' in api and isinstance(api['generation_metrics'], dict):
                metrics = api['generation_metrics']
                check_range('result_data.implementations.api.generation_metrics.duration_minutes',
                          metrics.get('duration_minutes'), 0, None, 'duration_minutes')
                check_range('result_data.implementations.api.generation_metrics.clarifications_count',
                          metrics.get('clarifications_count'), 0, None, 'clarifications_count')
                check_range('result_data.implementations.api.generation_metrics.interventions_count',
                          metrics.get('interventions_count'), 0, None, 'interventions_count')
                check_range('result_data.implementations.api.generation_metrics.reruns_count',
                          metrics.get('reruns_count'), 0, None, 'reruns_count')
                check_range('result_data.implementations.api.generation_metrics.test_iterations_count',
                          metrics.get('test_iterations_count'), 1, None, 'test_iterations_count')
                
                # test_runs ranges
                if 'test_runs' in metrics and isinstance(metrics['test_runs'], list):
                    for i, test_run in enumerate(metrics['test_runs']):
                        if isinstance(test_run, dict):
                            check_range(f'result_data.implementations.api.generation_metrics.test_runs[{i}].pass_rate',
                                      test_run.get('pass_rate'), 0, 1, 'pass_rate')
                            check_range(f'result_data.implementations.api.generation_metrics.test_runs[{i}].total_tests',
                                      test_run.get('total_tests'), 0, None, 'total_tests')
                            check_range(f'result_data.implementations.api.generation_metrics.test_runs[{i}].passed',
                                      test_run.get('passed'), 0, None, 'passed')
                            check_range(f'result_data.implementations.api.generation_metrics.test_runs[{i}].failed',
                                      test_run.get('failed'), 0, None, 'failed')
                
                # llm_usage ranges
                if 'llm_usage' in metrics and isinstance(metrics['llm_usage'], dict):
                    llm_usage = metrics['llm_usage']
                    check_range('result_data.implementations.api.generation_metrics.llm_usage.input_tokens',
                              llm_usage.get('input_tokens'), 0, None, 'input_tokens')
                    check_range('result_data.implementations.api.generation_metrics.llm_usage.output_tokens',
                              llm_usage.get('output_tokens'), 0, None, 'output_tokens')
                    check_range('result_data.implementations.api.generation_metrics.llm_usage.total_tokens',
                              llm_usage.get('total_tokens'), 0, None, 'total_tokens')
                    check_range('result_data.implementations.api.generation_metrics.llm_usage.requests_count',
                              llm_usage.get('requests_count'), 0, None, 'requests_count')
                    check_range('result_data.implementations.api.generation_metrics.llm_usage.estimated_cost_usd',
                              llm_usage.get('estimated_cost_usd'), 0, None, 'estimated_cost_usd')
            
            # acceptance ranges
            if 'acceptance' in api and isinstance(api['acceptance'], dict):
                acceptance = api['acceptance']
                check_range('result_data.implementations.api.acceptance.pass_count',
                          acceptance.get('pass_count'), 0, None, 'pass_count')
                check_range('result_data.implementations.api.acceptance.fail_count',
                          acceptance.get('fail_count'), 0, None, 'fail_count')
                check_range('result_data.implementations.api.acceptance.not_run_count',
                          acceptance.get('not_run_count'), 0, None, 'not_run_count')
                check_range('result_data.implementations.api.acceptance.passrate',
                          acceptance.get('passrate'), 0, 1, 'passrate')
            
            # quality_metrics ranges
            if 'quality_metrics' in api and isinstance(api['quality_metrics'], dict):
                quality = api['quality_metrics']
                check_range('result_data.implementations.api.quality_metrics.overreach_incidents_count',
                          quality.get('overreach_incidents_count'), 0, None, 'overreach_incidents_count')
                check_range('result_data.implementations.api.quality_metrics.contract_completeness_passrate',
                          quality.get('contract_completeness_passrate'), 0, 1, 'contract_completeness_passrate')
            
            # scores ranges
            if 'scores' in api and isinstance(api['scores'], dict):
                scores = api['scores']
                score_fields = [
                    'correctness_C', 'reproducibility_R', 'determinism_D',
                    'effort_E', 'speed_S', 'contract_docs_K', 'overall_score'
                ]
                for score_field in score_fields:
                    check_range(f'result_data.implementations.api.scores.{score_field}',
                              scores.get(score_field), 0, 100, score_field)
                
                # penalty_overreach_PO has different range
                check_range('result_data.implementations.api.scores.penalty_overreach_PO',
                          scores.get('penalty_overreach_PO'), 0, 40, 'penalty_overreach_PO')
        
        # UI validation
        if 'ui' in implementations and isinstance(implementations['ui'], dict):
            ui = implementations['ui']
            
            if 'generation_metrics' in ui and isinstance(ui['generation_metrics'], dict):
                metrics = ui['generation_metrics']
                check_range('result_data.implementations.ui.generation_metrics.duration_minutes',
                          metrics.get('duration_minutes'), 0, None, 'duration_minutes')
                check_range('result_data.implementations.ui.generation_metrics.clarifications_count',
                          metrics.get('clarifications_count'), 0, None, 'clarifications_count')
                check_range('result_data.implementations.ui.generation_metrics.interventions_count',
                          metrics.get('interventions_count'), 0, None, 'interventions_count')
                check_range('result_data.implementations.ui.generation_metrics.reruns_count',
                          metrics.get('reruns_count'), 0, None, 'reruns_count')
    
    # submission.github_issue ranges (v3.0)
    if 'submission' in result_data and isinstance(result_data['submission'], dict):
        submission = result_data['submission']
        if 'github_issue' in submission and isinstance(submission['github_issue'], dict):
            github_issue = submission['github_issue']
            check_range('result_data.submission.github_issue.issue_number',
                      github_issue.get('issue_number'), 1, None, 'issue_number')
    
    # storage_metadata ranges (v3.0)
    if 'storage_metadata' in result_data and isinstance(result_data['storage_metadata'], dict):
        storage = result_data['storage_metadata']
        check_range('result_data.storage_metadata.partition_month',
                  storage.get('partition_month'), 1, 12, 'partition_month')


def validate_with_schema(data: Dict, schema: Dict, result: ValidationResult):
    """
    Validate using JSON Schema (if available).
    
    This provides comprehensive validation using the official schema.
    Errors are added to the result object.
    """
    if not JSONSCHEMA_AVAILABLE or schema is None:
        return
    
    validator = Draft7Validator(schema)
    
    for error in validator.iter_errors(data):
        # Extract field path
        field_path = '.'.join(str(p) for p in error.absolute_path)
        if not field_path:
            field_path = 'root'
        
        # Determine category based on error type
        error_type = error.validator
        if error_type == 'required':
            category = 'required_fields'
        elif error_type == 'type':
            category = 'data_types'
        elif error_type == 'enum':
            category = 'enum_values'
        elif error_type in ['pattern', 'format']:
            category = 'formats'
        elif error_type in ['minimum', 'maximum']:
            category = 'ranges'
        else:
            category = 'required_fields'  # Default category
        
        # Add error
        result.add_error(category, field_path, error.message, error_type.upper())


def validate_result_json(data: Dict, schema: Optional[Dict] = None, use_schema: bool = True) -> ValidationResult:
    """
    Validate result JSON data.
    
    Args:
        data: Result JSON dictionary to validate
        schema: Optional pre-loaded schema dictionary
        use_schema: Whether to use JSON Schema validation (in addition to explicit checks)
    
    Returns:
        ValidationResult object with validation results
    """
    result = ValidationResult()
    
    # Load schema if not provided and schema validation is requested
    if use_schema and schema is None:
        schema = load_schema()
    
    # Run explicit validation checks (always)
    validate_required_fields(data, result)
    validate_data_types(data, result)
    validate_enum_values(data, result)
    validate_formats(data, result)
    validate_ranges(data, result)
    
    # Run JSON Schema validation if available and requested
    if use_schema and JSONSCHEMA_AVAILABLE and schema is not None:
        validate_with_schema(data, schema, result)
    
    return result


def validate_result_file(file_path: str, schema: Optional[Dict] = None, use_schema: bool = True) -> ValidationResult:
    """
    Validate a result file.
    
    Args:
        file_path: Path to result JSON file
        schema: Optional pre-loaded schema dictionary
        use_schema: Whether to use JSON Schema validation
    
    Returns:
        ValidationResult object with validation results
    """
    result = ValidationResult()
    
    # Check file exists
    if not os.path.exists(file_path):
        result.add_error('required_fields', file_path, f"File not found: {file_path}", 'FILE_NOT_FOUND')
        return result
    
    # Load JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error('required_fields', file_path, f"Invalid JSON: {e}", 'INVALID_JSON')
        return result
    except Exception as e:
        result.add_error('required_fields', file_path, f"Error reading file: {e}", 'FILE_READ_ERROR')
        return result
    
    # Validate JSON data
    return validate_result_json(data, schema, use_schema)


def validate_directory(dir_path: str, pattern: str = "*.json", schema: Optional[Dict] = None, use_schema: bool = True) -> Dict:
    """
    Validate all result files in a directory.
    
    Args:
        dir_path: Path to directory
        pattern: Glob pattern for files to validate
        schema: Optional pre-loaded schema dictionary
        use_schema: Whether to use JSON Schema validation
    
    Returns:
        Dictionary with summary and individual file results
    """
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        return {
            'success': False,
            'error': f"Directory not found: {dir_path}",
            'files': []
        }
    
    if not dir_path.is_dir():
        return {
            'success': False,
            'error': f"Not a directory: {dir_path}",
            'files': []
        }
    
    # Find all matching files
    files = list(dir_path.glob(pattern))
    
    if not files:
        return {
            'success': True,
            'message': f"No files matching pattern '{pattern}' found in {dir_path}",
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'files': []
        }
    
    # Load schema once for all files
    if use_schema and schema is None:
        schema = load_schema()
    
    # Validate each file
    results = []
    valid_count = 0
    invalid_count = 0
    
    for file_path in files:
        validation_result = validate_result_file(str(file_path), schema, use_schema)
        
        if validation_result.valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        results.append({
            'file': str(file_path.name),
            'file_path': str(file_path),
            'valid': validation_result.valid,
            'error_count': len(validation_result.errors),
            'errors': validation_result.errors
        })
    
    return {
        'success': True,
        'total_files': len(files),
        'valid_files': valid_count,
        'invalid_files': invalid_count,
        'files': results,
        'validator_version': VALIDATOR_VERSION
    }


def format_text_output(validation_result: ValidationResult, file_path: Optional[str] = None) -> str:
    """
    Format validation result as human-readable text.
    
    Args:
        validation_result: ValidationResult object
        file_path: Optional file path to include in output
    
    Returns:
        Formatted text string
    """
    lines = []
    
    if file_path:
        lines.append(f"Validation Result for: {file_path}")
        lines.append("=" * 60)
    
    if validation_result.valid:
        lines.append("✅ VALID - All validation checks passed")
    else:
        lines.append("❌ INVALID - Validation failed")
        lines.append(f"\nTotal Errors: {len(validation_result.errors)}")
        
        # Group errors by category
        for category, errors in validation_result.categories.items():
            if errors:
                lines.append(f"\n{category.replace('_', ' ').title()} ({len(errors)} errors):")
                for error in errors:
                    lines.append(f"  • [{error['field_path']}] {error['message']}")
    
    if validation_result.warnings:
        lines.append(f"\nWarnings ({len(validation_result.warnings)}):")
        for warning in validation_result.warnings:
            lines.append(f"  • {warning}")
    
    return "\n".join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Validate PawMate result files against v3.0 schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'path',
        type=str,
        help='Path to result file or directory'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--schema', '-s',
        type=str,
        default=None,
        help='Path to schema file (default: auto-detect)'
    )
    parser.add_argument(
        '--no-schema',
        action='store_true',
        help='Skip JSON Schema validation, use only explicit checks'
    )
    parser.add_argument(
        '--pattern', '-p',
        type=str,
        default='*.json',
        help='Glob pattern for files in directory (default: *.json)'
    )
    
    args = parser.parse_args()
    
    # Load schema if needed
    schema = None
    use_schema = not args.no_schema
    
    if use_schema:
        schema = load_schema(args.schema)
        if schema is None and JSONSCHEMA_AVAILABLE:
            print("Warning: Could not load schema, using explicit validation only", file=sys.stderr)
    
    # Determine if path is file or directory
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)
    
    # Validate
    if path.is_file():
        # Single file validation
        validation_result = validate_result_file(str(path), schema, use_schema)
        
        if args.output == 'json':
            output = validation_result.to_dict()
            output['file'] = str(path)
            json.dump(output, sys.stdout, indent=2)
            sys.stdout.write('\n')
        else:
            print(format_text_output(validation_result, str(path)))
        
        sys.exit(0 if validation_result.valid else 1)
    
    elif path.is_dir():
        # Directory validation
        directory_result = validate_directory(str(path), args.pattern, schema, use_schema)
        
        if not directory_result.get('success', False):
            print(f"Error: {directory_result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
        
        if args.output == 'json':
            json.dump(directory_result, sys.stdout, indent=2)
            sys.stdout.write('\n')
        else:
            # Text summary
            print(f"Directory Validation: {path}")
            print("=" * 60)
            print(f"Total Files: {directory_result['total_files']}")
            print(f"Valid Files: {directory_result['valid_files']}")
            print(f"Invalid Files: {directory_result['invalid_files']}")
            
            if directory_result['invalid_files'] > 0:
                print("\nInvalid Files:")
                for file_result in directory_result['files']:
                    if not file_result['valid']:
                        print(f"\n  {file_result['file']} ({file_result['error_count']} errors)")
                        for error in file_result['errors'][:5]:  # Show first 5 errors
                            print(f"    • [{error['field_path']}] {error['message']}")
                        if file_result['error_count'] > 5:
                            print(f"    ... and {file_result['error_count'] - 5} more errors")
        
        sys.exit(0 if directory_result['invalid_files'] == 0 else 1)
    
    else:
        print(f"Error: Path must be a file or directory: {args.path}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
