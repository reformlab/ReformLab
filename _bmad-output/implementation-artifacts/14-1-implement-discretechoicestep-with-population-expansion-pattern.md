# Story 14.1: Implement DiscreteChoiceStep with Population Expansion Pattern

Status: ready-for-dev

## Story

As a **platform developer**,
I want a `DiscreteChoiceStep` that implements the OrchestratorStep protocol and performs population expansion to evaluate household alternatives via the ComputationAdapter,
so that the orchestrator can model household investment decisions as discrete choice problems without modifying existing interfaces.

## Acceptance Criteria

1. **AC-1: Protocol compliance** — `DiscreteChoiceStep` implements the `OrchestratorStep` protocol (`name` property, `execute(year, state) -> YearState` method) and registers with the `StepRegistry` without modification to orchestrator core.
2. **AC-2: Population expansion** — Given a population of N households and a choice set of M alternatives, expansion creates M copies of each household with attributes modified per alternative, producing an N×M expanded population as a `PopulationData` instance.
3. **AC-3: Adapter batch call** — The expanded N×M population is passed to `ComputationAdapter.compute()` in one vectorized batch call (not M separate calls per household).
4. **AC-4: Cost matrix reshape** — OpenFisca results for the expanded population are reshaped into an N×M cost matrix (PyArrow-based), with one cost value per household per alternative.
5. **AC-5: No interface changes** — No modifications to `ComputationAdapter`, `YearState`, `OrchestratorConfig`, or orchestrator loop logic (`runner.py`). The step is purely additive.
6. **AC-6: Decision domain protocol** — A `DecisionDomain` protocol defines the contract for decision domains (choice set, attribute overrides, cost extraction), enabling Stories 14.3/14.4 to implement vehicle and heating domains.
7. **AC-7: State storage** — Step results (cost matrix, expanded population metadata) are stored in `YearState.data` under stable module-level string keys.
8. **AC-8: Determinism** — Given identical inputs and seeds, the expansion and reshape produce identical outputs across runs. No randomness in this story (logit draws are Story 14.2).
9. **AC-9: Logging** — Step execution logs year, step name, original population size, expanded population size, and number of alternatives using structured key=value format.

## Tasks / Subtasks

- [ ] Task 1: Create `src/reformlab/discrete_choice/` module structure (AC: 1, 5)
  - [ ] 1.1: Create `__init__.py` with public API exports and module docstring
  - [ ] 1.2: Create `types.py` with frozen dataclasses: `Alternative`, `ChoiceSet`, `CostMatrix`, `ExpansionResult`
  - [ ] 1.3: Create `errors.py` with `DiscreteChoiceError`, `ExpansionError`, `ReshapeError`
  - [ ] 1.4: Create `domain.py` with `DecisionDomain` protocol (choice set definition, attribute overrides, cost extraction)

- [ ] Task 2: Implement population expansion logic (AC: 2, 3, 8)
  - [ ] 2.1: Create `expansion.py` with `expand_population(population: PopulationData, choice_set: ChoiceSet, domain: DecisionDomain) -> ExpansionResult`
  - [ ] 2.2: Implement row cloning — for each entity table in `PopulationData.tables`, clone rows M times
  - [ ] 2.3: Apply alternative-specific attribute overrides to each cloned segment
  - [ ] 2.4: Add `_alternative_id` and `_original_household_index` tracking columns to expanded tables
  - [ ] 2.5: Return `ExpansionResult` with expanded `PopulationData` + metadata (N, M, alternative names)

- [ ] Task 3: Implement cost matrix reshape (AC: 4, 8)
  - [ ] 3.1: Create `reshape.py` with `reshape_to_cost_matrix(result: ComputationResult, expansion: ExpansionResult, cost_column: str) -> CostMatrix`
  - [ ] 3.2: Extract cost column from computation result output table
  - [ ] 3.3: Reshape flat N×M array into N rows × M columns matrix (PyArrow StructArray or dict of arrays)
  - [ ] 3.4: Validate output dimensions match expansion metadata (N households × M alternatives)

- [ ] Task 4: Implement `DiscreteChoiceStep` class (AC: 1, 5, 7, 9)
  - [ ] 4.1: Create `step.py` with `DiscreteChoiceStep` implementing `OrchestratorStep` protocol
  - [ ] 4.2: Use `__slots__` pattern, properties for `name`, `depends_on`, `description`
  - [ ] 4.3: Constructor accepts `ComputationAdapter`, `DecisionDomain`, `PolicyConfig`, and configuration
  - [ ] 4.4: `execute()` method orchestrates: expand → compute → reshape → store in state
  - [ ] 4.5: Define stable state keys: `DISCRETE_CHOICE_COST_MATRIX_KEY`, `DISCRETE_CHOICE_EXPANSION_KEY`, `DISCRETE_CHOICE_METADATA_KEY`
  - [ ] 4.6: Add structured logging (INFO for step events, DEBUG for row counts)

- [ ] Task 5: Write tests (AC: all)
  - [ ] 5.1: Create `tests/discrete_choice/conftest.py` with fixtures: mock adapter, sample population, sample choice set, sample domain
  - [ ] 5.2: `test_types.py` — frozen dataclass validation, CostMatrix construction, Alternative immutability
  - [ ] 5.3: `test_expansion.py` — row cloning correctness, attribute override application, tracking column presence, N×M dimensions, determinism
  - [ ] 5.4: `test_reshape.py` — flat-to-matrix reshape, dimension validation, cost column extraction, error on mismatched dimensions
  - [ ] 5.5: `test_step.py` — protocol compliance (`is_protocol_step`), StepRegistry registration, full execute cycle with MockAdapter, state key storage, logging output
  - [ ] 5.6: Integration test — end-to-end expansion → compute → reshape with orchestrator runner

- [ ] Task 6: Lint, type-check, regression (AC: all)
  - [ ] 6.1: `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [ ] 6.2: Add mypy overrides in `pyproject.toml` if needed
  - [ ] 6.3: `uv run mypy src/`
  - [ ] 6.4: `uv run pytest tests/` — full regression suite passes

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**OrchestratorStep protocol** — from `src/reformlab/orchestrator/step.py:42-71`:
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: "YearState") -> "YearState": ...
```
Optional: `depends_on: tuple[str, ...]`, `description: str`.

**YearState** — from `src/reformlab/orchestrator/types.py:20-37`:
```python
@dataclass(frozen=True)
class YearState:
    year: int
    data: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```
State is immutable — update via `replace(state, data=new_data)`.

**ComputationAdapter.compute()** — from `src/reformlab/computation/adapter.py`:
```python
def compute(self, population: PopulationData, policy: PolicyConfig, period: int) -> ComputationResult
```

**PopulationData** — from `src/reformlab/computation/types.py`:
```python
@dataclass(frozen=True)
class PopulationData:
    tables: dict[str, pa.Table]
    metadata: dict[str, Any] = field(default_factory=dict)
```

**ComputationResult** — from `src/reformlab/computation/types.py`:
```python
@dataclass(frozen=True)
class ComputationResult:
    output_fields: pa.Table  # OutputFields alias
    adapter_version: str
    period: int
    metadata: dict[str, Any] = field(default_factory=dict)
    entity_tables: dict[str, pa.Table] = field(default_factory=dict)
```

### Existing Code Patterns to Follow

**Step class pattern** (reference: `src/reformlab/orchestrator/carry_forward.py`, `src/reformlab/vintage/transition.py`):
- `__slots__` for memory efficiency
- Properties for `name`, `depends_on`, `description`
- Frozen dataclass for configuration with `__post_init__` validation
- Custom exceptions with context (year, step_name, original_error)
- Module-level stable string key constants (e.g., `COMPUTATION_RESULT_KEY = "computation_result"`)
- Sorted deterministic processing order
- `replace(state, data=new_data)` for immutable state updates

**ComputationStep adapter integration pattern** (reference: `src/reformlab/orchestrator/computation_step.py`):
- Accepts `ComputationAdapter`, `PopulationData`, `PolicyConfig` in constructor
- Calls `adapter.compute(population, policy, period=year)`
- Wraps adapter errors in step-specific exception with context
- Logs adapter_version, row_count, year in structured format

**Module structure pattern** (reference: `src/reformlab/vintage/`):
```
src/reformlab/discrete_choice/
├── __init__.py       # Public API exports + module docstring
├── types.py          # Frozen dataclasses: Alternative, ChoiceSet, CostMatrix, ExpansionResult
├── errors.py         # DiscreteChoiceError hierarchy
├── domain.py         # DecisionDomain protocol
├── expansion.py      # Population expansion logic
├── reshape.py        # Cost matrix reshape logic
└── step.py           # DiscreteChoiceStep class
```

### Population Expansion Design

From the [design note](../../_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md):

```
Original population:     N households
Expand by alternatives:  N × M options = N×M "virtual" households
Run OpenFisca:           compute(expanded_population, policy, year)
Reshape results:         N × M cost matrix
```

**Expansion implementation detail:**
- For each entity table in `PopulationData.tables`, concatenate M copies
- Each copy has attributes modified per the alternative's attribute overrides (e.g., copy 2 might set `vehicle_type = "ev"`, `fuel_cost = 0.15`)
- Add `_alternative_id` column (0..M-1) and `_original_index` column (0..N-1) for reshape tracking
- The expanded `PopulationData` is a valid input to `ComputationAdapter.compute()` — no adapter changes needed

**Cost matrix representation:**
- Use a frozen dataclass wrapping a `pa.Table` with N rows and M named columns (one per alternative)
- Or: dict mapping alternative name → `pa.Array` of length N
- Each cell `[i, j]` = cost for household i choosing alternative j (as computed by OpenFisca)

### DecisionDomain Protocol Design

This story defines the protocol; Stories 14.3 and 14.4 implement it for vehicle and heating domains.

```python
@runtime_checkable
class DecisionDomain(Protocol):
    @property
    def name(self) -> str:
        """Domain identifier (e.g., 'vehicle', 'heating')."""
        ...

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        """Available alternatives in this domain."""
        ...

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table:
        """Modify population table attributes for a given alternative."""
        ...

    def extract_cost(
        self, result: ComputationResult, alternative: Alternative
    ) -> pa.Array:
        """Extract the cost value from computation results for an alternative."""
        ...
```

### Performance Notes

From design note performance analysis:
- 100k households × 5 alternatives = 500k rows per domain per year
- OpenFisca is vectorized — processes arrays, so 500k rows is ~5x cost, not 500k separate calls
- Eligibility filtering (Story 14.5) will reduce this further
- For this story: focus on correctness, not optimization; 14.5 adds eligibility filtering

### Key Design Decisions

1. **Single batch call, not per-alternative calls** — the adapter receives one N×M population, not M calls of size N. This is critical for performance with OpenFisca's vectorized engine.
2. **DecisionDomain as Protocol, not ABC** — follows project convention of structural typing with `@runtime_checkable`.
3. **New subsystem module `discrete_choice/`** — follows the same pattern as `vintage/` (separate from `orchestrator/` but implementing `OrchestratorStep`).
4. **No logit model in this story** — expansion + compute + reshape only. The logit probability computation and seed-controlled draws are Story 14.2.
5. **No specific decision domains** — the protocol is generic. Vehicle (14.3) and heating (14.4) domains implement it.
6. **PyArrow throughout** — expansion and reshape operate on `pa.Table` / `pa.Array`. No pandas.

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 3.1, 3.2 | Depends on | OrchestratorStep protocol, StepRegistry |
| 3.5 | Pattern reference | ComputationStep adapter integration |
| 3.4 | Pattern reference | VintageTransitionStep (separate module, implements protocol) |
| 14.2 | Blocks | Logit model consumes the CostMatrix produced here |
| 14.3 | Blocks | Vehicle domain implements DecisionDomain protocol |
| 14.4 | Blocks | Heating domain implements DecisionDomain protocol |
| 14.5 | Blocks | Eligibility filtering wraps the expansion logic |

### Out of Scope Guardrails

- **DO NOT** implement logit probability computation or seed-controlled draws (Story 14.2)
- **DO NOT** implement specific vehicle or heating decision domains (Stories 14.3, 14.4)
- **DO NOT** implement eligibility filtering (Story 14.5)
- **DO NOT** modify any existing orchestrator files (`runner.py`, `step.py`, `types.py`, `computation_step.py`)
- **DO NOT** modify the `ComputationAdapter` protocol
- **DO NOT** use pandas — PyArrow only
- **DO NOT** add nested logit — conditional logit only, and even that is 14.2
- **DO NOT** add actual state mutation (household attribute updates after choice) — that's part of 14.3/14.4

### Testing Standards

- **Mirror structure:** `tests/discrete_choice/` with `__init__.py` and `conftest.py`
- **Class-based grouping:** `TestPopulationExpansion`, `TestCostMatrixReshape`, `TestDiscreteChoiceStep`, `TestDecisionDomainProtocol`
- **Protocol compliance test:** Verify `is_protocol_step(step)` returns `True` and step registers with `StepRegistry`
- **MockAdapter fixture:** Return known output values for deterministic reshape testing
- **MockDomain fixture:** Simple test domain with 3 alternatives that overrides one column
- **Golden value tests:** Hand-computed N×M expansion for small N=3, M=3 population
- **Determinism tests:** Same inputs → same expansion and reshape results
- **Edge cases:** Empty population (N=0), single alternative (M=1), single household (N=1), domain with no attribute overrides

### Edge Case Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty population (N=0) | Returns empty CostMatrix with correct M columns, no adapter call |
| Single alternative (M=1) | Expansion is identity (no cloning), cost matrix is N×1 |
| Missing cost column in result | `ReshapeError` with column name and available columns |
| Adapter compute failure | `DiscreteChoiceError` wrapping original error with year, step, domain context |
| Population with multiple entity tables | All entity tables are expanded consistently |
| Alternative with no attribute overrides | Cloned rows are identical to original (keep-current alternative) |

### Project Structure Notes

```
src/reformlab/
├── discrete_choice/          # NEW — Story 14.1
│   ├── __init__.py
│   ├── types.py
│   ├── errors.py
│   ├── domain.py
│   ├── expansion.py
│   ├── reshape.py
│   └── step.py
├── orchestrator/             # UNCHANGED — no modifications
├── vintage/                  # Reference pattern for module structure
├── computation/              # UNCHANGED — adapter protocol used, not modified
└── ...

tests/
├── discrete_choice/          # NEW — Story 14.1
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_types.py
│   ├── test_expansion.py
│   ├── test_reshape.py
│   └── test_step.py
└── ...
```

No new dependencies required — uses only existing pyarrow and standard library.

### References

- [Source: `src/reformlab/orchestrator/step.py` — OrchestratorStep protocol, StepRegistry, is_protocol_step]
- [Source: `src/reformlab/orchestrator/types.py` — YearState, OrchestratorConfig]
- [Source: `src/reformlab/computation/types.py` — PopulationData, PolicyConfig, ComputationResult]
- [Source: `src/reformlab/computation/adapter.py` — ComputationAdapter protocol]
- [Source: `src/reformlab/orchestrator/computation_step.py` — ComputationStep (adapter integration pattern)]
- [Source: `src/reformlab/vintage/transition.py` — VintageTransitionStep (step implementation pattern)]
- [Source: `src/reformlab/orchestrator/carry_forward.py` — CarryForwardStep (config + validation pattern)]
- [Source: `_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md` — Full design note]
- [Source: `docs/epics.md` — Epic 14 acceptance criteria, BKL-1401]
- [Source: `docs/project-context.md` — Project rules and conventions]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All architecture patterns extracted from existing codebase (OrchestratorStep, ComputationAdapter, YearState)
- Design note fully integrated (population expansion flow, performance analysis, decision domain spec)
- Cross-story dependencies mapped (14.2 logit, 14.3 vehicle, 14.4 heating, 14.5 eligibility)
- Out-of-scope guardrails explicitly defined to prevent scope creep
- Module structure mirrors `vintage/` subsystem pattern
- No existing interface changes required — purely additive

### File List

