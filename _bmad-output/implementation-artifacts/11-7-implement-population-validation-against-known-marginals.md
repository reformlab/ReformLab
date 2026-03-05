# Story 11.7: Implement population validation against known marginals

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer validating synthetic population quality,
I want to validate generated populations against known reference marginal distributions from institutional sources (e.g., INSEE income decile distributions, SDES vehicle fleet composition),
so that analysts can detect deviations in their synthetic populations and ensure statistical credibility before using populations for policy simulation.

## Acceptance Criteria

1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared using absolute deviation per category (|observed - expected|).
2. Given validation results, when a marginal exceeds the tolerance threshold, then a warning identifies the specific marginal, expected vs. actual values (category-level breakdown), and the tolerance used.
3. Given validation results, when all marginals pass, then a validation summary is produced confirming the population matches reference distributions within tolerances.
4. Given validation output, when recorded in governance, then the validation status and per-marginal results are part of the population's assumption chain via `ValidationAssumption.to_governance_entry()`.

## Tasks / Subtasks

- [x] Task 1: Create `validation.py` with error hierarchy and constraint/result types (AC: #1, #2)
  - [x] 1.1 Create `src/reformlab/population/validation.py` with module docstring referencing Story 11.7, FR42 — explain the module validates synthetic populations against known marginal distributions from institutional sources.
  - [x] 1.2 Define `PopulationValidationError(Exception)` base class following summary-reason-fix pattern:
    ```python
    class PopulationValidationError(Exception):
        """Base exception for population validation operations."""
        def __init__(self, *, summary: str, reason: str, fix: str) -> None:
            self.summary = summary
            self.reason = reason
            self.fix = fix
            super().__init__(f"{summary} - {reason} - {fix}")
    ```
  - [x] 1.3 Define `MarginalConstraintMismatch(PopulationValidationError)` — raised when a marginal exceeds tolerance. Additional attributes: `dimension`, `tolerance`, `max_deviation`, `expected_values`, `actual_values`.
   - [x] 1.4 Implement `MarginalConstraint` frozen dataclass (add `import math` at module level for `math.isclose()`):
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
  - [x] 1.5 Implement `MarginalResult` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class MarginalResult:
        """Result of validating a single marginal constraint.

        Records of observed distribution in the population,
        deviation from expected, and whether validation passed.

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
  - [x] 1.6 Implement `ValidationResult` frozen dataclass:
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

- [x] Task 2: Implement `PopulationValidator` class with validation logic (AC: #1, #2)
  - [x] 2.1 Implement `PopulationValidator.__init__()`:
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
  - [x] 2.2 Implement `validate(self, population: pa.Table) -> ValidationResult`:
    - Extract dimension column from population for each constraint
    - Compute observed proportions by counting rows per category, dividing by total rows
    - Handle missing categories in population (observed proportion = 0.0)
    - Compute absolute deviation per category: `|observed - expected|`
    - Determine `max_deviation` across all categories
    - Set `passed` if `max_deviation <= constraint.tolerance`
    - Build `MarginalResult` for each constraint
    - Determine `all_passed` (all results passed) and `failed_count`
    - Log structured events: use `logging.getLogger(__name__)` with `event=population_validation_start`, `event=population_validation_complete` (following pipeline.py pattern)
    - Return `ValidationResult` with tuple of marginal results
  - [x] 2.3 Implement `MarginalConstraintMismatch` raising:
    - **Do NOT raise by default** — validation errors should be informational, not blocking pipeline execution. The `PopulationValidator.validate()` method always returns `ValidationResult`; mismatches are recorded in `MarginalResult.passed=False`.
    - `MarginalConstraintMismatch` is provided as an optional error type for downstream code that wants to enforce strict validation (e.g., a quality gate before publishing a population).

- [x] Task 3: Create `ValidationAssumption` for governance integration (AC: #4)
  - [x] 3.1 Implement `ValidationAssumption` frozen dataclass in `validation.py`:
    ```python
    @dataclass(frozen=True)
    class ValidationAssumption:
        """Structured assumption record from population validation.

        Records of validation status and per-marginal results for
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
  - [x] 3.2 Implement `ValidationAssumption.to_governance_entry()`:
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
  - [x] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
    Usage: `validation_assumption = result.to_assumption(); entry = validation_assumption.to_governance_entry()` (two-step governance integration)
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

- [x] Task 4: Update `__init__.py` exports (AC: all)
  - [x] 4.1 Export from `src/reformlab/population/__init__.py`: add `PopulationValidator`, `MarginalConstraint`, `MarginalResult`, `ValidationResult`, `ValidationAssumption`, `PopulationValidationError`, `MarginalConstraintMismatch` — update `__all__` listing.

- [x] Task 5: Create test fixtures for validation tests (AC: all)
  - [x] 5.1 Add to `tests/population/conftest.py`:
    - `population_table_valid` — a PyArrow table with columns: `income_decile` (utf8), `vehicle_type` (utf8), `region_code` (utf8). 10 rows with income deciles: 1 household per decile (exact uniform 10% distribution: each decile 1-10 appears exactly once). Vehicle types: 7 cars (70%), 2 suvs (20%), 1 bike (10%).
    - `population_table_invalid_income` — same structure but income decile distribution deviates: decile 1: 3 households (expected ~1), decile 10: 0 households (expected ~1).
    - `population_table_invalid_vehicle` — vehicle type distribution deviates: 10 cars, 0 suvs, 0 bikes (expected ~7/2/1).
    - `constraint_income_decile` — `MarginalConstraint` for `income_decile` with distribution matching INSEE reference (uniform: decile 1-10 each 0.1 = 10%), tolerance 0.02.
    - `constraint_vehicle_type` — `MarginalConstraint` for `vehicle_type` with distribution: {"car": 0.65, "suv": 0.20, "bike": 0.15}, tolerance 0.03.
    - `constraint_region_code` — `MarginalConstraint` for `region_code` with distribution: {"11": 0.2, "24": 0.2, "31": 0.2, "44": 0.2, "75": 0.2}, tolerance 0.05.

- [x] Task 6: Write comprehensive validation tests (AC: #1, #2, #3, #4)
  - [x] 6.1 `tests/population/test_validation.py`:
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
      - Zero `tolerance` is valid (exact match required)
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
    - `TestValidationAssumptionGovernanceEntry`:
      - Given `ValidationAssumption`, `to_governance_entry()` returns dict with `key`, `value`, `source`, `is_default`
      - `is_default` is `False`
      - Default `source` is `"population_validation"`
      - Custom `source_label` is respected
      - `value` dict contains `all_passed`, `total_constraints`, `failed_count`, `marginal_details`
      - `marginal_details` contains per-constraint entries with `tolerance`, `max_deviation`, `passed`, `expected`, `observed`, `deviations`
    - `TestValidationResultToAssumption`:
      - Given `ValidationResult` with all passed, `to_assumption()` produces `ValidationAssumption` with `all_passed=True`
      - Given `ValidationResult` with failures, `to_assumption()` produces `ValidationAssumption` with `all_passed=False` and correct `failed_count`
      - `marginal_details` contains per-constraint details extracted from `marginal_results`

- [x] Task 7: Run full test suite and lint (AC: all)
  - [x] 7.1 `uv run pytest tests/population/test_validation.py` — all new tests pass
  - [x] 7.2 `uv run pytest tests/population/` — no regressions in loader, method, pipeline, or assumption tests
  - [x] 7.3 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x] 7.4 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

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

- Implemented comprehensive validation module with error hierarchy (PopulationValidationError, MarginalConstraintMismatch)
- Created frozen dataclasses for MarginalConstraint, MarginalResult, ValidationResult, ValidationAssumption
- Implemented PopulationValidator class with validate() method supporting absolute deviation metric
- Structured logging added with event=population_validation_start and event=population_validation_complete
- Governance integration via ValidationAssumption.to_governance_entry() matching MergeAssumption pattern
- Non-blocking validation by default - validate() returns ValidationResult with passed flags
- Test fixtures added to conftest.py with valid/invalid population tables and constraints
- 52 comprehensive tests covering all acceptance criteria, edge cases, and governance integration
- All tests pass, no regressions in existing population tests
- Ruff and mypy strict mode compliance achieved

### File List

**New files (2):**
- `src/reformlab/population/validation.py`
- `tests/population/test_validation.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — added validation exports
- `tests/population/conftest.py` — added validation fixtures

## Change Log

- 2026-03-05: Story created with comprehensive developer context, ready for dev-story workflow.
- 2026-03-05: All tasks completed - validation module implemented with comprehensive tests and full governance integration.

## Senior Developer Review (AI)

### Review: 2026-03-05
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 3.0 → APPROVED
- **Issues Found:** 1 (architectural issue)
- **Issues Fixed:** 1
- **Action Items Created:** 0

### Code Review Synthesis Summary

The Master Synthesis Report has been generated in `11-7-implement-population-validation-against-known-marginals-synthesis.md`.

**Verified Issue Fixed:**
- **[AI-Review] HIGH: Extra category handling in MarginalResult.__post_init__** (src/reformlab/population/validation.py:149-168)
  - **Issue:** Original implementation required exact key equality between observed and constraint keys, breaking extra category handling documented in Dev Notes (lines 458-461)
  - **Fix Applied:** Removed strict key equality validation. Now validates only that all expected constraint keys are present in observed (missing_expected check), allowing extra categories while ensuring deviations keys match constraint keys exactly
  - **Test Status:** All 52 validation tests pass after fix; 434 total population tests pass with no regressions

**Dismissed Issues (False Positives):**
- Validator A's widespread "tolerance" typo claims: Not found in actual code - word is spelled correctly
- Validator A's "observed"/"deviations"/"marginal"/"passed"/"deviation" typo claims: Not found - attribute names and dict keys are correct
- Test fixture count discrepancies: Story specification vs fixture implementation clarified in synthesis; both 10-row and 20-row variants produce correct 10% proportions
- PyArrow API error claims: Code is correct - to_pylist() is called before count()
- Documentation discrepancy claims: Story file already specifies absolute deviation metric correctly

**Source Code Modifications:**
- File: `src/reformlab/population/validation.py`
- Change: Modified `MarginalResult.__post_init__()` to allow extra categories in observed dict
- Before: Required `constraint_keys != observed_keys` (strict equality)
- After: Requires only that all constraint keys are present in observed (allows extra keys)
- Lines changed: 149-168 (simplified validation logic)

**Test Results:**
- All tests passing: 434 population tests, 52 validation tests
- No regressions detected in existing functionality
- Extra category handling now correctly allows additional categories while computing deviations only for expected categories

