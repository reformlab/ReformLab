# Story 23.3: Normalize live OpenFisca results into the stable app-facing output schema

Status: ready-for-dev

## Story

As a platform developer,
I want a normalization boundary that maps live OpenFisca output variables into the stable app-facing schema used by indicators, comparison, and export flows,
so that downstream consumers continue working without branching on runtime mode or knowing about OpenFisca variable names.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P0
**Estimate:** 8 SP
**Dependencies:** Story 23.1 (runtime-mode contract), Story 23.2 (population resolver)

## Acceptance Criteria

1. Given a successful live OpenFisca run, when results are packaged for the app, then they conform to the stable normalized output schema used by existing result consumers.
2. Given a normalized result payload, when inspected, then it includes run/scenario identifiers, runtime mode, simulation mode, and executed population provenance alongside the normalized result data required by existing consumers.
3. Given an existing indicator or comparison flow, when it consumes normalized live results, then it behaves without requiring a runtime-specific code path.
4. Given a mapping or schema mismatch during normalization, when detected, then the error identifies the offending field or mapping boundary clearly.
5. Given replay-mode results, when packaged, then they also conform to the same normalized output schema.

## Tasks / Subtasks

### Task 1: Define NormalizedOutputSchema and normalization contract (AC: 1, 2)

- [ ] **Create `src/reformlab/computation/result_normalizer.py`** (AC: 1, 2)
  - [ ] Define `NormalizedOutputSchema` frozen dataclass:
    - `run_id: str` — unique run identifier
    - `scenario_id: str` — scenario identifier
    - `runtime_mode: Literal["live", "replay"]` — execution path mode (Story 23.1)
    - `simulation_mode: str` — "annual" or "horizon_step" (from ScenarioConfig)
    - `population_id: str | None` — executed population reference
    - `population_source: str | None` — "bundled" / "uploaded" / "generated" (Story 23.2)
    - `adapter_version: str` — adapter version from ComputationResult
    - `panel: PanelOutput` — the normalized panel data
    - `manifest: RunManifest` — full governance manifest
    - `metadata: dict[str, Any]` — additional execution metadata
  - [ ] Define `NormalizationError` exception class with `{"what", "why", "fix"}` pattern

### Task 2: Implement output variable mapping layer (AC: 1, 4)

- [ ] **Build normalization logic in `result_normalizer.py`** (AC: 1, 4)
  - [ ] Define `_DEFAULT_OUTPUT_MAPPING: dict[str, str]` — hardcoded default mapping from common OpenFisca variable names to project schema names:
    - `"revenu_disponible"` → `"disposable_income"`
    - `"irpp"` → `"income_tax"`
    - `"impots_directs"` → `"direct_taxes"`
    - `"revenu_net"` → `"net_income"`
    - `"menage"`/`"individu"` entity-level variables → household-level aggregation
  - [ ] Implement `normalize_computation_result(comp_result: ComputationResult, mapping_config: MappingConfig | None, runtime_mode: str) -> pa.Table`:
    - If `mapping_config` is provided, use `apply_output_mapping(comp_result.output_fields, mapping_config)`
    - If no `mapping_config`, apply `_DEFAULT_OUTPUT_MAPPING` (rename known OpenFisca names, pass through unknown columns unchanged)
    - Ensure `household_id` column exists (delegate to `_ensure_household_id_column` pattern from `panel.py`)
    - Validate that at least one expected indicator field is present after normalization; raise `NormalizationError` if schema is entirely incompatible
  - [ ] Implement `normalize_entity_tables(comp_result: ComputationResult, mapping_config: MappingConfig | None) -> pa.Table`:
    - When `ComputationResult.entity_tables` has data from multiple entities, merge/flatten to household-level table
    - For the first slice, use the primary entity table (same as current `output_fields` behavior)

### Task 3: Wire normalization into the panel builder (AC: 1, 3, 5)

- [ ] **Extend `PanelOutput.from_orchestrator_result()` to accept a normalizer** (AC: 1, 3, 5)
  - [ ] Add optional `normalizer: Callable[[ComputationResult], pa.Table] | None = None` parameter
  - [ ] When normalizer is provided, apply it to each yearly `ComputationResult` before concatenation
  - [ ] When normalizer is `None`, use current behavior (pass through `output_fields` as-is) — this preserves replay/mock compatibility
  - [ ] Record normalization info in panel metadata: `"normalized": bool`, `"mapping_applied": bool`

### Task 4: Wire normalization into the orchestration path (AC: 1, 2, 5)

- [ ] **Update `_execute_orchestration()` in `api.py`** (AC: 1, 2, 5)
  - [ ] Build normalizer function based on `run_config.runtime_mode`:
    - `live` mode → normalizer applies `_DEFAULT_OUTPUT_MAPPING` (and optional `MappingConfig` if available)
    - `replay` mode → no normalization (passthrough) — replay results already use app-facing names
  - [ ] Pass normalizer to `PanelOutput.from_orchestrator_result()` call (line 1850)
  - [ ] Pass `population_id` and `population_source` through from `ScenarioConfig` to `NormalizedOutputSchema`

### Task 5: Wire normalization into the server run route (AC: 1, 2)

- [ ] **Update `run_simulation()` in `routes/runs.py`** (AC: 1, 2)
  - [ ] After `_execute_orchestration()` returns `SimulationResult`, wrap it in `NormalizedOutputSchema` if not already
  - [ ] Ensure `population_id` and `population_source` are available in the normalization path

### Task 6: Tests — unit tests for normalizer (AC: 1, 3, 4, 5)

- [ ] **Create `tests/computation/test_result_normalizer.py`** (AC: 1, 3, 4, 5)
  - [ ] `TestNormalizedOutputSchema`:
    - `test_schema_fields_present()` — all required fields exist and are typed correctly
    - `test_schema_is_frozen()` — cannot mutate after construction
  - [ ] `TestNormalizeComputationResult`:
    - `test_renames_known_openfisca_variables()` — `"revenu_disponible"` → `"disposable_income"`
    - `test_passes_through_unknown_columns()` — columns not in mapping are preserved
    - `test_with_explicit_mapping_config()` — uses `MappingConfig` when provided
    - `test_without_mapping_uses_defaults()` — uses `_DEFAULT_OUTPUT_MAPPING`
    - `test_raises_on_empty_or_incompatible_schema()` — `NormalizationError` when no recognizable columns
    - `test_error_has_what_why_fix()` — error detail follows project pattern
  - [ ] `TestNormalizeEntityTables`:
    - `test_primary_entity_used_when_no_entity_tables()` — falls back to `output_fields`
    - `test_entity_tables_merged_to_household_level()` — future multi-entity support
  - [ ] `TestRuntimeModeBehavior`:
    - `test_live_mode_applies_normalization()` — live uses normalizer
    - `test_replay_mode_skips_normalization()` — replay passes through as-is
    - `test_both_modes_produce_same_column_names()` — both produce `household_id`, `year`, `income`, etc.

### Task 7: Tests — integration with panel builder (AC: 1, 3)

- [ ] **Extend `tests/orchestrator/test_panel.py`** (AC: 1, 3)
  - [ ] `TestPanelBuilderWithNormalizer`:
    - `test_from_orchestrator_result_applies_normalizer()` — normalizer function is called per year
    - `test_normalizer_preserves_decision_columns()` — decision columns from Story 14-6 survive normalization
    - `test_panel_metadata_records_normalization()` — metadata includes `"normalized": true`
    - `test_no_normalizer_preserves_current_behavior()` — without normalizer, behavior is unchanged (regression)

### Task 8: Tests — regression for indicators and comparison (AC: 3)

- [ ] **Create `tests/computation/test_normalization_regression.py`** (AC: 3)
  - [ ] `TestIndicatorCompatibilityWithNormalizedOutput`:
    - `test_distributional_indicators_accept_normalized_live_output()` — default config (`income_field="income"`) works
    - `test_welfare_indicators_accept_normalized_live_output()` — default config (`welfare_field="disposable_income"`) works
    - `test_fiscal_indicators_accept_normalized_live_output()` — auto-detects fiscal columns
  - [ ] `TestComparisonWithMixedRuntimeModes`:
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

**Existing Infrastructure to Reuse**

1. **`apply_output_mapping(table, config)`** in `mapping.py:277` — already renames OpenFisca columns to project names given a `MappingConfig`. This is the core function.
2. **`MappingConfig`** — field mapping with `output_mappings` property, YAML loading, validation
3. **`_DEFAULT_OUTPUT_MAPPING`** — NEW: hardcoded fallback for the most common OpenFisca variable names when no YAML mapping file is provided
4. **`PanelOutput.from_orchestrator_result()`** — already iterates yearly states and concatenates. Add optional normalizer callback.
5. **`_ensure_household_id_column()`** in `panel.py:342` — already handles household_id normalization

**Key Design Decision: Where to Normalize**

Normalize at the **ComputationResult → PanelOutput** boundary, NOT inside the adapter. This keeps:
- `ComputationAdapter` protocol unchanged
- Adapter producing raw OpenFisca variable names (its job)
- Normalization logic in one place (panel builder)
- Replay/mock paths unaffected (they already use app-facing names)

**What the Normalized Schema Looks Like**

The normalized panel table must have at minimum these columns for indicators to work with default configs:

| Column | Type | Consumer |
|--------|------|----------|
| `household_id` | int64 | panel joins, comparison |
| `year` | int64 | year grouping, fiscal indicators |
| `income` | float64 | distributional indicators (default `income_field`) |
| `disposable_income` | float64 | welfare indicators (default `welfare_field`) |
| `carbon_tax` | float64 | fiscal indicators (auto-detected by `_rev_suffixes`) |

The `SimpleCarbonTaxAdapter` already produces exactly these columns. The normalization layer ensures live OpenFisca results produce the same columns.

### Source Tree Components

**New files to create:**

| File Path | Purpose |
|-----------|---------|
| `src/reformlab/computation/result_normalizer.py` | Normalization boundary: schema, mapping, error types |
| `tests/computation/test_result_normalizer.py` | Unit tests for normalizer |
| `tests/computation/test_normalization_regression.py` | Regression tests for indicator/comparison compatibility |

**Files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/orchestrator/panel.py` | Panel builder | Add optional `normalizer` parameter to `from_orchestrator_result()` |
| `src/reformlab/interfaces/api.py` | API entry point | Build normalizer based on runtime_mode, pass to panel builder |
| `src/reformlab/server/routes/runs.py` | Server run route | Wire population_id/population_source into normalization path |

### Implementation Notes

**Default OpenFisca-to-Project Mapping**

```python
# src/reformlab/computation/result_normalizer.py

from __future__ import annotations

# Mapping from common OpenFisca-France variable names to project schema names.
# Used as fallback when no MappingConfig YAML file is provided.
# Only output-direction mappings are included.
_DEFAULT_OUTPUT_MAPPING: dict[str, str] = {
    "revenu_disponible": "disposable_income",
    "irpp": "income_tax",
    "impots_directs": "direct_taxes",
    "revenu_net": "net_income",
    "revenu_brut": "gross_income",
    "prestations_sociales": "social_benefits",
    "taxe_carbone": "carbon_tax",
}
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

        # NEW: Apply normalization if provided
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
    create_live_normalizer,
)

# Build normalizer based on runtime mode
if run_config.runtime_mode == "live":
    normalizer = create_live_normalizer(mapping_config=None)
else:
    normalizer = None  # replay path: already uses app-facing names

panel_output = PanelOutput.from_orchestrator_result(
    orchestrator_result,
    normalizer=normalizer,
)
```

**Error Example**

When normalization detects an incompatible schema:
```json
{
  "what": "Output normalization failed",
  "why": "Live OpenFisca result has no recognizable output columns. Available: [ncc, agec, ageq]. Expected at least one of: revenu_disponible, irpp, revenu_net, or a custom MappingConfig.",
  "fix": "Provide a MappingConfig YAML file that maps OpenFisca variable names to project schema fields, or verify that the adapter's output_variables configuration includes the expected variables."
}
```

### Testing Standards

- Follow `tests/{subsystem}/` mirror structure
- `tests/computation/test_result_normalizer.py` — unit tests for normalization logic
- `tests/computation/test_normalization_regression.py` — regression proving indicators work
- Extend `tests/orchestrator/test_panel.py` — integration with panel builder
- Use `MockAdapter` for all tests; no real OpenFisca required
- Build PyArrow tables inline for test fixtures

### Project Structure Notes

- New module `src/reformlab/computation/result_normalizer.py` stays within the computation subsystem (behind adapter boundary, no OpenFisca imports)
- Normalization is a **pure transformation** on PyArrow tables — no I/O, no state
- The normalizer is a **callable** (`Callable[[ComputationResult], pa.Table]`) so it can be composed, tested independently, and optionally injected
- Replay/mock paths are completely unaffected — they pass `normalizer=None`

### Scope Boundaries

**In scope:**
- Default mapping for common OpenFisca-France variables
- Normalization boundary at ComputationResult → PanelOutput
- `NormalizedOutputSchema` type definition
- Error handling for incompatible schemas
- Integration with panel builder and API path
- Regression tests for indicator/comparison compatibility

**Out of scope (future stories):**
- YAML mapping file discovery/loading per template (just accept optional `MappingConfig`)
- Multi-entity aggregation (flatten to primary entity for first slice)
- Policy-specific variable mapping (template `compute.py` produces extra columns that are already in project namespace)
- Normalization of input data (input mapping is separate from output normalization)
- Frontend changes (Story 23.3 is backend-only)

### References

- Epic 23 Story 23.3: `_bmad-output/planning-artifacts/epics.md` (Story 23.3 definition)
- Story 23.1: Runtime mode contract — `src/reformlab/computation/types.py:10-11` (`RuntimeMode`), `src/reformlab/interfaces/api.py:89-91` (`RunConfig.runtime_mode`)
- Story 23.2: Population resolver — `src/reformlab/server/population_resolver.py` (`ResolvedPopulation.source`)
- Existing mapping infrastructure: `src/reformlab/computation/mapping.py:277` (`apply_output_mapping`), `src/reformlab/computation/mapping.py:52-83` (`MappingConfig`)
- Panel builder: `src/reformlab/orchestrator/panel.py:64-137` (`PanelOutput.from_orchestrator_result`)
- API orchestration: `src/reformlab/interfaces/api.py:1715-1891` (`_execute_orchestrator`)
- SimpleCarbonTaxAdapter: `src/reformlab/interfaces/api.py:464-678` — defines the expected output schema
- Indicator defaults: `src/reformlab/interfaces/api.py:186` (`income_field="income"`), `:214` (`welfare_field="disposable_income"`)
- Project Context: `_bmad-output/project-context.md` — frozen dataclasses, PyArrow-first, error pattern
- Antipatterns: `[ANTIPATTERNS]` — Story 23.1 lessons on ownership boundaries and field placement

## Dev Agent Record

### Agent Model Used

(To be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
