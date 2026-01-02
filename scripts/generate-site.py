#!/usr/bin/env python3
"""
generate-site.py — Generate static HTML site with embedded leaderboard data

Reads the HTML template from site/index.html, loads leaderboard JSON data,
embeds the data directly in the HTML, and generates a final static HTML file
ready for GitHub Pages deployment.

Usage:
    python3 scripts/generate-site.py [--template <path>] [--output <path>] [--leaderboard <path>]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def load_html_template(template_path: Path) -> str:
    """Load HTML template file.
    
    Args:
        template_path: Path to HTML template file
    
    Returns:
        HTML template content as string
    
    Raises:
        FileNotFoundError: If template file doesn't exist
        IOError: If file cannot be read
    """
    if not template_path.exists():
        raise FileNotFoundError(f"HTML template not found: {template_path}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Error reading template file {template_path}: {e}")


def load_leaderboard_json(leaderboard_path: Path) -> dict:
    """Load and validate leaderboard JSON data.
    
    Args:
        leaderboard_path: Path to leaderboard.json file
    
    Returns:
        Leaderboard data as dictionary
    
    Raises:
        FileNotFoundError: If leaderboard file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If JSON structure is invalid
    """
    if not leaderboard_path.exists():
        raise FileNotFoundError(
            f"Leaderboard JSON not found: {leaderboard_path}\n"
            f"Run aggregate_results.py first to generate leaderboard.json"
        )
    
    try:
        with open(leaderboard_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {leaderboard_path}: {e}", e.doc, e.pos)
    
    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(f"Leaderboard JSON must be an object, got {type(data)}")
    
    if 'metadata' not in data:
        raise ValueError("Leaderboard JSON missing 'metadata' field")
    
    if 'results' not in data:
        raise ValueError("Leaderboard JSON missing 'results' field")
    
    if 'sorted_views' not in data:
        raise ValueError("Leaderboard JSON missing 'sorted_views' field")
    
    sorted_views = data['sorted_views']
    if not isinstance(sorted_views, dict):
        raise ValueError("'sorted_views' must be an object")
    
    required_views = ['by_quality', 'by_speed', 'by_composite']
    for view in required_views:
        if view not in sorted_views:
            raise ValueError(f"'sorted_views' missing required view: {view}")
    
    return data


def embed_leaderboard_data(html_content: str, leaderboard_data: dict) -> str:
    """Embed leaderboard JSON data directly in HTML as JavaScript variable.
    
    Replaces the fetch API call with embedded data assignment.
    
    Args:
        html_content: Original HTML template content
        leaderboard_data: Leaderboard data dictionary
    
    Returns:
        HTML content with embedded leaderboard data
    """
    # Convert leaderboard data to JSON string (safe for embedding in JavaScript)
    leaderboard_json = json.dumps(leaderboard_data, ensure_ascii=False, indent=2)
    
    # Find where to insert the embedded data constant
    # Look for the comment before loadLeaderboardData function
    insertion_marker = '// Load leaderboard JSON data'
    if insertion_marker not in html_content:
        raise ValueError("Could not find insertion point for embedded data in HTML template")
    
    insertion_idx = html_content.find(insertion_marker)
    
    # Find the start of the loadLeaderboardData function
    function_start = 'async function loadLeaderboardData() {'
    if function_start not in html_content:
        raise ValueError("Could not find loadLeaderboardData function in HTML template")
    
    start_idx = html_content.find(function_start)
    if start_idx == -1 or start_idx < insertion_idx:
        raise ValueError("Could not find loadLeaderboardData function in HTML template")
    
    # Find the matching closing brace for the function (handle nested braces)
    brace_count = 0
    in_function = False
    end_idx = start_idx
    
    for i in range(start_idx, len(html_content)):
        char = html_content[i]
        if char == '{':
            if not in_function:
                in_function = True
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if in_function and brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx == start_idx or not in_function:
        raise ValueError("Could not find end of loadLeaderboardData function in HTML template")
    
    # Create the embedded data constant
    embedded_data_constant = f"""        // Embedded leaderboard data (generated by generate-site.py)
        const embeddedLeaderboardData = {leaderboard_json};
        
"""
    
    # Create the replacement function (without the embedded data constant, it's added separately)
    replacement_function = """        // Load leaderboard data from embedded variable
        async function loadLeaderboardData() {
            try {
                // Use embedded data instead of fetch
                const data = embeddedLeaderboardData;
                
                // Validate structure
                if (!data.metadata || !data.results || !data.sorted_views) {
                    throw new Error('Invalid leaderboard JSON structure: missing required fields');
                }
                
                if (!data.sorted_views.by_quality || !data.sorted_views.by_speed || !data.sorted_views.by_composite) {
                    throw new Error('Invalid leaderboard JSON structure: missing sorted_views');
                }
                
                leaderboardData = data;
                console.log('Leaderboard data loaded successfully:', data.metadata);
                
                // Initialize charts with data
                initializeCharts();
                updateCharts(currentSort);
                
            } catch (error) {
                console.error('Error loading leaderboard data:', error);
                displayError(error.message);
            }
        }
"""
    
    # Replace: insert embedded data constant, then replace the function
    new_html = (
        html_content[:insertion_idx] +
        embedded_data_constant +
        html_content[insertion_idx:start_idx] +
        replacement_function +
        html_content[end_idx:]
    )
    
    return new_html


def write_static_html(html_content: str, output_path: Path) -> None:
    """Write final static HTML file.
    
    Args:
        html_content: Final HTML content with embedded data
        output_path: Path to output HTML file
    
    Raises:
        IOError: If file cannot be written
    """
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Generated static HTML site: {output_path}")
        
    except IOError as e:
        raise IOError(f"Error writing HTML file {output_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate static HTML site with embedded leaderboard data'
    )
    parser.add_argument(
        '--template',
        default='site/index.html',
        help='Path to HTML template file (relative to repo root)'
    )
    parser.add_argument(
        '--output',
        default='site/index.html',
        help='Path to output HTML file (relative to repo root)'
    )
    parser.add_argument(
        '--leaderboard',
        default='aggregates/leaderboard.json',
        help='Path to leaderboard JSON file (relative to repo root)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script directory's parent (repo root)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    template_path = repo_root / args.template
    output_path = repo_root / args.output
    leaderboard_path = repo_root / args.leaderboard
    
    try:
        # Step 1: Load HTML template
        print(f"Reading HTML template: {template_path}")
        html_content = load_html_template(template_path)
        
        # Step 2: Load leaderboard JSON data
        print(f"Loading leaderboard data: {leaderboard_path}")
        leaderboard_data = load_leaderboard_json(leaderboard_path)
        print(f"  Loaded {leaderboard_data['metadata']['total_results']} results")
        
        # Step 3: Embed leaderboard data in HTML
        print("Embedding leaderboard data in HTML...")
        html_with_data = embed_leaderboard_data(html_content, leaderboard_data)
        
        # Step 4: Write final static HTML file
        print(f"Writing static HTML site: {output_path}")
        write_static_html(html_with_data, output_path)
        
        print(f"\n✓ Static HTML site generated successfully!")
        print(f"  Output: {output_path}")
        print(f"  Ready for GitHub Pages deployment")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, json.JSONDecodeError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

