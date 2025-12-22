# Comparison Report Template — Copy/Paste

> **Operator instructions:** Use this template to compare multiple tools for the same **frozen spec reference** and **target model**. Fill all bracketed fields. Do not infer missing values; record **Unknown** if evidence is missing.

---

### 0) Report Header
- **report_id**: [e.g., SpecCommit-abc123-ModelA-Comparison]
- **spec_reference**: [commit/tag/hash]
- **target_model**: [A|B]
- **evaluation_window**: [date/time range]
- **tools_compared**: [Tool A, Tool B, ...]
- **notes**: [any constraints or anomalies]

---

### 1) Executive Summary (1–6 bullets)
- **Key takeaway 1**: [...]
- **Key takeaway 2**: [...]
- **Most important failure mode(s)**: [...]
- **Most important strengths**: [...]
- **Reproducibility highlight** (Run 1 vs Run 2): [...]
- **Test iterations highlight**: [average or range of test iterations across tools]

---

### 2) Benchmark Setup (Inputs + Consistency)
- **frozen_inputs_used**:
  - `docs/Master_Functional_Spec.md`
  - `docs/API_Contract.md`
  - `docs/Seed_Data.md`
  - `docs/Image_Handling.md`
  - `docs/Acceptance_Criteria.md`
  - `docs/Benchmarking_Method.md`
- **operator_notes**: [any deviations from the standard procedure; if none, "None"]

---

### 3) Comparison Table (Required)
> One row per tool. Values typically reflect the average across Run 1 and Run 2 unless stated. Use **Unknown** where applicable.

#### Identification + Inputs
- tool_name
- tool_version
- target_model
- spec_reference
- run_environment

#### Timing
- api_time_run1_minutes
- api_time_run2_minutes
- ui_time_run1_minutes (if applicable)
- ui_time_run2_minutes (if applicable)

#### Test Iterations
- test_iterations_run1 (number of times tests were run before all passed)
- test_iterations_run2

#### Acceptance Results
- acceptance_passrate_run1
- acceptance_passrate_run2

#### Evidence pointers (required for auditability)
- run1_artifacts_path
- run2_artifacts_path

> Table entry format is operator-choice (Markdown table, CSV, spreadsheet), but the **column names above must be preserved**.

---

### 4) Timing and Test Iterations Summary (Per tool)
For each tool, provide a short summary of timing metrics and test iterations.

#### [Tool Name]
- **API Time (Run 1)**: [minutes]
- **API Time (Run 2)**: [minutes]
- **UI Time (Run 1)**: [minutes|N/A]
- **UI Time (Run 2)**: [minutes|N/A]
- **Test Iterations (Run 1)**: [count]
- **Test Iterations (Run 2)**: [count]
- **Acceptance Pass Rate (Run 1)**: [0.0-1.0]
- **Acceptance Pass Rate (Run 2)**: [0.0-1.0]
- **Evidence pointers**:
  - Run 1: [...]
  - Run 2: [...]

---

### 5) Notable Failures / Defects (Cross-tool)
List the most meaningful correctness failures and which tools were impacted.
- **Failure**: [short description]
  - **Impacted tools**: [...]
  - **Evidence**: [...]
  - **Notes**: [...]

---

### 6) Overreach Notes (Cross-tool)
Summarize any `NOR-*` violations or features beyond `REQ-*`.
- **Incident**: [NOR-#### or "no supporting REQ-*"]
  - **Tool(s)**: [...]
  - **Evidence**: [...]
  - **Impact**: [...]

---

### 7) Reproducibility (Run 1 vs Run 2) Diffs (Per tool)
For each tool, summarize differences between runs.

#### [Tool Name]
- **Rating**: [None|Minor|Major|Unknown]
- **Differences**:
  - Timing: [...]
  - Acceptance: [...]
  - Test Iterations: [...]
  - Artifacts: [...]
- **Evidence**: [...]

---

### 8) Evidence Index (Optional but recommended)
Provide a quick index of the run folders and key files for auditability.
- [Tool Name] Run 1: [path]
- [Tool Name] Run 2: [path]

