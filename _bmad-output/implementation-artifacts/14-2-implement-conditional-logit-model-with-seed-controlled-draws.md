
# Story 14.2: Implement Conditional Logit Model with Seed-Controlled Draws

Status: dev-complete

## Story

As a **platform developer**,
I want a conditional logit model that computes choice probabilities from cost matrices and makes seed-controlled random draws,
so that household investment decisions are statistically grounded, fully reproducible, and ready for vehicle/heating domain integration.

## Acceptance Criteria

1. **AC-1: Logit probability computation** — Given an N×M `CostMatrix` and a `TasteParameters` (β coefficient), when the logit model computes, then choice probabilities are `P(j|C_i) = exp(V_ij) / Σ_k exp(V_ik)` for each household, where `V_ij = beta_cost × cost_ij`. Computation uses the log-sum-exp trick for numerical stability (subtract per-row max before exponentiation). If any cost value is `NaN` or `Inf`, a `LogitError` is raised with the invalid cell positions before computation proceeds.
2. **AC-2: Seed-controlled draws** — Given choice probabilities and a random seed (from `YearState.seed`), when draws are made, then each household is assigned exactly one chosen alternative per decision domain. Draws use `random.Random(seed)` instance (not global state) with inverse CDF sampling. If `seed` is `None`, draws proceed with an unseeded `random.Random()` and a governance warning is logged.
3. **AC-3: Reproducibility** — Given identical cost matrices and identical seeds, when draws are made twice, then the chosen alternatives are bit-identical across runs. Household draw order is deterministic (sorted household index 0..N-1).
4. **AC-4: Stochastic variation** — Given a different seed, when draws are made, then household-level choices differ but the aggregate choice distribution remains statistically consistent with the probability distribution. Verified by tolerance-based comparison: for N ≥ 1000, each alternative's observed frequency must be within 5× standard error of its expected probability (`|observed_freq - expected_prob| < 5 * sqrt(expected_prob * (1 - expected_prob) / N)`). No external statistical library required.
5. **AC-5: Probability normalization** — Given the logit model, when probabilities are computed, then all probability vectors sum to 1.0 within floating-point tolerance (`|sum - 1.0| < 1e-10`) for each household. Verified by `__post_init__` validation on `ChoiceResult`.
6. **AC-6: Type system** — `TasteParameters` is a frozen dataclass with `beta_cost: float`. `ChoiceResult` is a frozen dataclass containing `chosen` (`pa.Array` of string alternative IDs, length N), `probabilities` (`pa.Table` N×M), `utilities` (`pa.Table` N×M), `alternative_ids` (`tuple[str, ...]`), and `seed` (`int | None`).
7. **AC-7: Step integration** — `LogitChoiceStep` implements the `OrchestratorStep` protocol, reads `CostMatrix` from `YearState.data[DISCRETE_CHOICE_COST_MATRIX_KEY]`, applies the logit model, and stores `ChoiceResult` in `YearState.data[DISCRETE_CHOICE_RESULT_KEY]`. It depends on `DiscreteChoiceStep` by default (`depends_on=("discrete_choice",)`).
8. **AC-8: State storage** — Step results are stored in `YearState.data` under stable module-level string key: `DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"` → `ChoiceResult` instance. Taste parameters are recorded by creating a new dict from the existing `DISCRETE_CHOICE_METADATA_KEY` contents plus keys `beta_cost` (`float`) and `choice_seed` (`int | None`), stored back via `dataclasses.replace()` (never mutate the existing dict in-place).
9. **AC-9: Logging** — Step execution logs year, step name, N households, M alternatives, β coefficient, and seed using structured key=value format. A `WARNING`-level log is emitted if `seed is None`.
10. **AC-10: No interface changes** — No modifications to `DiscreteChoiceStep`, `ComputationAdapter`, `YearState`, `OrchestratorConfig`, or orchestrator loop logic. The step is purely additive.

## Tasks / Subtasks

- [x] Task 1: Add `TasteParameters` and `ChoiceResult` to `types.py` (AC: 6)
  - [x] 1.1: Add `TasteParameters` frozen dataclass with `beta_cost: float`
  - [x] 1.2: Add `ChoiceResult` frozen dataclass with `chosen` (`pa.Array`), `probabilities` (`pa.Table`), `utilities` (`pa.Table`), `alternative_ids` (`tuple[str, ...]`), `seed` (`int | None`)
  - [x] 1.3: Add `__post_init__` validation on `ChoiceResult`: probability row sums within tolerance, column names match `alternative_ids`, `chosen` length equals N

- [x] Task 2: Add `LogitError` to `errors.py` (AC: 1, 2)
  - [x] 2.1: Add `LogitError(DiscreteChoiceError)` for probability computation or draw failures

- [x] Task 3: Implement `logit.py` with pure functions (AC: 1, 2, 3, 5)
  - [x] 3.1: Implement `compute_utilities(cost_matrix: CostMatrix, taste_parameters: TasteParameters) -> pa.Table` — returns N×M table where `V_ij = beta_cost × cost_ij`
  - [x] 3.2: Implement `compute_probabilities(utilities: pa.Table) -> pa.Table` — applies softmax per row using log-sum-exp trick: subtract per-row max, exponentiate, normalize. Returns N×M probability table with same column names.
  - [x] 3.3: Implement `draw_choices(probabilities: pa.Table, alternative_ids: tuple[str, ...], seed: int | None) -> ChoiceResult` — uses `random.Random(seed)` for inverse CDF sampling over each household row in deterministic order (0..N-1). Returns `ChoiceResult` with all fields populated.

- [x] Task 4: Implement `LogitChoiceStep` in `logit.py` (AC: 7, 8, 9, 10)
  - [x] 4.1: Create `LogitChoiceStep` implementing `OrchestratorStep` protocol with `__slots__`
  - [x] 4.2: Constructor accepts `TasteParameters`, optional `cost_matrix_key` (default: `DISCRETE_CHOICE_COST_MATRIX_KEY`), `name` (default: `"logit_choice"`), `depends_on` (default: `("discrete_choice",)`)
  - [x] 4.3: `execute()` reads CostMatrix from state, calls `compute_utilities` → `compute_probabilities` → `draw_choices` with `state.seed`
  - [x] 4.4: Stores `ChoiceResult` under `DISCRETE_CHOICE_RESULT_KEY`; creates a new dict from existing `DISCRETE_CHOICE_METADATA_KEY` contents plus `beta_cost` and `choice_seed`, stores new dict back via `dataclasses.replace()`
  - [x] 4.5: Structured key=value logging at INFO (step_start, step_complete) and WARNING (null seed)

- [x] Task 5: Update `__init__.py` with new exports (AC: 6, 7, 8)
  - [x] 5.1: Export `TasteParameters`, `ChoiceResult`, `LogitChoiceStep`, `LogitError`, `DISCRETE_CHOICE_RESULT_KEY`
  - [x] 5.2: Export pure functions `compute_utilities`, `compute_probabilities`, `draw_choices`

- [x] Task 6: Write tests (AC: all)
  - [x] 6.1: Add `ChoiceResult` and `TasteParameters` fixtures to `conftest.py`
  - [x] 6.2: `test_types.py` — Add tests for `TasteParameters` immutability, `ChoiceResult` construction and `__post_init__` validation (invalid probability sums, column mismatch, wrong chosen length)
  - [x] 6.3: `test_logit.py` — `TestComputeUtilities`: correct V_ij values, empty matrix, zero beta, negative beta
  - [x] 6.4: `test_logit.py` — `TestComputeProbabilities`: softmax correctness, sum-to-one, numerical stability (large values), equal costs → uniform distribution, single alternative → probability 1.0
  - [x] 6.5: `test_logit.py` — `TestDrawChoices`: determinism (same seed same result), variation (different seed different choices), single alternative always chosen, empty population, inverse CDF correctness with known probabilities
  - [x] 6.6: `test_logit.py` — `TestLogitChoiceStep`: protocol compliance, StepRegistry registration, full execute cycle (reads CostMatrix from state, stores ChoiceResult), metadata extension, null-seed warning log, missing CostMatrix error
  - [x] 6.7: Golden value test — hand-computed 3×3 logit probabilities and draws with known seed

- [x] Task 7: Lint, type-check, regression (AC: all)
  - [x] 7.1: `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [x] 7.2: `uv run mypy src/reformlab/discrete_choice/`
  - [x] 7.3: `uv run mypy src/`
  - [x] 7.4: `uv run pytest tests/` — full regression suite passes

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Conditional logit formula:**
```
V_ij = β_cost × cost_ij                          # deterministic utility
P(j|C_i) = exp(V_ij) / Σ_k∈C exp(V_ik)          # choice probability
```

**Numerically stable implementation (log-sum-exp trick):**
```
V_max_i = max_j(V_ij)                            # per-household max
P(j|C_i) = exp(V_ij - V_max_i) / Σ_k exp(V_ik - V_max_i)
```
This prevents overflow when β × cost produces large absolute values.

**Seed-controlled draw (inverse CDF sampling):**
```python
rng = random.Random(seed)                         # isolated RNG instance
for i in range(n_households):                     # deterministic order
    u = rng.random()                               # uniform [0, 1)
    cumulative = 0.0
    for j in range(m_alternatives):
        cumulative += probabilities[i][j]
        if u < cumulative:
            chosen[i] = alternative_ids[j]
            break
    else:
        chosen[i] = alternative_ids[-1]            # numerical safety
```

**CRITICAL: Use `random.Random(seed)`, NOT global `random.seed()`** — the project uses `random` stdlib, NOT numpy. Numpy is NOT in the dependency list. Using an instance avoids global state pollution and is thread-safe.

### CostMatrix Integration (from Story 14.1)

The `CostMatrix` from Story 14.1 is a frozen dataclass wrapping a `pa.Table`:
- **N rows** = households, **M columns** = alternatives
- Column names are alternative IDs (e.g., `"option_a"`, `"option_b"`)
- Each cell `[i, j]` = cost for household i choosing alternative j
- Stored in `YearState.data[DISCRETE_CHOICE_COST_MATRIX_KEY]`
- Access via: `cost_matrix.table`, `cost_matrix.alternative_ids`, `cost_matrix.n_households`, `cost_matrix.n_alternatives`

### Seed Handling Pattern (from orchestrator)

- `YearState.seed` is `int | None`, derived as `master_seed ^ year` by the orchestrator runner
- Steps receive the year's seed in `state.seed`
- If `seed is None`: orchestrator is running without seed control (non-deterministic mode)
- **Convention**: Use `random.Random(seed)` for reproducible draws; log WARNING if seed is None
- **DO NOT** derive per-household sub-seeds (no `seed ^ household_index`). Sequential draws from a single seeded `random.Random` instance are deterministic and simpler.

### Existing Step Implementation Pattern

Reference: `DiscreteChoiceStep` in `src/reformlab/discrete_choice/step.py`:
- `__slots__` for memory efficiency
- Properties for `name`, `depends_on`, `description`
- `execute(year, state) -> YearState` returns new state via `replace(state, data=new_data)`
- Wraps errors in `DiscreteChoiceError` with context (year, step_name, domain_name)
- Structured logging: `year=%d step_name=%s event=step_start`

### State Key Integration

Story 14.1 stores:
```python
DISCRETE_CHOICE_COST_MATRIX_KEY = "discrete_choice_cost_matrix"     # CostMatrix
DISCRETE_CHOICE_EXPANSION_KEY = "discrete_choice_expansion"         # ExpansionResult
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"           # dict
```

Story 14.2 adds:
```python
DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"               # ChoiceResult
```

Story 14.2 also **extends** the existing `DISCRETE_CHOICE_METADATA_KEY` dict with:
- `"beta_cost"`: float — the taste parameter used
- `"choice_seed"`: int | None — the seed used for draws

### Key Design Decisions

1. **Pure functions + step class** — `compute_utilities`, `compute_probabilities`, `draw_choices` are pure functions in `logit.py`. `LogitChoiceStep` composes them. This allows 14.3/14.4 to use the functions directly or via the step.
2. **`random.Random` instance, NOT numpy** — numpy is not in the project dependencies. Use stdlib `random.Random(seed)` for isolated, reproducible RNG.
3. **`math.exp` for exponentiation** — standard library, no external dependency.
4. **Single `beta_cost` coefficient** — the CostMatrix has one cost per alternative per household (total cost after OpenFisca). Multi-component utilities (β_purchase + β_annual + ...) are a future extension for 14.3/14.4 or Epic 15 (calibration).
5. **`LogitChoiceStep` as separate step** — runs after `DiscreteChoiceStep` in the pipeline (`depends_on=("discrete_choice",)`). Does NOT modify `DiscreteChoiceStep` (AC-10).
6. **`ChoiceResult` uses `pa.Array` for `chosen`** — consistent with PyArrow-first convention. Large N (100k) is handled efficiently. Will integrate with panel output in Story 14.6.
7. **No domain-specific logic** — the logit model is generic. Domain-specific concerns (which alternatives, what costs) are handled by `DecisionDomain` (14.3/14.4).

### Edge Case Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty cost matrix (N=0) | Return empty `ChoiceResult` with 0-length arrays and correct M columns |
| Single alternative (M=1) | All probabilities = 1.0, all households choose the single alternative |
| All costs equal | Uniform distribution: P = 1/M for each alternative |
| `beta_cost = 0.0` | Utility = 0 for all → uniform distribution (1/M) |
| `beta_cost > 0` | Higher cost → higher utility → more likely chosen (unusual but valid) |
| `seed = None` | Non-deterministic draws with WARNING log; `ChoiceResult.seed = None` |
| Very large `|beta × cost|` | Log-sum-exp trick prevents overflow; probabilities remain valid |
| `NaN` or `Inf` in cost matrix | `LogitError` with descriptive message listing the invalid cell positions |
| Missing CostMatrix in state | `DiscreteChoiceError` with available state keys listed |

### Testing Standards

- **Mirror structure:** Tests in `tests/discrete_choice/test_logit.py`
- **Class-based grouping:** `TestComputeUtilities`, `TestComputeProbabilities`, `TestDrawChoices`, `TestLogitChoiceStep`
- **Protocol compliance test:** Verify `is_protocol_step(step)` and StepRegistry registration
- **Golden value test:** Hand-computed 3×3 logit with known β and seed, verified probabilities and draws
- **Determinism tests:** Same inputs + same seed → identical `ChoiceResult`
- **Statistical test:** Different seeds produce different individual choices but consistent aggregate proportions (tolerance-based: for N ≥ 1000, `|observed_freq - expected_prob| < 5 * sqrt(expected_prob * (1 - expected_prob) / N)` per alternative; no scipy required)
- **Numerical stability test:** β × cost values in range [-1000, +1000] should produce valid probabilities
- **Sum-to-one test:** Every probability row sums to 1.0 within 1e-10 tolerance

### Project Structure Notes

```
src/reformlab/discrete_choice/
├── __init__.py       # Updated: add new exports
├── types.py          # Updated: add TasteParameters, ChoiceResult
├── errors.py         # Updated: add LogitError
├── domain.py         # UNCHANGED
├── expansion.py      # UNCHANGED
├── reshape.py        # UNCHANGED
├── step.py           # UNCHANGED (DiscreteChoiceStep from 14.1)
└── logit.py          # NEW — pure logit functions + LogitChoiceStep

tests/discrete_choice/
├── __init__.py       # UNCHANGED
├── conftest.py       # Updated: add TasteParameters/ChoiceResult fixtures
├── test_types.py     # Updated: add TasteParameters/ChoiceResult tests
├── test_expansion.py # UNCHANGED
├── test_reshape.py   # UNCHANGED
├── test_step.py      # UNCHANGED
└── test_logit.py     # NEW — logit model and LogitChoiceStep tests
```

No new dependencies required — uses only existing `pyarrow`, `random` (stdlib), and `math` (stdlib).

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 14.1 | Depends on | Consumes `CostMatrix` stored by `DiscreteChoiceStep` |
| 14.3 | Blocks | Vehicle domain uses `ChoiceResult` to update household state |
| 14.4 | Blocks | Heating domain uses `ChoiceResult` to update household state |
| 14.5 | Blocks | Eligibility filtering wraps the expansion before logit |
| 14.6 | Blocks | Panel output records `ChoiceResult` fields (chosen, probabilities, utilities) |
| 15.2 | Blocks | Calibration engine optimizes `TasteParameters.beta_cost` |

### Out of Scope Guardrails

- **DO NOT** implement nested logit — conditional logit only
- **DO NOT** implement multi-component utilities (multiple β coefficients per cost component) — single `beta_cost` only
- **DO NOT** implement specific vehicle or heating decision domains (Stories 14.3, 14.4)
- **DO NOT** implement eligibility filtering (Story 14.5)
- **DO NOT** modify `DiscreteChoiceStep`, `expansion.py`, `reshape.py`, or `step.py`
- **DO NOT** modify any orchestrator files (`runner.py`, `step.py`, `types.py`)
- **DO NOT** modify the `ComputationAdapter` protocol
- **DO NOT** add numpy or any new dependency
- **DO NOT** update household state after choice (that's 14.3/14.4)
- **DO NOT** implement calibration of β parameters (that's Epic 15)

### References

- [Source: `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep, state keys, execute pattern]
- [Source: `src/reformlab/discrete_choice/types.py` — CostMatrix, Alternative, ChoiceSet, ExpansionResult]
- [Source: `src/reformlab/discrete_choice/errors.py` — DiscreteChoiceError hierarchy]
- [Source: `src/reformlab/discrete_choice/__init__.py` — Public API exports]
- [Source: `src/reformlab/orchestrator/types.py` — YearState (seed: int | None)]
- [Source: `src/reformlab/orchestrator/runner.py:362-379` — _derive_year_seed: master_seed ^ year]
- [Source: `src/reformlab/orchestrator/step.py:42-71` — OrchestratorStep protocol, StepRegistry, is_protocol_step]
- [Source: `src/reformlab/data/synthetic.py` — random.seed pattern for deterministic generation]
- [Source: `src/reformlab/population/methods/conditional.py` — random.Random usage pattern]
- [Source: `_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md` — Logit formula, decision flow, taste parameters]
- [Source: `docs/epics.md` — Epic 14 acceptance criteria, BKL-1402]
- [Source: `docs/project-context.md` — Project rules: no numpy, random stdlib, PyArrow-first, frozen dataclasses]
- [Source: `pyproject.toml` — Dependencies: no numpy, uses random stdlib]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging cycles needed.

### Implementation Plan

TDD approach: for each task, wrote failing tests first (RED), implemented minimal code (GREEN), then verified with lint/type-check.

1. Tasks 1+2 together: Added TasteParameters, ChoiceResult to types.py and LogitError to errors.py. ChoiceResult __post_init__ validates probability sums, column names, and chosen length.
2. Task 3: Implemented compute_utilities (with NaN/Inf validation), compute_probabilities (log-sum-exp softmax), draw_choices (inverse CDF with random.Random instance) as pure functions in logit.py.
3. Task 4: Implemented LogitChoiceStep with __slots__, OrchestratorStep protocol, structured logging, metadata extension via new dict (no in-place mutation).
4. Task 5: Updated __init__.py with all new exports.
5. Task 6: 35 test cases in test_logit.py (utilities, probabilities, draws, step integration, golden values), 7 new tests in test_types.py, 2 fixtures in conftest.py.
6. Task 7: ruff, mypy (strict), full regression suite — all green.

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All architecture patterns extracted from existing codebase (OrchestratorStep, seed handling, CostMatrix)
- Design note logit formula and decision flow fully integrated
- Dependency constraint verified: numpy NOT available, use stdlib random + math
- Cross-story dependencies mapped (14.1 CostMatrix input, 14.3/14.4 ChoiceResult output, 15.2 calibration)
- Out-of-scope guardrails explicitly defined (no nested logit, no multi-β, no domain logic)
- Numerical stability approach specified (log-sum-exp trick)
- Seed handling pattern documented (random.Random instance, not global state)
- Edge cases comprehensively defined (empty matrix, single alternative, null seed, NaN costs)
- Antipatterns from 14.1 addressed: single representation for ChoiceResult, clear ownership of logit computation, consistent naming
- All 10 ACs satisfied: logit formula (AC-1), seed-controlled draws (AC-2), reproducibility (AC-3), stochastic variation (AC-4), probability normalization (AC-5), type system (AC-6), step integration (AC-7), state storage (AC-8), logging (AC-9), no interface changes (AC-10)
- Full regression: 2334 tests passed, 0 failures, mypy strict clean on 128 source files

### File List

#### New Files
- `src/reformlab/discrete_choice/logit.py` — Pure logit functions (compute_utilities, compute_probabilities, draw_choices) + LogitChoiceStep + DISCRETE_CHOICE_RESULT_KEY
- `tests/discrete_choice/test_logit.py` — 35 tests: TestComputeUtilities (6), TestComputeProbabilities (7), TestDrawChoices (8), TestGoldenValues (1), TestLogitChoiceStep (13)

#### Modified Files
- `src/reformlab/discrete_choice/types.py` — Added TasteParameters (frozen, beta_cost), ChoiceResult (frozen, __post_init__ validation)
- `src/reformlab/discrete_choice/errors.py` — Added LogitError(DiscreteChoiceError)
- `src/reformlab/discrete_choice/__init__.py` — Exported TasteParameters, ChoiceResult, LogitChoiceStep, LogitError, DISCRETE_CHOICE_RESULT_KEY, compute_utilities, compute_probabilities, draw_choices
- `tests/discrete_choice/conftest.py` — Added sample_taste_parameters, sample_cost_matrix fixtures
- `tests/discrete_choice/test_types.py` — Added TestTasteParameters (4 tests), TestChoiceResult (7 tests)

