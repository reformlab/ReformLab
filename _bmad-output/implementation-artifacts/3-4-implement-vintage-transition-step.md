# Story 3.4: Implement Vintage Transition Step

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **framework developer**,
I want **to implement a vintage transition step that tracks asset cohort aging and turnover through multi-year simulations**,
so that **analysts can model how vehicle fleets, heating systems, or other durable goods evolve over time, enabling accurate carbon-tax and subsidy impact analysis across projection horizons**.

## Acceptance Criteria

From backlog (BKL-304), aligned with FR15, FR16, NFR6, NFR7.

1. **AC-1: Vintage transition step ages cohorts by one year**
   - Given a vehicle fleet with age distribution at year t, when vintage transition runs, then all cohorts age by one year (cohort_age += 1).
   - The step implements the `OrchestratorStep` protocol from Story 3-2.

2. **AC-2: New vintages are added according to transition rules**
   - Given transition rules specifying new cohort entry rates, when vintage transition executes, then new vintage cohorts (age=0) are added to the population.
   - Given scrappage/retirement rules, when transition executes, then cohorts exceeding maximum age are removed from the active fleet.

3. **AC-3: Identical inputs and seeds produce identical outputs**
   - Given identical transition rules and seeds, when vintage transition runs twice, then vintage state at year t+n is bit-identical.
   - Determinism is maintained across runs on the same machine (NFR6).
   - Determinism is maintained across different machines with same Python/dependency versions (NFR7).

4. **AC-4: Vintage composition is visible per year in state output**
   - Given vintage state at each year, when panel output is produced, then vintage composition (cohort counts, age distribution) is visible per year in `YearState.data`.
   - The vintage module provides utilities to extract vintage summaries for indicator computation.

5. **AC-5: Step integrates with orchestrator pipeline**
   - Given a configured VintageTransitionStep, when registered with StepRegistry and executed via Orchestrator, then it executes correctly in the yearly pipeline.
   - Given a `depends_on` relationship with carry-forward step, when the pipeline is built, then vintage transition executes after carry-forward.

6. **AC-6: Asset class is configurable (MVP: vehicles OR heating)**
   - Given a VintageConfig specifying asset_class="vehicle", when transition runs, then vehicle-specific cohort logic is applied.
   - The design supports adding additional asset classes (heating, appliances) in future stories without modifying core transition logic.

## Dependencies

- **Required prior stories:**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `YearState`, `OrchestratorConfig`
  - Story 3-2 (BKL-302): Step interface - provides `OrchestratorStep` Protocol, `StepRegistry`, `@step` decorator
  - Story 3-3 (BKL-303): Carry-forward step - demonstrates step pattern, may be used for dependency ordering
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-3-implement-carry-forward-step`: `done`
- **Follow-on stories:**
  - Story 3-5 (BKL-305): ComputationAdapter integration - orchestrates adapter calls alongside vintage transition
  - Story 3-7 (BKL-307): Panel output - will consume vintage state per year

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and review existing patterns (AC: dependency check)
  - [ ] 0.1 Verify Story 3-1, 3-2, 3-3 status is `done`
  - [ ] 0.2 Review `CarryForwardStep` implementation for patterns to follow
  - [ ] 0.3 Review `YearState` dataclass for vintage data structure requirements
  - [ ] 0.4 Confirm vintage module location: `src/reformlab/vintage/`
  - [ ] 0.5 Record dependency verification evidence in Dev Agent Record

- [ ] Task 1: Define vintage data structures (AC: #4, #6)
  - [ ] 1.1 Create `src/reformlab/vintage/types.py` with:
    - `VintageCohort`: frozen dataclass representing a single cohort (age, count, attributes)
    - `VintageState`: frozen dataclass containing all cohorts for an asset class
    - `VintageSnapshot`: summary statistics for a given year
  - [ ] 1.2 Define `AssetClass` enum: `VEHICLE`, `HEATING` (MVP: implement vehicle only)
  - [ ] 1.3 Define `VintageSummary` for extracting per-year statistics

- [ ] Task 2: Define vintage transition configuration schema (AC: #2, #6)
  - [ ] 2.1 Create `src/reformlab/vintage/config.py` with:
    - `VintageTransitionRule`: frozen dataclass for a single transition rule
      - `rule_type: Literal["age", "entry", "exit"]`
      - `period_semantics: str` (NFR10 compliance, like carry-forward)
      - `parameters: dict` (age increment, entry rate, max age for exit)
  - [ ] 2.2 Define `VintageConfig`: frozen dataclass with:
    - `asset_class: AssetClass`
    - `rules: tuple[VintageTransitionRule, ...]`
    - `max_cohort_age: int | None` (for automatic retirement)
    - `initial_state: VintageState | None`
  - [ ] 2.3 Add config validation to reject missing period semantics (NFR10)

- [ ] Task 3: Implement VintageTransitionStep class (AC: #1, #3, #5)
  - [ ] 3.1 Create `src/reformlab/vintage/transition.py` with `VintageTransitionStep`:
    - Implements `OrchestratorStep` protocol
    - `name: str = "vintage_transition"`
    - `depends_on: tuple[str, ...] = ("carry_forward",)` (default dependency)
    - `execute(year: int, state: YearState) -> YearState`
  - [ ] 3.2 Implement cohort aging logic:
    - All existing cohorts: age += 1
    - Deterministic ordering (sorted by cohort attributes)
  - [ ] 3.3 Implement new vintage entry logic:
    - Add new cohorts (age=0) based on entry rules
    - Entry count can be fixed or derived from state data
  - [ ] 3.4 Implement cohort exit/retirement logic:
    - Remove cohorts exceeding max_cohort_age
    - Exit counts tracked for output
  - [ ] 3.5 Ensure state updates create new `YearState` (immutability via `replace()`)
  - [ ] 3.6 Store vintage state in `state.data["vintage_<asset_class>"]`

- [ ] Task 4: Add vintage-specific errors (AC: #2, #3)
  - [ ] 4.1 Create `src/reformlab/vintage/errors.py` with:
    - `VintageConfigError`: invalid vintage configuration
    - `VintageTransitionError`: runtime failures during transition
  - [ ] 4.2 Ensure errors include actionable messages with asset class and cohort details

- [ ] Task 5: Add determinism and reproducibility guarantees (AC: #3)
  - [ ] 5.1 Document seed usage for any stochastic transitions
  - [ ] 5.2 If entry/exit rates use randomness, derive seed from `state.seed`
  - [ ] 5.3 Add determinism test: same input state produces identical output across runs
  - [ ] 5.4 Add cross-machine reproducibility documentation

- [ ] Task 6: Implement vehicle asset class MVP (AC: #1, #2, #6)
  - [ ] 6.1 Define vehicle-specific cohort attributes (fuel type, efficiency class, etc.)
  - [ ] 6.2 Implement default vehicle transition rules:
    - Aging: all vehicles age by 1 year per step
    - Entry: new vehicles enter fleet (age=0)
    - Exit: vehicles above max_age retire
  - [ ] 6.3 Create factory function: `vehicle_transition_step(config: VintageConfig) -> VintageTransitionStep`

- [ ] Task 7: Add tests for vintage transition step (AC: all)
  - [ ] 7.1 Create `tests/vintage/test_types.py`:
    - Test VintageCohort immutability
    - Test VintageState operations
  - [ ] 7.2 Create `tests/vintage/test_config.py`:
    - Valid configurations pass
    - Missing period semantics rejected (NFR10)
    - Invalid rule types rejected
  - [ ] 7.3 Create `tests/vintage/test_transition.py`:
    - Test cohort aging (all cohorts age += 1)
    - Test new vintage entry (age=0 cohorts added)
    - Test cohort exit (cohorts above max age removed)
    - Test determinism (identical inputs → identical outputs)
  - [ ] 7.4 Create `tests/vintage/test_integration.py`:
    - VintageTransitionStep works with StepRegistry
    - Pipeline execution with carry-forward + vintage transition
    - Vintage state visible in yearly panel output

- [ ] Task 8: Export APIs and run quality gates (AC: all)
  - [ ] 8.1 Create `src/reformlab/vintage/__init__.py` with exports:
    - Types: `VintageCohort`, `VintageState`, `VintageSnapshot`, `AssetClass`
    - Config: `VintageConfig`, `VintageTransitionRule`
    - Step: `VintageTransitionStep`
    - Errors: `VintageConfigError`, `VintageTransitionError`
    - Factory: `vehicle_transition_step`
  - [ ] 8.2 Add concise docstrings for public APIs
  - [ ] 8.3 Run `ruff check src/reformlab/vintage tests/vintage`
  - [ ] 8.4 Run `mypy src/reformlab/vintage`
  - [ ] 8.5 Run full orchestrator test suite to ensure no regressions

## Dev Notes

### Architecture Alignment

**From architecture.md - Step-Pluggable Dynamic Orchestrator:**
> For each year t in [start_year .. end_year]:
>   3. Execute transition steps (pluggable pipeline):
>      a. Vintage transitions (asset cohort aging, fleet turnover)

**From architecture.md - Subsystems:**
> `vintage/`: Cohort/vintage state management. Registered as orchestrator step. Tracks asset classes (vehicles, heating) through time.

**From architecture.md - Dynamic Execution Semantics:**
> Vintage states are updated through registered transition step functions.
> Randomness is seed-controlled and logged in manifests.

**From PRD FR15:**
> System can track asset/cohort vintages (for example, vehicle/heating cohorts) by year.

**From PRD FR16:**
> Analyst can configure transition rules for state updates between years.

**From PRD NFR6:**
> Identical inputs produce bit-identical outputs across runs on the same machine.

**From PRD NFR7:**
> Identical inputs produce identical outputs across different machines and operating systems (Python version and dependency versions held constant).

### Existing Code Patterns to Follow

**From Story 3-3 (`src/reformlab/orchestrator/carry_forward.py`):**
```python
# Config pattern with frozen dataclass and NFR10 validation
@dataclass(frozen=True)
class CarryForwardRule:
    variable: str
    rule_type: RuleType
    period_semantics: str  # NFR10 compliance
    value: float | None = None
    custom_fn: Callable[[int, Any, "YearState"], Any] | None = None

    def __post_init__(self) -> None:
        if not self.period_semantics or not self.period_semantics.strip():
            raise CarryForwardConfigError(
                f"Rule for '{self.variable}' missing period_semantics (NFR10)"
            )

# Step class implementing OrchestratorStep protocol
class CarryForwardStep:
    __slots__ = ("_config", "_name", "_depends_on", "_description")

    def __init__(
        self,
        config: CarryForwardConfig,
        name: str = "carry_forward",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        ...

    @property
    def name(self) -> str:
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        return self._depends_on

    def execute(self, year: int, state: "YearState") -> "YearState":
        # Create mutable copy of data
        new_data = dict(state.data)
        # Apply rules in sorted order for determinism
        sorted_rules = sorted(self._config.rules, key=lambda r: r.variable)
        # ... apply rules ...
        return replace(state, data=new_data)
```

**From Story 3-2 (`src/reformlab/orchestrator/step.py`):**
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: "YearState") -> "YearState": ...

# Optional metadata
@property
def depends_on(self) -> tuple[str, ...]:
    return ()
```

**From Story 3-1 (`src/reformlab/orchestrator/types.py`):**
```python
@dataclass(frozen=True)
class YearState:
    year: int
    data: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Previous Story Intelligence (Story 3-3)

From Story 3-3 completion notes:
- `CarryForwardStep` implements `OrchestratorStep` protocol with `@runtime_checkable`
- Frozen dataclasses for config (CarryForwardRule, CarryForwardConfig)
- NFR10 compliance: `period_semantics` required on all rules, validated in `__post_init__`
- Determinism: rules sorted by variable name before application
- Immutability: uses `replace()` to create new `YearState`
- Error classes: `CarryForwardConfigError`, `CarryForwardExecutionError`
- 38 tests in `tests/orchestrator/test_carry_forward.py`
- All 144 orchestrator tests pass

Key patterns to replicate:
- Protocol-based step interface with `__slots__`
- Frozen dataclasses for immutable configuration
- `depends_on` for step ordering (vintage depends on carry_forward by default)
- Clear error classes with actionable messages
- Sorted/deterministic ordering of operations
- State updates via `replace()` for immutability

### Git Intelligence (Recent Commits)

Recent commits show overnight-build workflow pattern:
- `1842ca6`: 3-3 mark done
- `8ca6030`: 3-3 code review
- `5e638e9`: 3-3 dev story
- `40af129`: 3-3 validate story
- `4e8b3ec`: 3-3 create story

Pattern: create → validate → dev → code-review → mark-done

### Design Decisions

**Vintage Data Model:**
```python
@dataclass(frozen=True)
class VintageCohort:
    """A single cohort of assets with shared vintage characteristics."""
    age: int  # Years since manufacture/installation
    count: int  # Number of assets in this cohort
    attributes: tuple[tuple[str, Any], ...] = ()  # Immutable attribute pairs
    # Example: (("fuel_type", "diesel"), ("efficiency_class", "B"))

@dataclass(frozen=True)
class VintageState:
    """Complete vintage state for an asset class."""
    asset_class: AssetClass
    cohorts: tuple[VintageCohort, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def total_count(self) -> int:
        return sum(c.count for c in self.cohorts)

    def age_distribution(self) -> dict[int, int]:
        return {c.age: c.count for c in sorted(self.cohorts, key=lambda c: c.age)}
```

**VintageTransitionRule Design:**
```python
RuleType = Literal["age", "entry", "exit"]

@dataclass(frozen=True)
class VintageTransitionRule:
    """Rule for vintage state transition."""
    rule_type: RuleType
    period_semantics: str  # NFR10 compliance, e.g., "annual_aging"
    parameters: dict[str, Any] = field(default_factory=dict)
    # For "entry": {"count": 1000} or {"rate": 0.05, "base_key": "population"}
    # For "exit": {"max_age": 20}
    # For "age": {} (no parameters needed, all cohorts age by 1)

    def __post_init__(self) -> None:
        if not self.period_semantics or not self.period_semantics.strip():
            raise VintageConfigError(
                f"Vintage rule '{self.rule_type}' missing period_semantics (NFR10)"
            )
```

**VintageTransitionStep Design:**
```python
class VintageTransitionStep:
    """Orchestrator step for vintage cohort transitions."""

    __slots__ = ("_config", "_name", "_depends_on", "_description")

    def __init__(
        self,
        config: VintageConfig,
        name: str = "vintage_transition",
        depends_on: tuple[str, ...] = ("carry_forward",),
        description: str | None = None,
    ) -> None:
        self._config = config
        self._name = name
        self._depends_on = depends_on
        self._description = description or f"Vintage transition for {config.asset_class.value}"

    def execute(self, year: int, state: YearState) -> YearState:
        # Load current vintage state from YearState.data
        vintage_key = f"vintage_{self._config.asset_class.value}"
        current = state.data.get(vintage_key)

        # Apply transition rules in deterministic order
        new_state = self._apply_transitions(year, current, state)

        # Store updated vintage state
        new_data = dict(state.data)
        new_data[vintage_key] = new_state
        return replace(state, data=new_data)

    def _apply_transitions(
        self,
        year: int,
        current: VintageState | None,
        state: YearState,
    ) -> VintageState:
        # 1. Age all existing cohorts
        # 2. Remove cohorts exceeding max_age (exit rule)
        # 3. Add new cohorts (entry rule)
        ...
```

### Project Structure Notes

**New files to create:**
- `src/reformlab/vintage/__init__.py` - Module exports
- `src/reformlab/vintage/types.py` - Data structures (VintageCohort, VintageState, AssetClass)
- `src/reformlab/vintage/config.py` - Configuration (VintageConfig, VintageTransitionRule)
- `src/reformlab/vintage/transition.py` - VintageTransitionStep implementation
- `src/reformlab/vintage/errors.py` - Error classes

**New test files:**
- `tests/vintage/__init__.py`
- `tests/vintage/test_types.py`
- `tests/vintage/test_config.py`
- `tests/vintage/test_transition.py`
- `tests/vintage/test_integration.py`

**Directory structure:**
```
src/reformlab/vintage/
├── __init__.py
├── types.py      # VintageCohort, VintageState, VintageSnapshot, AssetClass
├── config.py     # VintageConfig, VintageTransitionRule
├── transition.py # VintageTransitionStep
└── errors.py     # VintageConfigError, VintageTransitionError

tests/vintage/
├── __init__.py
├── test_types.py
├── test_config.py
├── test_transition.py
└── test_integration.py
```

### Testing Standards

- Use `pytest` with vintage-specific fixtures
- Test all rule types: age, entry, exit
- Test NFR10 compliance (period semantics validation)
- Test determinism with identical inputs
- Test integration with StepRegistry and Orchestrator
- Test pipeline ordering with carry-forward step
- Ensure existing orchestrator tests still pass (144 tests)

### Asset Class Design (MVP: Vehicle)

**Vehicle cohort attributes:**
```python
# Vehicle-specific attributes stored in VintageCohort.attributes
# Fuel type: petrol, diesel, hybrid, electric
# Efficiency class: A, B, C, D, E, F, G
# Size category: small, medium, large, suv

# Example cohort:
VintageCohort(
    age=5,
    count=100_000,
    attributes=(
        ("fuel_type", "diesel"),
        ("efficiency_class", "C"),
        ("size_category", "medium"),
    )
)
```

**Default vehicle transition rules:**
```python
default_vehicle_rules = (
    VintageTransitionRule(
        rule_type="age",
        period_semantics="annual_cohort_aging",
    ),
    VintageTransitionRule(
        rule_type="exit",
        period_semantics="annual_retirement_above_max_age",
        parameters={"max_age": 20},
    ),
    VintageTransitionRule(
        rule_type="entry",
        period_semantics="annual_new_vehicle_sales",
        parameters={"count": 50_000},  # Or derive from state
    ),
)
```

### Out-of-Scope Guardrails

- No ComputationAdapter calls (Story 3-5)
- No panel output formatting (Story 3-7)
- No manifest generation (Epic 5)
- No heating asset class implementation (future story)
- No behavioral responses (Phase 2)
- No market equilibrium (out of scope)
- No complex demographic modeling in this step (carry-forward handles that)

### Error Handling Patterns

Follow existing orchestrator error patterns:
```python
class VintageConfigError(Exception):
    """Invalid vintage configuration."""

class VintageTransitionError(Exception):
    """Error during vintage transition step execution."""
```

Include actionable messages:
- "VintageConfig for 'vehicle' missing required 'age' rule"
- "VintageTransitionRule 'entry' missing period_semantics (NFR10)"
- "Cannot apply exit rule: cohort age 15 exceeds configured max_age 20"

### Performance Considerations

- Use frozen dataclasses with tuples for cohort storage (immutable, hashable)
- Avoid dict operations inside tight loops
- Sort cohorts once per execute() call
- Target: <100ms for fleet of 1M vehicles across ~50 cohorts

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems]
- [Source: _bmad-output/planning-artifacts/architecture.md#Dynamic Execution Semantics]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-304]
- [Source: _bmad-output/planning-artifacts/prd.md#FR15]
- [Source: _bmad-output/planning-artifacts/prd.md#FR16]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR6]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR7]
- [Source: src/reformlab/orchestrator/step.py - OrchestratorStep Protocol]
- [Source: src/reformlab/orchestrator/types.py - YearState dataclass]
- [Source: src/reformlab/orchestrator/carry_forward.py - CarryForwardStep pattern]
- [Source: _bmad-output/implementation-artifacts/3-3-implement-carry-forward-step.md]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
