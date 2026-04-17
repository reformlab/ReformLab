# Runtime Diagnostics and Troubleshooting

This guide helps operators and developers investigate failed runs and understand runtime mode behavior.

## Overview

ReformLab supports two runtime execution modes:

- **Live Mode** (default): Executes scenarios using the live OpenFisca web runtime
- **Replay Mode** (explicit opt-in): Reuses precomputed output files for faster execution

Each run produces an immutable manifest documenting all parameters, data sources, assumptions, and execution configuration for reproducibility and debugging.

## Runtime Mode Diagnostics

### Live Mode (Default)

Live OpenFisca is the default runtime for web runs. When no `runtime_mode` is specified in a run request, the system automatically uses live execution.

**Verification:**

Check the runtime mode in multiple places:

1. **API Response**: After POST /api/runs, check `runtime_mode` field in the response
2. **Result Details**: GET /api/results/{run_id} returns `runtime_mode` in the metadata
3. **Manifest File**: `manifest.json` contains `runtime_mode: "live"`

```bash
# Check runtime mode via API
curl -H "Authorization: Bearer <token>" \
  https://api.reformlab.com/api/results/<run_id> | jq '.runtime_mode'

# Check manifest file directly
cat ~/.reformlab/results/<run_id>/manifest.json | jq '.runtime_mode'
```

**Expected Value:** `"live"`

**Preflight Warnings:**

- **MockAdapter environments**: Expect `runtime-info` warning (non-blocking)
  ```
  WARNING: Using MockAdapter for testing — not suitable for production
  ```
- **Live adapter environments**: No warnings for valid configurations

**Common Live Mode Errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Adapter initialization failed` | OpenFisca web API unreachable | Check network connectivity, verify API endpoint |
| `Computation failed at year <year>` | Policy parameter invalid for year | Verify rate_schedule covers all requested years |
| `Normalization failed` | Adapter output missing expected columns | Check mapping configuration, verify OpenFisca variables |

### Replay Mode (Explicit)

Replay mode is an explicit, manual opt-in path. It is **NOT** a fallback and is never invoked automatically. Replay mode requires precomputed output files to exist.

**Verification:**

```bash
# Check runtime mode in manifest
cat ~/.reformlab/results/<run_id>/manifest.json | jq '.runtime_mode'
# Expected: "replay"
```

**Common Replay Errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Replay mode unavailable` — No precomputed data files found | Missing precomputed CSV files | Ensure CSV files exist in `REFORMLAB_OPENFISCA_DATA_DIR` or use live mode |
| `422 Unprocessable Entity` | Invalid replay data format | Verify CSV has required columns: household_id, income_tax, carbon_tax |
| `File not found: <year>.csv` | Precomputed data missing for requested year | Generate precomputed data or use live mode for that year |

**Enabling Replay Mode:**

```bash
# Set environment variable pointing to precomputed data directory
export REFORMLAB_OPENFISCA_DATA_DIR=/path/to/precomputed/data

# Precomputed data must have CSV files for each year:
# <data_dir>/2025.csv
# <data_dir>/2026.csv
# etc.
```

## Population Resolution Diagnostics

### Population Sources

Populations can be:

- **Bundled**: Distributed with the product in `data/populations/`
- **Uploaded**: User-uploaded files in `.reformlab/uploaded-populations/`
- **Generated**: Synthetic populations created via data fusion or population generator (identified by `.manifest.json` sidecar)

### Population Executability

All populations must be executable, meaning they contain minimum required columns for live execution.

**Required Columns:**

- `household_id`: Unique identifier for each household/entity
- `income`: Pre-tax household income
- `disposable_income`: Post-tax household income (needed for redistribution)
- `carbon_tax`: Carbon tax liability (needed for policy scenarios)

**Verification:**

```bash
# Check available populations
curl -H "Authorization: Bearer <token>" \
  https://api.reformlab.com/api/populations

# Check preflight validation for a specific population
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"population_id": "<id>"}' \
  https://api.reformlab.com/api/validation/preflight
```

**Inspecting Population Files:**

```bash
# Check population schema (CSV)
head -1 data/populations/<id>.csv

# Check population schema (Parquet)
python3 -c "import pyarrow.parquet as pq; print(pq.read_schema('data/populations/<id>.parquet'))"

# Check generated population metadata
cat data/populations/<id>.manifest.json | jq '.source'
```

**Common Population Errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Population '<id>' not found` | Unknown population ID | Check available populations via GET /api/populations |
| `Missing required columns: <list>` | Population schema incomplete | Add missing columns to population file |
| `Population cannot be resolved` | Path traversal or invalid characters | Use valid alphanumeric population IDs only |
| `Population is incompatible with live execution` | Schema validation failed | Regenerate population with correct schema |

**Population Resolution Order:**

The resolver checks sources in this order:

1. Bundled populations (`data/populations/`)
2. Uploaded populations (`.reformlab/uploaded-populations/`)
3. Generated populations (bundled path + `.manifest.json` sidecar)

Bundled populations shadow uploaded populations on duplicate IDs (matching existing behavior).

## Mapping and Normalization Diagnostics

### Normalization Layer

Live OpenFisca outputs are normalized to the app-facing schema via `result_normalizer.py`. The normalizer:

1. Maps French OpenFisca variable names to English project schema names
2. Validates that minimum required indicator columns are present
3. Returns a normalized `pa.Table` for downstream consumption

### Default Output Mapping

When no explicit `MappingConfig` is provided, the normalizer uses `_DEFAULT_OUTPUT_MAPPING`:

```python
{
    "revenu_disponible": "disposable_income",
    "irpp": "income_tax",
    "impots_directs": "direct_taxes",
    "revenu_net": "net_income",
    "salaire_net": "income",
    "revenu_brut": "gross_income",
    "prestations_sociales": "social_benefits",
    "taxe_carbone": "carbon_tax",
}
```

**Verification:**

```bash
# Check normalized output columns
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "<run_id>"}' \
  https://api.reformlab.com/api/indicators/distributional | jq '.data | keys'

# Expected keys include: household_id, year, income, disposable_income, carbon_tax, etc.
```

### Custom Mapping

If the default mapping doesn't match your adapter's output, provide a `MappingConfig` YAML file:

```yaml
output_mapping:
  your_french_variable: "your_project_field"
  another_variable: "another_field"
```

**Minimum Required Columns:**

At least one of these columns must survive normalization:

- `income`
- `disposable_income`
- `carbon_tax`

**Common Normalization Errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Output normalization failed` — No recognizable OpenFisca columns found | Adapter output doesn't include any mapped variables | Verify adapter output includes expected variables, provide MappingConfig |
| `Column rename produces duplicate '<name>'` | Mapping creates duplicate column name | Adjust MappingConfig to resolve naming conflict |
| `Missing required indicator columns` | Normalized output lacks minimum required columns | Ensure at least one of income/disposable_income/carbon_tax is present |
| `NormalizationError: <message>` | Schema validation failed | Check error message for specific missing fields |

**Inspecting Normalization:**

```bash
# Check if normalization was applied
cat ~/.reformlab/results/<run_id>/manifest.json | jq '.mappings'

# View panel schema (after normalization)
python3 -c "import pyarrow.parquet as pq; print(pq.read_schema('~/.reformlab/results/<run_id>/panel.parquet'))"
```

## Failed Run Investigation Checklist

When a run fails, follow this step-by-step investigation:

### Step 1: Check Manifest

**Path:** `~/.reformlab/results/{run_id}/manifest.json`

**Verify:**
- `runtime_mode` is as expected ("live" or "replay")
- `population_id` and `population_source` are populated (if population was used)
- `integrity_hash` matches content (tamper detection)

```bash
cat ~/.reformlab/results/<run_id>/manifest.json | jq '{runtime_mode, population_id, population_source, integrity_hash}'
```

**Common Issues:**
- Empty `runtime_mode`: Indicates older run before Story 23.1 (defaults to "live")
- Empty `population_source`: Indicates older run before Story 23.5

### Step 2: Check Result Details

**Endpoint:** `GET /api/results/{run_id}`

**Verify:**
- `runtime_mode`, `population_source`, and other metadata fields are present
- Timestamps indicate expected execution order
- `status` is "completed" or "failed"

```bash
curl -H "Authorization: Bearer <token>" \
  https://api.reformlab.com/api/results/<run_id> | jq '{runtime_mode, population_source, status, timestamp}'
```

**Common Issues:**
- Status "failed": Run did not complete successfully
- Missing metadata fields: May indicate older run or partial failure

### Step 3: Check Logs

**Location:** Container or local logs directory

**Look for:**
- ERROR or CRITICAL level messages around run timestamp
- Adapter initialization logs (live vs replay selection)
- Population resolution logs (file path, row count)

```bash
# In container:
kubectl logs <pod-name> | grep "<run_id>" | grep -i error

# Local:
tail -f reformlab.log | grep "<run_id>"
```

**Common Issues:**
- Adapter initialization failures: Check OpenFisca API availability
- Population resolution errors: Verify population file exists and is readable
- Normalization errors: Check mapping configuration

### Step 4: Validate Population

**Endpoint:** `POST /api/validation/preflight` with `population_id`

**Verify:**
- Preflight passes for requested population
- Population file exists and is readable
- Schema contains required columns

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"population_id": "<id>"}' \
  https://api.reformlab.com/api/validation/preflight
```

**Common Issues:**
- Preflight fails: Fix population schema or select different population
- File not found: Check population directory configuration

### Step 5: Verify Adapter

**Check:**
- Which adapter initialized (MockAdapter, OpenFiscaAdapter, OpenFiscaApiAdapter)
- Adapter version matches expected version
- Any adapter-specific warnings in logs

```bash
# Check logs for adapter initialization
grep "Adapter initialized" reformlab.log
```

**Adapter Types:**
- `MockAdapter`: For testing only, emits warning
- `OpenFiscaAdapter`: Embedded OpenFisca (if installed)
- `OpenFiscaApiAdapter`: Web API adapter (default)

### Step 6: Inspect Normalization

**Check:**
- Normalization succeeded (no NormalizationError in logs)
- Normalized output contains expected columns
- Mapping configuration was applied (if custom)

```bash
# Check for normalization errors
grep "normalization" reformlab.log | grep -i error

# Verify output columns
python3 -c "import pyarrow.parquet as pq; t = pq.read_table('~/.reformlab/results/<run_id>/panel.parquet'); print(t.column_names)"
```

### Step 7: Test Indicators and Exports

**Endpoints:**
- `POST /api/indicators/{type}` with run_id in request body
- `POST /api/exports/csv` or `POST /api/exports/parquet` with run_id in request body

**Verify:**
- Indicator computation returns 200 with valid result
- Export succeeds and file is downloadable

```bash
# Test indicator computation
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "<run_id>"}' \
  https://api.reformlab.com/api/indicators/distributional

# Test CSV export
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "<run_id>"}' \
  https://api.reformlab.com/api/exports/csv -o export.csv
```

**Common Issues:**
- 409 Conflict: Panel data not available (failed run or evicted from cache)
- 404 Not Found: Run ID does not exist

## Additional Resources

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/docs` | Full API reference (Swagger UI) |
| `POST /api/validation/preflight` | Validate configuration before running |
| `GET /api/results/{run_id}` | Retrieve run result details |
| `POST /api/indicators/{type}` | Compute indicators on a run |
| `POST /api/comparison` | Compare two runs |
| `POST /api/exports/csv` or `POST /api/exports/parquet` | Export run results as CSV or Parquet |
| `GET /api/populations` | List available populations |

### Source Files

| File | Purpose |
|------|---------|
| `src/reformlab/computation/result_normalizer.py` | Normalization implementation |
| `src/reformlab/server/population_resolver.py` | Population resolution logic |
| `src/reformlab/server/validation.py` | Preflight validation checks |
| `src/reformlab/governance/manifest.py` | Manifest schema and validation |
| `src/reformlab/server/result_store.py` | Result persistence and retrieval |
| `src/reformlab/server/dependencies.py` | Adapter factory and singleton management |

### Error Response Format

All errors follow the project error pattern:

```json
{
  "what": "High-level description of what failed",
  "why": "Detailed reason for the failure",
  "fix": "Actionable guidance to resolve the issue"
}
```

### Determinism and Reproducibility

- All runs are deterministic and reproducible with the same seed
- Seeds are explicit and logged in manifests
- Seeds are derived deterministically: `master_seed XOR year`
- Manifest integrity is verified via SHA-256 hash

### Data Hashes

Manifests include SHA-256 hashes of:
- Input files (data_hashes)
- Output artifacts (output_hashes)
- These are stored under `manifest.data_hashes` and `manifest.output_hashes`

### Common Failure Patterns

| Pattern | Likely Cause | Investigation Path |
|---------|--------------|-------------------|
| Run fails at first year | Policy parameter invalid for start year | Check rate_schedule, verify year coverage |
| Run fails at later year | Year-specific policy missing | Check policy dict for all years in range |
| 409 on indicators | Panel data not available | Check run status, verify panel.parquet exists |
| 422 on population resolution | Population schema invalid | Verify required columns present |
| Normalization error | Adapter output incompatible | Check mapping, verify OpenFisca variables |
| Replay mode fails | Precomputed data missing | Verify CSV files exist in data directory |

### Support and Escalation

If the investigation checklist does not resolve the issue:

1. Collect the following information:
   - Run ID
   - Manifest content (`manifest.json`)
   - Relevant log excerpts
   - Population ID and source
   - Runtime mode used

2. Create an issue with:
   - Clear description of the failure
   - Steps to reproduce (if applicable)
   - Collected diagnostic information
   - Expected vs actual behavior
