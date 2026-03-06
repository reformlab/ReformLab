
# Story 13.2: Implement vehicle malus template (new built-in)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want a built-in vehicle malus (emission penalty) template that computes penalties for high-emission vehicles based on configurable emission thresholds,
so that I can model the French _malus écologique_ and similar vehicle emission penalty policies in scenarios, portfolios, and multi-year projections.

## Acceptance Criteria

1. **AC1: VehicleMalusParameters dataclass** — Given a `VehicleMalusParameters` frozen dataclass subclassing `PolicyParameters`, when registered via the Story 13.1 custom template API (`register_policy_type("vehicle_malus")` + `register_custom_template()`), then `infer_policy_type()` resolves instances to `"vehicle_malus"`, and the class is usable in `BaselineScenario`, `ReformScenario`, `PolicyConfig`, and `PolicyPortfolio`.

2. **AC2: Malus computation** — Given a population table with `household_id` (int64), `income` (float64), and `vehicle_emissions_gkm` (float64) columns, when `compute_vehicle_malus()` is called with `VehicleMalusParameters`, then:
   - Households with `vehicle_emissions_gkm > emission_threshold` pay a malus of `(vehicle_emissions_gkm - emission_threshold) * malus_rate_per_gkm` EUR.
   - Households with `vehicle_emissions_gkm <= emission_threshold` pay 0.
   - The function returns a `VehicleMalusResult` frozen dataclass containing `household_ids`, `malus_amount`, `income_decile`, `total_revenue`, `year`, and `template_name`.
   - Income deciles (1–10) are assigned using the existing `assign_income_deciles()` utility.

3. **AC3: Year-indexed schedules** — Given `VehicleMalusParameters` with a `rate_schedule` mapping years to `malus_rate_per_gkm` values and a `threshold_schedule` mapping years to emission thresholds, when `compute_vehicle_malus()` is called for year `t`, then the computation uses `rate_schedule[t]` as the per-gCO2/km rate and `threshold_schedule[t]` as the emission threshold for that year. If a year is missing from a schedule, computation raises a clear error identifying the missing year.

4. **AC4: Decile aggregation** — Given a `VehicleMalusResult`, when `aggregate_vehicle_malus_by_decile()` is called, then it returns a `VehicleMalusDecileResults` frozen dataclass with per-decile `household_count`, `mean_malus`, and `total_malus` tuples (10 entries each, deciles 1–10).

5. **AC5: Batch and comparison** — Given multiple vehicle malus scenarios (e.g., different threshold/rate combinations), when `run_vehicle_malus_batch()` and `compare_vehicle_malus_decile_impacts()` are called, then:
   - Batch executes all scenarios on the same population and returns `dict[str, VehicleMalusResult]`.
   - Comparison produces a `ComparisonResult` with per-scenario `VehicleMalusDecileResults` and a wide-format `pa.Table`.

6. **AC6: Template YAML pack** — Given at least 2 YAML variant files in `src/reformlab/templates/packs/vehicle_malus/`, when loaded via `load_vehicle_malus_template()`, then each returns a `BaselineScenario` with `VehicleMalusParameters` policy and `policy_type.value == "vehicle_malus"`. YAML round-trip (dump → reload) preserves all field values.

7. **AC7: Portfolio composition** — Given a `VehicleMalusParameters` policy in a `PolicyConfig`, when added to a `PolicyPortfolio` alongside a carbon tax and a subsidy template, then: (a) portfolio construction succeeds, (b) `validate_compatibility()` detects conflicts using the same rules as built-in types, (c) `PortfolioComputationStep` passes malus parameters to the adapter via `asdict()`.

## Tasks / Subtasks

- [ ] **Task 1: Define VehicleMalusParameters and register** (AC: #1)
  - [ ] 1.1 Create `src/reformlab/templates/vehicle_malus/__init__.py` with module docstring and exports
  - [ ] 1.2 Create `src/reformlab/templates/vehicle_malus/compute.py` with `VehicleMalusParameters` frozen dataclass:
    - Fields: `emission_threshold: float = 118.0` (default: 2025 French threshold), `malus_rate_per_gkm: float = 50.0` (EUR per gCO2/km above threshold), `threshold_schedule: dict[int, float] = field(default_factory=dict)` (year → threshold override)
    - Inherits `rate_schedule`, `exemptions`, `thresholds`, `covered_categories` from `PolicyParameters`
    - `rate_schedule` maps year → `malus_rate_per_gkm` for year-indexed overrides
    - `threshold_schedule` maps year → `emission_threshold` for year-indexed overrides
  - [ ] 1.3 Add auto-registration in module `__init__.py`: call `register_policy_type("vehicle_malus")` and `register_custom_template()` at import time
  - [ ] 1.4 Verify `infer_policy_type()` resolves `VehicleMalusParameters` → `"vehicle_malus"`

- [ ] **Task 2: Implement compute_vehicle_malus()** (AC: #2, #3)
  - [ ] 2.1 Implement `compute_vehicle_malus(population, policy, year, template_name) -> VehicleMalusResult`
  - [ ] 2.2 Define `VehicleMalusResult` frozen dataclass with fields: `household_ids: pa.Array`, `malus_amount: pa.Array`, `vehicle_emissions: pa.Array`, `income_decile: pa.Array`, `total_revenue: float`, `year: int`, `template_name: str`
  - [ ] 2.3 Implement year-indexed lookup: use `rate_schedule.get(year, policy.malus_rate_per_gkm)` for rate, `threshold_schedule.get(year, policy.emission_threshold)` for threshold — raise error if neither default nor year-specific value is available
  - [ ] 2.4 Implement malus formula: `max(0, (emissions_gkm - threshold)) * rate_per_gkm` per household
  - [ ] 2.5 Handle missing `vehicle_emissions_gkm` column gracefully: treat as 0 emissions (no malus)
  - [ ] 2.6 Use `assign_income_deciles()` from `reformlab.templates.carbon_tax.compute` for decile assignment

- [ ] **Task 3: Implement decile aggregation** (AC: #4)
  - [ ] 3.1 Implement `aggregate_vehicle_malus_by_decile(result) -> VehicleMalusDecileResults`
  - [ ] 3.2 Define `VehicleMalusDecileResults` frozen dataclass with `decile`, `household_count`, `mean_malus`, `total_malus` tuple fields
  - [ ] 3.3 Follow the exact pattern from `feebate/compute.py:aggregate_feebate_by_decile()` — iterate deciles 1–10, compute mean and total per group

- [ ] **Task 4: Implement batch and comparison** (AC: #5)
  - [ ] 4.1 Create `src/reformlab/templates/vehicle_malus/compare.py`
  - [ ] 4.2 Implement `run_vehicle_malus_batch(population, scenarios, year) -> dict[str, VehicleMalusResult]` — follow `feebate/compare.py:run_feebate_batch()` pattern, validate `isinstance(scenario.policy, VehicleMalusParameters)`
  - [ ] 4.3 Implement `compare_vehicle_malus_decile_impacts(results) -> ComparisonResult` — follow feebate comparison pattern with wide-format table
  - [ ] 4.4 Implement `vehicle_malus_decile_results_to_table(decile_results) -> pa.Table` conversion utility
  - [ ] 4.5 Define `ComparisonResult` frozen dataclass (or reuse naming convention from feebate)

- [ ] **Task 5: Create YAML template pack** (AC: #6)
  - [ ] 5.1 Create directory `src/reformlab/templates/packs/vehicle_malus/`
  - [ ] 5.2 Create `vehicle-malus-french-2026.yaml` — French 2026 barème simplified: threshold 108 gCO2/km, progressive rate starting at ~50 EUR/gkm, 11-year schedule 2026–2036 with tightening thresholds
  - [ ] 5.3 Create `vehicle-malus-flat-rate.yaml` — Simple flat-rate variant: fixed threshold 120 gCO2/km, fixed rate 50 EUR/gkm, 11-year constant schedule
  - [ ] 5.4 Add `README.md` to pack directory documenting variants
  - [ ] 5.5 Add `list_vehicle_malus_templates()`, `load_vehicle_malus_template()`, `get_vehicle_malus_pack_dir()` to `packs/__init__.py` — follow exact pattern of existing packs but use custom type registration for policy_type validation
  - [ ] 5.6 Export new pack functions from `src/reformlab/templates/packs/__init__.py` and add to `__all__`

- [ ] **Task 6: Export from templates package** (AC: #1, #5)
  - [ ] 6.1 Export `VehicleMalusParameters`, `VehicleMalusResult`, `VehicleMalusDecileResults`, `ComparisonResult`, computation functions, and pack utilities from `src/reformlab/templates/vehicle_malus/__init__.py`
  - [ ] 6.2 Ensure `vehicle_malus` module is importable via `from reformlab.templates.vehicle_malus import ...`
  - [ ] 6.3 Add pack loading functions to `src/reformlab/templates/__init__.py` exports and `__all__`

- [ ] **Task 7: Write comprehensive tests** (AC: #1–#7)
  - [ ] 7.1 Create `tests/templates/vehicle_malus/__init__.py`
  - [ ] 7.2 Create `tests/templates/vehicle_malus/conftest.py` with fixtures: `sample_population` (10 households with varying emissions), `small_population` (3 households), parameter fixtures (flat rate, French-style progressive)
  - [ ] 7.3 Create `tests/templates/vehicle_malus/test_compute.py` with test classes:
    - `TestVehicleMalusParameters`: frozen, inherits PolicyParameters, custom fields accessible
    - `TestComputeVehicleMalus`: basic computation, above/below threshold, zero emissions, missing column, year-indexed rates, year-indexed thresholds, total revenue correctness, income decile assignment
    - `TestVehicleMalusResult`: frozen, fields present
    - `TestAggregateVehicleMalusByDecile`: mean/total per decile, empty decile handling
  - [ ] 7.4 Create `tests/templates/vehicle_malus/test_compare.py` with test classes:
    - `TestRunVehicleMalusBatch`: single scenario, multiple scenarios, wrong policy type raises
    - `TestCompareVehicleMalusDecileImpacts`: comparison result structure, wide-format table columns
  - [ ] 7.5 Create `tests/templates/vehicle_malus/test_pack.py` with tests:
    - `TestVehicleMalusPack`: list templates, load template, YAML round-trip, load nonexistent raises
  - [ ] 7.6 Add portfolio integration test: vehicle malus + carbon tax + subsidy in portfolio, validate_compatibility detects overlapping categories
  - [ ] 7.7 Add YAML loading test: load custom type YAML, verify VehicleMalusParameters instance with correct field values
  - [ ] 7.8 Run `uv run ruff check src/ tests/` and `uv run mypy src/`
  - [ ] 7.9 Run `uv run pytest tests/ -x` to verify no regressions

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclasses are NON-NEGOTIABLE:**
```python
from __future__ import annotations
from dataclasses import dataclass, field
from reformlab.templates.schema import PolicyParameters

@dataclass(frozen=True)
class VehicleMalusParameters(PolicyParameters):
    """Vehicle malus (penalty) for high-emission vehicles.

    Models the French malus écologique and similar emission-based
    vehicle registration penalties.
    """
    emission_threshold: float = 118.0  # gCO2/km (2025 French default)
    malus_rate_per_gkm: float = 50.0   # EUR per gCO2/km above threshold
    threshold_schedule: dict[int, float] = field(default_factory=dict)
```

**`from __future__ import annotations`** on every file. Use `if TYPE_CHECKING:` guards for type-only imports. [Source: docs/project-context.md#Python Language Rules]

**PyArrow is the canonical data type** — all computation uses `pa.Table`, `pa.Array`, `pc.compute` operations. No pandas in core logic. [Source: docs/project-context.md#Critical Don't-Miss Rules]

**Subsystem-specific exceptions** — Use `TemplateError` from `reformlab.templates.exceptions` for registration errors. Never raise bare `Exception` or `ValueError` for domain errors. [Source: docs/project-context.md#Python Language Rules]

**Logging** — use `logging.getLogger(__name__)` with structured key=value format. [Source: docs/project-context.md#Code Quality & Style Rules]

### Existing Code Patterns to Follow

**Feebate as primary reference model.** The vehicle malus template is structurally very similar to the feebate template — both compute a penalty based on a metric value (vehicle emissions) relative to a threshold. Key differences:
- Feebate has both fee (above pivot) AND rebate (below pivot); vehicle malus is penalty-only (no rebate for low-emission vehicles).
- Vehicle malus uses year-indexed schedules for both rate AND threshold (threshold tightens over time per French policy).

**Compute module pattern** — Follow `src/reformlab/templates/feebate/compute.py`:
1. Define Result frozen dataclass with `pa.Array` per-household fields + scalar aggregates
2. Define DecileResults frozen dataclass with `tuple[int, ...]` / `tuple[float, ...]` per-decile fields
3. Main `compute_*()` function takes `(population: pa.Table, policy, year, template_name)` → Result
4. `aggregate_*_by_decile(result)` → DecileResults
5. Use `assign_income_deciles()` from `reformlab.templates.carbon_tax.compute` for decile assignment

**Compare module pattern** — Follow `src/reformlab/templates/feebate/compare.py`:
1. `run_*_batch(population, scenarios, year)` — validates policy type, runs each scenario
2. `compare_*_decile_impacts(results)` — aggregates by decile, builds wide-format `pa.Table`
3. `*_decile_results_to_table(decile_results)` — conversion utility
4. Own `ComparisonResult` frozen dataclass per module (not shared)

**Pack loader pattern** — Follow `src/reformlab/templates/packs/__init__.py`:
1. `list_vehicle_malus_templates()` — glob `*.yaml` in pack dir
2. `load_vehicle_malus_template(variant_name)` — load + type-check `BaselineScenario`
3. `get_vehicle_malus_pack_dir()` → `Path`

**IMPORTANT: Custom type registration at module import time.** Since vehicle malus is a custom policy type (not a built-in `PolicyType` enum member), the `vehicle_malus/__init__.py` must register the type when imported. This means:
- `register_policy_type("vehicle_malus")` runs at module level
- `register_custom_template("vehicle_malus", VehicleMalusParameters)` runs at module level
- The `packs/__init__.py` loader must `import reformlab.templates.vehicle_malus` before attempting to load YAML files (to ensure registration happens)
- Test cleanup: tests importing this module do NOT need the autouse cleanup fixture from Story 13.1 tests — the registration happens once at import and is stable. However, if tests define their own custom types, they should still clean up.

### Vehicle Malus Policy Context (French _Malus Écologique_)

The French vehicle malus is a one-time registration tax on new vehicles based on CO2 emissions:

- **2026 barème:** Starts at 108 gCO2/km (50 EUR), scales sharply to 80,000 EUR at 192+ gCO2/km
- **Progressive tightening:** Threshold decreases annually (was 118 in 2024, 113 in 2025, 108 in 2026)
- **Simplified model for this template:** Instead of the exact French step-function barème (which has ~80 discrete brackets), the template uses a linear rate model: `malus = max(0, emissions - threshold) * rate_per_gkm`. This is a deliberate simplification appropriate for microsimulation at population scale.
- **Year-indexed schedules** allow modeling the threshold tightening and rate increases over 10+ years.
- **Electric/hydrogen vehicles** are exempt (emissions = 0, so malus = 0 automatically).

### Source File Touchpoints

| File | Change Type | Purpose |
|------|-------------|---------|
| `src/reformlab/templates/vehicle_malus/__init__.py` | **CREATE** | Module exports + type registration |
| `src/reformlab/templates/vehicle_malus/compute.py` | **CREATE** | VehicleMalusParameters, VehicleMalusResult, VehicleMalusDecileResults, compute_vehicle_malus(), aggregate_vehicle_malus_by_decile() |
| `src/reformlab/templates/vehicle_malus/compare.py` | **CREATE** | ComparisonResult, run_vehicle_malus_batch(), compare_vehicle_malus_decile_impacts(), vehicle_malus_decile_results_to_table() |
| `src/reformlab/templates/packs/vehicle_malus/vehicle-malus-french-2026.yaml` | **CREATE** | French 2026-style template variant |
| `src/reformlab/templates/packs/vehicle_malus/vehicle-malus-flat-rate.yaml` | **CREATE** | Simple flat-rate template variant |
| `src/reformlab/templates/packs/vehicle_malus/README.md` | **CREATE** | Pack documentation |
| `src/reformlab/templates/packs/__init__.py` | **MODIFY** | Add list/load/get functions for vehicle_malus pack |
| `src/reformlab/templates/__init__.py` | **MODIFY** | Export vehicle_malus pack utilities |
| `tests/templates/vehicle_malus/__init__.py` | **CREATE** | Test package |
| `tests/templates/vehicle_malus/conftest.py` | **CREATE** | Population and parameter fixtures |
| `tests/templates/vehicle_malus/test_compute.py` | **CREATE** | Compute unit tests |
| `tests/templates/vehicle_malus/test_compare.py` | **CREATE** | Batch and comparison tests |
| `tests/templates/vehicle_malus/test_pack.py` | **CREATE** | Pack loading and YAML tests |

### Project Structure Notes

- New module at `src/reformlab/templates/vehicle_malus/` — follows the existing pattern of one subdirectory per policy type under `templates/`
- New pack directory at `src/reformlab/templates/packs/vehicle_malus/` — follows the existing pattern of one subdirectory per policy type under `packs/`
- Tests mirror at `tests/templates/vehicle_malus/` — follows the existing pattern
- **No new dependencies required** — uses existing pyarrow, dataclasses, yaml
- **No modifications to orchestrator, adapter, or schema core** — vehicle malus flows through the custom template registration API from Story 13.1

### Key Design Decisions

**1. Linear rate model (NOT step-function barème):**
The French malus uses ~80 discrete brackets with non-linear escalation. This template uses a simplified linear model (`(emissions - threshold) * rate_per_gkm`) which is appropriate for microsimulation because:
- Population-level distributional analysis doesn't require bracket-level precision
- The linear model is composable in portfolios and transparent in manifests
- A future Story 13.4 notebook demo can show how to author a custom template with the exact bracket logic if needed

**2. Year-indexed dual schedules:**
Unlike other templates that only have `rate_schedule`, vehicle malus needs BOTH rate and threshold to vary by year (the French threshold tightens annually). The `threshold_schedule` dict provides this. When a year is present in `threshold_schedule`, it overrides the default `emission_threshold`. When a year is present in `rate_schedule`, it overrides the default `malus_rate_per_gkm`.

**3. Registration at import time:**
The vehicle malus type is registered when the module is first imported. This is clean for production use but means tests that import the module will have the type registered automatically. This is the correct behavior — vehicle malus is a "built-in custom" type shipped with the package, not a user-defined type that needs cleanup.

### Cross-Story Dependencies

- **Depends on:** Story 13.1 (custom template authoring API — dev-complete)
- **Blocks:** Story 13.4 (validate custom templates in portfolios + notebook demo)
- **Parallel with:** Story 13.3 (energy poverty aid template — can be developed independently)

### Out of Scope Guardrails

- **Do NOT** implement the exact French step-function barème with 80+ brackets. Use the simplified linear model.
- **Do NOT** implement a weight-based malus (_malus au poids_). That would be a separate template.
- **Do NOT** modify the `ComputationAdapter` protocol or orchestrator core. Vehicle malus flows through existing infrastructure.
- **Do NOT** modify `PolicyType` enum — vehicle malus is registered as a `CustomPolicyType` via the Story 13.1 API.
- **Do NOT** modify the JSON Schema files — custom types bypass JSON Schema validation by design (Story 13.1 decision).
- **Do NOT** build a notebook demo — that is Story 13.4's scope.

### Testing Standards

- **Mirror source structure:** Tests in `tests/templates/vehicle_malus/`
- **Class-based grouping:** `TestVehicleMalusParameters`, `TestComputeVehicleMalus`, `TestAggregateVehicleMalusByDecile`, etc.
- **Fixtures in conftest:** Population tables built inline with PyArrow, parameter fixtures for different scenarios
- **Direct assertions:** Plain `assert`, `pytest.raises(TemplateError, match=...)` for errors
- **No MockAdapter needed:** Vehicle malus compute/compare tests work directly on population tables — no adapter involved (the adapter is only used at orchestrator level, tested in Story 13.1)
- **Coverage target:** >90% for all new code
- **Golden value tests:** At least one test with hand-computed expected values (e.g., household with 160 gCO2/km, threshold 120, rate 50 → malus = (160-120)*50 = 2000 EUR)

### References

- [Source: `src/reformlab/templates/feebate/compute.py` — Primary reference for compute module pattern]
- [Source: `src/reformlab/templates/feebate/compare.py` — Primary reference for compare module pattern]
- [Source: `src/reformlab/templates/feebate/__init__.py` — Module export pattern]
- [Source: `src/reformlab/templates/packs/__init__.py` — Pack loader pattern (list/load/get)]
- [Source: `src/reformlab/templates/packs/feebate/feebate-vehicle-emissions.yaml` — YAML template structure reference]
- [Source: `tests/templates/feebate/conftest.py` — Test fixture pattern (population with vehicle_emissions_gkm)]
- [Source: `src/reformlab/templates/schema.py` — PolicyParameters base class, register_policy_type(), register_custom_template(), CustomPolicyType]
- [Source: `src/reformlab/templates/carbon_tax/compute.py:assign_income_deciles()` — Shared decile utility]
- [Source: `docs/project-context.md` — Frozen dataclasses, PyArrow-first, exception hierarchy, coding standards]
- [Source: `docs/epics.md#Story 13.2` — Acceptance criteria from backlog]
- [Source: `_bmad-output/implementation-artifacts/13-1-define-custom-template-authoring-api-and-registration.md` — Predecessor story with registration API details]
- [Source: https://www.service-public.gouv.fr/particuliers/vosdroits/F35947 — French malus écologique 2026 barème]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- Feebate template identified as primary reference model (closest structural analog to vehicle malus)
- French malus écologique 2026 policy researched: threshold 108 gCO2/km, max 80,000 EUR, progressive scale
- Design decision: linear rate model (NOT step-function barème) for microsimulation appropriateness
- Design decision: dual year-indexed schedules (rate + threshold) for annual policy tightening
- Design decision: import-time registration (vehicle malus is a "built-in custom" shipped type)
- 7 tasks with detailed subtasks covering: parameters, compute, decile aggregation, batch/compare, YAML pack, exports, tests
- 13 source files to create/modify identified
- Cross-story dependencies mapped: 13.1 (done) → 13.2 (this) → 13.4

### File List

- `src/reformlab/templates/vehicle_malus/__init__.py` — CREATE: Module exports + type registration
- `src/reformlab/templates/vehicle_malus/compute.py` — CREATE: Parameters, result types, computation logic
- `src/reformlab/templates/vehicle_malus/compare.py` — CREATE: Batch execution and comparison utilities
- `src/reformlab/templates/packs/vehicle_malus/vehicle-malus-french-2026.yaml` — CREATE: French 2026 variant
- `src/reformlab/templates/packs/vehicle_malus/vehicle-malus-flat-rate.yaml` — CREATE: Flat rate variant
- `src/reformlab/templates/packs/vehicle_malus/README.md` — CREATE: Pack documentation
- `src/reformlab/templates/packs/__init__.py` — MODIFY: Add vehicle_malus pack functions
- `src/reformlab/templates/__init__.py` — MODIFY: Export vehicle_malus pack utilities
- `tests/templates/vehicle_malus/__init__.py` — CREATE: Test package
- `tests/templates/vehicle_malus/conftest.py` — CREATE: Test fixtures
- `tests/templates/vehicle_malus/test_compute.py` — CREATE: Computation tests
- `tests/templates/vehicle_malus/test_compare.py` — CREATE: Batch/comparison tests
- `tests/templates/vehicle_malus/test_pack.py` — CREATE: Pack loading tests
