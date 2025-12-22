# PawMate AI Results Repository

This repository contains tools and scripts for processing, aggregating, and analyzing benchmark results from the PawMate AI Challenge.

## Purpose

This repository is separate from the main `pawmate-ai-challenge` repository to maintain a clear separation of concerns:

- **pawmate-ai-challenge**: Contains the benchmark specification, prompts, and tools for generating result files during benchmark runs
- **pawmate-ai-results**: Contains tools for processing submitted result files, generating comparison reports, and analyzing aggregated data

## Repository Structure

```
pawmate-ai-results/
├── scripts/
│   ├── aggregate_results.py       # Generate HTML comparison reports from result files
│   ├── generate_dashboard.py       # Generate dashboard visualizations
│   └── validate_result.sh         # Validate result files against schema
├── schemas/
│   └── result-schema-v2.0-proposed.json  # JSON schema for result files
└── docs/
    └── Comparison_Report_Template.md      # Template for manual comparison reports
```

## Usage

### Aggregating Results

To generate HTML comparison reports from submitted result files:

```bash
python3 scripts/aggregate_results.py --input-dir results/submitted --output-dir results/compiled
```

This will:
- Read all `.json` result files from the input directory
- Group them by spec reference, model, and API style
- Generate HTML comparison reports with charts and tables
- Output reports to the specified output directory

### Validating Result Files

To validate a result file against the schema:

```bash
./scripts/validate_result.sh path/to/result_file.json
```

## Result File Schema

Result files must conform to the schema defined in `schemas/result-schema-v2.0-proposed.json`. The schema defines:

- **Run identity**: Tool name, version, run number, target model, API style
- **API implementation metrics**: Timing, test runs, LLM usage, acceptance results
- **UI implementation metrics**: Timing, build success, LLM usage (if UI was implemented)
- **Submission metadata**: Timestamp, submitter, submission method

## Key Metrics Tracked

The comparison reports focus on **automated, measurable metrics**:

- **Timing**: API generation time, UI generation time (if applicable)
- **Test iterations**: Number of times tests were run before all passed
- **Acceptance pass rate**: Percentage of acceptance criteria passed
- **LLM usage**: Token counts, request counts, estimated costs (if available)
- **Build success**: Whether UI builds and runs without errors (automated check)

**Note**: Subjective scoring metrics (correctness, determinism, effort, overall score) are no longer included in comparison reports as of Phase 2 refinement.

## Integration with Challenge Repository

Result files are generated in the `pawmate-ai-challenge` repository using `scripts/generate_result_file.sh`. Once generated, result files can be:

1. Submitted to this repository (via PR or direct commit)
2. Processed using the aggregation scripts in this repository
3. Included in comparison reports

## Schema Version

The schema version is tracked in each result file. The aggregation scripts only support:
- **v2.0**: Current schema with separate API/UI implementations, test run tracking, and LLM usage

## Contributing

When adding new result files:
1. Ensure the file validates against the schema
2. Follow the naming convention: `{tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json`
3. Include complete metrics (use "Unknown" if evidence is missing, per evidence-first rule)

