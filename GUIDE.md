# GUIDE.md — Polarize Agent Interface

You are an AI coding agent. This tool helps you convert compute-heavy
pandas code to Polars. You handle the conversion. This tool handles
discovery and validation.

## Prerequisites

- Python 3.10+
- `pip install polarize`

## Workflow

### Step 1: Discover Compute-Heavy Operations

```bash
polarize discover <path> --threshold high
```

This returns a JSON report ranking pandas operations by compute weight.
Convert **high-weight operations first** — they have the most performance
impact.

Output:
```json
{
  "file": "pipeline.py",
  "operations": [
    {
      "line": 42,
      "code": "df.groupby('user_id').agg({'amount': 'sum'})",
      "operation": "groupby+agg",
      "compute_weight": "high"
    }
  ],
  "data_sources": [
    {"method": "read_csv", "line": 5, "code": "pd.read_csv('data.csv')"}
  ],
  "summary": {
    "total_ops": 14,
    "compute_heavy_ops": 4,
    "suggested_conversion_order": [42, 87, 23, 91]
  }
}
```

Options:
- `--threshold high|medium|low` — minimum weight to report (default: medium)
- `--recursive` — scan directories
- `--format json|text` — output format (default: json)

### Step 2: Convert (You Do This)

Convert the identified operations to Polars. Follow these rules:

1. Convert in the `suggested_conversion_order` (highest impact first)
2. Preserve all non-pandas code unchanged
3. Add `import polars as pl` if not present
4. Remove `import pandas as pd` only if ALL pandas usage is converted
5. Keep the same variable names and function signatures

### Step 3: Validate

```bash
polarize validate --original <file> --converted <file> -- [script args...]
```

Everything after `--` is forwarded to both scripts as arguments. The
scripts handle their own IO — local files, S3 paths, DB connections,
multiple inputs, anything.

Output:
```json
{
  "status": "pass",
  "checks": [
    {"check": "syntax", "passed": true, "message": "Valid Python syntax"},
    {"check": "imports", "passed": true, "message": "Polars import found"},
    {"check": "equivalence", "passed": true, "message": "Outputs match"}
  ]
}
```

Exit codes: `0` = pass, `1` = fail, `2` = parse error.

### Step 4: Profile

```bash
polarize profile --original <file> --converted <file> [--runs 5] -- [script args...]
```

Output:
```json
{
  "original_time_s": 2.345,
  "converted_time_s": 0.412,
  "original_peak_memory_mb": 256.3,
  "converted_peak_memory_mb": 89.1,
  "time_improvement_pct": 82.4,
  "memory_improvement_pct": 65.2,
  "runs": 5
}
```

## Incremental Conversion Loop

Follow this loop for best results:

1. `polarize discover script.py --threshold high`
2. Convert high-weight operations
3. `polarize validate --original script.py --converted script_polars.py -- [args]`
4. `polarize profile --original script.py --converted script_polars.py -- [args]`
5. Report results to user
6. **Only if user wants more improvement:**
   - `polarize discover script.py --threshold medium`
   - Repeat from step 2

## Reference: Supported Operations

```bash
polarize ops [--threshold high|medium|low]
```

Lists all pandas operations polarize can detect, with their compute weights.

## Python API

```python
from polarize import discover, validate, profile

report = discover("script.py", threshold="high")
result = validate(original="script.py", converted="out.py", script_args=["s3://bucket/data/"])
bench = profile(original="script.py", converted="out.py", runs=5, script_args=["input.parquet"])
```
