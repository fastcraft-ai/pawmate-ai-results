#!/usr/bin/env python3
"""
aggregate_results.py — Benchmark results aggregation with v2.0 schema support

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
    
    # Only support v2.0 schema
    if 'implementations' in data.get('result_data', {}):
        return '2.0'
    
    # If schema_version is explicitly set to something else, return it (for error reporting)
    if schema_version != '2.0':
        return schema_version
    
    # Default to 2.0
    return '2.0'


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


def extract_metrics_v2(result: dict) -> dict:
    """Extract metrics from v2.0 schema (separate API/UI)."""
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
        
        if schema_ver != '2.0':
            print(f"Warning: Skipping result with unsupported schema version {schema_ver}: {run1.get('_filename', 'unknown')}", file=sys.stderr)
            continue
        
        metrics = extract_metrics_v2(run1)
        
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


def main():
    parser = argparse.ArgumentParser(description='Benchmark results aggregation (v2.0 schema)')
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
    
    # Find all result files
    result_files = list(input_dir.glob('*.json'))
    
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


if __name__ == '__main__':
    main()

