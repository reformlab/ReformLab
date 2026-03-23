# API Reference

**How to read this document:** Each endpoint is listed with its HTTP method, path, request body (if any), response shape, and possible error codes. All endpoints require authentication via bearer token (obtained from `POST /api/auth/login`) except the login endpoint itself and the OpenAPI docs at `/api/docs`.

All error responses follow the **What/Why/Fix** pattern:

```json
{
  "error": "Category",
  "what": "What went wrong",
  "why": "Why it happened",
  "fix": "What you can do about it",
  "status_code": 422
}
```

---

## Authentication

### `POST /api/auth/login`

Obtain a bearer token for subsequent requests.

**Request:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `password` | `string` | yes | Server password (`REFORMLAB_PASSWORD` env var) |

**Response (200):**

| Field | Type | Description |
|-------|------|-------------|
| `token` | `string` | Bearer token for `Authorization` header |

---

## Simulation Runs

### `POST /api/runs`

Execute a simulation synchronously. Blocks until complete (<10s for 100k households). Auto-saves metadata, panel data, and manifest to persistent storage.

**Request (`RunRequest`):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `template_name` | `string?` | `null` | Policy template to use from the registry |
| `policy` | `dict` | `{}` | Policy parameter overrides |
| `start_year` | `int` | `2025` | First simulation year |
| `end_year` | `int` | `2030` | Last simulation year |
| `population_id` | `string?` | `null` | ID of a population file in `data/populations/` |
| `seed` | `int?` | `null` | Random seed for deterministic results |
| `baseline_id` | `string?` | `null` | Run ID of baseline (for reform runs) |
| `portfolio_name` | `string?` | `null` | Set automatically for portfolio-originated runs |
| `policy_type` | `string?` | `null` | For metadata recording |

**Response (200) — `RunResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | UUID identifying the run |
| `success` | `bool` | Whether the simulation completed without errors |
| `scenario_id` | `string` | Content-addressable scenario hash |
| `years` | `list[int]` | Years that were simulated |
| `row_count` | `int` | Total rows in the output panel |
| `manifest_id` | `string` | Governance manifest identifier |

### `POST /api/runs/memory-check`

Pre-flight memory estimation before running a simulation.

**Request (`MemoryCheckRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_name` | `string` | yes | Template to estimate for |
| `policy` | `dict` | no | Policy parameters |
| `start_year` | `int` | yes | First year |
| `end_year` | `int` | yes | Last year |
| `population_id` | `string?` | no | Population dataset |

**Response (200) — `MemoryCheckResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `should_warn` | `bool` | True if estimated memory exceeds safe threshold |
| `estimated_gb` | `float` | Estimated memory usage in GB |
| `available_gb` | `float` | Available system memory in GB |
| `message` | `string` | Human-readable summary |

---

## Indicators

### `POST /api/indicators/{indicator_type}`

Compute an indicator from a cached simulation result.

**Path parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `indicator_type` | `distributional`, `geographic`, `fiscal` | Type of indicator to compute. `welfare` is not allowed here (use comparison endpoint). |

**Request (`IndicatorRequest`):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `run_id` | `string` | — | Run to compute indicators for |
| `income_field` | `string` | `"income"` | Column name for income (distributional only) |
| `by_year` | `bool` | `false` | Break down by year |

**Response (200) — `IndicatorResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `indicator_type` | `string` | Echo of the requested type |
| `data` | `dict[str, list]` | Columnar data (PyArrow table serialized as dict of arrays) |
| `metadata` | `dict` | Computation metadata (row count, timing, etc.) |
| `warnings` | `list[str]` | Any non-fatal warnings |
| `excluded_count` | `int` | Rows excluded due to missing data |

**Errors:** `422` invalid type or welfare without comparison; `404` unknown run_id; `409` panel data evicted.

---

## Comparison

### `POST /api/comparison`

Compare welfare indicators between a baseline and reform simulation run.

**Request (`ComparisonRequest`):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `baseline_run_id` | `string` | — | Baseline simulation run |
| `reform_run_id` | `string` | — | Reform simulation run |
| `welfare_field` | `string` | `"disposable_income"` | Field to measure welfare change |
| `threshold` | `float` | `0.0` | Minimum change threshold |

**Response (200):** Same as `IndicatorResponse` with `indicator_type: "welfare"`.

**Errors:** `404` unknown run_id; `409` panel data evicted.

### `POST /api/comparison/portfolios`

Compare indicator results across 2–5 portfolio simulation runs.

**Request (`PortfolioComparisonRequest`):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `run_ids` | `list[str]` | — | 2–5 unique run IDs to compare |
| `baseline_run_id` | `string?` | first in list | Which run is the baseline |
| `indicator_types` | `list[str]` | `["distributional", "fiscal"]` | Indicator types to compare |
| `include_welfare` | `bool` | `true` | Include welfare comparison |
| `include_deltas` | `bool` | `true` | Include absolute differences |
| `include_pct_deltas` | `bool` | `true` | Include percentage differences |

**Response (200) — `PortfolioComparisonResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `comparisons` | `dict[str, ComparisonData]` | Per-indicator comparison data (columns + data arrays) |
| `cross_metrics` | `list[CrossMetricItem]` | Aggregate ranking metrics across portfolios |
| `portfolio_labels` | `list[str]` | Human-readable labels derived from run metadata |
| `metadata` | `dict` | Comparison metadata |
| `warnings` | `list[str]` | Non-fatal warnings |

**Errors:** `422` wrong run count, duplicates, or reserved labels; `404` unknown run; `409` evicted data.

---

## Scenarios

### `GET /api/scenarios`

List all registered scenario names.

**Response (200):** `{"scenarios": ["scenario-a", "scenario-b"]}`

### `GET /api/scenarios/{name}`

Get a scenario by name.

**Response (200) — `ScenarioResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Scenario name |
| `policy_type` | `string` | `carbon_tax`, `subsidy`, `rebate`, or `feebate` |
| `description` | `string` | Human-readable description |
| `version` | `string` | Version string |
| `policy` | `dict` | Policy parameters (rate_schedule, exemptions, etc.) |
| `year_schedule` | `dict` | `{start_year, end_year}` |
| `baseline_ref` | `string?` | Name of baseline scenario (reform scenarios only) |

### `POST /api/scenarios`

Create and register a new scenario.

**Request (`CreateScenarioRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | yes | Unique scenario name |
| `policy_type` | `string?` | no | One of: `carbon_tax`, `subsidy`, `rebate`, `feebate`. Can also be set via `_type` key in policy dict. |
| `policy` | `dict` | yes | Policy parameters (rate_schedule, exemptions, etc.) |
| `start_year` | `int` | yes | First year |
| `end_year` | `int` | yes | Last year |
| `description` | `string` | no | Human-readable description |
| `baseline_ref` | `string?` | no | If set, creates a ReformScenario referencing this baseline |

**Response (201):** `{"version_id": "abc123..."}`

### `POST /api/scenarios/{name}/clone`

Clone an existing scenario with a new name.

**Request:** `{"new_name": "my-clone"}`

**Response (201):** `ScenarioResponse` of the cloned scenario.

---

## Templates

### `GET /api/templates`

List available policy templates.

**Response (200):**

```json
{
  "templates": [
    {
      "id": "carbon-tax-basic",
      "name": "Carbon Tax Basic",
      "type": "carbon_tax",
      "parameter_count": 4,
      "description": "...",
      "parameter_groups": ["rate_schedule", "exemptions", ...]
    }
  ]
}
```

### `GET /api/templates/{name}`

Get a template with full parameter details, including default policy values.

**Response (200) — `TemplateDetailResponse`:** Same as list item plus `default_policy: dict`.

---

## Portfolios

A portfolio is a collection of 2+ policies that are combined and simulated together.

### `GET /api/portfolios`

List all saved portfolios.

**Response (200):** `list[PortfolioListItem]` with `name`, `description`, `version_id`, `policy_count`.

### `GET /api/portfolios/{name}`

Get portfolio detail including all policies.

**Response (200) — `PortfolioDetailResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Portfolio name (lowercase slug) |
| `description` | `string` | Description |
| `version_id` | `string` | Content-addressable version hash |
| `policies` | `list[PortfolioPolicyItem]` | Individual policies with rate_schedule and parameters |
| `resolution_strategy` | `string` | How conflicts are resolved: `error`, `sum`, `first_wins`, `last_wins`, `max` |
| `policy_count` | `int` | Number of policies |

### `POST /api/portfolios`

Create and save a new portfolio. Requires at least 2 policies.

**Request (`CreatePortfolioRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | yes | Lowercase slug (`[a-z0-9-]`, max 64 chars) |
| `description` | `string` | no | Description |
| `policies` | `list[PortfolioPolicyRequest]` | yes | At least 2 policy definitions |
| `resolution_strategy` | `string` | no | Default: `"error"` |

**`PortfolioPolicyRequest` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Policy name |
| `policy_type` | `string` | `carbon_tax`, `subsidy`, `rebate`, or `feebate` |
| `rate_schedule` | `dict[str, float]` | Year → rate mapping (string keys) |
| `exemptions` | `list[str]` | Exempted categories |
| `thresholds` | `list[float]` | Threshold values |
| `covered_categories` | `list[str]` | Categories this policy covers |
| `extra_params` | `dict` | Additional policy-type-specific parameters |

**Response (201):** `{"version_id": "abc123..."}`

**Errors:** `409` name already exists; `422` invalid name, strategy, or policy_type; `400` fewer than 2 policies.

### `PUT /api/portfolios/{name}`

Update an existing portfolio's policies.

**Request (`UpdatePortfolioRequest`):** Same as create but `description` and `resolution_strategy` are optional (preserved from existing if omitted).

**Response (200):** `PortfolioDetailResponse` with new version_id.

### `DELETE /api/portfolios/{name}`

Delete a portfolio. **Response (204):** No content.

### `POST /api/portfolios/{name}/clone`

Clone a portfolio with a new name.

**Request:** `{"new_name": "my-clone"}`

**Response (201):** `PortfolioDetailResponse` of the cloned portfolio.

### `POST /api/portfolios/validate`

Validate a draft portfolio for policy conflicts without saving.

**Request (`ValidatePortfolioRequest`):**

| Field | Type | Description |
|-------|------|-------------|
| `policies` | `list[PortfolioPolicyRequest]` | At least 2 policies |
| `resolution_strategy` | `string` | Default: `"error"` |

**Response (200) — `ValidatePortfolioResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `conflicts` | `list[PortfolioConflict]` | Detected conflicts (type, indices, parameter, description) |
| `is_compatible` | `bool` | True if no conflicts found |

---

## Results

### `GET /api/results`

List all saved simulation results (metadata only, no panel loading).

**Response (200):** `list[ResultListItem]`

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | UUID |
| `timestamp` | `string` | ISO 8601 |
| `run_kind` | `string` | `"scenario"` or `"portfolio"` |
| `start_year` / `end_year` | `int` | Year range |
| `row_count` | `int` | Panel rows |
| `status` | `string` | `"completed"` or `"failed"` |
| `data_available` | `bool` | True if panel data exists on disk or in cache |
| `template_name` | `string?` | Scenario runs only |
| `policy_type` | `string?` | Scenario runs only |
| `portfolio_name` | `string?` | Portfolio runs only |

### `GET /api/results/{run_id}`

Full detail for a single result. Includes column list and basic indicators when `data_available` is true.

**Response (200):** `ResultDetailResponse` — extends list item with `population_id`, `seed`, `manifest_id`, `scenario_id`, `adapter_version`, `started_at`, `finished_at`, `indicators`, `columns`, `column_count`.

### `DELETE /api/results/{run_id}`

Delete a result from persistent store and cache. **Response (204).**

### `GET /api/results/{run_id}/export/csv`

Download panel data as CSV. **Response:** `text/csv` streaming download.

### `GET /api/results/{run_id}/export/parquet`

Download panel data as Parquet. **Response:** `application/octet-stream` streaming download.

**Errors (all result endpoints):** `404` unknown run_id; `409` panel data not available; `400` invalid run_id format.

---

## Data Fusion

Population generation from multiple institutional data sources.

### `GET /api/data-fusion/sources`

List all available data sources grouped by provider.

**Response (200):**

```json
{
  "sources": {
    "insee": [{"id": "...", "provider": "insee", "name": "...", ...}],
    "eurostat": [...],
    "ademe": [...],
    "sdes": [...]
  }
}
```

Each `DataSourceItem` has: `id`, `provider`, `name`, `description`, `variable_count`, `record_count`, `source_url`.

### `GET /api/data-fusion/sources/{provider}/{dataset_id}`

Get dataset detail including column schema.

**Response (200) — `DataSourceDetail`:** Extends `DataSourceItem` with `columns: list[ColumnInfo]` (each has `name`, `type`, `description`).

**Errors:** `404` unknown provider or dataset_id.

### `GET /api/data-fusion/merge-methods`

Return available merge methods with plain-language descriptions.

**Response (200):**

```json
{
  "methods": [
    {
      "id": "uniform",
      "name": "Uniform Distribution",
      "what_it_does": "Matches each household...",
      "assumption": "Variables are statistically independent...",
      "when_appropriate": "Quick baseline...",
      "tradeoff": "Fast and simple, but...",
      "parameters": [{"name": "seed", "type": "int", ...}]
    }
  ]
}
```

Available methods: `uniform`, `ipf` (Iterative Proportional Fitting), `conditional` (Conditional Sampling).

### `POST /api/data-fusion/generate`

Execute the population generation pipeline.

**Request (`GeneratePopulationRequest`):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sources` | `list[DataFusionSourceSelection]` | — | At least 2 sources (each has `provider` + `dataset_id`) |
| `merge_method` | `string` | `"uniform"` | `uniform`, `ipf`, or `conditional` |
| `seed` | `int` | `42` | Random seed |
| `ipf_constraints` | `list[IPFConstraintRequest]` | `[]` | Marginal constraints for IPF (`dimension` + `targets` dict) |
| `strata_columns` | `list[str]` | `[]` | Columns for conditional sampling stratification |

**Response (200) — `GeneratePopulationResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | True on success |
| `summary` | `PopulationSummary` | `record_count`, `column_count`, `columns` |
| `step_log` | `list[StepLogItem]` | Per-step execution log with timing |
| `assumption_chain` | `list[AssumptionRecordItem]` | Documented assumptions from each step |
| `validation_result` | `ValidationResultResponse?` | Marginal constraint validation (IPF only) |

**Errors:** `422` fewer than 2 sources, unknown provider/dataset/method.

---

## Decisions

### `POST /api/decisions/summary`

Aggregate decision outcomes from a simulation that included discrete choice domains.

**Request (`DecisionSummaryRequest`):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `run_id` | `string` | — | Simulation run with decision data |
| `domain_name` | `string?` | `null` | Filter to one domain (`vehicle`, `heating`), or null for all |
| `group_by` | `string?` | `null` | Only `"decile"` is supported |
| `group_value` | `string?` | `null` | Decile number `"1"`–`"10"` |
| `year` | `int?` | `null` | If set, include mean probabilities for that year |

**Response (200) — `DecisionSummaryResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Echo of input |
| `domains` | `list[DomainSummary]` | Per-domain summaries |
| `metadata` | `dict` | `{start_year, end_year}` |
| `warnings` | `list[str]` | Non-fatal warnings |

**`DomainSummary`:**

| Field | Type | Description |
|-------|------|-------------|
| `domain_name` | `string` | `"vehicle"` or `"heating"` |
| `alternative_ids` | `list[str]` | e.g. `["keep_current", "buy_ev", ...]` |
| `alternative_labels` | `dict[str, str]` | Human-readable labels |
| `yearly_outcomes` | `list[YearlyOutcome]` | Per-year counts, percentages, and optional mean probabilities |

**Errors:** `404` unknown run; `409` evicted data; `422` no decision data, invalid group_by, or unknown domain.

---

## Exports (Legacy)

These endpoints duplicate the result export functionality. Prefer `GET /api/results/{run_id}/export/csv` instead.

### `POST /api/exports/csv`

**Request:** `{"run_id": "..."}` — **Response:** CSV download.

### `POST /api/exports/parquet`

**Request:** `{"run_id": "..."}` — **Response:** Parquet download.

---

## Populations

### `GET /api/populations`

List available population datasets from the `data/populations/` directory.

**Response (200):**

```json
{
  "populations": [
    {
      "id": "insee-households-2023-100k",
      "name": "Insee Households 2023 100k",
      "households": 100000,
      "source": "insee",
      "year": 2023
    }
  ]
}
```

---

## OpenAPI

The full OpenAPI specification is available at `GET /api/openapi.json` and the interactive Swagger UI at `GET /api/docs`.
