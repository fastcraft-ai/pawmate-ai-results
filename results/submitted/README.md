# Submitted Results

This directory contains submitted benchmark result files (`.json` format).

## Usage

After generating a result file using `generate_result_file.sh` in the `pawmate-ai-challenge` repository, copy it to this directory:

```bash
# From pawmate-ai-challenge repo
cp your-result-file.json /path/to/pawmate-ai-results/results/submitted/
```

## File Naming

Result files should follow the naming convention:
```
{tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json
```

Example: `cursor_modelA_REST_run1_20241218T1430.json`

## Processing

Once files are in this directory, run the aggregation script to generate comparison reports:

```bash
python3 scripts/aggregate_results.py --input-dir results/submitted --output-dir results/compiled
```

