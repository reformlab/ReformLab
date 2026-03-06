
# Story 13.4: Validate custom templates in portfolios and build notebook demo

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to compose custom policy templates (vehicle malus, energy poverty aid) into portfolios alongside built-in templates and see a pedagogical notebook demonstrating the full custom template lifecycle,
so that I can confidently author, register, and deploy custom policy templates in production portfolios without consulting external documentation.

## Acceptance Criteria

1. **AC1: Custom template in portfolio execution** — Given a custom template (e.g., `VehicleMalusParameters`) authored and registered via the Story 13.1 API, when added to a `PolicyPortfolio` alongside built-in templates (e.g., `CarbonTaxParameters`, `SubsidyParameters`), then the portfolio constructs successfully, `validate_compatibility()` runs without errors for non-conflicting policies, and `PortfolioComputationStep` passes the custom template's parameters to the adapter via `asdict()` without error.

2. **AC2: Portfolio execution with all Epic 13 templates** — Given a portfolio containing at least one `VehicleMalusParameters` policy, one `EnergyPovertyAidParameters` policy, and one built-in `CarbonTaxParameters` policy, when executed through the orchestrator's `PortfolioComputationStep` with a population containing `household_id`, `income`, `carbon_emissions`, `vehicle_emissions_gkm`, and `energy_expenditure` columns, then all three policies produce per-household results that are merged into a single output table with `{policy_type}_` prefixed columns per the `PortfolioComputationStep` convention (`household_id` preserved as join key, each policy's output columns prefixed by its policy type). Tests must assert non-zero malus and aid totals to confirm the population data actually triggers policy logic.

3. **AC3: Conflict detection for custom templates** — Given a portfolio with two policies of the same custom type (e.g., two `VehicleMalusParameters` with overlapping `rate_schedule` years), when `validate_compatibility()` is called, then it detects both `same_policy_type` and `overlapping_years` conflicts, identical to the behavior for built-in policy types.

4. **AC4: Notebook demo end-to-end** — Given the notebook at `notebooks/demo/epic13_custom_templates.ipynb`, when run in CI via `uv run pytest --nbmake notebooks/demo/epic13_custom_templates.ipynb -v`, then it completes without errors and demonstrates: (a) defining a simple custom template from scratch, (b) registering it via `register_policy_type()` + `register_custom_template()`, (c) using it in a `BaselineScenario`, (d) composing it into a portfolio with built-in templates, (e) running batch comparison using template-specific `run_*_batch()` functions, (f) comparing a portfolio with custom templates against one using only built-in templates.

5. **AC5: Notebook pedagogical quality** — Given the notebook, when read by an analyst unfamiliar with the custom template API, then: (a) every code cell is preceded by a markdown cell with a plain-language explanation, (b) the lifecycle steps are explicitly enumerated (define frozen dataclass → register type → register class → use in scenario/portfolio), (c) sections "Define a Custom Template", "Register and Use", and "Portfolios with Custom Templates" are present as markdown headings, and (d) no external documentation is needed to understand the workflow.

6. **AC6: Static notebook tests** — Given the test file `tests/notebooks/test_epic13_demo_notebook.py`, when run, then it validates: (a) notebook exists at expected path, (b) outputs are cleared (execution_count=None, outputs=[]), (c) uses public API imports only (no `reformlab.computation.*` internals), (d) contains key API calls (`register_policy_type`, `register_custom_template`, `PolicyPortfolio`, `validate_compatibility`), (e) CI workflow includes nbmake execution line.

7. **AC7: YAML round-trip with custom template in portfolio** — Given a `PolicyPortfolio` containing a custom template policy, when serialized via `dump_portfolio()` and reloaded via `load_portfolio()` (with the custom template modules imported beforehand so types are registered), then the round-trip preserves all custom template fields (including custom-specific fields like `emission_threshold`, `income_ceiling`, etc.). Tests and notebook must import `reformlab.templates.vehicle_malus` and `reformlab.templates.energy_poverty_aid` before calling `load_portfolio()` to ensure registration side effects have run.

## Tasks / Subtasks

- [ ] **Task 1: Write portfolio integration tests** (AC: #1, #2, #3, #7)
  - [ ] 1.1 Create `tests/templates/test_custom_template_portfolio_integration.py` with test classes:
    - `TestCustomTemplatePortfolioExecution`: portfolio with VehicleMalusParameters + CarbonTaxParameters + SubsidyParameters constructs and validates without conflict; portfolio with VehicleMalusParameters + EnergyPovertyAidParameters + CarbonTaxParameters constructs successfully
    - `TestCustomTemplateConflictDetection`: two VehicleMalusParameters with overlapping rate_schedule years triggers same_policy_type + overlapping_years conflicts; two EnergyPovertyAidParameters triggers same_policy_type conflict
    - `TestPortfolioComputationWithCustomTemplates`: `PortfolioComputationStep` executes a portfolio with custom templates using MockAdapter; verify `asdict()` conversion produces complete dict with custom fields (emission_threshold, income_ceiling, etc.); assert non-zero malus and aid totals from seeded population
    - `TestPortfolioYamlRoundTripWithCustomTemplates`: `dump_portfolio()` + `load_portfolio()` round-trip preserves custom template fields; import custom template modules before `load_portfolio()` to ensure registration
  - [ ] 1.2 Use `MockAdapter` from existing test infrastructure — never use real OpenFisca
  - [ ] 1.3 Reference AC IDs in test docstrings

- [ ] **Task 2: Build notebook demo** (AC: #4, #5)
  - [ ] 2.1 Create `notebooks/demo/epic13_custom_templates.ipynb` following the Epic 12 demo pattern:
    - Section 0: Introduction (what you'll learn, prerequisites, ~15 min)
    - Section 1: Setup (path resolution, imports, output directory)
    - Section 2: "The Custom Template API" — explain the lifecycle with a diagram-like markdown
    - Section 3: "Define a Custom Template" — create a simple `ParkingLevyParameters` custom template (parking levy = flat charge per vehicle based on urban zone), demonstrate `@dataclass(frozen=True)`, subclassing `PolicyParameters`, `__post_init__` validation
    - Section 4: "Register and Use" — `register_policy_type()`, `register_custom_template()`, `infer_policy_type()`, use in `BaselineScenario`
    - Section 5: "Built-in Custom Templates" — show vehicle malus and energy poverty aid (shipped with package), run `compute_vehicle_malus()` and `compute_energy_poverty_aid()` on demo population, show decile results
    - Section 6: "Portfolios with Custom Templates" — compose vehicle malus + energy poverty aid + carbon tax into a portfolio, run `validate_compatibility()`, show that mixed built-in and custom templates work together
    - Section 7: "Compare Portfolios" — compare a "Green Transition" portfolio (carbon tax + vehicle malus + energy poverty aid) against a "Carbon Tax Only" portfolio, show distributional differences
    - Section 8: "YAML Round-Trip" — dump portfolio to YAML, reload, verify custom fields preserved
    - Section 9: Next Steps
  - [ ] 2.2 Create synthetic population data inline using `random.seed(42)` (same pattern as Epic 12 demo), with columns: `household_id`, `income`, `carbon_emissions`, `vehicle_emissions_gkm`, `energy_expenditure`. Target ~30% eligible for energy poverty aid, ~40% above vehicle malus emission threshold (> 118 gCO2/km)
  - [ ] 2.3 Use `show()` helper function for table display (inline definition, same as Epic 12)
  - [ ] 2.4 All code cells must have `execution_count: null` and `outputs: []` (committed clean)
  - [ ] 2.5 Use public API imports only — `from reformlab.templates.schema import ...`, `from reformlab.templates.vehicle_malus import ...`, `from reformlab.templates.energy_poverty_aid import ...`, `from reformlab.templates.portfolios import ...`
  - [ ] 2.6 Include plain-language markdown explanation before every code cell explaining what it does and why

- [ ] **Task 3: Write static notebook tests** (AC: #6)
  - [ ] 3.1 Create `tests/notebooks/test_epic13_demo_notebook.py` following `test_advanced_notebook.py` pattern:
    - `test_epic13_notebook_exists()` — file at expected path
    - `test_epic13_notebook_outputs_are_cleared()` — all code cells have execution_count=None, outputs=[]
    - `test_epic13_notebook_uses_public_api_only()` — contains `register_policy_type`, `register_custom_template`, `PolicyPortfolio`, `validate_compatibility`; does NOT contain `reformlab.computation`, `from openfisca import`
    - `test_epic13_notebook_covers_custom_template_lifecycle()` — contains key sections: "Define a Custom Template", "Register and Use", "Portfolios with Custom Templates"
    - `test_epic13_notebook_covers_portfolio_comparison()` — contains `compare_` or portfolio comparison code
    - `test_epic13_notebook_covers_yaml_round_trip()` — contains `dump_portfolio` or `dump_scenario_template` and `load_`

- [ ] **Task 4: Update CI workflow** (AC: #4, #6)
  - [ ] 4.1 Add `uv run pytest --nbmake notebooks/demo/epic13_custom_templates.ipynb -v` to `.github/workflows/ci.yml` (after existing notebook lines)

- [ ] **Task 5: Run verification** (AC: #1-#7)
  - [ ] 5.1 Run `uv run ruff check src/ tests/`
  - [ ] 5.2 Run `uv run mypy src/`
  - [ ] 5.3 Run `uv run pytest tests/ -x` to verify no regressions
  - [ ] 5.4 Run `uv run pytest --nbmake notebooks/demo/epic13_custom_templates.ipynb -v` to verify notebook executes

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**`from __future__ import annotations`** on every Python file. No exceptions. [Source: docs/project-context.md#Python Language Rules]

**Frozen dataclasses are NON-NEGOTIABLE** — all domain types use `@dataclass(frozen=True)`. [Source: docs/project-context.md#Critical Don't-Miss Rules]

**PyArrow is the canonical data type** — `pa.Table` for data, `pa.Array` for columns. No pandas in core logic. [Source: docs/project-context.md#Critical Don't-Miss Rules]

**Public API imports only in notebooks** — notebooks must NOT import from `reformlab.computation.*` or `openfisca`. Use `from reformlab.templates.*` and `from reformlab.indicators.*`. [Source: tests/notebooks/test_advanced_notebook.py pattern]

### Existing Code Patterns to Follow

**Notebook structure** — Follow `notebooks/demo/epic12_portfolio_comparison.ipynb` pattern exactly:
1. Markdown intro cell with "What is this?", prerequisites, time estimate
2. Setup code cell with path resolution, sys.path injection, imports, output dir, `show()` helper
3. Alternating markdown explanations + code cells
4. Export section with CSV/Parquet round-trip verification
5. Next Steps markdown cell

**Notebook path resolution pattern** (from all existing notebooks):
```python
NOTEBOOK_DIR = Path.cwd() if "__file__" not in dir() else Path(__file__).parent
if not (NOTEBOOK_DIR / "data").exists() and (NOTEBOOK_DIR / "notebooks" / "data").exists():
    NOTEBOOK_DIR = NOTEBOOK_DIR / "notebooks"
REPO_ROOT = NOTEBOOK_DIR if (NOTEBOOK_DIR / "src").exists() else NOTEBOOK_DIR.parent
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
```

**Notebook CI execution** — notebooks are tested via `uv run pytest --nbmake <path> -v` in `.github/workflows/ci.yml`. [Source: .github/workflows/ci.yml]

**Static notebook test pattern** — Follow `tests/notebooks/test_advanced_notebook.py`:
- `_load_notebook()` reads JSON
- `_cell_source(cell)` extracts source string
- `_all_sources(notebook)` concatenates all cell sources
- Tests check for specific strings in concatenated source (API names, section headings, import patterns)

**Inline synthetic data** (from Epic 12 demo):
```python
random.seed(42)
NUM_HOUSEHOLDS = 100
hh_incomes = [15000.0 + i * 850.0 + random.gauss(0, 2000) for i in range(NUM_HOUSEHOLDS)]
```

**Portfolio construction pattern:**
```python
portfolio = PolicyPortfolio(
    name="green-transition",
    policies=(
        PolicyConfig(policy_type=PolicyType.CARBON_TAX, policy=carbon_params, name="carbon-tax"),
        PolicyConfig(policy_type=infer_policy_type(malus_params), policy=malus_params, name="vehicle-malus"),
        PolicyConfig(policy_type=infer_policy_type(aid_params), policy=aid_params, name="energy-aid"),
    ),
)
```

**Portfolio YAML serialization** — `dump_portfolio()` and `load_portfolio()` in `reformlab.templates.portfolios`. Custom template fields are serialized via dataclass field introspection (not hardcoded). [Source: src/reformlab/templates/portfolios/composition.py]

**`PortfolioComputationStep` bridge** — converts `PolicyParameters` to adapter-compatible dict via `asdict()` in `_to_computation_policy()`. Custom templates work transparently because `asdict()` handles all frozen dataclass fields. [Source: src/reformlab/orchestrator/portfolio_step.py]

### Key Design Decisions

**1. Notebook creates synthetic data inline (NOT from CSV file):**
The Epic 12 portfolio comparison notebook creates synthetic population data inline with `random.seed(42)`. Story 13.4 follows the same pattern. This avoids creating another population CSV and keeps the notebook self-contained. The population needs `vehicle_emissions_gkm` (float64, gCO2/km — matching `compute_vehicle_malus()` expected column name) and `energy_expenditure` (float64, EUR — matching `compute_energy_poverty_aid()` expected column name) columns that don't exist in any shipped CSV.

**2. Simple custom template example for pedagogy:**
The notebook defines a minimal `ParkingLevyParameters` template to demonstrate the authoring lifecycle. This is deliberately simple (one custom field: `levy_per_vehicle`) so the reader focuses on the registration API, not computation logic. Vehicle malus and energy poverty aid are then shown as "shipped" custom templates for production use.

**3. No new source code in `src/`:**
This story creates no new modules under `src/reformlab/`. It validates existing functionality (custom templates in portfolios) and creates demonstration artifacts (notebook + tests). All source code was created in Stories 13.1-13.3.

**4. Portfolio comparison uses template-specific batch APIs:**
The notebook demonstrates `run_vehicle_malus_batch()`, `run_energy_poverty_aid_batch()`, and the portfolio-level comparison, showing how template-specific and portfolio-level APIs complement each other.

**5. Notebook registration cleanup:**
The notebook's custom `ParkingLevyParameters` registration persists only within the notebook kernel session. No cleanup code is needed since the kernel exits after execution. In tests, the existing `_cleanup_custom_registrations` fixture pattern handles test isolation. [Source: tests/templates/test_custom_templates.py]

### Source File Touchpoints

| File | Change Type | Purpose |
|------|-------------|---------|
| `notebooks/demo/epic13_custom_templates.ipynb` | **CREATE** | Pedagogical notebook demonstrating custom template lifecycle |
| `tests/notebooks/test_epic13_demo_notebook.py` | **CREATE** | Static notebook validation tests |
| `tests/templates/test_custom_template_portfolio_integration.py` | **CREATE** | Portfolio integration tests with custom templates |
| `.github/workflows/ci.yml` | **MODIFY** | Add nbmake execution line for new notebook |

### Population Data Requirements (for notebook inline generation)

The notebook creates a 100-household synthetic population inline:

| Column | Type | Range | Purpose |
|--------|------|-------|---------|
| `household_id` | int64 | 0-99 | Unique ID |
| `income` | float64 | ~5,000-80,000 EUR | Eligibility, decile assignment |
| `carbon_emissions` | float64 | ~1-8 tCO2 | Carbon tax computation |
| `vehicle_emissions_gkm` | float64 | ~80-250 gCO2/km | Vehicle malus computation (must match `compute_vehicle_malus()` expected column name) |
| `energy_expenditure` | float64 | ~200-3,000 EUR | Energy poverty aid eligibility (must match `compute_energy_poverty_aid()` expected column name) |

Distribution targets for interesting results:
- ~30% households eligible for energy poverty aid (income < 11,000 AND energy_share >= 0.08)
- ~40% households above vehicle malus emission threshold (> 118 gCO2/km)
- Income spread creates 10 populated deciles

### Cross-Story Dependencies

- **Depends on:** Story 13.1 (custom template API — done), Story 13.2 (vehicle malus — done), Story 13.3 (energy poverty aid — done)
- **Depends on:** Epic 12 (portfolio model — done)
- **Blocks:** Nothing (final story in Epic 13)
- **Pattern source:** Epic 12 Story 12.5 notebook demo (`notebooks/demo/epic12_portfolio_comparison.ipynb`)

### Out of Scope Guardrails

- **Do NOT** create new source modules under `src/reformlab/`. This story validates existing code, it does not add new production code.
- **Do NOT** modify `PolicyType` enum, `CustomPolicyType`, or the registration API. Those are Story 13.1's scope (done).
- **Do NOT** modify vehicle malus or energy poverty aid compute/compare modules. Those are Stories 13.2/13.3's scope (done).
- **Do NOT** create a new population CSV file. Use inline synthetic data generation in the notebook (same pattern as Epic 12 demo).
- **Do NOT** use `PortfolioComputationStep` directly in the notebook — that's an orchestrator internal. Use the template-specific batch/compare APIs and portfolio-level `validate_compatibility()` to demonstrate integration.
- **Do NOT** add pandas imports. All data is PyArrow throughout.
- **Do NOT** use `matplotlib` in the notebook unless it adds clear pedagogical value. The Epic 12 demo uses text-based `show()` output, not charts. Follow the same minimal visualization approach.

### Testing Standards

- **Static notebook tests in `tests/notebooks/`** — JSON structure checks without kernel launch
- **nbmake execution in CI** — full notebook execution with fresh kernel
- **Portfolio integration tests in `tests/templates/`** — unit tests with MockAdapter, no real OpenFisca
- **`PortfolioComputationStep` is test-only** — integration tests may use `PortfolioComputationStep` directly, but the notebook must NOT (it uses public template-level APIs only)
- **Registration precondition** — tests involving `load_portfolio()` with custom templates must import `reformlab.templates.vehicle_malus` and `reformlab.templates.energy_poverty_aid` before loading, so import-time registration side effects run
- **Non-zero result assertions** — integration tests must assert that malus totals > 0 and aid totals > 0 for the seeded population, to prevent silent zero-result failures from column name mismatches
- **Class-based test grouping** — `TestCustomTemplatePortfolioExecution`, `TestCustomTemplateConflictDetection`, etc.
- **Direct assertions** — plain `assert`, `pytest.raises(TemplateError, match=...)` for errors
- **AC ID references** — comment AC IDs in test docstrings

### Notebook Section Plan (Detailed)

```
Section 0: Introduction (markdown)
  "Epic 13 Demo — Custom Policy Templates in Portfolios"
  - What you'll learn: define, register, and deploy custom templates
  - Prerequisites: familiarity with templates (Epic 2), portfolios (Epic 12)
  - Time: ~15 minutes

Section 1: Setup (code)
  - Path resolution (standard pattern)
  - Imports: schema types, vehicle_malus, energy_poverty_aid, portfolios
  - Output dir: notebooks/data/epic13_outputs/
  - show() helper function

Section 2: The Custom Template Lifecycle (markdown)
  Plain-language explanation:
  1. Define a frozen dataclass subclassing PolicyParameters
  2. Call register_policy_type("my_type") to create a CustomPolicyType
  3. Call register_custom_template(type, MyParameters) to link them
  4. Use in BaselineScenario — policy_type is auto-inferred

Section 3: Define a Custom Template (code + markdown)
  - Define ParkingLevyParameters(PolicyParameters) with levy_per_vehicle field
  - Show __post_init__ validation
  - Register with register_policy_type + register_custom_template
  - Verify with infer_policy_type()
  - Use in BaselineScenario

Section 4: Built-in Custom Templates (code + markdown)
  - Show VehicleMalusParameters and EnergyPovertyAidParameters
  - Create 100-household synthetic population (random.seed(42)) with columns:
    household_id, income, carbon_emissions, vehicle_emissions_gkm, energy_expenditure
  - Run compute_vehicle_malus() and compute_energy_poverty_aid()
  - Show decile aggregation results

Section 5: Portfolios with Custom Templates (code + markdown)
  - Build "Green Transition" portfolio: carbon tax + vehicle malus + energy poverty aid
  - Run validate_compatibility() — no conflicts (different types)
  - Show portfolio structure

Section 6: Portfolio Comparison (code + markdown)
  - Build "Carbon Tax Only" portfolio: carbon tax only (2 policies: low and high rate)
  - Compare both portfolios' distributional impact
  - Use template-specific batch APIs for detailed analysis

Section 7: YAML Round-Trip (code + markdown)
  - dump_portfolio() to tmp file
  - load_portfolio() from tmp file
  - Verify custom fields preserved

Section 8: Export and Verify (code + markdown)
  - Export comparison tables to CSV/Parquet
  - Round-trip verification

Section 9: Next Steps (markdown)
  - Links to Epic 14 (discrete choice), Epic 17 (GUI)
```

### References

- [Source: `notebooks/demo/epic12_portfolio_comparison.ipynb` — Primary reference for notebook structure]
- [Source: `tests/notebooks/test_advanced_notebook.py` — Static notebook test pattern]
- [Source: `.github/workflows/ci.yml` — CI execution pattern for notebooks]
- [Source: `src/reformlab/templates/schema.py` — register_policy_type(), register_custom_template(), infer_policy_type()]
- [Source: `src/reformlab/templates/vehicle_malus/__init__.py` — Import-time registration pattern]
- [Source: `src/reformlab/templates/energy_poverty_aid/__init__.py` — Import-time registration pattern]
- [Source: `src/reformlab/templates/portfolios/composition.py` — validate_compatibility(), dump_portfolio(), load_portfolio()]
- [Source: `src/reformlab/templates/portfolios/portfolio.py` — PolicyConfig, PolicyPortfolio]
- [Source: `src/reformlab/orchestrator/portfolio_step.py` — PortfolioComputationStep, _to_computation_policy(), asdict() bridge]
- [Source: `src/reformlab/templates/vehicle_malus/compute.py` — VehicleMalusParameters, compute_vehicle_malus()]
- [Source: `src/reformlab/templates/energy_poverty_aid/compute.py` — EnergyPovertyAidParameters, compute_energy_poverty_aid()]
- [Source: `src/reformlab/templates/vehicle_malus/compare.py` — run_vehicle_malus_batch(), compare_vehicle_malus_decile_impacts()]
- [Source: `src/reformlab/templates/energy_poverty_aid/compare.py` — run_energy_poverty_aid_batch(), compare_energy_poverty_aid_decile_impacts()]
- [Source: `docs/project-context.md` — Frozen dataclasses, PyArrow-first, coding standards]
- [Source: `docs/epics.md#Story 13.4` — Acceptance criteria from backlog]
- [Source: `_bmad-output/implementation-artifacts/13-1-define-custom-template-authoring-api-and-registration.md` — Custom template API story]
- [Source: `_bmad-output/implementation-artifacts/13-2-implement-vehicle-malus-template.md` — Vehicle malus story]
- [Source: `_bmad-output/implementation-artifacts/13-3-implement-energy-poverty-aid-template.md` — Energy poverty aid story]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- Epic 12 portfolio comparison notebook analyzed as primary reference (epic12_portfolio_comparison.ipynb)
- Portfolio execution pipeline analyzed: PolicyConfig → _to_computation_policy() → asdict() → Adapter
- Custom template registration lifecycle fully documented: define → register_policy_type → register_custom_template → infer_policy_type
- Static notebook test pattern extracted from test_advanced_notebook.py (7 test functions, JSON-based validation)
- CI workflow pattern confirmed: `uv run pytest --nbmake <notebook> -v`
- Existing population CSVs analyzed: demo-quickstart-100 (3 cols), demo-advanced-100 (4 cols) — neither has vehicle_emissions or energy_expenditure
- Decision: inline synthetic data generation (Epic 12 pattern), not new CSV file
- validate_compatibility() conflict detection covers 4 types: same_policy_type, overlapping_years, overlapping_categories, parameter_mismatch
- PortfolioComputationStep uses asdict() bridge for all PolicyParameters subclasses (custom templates transparent)
- Notebook section plan designed: 10 sections covering full custom template lifecycle + portfolio integration
- 4 new files to create, 1 file to modify (CI workflow)
- No new source code under src/ — this story validates and demonstrates existing functionality

### File List

- `notebooks/demo/epic13_custom_templates.ipynb` — CREATE: Pedagogical notebook demo
- `tests/notebooks/test_epic13_demo_notebook.py` — CREATE: Static notebook validation tests
- `tests/templates/test_custom_template_portfolio_integration.py` — CREATE: Portfolio integration tests
- `.github/workflows/ci.yml` — MODIFY: Add nbmake line for Epic 13 notebook
