# Compiled Reports

This directory contains generated comparison reports and dashboards.

## Contents

After running the aggregation scripts, this directory will contain:
- HTML comparison reports (one per spec/model/API-style combination)
- Dashboard visualizations (if generated)

## Generating Reports

To generate reports from submitted result files:

```bash
# Generate HTML comparison reports
python3 scripts/aggregate_results.py --input-dir results/submitted --output-dir results/compiled

# Generate dashboard (optional)
python3 scripts/generate_dashboard.py --input-dir results/submitted --output-file results/compiled/dashboard.html
```

## Viewing Reports

Open the generated `.html` files in your web browser to view interactive comparison reports with charts and metrics.

