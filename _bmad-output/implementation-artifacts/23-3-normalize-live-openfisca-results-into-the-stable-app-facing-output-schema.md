# Story 23.3: Normalize live OpenFisca results into the stable app-facing output schema

Status: complete

## Story

As a platform developer,
I want a normalization boundary that maps live OpenFisca output variables into the stable app-facing schema used by indicators, comparison, and export flows,
so that downstream consumers continue working without branching on runtime mode or knowing about OpenFisca variable names.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P0
**Estimate:** 8 SP
**Dependencies:** Story 23.1 (runtime-mode contract), Story 23.2 (population resolver)

## Acceptance Criteria

1. Given a successful live OpenFisca run, when results are packaged for the app, then they conform to the stable normalized output schema (see "Normalized Panel Schema" table in Dev Notes) used by existing result consumers.
2. Given a normalized result payload, when inspected, then `SimulationResult.metadata` contains `runtime_mode`, `normalized`, and `mapping_applied` keys alongside the result data required by existing consumers. Population provenance (`population_id`, `population_source`) is included when available from the run path.
3. Given an existing indicator or comparison flow, when it consumes normalized live results, then it behaves without requiring a runtime-specific code path.
4. Given a mapping or schema mismatch during normalization, when detected, then `NormalizationError` is raised with the standard `{what, why, fix}` error payload. The error is considered triggered when zero columns from `_MINIMUM_REQUIRED_COLUMNS` survive normalization — this is the minimum threshold for downstream compatibility.
5. Given replay-mode results, when packaged, then they conform to the same column schema as live results. Replay mode applies no column renaming but records `"normalized": false, "mapping_applied": false` in panel metadata for consistency.

## Tasks / Subtasks

### Task 1: Create result_normalizer.py with normalization types and functions (AC: 1, 4)

- [x] **Create `src/reformlab/computation/result_normalizer.py`** (AC: 1, 4)
  - [x] Define `NormalizationError` exception class with `{"what", "why", "fix"}` pattern
  - [x] Define `_DEFAULT_OUTPUT_MAPPING: dict[str, str]` — hardcoded default mapping from common OpenFisca variable names to project schema names:
    - `"revenu_disponible"` → `"disposable_income"`
    - `"irpp"` → `"income_tax"`
    - `"impots_directs"` → `"direct_taxes"`
    - `"revenu_net"` → `"net_income"`
    - `"salaire_net"` → `"income"` (canonical income for distributional indicators)
    - `"revenu_brut"` → `"gross_income"`
    - `"prestations_sociales"` → `"social_benefits"`
    - `"taxe_carbone"` → `"carbon_tax"`
  - [x] Define `_MINIMUM_REQUIRED_COLUMNS: frozenset[str] = frozenset({"household_id", "income", "disposable_income", "carbon_tax"})` — at least one of these must survive normalization for the result to be considered compatible
  - [x] Define `NORMALIZED_KEY: str = "normalized"` and `MAPPING_APPLIED_KEY: str = "mapping_applied"` — metadata key constants

### Task 2: Implement normalization logic (AC: 1, 4)

- [x] **Build normalization functions in `result_normalizer.py`** (AC: 1, 4)
  - [x] Implement `normalize_computation_result(comp_result: ComputationResult, mapping_config: MappingConfig | None = None) -> pa.Table`:
    - If `mapping_config` is provided, use `apply_output_mapping(comp_result.output_fields, mapping_config)`
    - If no `mapping_config`, apply `_DEFAULT_OUTPUT_MAPPING` (rename known OpenFisca names, pass through unknown columns unchanged)
    - Ensure `household_id` column exists (delegate to `_ensure_household_id_column` pattern from `panel.py`)
    - Validate that at least one column from `_MINIMUM_REQUIRED_COLUMNS` is present after normalization; raise `NormalizationError` if schema is entirely incompatible
  - [x] Implement `create_live_normalizer(mapping_config: MappingConfig | None = None) -> Callable[[ComputationResult], pa.Table]`:
    - Factory that returns a `Callable[[ComputationResult], pa.Table]` wrapping `normalize_computation_result()`
    - This is the callable passed to `PanelOutput.from_orchestrator_result()`
  - [x] Implement `normalize_entity_tables(comp_result: ComputationResult, mapping_config: MappingConfig | None = None) -> pa.Table`:
    - **First-slice stub**: returns `comp_result.output_fields` directly (multi-entity aggregation deferred to future story)
    - Add `# TODO: multi-entity merge to household-level (future story)` comment

### Task 3: Wire normalization into the panel builder (AC: 1, 3, 5)

- [x] **Extend `PanelOutput.from_orchestrator_result()` to accept a normalizer** (AC: 1, 3, 5)
  - [x] Add optional `normalizer: Callable[[ComputationResult], pa.Table] | None = None` parameter
  - [x] When normalizer is provided, apply it to each yearly `ComputationResult` before concatenation
  - [x] When normalizer is `None`, use current behavior (pass through `output_fields` as-is) — this preserves replay/mock compatibility
  - [x] Record normalization info in panel metadata: `"normalized": bool`, `"mapping_applied": bool`

### Task 4: Wire normalization into the run path (AC: 1, 2, 5)

This task covers both the Python API layer (normalizer construction) and the server layer (metadata assembly). The split is: **normalizer callback runs in `_execute_orchestration()` (api.py)**, **provenance metadata is added by the server route (runs.py)** where `run_id` and population resolver results are available.

- [x] **Update `_execute_orchestration()` in `api.py`** (AC: 1, 5)
  - [x] Build normalizer callable based on `run_config.runtime_mode`:
    - `live` mode → `normalizer = create_live_normalizer(mapping_config=None)`
    - `replay` mode → `normalizer = None` (passthrough — replay results already use app-facing names)
  - [x] Pass normalizer to `PanelOutput.from_orchestrator_result()` call
  - [x] Record `runtime_mode` and `normalized` info in `SimulationResult.metadata`

- [x] **Update `run_simulation()` in `routes/runs.py`** (AC: 1, 2)
  - [x] After `_execute_orchestration()` returns `SimulationResult`, add `population_id` and `population_source` to `result.metadata` (available from population resolver results in the server layer)
  - [x] `SimulationResult` itself is unchanged — normalization metadata flows through `SimulationResult.metadata` dict, not through a new wrapper type

- [x] **Add `population_id` and `population_source` to `ScenarioConfig`** (AC: 2)
  - [x] Add `population_id: str | None = None` and `population_source: str | None = None` to `ScenarioConfig` in `api.py`
  - [x] Update `run_simulation()` in `runs.py` to pass these from resolver results into `ScenarioConfig`

### Task 5: Tests — unit tests for normalizer (AC: 1, 3, 4, 5)

- [x] **Create `tests/computation/test_result_normalizer.py`** (AC: 1, 3, 4, 5)
  - [x] `TestNormalizationError`:
    - `test_error_has_what_why_fix()` — error detail follows project pattern
  - [x] `TestNormalizeComputationResult`:
    - `test_renames_known_openfisca_variables()` — `"revenu_disponible"` → `"disposable_income"`, `"salaire_net"` → `"income"`
    - `test_passes_through_unknown_columns()` — columns not in mapping are preserved
    - `test_with_explicit_mapping_config()` — uses `MappingConfig` when provided
    - `test_without_mapping_uses_defaults()` — uses `_DEFAULT_OUTPUT_MAPPING`
    - `test_raises_on_empty_or_incompatible_schema()` — `NormalizationError` when no columns from `_MINIMUM_REQUIRED_COLUMNS` are present
    - `test_minimum_columns_threshold()` — succeeds when at least one column from `_MINIMUM_REQUIRED_COLUMNS` survives
  - [x] `TestCreateLiveNormalizer`:
    - `test_returns_callable()` — factory returns a function accepting ComputationResult
    - `test_callable_produces_normalized_table()` — applies mapping correctly
  - [x] `TestNormalizeEntityTables`:
    - `test_stub_returns_output_fields()` — first-slice implementation returns `comp_result.output_fields` directly
  - [x] `TestRuntimeModeBehavior`:
    - `test_live_mode_applies_normalization()` — live uses normalizer
    - `test_replay_mode_skips_normalization()` — replay passes through as-is
    - `test_both_modes_produce_same_column_names()` — both produce `household_id`, `year`, `income`, etc.

### Task 6: Tests — integration with panel builder (AC: 1, 3)

- [x] **Extend `tests/orchestrator/test_panel.py`** (AC: 1, 3)
  - [x] `TestPanelBuilderWithNormalizer`:
    - `test_from_orchestrator_result_applies_normalizer()` — normalizer function is called per year
    - `test_normalizer_preserves_decision_columns()` — decision columns from Story 14-6 survive normalization
    - `test_panel_metadata_records_normalization()` — metadata includes `"normalized": true`
    - `test_no_normalizer_preserves_current_behavior()` — without normalizer, behavior is unchanged (regression)

### Task 7: Tests — regression for indicators and comparison (AC: 3)

- [x] **Create `tests/computation/test_normalization_regression.py`** (AC: 3)
  - [x] `TestIndicatorCompatibilityWithNormalizedOutput`:
    - `test_distributional_indicators_accept_normalized_live_output()` — default config (`income_field="income"`) works because `_DEFAULT_OUTPUT_MAPPING` includes `"salaire_net"` → `"income"`
    - `test_welfare_indicators_accept_normalized_live_output()` — default config (`welfare_field="disposable_income"`) works
    - `test_fiscal_indicators_accept_normalized_live_output()` — auto-detects fiscal columns
  - [x] `TestComparisonWithMixedRuntimeModes`:
    - `test_compare_live_vs_replay_results()` — both produce comparable panels
    - `test_no_runtime_branching_in_indicators()` — indicator code does not check runtime_mode

## Dev Notes

### Architecture Patterns

**The Normalization Boundary**

The current data flow from computation to app-facing output is:

```
OpenFisca Adapter → ComputationResult.output_fields (OpenFisca variable names)
  → YearState.data[COMPUTATION_RESULT_KEY]
  → PanelOutput.from_orchestrator_result() (direct concat, NO renaming)
  → SimulationResult.panel_output
  → indicators / comparison / export
```

The gap: OpenFisca returns **French variable names** (e.g., `revenu_disponible`, `irpp`) while the app expects **English schema names** (e.g., `disposable_income`, `income_tax`). The mock adapter (`SimpleCarbonTaxAdapter`) and precomputed data already use English names, so indicators work by default with those paths. Live OpenFisca results break this assumption.

**Design: No New Schema Wrapper**

Normalization provenance is tracked through **existing types**, not a new wrapper dataclass:
- `SimulationResult.metadata` — stores `runtime_mode`, `population_id`, `population_source`, `normalized`, `mapping_applied`
- `PanelOutput.metadata` — stores `normalized`, `mapping_applied`

This avoids creating `NormalizedOutputSchema` (which would import `PanelOutput` from `orchestrator/`, violating the `computation/` → `orchestrator/` layer boundary) and avoids duplicating fields already on `SimulationResult`.

**Existing Infrastructure to Reuse**

1. **`apply_output_mapping(table, config)`** in `mapping.py` — already renames OpenFisca columns to project names given a `MappingConfig`. This is the core function.
2. **`MappingConfig`** — field mapping with `output_mappings` property, YAML loading, validation
3. **`_DEFAULT_OUTPUT_MAPPING`** — NEW: hardcoded fallback for the most common OpenFisca variable names when no YAML mapping file is provided
4. **`PanelOutput.from_orchestrator_result()`** — already iterates yearly states and concatenates. Add optional normalizer callback.
5. **`_ensure_household_id_column()`** in `panel.py` — already handles household_id normalization

**Key Design Decision: Where to Normalize**

Normalize at the **ComputationResult → PanelOutput** boundary, NOT inside the adapter. This keeps:
- `ComputationAdapter` protocol unchanged
- Adapter producing raw OpenFisca variable names (its job)
- Normalization logic in one place (panel builder)
- Replay/mock paths unaffected (they already use app-facing names)

**Normalized Panel Schema**

The normalized panel table must have at minimum these columns for indicators to work with default configs:

| Column | Type | Required | Source for Live OpenFisca | Consumer |
|--------|------|----------|---------------------------|----------|
| `household_id` | int64 | Yes | `_ensure_household_id_column()` | panel joins, comparison |
| `year` | int64 | Yes | Added by panel builder | year grouping, fiscal indicators |
| `income` | float64 | Yes* | `"salaire_net"` → `"income"` in default mapping | distributional indicators (default `income_field`) |
| `disposable_income` | float64 | Yes* | `"revenu_disponible"` → `"disposable_income"` | welfare indicators (default `welfare_field`) |
| `carbon_tax` | float64 | Yes* | `"taxe_carbone"` → `"carbon_tax"` | fiscal indicators (auto-detected) |

\* At least one of these indicator columns must be present after normalization, enforced by `_MINIMUM_REQUIRED_COLUMNS` validation.

Unknown columns not in the mapping are passed through unchanged.

**Metadata Tracking**

Normalization provenance is recorded via these metadata keys (defined as constants in `result_normalizer.py`):

| Key | Location | Type | Description |
|-----|----------|------|-------------|
| `"normalized"` | `PanelOutput.metadata`, `SimulationResult.metadata` | `bool` | Whether normalization was applied |
| `"mapping_applied"` | `PanelOutput.metadata`, `SimulationResult.metadata` | `bool` | Whether a column mapping was applied |
| `"runtime_mode"` | `SimulationResult.metadata` | `str` | `"live"` or `"replay"` |
| `"population_id"` | `SimulationResult.metadata` | `str | None` | Executed population reference (server path only) |
| `"population_source"` | `SimulationResult.metadata` | `str | None` | `"bundled"` / `"uploaded"` / `"generated"` (server path only) |

### Source Tree Components

**New files to create:**

| File Path | Purpose |
|-----------|---------|
| `src/reformlab/computation/result_normalizer.py` | Normalization boundary: mapping, error types, metadata constants |
| `tests/computation/test_result_normalizer.py` | Unit tests for normalizer |
| `tests/computation/test_normalization_regression.py` | Regression tests for indicator/comparison compatibility |

**Files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/orchestrator/panel.py` | Panel builder | Add optional `normalizer` parameter to `from_orchestrator_result()` |
| `src/reformlab/interfaces/api.py` | API entry point | Add `population_id`/`population_source` to `ScenarioConfig`; build normalizer based on runtime_mode; record metadata in `SimulationResult` |
| `src/reformlab/server/routes/runs.py` | Server run route | Pass `population_id`/`population_source` into `ScenarioConfig`; add to result metadata |

### Implementation Notes

**Default OpenFisca-to-Project Mapping**

```python
# src/reformlab/computation/result_normalizer.py

from __future__ import annotations

# Mapping from common OpenFisca-France variable names to project schema names.
# Used as fallback when no MappingConfig YAML file is provided.
# Only output-direction mappings are included.
#
# Mapping precedence: explicit run config MappingConfig > _DEFAULT_OUTPUT_MAPPING
_DEFAULT_OUTPUT_MAPPING: dict[str, str] = {
    "revenu_disponible": "disposable_income",
    "irpp": "income_tax",
    "impots_directs": "direct_taxes",
    "revenu_net": "net_income",
    "salaire_net": "income",
    "revenu_brut": "gross_income",
    "prestations_sociales": "social_benefits",
    "taxe_carbone": "carbon_tax",
}

# Minimum required columns for normalization to succeed.
# At least one of these must be present after normalization.
_MINIMUM_REQUIRED_COLUMNS: frozenset[str] = frozenset({
    "household_id", "income", "disposable_income", "carbon_tax",
})
```

**Panel Builder Extension**

```python
# panel.py — extend from_orchestrator_result()

@classmethod
def from_orchestrator_result(
    cls,
    result: OrchestratorResult,
    normalizer: Callable[[ComputationResult], pa.Table] | None = None,
) -> PanelOutput:
    # ...
    for year in sorted(result.yearly_states.keys()):
        year_state = result.yearly_states[year]
        comp_result = year_state.data.get(COMPUTATION_RESULT_KEY)
        if comp_result is None:
            continue

        # Apply normalization if provided
        if normalizer is not None:
            output_table = normalizer(comp_result)
        else:
            output_table = comp_result.output_fields
        # ... rest of existing logic (decision columns, household_id, year)
```

**Normalization in the API Path**

```python
# api.py — in _execute_orchestration()

from reformlab.computation.result_normalizer import (
    NORMALIZED_KEY,
    MAPPING_APPLIED_KEY,
    create_live_normalizer,
)

# Build normalizer based on runtime mode
if run_config.runtime_mode == "live":
    normalizer = create_live_normalizer(mapping_config=None)
    extra_metadata = {NORMALIZED_KEY: True, MAPPING_APPLIED_KEY: True, "runtime_mode": "live"}
else:
    normalizer = None  # replay path: already uses app-facing names
    extra_metadata = {NORMALIZED_KEY: False, MAPPING_APPLIED_KEY: False, "runtime_mode": "replay"}

panel_output = PanelOutput.from_orchestrator_result(
    orchestrator_result,
    normalizer=normalizer,
)

# ... construct SimulationResult with extra_metadata merged into metadata
```

**Population Provenance in Server Route**

```python
# runs.py — in run_simulation()

# Pass population_id/population_source through ScenarioConfig
scenario_config = ScenarioConfig(
    ...,
    population_id=resolved_population.id,
    population_source=resolved_population.source,
)

result = _execute_orchestration(scenario_config, run_config, adapter)

# Add server-layer provenance to result metadata
result.metadata["population_id"] = resolved_population.id
result.metadata["population_source"] = resolved_population.source
```

**Error Example**

When normalization detects an incompatible schema:
```json
{
  "what": "Output normalization failed",
  "why": "Live OpenFisca result has no recognizable output columns. Available: [ncc, agec, ageq]. Expected at least one of: household_id, income, disposable_income, carbon_tax.",
  "fix": "Provide a MappingConfig YAML file that maps OpenFisca variable names to project schema fields, or verify that the adapter's output_variables configuration includes the expected variables."
}
```

### Testing Standards

- Follow `tests/{subsystem}/` mirror structure
- `tests/computation/test_result_normalizer.py` — unit tests for normalization logic
- `tests/computation/test_normalization_regression.py` — regression proving indicators work with normalized output
- Extend `tests/orchestrator/test_panel.py` — integration with panel builder
- Use `MockAdapter` for all tests; no real OpenFisca required
- Build PyArrow tables inline for test fixtures

### Project Structure Notes

- New module `src/reformlab/computation/result_normalizer.py` stays within the computation subsystem — contains only `pa.Table` transformations, error types, and constants; NO imports from `orchestrator/`
- Normalization is a **pure transformation** on PyArrow tables — no I/O, no state
- The normalizer is a **callable** (`Callable[[ComputationResult], pa.Table]`) so it can be composed, tested independently, and optionally injected
- Replay/mock paths are completely unaffected — they pass `normalizer=None`
- Normalization provenance flows through `SimulationResult.metadata` and `PanelOutput.metadata` — no new wrapper type

### Scope Boundaries

**In scope:**
- Default mapping for common OpenFisca-France variables (including `income` via `"salaire_net"`)
- Normalization boundary at ComputationResult → PanelOutput
- `NormalizationError` with minimum column validation
- Integration with panel builder and API path
- Regression tests for indicator/comparison compatibility
- `population_id`/`population_source` fields on `ScenarioConfig` and metadata flow

**Out of scope (future stories):**
- YAML mapping file discovery/loading per template (just accept optional `MappingConfig`)
- Multi-entity aggregation (flatten to primary entity for first slice — `normalize_entity_tables()` is a stub)
- Policy-specific variable mapping (template `compute.py` produces extra columns that are already in project namespace)
- Normalization of input data (input mapping is separate from output normalization)
- Frontend changes (Story 23.3 is backend-only)
- `simulation_mode` field on `ScenarioConfig` (deferred to future story; not required for normalization correctness)

### References

- Epic 23 Story 23.3: `_bmad-output/planning-artifacts/epics.md` (Story 23.3 definition)
- Story 23.1: Runtime mode contract — `src/reformlab/computation/types.py` (`RuntimeMode`), `src/reformlab/interfaces/api.py` (`RunConfig.runtime_mode`)
- Story 23.2: Population resolver — `src/reformlab/server/population_resolver.py` (`ResolvedPopulation.source`)
- Existing mapping infrastructure: `src/reformlab/computation/mapping.py` (`apply_output_mapping`), `src/reformlab/computation/mapping.py` (`MappingConfig`)
- Panel builder: `src/reformlab/orchestrator/panel.py` (`PanelOutput.from_orchestrator_result`)
- API orchestration: `src/reformlab/interfaces/api.py` (`_execute_orchestration`)
- SimpleCarbonTaxAdapter: `src/reformlab/interfaces/api.py` — defines the expected output schema
- Indicator defaults: `src/reformlab/interfaces/api.py` (`income_field="income"`), (`welfare_field="disposable_income"`)
- Project Context: `_bmad-output/project-context.md` — frozen dataclasses, PyArrow-first, error pattern
- Antipatterns: `[ANTIPATTERNS]` — Story 23.1 lessons on ownership boundaries and field placement

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Opus 4.6 equivalent)

### Debug Log References

None. All acceptance criteria were met without requiring debug sessions.

### Completion Notes List

- **TDD Approach**: Story was executed following red-green-refactor TDD methodology. Tests were written first, then implementation was added to make them pass.

- **Key Implementation Decisions**:
  1. Normalization boundary placed at `ComputationResult → PanelOutput` stage, not inside the adapter
  2. Normalization is a callable that can be injected, allowing replay/mock paths to pass through unchanged
  3. Metadata tracking uses existing `SimulationResult.metadata` and `PanelOutput.metadata` dictionaries, avoiding new wrapper types
  4. Household ID fallback is added after meaningful column validation to ensure minimum required columns are checked first

- **Testing Coverage**:
  - 17 unit tests in `test_result_normalizer.py` covering normalization logic, error handling, and runtime mode behavior
  - 4 integration tests in `test_panel.py` extending panel builder with normalizer support
  - 5 regression tests in `test_normalization_regression.py` proving indicators and comparison work with normalized output without runtime branching

- **Validation Strategy**:
  - Minimum required columns validation ensures at least one of `household_id`, `income`, `disposable_income`, `carbon_tax` survives normalization
  - `normalize_entity_tables()` is a stub returning `output_fields` directly with TODO comment for future multi-entity aggregation

- **Population Provenance**:
  - `population_id` and `population_source` added to `ScenarioConfig` in `api.py`
  - These fields flow through to `SimulationResult.metadata` from the server layer in `runs.py`
  - Population resolver results are passed from `run_simulation()` into `ScenarioConfig`

- **MockAdapter Fix**:
  - Updated `MockAdapter` default output to include required columns (`household_id`, `income`, `disposable_income`, `carbon_tax`)
  - This ensures existing tests pass with normalization enabled in live mode
  - The default output now matches the expected app-facing schema (English names)

### File List

**New files created:**

| File Path | Purpose | Lines |
|-----------|---------|-------|
| `src/reformlab/computation/result_normalizer.py` | Normalization boundary: mapping, error types, metadata constants | ~160 |
| `tests/computation/test_result_normalizer.py` | Unit tests for normalizer (17 tests) | ~220 |
| `tests/computation/test_normalization_regression.py` | Regression tests for indicator/comparison compatibility (5 tests) | ~220 |

**Files modified:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/orchestrator/panel.py` | Panel builder | Added `normalizer` parameter to `from_orchestrator_result()`; added normalization metadata tracking |
| `src/reformlab/interfaces/api.py` | API entry point | Added `population_id`/`population_source` to `ScenarioConfig`; added normalizer construction based on `runtime_mode`; updated `_execute_orchestration()` and `_run_direct_scenario()` with normalization logic |
| `src/reformlab/server/routes/runs.py` | Server run route | Updated `run_simulation()` and `_run_portfolio()` to pass `population_id`/`population_source` into `ScenarioConfig` |
| `src/reformlab/computation/mock_adapter.py` | Mock adapter | Updated default output to include required columns (`household_id`, `income`, `disposable_income`, `carbon_tax`) to work with normalization in live mode |
| `tests/orchestrator/test_panel.py` | Panel tests | Added `TestPanelBuilderWithNormalizer` class with 4 integration tests |
