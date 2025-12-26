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
│   ├── aggregate_results.py          # Generate HTML comparison reports from result files
│   ├── generate_dashboard.py          # Generate dashboard visualizations
│   ├── validate_result.sh            # Validate result files against schema
│   └── process_emailed_result.sh     # Process result files received via email
├── schemas/
│   └── result-schema-v2.0-proposed.json  # JSON schema for result files
├── results/
│   ├── submitted/                    # Result files submitted by developers
│   └── compiled/                     # Generated comparison reports
└── docs/
    └── Comparison_Report_Template.md      # Template for manual comparison reports
```

## Usage

### Processing Emailed Results (For Maintainers)

External developers submit results via email. To process received result files:

```bash
# Quick process: copy to submitted/ and validate
./scripts/process_emailed_result.sh ~/Downloads/result_file.json

# Copy, validate, and run aggregation
./scripts/process_emailed_result.sh ~/Downloads/result_file.json --aggregate

# Copy only (no validation or aggregation)
./scripts/process_emailed_result.sh ~/Downloads/result_file.json --copy-only
```

The script will:
1. Copy the result file to `results/submitted/`
2. Validate the file (optional)
3. Run aggregation to update comparison reports (optional)

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

Result files are generated in the `pawmate-ai-challenge` repository using `scripts/generate_result_file.sh`.

### Submission Workflow

**For external developers** (recommended):
1. Generate result file in `pawmate-ai-challenge`
2. Run `./scripts/submit_result.sh` in `pawmate-ai-challenge`
3. Email is sent with result file attachment
4. Maintainer receives email and processes result using `./scripts/process_emailed_result.sh`

**For maintainers with repo access**:
1. Generate result file in `pawmate-ai-challenge`
2. Copy file to `results/submitted/` in this repo
3. Commit and push directly (or create PR)

### Result Processing

Once result files are in `results/submitted/`:
1. Validate using `./scripts/validate_result.sh`
2. Aggregate using `python3 scripts/aggregate_results.py`
3. Compiled reports are generated in `results/compiled/`

## Schema Version

The schema version is tracked in each result file. The aggregation scripts only support:
- **v2.0**: Current schema with separate API/UI implementations, test run tracking, and LLM usage

## Submitting Results

### For External Developers

Use the submission script in the `pawmate-ai-challenge` repository:

```bash
# In pawmate-ai-challenge repo
./scripts/submit_result.sh your-result-file.json
```

See the [Submitting Results Guide](https://github.com/rsdickerson/pawmate-ai-challenge/blob/main/docs/Submitting_Results.md) in the challenge repository for detailed instructions.

### For Maintainers

When adding result files directly to this repository:
1. Ensure the file validates against the schema
2. Follow the naming convention: `{tool-slug}_{model}_{api-type}_{run-number}_{timestamp}.json`
3. Include complete metrics (use "Unknown" if evidence is missing, per evidence-first rule)
4. Place files in `results/submitted/`
5. Run aggregation to update comparison reports

