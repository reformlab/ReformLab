# Domain Model Reference

**How to read this document:** This reference catalogs every frozen dataclass and type definition in the `reformlab` package, organized by subsystem (layer). Each type lists its fields, constraints, and relationships to other types.

All domain types follow two conventions:

1. **Frozen dataclasses** — Immutable after creation (`@dataclass(frozen=True)`). This guarantees no mutation during simulation and makes provenance tracking reliable.
2. **PyArrow-first data** — Tabular data uses `pyarrow.Table`, not pandas DataFrames. This keeps memory usage predictable and avoids implicit type coercion.

---

## Computation Layer

> `from reformlab.computation import PopulationData, PolicyConfig, ComputationResult`

Source: `src/reformlab/computation/types.py`

### `PopulationData`

Wraps a population dataset with metadata. The underlying data is a PyArrow Table keyed by entity type (e.g. `"individu"`, `"menage"`).

| Field | Type | Description |
|-------|------|-------------|
| `tables` | `dict[str, pa.Table]` | Entity tables keyed by name. Single-entity datasets use `"default"`. |
| `metadata` | `dict[str, Any]` | Optional metadata (source, vintage, row counts) |

**Properties:** `row_count: int` — total rows across all entity tables.

### `PolicyConfig`

Scenario parameters for a single computation period.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `policy` | `dict[str, Any]` | — | Policy parameter values |
| `name` | `str` | `""` | Human-readable name |
| `description` | `str` | `""` | Description |

### `ComputationResult`

Result returned by a `ComputationAdapter.compute()` call.

| Field | Type | Description |
|-------|------|-------------|
| `output_fields` | `pa.Table` | Primary output table (person-entity when multi-entity) |
| `adapter_version` | `str` | Version string of the adapter |
| `period` | `int` | Computation period (year) |
| `metadata` | `dict[str, Any]` | Timing, row count, run-level info |
| `entity_tables` | `dict[str, pa.Table]` | Per-entity output tables (empty for single-entity) |

---

## Orchestrator Layer

> `from reformlab.orchestrator import YearState, OrchestratorConfig, OrchestratorResult`

Source: `src/reformlab/orchestrator/types.py`

### `YearState`

Immutable snapshot of the simulation state at a point in the yearly loop.

| Field | Type | Description |
|-------|------|-------------|
| `year` | `int` | Current simulation year |
| `population` | `PopulationData` | Current population state |
| `policy` | `PolicyConfig` | Policy parameters for this year |
| `results` | `dict[str, Any]` | Accumulated results from prior steps |
| `metadata` | `dict[str, Any]` | Step-level metadata |

### `OrchestratorConfig`

Configuration for a multi-year simulation run.

| Field | Type | Description |
|-------|------|-------------|
| `start_year` | `int` | First simulation year |
| `end_year` | `int` | Last simulation year (inclusive) |
| `seed` | `int?` | Random seed for reproducibility |
| `steps` | `tuple[PipelineStep, ...]` | Ordered pipeline steps |

### `OrchestratorResult`

Complete result of a multi-year simulation.

| Field | Type | Description |
|-------|------|-------------|
| `yearly_states` | `dict[int, YearState]` | Final state per year |
| `metadata` | `dict[str, Any]` | Run-level metadata |
| `success` | `bool` | Whether all years completed |

**Type aliases:**

- `YearStep = Callable[[int, YearState], YearState]` — bare callable step
- `PipelineStep = YearStep | OrchestratorStep` — either form

---

## Indicators Layer

> `from reformlab.indicators import DecileIndicators, WelfareIndicators, FiscalIndicators, IndicatorResult`

Source: `src/reformlab/indicators/types.py`

### `IndicatorResult`

Container for computed indicator data. All indicator types share this wrapper.

| Field | Type | Description |
|-------|------|-------------|
| `indicator_type` | `str` | `"distributional"`, `"geographic"`, `"welfare"`, or `"fiscal"` |
| `data` | varies | The typed indicator dataclass |
| `metadata` | `dict[str, Any]` | Computation metadata |
| `warnings` | `list[str]` | Non-fatal warnings |
| `excluded_count` | `int` | Rows excluded due to missing data |

**Methods:** `to_table() -> pa.Table`, `export_csv(path)`, `export_parquet(path)`.

### `DecileIndicators`

Distributional analysis by income decile.

| Field | Type | Description |
|-------|------|-------------|
| `deciles` | `pa.Table` | Table with columns: `decile`, `mean_income`, `mean_tax`, `tax_share`, etc. |
| `gini_before` | `float` | Gini coefficient before policy |
| `gini_after` | `float` | Gini coefficient after policy |
| `total_revenue` | `float` | Total tax revenue collected |

### `RegionIndicators`

Geographic breakdown of policy impacts.

| Field | Type | Description |
|-------|------|-------------|
| `regions` | `pa.Table` | Table with columns: `region`, `mean_impact`, `household_count`, etc. |

### `WelfareIndicators`

Welfare comparison between baseline and reform scenarios.

| Field | Type | Description |
|-------|------|-------------|
| `winners` | `int` | Households better off under reform |
| `losers` | `int` | Households worse off |
| `neutral` | `int` | Households unchanged |
| `mean_gain` | `float` | Average welfare change |
| `detail` | `pa.Table` | Per-household welfare deltas |

### `FiscalIndicators`

Government revenue and expenditure analysis.

| Field | Type | Description |
|-------|------|-------------|
| `total_revenue` | `float` | Total government revenue from policy |
| `total_expenditure` | `float` | Total expenditure (subsidies, rebates) |
| `net_fiscal` | `float` | Revenue minus expenditure |
| `detail` | `pa.Table` | Yearly breakdown |

### Configuration Types

Each indicator type has a corresponding config:

- `DistributionalConfig(income_field, by_year)`
- `GeographicConfig(region_field, by_year)`
- `WelfareConfig(welfare_field, threshold)`
- `FiscalConfig(by_year)`

---

## Vintage Layer

> `from reformlab.vintage import VintageCohort, VintageState, VintageSummary`

Source: `src/reformlab/vintage/types.py`

Tracks the age distribution of capital stock (vehicles, heating systems) as it evolves year by year.

### `VintageCohort`

A single age cohort within a vintage distribution.

| Field | Type | Description |
|-------|------|-------------|
| `age` | `int` | Years since purchase/installation |
| `count` | `int` | Number of units in this cohort |
| `technology` | `str` | Technology type (e.g. `"petrol"`, `"heat_pump"`) |

### `VintageState`

Collection of cohorts for an asset class at a point in time.

| Field | Type | Description |
|-------|------|-------------|
| `asset_class` | `str` | e.g. `"vehicle"`, `"heating"` |
| `year` | `int` | Reference year |
| `cohorts` | `tuple[VintageCohort, ...]` | All age cohorts |

### `VintageSummary`

Derived metrics from a VintageState.

| Field | Type | Description |
|-------|------|-------------|
| `mean_age` | `float` | Average age across all units |
| `technology_shares` | `dict[str, float]` | Share by technology type |
| `total_units` | `int` | Total stock count |

**Class method:** `VintageSummary.from_state(state: VintageState) -> VintageSummary`

---

## Discrete Choice Layer

> `from reformlab.discrete_choice import Alternative, ChoiceSet, CostMatrix, ChoiceResult`

Source: `src/reformlab/discrete_choice/types.py`

Models household-level technology adoption decisions using multinomial logit.

### `Alternative`

A single option in a choice set (e.g. "buy EV", "keep current vehicle").

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier |
| `label` | `str` | Human-readable name |
| `attributes` | `dict[str, float]` | Cost, emissions, comfort scores, etc. |

### `ChoiceSet`

Collection of alternatives available to a decision-maker.

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `str` | Decision domain (e.g. `"vehicle"`, `"heating"`) |
| `alternatives` | `tuple[Alternative, ...]` | Available options |

**Validation:** At least 2 alternatives required; IDs must be unique within a set.

**Properties:** `ids: list[str]`, `labels: dict[str, str]`.

### `CostMatrix`

N×M matrix mapping households to alternative-specific costs.

| Field | Type | Description |
|-------|------|-------------|
| `values` | `pa.Table` | Table with one column per alternative, one row per household |
| `alternative_ids` | `tuple[str, ...]` | Column order |

**Validation:** Column count must match alternative count; all values must be numeric.

### `TasteParameters`

Parameters for the multinomial logit utility function.

| Field | Type | Description |
|-------|------|-------------|
| `scale` | `float` | Scale parameter (must be > 0) |
| `attribute_weights` | `dict[str, float]` | Weights per attribute in utility function |

### `ChoiceResult`

Output of a discrete choice simulation step.

| Field | Type | Description |
|-------|------|-------------|
| `chosen` | `pa.Array` | String array of chosen alternative IDs (one per household) |
| `probabilities` | `pa.Table` | Probability matrix (one column per alternative) |
| `domain` | `str` | Domain name |
| `year` | `int` | Simulation year |

**Validation:** `chosen` length must equal `probabilities` row count; probabilities must sum to ~1.0 per row.

### `ExpansionResult`

Result of applying a chosen alternative to the population table.

| Field | Type | Description |
|-------|------|-------------|
| `table` | `pa.Table` | Updated population table with new columns |
| `columns_added` | `tuple[str, ...]` | Names of new/modified columns |

---

## Calibration Layer

> `from reformlab.calibration import CalibrationTarget, CalibrationEngine, CalibrationResult`

Source: `src/reformlab/calibration/types.py`

Calibrates model parameters to match observed real-world data.

### `CalibrationTarget`

A single empirical observation to calibrate against.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Target identifier |
| `domain` | `str` | Which model domain this targets |
| `metric` | `str` | What is being measured (e.g. `"market_share"`, `"adoption_rate"`) |
| `observed_value` | `float` | Empirical value |
| `weight` | `float` | Importance weight in objective function (default 1.0) |
| `tolerance` | `float` | Acceptable deviation (default 0.05) |

**Validation:** `weight > 0`, `tolerance > 0`, `observed_value` is finite.

### `CalibrationTargetSet`

Collection of calibration targets with validation.

| Field | Type | Description |
|-------|------|-------------|
| `targets` | `tuple[CalibrationTarget, ...]` | All targets |
| `source` | `str` | Data source description |

**Methods:** `by_domain() -> dict[str, list[CalibrationTarget]]`, `validate_consistency()`, `to_governance_entry() -> dict`.

### `CalibrationConfig`

Configuration for a calibration run.

| Field | Type | Description |
|-------|------|-------------|
| `method` | `str` | Optimization method (e.g. `"nelder-mead"`, `"powell"`) |
| `max_iterations` | `int` | Maximum optimization iterations |
| `convergence_threshold` | `float` | Stop when improvement drops below this |
| `seed` | `int?` | Random seed |

### `CalibrationResult`

Output of a calibration run.

| Field | Type | Description |
|-------|------|-------------|
| `parameters` | `dict[str, float]` | Optimized parameter values |
| `fit_metrics` | `FitMetrics` | Goodness-of-fit statistics |
| `iterations` | `int` | Number of iterations performed |
| `converged` | `bool` | Whether optimization converged |

**Methods:** `to_governance_entry() -> dict` — for inclusion in `RunManifest`.

### `FitMetrics`

Goodness-of-fit statistics.

| Field | Type | Description |
|-------|------|-------------|
| `rmse` | `float` | Root mean squared error |
| `mae` | `float` | Mean absolute error |
| `max_error` | `float` | Maximum single-target error |
| `r_squared` | `float` | Coefficient of determination |

**Validation:** `rmse >= 0`, `mae >= 0`, `r_squared` in `[-inf, 1.0]`.

### `HoldoutValidationResult`

Result of validating calibrated parameters against held-out targets.

| Field | Type | Description |
|-------|------|-------------|
| `holdout_targets` | `tuple[CalibrationTarget, ...]` | Targets used for validation |
| `predictions` | `dict[str, float]` | Model predictions for each target |
| `fit_metrics` | `FitMetrics` | Out-of-sample fit |
| `comparisons` | `tuple[RateComparison, ...]` | Per-target observed vs predicted |

**Methods:** `to_governance_entry() -> dict`.

---

## Governance Layer

> `from reformlab.governance import RunManifest`

Source: `src/reformlab/governance/manifest.py`

Every simulation run produces a manifest that records what happened and why. This is the core of ReformLab's "assumption transparency" guarantee.

### `RunManifest`

Immutable record of a complete simulation run.

| Field | Type | Description |
|-------|------|-------------|
| `manifest_id` | `str` | Content-addressable hash |
| `adapter_version` | `str` | Computation backend version |
| `population_source` | `str` | Where population data came from |
| `scenario_id` | `str` | Scenario content hash |
| `start_year` | `int` | First simulation year |
| `end_year` | `int` | Last simulation year |
| `seed` | `int?` | Random seed used |
| `assumptions` | `tuple[AssumptionEntry, ...]` | All assumptions made during the run |
| `mappings` | `tuple[MappingEntry, ...]` | Variable mappings applied |
| `integrity_hash` | `str?` | SHA-256 of manifest content |
| `created_at` | `str` | ISO 8601 timestamp |

**Methods:**

- `to_json() -> str` — Serialize to JSON
- `from_json(data: str) -> RunManifest` — Deserialize
- `compute_integrity_hash() -> str` — SHA-256 of deterministic content
- `verify_integrity() -> bool` — Check hash matches content
- `with_integrity_hash() -> RunManifest` — Return copy with computed hash

### `AssumptionEntry` (TypedDict)

| Key | Type | Description |
|-----|------|-------------|
| `category` | `str` | e.g. `"data"`, `"model"`, `"policy"` |
| `description` | `str` | What was assumed |
| `source` | `str` | Where this assumption comes from |

### `MappingEntry` (TypedDict)

| Key | Type | Description |
|-----|------|-------------|
| `source_field` | `str` | Original field name |
| `target_field` | `str` | Mapped field name |
| `transform` | `str` | Transformation applied |

---

## Template Layer

> `from reformlab.templates.schema import PolicyType, PolicyParameters, BaselineScenario, ReformScenario`

Source: `src/reformlab/templates/schema.py`

### `PolicyType` (Enum)

| Value | Description |
|-------|-------------|
| `carbon_tax` | Carbon tax on emissions |
| `subsidy` | Technology adoption subsidy |
| `rebate` | Revenue redistribution rebate |
| `feebate` | Fee-and-rebate combination |

### `PolicyParameters` (Base)

Base frozen dataclass for all policy parameters.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rate_schedule` | `dict[int, float]` | `{}` | Year → rate mapping |
| `exemptions` | `tuple[str, ...]` | `()` | Exempted categories |
| `thresholds` | `tuple[float, ...]` | `()` | Threshold values |
| `covered_categories` | `tuple[str, ...]` | `()` | Categories this policy covers |

**Subclasses:** `CarbonTaxParameters`, `SubsidyParameters`, `RebateParameters`, `FeebateParameters` — each may add type-specific fields.

### `BaselineScenario`

A complete baseline scenario template.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Scenario name |
| `policy_type` | `PolicyType` | Type of policy |
| `year_schedule` | `YearSchedule` | Start/end years |
| `policy` | `PolicyParameters` | Default parameters |
| `description` | `str` | Description |

### `ReformScenario`

A reform scenario that references a baseline.

| Field | Type | Description |
|-------|------|-------------|
| (inherits BaselineScenario fields) | | |
| `baseline_ref` | `str` | Name of the baseline scenario |

### `YearSchedule`

| Field | Type | Description |
|-------|------|-------------|
| `start_year` | `int` | First year |
| `end_year` | `int` | Last year |

---

## Population Layer

> `from reformlab.population import PopulationPipeline, MergeConfig, SourceCache`

### Pipeline Types

| Type | Description |
|------|-------------|
| `SourceConfig` | Data source download configuration (provider, dataset, cache settings) |
| `CacheStatus` | Whether a source is cached, stale, or missing |
| `MergeConfig` | Merge operation configuration (seed) |
| `MergeResult` | Merged table + assumption record |
| `MergeAssumption` | Structured assumption (method, description) |
| `IPFConstraint` | Marginal constraint for IPF (dimension + target distribution) |
| `IPFResult` | IPF convergence diagnostics (iterations, max deviation, converged) |

### Module Public API

```python
from reformlab.population import (
    # Pipeline
    PopulationPipeline,
    SourceCache,
    # Loaders
    get_insee_loader, get_eurostat_loader, get_ademe_loader, get_sdes_loader,
    make_insee_config, make_eurostat_config, make_ademe_config, make_sdes_config,
    # Merge methods
    UniformMergeMethod, IPFMergeMethod, ConditionalSamplingMethod,
    # Types
    MergeConfig, IPFConstraint,
    # Catalogs
    INSEE_CATALOG, EUROSTAT_CATALOG, ADEME_CATALOG, SDES_CATALOG,
    # Validation
    PopulationValidator, MarginalConstraint,
    # Errors
    PipelineError, PipelineConfigError, DataSourceError,
)
```
