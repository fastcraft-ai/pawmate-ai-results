#!/usr/bin/env python3
"""
generate_dashboard.py — Generate static HTML dashboard for benchmark results

Usage:
    python3 scripts/generate_dashboard.py [--input-dir <dir>] [--output-file <file>]

Options:
    --input-dir <dir>      Directory containing result files (default: results/submitted/)
    --output-file <file>   Output HTML file (default: results/compiled/dashboard.html)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import json


def parse_result_file(file_path: Path) -> Optional[dict]:
    """Parse a result file and return structured data."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        data['_filename'] = file_path.name
        return data
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None


def generate_dashboard(results: List[dict], output_path: Path) -> None:
    """Generate HTML dashboard."""
    
    # Group by tool
    tools = defaultdict(lambda: {'run1': None, 'run2': None, 'info': {}})
    
    for result in results:
        ri = result['result_data']['run_identity']
        tool_key = f"{ri['tool_name']} {ri.get('tool_version', '')}".strip()
        run_num = ri['run_number']
        
        if run_num == 1:
            tools[tool_key]['run1'] = result
        elif run_num == 2:
            tools[tool_key]['run2'] = result
        
        # Store tool info
        if not tools[tool_key]['info']:
            tools[tool_key]['info'] = {
                'name': ri['tool_name'],
                'version': ri.get('tool_version', ''),
                'model': ri['target_model'],
                'api_style': ri['api_style'],
                'spec_ref': ri['spec_reference']
            }
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PawMate Benchmark Results Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .score {{
            font-weight: 600;
        }}
        
        .score-high {{
            color: #27ae60;
        }}
        
        .score-medium {{
            color: #f39c12;
        }}
        
        .score-low {{
            color: #e74c3c;
        }}
        
        .score-unknown {{
            color: #95a5a6;
            font-style: italic;
        }}
        
        .dimension {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin: 2px;
        }}
        
        .dim-C {{ background: #3498db; color: white; }}
        .dim-R {{ background: #9b59b6; color: white; }}
        .dim-D {{ background: #1abc9c; color: white; }}
        .dim-E {{ background: #e67e22; color: white; }}
        .dim-S {{ background: #f1c40f; color: #333; }}
        .dim-K {{ background: #34495e; color: white; }}
        
        .controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        label {{
            font-weight: 500;
            color: #555;
        }}
        
        select, input {{
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>PawMate Benchmark Results Dashboard</h1>
        <p class="subtitle">AI Tool Comparison Results</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(tools)}</div>
                <div class="stat-label">Tools Tested</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(results)}</div>
                <div class="stat-label">Total Runs</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label for="filter-model">Model:</label>
                <select id="filter-model">
                    <option value="">All</option>
                    <option value="A">Model A</option>
                    <option value="B">Model B</option>
                </select>
            </div>
            <div class="control-group">
                <label for="filter-api">API Style:</label>
                <select id="filter-api">
                    <option value="">All</option>
                    <option value="REST">REST</option>
                    <option value="GraphQL">GraphQL</option>
                </select>
            </div>
            <div class="control-group">
                <label for="sort-by">Sort by:</label>
                <select id="sort-by">
                    <option value="overall">Overall Score</option>
                    <option value="correctness">Correctness (C)</option>
                    <option value="speed">Speed (S)</option>
                    <option value="effort">Effort (E)</option>
                </select>
            </div>
        </div>
        
        <table id="results-table">
            <thead>
                <tr>
                    <th>Tool</th>
                    <th>Version</th>
                    <th>Model</th>
                    <th>API</th>
                    <th>TTFR (min)</th>
                    <th>TTFC (min)</th>
                    <th><span class="dimension dim-C">C</span></th>
                    <th><span class="dimension dim-R">R</span></th>
                    <th><span class="dimension dim-D">D</span></th>
                    <th><span class="dimension dim-E">E</span></th>
                    <th><span class="dimension dim-S">S</span></th>
                    <th><span class="dimension dim-K">K</span></th>
                    <th>Overall</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Generate table rows
    for tool_key in sorted(tools.keys()):
        tool_data = tools[tool_key]
        info = tool_data['info']
        run1 = tool_data['run1']
        run2 = tool_data['run2']
        
        # Get scores (prefer run1, fallback to run2)
        run = run1 or run2
        if not run:
            continue
        
        scores = run['result_data']['scores']
        metrics = run['result_data']['metrics']
        
        # Format scores
        def format_score(value):
            if value == "Unknown" or value is None:
                return '<span class="score-unknown">Unknown</span>'
            try:
                num = float(value)
                if num >= 80:
                    return f'<span class="score score-high">{num:.1f}</span>'
                elif num >= 60:
                    return f'<span class="score score-medium">{num:.1f}</span>'
                else:
                    return f'<span class="score score-low">{num:.1f}</span>'
            except:
                return '<span class="score-unknown">Unknown</span>'
        
        ttfr = metrics['ttfr'].get('minutes', 'Unknown')
        ttfc = metrics['ttfc'].get('minutes', 'Unknown')
        
        html += f"""
                <tr data-model="{info['model']}" data-api="{info['api_style']}">
                    <td>{info['name']}</td>
                    <td>{info['version']}</td>
                    <td>{info['model']}</td>
                    <td>{info['api_style']}</td>
                    <td>{ttfr if ttfr != 'Unknown' else '—'}</td>
                    <td>{ttfc if ttfc != 'Unknown' else '—'}</td>
                    <td>{format_score(scores.get('correctness_C'))}</td>
                    <td>{format_score(scores.get('reproducibility_R'))}</td>
                    <td>{format_score(scores.get('determinism_D'))}</td>
                    <td>{format_score(scores.get('effort_E'))}</td>
                    <td>{format_score(scores.get('speed_S'))}</td>
                    <td>{format_score(scores.get('contract_docs_K'))}</td>
                    <td>{format_score(scores.get('overall_score'))}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <script>
        const table = document.getElementById('results-table');
        const filterModel = document.getElementById('filter-model');
        const filterApi = document.getElementById('filter-api');
        const sortBy = document.getElementById('sort-by');
        
        function filterAndSort() {
            const modelFilter = filterModel.value;
            const apiFilter = filterApi.value;
            const sortValue = sortBy.value;
            
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            
            // Filter
            rows.forEach(row => {
                const model = row.getAttribute('data-model');
                const api = row.getAttribute('data-api');
                
                let show = true;
                if (modelFilter && model !== modelFilter) show = false;
                if (apiFilter && api !== apiFilter) show = false;
                
                row.style.display = show ? '' : 'none';
            });
            
            // Sort
            const visibleRows = rows.filter(r => r.style.display !== 'none');
            visibleRows.sort((a, b) => {
                const getScore = (row, type) => {
                    const cells = row.querySelectorAll('td');
                    if (type === 'overall') {
                        const text = cells[12].textContent;
                        return text === 'Unknown' ? -1 : parseFloat(text) || -1;
                    } else if (type === 'correctness') {
                        const text = cells[6].textContent;
                        return text === 'Unknown' ? -1 : parseFloat(text) || -1;
                    } else if (type === 'speed') {
                        const text = cells[10].textContent;
                        return text === 'Unknown' ? -1 : parseFloat(text) || -1;
                    } else if (type === 'effort') {
                        const text = cells[9].textContent;
                        return text === 'Unknown' ? 101 : parseFloat(text) || 101;
                    }
                    return 0;
                };
                
                const aScore = getScore(a, sortValue);
                const bScore = getScore(b, sortValue);
                
                if (sortValue === 'effort') {
                    return aScore - bScore; // Lower is better
                } else {
                    return bScore - aScore; // Higher is better
                }
            });
            
            // Reorder
            const tbody = table.querySelector('tbody');
            visibleRows.forEach(row => tbody.appendChild(row));
        }
        
        filterModel.addEventListener('change', filterAndSort);
        filterApi.addEventListener('change', filterAndSort);
        sortBy.addEventListener('change', filterAndSort);
    </script>
</body>
</html>
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✓ Generated dashboard: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate HTML dashboard for benchmark results')
    parser.add_argument('--input-dir', default='results/submitted', help='Input directory')
    parser.add_argument('--output-file', default='results/compiled/dashboard.html', help='Output HTML file')
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    input_dir = repo_root / args.input_dir
    output_file = repo_root / args.output_file
    
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Find all result files
    result_files = list(input_dir.glob('*.json'))
    
    if not result_files:
        print(f"No result files found in {input_dir}", file=sys.stderr)
        sys.exit(0)
    
    # Parse results
    results = []
    for result_file in result_files:
        result = parse_result_file(result_file)
        if result:
            results.append(result)
    
    if not results:
        print("No valid results to display", file=sys.stderr)
        sys.exit(0)
    
    # Generate dashboard
    generate_dashboard(results, output_file)


if __name__ == '__main__':
    main()

