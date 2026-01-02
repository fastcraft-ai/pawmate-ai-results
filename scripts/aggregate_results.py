#!/usr/bin/env python3
"""
aggregate_results.py — Benchmark results aggregation with v2.0 and v3.0 schema support

Generates HTML reports with:
- Clear metric names (no cryptic abbreviations)
- Visual charts and graphs
- Separate API and UI timing/scoring
- Executive summary with insights
- Better readability

Usage:
    python3 scripts/aggregate_results.py [--input-dir <dir>] [--output-dir <dir>]
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def detect_schema_version(data: dict) -> str:
    """Detect which schema version is being used."""
    schema_version = data.get('schema_version', '2.0')
    
    # Check for v3.0 schema (explicitly set)
    if schema_version == '3.0':
        return '3.0'
    
    # Check for v2.0 schema (explicitly set or default)
    if schema_version == '2.0':
        return '2.0'
    
    # Fallback: if implementations structure exists, assume v2.0 (backward compatibility)
    if 'implementations' in data.get('result_data', {}):
        return '2.0'
    
    # If schema_version is explicitly set to something else, return it (for error reporting)
    return schema_version


def parse_result_file(file_path: Path) -> Optional[dict]:
    """Parse a result file and return structured data."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Add metadata
        data['_filename'] = file_path.name
        data['_filepath'] = str(file_path)
        data['_schema_version'] = detect_schema_version(data)
        
        return data
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None


def extract_metrics(result: dict) -> dict:
    """Extract metrics from v2.0 or v3.0 schema (separate API/UI).
    
    Core structure (run_identity, implementations) is identical between v2.0 and v3.0,
    so the same extraction logic works for both versions.
    """
    impls = result['result_data']['implementations']
    
    api_metrics = {}
    ui_metrics = {}
    
    # API implementation
    if 'api' in impls:
        api = impls['api']
        gen = api.get('generation_metrics', {})
        
        api_metrics = {
            'time': gen.get('duration_minutes', 'N/A'),
            'llm_model': gen.get('llm_model', 'Unknown'),
            'test_iterations': gen.get('test_iterations_count', 'N/A'),
            'test_runs': gen.get('test_runs', [])
        }
    
    # UI implementation
    if 'ui' in impls:
        ui = impls['ui']
        gen = ui.get('generation_metrics', {})
        
        ui_metrics = {
            'time': gen.get('duration_minutes', 'N/A'),
            'llm_model': gen.get('llm_model', 'Unknown'),
            'build_success': ui.get('build_success', False),
            'backend_changes': gen.get('backend_changes_required', False)
        }
    
    return {
        'api': api_metrics,
        'ui': ui_metrics,
        'has_ui': 'ui' in impls
    }


def generate_html_report(group_key: Tuple[str, str, str], group_results: List[dict], output_dir: Path) -> None:
    """Generate an enhanced HTML comparison report."""
    spec_ref, model, api_type = group_key
    
    # Group by tool
    tools = defaultdict(lambda: {'run1': None, 'run2': None})
    
    for result in group_results:
        ri = result['result_data']['run_identity']
        tool_key = f"{ri['tool_name']} {ri.get('tool_version', '')}".strip()
        run_num = ri['run_number']
        
        if run_num == 1:
            tools[tool_key]['run1'] = result
        elif run_num == 2:
            tools[tool_key]['run2'] = result
    
    report_id = f"{spec_ref}-Model{model}-{api_type}-Comparison"
    report_path = output_dir / f"{report_id}.html"
    
    # Prepare data for charts
    tool_names = sorted(tools.keys())
    
    # Extract metrics for each tool
    tool_data = []
    for tool_name in tool_names:
        run1 = tools[tool_name]['run1']
        if not run1:
            continue
        
        schema_ver = run1.get('_schema_version', '2.0')
        
        # Support both v2.0 and v3.0 schemas (core structure is identical)
        if schema_ver not in ['2.0', '3.0']:
            print(f"Warning: Skipping result with unsupported schema version {schema_ver}: {run1.get('_filename', 'unknown')}", file=sys.stderr)
            continue
        
        metrics = extract_metrics(run1)
        
        tool_data.append({
            'name': tool_name,
            'schema_version': schema_ver,
            'metrics': metrics,
            'run1': run1,
            'run2': tools[tool_name]['run2']
        })
    
    # Generate HTML
    html = generate_html_content(report_id, spec_ref, model, api_type, tool_data)
    
    with open(report_path, 'w') as f:
        f.write(html)
    
    print(f"✓ Generated HTML report: {report_path}")


def generate_html_content(report_id: str, spec_ref: str, model: str, api_type: str, tool_data: List[dict]) -> str:
    """Generate the HTML content for the report."""
    
    # Generate executive summary
    summary_html = generate_executive_summary(tool_data)
    
    # Generate comparison tables
    tables_html = generate_comparison_tables(tool_data)
    
    # Generate charts
    charts_html = generate_charts_html(tool_data)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_id} - Benchmark Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        
        h2 {{
            color: #555;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        h3 {{
            color: #666;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .report-header h1 {{
            color: white;
            border: none;
            margin: 0;
        }}
        
        .meta-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .meta-item {{
            background: rgba(255,255,255,0.2);
            padding: 10px 15px;
            border-radius: 6px;
        }}
        
        .meta-label {{
            font-size: 0.85rem;
            opacity: 0.9;
        }}
        
        .meta-value {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 5px;
        }}
        
        .executive-summary {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 20px;
            border-radius: 6px;
            margin: 30px 0;
        }}
        
        .summary-highlights {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .highlight-card {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #c8e6c9;
        }}
        
        .highlight-label {{
            font-size: 0.875rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .highlight-value {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #2e7d32;
            margin-top: 5px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tr:hover {{
            background: #f5f5f5;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .metric-explainer {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 20px 0;
            border-radius: 6px;
        }}
        
        .metric-explainer strong {{
            color: #e65100;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .badge-v2 {{
            background: #4caf50;
            color: white;
        }}
        
        .badge-v3 {{
            background: #2196f3;
            color: white;
        }}
        
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>📊 {report_id}</h1>
            <div class="meta-info">
                <div class="meta-item">
                    <div class="meta-label">Specification</div>
                    <div class="meta-value">{spec_ref}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Target Model</div>
                    <div class="meta-value">Model {model}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">API Style</div>
                    <div class="meta-value">{api_type}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Generated</div>
                    <div class="meta-value">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                </div>
            </div>
        </div>
        
        {summary_html}
        
        <h2>📈 Visual Comparison</h2>
        {charts_html}
        
        <h2>📋 Detailed Metrics</h2>
        {tables_html}
        
        <div class="footer">
            <p>PawMate Benchmark Report • Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def generate_executive_summary(tool_data: List[dict]) -> str:
    """Generate executive summary section."""
    if not tool_data:
        return "<p>No data available for summary.</p>"
    
    # Calculate some interesting statistics
    total_tools = len(tool_data)
    tools_with_ui = sum(1 for t in tool_data if t['metrics'].get('has_ui', False))
    
    # Find fastest API generation
    api_times = []
    for tool in tool_data:
        time = tool['metrics']['api'].get('time', 'N/A')
        if time != 'N/A' and isinstance(time, (int, float)):
            api_times.append((tool['name'], time))
    
    fastest_api = min(api_times, key=lambda x: x[1]) if api_times else None
    
    # Calculate average test iterations
    test_iterations_list = []
    for tool in tool_data:
        iterations = tool['metrics']['api'].get('test_iterations', 'N/A')
        if iterations != 'N/A' and isinstance(iterations, (int, float)):
            test_iterations_list.append(iterations)
    
    avg_test_iterations = sum(test_iterations_list) / len(test_iterations_list) if test_iterations_list else None
    
    html = """
    <div class="executive-summary">
        <h2>📝 Executive Summary</h2>
        <div class="summary-highlights">
            <div class="highlight-card">
                <div class="highlight-label">Tools Compared</div>
                <div class="highlight-value">""" + str(total_tools) + """</div>
            </div>
            <div class="highlight-card">
                <div class="highlight-label">With UI Implementation</div>
                <div class="highlight-value">""" + str(tools_with_ui) + """</div>
            </div>
    """
    
    if fastest_api:
        html += f"""
            <div class="highlight-card">
                <div class="highlight-label">Fastest API Generation</div>
                <div class="highlight-value">{fastest_api[0]}</div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">{fastest_api[1]} minutes</div>
            </div>
        """
    
    if avg_test_iterations:
        html += f"""
            <div class="highlight-card">
                <div class="highlight-label">Avg Test Iterations</div>
                <div class="highlight-value">{avg_test_iterations:.1f}</div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">times tests were run</div>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html


def generate_comparison_tables(tool_data: List[dict]) -> str:
    """Generate HTML comparison tables."""
    
    html = ""
    
    # API metrics table
    if tool_data:
        html += """
        <h3>API Implementation Metrics</h3>
        <div class="metric-explainer">
            <strong>Understanding the metrics:</strong>
            <ul style="margin-top: 10px; margin-left: 20px;">
                <li><strong>Time:</strong> Minutes from start to completion</li>
                <li><strong>Test Iterations:</strong> Number of times tests were run before all passed</li>
            </ul>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Tool</th>
                    <th>LLM Model</th>
                    <th>Time (min)</th>
                    <th>Test Iterations</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for tool in tool_data:
            api = tool['metrics']['api']
            html += f"""
                <tr>
                    <td><strong>{tool['name']}</strong></td>
                    <td>{api.get('llm_model', 'Unknown')}</td>
                    <td>{api.get('time', 'N/A')}</td>
                    <td>{api.get('test_iterations', 'N/A')}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        # UI metrics table (if any have UI)
        tools_with_ui = [t for t in tool_data if t['metrics'].get('has_ui', False)]
        if tools_with_ui:
            html += """
            <h3>UI Implementation Metrics</h3>
            <div class="metric-explainer">
                <strong>UI-specific metrics:</strong>
                <ul style="margin-top: 10px; margin-left: 20px;">
                    <li><strong>Time:</strong> Minutes from start to completion</li>
                    <li><strong>Build Success:</strong> Whether UI builds and runs without errors</li>
                    <li><strong>Backend Changes:</strong> Whether UI required backend modifications</li>
                </ul>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Tool</th>
                        <th>LLM Model</th>
                        <th>Time (min)</th>
                        <th>Build Success</th>
                        <th>Backend Changes</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for tool in tools_with_ui:
                ui = tool['metrics']['ui']
                backend_changes = '✓ Yes' if ui.get('backend_changes', False) else '✗ No'
                build_success = '✓ Yes' if ui.get('build_success', False) else '✗ No'
                
                html += f"""
                    <tr>
                        <td><strong>{tool['name']}</strong></td>
                        <td>{ui.get('llm_model', 'Unknown')}</td>
                        <td>{ui.get('time', 'N/A')}</td>
                        <td>{build_success}</td>
                        <td>{backend_changes}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
    
    return html


def generate_charts_html(tool_data: List[dict]) -> str:
    """Generate Chart.js visualizations."""
    
    if not tool_data:
        return "<p>No data available for charts.</p>"
    
    tool_names = [t['name'] for t in tool_data]
    api_times = [t['metrics']['api'].get('time', 0) if isinstance(t['metrics']['api'].get('time', 0), (int, float)) else 0 for t in tool_data]
    ui_times = [t['metrics']['ui'].get('time', 0) if t['metrics'].get('has_ui') and isinstance(t['metrics']['ui'].get('time', 0), (int, float)) else 0 for t in tool_data]
    
    # Prepare test iterations data
    test_iterations = [t['metrics']['api'].get('test_iterations', 0) if isinstance(t['metrics']['api'].get('test_iterations', 0), (int, float)) else 0 for t in tool_data]
    
    html = f"""
    <div class="chart-container">
        <canvas id="timingChart"></canvas>
    </div>
    
    <div class="chart-container">
        <canvas id="iterationsChart"></canvas>
    </div>
    
    <script>
        // Timing comparison chart
        new Chart(document.getElementById('timingChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(tool_names)},
                datasets: [
                    {{
                        label: 'API Generation Time (minutes)',
                        data: {json.dumps(api_times)},
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'UI Generation Time (minutes)',
                        data: {json.dumps(ui_times)},
                        backgroundColor: 'rgba(118, 75, 162, 0.8)',
                        borderColor: 'rgba(118, 75, 162, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Generation Time Comparison',
                        font: {{ size: 16 }}
                    }},
                    legend: {{
                        position: 'top'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Minutes'
                        }}
                    }}
                }}
            }}
        }});
        
        // Test iterations chart
        new Chart(document.getElementById('iterationsChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(tool_names)},
                datasets: [
                    {{
                        label: 'Test Iterations',
                        data: {json.dumps(test_iterations)},
                        backgroundColor: 'rgba(255, 152, 0, 0.8)',
                        borderColor: 'rgba(255, 152, 0, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Test Iterations Before All Pass',
                        font: {{ size: 16 }}
                    }},
                    legend: {{
                        position: 'top'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Iterations'
                        }}
                    }}
                }}
            }}
        }});
    </script>
    """
    
    return html


def extract_csv_data(results: List[dict]) -> List[dict]:
    """Extract data for CSV export from result files.
    
    Extracts specified fields: tool_name, tool_version, target_model, api_style,
    pass_rate, duration_minutes, llm_model, submission_timestamp.
    Excludes: test_iterations_count and test_runs details.
    """
    csv_rows = []
    
    for result in results:
        try:
            ri = result['result_data']['run_identity']
            impls = result['result_data']['implementations']
            submission = result['result_data']['submission']
            
            # Extract run_identity fields
            tool_name = ri.get('tool_name', '')
            tool_version = ri.get('tool_version', '')
            target_model = ri.get('target_model', '')
            api_style = ri.get('api_style', '')
            
            # Extract API implementation metrics (if exists)
            pass_rate = None
            duration_minutes = None
            llm_model = None
            
            if 'api' in impls:
                api = impls['api']
                gen = api.get('generation_metrics', {})
                acceptance = api.get('acceptance', {})
                
                duration_minutes = gen.get('duration_minutes')
                llm_model = gen.get('llm_model', '')
                pass_rate = acceptance.get('passrate')
            
            # Extract submission timestamp
            submission_timestamp = submission.get('submitted_timestamp', '')
            
            # Create CSV row
            csv_row = {
                'tool_name': tool_name,
                'tool_version': tool_version,
                'target_model': target_model,
                'api_style': api_style,
                'pass_rate': pass_rate if pass_rate is not None else '',
                'duration_minutes': duration_minutes if duration_minutes is not None else '',
                'llm_model': llm_model if llm_model else '',
                'submission_timestamp': submission_timestamp
            }
            
            csv_rows.append(csv_row)
            
        except (KeyError, TypeError) as e:
            # Skip invalid results, but log warning
            filename = result.get('_filename', 'unknown')
            print(f"Warning: Skipping result file {filename} due to missing required fields: {e}", file=sys.stderr)
            continue
    
    return csv_rows


def write_csv_export(csv_rows: List[dict], output_path: Path) -> None:
    """Write CSV export to file.
    
    Args:
        csv_rows: List of dictionaries with CSV data
        output_path: Path to output CSV file
    """
    # Define CSV column order
    fieldnames = [
        'tool_name',
        'tool_version',
        'target_model',
        'api_style',
        'pass_rate',
        'duration_minutes',
        'llm_model',
        'submission_timestamp'
    ]
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV file
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for row in csv_rows:
                # Format numeric values appropriately
                formatted_row = {}
                for key, value in row.items():
                    if key == 'pass_rate' and value != '' and value is not None:
                        # Format pass_rate as decimal (e.g., 0.957)
                        try:
                            formatted_row[key] = f"{float(value):.3f}"
                        except (ValueError, TypeError):
                            formatted_row[key] = ''
                    elif key == 'duration_minutes' and value != '' and value is not None:
                        # Format duration_minutes with appropriate precision
                        try:
                            formatted_row[key] = f"{float(value):.2f}"
                        except (ValueError, TypeError):
                            formatted_row[key] = ''
                    else:
                        # Keep other values as-is (strings, empty strings)
                        formatted_row[key] = value if value is not None else ''
                
                writer.writerow(formatted_row)
        
        print(f"✓ Generated CSV export: {output_path}")
        
    except IOError as e:
        print(f"Error writing CSV file {output_path}: {e}", file=sys.stderr)
        raise


def find_result_files(input_dir: Path) -> List[Path]:
    """Find all result JSON files in input directory.
    
    Handles both flat directory structure and time-partitioned structure (submissions/YYYY/MM/).
    
    Args:
        input_dir: Root input directory
        
    Returns:
        List of Path objects to JSON files
    """
    result_files = []
    
    if not input_dir.exists():
        return result_files
    
    # First, try flat structure: look for *.json files directly in input_dir
    flat_files = list(input_dir.glob('*.json'))
    if flat_files:
        result_files.extend(flat_files)
    
    # Also check for time-partitioned structure: submissions/YYYY/MM/*.json
    # Check if input_dir contains year directories (numeric)
    for year_dir in input_dir.iterdir():
        if year_dir.is_dir() and year_dir.name.isdigit():
            # This might be a year directory (YYYY)
            for month_dir in year_dir.iterdir():
                if month_dir.is_dir() and month_dir.name.isdigit():
                    # This might be a month directory (MM)
                    month_files = list(month_dir.glob('*.json'))
                    result_files.extend(month_files)
    
    return result_files


def extract_leaderboard_data(results: List[dict]) -> List[dict]:
    """Extract data for leaderboard from result files.
    
    Extracts key fields needed for leaderboard:
    - Tool identification: tool_name, tool_version, run_id
    - Configuration: target_model, api_style, run_number
    - Quality metric: pass_rate
    - Speed metric: duration_minutes
    - Additional context: llm_model, submitted_timestamp, submitted_by
    """
    leaderboard_entries = []
    
    for result in results:
        try:
            ri = result['result_data']['run_identity']
            impls = result['result_data']['implementations']
            submission = result['result_data']['submission']
            
            # Extract tool identification
            tool_name = ri.get('tool_name', '')
            tool_version = ri.get('tool_version', '')
            run_id = ri.get('run_id', '')
            
            # Extract configuration
            target_model = ri.get('target_model', '')
            api_style = ri.get('api_style', '')
            run_number = ri.get('run_number', None)
            
            # Extract API implementation metrics (required for leaderboard)
            if 'api' not in impls:
                # Skip results without API implementation
                continue
            
            api = impls['api']
            gen = api.get('generation_metrics', {})
            acceptance = api.get('acceptance', {})
            
            pass_rate = acceptance.get('passrate')
            duration_minutes = gen.get('duration_minutes')
            llm_model = gen.get('llm_model', '')
            
            # Skip entries with missing critical metrics
            if pass_rate is None or duration_minutes is None:
                filename = result.get('_filename', 'unknown')
                print(f"Warning: Skipping result file {filename} - missing pass_rate or duration_minutes", file=sys.stderr)
                continue
            
            # Extract submission context
            submitted_timestamp = submission.get('submitted_timestamp', '')
            submitted_by = submission.get('submitted_by', '')
            
            # Create leaderboard entry
            entry = {
                'tool_name': tool_name,
                'tool_version': tool_version,
                'run_id': run_id,
                'target_model': target_model,
                'api_style': api_style,
                'run_number': run_number,
                'pass_rate': pass_rate,
                'duration_minutes': duration_minutes,
                'llm_model': llm_model,
                'submitted_timestamp': submitted_timestamp,
                'submitted_by': submitted_by
            }
            
            leaderboard_entries.append(entry)
            
        except (KeyError, TypeError) as e:
            # Skip invalid results, but log warning
            filename = result.get('_filename', 'unknown')
            print(f"Warning: Skipping result file {filename} due to missing required fields: {e}", file=sys.stderr)
            continue
    
    return leaderboard_entries


def calculate_composite_score(pass_rate: float, duration_minutes: float) -> float:
    """Calculate composite "fast+quality" score.
    
    Uses formula: pass_rate / duration_minutes (higher is better)
    This rewards both high quality (pass_rate) and speed (low duration).
    
    Args:
        pass_rate: Quality metric (0.0 to 1.0, higher is better)
        duration_minutes: Speed metric (lower is better)
    
    Returns:
        Composite score (higher is better)
    """
    # Handle edge cases
    if duration_minutes <= 0:
        # If duration is zero or negative, return 0 (invalid)
        return 0.0
    
    if pass_rate < 0:
        # If pass_rate is negative, return 0 (invalid)
        return 0.0
    
    # Calculate composite: pass_rate / duration_minutes
    # Higher pass_rate and lower duration both increase the score
    composite = pass_rate / duration_minutes
    
    return composite


def generate_sorted_views(entries: List[dict]) -> dict:
    """Generate multiple sorted leaderboard views.
    
    Args:
        entries: List of leaderboard entries with metrics
    
    Returns:
        Dictionary with sorted views: by_quality, by_speed, by_composite
    """
    # Calculate composite scores for all entries
    entries_with_composite = []
    for entry in entries:
        composite_score = calculate_composite_score(
            entry['pass_rate'],
            entry['duration_minutes']
        )
        entry_copy = entry.copy()
        entry_copy['composite_score'] = composite_score
        entries_with_composite.append(entry_copy)
    
    # Sort by quality (pass_rate, descending)
    by_quality = sorted(
        entries_with_composite,
        key=lambda x: x['pass_rate'],
        reverse=True
    )
    
    # Sort by speed (duration_minutes, ascending)
    by_speed = sorted(
        entries_with_composite,
        key=lambda x: x['duration_minutes']
    )
    
    # Sort by composite score (descending)
    by_composite = sorted(
        entries_with_composite,
        key=lambda x: x['composite_score'],
        reverse=True
    )
    
    return {
        'by_quality': by_quality,
        'by_speed': by_speed,
        'by_composite': by_composite
    }


def build_leaderboard_json(entries: List[dict], sorted_views: dict) -> dict:
    """Build leaderboard JSON structure with metadata and sorted views.
    
    Args:
        entries: List of all leaderboard entries
        sorted_views: Dictionary with sorted views
    
    Returns:
        Complete leaderboard JSON structure
    """
    leaderboard = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_results': len(entries),
            'sort_options': {
                'by_quality': {
                    'field': 'pass_rate',
                    'direction': 'descending',
                    'description': 'Sorted by acceptance test pass rate (quality)'
                },
                'by_speed': {
                    'field': 'duration_minutes',
                    'direction': 'ascending',
                    'description': 'Sorted by generation duration (speed)'
                },
                'by_composite': {
                    'field': 'composite_score',
                    'direction': 'descending',
                    'description': 'Sorted by composite fast+quality score (pass_rate / duration_minutes)'
                }
            }
        },
        'results': entries,
        'sorted_views': sorted_views
    }
    
    return leaderboard


def write_leaderboard_json(leaderboard: dict, output_path: Path) -> None:
    """Write leaderboard JSON to file.
    
    Args:
        leaderboard: Leaderboard data structure
        output_path: Path to output JSON file
    """
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file with pretty-printing
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Generated leaderboard: {output_path}")
        
    except IOError as e:
        print(f"Error writing leaderboard file {output_path}: {e}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description='Benchmark results aggregation (v2.0 and v3.0 schema support)')
    parser.add_argument('--input-dir', default='results/submitted', help='Input directory')
    parser.add_argument('--output-dir', default='results/compiled', help='Output directory')
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    input_dir = repo_root / args.input_dir
    output_dir = repo_root / args.output_dir
    
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all result files (handles both flat and time-partitioned structure)
    result_files = find_result_files(input_dir)
    
    if not result_files:
        print(f"No result files found in {input_dir}", file=sys.stderr)
        sys.exit(0)
    
    print(f"Found {len(result_files)} result file(s)")
    
    # Parse results
    results = []
    for result_file in result_files:
        result = parse_result_file(result_file)
        if result:
            results.append(result)
    
    if not results:
        print("No valid results to aggregate", file=sys.stderr)
        sys.exit(0)
    
    # Group results by (spec_version, model, api_type)
    grouped = defaultdict(list)
    for result in results:
        ri = result['result_data']['run_identity']
        key = (ri['spec_reference'], ri['target_model'], ri['api_style'])
        grouped[key].append(result)
    
    # Generate HTML reports
    for group_key, group_results in grouped.items():
        generate_html_report(group_key, group_results, output_dir)
    
    print(f"\n✓ Enhanced reports generated in: {output_dir}")
    print("  Open the .html files in your browser for interactive visualizations")
    
    # Generate CSV export
    csv_rows = extract_csv_data(results)
    if csv_rows:
        # Write CSV to aggregates/results.csv
        repo_root = script_dir.parent
        aggregates_dir = repo_root / 'aggregates'
        csv_output_path = aggregates_dir / 'results.csv'
        write_csv_export(csv_rows, csv_output_path)
    else:
        print("No data available for CSV export", file=sys.stderr)
    
    # Generate leaderboard
    leaderboard_entries = extract_leaderboard_data(results)
    if leaderboard_entries:
        sorted_views = generate_sorted_views(leaderboard_entries)
        leaderboard_json = build_leaderboard_json(leaderboard_entries, sorted_views)
        
        # Write leaderboard to aggregates/leaderboard.json
        repo_root = script_dir.parent
        aggregates_dir = repo_root / 'aggregates'
        leaderboard_output_path = aggregates_dir / 'leaderboard.json'
        write_leaderboard_json(leaderboard_json, leaderboard_output_path)
    else:
        print("No data available for leaderboard generation", file=sys.stderr)


if __name__ == '__main__':
    main()

