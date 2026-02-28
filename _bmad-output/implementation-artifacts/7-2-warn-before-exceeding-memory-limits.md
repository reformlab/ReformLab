# Story 7.2: Warn Before Exceeding Memory Limits

Status: ready-for-dev

## Story

As a **policy analyst or researcher**,
I want **the system to warn me before attempting to run a simulation that is likely to exceed available memory**,
so that **I can adjust my population size or expectations before waiting for a run that will crash or hang**.

## Acceptance Criteria

From backlog (BKL-702), aligned with NFR3.

1. **AC-1: Memory warning displayed for large populations on constrained machines**
   - Given a population exceeding 500k households on a 16GB machine
   - When a run is attempted
   - Then a clear memory warning is displayed before execution begins

2. **AC-2: No warning for populations within safe limits**
   - Given a population within the safe memory threshold
   - When a run is attempted
   - Then no warning is shown and execution proceeds normally

3. **AC-3: Warning includes actionable guidance**
   - Given a memory warning is triggered
   - When the warning is displayed
   - Then it includes: estimated memory requirement, available memory, population size, projection years, and suggested remediation (reduce population size, reduce projection horizon, increase available memory, or intentionally bypass with documented override)

4. **AC-4: Warning is configurable and can be suppressed**
   - Given a user who wants to proceed despite the warning
   - When they configure `REFORMLAB_SKIP_MEMORY_WARNING=true` or pass `skip_memory_check=True`
   - Then the warning is suppressed and execution proceeds

5. **AC-5: Memory check is fast and non-blocking**
   - Given a memory check before execution
   - When invoked
   - Then the check completes in under 100ms and does not impact simulation performance

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependencies (from backlog BKL-702):**
  - Story 7-1 (BKL-701): Benchmark suite completed (DONE) — establishes performance baseline

- **Integration dependencies:**
  - Story 6-1 (BKL-601): Stable API surface for user-facing warning entrypoint (DONE)
  - Story 6-6 (BKL-606): Canonical user-facing warning/error message format (DONE)
  - Story 5-2 (BKL-502): Manifest warning capture helpers (`capture_warnings`) (DONE)
  - Story 3-5 (BKL-305): Orchestrator execution flow where pre-run checks occur (DONE)

- **Follow-on stories (not in scope here):**
  - Story 7-3 (BKL-703): Enforce CI quality gates
  - Story 7-4 (BKL-704): External pilot run carbon-tax workflow
  - Story 7-5 (BKL-705): Define Phase 1 exit checklist and pilot sign-off criteria

## Tasks / Subtasks

- [ ] **Task 0: Review prerequisite contracts and dependency status** (AC: dependency check)
  - [ ] Confirm dependencies in `sprint-status.yaml` for 7-1, 6-1, 6-6, 5-2, 3-5
  - [ ] Review `interfaces/api.py` run_scenario() entrypoint for pre-execution hook location
  - [ ] Review `governance/capture.py` warning capture patterns
  - [ ] Review `interfaces/errors.py` for warning/error patterns

- [ ] **Task 1: Create memory estimation module in governance layer** (AC: 1, 3, 5)
  - [ ] Add `src/reformlab/governance/memory.py`
  - [ ] Implement `MemoryEstimate` dataclass:
    - `population_size: int` (row count)
    - `projection_years: int`
    - `estimated_bytes: int` (memory estimate for simulation)
    - `available_bytes: int` (system available memory)
    - `threshold_bytes: int` (safe threshold for target environment)
    - `exceeds_threshold` as a computed property (not duplicated state)
  - [ ] Implement `estimate_memory_usage(population_size: int, projection_years: int) -> MemoryEstimate`
    - Use baseline heuristic from benchmark context: `population_size * projection_years * 800` bytes
    - Apply configurable safety multiplier (default `2.0`) via `REFORMLAB_MEMORY_MULTIPLIER`
  - [ ] Implement `get_available_memory() -> int` using `psutil` or fallback detection
  - [ ] Export from `src/reformlab/governance/__init__.py`

- [ ] **Task 2: Create memory warning types in interfaces layer** (AC: 1, 3)
  - [ ] Add `MemoryWarning` class to `src/reformlab/interfaces/errors.py`:
    - Follow canonical format: "[What] — [Why] — [How to fix]"
    - Include `estimate: MemoryEstimate` for structured access
    - Include clear message with population size, estimated MB, available MB, threshold MB
  - [ ] Add `MemoryCheckResult` dataclass to `src/reformlab/interfaces/api.py`:
    - `should_warn: bool`
    - `estimate: MemoryEstimate`
    - `message: str` (formatted warning if applicable)

- [ ] **Task 3: Implement pre-execution memory check** (AC: 1, 2, 4, 5)
  - [ ] Add `check_memory_requirements(config: RunConfig | ScenarioConfig, skip_check: bool = False) -> MemoryCheckResult` to `interfaces/api.py`
  - [ ] Add `REFORMLAB_SKIP_MEMORY_WARNING` env var support
  - [ ] Add `skip_memory_check` parameter to `run_scenario()` API
  - [ ] Integrate check into `run_scenario()` before orchestrator execution
  - [ ] Ensure check completes in < 100ms (no disk I/O, pure estimation)

- [ ] **Task 4: Implement memory warning emission** (AC: 1, 3)
  - [ ] On threshold exceeded: emit Python `warnings.warn()` with `MemoryWarning`
  - [ ] Log warning at WARNING level via standard logger
  - [ ] Include warning text in run manifest `warnings` via `capture_warnings(..., additional_warnings=[...])`
  - [ ] Warning message format:
    ```
    Memory warning — Population of {N} households over {Y} years requires ~{X}GB,
    but only {M}GB available (threshold: {T}GB for safe operation on 16GB machine) —
    Reduce population size, increase available memory, or set REFORMLAB_SKIP_MEMORY_WARNING=true to proceed
    ```

- [ ] **Task 5: Write unit tests for memory estimation** (AC: 1, 2, 3, 5)
  - [ ] Add `tests/governance/test_memory.py`
  - [ ] Test `estimate_memory_usage()` returns reasonable estimates for known population sizes
  - [ ] Test threshold comparison logic (above/below)
  - [ ] Test performance: estimation completes in < 100ms for 1M households
  - [ ] Test `get_available_memory()` returns positive integer

- [ ] **Task 6: Write integration tests for warning flow** (AC: 1, 2, 4)
  - [ ] Add `tests/interfaces/test_memory_warning.py`
  - [ ] Test: Large population triggers warning via `run_scenario()`
  - [ ] Test: Small population does not trigger warning
  - [ ] Test: `skip_memory_check=True` suppresses warning
  - [ ] Test: `REFORMLAB_SKIP_MEMORY_WARNING=true` env var suppresses warning
  - [ ] Test: Warning appears in run manifest `warnings` field

- [ ] **Task 7: Run quality checks** (AC: all)
  - [ ] Run `ruff check src/reformlab/governance src/reformlab/interfaces tests/governance tests/interfaces`
  - [ ] Run `mypy src/reformlab/governance src/reformlab/interfaces`
  - [ ] Run targeted tests: `pytest tests/governance tests/interfaces -v -k memory`

## Dev Notes

### Architecture Alignment

This story implements memory-limit warnings from PRD NFR3 and directly addresses BKL-702 acceptance criteria.

**Layered architecture integration:**
- Memory estimation lives in `governance/` (operational guardrails concern)
- Warning types live in `interfaces/errors.py` (user-facing error/warning layer)
- Pre-execution check integrates into `interfaces/api.py` run_scenario() flow
- Uses existing manifest warning capture pattern from `governance/capture.py`

**Key existing modules to use:**
- `src/reformlab/interfaces/api.py` - run_scenario() entrypoint where check integrates
- `src/reformlab/interfaces/errors.py` - Error/warning type patterns
- `src/reformlab/governance/capture.py` - `capture_warnings()` pattern
- `src/reformlab/governance/benchmarking.py` - Pattern for structured result dataclasses

### Code Patterns to Follow

**Warning dataclass pattern (from governance/benchmarking.py):**
```python
@dataclass(frozen=True)
class MemoryEstimate:
    """Memory usage estimate for a simulation run."""
    population_size: int
    projection_years: int
    estimated_bytes: int
    available_bytes: int
    threshold_bytes: int

    @property
    def exceeds_threshold(self) -> bool:
        return self.estimated_bytes > min(self.available_bytes, self.threshold_bytes)

    @property
    def estimated_gb(self) -> float:
        return self.estimated_bytes / (1024 ** 3)

    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024 ** 3)

    def __repr__(self) -> str:
        status = "EXCEEDS THRESHOLD" if self.exceeds_threshold else "OK"
        return (
            f"MemoryEstimate({status}, population={self.population_size:,}, "
            f"years={self.projection_years}, est={self.estimated_gb:.1f}GB, "
            f"avail={self.available_gb:.1f}GB)"
        )
```

**Error pattern (from interfaces/errors.py:55-79):**
```python
class MemoryWarning(UserWarning):
    """Warning emitted when simulation may exceed available memory.

    Follows canonical format: "[What] — [Why] — [How to fix]".
    """

    def __init__(self, estimate: MemoryEstimate) -> None:
        self.estimate = estimate
        message = (
            f"Memory warning — Population of {estimate.population_size:,} households "
            f"over {estimate.projection_years} years requires ~{estimate.estimated_gb:.1f}GB, "
            f"but only {estimate.available_gb:.1f}GB available — "
            "Reduce population size, increase available memory, or set "
            "REFORMLAB_SKIP_MEMORY_WARNING=true to proceed"
        )
        super().__init__(message)
```

**API integration pattern (at run_scenario() start):**
```python
def run_scenario(
    config: RunConfig | ScenarioConfig | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,
    *,
    skip_memory_check: bool = False,
) -> SimulationResult:
    # ... existing normalization/validation ...

    # Step 2b: Memory pre-check (before orchestration)
    if not skip_memory_check and not _should_skip_memory_check():
        check_result = check_memory_requirements(run_config)
        if check_result.should_warn:
            import warnings
            warnings.warn(MemoryWarning(check_result.estimate))
            logger.warning(check_result.message)

    # ... continue with orchestration ...
```

### Memory Estimation Heuristics

Based on Story 7-1 benchmark performance (100k households in ~8.4s), memory estimation uses:

| Component | Per Household-Year | Notes |
|-----------|-------------------|-------|
| Core state arrays (income, carbon_tax, etc.) | ~200 bytes | 5-10 float64 columns |
| Indicator buffers (deciles, aggregates) | ~100 bytes | During computation |
| Panel output (PyArrow table) | ~500 bytes | Including schema overhead |
| Safety margin | 2x multiplier | For peak usage during computation |

**Formula:**
```python
base_bytes = population_size * projection_years * 800  # ~800 bytes per household-year
estimated_bytes = base_bytes * 2  # 2x safety margin
```

**Thresholds (for 16GB target machine):**
- Safe threshold: 12GB (75% of 16GB, leaving room for OS and other processes)
- Warning threshold: Population × Years × 800 × 2 > available_memory × 0.75

### File Structure Requirements

```
src/reformlab/
  governance/
    memory.py              # MemoryEstimate, estimate_memory_usage, get_available_memory
    __init__.py            # Export memory APIs
  interfaces/
    errors.py              # Add MemoryWarning
    api.py                 # Add check_memory_requirements and update run_scenario

tests/
  governance/
    test_memory.py         # Memory estimation unit tests
  interfaces/
    test_memory_warning.py # Integration tests for warning flow
```

### Testing Standards

**Performance test:**
```python
import time

def test_memory_estimation_performance():
    """Memory estimation completes in under 100ms for large populations."""
    start = time.perf_counter()
    estimate = estimate_memory_usage(population_size=1_000_000, projection_years=20)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.1, f"Memory estimation took {elapsed:.3f}s, expected < 0.1s"
    assert estimate.population_size == 1_000_000
```

**Warning integration test:**
```python
import warnings
import pytest

def test_large_population_triggers_warning(monkeypatch):
    """Large populations trigger MemoryWarning via run_scenario."""
    # Mock available memory to 8GB
    monkeypatch.setattr("reformlab.governance.memory.get_available_memory", lambda: 8 * 1024**3)

    config = ScenarioConfig(
        template_name="test",
        parameters={},
        start_year=2025,
        end_year=2035,
        population_path=Path("tests/fixtures/large_population.parquet"),  # 600k rows
    )

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # This should trigger warning but proceed
        result = run_scenario(config, adapter=mock_adapter)

        assert len(w) == 1
        assert issubclass(w[0].category, MemoryWarning)
        assert "600,000 households" in str(w[0].message)
```

### Scope Guardrails

- **In scope:**
  - Pre-execution memory estimation and warning emission
  - Environment variable and parameter-based warning suppression
  - Memory warning in run manifest warnings field
  - Heuristic-based estimation (not actual measurement)

- **Out of scope:**
  - Actual memory profiling during execution (too slow)
  - Automatic population reduction or streaming
  - GPU memory estimation
  - Cross-platform memory detection edge cases (fallback to conservative estimate)
  - CI gating based on memory (Story 7-3)

### Previous Story Intelligence

From Story 7-1 (verify-simulation-outputs-against-benchmarks):
- Benchmark suite runs 100k households in ~8.4 seconds
- Uses deterministic 100k population fixture with fixed seed
- Pattern established for structured result dataclasses (`BenchmarkResult`, `BenchmarkSuiteResult`)
- Pattern established for governance module organization
- Tests in `tests/benchmarks/` with custom pytest marker

Apply learnings:
- Follow same dataclass patterns for `MemoryEstimate`
- Use same result/summary pattern for `MemoryCheckResult`
- Keep governance module focused on single responsibility
- Export public APIs cleanly from `__init__.py`

### Git Intelligence

Recent commits:
- `3ef1751` overnight-build: 7-1-verify-simulation-outputs-against-benchmarks — code review
- `7c732e4` overnight-build: 7-1-verify-simulation-outputs-against-benchmarks — dev story
- Story 7-1 files: `governance/benchmarking.py`, `tests/benchmarks/`

Pattern: New governance capabilities added as separate modules with clean exports.

### Project Structure Notes

- Memory estimation stays inside existing `governance` subsystem (no new top-level subsystem)
- Warning types stay in existing `interfaces/errors.py` (consistent with ConfigurationError pattern)
- API integration happens in existing `interfaces/api.py` run_scenario()
- Tests parallel existing test structure (`tests/governance/`, `tests/interfaces/`)

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-702] - Story requirements
- [Source: _bmad-output/planning-artifacts/prd.md#NFR3] - Memory limit handling requirement
- [Source: _bmad-output/planning-artifacts/prd.md#Computational-Performance] - Performance targets
- [Source: _bmad-output/planning-artifacts/architecture.md#Governance] - Governance layer patterns
- [Source: src/reformlab/interfaces/api.py] - run_scenario() entrypoint
- [Source: src/reformlab/interfaces/errors.py] - Error/warning patterns
- [Source: src/reformlab/governance/capture.py] - Warning capture patterns
- [Source: src/reformlab/governance/benchmarking.py] - Structured result dataclass patterns
- [Source: _bmad-output/implementation-artifacts/7-1-verify-simulation-outputs-against-benchmarks.md] - Previous story patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
