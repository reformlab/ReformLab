<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 7 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260305T162234Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 11.7

You are synthesizing 2 independent validator reviews.

Your mission:
1. VERIFY each issue raised by validators
   - Cross-reference with story content
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Blocks implementation or causes major problems
   - High: Significant gaps or ambiguities
   - Medium: Improvements that would help
   - Low: Nice-to-have suggestions

3. SYNTHESIZE findings
   - Merge duplicate issues from different validators
   - Note validator consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual validators

4. APPLY changes to story file
   - You have WRITE PERMISSION to modify the story
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Changes Applied

]]></mission>
<context>
<file id="e58fb4dd" path="docs/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="e4da3166" path="_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals.md" label="STORY FILE"><![CDATA[

# Story 11.7: Implement population validation against known marginals

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer validating synthetic population quality,
I want to validate generated populations against known reference marginal distributions from institutional sources (e.g., INSEE income decile distributions, SDES vehicle fleet composition),
so that analysts can detect deviations in their synthetic populations and ensure statistical credibility before using populations for policy simulation.

## Acceptance Criteria

1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared with a documented distance metric (Chi-squared or total variation distance).
2. Given validation results, when a marginal exceeds the tolerance threshold, then a warning identifies the specific marginal, expected vs. actual values (category-level breakdown), and the tolerance used.
3. Given validation results, when all marginals pass, then a validation summary is produced confirming the population matches reference distributions within tolerances.
4. Given validation output, when recorded in governance, then the validation status and per-marginal results are part of the population's assumption chain via `ValidationAssumption.to_governance_entry()`.

## Tasks / Subtasks

- [ ] Task 1: Create `validation.py` with error hierarchy and constraint/result types (AC: #1, #2)
  - [ ] 1.1 Create `src/reformlab/population/validation.py` with module docstring referencing Story 11.7, FR42 — explain the module validates synthetic populations against known marginal distributions from institutional sources.
  - [ ] 1.2 Define `PopulationValidationError(Exception)` base class following summary-reason-fix pattern:
    ```python
    class PopulationValidationError(Exception):
        """Base exception for population validation operations."""
        def __init__(self, *, summary: str, reason: str, fix: str) -> None:
            self.summary = summary
            self.reason = reason
            self.fix = fix
            super().__init__(f"{summary} - {reason} - {fix}")
    ```
  - [ ] 1.3 Define `MarginalConstraintMismatch(PopulationValidationError)` — raised when a marginal exceeds tolerance. Additional attributes: `dimension`, `tolerance`, `max_deviation`, `expected_values`, `actual_values`.
  - [ ] 1.4 Implement `MarginalConstraint` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class MarginalConstraint:
        """A reference marginal distribution for validation.

        Specifies the expected distribution of a categorical variable
        in the population. Used to validate synthetic populations
        against institutional benchmarks.

        Attributes:
            dimension: Column name in the population table.
            distribution: Mapping from category value to expected proportion (sums to 1.0).
            tolerance: Maximum acceptable absolute deviation per category.
        """
        dimension: str
        distribution: dict[str, float]
        tolerance: float

        def __post_init__(self) -> None:
            # Validate dimension is non-empty string
            if not self.dimension or self.dimension.strip() == "":
                msg = "dimension must be a non-empty string"
                raise ValueError(msg)
            # Validate distribution is non-empty
            if not self.distribution:
                msg = "distribution must be a non-empty dict"
                raise ValueError(msg)
            # Validate all proportions are >= 0
            for cat, prop in self.distribution.items():
                if prop < 0:
                    msg = f"distribution proportion for {cat!r} must be >= 0, got {prop}"
                    raise ValueError(msg)
            # Validate proportions sum to 1.0 (within floating point tolerance)
            total = sum(self.distribution.values())
            if not math.isclose(total, 1.0, reltol=1e-9, abs_tol=1e-9):
                msg = f"distribution proportions must sum to 1.0, got {total}"
                raise ValueError(msg)
            # Validate tolerance is positive
            if self.tolerance < 0:
                msg = f"tolerance must be >= 0, got {self.tolerance}"
                raise ValueError(msg)
            # Shallow copy — safe because values are floats (immutable)
            object.__setattr__(self, "distribution", dict(self.distribution))
    ```
  - [ ] 1.5 Implement `MarginalResult` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class MarginalResult:
        """Result of validating a single marginal constraint.

        Records the observed distribution in the population,
        the deviation from expected, and whether validation passed.

        Attributes:
            constraint: The marginal constraint being validated.
            observed: Observed proportions in the population.
            deviations: Absolute deviation per category (observed - expected).
            max_deviation: Maximum absolute deviation across all categories.
            passed: Whether constraint passed (max_deviation <= tolerance).
        """
        constraint: MarginalConstraint
        observed: dict[str, float]
        deviations: dict[str, float]
        max_deviation: float
        passed: bool
    ```
    Validate in `__post_init__`: all category keys in `observed` and `deviations` match `constraint.distribution`, `passed` is boolean, `max_deviation >= 0`.
  - [ ] 1.6 Implement `ValidationResult` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class ValidationResult:
        """Overall result of population validation against marginals.

        Aggregates results from all marginal constraints and provides
        governance-integrated assumption recording.

        Attributes:
            all_passed: Whether all constraints passed within tolerance.
            marginal_results: Ordered results for each constraint.
            total_constraints: Number of constraints validated.
            failed_count: Number of constraints that failed.
        """
        all_passed: bool
        marginal_results: tuple[MarginalResult, ...]
        total_constraints: int
        failed_count: int
    ```
    Validate in `__post_init__`: `marginal_results` is tuple, `total_constraints == len(marginal_results)`, `failed_count` matches count of `not result.passed` for each result.

- [ ] Task 2: Implement `PopulationValidator` class with validation logic (AC: #1, #2)
  - [ ] 2.1 Implement `PopulationValidator.__init__()`:
    ```python
    class PopulationValidator:
        """Validates synthetic populations against known marginal distributions.

        Supports multiple distance metrics and configurable tolerances.
        Results integrate with governance layer via assumption recording.

        Example:
            >>> validator = PopulationValidator(
            ...     constraints=[
            ...         MarginalConstraint(
            ...             dimension="income_decile",
            ...             distribution={"1": 0.08, "2": 0.12, "3": 0.15, ...},
            ...             tolerance=0.02,
            ...         ),
            ...         MarginalConstraint(
            ...             dimension="vehicle_type",
            ...             distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            ...             tolerance=0.03,
            ...         ),
            ...     ],
            ... )
            >>> result = validator.validate(population_table)
            >>> result.all_passed  # True if all within tolerance
        """
        def __init__(self, constraints: Sequence[MarginalConstraint]) -> None:
            if not constraints:
                msg = "constraints must be a non-empty sequence"
                raise ValueError(msg)
            self._constraints = tuple(constraints)
    ```
  - [ ] 2.2 Implement `validate(self, population: pa.Table) -> ValidationResult`:
    - Extract dimension column from population for each constraint
    - Compute observed proportions by counting rows per category, dividing by total rows
    - Handle missing categories in population (observed proportion = 0.0)
    - Compute absolute deviation per category: `|observed - expected|`
    - Determine `max_deviation` across all categories
    - Set `passed` if `max_deviation <= constraint.tolerance`
    - Build `MarginalResult` for each constraint
    - Determine `all_passed` (all results passed) and `failed_count`
    - Return `ValidationResult` with tuple of marginal results
  - [ ] 2.3 Implement `MarginalConstraintMismatch` raising:
    - **Do NOT raise by default** — validation errors should be informational, not blocking pipeline execution. The `PopulationValidator.validate()` method always returns `ValidationResult`; mismatches are recorded in `MarginalResult.passed=False`.
    - `MarginalConstraintMismatch` is provided as an optional error type for downstream code that wants to enforce strict validation (e.g., a quality gate before publishing a population).

- [ ] Task 3: Create `ValidationAssumption` for governance integration (AC: #4)
  - [ ] 3.1 Implement `ValidationAssumption` frozen dataclass in `validation.py`:
    ```python
    @dataclass(frozen=True)
    class ValidationAssumption:
        """Structured assumption record from population validation.

        Records the validation status and per-marginal results for
        governance integration. Can be converted to governance-compatible
        AssumptionEntry format via to_governance_entry().

        Attributes:
            all_passed: Whether all constraints passed within tolerance.
            total_constraints: Number of constraints validated.
            failed_count: Number of constraints that failed.
            marginal_details: Per-constraint details with deviations.
        """
        all_passed: bool
        total_constraints: int
        failed_count: int
        marginal_details: dict[str, dict[str, Any]]

        def __post_init__(self) -> None:
            # Coerce to tuple for immutability
            # Deep-copy is unnecessary since all contents are primitives/floats
            object.__setattr__(self, "marginal_details", dict(self.marginal_details))
    ```
  - [ ] 3.2 Implement `ValidationAssumption.to_governance_entry()`:
    ```python
    def to_governance_entry(self, *, source_label: str = "population_validation") -> dict[str, Any]:
        """Convert to governance-compatible AssumptionEntry format.

        Returns a dict with keys: key, value, source, is_default.
        The value dict includes all validation details.

        Args:
            source_label: Label for the source field.
                Defaults to "population_validation".

        Returns:
            Dict matching governance.manifest.AssumptionEntry structure.
        """
        return {
            "key": "population_validation",
            "value": {
                "all_passed": self.all_passed,
                "total_constraints": self.total_constraints,
                "failed_count": self.failed_count,
                "marginal_details": self.marginal_details,
            },
            "source": source_label,
            "is_default": False,
        }
    ```
  - [ ] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
    ```python
    def to_assumption(self) -> ValidationAssumption:
        """Convert validation result to governance-compatible assumption.

        Builds a ValidationAssumption with per-constraint details
        including dimension, tolerance, max_deviation, passed status, and
        expected vs. observed proportions.
        """
        marginal_details: dict[str, dict[str, Any]] = {}
        for result in self.marginal_results:
            marginal_details[result.constraint.dimension] = {
                "tolerance": result.constraint.tolerance,
                "max_deviation": result.max_deviation,
                "passed": result.passed,
                "expected": result.constraint.distribution,
                "observed": result.observed,
                "deviations": result.deviations,
            }

        return ValidationAssumption(
            all_passed=self.all_passed,
            total_constraints=self.total_constraints,
            failed_count=self.failed_count,
            marginal_details=marginal_details,
        )
    ```

- [ ] Task 4: Update `__init__.py` exports (AC: all)
  - [ ] 4.1 Export from `src/reformlab/population/__init__.py`: add `PopulationValidator`, `MarginalConstraint`, `MarginalResult`, `ValidationResult`, `ValidationAssumption`, `PopulationValidationError`, `MarginalConstraintMismatch` — update `__all__` listing.

- [ ] Task 5: Create test fixtures for validation tests (AC: all)
  - [ ] 5.1 Add to `tests/population/conftest.py`:
    - `population_table_valid` — a PyArrow table with columns: `income_decile` (utf8), `vehicle_type` (utf8), `region_code` (utf8). 10 rows with income deciles distributed roughly matching INSEE reference: decile 1: 1 household, decile 2: 1 household, ... decile 10: 1 household (uniform distribution). Vehicle types: 7 cars, 2 suvs, 1 bike.
    - `population_table_invalid_income` — same structure but income decile distribution deviates: decile 1: 3 households (expected ~1), decile 10: 0 households (expected ~1).
    - `population_table_invalid_vehicle` — vehicle type distribution deviates: 10 cars, 0 suvs, 0 bikes (expected ~7/2/1).
    - `constraint_income_decile` — `MarginalConstraint` for `income_decile` with distribution matching INSEE reference (equal 0.08 per decile? No, decile 1-10 each ~10% = 0.1), tolerance 0.02.
    - `constraint_vehicle_type` — `MarginalConstraint` for `vehicle_type` with distribution: {"car": 0.65, "suv": 0.20, "bike": 0.15}, tolerance 0.03.
    - `constraint_region_code` — `MarginalConstraint` for `region_code` with distribution: {"11": 0.2, "24": 0.2, "31": 0.2, "44": 0.2, "75": 0.2}, tolerance 0.05.

- [ ] Task 6: Write comprehensive validation tests (AC: #1, #2, #3, #4)
  - [ ] 6.1 `tests/population/test_validation.py`:
    - `TestPopulationValidationErrorHierarchy`:
      - `PopulationValidationError` inherits `Exception`, summary-reason-fix pattern
      - `MarginalConstraintMismatch` inherits `PopulationValidationError`, has `dimension`, `tolerance`, `max_deviation`, `expected_values`, `actual_values`
    - `TestMarginalConstraint`:
      - Frozen dataclass
      - Holds `dimension`, `distribution`, `tolerance`
      - Empty `dimension` raises `ValueError`
      - Empty `distribution` raises `ValueError`
      - Negative proportion in `distribution` raises `ValueError`
      - Proportions not summing to 1.0 raise `ValueError`
      - Negative `tolerance` raises `ValueError`
      - Distribution coerced to dict in `__post_init__`
    - `TestMarginalResult`:
      - Frozen dataclass
      - Holds `constraint`, `observed`, `deviations`, `max_deviation`, `passed`
      - All category keys match between `constraint.distribution`, `observed`, and `deviations`
      - `max_deviation` equals maximum value in `deviations` dict
      - `passed` is boolean
      - `max_deviation >= 0`
    - `TestValidationResult`:
      - Frozen dataclass
      - Holds `all_passed`, `marginal_results`, `total_constraints`, `failed_count`
      - `marginal_results` is tuple
      - `total_constraints` equals `len(marginal_results)`
      - `failed_count` matches count of failed results
    - `TestPopulationValidatorConstruction`:
      - Constructor accepts constraints sequence
      - Empty constraints list raises `ValueError`
      - Constraints stored as tuple
    - `TestPopulationValidatorValidateSingleConstraint`:
      - Single constraint with perfect match → `MarginalResult.passed` is `True`, `max_deviation == 0.0`
      - Single constraint within tolerance → `passed` is `True`
      - Single constraint exceeding tolerance → `passed` is `False`, `max_deviation > tolerance`
      - `observed` proportions sum to 1.0
      - `deviations` computed correctly per category
    - `TestPopulationValidatorValidateMultipleConstraints`:
      - Two constraints, both passing → `ValidationResult.all_passed` is `True`, `failed_count` is 0
      - Two constraints, one failing → `all_passed` is `False`, `failed_count` is 1
      - `total_constraints` is 2
      - `marginal_results` ordered by constraint insertion order
    - `TestPopulationValidatorValidateMissingCategory`:
      - Population missing a category from expected distribution → observed proportion 0.0, deviation equals expected proportion
      - Constraint fails if deviation exceeds tolerance
    - `TestPopulationValidatorValidateExtraCategory`:
      - Population has category not in expected distribution → observed proportion for that category, but deviation only computed for expected categories
      - Extra category counts toward total rows for proportion calculation
    - `TestPopulationValidatorValidateAgainstRealisticPopulation`:
      - Use `population_table_valid` with `constraint_income_decile` and `constraint_vehicle_type` → both pass within tolerance
      - Use `population_table_valid` with `constraint_region_code` → passes within tolerance
      - Use `population_table_invalid_income` → `constraint_income_decile` fails with max deviation documented
      - Use `population_table_invalid_vehicle` → `constraint_vehicle_type` fails with max deviation documented
    - `TestValidationAssumptionGovernanceEntries`:
      - Given `ValidationAssumption`, `to_governance_entries()` returns dict with `key`, `value`, `source`, `is_default`
      - `is_default` is `False`
      - Default `source` is `"population_validation"`
      - Custom `source_label` is respected
      - `value` dict contains `all_passed`, `total_constraints`, `failed_count`, `marginal_details`
      - `marginal_details` contains per-constraint entries with `tolerance`, `max_deviation`, `passed`, `expected`, `observed`, `deviations`
    - `TestValidationAssumptionIntegrationWithManifest`:
      - Given governance entry from `ValidationAssumption`, when validated against `RunManifest` assumptions schema, then entry passes validation
      - Use `minimal_manifest` from `tests/governance/conftest.py` for required fields
      - Use `cast(AssumptionEntry, entry)` for mypy strict
    - `TestValidationResultToAssumption`:
      - Given `ValidationResult` with all passed, `to_assumption()` produces `ValidationAssumption` with `all_passed=True`
      - Given `ValidationResult` with failures, `to_assumption()` produces `ValidationAssumption` with `all_passed=False` and correct `failed_count`
      - `marginal_details` contains per-constraint details extracted from `marginal_results`

- [ ] Task 7: Run full test suite and lint (AC: all)
  - [ ] 7.1 `uv run pytest tests/population/test_validation.py` — all new tests pass
  - [ ] 7.2 `uv run pytest tests/population/` — no regressions in loader, method, pipeline, or assumption tests
  - [ ] 7.3 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [ ] 7.4 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Validation Layer

This story creates the **validation layer** for the population module. It validates synthetic populations produced by `PopulationPipeline` against known reference marginals from institutional sources (INSEE, Eurostat, ADEME, SDES).

```
src/reformlab/population/
├── __init__.py          ← Modified: add new exports
├── assumptions.py       ← UNCHANGED (Story 11.6)
├── pipeline.py          ← UNCHANGED (Story 11.6)
├── validation.py        ← NEW (this story) — population validation
├── loaders/             ← UNCHANGED (Stories 11.1–11.3)
├── methods/             ← UNCHANGED (Stories 11.4–11.5)
└── validation.py        ← Will NOT exist after Story 11.8 (integration into pipeline)
```

**Wait, correction:** The validation.py file IS created by this story. Story 11.8 (notebook) will use `PopulationValidator` to validate the example French household population. The validation module persists — it's not temporary.

### Design Pattern: Non-Blocking Validation by Default

**CRITICAL:** `PopulationValidator.validate()` does NOT raise exceptions when constraints fail. It returns a `ValidationResult` with `passed=False` flags. This is intentional:

- Validation is **informational**, not blocking — analysts should see validation warnings and decide whether to proceed
- Pipeline execution (`PopulationPipeline.execute()`) continues even if validation fails
- Downstream code can optionally enforce strict validation by raising `MarginalConstraintMismatch` if needed

**Error hierarchy purpose:** `PopulationValidationError` and `MarginalConstraintMismatch` exist for:
1. Quality gates (e.g., a "population must pass validation" workflow step)
2. Optional strict mode: caller checks `result.all_passed` and raises `MarginalConstraintMismatch` if `False`

### Distance Metric: Absolute Deviation per Category

The validation metric is **absolute deviation per category**:

```
deviation[category] = |observed[category] - expected[category]|
max_deviation = max(deviations.values())
passed = (max_deviation <= tolerance)
```

This is simple, interpretable, and sufficient for detecting significant deviations in categorical marginal distributions. More complex metrics (Chi-squared, K-S test) are out of scope for MVP.

**Example interpretation:**
- Constraint: `income_decile` distribution: {"1": 0.08, "2": 0.12, ..., "10": 0.08}
- Tolerance: 0.02
- Observed: {"1": 0.10, "2": 0.11, ..., "10": 0.07}
- Deviations: {"1": 0.02, "2": 0.01, ..., "10": 0.01}
- `max_deviation`: 0.02 (from decile 1)
- `passed`: `True` (0.02 <= 0.02)

If `max_deviation` were 0.025, then `passed` would be `False` and the analyst would see a warning identifying decile 1 as the problematic marginal.

### Governance Integration Pattern

`ValidationAssumption.to_governance_entry()` follows the same pattern as `MergeAssumption.to_governance_entry()`:

```python
{
    "key": "population_validation",
    "value": {
        "all_passed": True,
        "total_constraints": 2,
        "failed_count": 0,
        "marginal_details": {
            "income_decile": {
                "tolerance": 0.02,
                "max_deviation": 0.01,
                "passed": True,
                "expected": {"1": 0.08, "2": 0.12, ...},
                "observed": {"1": 0.09, "2": 0.11, ...},
                "deviations": {"1": 0.01, "2": -0.01, ...},
            },
            "vehicle_type": {
                "tolerance": 0.03,
                "max_deviation": 0.02,
                "passed": True,
                "expected": {"car": 0.65, "suv": 0.20, "bike": 0.15},
                "observed": {"car": 0.67, "suv": 0.18, "bike": 0.15},
                "deviations": {"car": 0.02, "suv": -0.02, "bike": 0.0},
            },
        },
    },
    "source": "population_validation",
    "is_default": False,
}
```

This entry is appended to `RunManifest.assumptions` alongside pipeline merge assumptions, providing full traceability of validation results.

### Proportion Computation Algorithm

To compute observed proportions from a PyArrow table:

```python
# Extract dimension column
column_data = population.column(dimension).to_pylist()

# Count rows per category
counts: dict[str, int] = {}
for category in constraint.distribution.keys():
    counts[category] = column_data.count(category)

# Count extra categories (not in expected distribution)
all_categories = set(column_data)
extra_categories = all_categories - set(constraint.distribution.keys())
for category in extra_categories:
    counts[category] = column_data.count(category)

total_rows = len(column_data)

# Compute observed proportions
observed: dict[str, float] = {}
for category, count in counts.items():
    observed[category] = count / total_rows if total_rows > 0 else 0.0
```

**Edge cases handled:**
- Missing category in population: `observed[category] = 0.0`, `deviation = expected[category]`
- Extra category not in expected: included in counts but not in `deviations` (deviation undefined for non-expected categories)
- Zero rows: all proportions are 0.0, deviations equal expected values (constraint will fail unless expected values are all 0.0)

### Tolerance Selection Guidance

The choice of tolerance is analyst-controlled and depends on the marginal and use case. Typical ranges:

| Marginal Type | Typical Tolerance | Rationale |
|---------------|-------------------|-----------|
| Income decile distribution | 0.01 - 0.03 | INSEE surveys have sampling error; synthetic population matching within 1-3 percentage points is acceptable |
| Vehicle fleet composition | 0.02 - 0.05 | SDES data aggregates from multiple sources; moderate tolerance accommodates reporting lag |
| Geographic distribution | 0.01 - 0.02 | Regional populations are well-measured; synthetic should match closely |
| Heating system mix | 0.03 - 0.05 | ADEME surveys smaller samples; higher tolerance |

**No automatic tolerance selection:** The system does not infer tolerances from sample size or statistical significance. Analysts must provide explicit tolerance values based on domain knowledge and credibility requirements.

### Relationship to IPF Constraints

`MarginalConstraint` is simpler than `IPFConstraint` from `methods/base.py`:

| Aspect | IPFConstraint | MarginalConstraint |
|--------|---------------|-------------------|
| Purpose | Enforce marginals during merge (reweighting) | Validate final population against reference |
| Targets | Target counts (absolute) | Expected proportions (relative) |
| Enforcement | Active (modifies weights) | Passive (only checks) |
| Use case | IPF merge method parameter | Post-merge quality check |

Both share the same conceptual model: a dimension with categorical values and target/reference distribution. However, `MarginalConstraint` is for validation only — it does not modify the population.

### PyArrow Table Operations

Validation relies on PyArrow operations:
- `population.column(name)` — extract a column as ChunkedArray
- `.to_pylist()` — convert to Python list for counting
- `len(column_data)` — get total row count

No new PyArrow dependencies or patterns beyond what's already used in the pipeline and merge methods.

### Integration with Pipeline (Story 11.6)

`PopulationValidator` can be used after `PopulationPipeline.execute()`:

```python
# Execute pipeline
pipeline_result = pipeline.execute()

# Validate population
validator = PopulationValidator(constraints=[...])
validation_result = validator.validate(pipeline_result.table)

# Check validation
if not validation_result.all_passed:
    # Log warning or raise MarginalConstraintMismatch if strict mode
    pass

# Record validation assumption
validation_assumption = validation_result.to_assumption()
# Append to governance manifest
manifest.assumptions.append(cast(AssumptionEntry, validation_assumption.to_governance_entry()))
```

This workflow will be demonstrated in Story 11.8 (notebook) for the French household example.

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `dataclasses` — frozen dataclasses (stdlib)
- `math` — `math.isclose()` for proportion sum validation (stdlib)
- `typing` — type hints (stdlib)
- `pyarrow` — `pa.Table` operations (existing dependency)
- `logging` — optional for structured logging (stdlib, existing pattern in pipeline)

Import patterns:
- `pyarrow` imported at runtime in `validation.py` (same as pipeline.py)
- No `TYPE_CHECKING` guards needed for PyArrow in validation types (only used in method signatures)

### Error Hierarchy Placement

Validation errors (`PopulationValidationError`, `MarginalConstraintMismatch`) live in `validation.py` rather than a separate `errors.py`. This follows the pattern from `pipeline.py` — the module is a single-file module at the population package level, and a separate `errors.py` would add a file for two small exception classes that are only used by validation logic.

### Logging Strategy (Optional)

Structured logging is optional but recommended for traceability:

```python
import logging

_logger = logging.getLogger(__name__)

# In validate() method:
_logger.info(
    "event=population_validation_start constraints=%d rows=%d",
    len(self._constraints),
    len(population),
)

_logger.info(
    "event=population_validation_complete all_passed=%s failed_count=%d/%d",
    validation_result.all_passed,
    validation_result.failed_count,
    validation_result.total_constraints,
)

# In to_assumption() method:
_logger.debug(
    "event=validation_assumption_created all_passed=%s constraints=%d",
    self.all_passed,
    self.total_constraints,
)
```

Follows the same key=value format as `pipeline.py`.

### Downstream Dependencies

Story 11.7 is consumed by:

- **Story 11.8** (Notebook) — demonstrates validation of the French household population against INSEE/SDES marginals
- **Future population workflows** — analysts can add validation steps to their pipelines to ensure quality before policy simulation
- **Governance layer** — validation assumptions are recorded in manifests for traceability

### Project Structure Notes

**New files (2):**
- `src/reformlab/population/validation.py`
- `tests/population/test_validation.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`

**No changes** to `pyproject.toml` (no new dependencies)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (not needed in validation.py)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for all value types: `MarginalConstraint`, `MarginalResult`, `ValidationResult`, `ValidationAssumption`
- `PopulationValidator` is a mutable class — NOT a frozen dataclass (it holds state)
- Protocols, not ABCs — no protocols in this story (validation is a concrete implementation)
- Subsystem-specific exceptions (`PopulationValidationError` hierarchy, not bare `Exception`)
- `dict[str, Any]` for metadata bags (`ValidationAssumption.marginal_details`)
- `tuple[...]` for immutable sequences (`marginal_results` in `ValidationResult`)
- `X | None` union syntax (not needed in this story)
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format (optional but recommended)
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, validation.py placement
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1107] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR42] — "System validates generated populations against known marginal distributions from source data"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type
- [Source: src/reformlab/population/methods/base.py] — `IPFConstraint` pattern reference for constraint design
- [Source: src/reformlab/population/pipeline.py] — Error hierarchy pattern, logging pattern
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; governance integration pattern
- [Source: src/reformlab/population/assumptions.py] — `to_governance_entry()` pattern reference

## Dev Agent Record

### Agent Model Used

glm-4.7

### Debug Log References

None - story created from scratch, no debug logs needed.

### Completion Notes List

- Comprehensive developer context created with validation algorithm specification
- Error hierarchy designed following pipeline.py pattern
- Governance integration via `ValidationAssumption.to_governance_entry()` matching `MergeAssumption` pattern
- Non-blocking validation by default with optional strict mode via `MarginalConstraintMismatch`
- Absolute deviation metric chosen for interpretability
- Test fixtures designed with valid and invalid populations
- Full alignment with project conventions (frozen dataclasses, PyArrow usage, structured logging)

### File List

**New files (2):**
- `src/reformlab/population/validation.py`
- `tests/population/test_validation.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add new exports

## Change Log

- 2026-03-05: Story created with comprehensive developer context, ready for dev-story workflow.



]]></file>
<file id="173799eb" path="src/reformlab/population/__init__.py" label="SOURCE CODE"><![CDATA[

"""Realistic population generation library for ReformLab.

Provides institutional data source loaders, statistical fusion methods,
and population pipeline composition for building synthetic populations
from open data sources (INSEE, Eurostat, ADEME, SDES).

This module implements EPIC-11 (Realistic Population Generation Library).
Phase 2 introduces optional network dependencies for data downloads,
with offline-first caching semantics.

Public API
----------
DataSourceLoader : Protocol
    Interface for institutional data source loaders.
SourceConfig : dataclass
    Immutable configuration for a data source download.
CacheStatus : dataclass
    Status of a cached data source.
SourceCache : class
    Disk-based caching infrastructure for downloaded data.
CachedLoader : class
    Base class wrapping protocol + cache logic.
MergeMethod : Protocol
    Interface for statistical dataset fusion methods.
MergeConfig : dataclass
    Immutable configuration for a merge operation.
MergeAssumption : dataclass
    Structured assumption record from a merge operation.
MergeResult : dataclass
    Immutable result of a merge operation.
UniformMergeMethod : class
    Uniform random matching with replacement.
IPFMergeMethod : class
    Iterative Proportional Fitting reweighting and matching.
IPFConstraint : dataclass
    A marginal constraint for IPF.
IPFResult : dataclass
    Convergence diagnostics from an IPF run.
ConditionalSamplingMethod : class
    Stratum-based conditional sampling merge.
PopulationPipeline : class
    Composable builder for population generation pipelines.
PipelineResult : dataclass
    Immutable result of a pipeline execution.
PipelineStepLog : dataclass
    Log entry for a completed pipeline step.
PipelineAssumptionChain : dataclass
    Complete assumption chain from a pipeline execution.
PipelineAssumptionRecord : dataclass
    Records a single assumption from a pipeline step.
PipelineError : Exception
    Base exception for population pipeline operations.
PipelineConfigError : PipelineError
    Raised for invalid pipeline configuration.
PipelineExecutionError : PipelineError
    Raised when a pipeline step fails during execution.
"""

from __future__ import annotations

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
    PipelineAssumptionRecord,
)
from reformlab.population.loaders.ademe import (
    ADEME_AVAILABLE_DATASETS,
    ADEME_CATALOG,
    ADEMEDataset,
    ADEMELoader,
    get_ademe_loader,
    make_ademe_config,
)
from reformlab.population.loaders.base import (
    CachedLoader,
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceError,
    DataSourceOfflineError,
    DataSourceValidationError,
)
from reformlab.population.loaders.eurostat import (
    EUROSTAT_AVAILABLE_DATASETS,
    EUROSTAT_CATALOG,
    EurostatDataset,
    EurostatLoader,
    get_eurostat_loader,
    make_eurostat_config,
)
from reformlab.population.loaders.insee import (
    AVAILABLE_DATASETS,
    INSEE_AVAILABLE_DATASETS,
    INSEE_CATALOG,
    INSEEDataset,
    INSEELoader,
    get_insee_loader,
    make_insee_config,
)
from reformlab.population.loaders.sdes import (
    SDES_AVAILABLE_DATASETS,
    SDES_CATALOG,
    SDESDataset,
    SDESLoader,
    get_sdes_loader,
    make_sdes_config,
)
from reformlab.population.methods.base import (
    IPFConstraint,
    IPFResult,
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.conditional import ConditionalSamplingMethod
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.ipf import IPFMergeMethod
from reformlab.population.methods.uniform import UniformMergeMethod
from reformlab.population.pipeline import (
    PipelineConfigError,
    PipelineError,
    PipelineExecutionError,
    PipelineResult,
    PipelineStepLog,
    PopulationPipeline,
)

__all__ = [
    "ADEME_AVAILABLE_DATASETS",
    "ADEME_CATALOG",
    "ADEMEDataset",
    "ADEMELoader",
    "AVAILABLE_DATASETS",
    "CachedLoader",
    "CacheStatus",
    "DataSourceDownloadError",
    "DataSourceError",
    "DataSourceLoader",
    "DataSourceOfflineError",
    "DataSourceValidationError",
    "EUROSTAT_AVAILABLE_DATASETS",
    "EUROSTAT_CATALOG",
    "EurostatDataset",
    "EurostatLoader",
    "INSEE_AVAILABLE_DATASETS",
    "INSEE_CATALOG",
    "INSEEDataset",
    "INSEELoader",
    "SDES_AVAILABLE_DATASETS",
    "SDES_CATALOG",
    "SDESDataset",
    "SDESLoader",
    "SourceCache",
    "SourceConfig",
    "PipelineAssumptionChain",
    "PipelineAssumptionRecord",
    "PipelineConfigError",
    "PipelineError",
    "PipelineExecutionError",
    "PipelineResult",
    "PipelineStepLog",
    "PopulationPipeline",
    "get_ademe_loader",
    "get_eurostat_loader",
    "get_insee_loader",
    "get_sdes_loader",
    "ConditionalSamplingMethod",
    "IPFConstraint",
    "IPFMergeMethod",
    "IPFResult",
    "MergeAssumption",
    "MergeConfig",
    "MergeConvergenceError",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
    "make_ademe_config",
    "make_eurostat_config",
    "make_insee_config",
    "make_sdes_config",
]


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-7-implement-population-validation-against-known-marginals
**Story File:** _bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals.md
**Validated:** 2026-03-05
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 3 | 0 |
| ⚡ Enhancements | 2 | 0 |
| ✨ Optimizations | 2 | 0 |
| 🤖 LLM Optimizations | 3 | 0 |

**Overall Assessment:** Story 11.7 has **critical contradictions** between acceptance criteria and implementation notes that will cause developer confusion. Several PyArrow API errors and typos present. Requires rework before dev-story can proceed.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | AC #1 vs Dev Notes contradiction on distance metric | AC #1, Dev Notes section "Distance Metric: Absolute Deviation per Category" | +3 |
| 🔴 CRITICAL | PyArrow API error - column_data.count() doesn't exist | Dev Notes - Proportion Computation Algorithm | +3 |
| 🔴 CRITICAL | Typo in "tolerance" attribute name | Task 1.3, Task 1.4 code blocks | +3 |
| 🟠 IMPORTANT | Missing guidance on two-step governance integration process | AC #4, Dev Notes sections | +1 |
| 🟠 IMPORTANT | Test fixture extra category handling unclear | Task 5.1, Test 6.1 | +1 |
| 🟠 IMPORTANT | Missing import specification for math module | Task 1.4 code block | +1 |
| 🟠 IMPORTANT | Algorithm unclear about PyArrow to Python list conversion | Dev Notes - Proportion Computation Algorithm | +1 |
| 🟡 MINOR | Inconsistent test fixture naming suggests wrong scope | Task 5.1 | +0.3 |
| 🟡 MINOR | Missing logging integration guidance in tasks | Task 2.2, Task 6.1 | +0.3 |
| 🟢 CLEAN PASS | INVEST criteria - I, V, E, S, T | INVEST assessment | -0.5 |
| 🟢 CLEAN PASS | Acceptance Criteria - specific, measurable, edge cases covered | AC #1-4 | -0.5 |
| 🟢 CLEAN PASS | Technical Alignment - follows patterns from previous stories | Dev Notes references | -0.5 |
| 🟢 CLEAN PASS | Implementation - frozen dataclasses, protocols, error patterns | All code examples | -0.5 |

### Evidence Score: 9.8

| Score | Verdict |
|-------|---------|
| **9.8** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 11.7

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ PASS | 0/10 | Story has clear dependency on Story 11.6 (PopulationPipeline produces population to validate). This is expected and documented. No blocking dependencies. |
| **N**egotiable | ⚠️ PARTIAL | 5/10 | Story prescribes exact implementation (absolute deviation metric only) but AC #1 mentions "Chi-squared or total variation distance". Dev Notes clarify only absolute deviation is implemented, creating ambiguity about which requirement to follow. |
| **V**aluable | ✅ PASS | 0/10 | Clear value: validates synthetic populations against institutional marginals for statistical credibility. Directly addresses FR42. |
| **E**stimable | ✅ PASS | 0/10 | Well-scoped with 7 tasks, specific dataclass definitions, clear algorithm specification in Dev Notes. Developer can estimate effort accurately. |
| **S**mall | ✅ PASS | 0/10 | Single new module (validation.py) with 2 files total (validation.py + test_validation.py). Focused on validation only, not feature creep. |
| **T**estable | ✅ PASS | 0/10 | All acceptance criteria are measurable: specific distance metrics, tolerance threshold behavior, validation summary output, governance integration. Edge cases covered in tests. |

### INVEST Violations

- **[5/10] N - Negotiable:** AC #1 mentions "Chi-squared or total variation distance" but Dev Notes explicitly state "More complex metrics (Chi-squared, K-S test) are out of scope for MVP." Developer doesn't know which to implement.

### Acceptance Criteria Issues

- **Ambiguity:** AC #1 says "each marginal is compared with a documented distance metric (Chi-squared or total variation distance)" but Dev Notes section "Distance Metric: Absolute Deviation per Category" explicitly states only absolute deviation is implemented.
  - *Quote:* "when validation is run, then each marginal is compared with a documented distance metric (Chi-squared or total variation distance)"
  - *Recommendation:* Either implement both metrics or clarify in AC that only absolute deviation is in scope. Update AC #1 to match Dev Notes or vice versa.
- **Incomplete:** Test fixture `TestPopulationValidatorValidateExtraCategory` (Task 6.1) doesn't specify what should happen with deviations for extra categories - are they computed, logged, or ignored?
  - *Quote:* "Population has category not in expected distribution → observed proportion for that category, but deviation only computed for expected categories"
  - *Recommendation:* Clarify expected behavior: extra categories should be counted in total rows for proportion calculation but deviations dict should only contain expected categories.

### Hidden Risks and Dependencies

- **Implementation Dependency:** Story depends on Story 11.6 (PopulationPipeline) being complete but this is expected and documented. No blocking issue.
  - *Impact:* Low - this is the natural dependency order in EPIC-11.
  - *Mitigation:* None needed - dependency is clear and correct.

### Estimation Reality-Check

**Assessment:** Realistic

The story scope is appropriate for a single module implementation:
- 2 new files (validation.py + test_validation.py)
- 1 modified file (__init__.py exports)
- ~7 tasks with clear subtasks
- Previous story patterns (pipeline.py assumptions integration) provide reference

However, **PyArrow API error** may cause implementation delays if developer discovers it during coding rather than story review.

**Estimation details:** The algorithmic complexity is low (proportion counting, deviation calculation). Main risk is PyArrow API usage which is mis-specified in Dev Notes.

### Technical Alignment

**Status:** Minor Issues

Story follows established patterns from previous stories:
- Frozen dataclasses for value types ✅
- Summary-reason-fix error pattern ✅
- Governance integration via `to_governance_entry()` ✅
- Module structure under population/ package ✅

- **Issue 1:** Dev Notes use incorrect PyArrow API - `column_data.count(category)` doesn't exist. PyArrow ChunkedArrays need conversion to Python list first (`.to_pylist()`).
  - *Architecture Reference:* Project Context - PyArrow canonical data type, but PyArrow API usage is incorrect.
  - *Recommendation:* Update Proportion Computation Algorithm to use `list(column_data.to_pylist()).count(category)` or use `value_counts()` PyArrow method.

- **Issue 2:** Dev Notes don't specify required `import math` at module level for `math.isclose()` in MarginalConstraint.__post_init__.
  - *Architecture Reference:* Project Context - Module-level imports pattern, but import specification is missing.
  - *Recommendation:* Add `import math` to Task 1.4 code block or explicitly state in Dev Notes "import math at module level for math.isclose()".

### Evidence Score: 9.8 → MAJOR REWORK

---

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

### 1. AC #1 vs Dev Notes Contradiction on Distance Metric

**Impact:** Developer cannot determine which validation metric to implement - AC #1 says one thing, Dev Notes say another. This is a direct conflict between acceptance criteria and implementation guidance.

**Source:** AC #1 (line 15) vs Dev Notes section "Distance Metric: Absolute Deviation per Category" (lines 372-392)

**Problem:**
- AC #1: "when validation is run, then each marginal is compared with a documented distance metric (Chi-squared or total variation distance)"
- Dev Notes: "The validation metric is **absolute deviation per category**... More complex metrics (Chi-squared, K-S test) are out of scope for MVP"

This is a **direct contradiction**. Developer implementing the story doesn't know whether to implement Chi-squared/total variation OR absolute deviation. Both cannot be correct simultaneously.

**Recommended Fix:**
- **Option A:** Implement absolute deviation only, update AC #1 to match Dev Notes: "each marginal is compared using absolute deviation per category metric"
- **Option B:** Implement both metrics as documented in AC #1, remove the "More complex metrics are out of scope for MVP" statement from Dev Notes

**Recommendation:** Option A is more aligned with story scope. Update AC #1 to say: "when validation is run, then each marginal is compared using absolute deviation per category (observed - expected)" and remove mention of Chi-squared/total variation.

---

### 2. PyArrow API Error in Dev Notes

**Impact:** Implementation will fail with `AttributeError` when developer tries to call `.count()` on PyArrow ChunkedArray. Developer will need to debug and discover correct API during implementation, causing delay.

**Source:** Dev Notes - Proportion Computation Algorithm (lines 432-461)

**Problem:**
The algorithm shows:
```python
# Count rows per category
counts: dict[str, int] = {}
for category in constraint.distribution.keys():
    counts[category] = column_data.count(category)
```

However, `column_data` from `population.column(dimension)` returns a PyArrow **ChunkedArray**, which **does not have a `.count()` method**. This is an incorrect PyArrow API usage.

**Recommended Fix:**
Update Proportion Computation Algorithm to use correct PyArrow API:
```python
# Extract dimension column as Python list first
column_list = population.column(dimension).to_pylist()

# Count rows per category
counts: dict[str, int] = {}
for category in constraint.distribution.keys():
    counts[category] = column_list.count(category)

# Or use PyArrow's value_counts() for efficiency:
import pyarrow as pa
value_counts = population.column(dimension).value_counts()
counts = {category: count for category, count in zip(
    value_counts.to_pylist()[0].to_pylist(), 
    value_counts.to_pylist()[1].to_pylist()
)}
```

Also add explicit instruction: "Convert PyArrow column to Python list using `.to_pylist()` before using `.count()` method, or use PyArrow's `.value_counts()` method for efficiency."

---

### 3. Typo in "tolerance" Attribute Name

**Impact:** Developer will likely implement typo "tolerance" instead of correct "tolerance" attribute. Test validation code will fail when trying to access result.tolerance, causing confusion and wasted debugging time.

**Source:** Task 1.3 (line 34) and Task 1.4 code blocks (lines 94, 238)

**Problem:**
Code blocks show:
```python
- [ ] 1.3 Define `MarginalConstraintMismatch(PopulationValidationError)` — raised when a marginal exceeds tolerance. Additional attributes: `dimension`, `tolerance`, `max_deviation`, `expected_values`, `actual_values`.
```

Note the typo: **`tolerance`** (should be `tolerance`).

This appears in:
- Task 1.3 description
- Task 1.4 code block (line 238): `"tolerance": result.constraint.tolerance,`

**Recommended Fix:**
- Change all instances of `tolerance` to `tolerance` in:
  - Task 1.3 description
  - Task 1.4 code block (line 238)
  - Task 6.1 test case description (line 320)
  - Task 6.1 test case description (line 325)
  - Dev Notes example (line 407, 415)

---

## ⚡ Enhancement Opportunities (Should Add)

Additional guidance that would significantly help the developer avoid mistakes.

### 1. Missing Guidance on Two-Step Governance Integration Process

**Benefit:** Clarifies the indirection between ValidationResult and ValidationAssumption, preventing confusion about which method to call.

**Source:** AC #4 vs Dev Notes sections

**Current Gap:**
AC #4 says: "when recorded in governance, then validation status and per-marginal results are part of population's assumption chain via `ValidationAssumption.to_governance_entry()`"

But Dev Notes show a **two-step process**:
1. `ValidationResult.to_assumption()` creates a `ValidationAssumption`
2. `ValidationAssumption.to_governance_entry()` produces governance dict

This pattern is correct (matches PipelineAssumptionChain pattern from Story 11.6), but it's not clearly explained in AC #4 or Tasks. Developer might try to call `to_governance_entry()` directly on `ValidationResult` and fail.

**Suggested Addition:**
Add explicit workflow example in Task 3.3 or create new subtask 3.4:
```python
# Two-step governance integration (follows Story 11.6 pattern):
validation_result = validator.validate(population)
# Step 1: Convert ValidationResult to ValidationAssumption
validation_assumption = validation_result.to_assumption()
# Step 2: Convert ValidationAssumption to governance entry
governance_entry = validation_assumption.to_governance_entry()
# Step 3: Append to manifest
manifest.assumptions.append(cast(AssumptionEntry, governance_entry))
```

This matches the pattern documented in Story 11.6 (PipelineAssumptionChain.to_governance_entries()).

---

### 2. Clarify Relationship Between MarginalConstraint and IPFConstraint

**Benefit:** Prevents developer confusion about why two similar constraint types exist and when to use each.

**Source:** Dev Notes - Relationship to IPF Constraints (lines 476-487)

**Current Gap:**
The comparison table shows purpose, targets, enforcement, use case - which is good - but doesn't explain **why** both are needed in the system or how they work together in a typical workflow.

**Suggested Addition:**
Add a workflow example showing typical usage:
```python
# IPF constraint is used DURING merge to enforce marginals (reweighting)
ipf_constraint = IPFConstraint(dimension="income_bracket", targets={"low": 4000, "medium": 3000, "high": 3000})
merged_population = ipf_method.merge(table_a, table_b, MergeConfig(seed=42), constraints=(ipf_constraint,))

# MarginalConstraint is used AFTER merge to VALIDATE result against reference
validation_constraint = MarginalConstraint(dimension="income_bracket", distribution={"low": 0.40, "medium": 0.30, "high": 0.30}, tolerance=0.02)
validationResult = validator.validate(merged_population, constraints=[validation_constraint])
```

---

## ✨ Optimizations (Nice to Have)

Performance hints, development tips, and additional context for complex scenarios.

### 1. Use PyArrow value_counts() for Performance

**Value:** Using native PyArrow `.value_counts()` is more efficient than manual Python counting for large populations.

**Suggestion:**
In Dev Notes Proportion Computation Algorithm, add performance optimization note:
```python
# Efficient alternative using PyArrow native operation
import pyarrow as pa

# Get category counts directly from PyArrow
value_counts_table = population.column(dimension).value_counts()
categories = value_counts_table.column("values").to_pylist()
counts = value_counts_table.column("counts").to_pylist()

counts = dict(zip(categories, counts))
```

This is O(N) native PyArrow operation vs O(N*k) Python loops where k is categories.

---

### 2. Clarify Zero-Row Edge Case Behavior

**Value:** Explicitly stating what happens with empty populations prevents edge case bugs.

**Suggestion:**
In Task 2.2 or Dev Notes Proportion Computation Algorithm, add explicit zero-row handling:
```python
# Edge case: Empty population
if population.num_rows == 0:
    # All observed proportions are 0.0
    observed = {cat: 0.0 for cat in constraint.distribution.keys()}
    # Deviations equal expected values (constraint fails unless all expected are 0.0)
    deviations = {cat: expected for cat, expected in constraint.distribution.items()}
    max_deviation = max(deviations.values()) if deviations else 0.0
```

This clarifies behavior for the edge case mentioned in Dev Notes line 461 but not shown in code example.

---

## 🤖 LLM Optimization Improvements

Token efficiency and clarity improvements for better dev agent processing.

### 1. Resolve Distance Metric Contradiction in AC #1

**Issue:** Conflicting requirements between AC and Dev Notes
**Token Impact:** Redundant - both sections describe different metrics but AC #1 must match implementation
**Current:**
```
1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared with a documented distance metric (Chi-squared or total variation distance).
```

**Optimized:**
```
1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared using absolute deviation per category (|observed - expected|).
```

**Rationale:** Removes ambiguity. Dev Notes already state only absolute deviation is implemented. AC should match the actual requirement. Save tokens by removing unnecessary alternative metric mention.

---

### 2. Fix PyArrow Algorithm Code Example

**Issue:** Incorrect API usage that will fail at runtime
**Token Impact:** High - prevents implementation failure
**Current:**
```
# Count rows per category
counts: dict[str, int] = {}
for category in constraint.distribution.keys():
    counts[category] = column_data.count(category)
```

**Optimized:**
```
# Convert to Python list first, then count
column_list = column_data.to_pylist()
counts: dict[str, int] = {}
for category in constraint.distribution.keys():
    counts[category] = column_list.count(category)
```

**Rationale:** Shows correct API usage. PyArrow ChunkedArrays don't have `.count()` method. This prevents implementation failure.

---

### 3. Clarify Governance Integration Workflow

**Issue:** Two-step process not explicit in tasks, only in Dev Notes
**Token Impact:** Medium - developer might miss indirection
**Current:**
```
- [ ] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
```

**Optimized:**
```
- [ ] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
    Converts ValidationResult to ValidationAssumption with per-constraint details.
    Usage: `validation_assumption = result.to_assumption(); entry = validation_assumption.to_governance_entry()`
```

**Rationale:** Explicit usage example prevents confusion about the two-step process. Saves tokens by being concise but complete.

---

## 📝 Changes Applied

No changes were applied to story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 85% |
| Architecture Alignment | 90% |
| Previous Story Integration | 95% |
| LLM Optimization Score | 75% |
| **Overall Quality Score** | **86%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ✅ No wheel reinvention risks - creates new validation module following established patterns
- **Technical Specification Disasters:** ⚠️ PyArrow API error, import specification missing, distance metric contradiction - 3 issues found
- **File Structure Disasters:** ✅ File structure correct - validation.py in population/, __init__.py exports documented
- **Regression Disasters:** ✅ No regression risks - new module, doesn't modify existing functionality
- **Implementation Disasters:** ⚠️ Typos in attribute names could cause bugs - "tolerance" appears multiple times

### Competition Outcome

🏆 **Validator identified 9 improvements** that enhance story context.

**Critical findings:** 3 blocking issues (AC contradiction, PyArrow API error, typo)
**Important findings:** 4 implementation gaps (governance workflow, test clarity, imports)
**Minor findings:** 2 enhancements and optimizations

Story 11.7 requires **major rework** before dev-story can proceed, particularly to resolve the distance metric contradiction and PyArrow API errors.

---

**Report Generated:** 2026-03-05
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-7-implement-population-validation-against-known-marginals
**Story File:** _bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals.md
**Validated:** 2026-03-05
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 5 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 1 | 0 |
| 🤖 LLM Optimizations | 1 | 0 |

**Overall Assessment:** Story has a CRITICAL ambiguity in AC #1 that contradicts the implementation specification. Missing test fixtures will cause immediate implementation failures. Several edge cases are unhandled.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | AC #1 distance metric contradiction: AC says "Chi-squared or total variation distance" but Dev Notes specify absolute deviation per category | Line 15 vs Lines 372-392 | +3 |
| 🔴 CRITICAL | Missing test fixtures: 5 fixtures specified in Task 5.1 don't exist in conftest.py - tests will fail | Task 5.1 vs tests/population/conftest.py | +3 |
| 🔴 CRITICAL | Undefined error behavior: No spec for what happens when dimension column missing from population table, or contains null values, or has wrong data type | No test coverage for these scenarios | +3 |
| 🟠 IMPORTANT | Zero tolerance validation missing: MarginalConstraint allows tolerance=0 but no test for this edge case | Lines 52, 74-76, test 6.1 not covering | +1 |
| 🟠 IMPORTANT | Missing logging guidance: No explicit structured logging requirements like pipeline.py uses | Line 541-572 in pipeline.py vs missing in validation.py | +1 |
| 🟠 IMPORTANT | ValidationAssumption method naming inconsistency: AC #4 mentions `to_governance_entries()` but implementation uses `to_governance_entry()` (singular) like MergeAssumption pattern | Line 18 vs Lines 199-225 | +1 |
| 🟠 IMPORTANT | Test fixture description ambiguous: `population_table_valid` fixture description unclear about exact expected counts per category | Line 259 fixture description vague | +1 |
| 🟠 IMPORTANT | Missing _MockLoader example: Task 6.1 references `_MockLoader` but conftest.py has no example shown | Existing conftest.py doesn't show pattern | +1 |
| 🟡 MINOR | Dev Notes verbosity: "Proportion Computation Algorithm" and "Distance Metric" sections are redundant with code examples | Lines 431-461, 372-392 | +0.3 |
| 🟢 CLEAN PASS | INVEST-V (Valuable): Clear business value stated | Lines 9-11 | -0.5 |
| 🟢 CLEAN PASS | INVEST-E (Estimable): Clear tasks with well-defined data structures | Tasks 1-7 | -0.5 |
| 🟢 CLEAN PASS | INVEST-S (Small): Appropriate scope similar to Stories 11.4/11.5 | Story size comparable | -0.5 |
| 🟢 CLEAN PASS | INVEST-T (Testable): ACs are objectively verifiable (except #1 ambiguity) | Lines 13-18 | -0.5 |
| 🟢 CLEAN PASS | Technical Alignment: Follows PyArrow, frozen dataclasses, error hierarchy patterns | Lines 489-496, 593-608 | -0.5 |
| 🟢 CLEAN PASS | No hidden dependencies: All dependencies explicitly documented | Downstream Dependencies section | -0.5 |

### Evidence Score: 17.3

| Score | Verdict |
|-------|---------|
| **17.3** | **REJECT** |

---

## 🎯 Ruthless Story Validation 11.7

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ Pass | 2/10 | Depends on Story 11.6 (documented), governance layer (existing). Sequential dependency pattern is acceptable. |
| **N**egotiable | ⚠️ Issue | 4/10 | AC #1 locks implementation to specific metrics but Dev Notes contradict with absolute deviation. Reduces flexibility. |
| **V**aluable | ✅ Pass | 0/10 | Clear benefit: detect deviations, ensure statistical credibility. Contributes to EPIC-11 goal. |
| **E**stimable | ✅ Pass | 0/10 | Clear 7 tasks, well-defined data structures, algorithm in Dev Notes. Scope is estimable. |
| **S**mall | ✅ Pass | 0/10 | Single module (validation.py) + test file. Complexity similar to Stories 11.4/11.5. |
| **T**estable | ⚠️ Issue | 3/10 | 4 ACs testable, but missing test scenarios for error handling edge cases (missing columns, null values, type mismatches). |

### INVEST Violations

- **[4/10] N (Negotiable):** AC #1 contradicts Dev Notes on distance metric - AC says "Chi-squared or total variation distance", implementation specifies absolute deviation per category
- **[3/10] T (Testable):** Missing test scenarios for critical edge cases - dimension column missing, null values, wrong data type, zero tolerance validation

### Acceptance Criteria Issues

- **Critical Ambiguity:** AC #1 specifies "Chi-squared or total variation distance" but Dev Notes (lines 372-392) explicitly implement absolute deviation per category. This is a fundamental contradiction that will confuse developers.
  - *Quote:* "each marginal is compared with a documented distance metric (Chi-squared or total variation distance)"
  - *Recommendation:* Change AC #1 to "each marginal is compared using absolute deviation per category" OR change Dev Notes to implement Chi-squared/total variation distance. Must match.

- **Missing Detail:** AC #2 says "a warning identifies..." but doesn't specify warning format, destination (stdout? log?), or how warnings are presented to analysts.
  - *Quote:* "when a marginal exceeds tolerance threshold, then a warning identifies..."
  - *Recommendation:* Specify warning mechanism - e.g., "logged as structured log entry", "returned in ValidationResult.warnings field", or "printed to stdout by PopulationValidator".

- **Vague:** AC #3 says "a validation summary is produced" but doesn't specify output format (dict? printed? part of ValidationResult?).
  - *Quote:* "then a validation summary is produced confirming that population matches reference distributions within tolerances"
  - *Recommendation:* Specify that ValidationResult.all_passed boolean serves as summary, or that a human-readable summary string is generated.

- **Ambiguous:** AC #4 says validation output "is part of population's assumption chain via ValidationAssumption.to_governance_entry()" but this is singular method name. AC mentions chain but implementation uses singular pattern.
  - *Quote:* "validation status and per-marginal results are part of the population's assumption chain via ValidationAssumption.to_governance_entry()"
  - *Recommendation:* Clarify whether ValidationAssumption is a single entry or collection. Based on implementation, it's a single entry like MergeAssumption, not a chain.

### Hidden Risks and Dependencies

- **Missing Test Fixtures:** 5 fixtures specified in Task 5.1 (population_table_valid, population_table_invalid_income, population_table_invalid_vehicle, constraint_income_decile, constraint_vehicle_type) don't exist in tests/population/conftest.py. Tests will fail with "fixture not found" errors.
  - *Impact:* Developer cannot run tests without first implementing fixtures. Creates circular dependency (tests need fixtures, but fixtures aren't in conftest).
  - *Mitigation:* Add all 5 fixtures to tests/population/conftest.py with clear PyArrow table definitions.

- **Missing Error Handling Scenarios:** No specification for error cases: dimension column missing from population table, dimension column contains null values, dimension column has wrong data type (numeric instead of categorical), zero-row population table behavior.
  - *Impact:* Developer must make assumptions, leading to inconsistent error handling across validators.
  - *Mitigation:* Add test cases in Task 6.1 for: TestPopulationValidatorValidateMissingColumn, TestPopulationValidatorValidateNullValues, TestPopulationValidatorValidateWrongDataType, TestPopulationValidatorValidateZeroRows.

- **Governance Test Pattern Missing:** AC #4 test (line 326-329) references "minimal_manifest from tests/governance/conftest.py" which exists, but test needs to understand cast(AssumptionEntry, entry) pattern.
  - *Impact:* Developer may forget to use cast() for mypy strict, causing type errors.
  - *Mitigation:* Already covered in Task 6.1, but ensure example shows cast() usage explicitly.

### Estimation Reality-Check

**Assessment:** Realistic but slightly underestimated

**estimation_details:**
Story size (7 tasks, ~650 lines) is comparable to Story 11.4 (7 tasks, 50 tests) and Story 11.5 (10 tasks, 122 tests). However, missing test fixtures and error handling scenarios add complexity not captured in estimation. Implementation complexity is moderate but test coverage gaps increase integration risk. The AC #1 vs Dev Notes contradiction may cause developer confusion requiring clarification, adding to estimation variance. Overall, estimation is realistic for core implementation but testing phase is more complex than stated.

### Technical Alignment

**Status:** ✅ Pass

- **✅ Clean Pass:** Story follows established patterns correctly:
  - PyArrow for table operations (pa.Table, .to_pylist(), len())
  - Frozen dataclasses with __post_init__ validation (MarginalConstraint, MarginalResult, ValidationResult, ValidationAssumption)
  - Subsystem-specific exceptions (PopulationValidationError hierarchy, summary-reason-fix pattern)
  - Error placement in validation.py matches pipeline.py pattern
  - Governance integration via to_governance_entry() matching MergeAssumption pattern
  - __all__ exports specified
  - Module docstring references Story 11.7, FR42

Minor alignment gaps exist but are not violations:
- Logging guidance is optional but pipeline.py has explicit pattern (lines 541-572) - validation.py should follow this for consistency
- Section headers follow project conventions
- No new dependencies required

### Evidence Score: 17.3 → REJECT

---

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

### 1. AC #1 vs Implementation CRITICAL Mismatch

**Impact:** Fundamental contradiction between acceptance criteria and implementation specification will cause developer confusion, test failures, and potential requirement rework.

**Source:** AC #1 (line 15) vs Dev Notes (lines 372-392)

**Problem:**
AC #1 states: "each marginal is compared with a documented distance metric (Chi-squared or total variation distance)"

But Dev Notes (lines 372-392) explicitly specify absolute deviation per category:
```python
deviation[category] = |observed[category] - expected[category]|
max_deviation = max(deviations.values())
passed = (max_deviation <= tolerance)
```

This is NOT Chi-squared and NOT total variation distance. The contradiction is irreconcilable.

**Recommended Fix:**
Option A: Change AC #1 to match implementation:
```
1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared using absolute deviation per category.
```

Option B: Change implementation to match AC (requires significant algorithm changes):
Implement Chi-squared or total variation distance metric in Dev Notes section.

**Recommendation:** Use Option A (change AC) because absolute deviation is already specified in Dev Notes with full algorithm detail and is simpler. This avoids scope creep and keeps story consistent.

---

### 2. Missing Test Fixtures

**Impact:** Tests will fail immediately with "fixture 'population_table_valid' not found" errors. Developer cannot run tests without first implementing fixtures, creating circular dependency.

**Source:** Task 5.1 (lines 257-264) vs tests/population/conftest.py (no fixtures present)

**Problem:**
Task 5.1 specifies 5 test fixtures to add to conftest.py:
- `population_table_valid` (line 259)
- `population_table_invalid_income` (line 260)
- `population_table_invalid_vehicle` (line 261)
- `constraint_income_decile` (line 262)
- `constraint_vehicle_type` (line 263)
- `constraint_region_code` (line 264)

These fixtures don't exist in tests/population/conftest.py. They must be created before tests can run.

**Recommended Fix:**
Add all fixtures to tests/population/conftest.py with explicit PyArrow table definitions. Example for population_table_valid:
```python
@pytest.fixture()
def population_table_valid() -> pa.Table:
    """Valid population table with expected income decile and vehicle type distributions.
    
    Income deciles: uniform distribution (1 household per decile, 10% each)
    Vehicle types: 7 cars (70%), 2 suvs (20%), 1 bike (10%)
    Total: 10 rows
    """
    return pa.table({
        "income_decile": pa.array(
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            type=pa.utf8(),
        ),
        "vehicle_type": pa.array(
            ["car", "car", "car", "car", "car", "car", "car", "suv", "suv", "bike"],
            type=pa.utf8(),
        ),
        "region_code": pa.array(
            ["11", "24", "31", "44", "75", "11", "24", "31", "44", "75", "11"],
            type=pa.utf8(),
        ),
    })
```

Repeat pattern for invalid_income, invalid_vehicle, and constraint fixtures.

---

### 3. Undefined Error Behavior

**Impact:** Developer must make assumptions about error handling for common failure modes, leading to inconsistent behavior and potential runtime errors not caught by tests.

**Source:** No test coverage for error scenarios in Task 6.1

**Problem:**
The story doesn't specify what happens when:
- Dimension column doesn't exist in population table
- Dimension column contains null (None) values
- Dimension column has wrong data type (numeric int instead of categorical utf8)
- Population table has 0 rows
- Tolerance is exactly 0.0

These are plausible error scenarios that will occur in production. Without specification, different developers will handle them differently, causing inconsistency.

**Recommended Fix:**
Add test cases to Task 6.1 for error scenarios:
```
- `TestPopulationValidatorValidateMissingColumn`:
  - Population missing dimension column → raises PopulationValidationError with message about missing column
  
- `TestPopulationValidatorValidateNullValues`:
  - Population has null values in dimension column → specify behavior (skip? count as separate category? raise error?)
  
- `TestPopulationValidatorValidateWrongDataType`:
  - Dimension column is numeric int instead of utf8 → specify behavior (convert? raise error?)
  
- `TestPopulationValidatorValidateZeroRows`:
  - Population has 0 rows → all observed proportions are 0.0, specify expected behavior
```

Also add to Dev Notes section:
```
### Error Handling Scenarios

The validator should handle the following cases explicitly:

1. Missing dimension column: Raise PopulationValidationError with message indicating column not found
2. Null values in dimension: Either raise error or treat as separate category (document choice)
3. Wrong data type: Raise PopulationValidationError indicating expected utf8/str type
4. Zero rows: All proportions are 0.0, constraints fail unless expected values are all 0.0
```

---

### 4. Zero Tolerance Validation Missing

**Impact:** MarginalConstraint allows tolerance=0 (line 52 allows tolerance < 0 to be rejected, but tolerance=0 is accepted). This is technically valid but represents a degenerate case (only exact matches pass). No test ensures this doesn't cause unexpected behavior.

**Source:** MarginalConstraint.__post_init__ (lines 74-76) vs test coverage in Task 6.1

**Problem:**
Validation accepts tolerance=0:
```python
if self.tolerance < 0:
    msg = f"tolerance must be >= 0, got {self.tolerance}"
    raise ValueError(msg)
```

Zero is allowed. But no test verifies that tolerance=0 works correctly and doesn't cause division-by-zero or other unexpected behavior.

**Recommended Fix:**
Add test case in Task 6.1:
```
- `TestMarginalConstraintZeroTolerance`:
  - Create MarginalConstraint with tolerance=0.0
  - Validate that it doesn't raise ValueError in __post_init__
  - Test validation with exact match (observed == expected) → passed=True, max_deviation=0.0
```

---

### 5. Missing Logging Guidance

**Impact:** Consistency with existing codebase patterns is compromised. Pipeline.py (Story 11.6) has explicit structured logging (lines 541-572). Validation.py lacks this guidance, making integration inconsistent.

**Source:** Logging Strategy section (lines 541-572) vs validation.py missing logging spec

**Problem:**
Story references optional logging (lines 541-572) but doesn't follow the explicit pattern from pipeline.py:
```python
_logger = logging.getLogger(__name__)
_logger.info("event=population_validation_start constraints=%d rows=%d", ...)
```

Without this explicit requirement, developers may skip logging entirely or use inconsistent format, reducing traceability.

**Recommended Fix:**
Add explicit logging requirement to Task 2 (PopulationValidator class):
```
2.2 Implement `validate(self, population: pa.Table) -> ValidationResult`:
    - Extract dimension column from population for each constraint
    - Compute observed proportions by counting rows per category, dividing by total rows
    - Handle missing categories in population (observed proportion = 0.0)
    - Compute absolute deviation per category: `|observed - expected|`
    - Determine `max_deviation` across all categories
    - Set `passed` if `max_deviation <= constraint.tolerance`
    - Build `MarginalResult` for each constraint
    - Determine `all_passed` (all results passed) and `failed_count`
    - **Log structured events**: use `logging.getLogger(__name__)` with `event=population_validation_start`, `event=population_validation_complete`
    - Return `ValidationResult` with tuple of marginal results
```

Follow the exact pattern from pipeline.py lines 541-572.

---

## ⚡ Enhancement Opportunities (Should Add)

Additional guidance that would significantly help developer avoid mistakes.

### 1. Test Fixture Clarity

**Benefit:** Prevents developer misinterpretation of fixture requirements.

**Source:** Task 5.1 fixture descriptions (lines 259-264)

**Current Gap:**
The `population_table_valid` fixture description (line 259) says:
```
"income deciles distributed roughly matching INSEE reference: decile 1: 1 household, decile 2: 1 household, ... decile 10: 1 household (uniform distribution)"
```

This is ambiguous about exact counts. It says "uniform distribution" but doesn't clarify whether this means exactly 1 per decile (for 10 rows) or approximately 1 per decile. Developer may implement incorrectly.

**Suggested Addition:**
Clarify with exact counts:
```
"income_decile: 1 household per decile (10 rows total), each decile 1-10 appears exactly once (uniform 10% distribution).
Vehicle types: 7 cars, 2 suvs, 1 bike (total 10 rows).
Region codes: mix of codes 11, 24, 31, 44, 75 (total 10 rows)."
```

---

### 2. Conftest Example Missing

**Benefit:** Prevents confusion about fixture implementation pattern.

**Source:** Task 5.1 references `_MockLoader` but conftest.py doesn't show example

**Current Gap:**
Task 6.1 (line 326) references `minimal_manifest` from `tests/governance/conftest.py`, which is good. But conftest.py for population fixtures (from Stories 11.4-11.6) shows the `_MockLoader` class pattern, but new fixtures for validation don't have an example showing the pattern for PyArrow table fixtures.

**Suggested Addition:**
Add example fixture to Dev Notes or Task 5.1:
```python
@pytest.fixture()
def sample_population_table() -> pa.Table:
    """Example PyArrow table fixture for validation testing."""
    return pa.table({
        "category_column": pa.array(["A", "B", "C", "A", "B"], type=pa.utf8()),
        "value_column": pa.array([100, 200, 150, 120, 180], type=pa.int64()),
    })

@pytest.fixture()
def sample_constraint() -> MarginalConstraint:
    """Example marginal constraint for testing."""
    return MarginalConstraint(
        dimension="category_column",
        distribution={"A": 0.4, "B": 0.4, "C": 0.2},
        tolerance=0.05,
    )
```

---

### 3. ValidationAssumption Details Incomplete

**Benefit:** Ensures consistency with existing MergeAssumption pattern and correct governance integration.

**Source:** ValidationAssumption implementation (lines 173-252) vs AC #4 (line 18)

**Current Gap:**
AC #4 says "validation status and per-marginal results are part of the population's assumption chain via `ValidationAssumption.to_governance_entry()`" (singular method name). The ValidationAssumption implementation follows MergeAssumption pattern with `to_governance_entry()` (singular, line 201), which is correct. But AC #4's wording could confuse developers into thinking there's a `to_governance_entries()` (plural) method that returns a list.

Also, the governance entry format (lines 214-225) needs to be verified against RunManifest.assumptions expectations.

**Suggested Addition:**
Clarify in AC #4:
```
4. Given validation output, when recorded in governance, then validation status and per-marginal results are appended to RunManifest.assumptions via ValidationAssumption.to_governance_entry() which produces a single AssumptionEntry dict matching the governance.manifest.AssumptionEntry format.
```

Also verify the governance entry format matches AssumptionEntry requirements (key, value, source, is_default) - it does in lines 214-225, so this is just clarification.

---

## ✨ Optimizations (Nice to Have)

Performance hints, development tips, and additional context for complex scenarios.

### 1. Remove Redundant Content

**Value:** Reduce token usage and improve clarity by removing verbose algorithm explanations that duplicate code examples.

**Suggestion:**
The Dev Notes section has redundancy:

Lines 431-461 "Proportion Computation Algorithm" shows detailed Python code for computing proportions. This is already implied by the validate() method spec in Task 2.2. Remove this section and reference the code example in Task 2.2 instead.

Lines 372-392 "Distance Metric: Absolute Deviation per Category" explains the algorithm in text AND shows code. The text explanation (lines 374-381) duplicates what the code already shows. Simplify to:
```
### Distance Metric

Absolute deviation per category is used:
- `deviation[cat] = |observed[cat] - expected[cat]|`
- `max_deviation = max(deviations.values())`
- `passed = (max_deviation <= tolerance)`
```

This reduces verbosity by ~50 tokens while maintaining clarity.

---

## 🤖 LLM Optimization Improvements

Token efficiency and clarity improvements for better dev agent processing.

### 1. Reduce Section Header Overhead

**Issue:** Excessive section headers consume tokens without adding value.

**Token Impact:** ~40 tokens savings

**Current:**
```
### Proportion Computation Algorithm

To compute observed proportions from a PyArrow table:
[... detailed section ...]

### Tolerance Selection Guidance

The choice of tolerance is analyst-controlled...
```

**Optimized:**
```
#### Proportion Computation

[inline description in Task 2.2 or Dev Notes reference]

#### Tolerance Guidance

Tolerance is analyst-controlled; no automatic selection...
```

**Rationale:** Using 4-level headers (`####`) instead of 3-level (`###`) for subsections reduces line count while maintaining hierarchy. Combined with removing redundant code examples (see Optimization #1), saves ~40 tokens.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 65% |
| Architecture Alignment | 95% |
| Previous Story Integration | 70% |
| LLM Optimization Score | 60% |
| **Overall Quality Score** | **72.5%** |

### Disaster Prevention Assessment

- **Requirement Contradictions:** ⚠️ FAIL - AC #1 contradicts Dev Notes on distance metric
- **Test Coverage Gaps:** ⚠️ FAIL - Missing fixtures and error scenario tests
- **Error Handling:** ⚠️ FAIL - Undefined behavior for common error cases
- **Integration Consistency:** ⚠️ WARN - Logging pattern not explicitly required

### Competition Outcome

🏆 **Validator identified 5 critical improvements and 8 enhancement/optimization opportunities** that significantly enhance story quality.

The AC #1 contradiction is a showstopper - it creates unresolvable ambiguity that will block developers. Missing test fixtures will cause immediate test failures. The story requires rework before dev-story can proceed successfully.

---

**Report Generated:** 2026-03-05
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-05</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" token_approx="2024">_bmad-output/project-context.md</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="session_id">d83f398a-d30d-46c9-b8d6-1568b5d7778a</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="e4da3166">embedded in prompt, file id: e4da3166</var>
<var name="story_id">11.7</var>
<var name="story_key">11-7-implement-population-validation-against-known-marginals</var>
<var name="story_num">7</var>
<var name="story_title">implement-population-validation-against-known-marginals</var>
<var name="template">False</var>
<var name="timestamp">20260305_1722</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="validator_count">2</var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>You are the MASTER SYNTHESIS agent. Your role is to evaluate validator findings
    and produce a definitive synthesis with applied fixes.</critical>
  <critical>You have WRITE PERMISSION to modify the story file being validated.</critical>
  <critical>All context (project_context.md, story file, anonymized validations) is EMBEDDED below - do NOT attempt to read files.</critical>
  <critical>Apply changes to story file directly using atomic write pattern (temp file + rename).</critical>

  <step n="1" goal="Analyze validator findings">
    <action>Read all anonymized validator outputs (Validator A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with story content and project_context.md
      - Determine if issue is valid or false positive
      - Note validator consensus (if 3+ validators agree, high confidence issue)
    </action>
    <action>Issues with low validator agreement (1-2 validators) require extra scrutiny</action>
  </step>

  <step n="1.5" goal="Review Deep Verify technical findings" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify provides automated technical analysis that complements validator reviews.
      DV findings focus on: patterns, boundary cases, assumptions, temporal issues, security, and worst-case scenarios.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Must be addressed - these indicate serious technical issues
      - ERROR findings: Should be addressed unless clearly false positive
      - WARNING findings: Consider addressing, document if dismissed
    </action>

    <action>Cross-reference DV findings with validator findings:
      - If validators AND DV flag same issue: High confidence, prioritize fix
      - If only DV flags issue: Verify technically valid, may be edge case validators missed
      - If only validators flag issue: Normal processing per step 1
    </action>

    <action>For each DV finding, determine:
      - Is this a genuine issue in the story specification?
      - Does the story need to address this edge case/scenario?
      - Is this already covered but DV missed it? (false positive)
    </action>

    <action>DV findings with patterns (CC-*, SEC-*, DB-*, DT-*, GEN-*) reference known antipatterns.
      Treat pattern-matched findings as higher confidence.</action>
  </step>

  <step n="2" goal="Verify and prioritize issues">
    <action>For verified issues, assign severity:
      - Critical: Blocks implementation or causes major problems
      - High: Significant gaps or ambiguities that need attention
      - Medium: Improvements that would help quality
      - Low: Nice-to-have suggestions
    </action>
    <action>Document false positives with clear reasoning for dismissal:
      - Why the validator was wrong
      - What evidence contradicts the finding
      - Reference specific story content or project_context.md
    </action>
  </step>

  <step n="3" goal="Apply changes to story file">
    <action>For each verified issue (starting with Critical, then High), apply fix directly to story file</action>
    <action>Changes should be natural improvements:
      - DO NOT add review metadata or synthesis comments to story
      - DO NOT reference the synthesis or validation process
      - Preserve story structure, formatting, and style
      - Make changes look like they were always there
    </action>
    <action>For each change, log in synthesis output:
      - File path modified
      - Section/line reference (e.g., "AC4", "Task 2.3")
      - Brief description of change
      - Before snippet (2-3 lines context)
      - After snippet (2-3 lines context)
    </action>
    <action>Use atomic write pattern for story modifications to prevent corruption</action>
  </step>

  <step n="4" goal="Generate synthesis report">
    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- VALIDATION_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z changes applied to story file]

## Validations Quality
[For each validator: name, score, comments]
[Summary of validation quality - 1-10 scale]

## Issues Verified (by severity)

### Critical
[Issues that block implementation - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Validator(s) | **Fix**: What was changed"]

### High
[Significant gaps requiring attention]

### Medium
[Quality improvements]

### Low
[Nice-to-have suggestions - may be deferred]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Validator(s) | **Dismissal Reason**: Why this is incorrect"]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Addressed
[List DV findings that resulted in story changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Action**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives or not applicable]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why dismissed}"]

### DV-Validator Overlap
[Note any findings flagged by both DV and validators - these are high confidence]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Changes Applied
[Complete list of modifications made to story file]
[Format for each change:
  **Location**: [File path] - [Section/line]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original content]
  ```
  **After**:
  ```
  [2-3 lines of updated content]
  ```
]
&lt;!-- VALIDATION_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="5" goal="Final verification">
    <action>Verify all Critical and High issues have been addressed</action>
    <action>Confirm story file changes are coherent and preserve structure</action>
    <action>Ensure synthesis report is complete with all sections populated</action>
  </step>
</workflow></instructions>
<output-template></output-template>
</compiled-workflow>