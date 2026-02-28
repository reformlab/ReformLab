# Story 7.1: Verify Simulation Outputs Against Published Benchmarks

Status: ready-for-dev

## Story

As a **policy analyst or researcher**,
I want **to verify simulation outputs against published reference benchmarks for carbon tax scenarios**,
so that **I can trust the simulation results and demonstrate credibility to stakeholders, policymakers, and peer reviewers**.

## Acceptance Criteria

1. **AC1: Benchmark suite completes in under 10 seconds for 100k households**
   - Given the benchmark suite and a 100k household synthetic population
   - When run on a standard laptop (4-core, 16GB RAM)
   - Then all benchmark tests complete in under 10 seconds total

2. **AC2: Results match published reference values within tolerances**
   - Given benchmark results from the simulation
   - When compared to published reference values (carbon tax revenue aggregates, distributional patterns)
   - Then deviations are within documented tolerances (e.g., ±0.1% for fiscal aggregates, ±1% for distributional shares)

3. **AC3: Clear failure diagnostics on benchmark mismatch**
   - Given a benchmark test failure
   - When the failure is reported
   - Then the output identifies: which metric failed, expected value, actual value, tolerance used, and deviation percentage

4. **AC4: Benchmark reference data is versioned and documented**
   - Given the benchmark reference data
   - When inspected
   - Then each reference value has documented source (publication, dataset, or calculation method)

5. **AC5: Benchmark can be run via pytest and Python API**
   - Given the benchmark suite
   - When invoked via `pytest tests/benchmarks/` or programmatic API
   - Then benchmarks execute and report pass/fail with diagnostics

## Tasks / Subtasks

- [ ] **Task 1: Create benchmark infrastructure** (AC: 3, 5)
  - [ ] Create `tests/benchmarks/` directory structure
  - [ ] Implement `BenchmarkResult` dataclass (passed, metric_name, expected, actual, tolerance, deviation, source)
  - [ ] Implement `BenchmarkSuite` class with `run()` method returning list of `BenchmarkResult`
  - [ ] Add `__repr__` for notebook-friendly display of benchmark results

- [ ] **Task 2: Create 100k household synthetic population fixture** (AC: 1)
  - [ ] Generate deterministic 100k household synthetic population with:
    - Income distribution matching French decile structure
    - Energy consumption patterns (housing type, heating, transport)
    - Regional distribution approximating French population
  - [ ] Store as fixture in `tests/benchmarks/fixtures/` (Parquet format)
  - [ ] Document generation method and seed for reproducibility

- [ ] **Task 3: Define benchmark reference values** (AC: 2, 4)
  - [ ] Create `tests/benchmarks/references/` directory
  - [ ] Create `carbon_tax_benchmarks.yaml` with reference values:
    - Aggregate carbon tax revenue at €44/tCO2
    - Mean tax burden by income decile (D1-D10)
    - Share of tax burden by decile (percentage)
  - [ ] Document source of each reference value (academic literature, official statistics, or calculation methodology)
  - [ ] Define tolerance for each metric type

- [ ] **Task 4: Implement fiscal aggregate benchmark** (AC: 1, 2, 3)
  - [ ] Test: Given 100k households at €44/tCO2, aggregate revenue matches reference within tolerance
  - [ ] Compute expected revenue from reference emissions × tax rate
  - [ ] Compare with simulated `carbon_tax` sum from panel output
  - [ ] Report clear pass/fail with deviation

- [ ] **Task 5: Implement distributional benchmark** (AC: 1, 2, 3)
  - [ ] Test: Given 100k households, mean carbon tax by decile matches reference pattern
  - [ ] Use `compute_distributional_indicators()` to compute decile means
  - [ ] Compare D1-D10 values against reference
  - [ ] Report per-decile pass/fail with deviations

- [ ] **Task 6: Implement performance benchmark** (AC: 1)
  - [ ] Test: Full 100k household simulation completes in under 10 seconds
  - [ ] Test: Distributional indicator computation completes in under 5 seconds
  - [ ] Use `time.perf_counter()` for accurate timing
  - [ ] Report timing results and pass/fail against NFR targets

- [ ] **Task 7: Add pytest integration** (AC: 5)
  - [ ] Create `tests/benchmarks/test_benchmark_suite.py`
  - [ ] Add `pytest.mark.benchmark` marker for optional slow-test skipping
  - [ ] Ensure benchmarks run in CI (but can be skipped with `-m "not benchmark"` for fast CI)

- [ ] **Task 8: Add public API for benchmark verification** (AC: 5)
  - [ ] Add `run_benchmarks()` function to `reformlab.interfaces.api`
  - [ ] Returns `BenchmarkSuiteResult` with list of benchmark outcomes
  - [ ] Provide clear summary output for notebook display

## Dev Notes

### Architecture Alignment

This story implements the "benchmark validation" capability described in the PRD's Scientific Rigor & Validation section and directly addresses NFR1 and NFR5 performance targets.

**Layered architecture integration:**
- Benchmarks exercise the full stack: Computation Adapter → Orchestrator → Indicators
- Uses existing `compute_distributional_indicators()` from `indicators/distributional.py`
- Uses existing `check_reproducibility()` pattern from `governance/reproducibility.py` as reference for structured result reporting

**Key existing modules to use:**
- `src/reformlab/indicators/distributional.py` - Decile-based indicator computation
- `src/reformlab/indicators/fiscal.py` - Fiscal indicator computation
- `src/reformlab/orchestrator/runner.py` - Orchestration execution
- `src/reformlab/computation/mock_adapter.py` - For deterministic benchmark fixtures
- `src/reformlab/governance/reproducibility.py` - Pattern for structured verification results

### Code Patterns to Follow

**Result dataclass pattern (from governance/reproducibility.py:27-60):**
```python
@dataclass(frozen=True)
class BenchmarkResult:
    """Result of a single benchmark test."""
    passed: bool
    metric_name: str
    expected: float
    actual: float
    tolerance: float
    deviation: float
    source: str  # Reference source documentation

    def details(self) -> str:
        """Return human-readable diagnostic summary."""
        status = "PASSED" if self.passed else "FAILED"
        return (
            f"{status}: {self.metric_name}\n"
            f"  Expected: {self.expected:.6f}\n"
            f"  Actual: {self.actual:.6f}\n"
            f"  Deviation: {self.deviation:.4%}\n"
            f"  Tolerance: ±{self.tolerance:.4%}\n"
            f"  Source: {self.source}"
        )
```

**Indicator computation pattern (from indicators/distributional.py):**
```python
from reformlab.indicators import compute_distributional_indicators
from reformlab.indicators.types import DistributionalConfig

config = DistributionalConfig(income_field="income", by_year=False)
result = compute_distributional_indicators(panel, config)
# Access: result.indicators[i].mean, result.indicators[i].decile
```

**API result pattern (from interfaces/api.py):**
```python
@dataclass(frozen=True)
class BenchmarkSuiteResult:
    """Result of running benchmark suite."""
    passed: bool
    results: list[BenchmarkResult]
    total_time_seconds: float

    def __repr__(self) -> str:
        passed_count = sum(1 for r in self.results if r.passed)
        return f"BenchmarkSuiteResult({passed_count}/{len(self.results)} passed, {self.total_time_seconds:.2f}s)"
```

### File Structure Requirements

```
tests/
  benchmarks/
    __init__.py
    conftest.py              # Pytest fixtures for benchmark population
    test_benchmark_suite.py  # Main benchmark tests
    fixtures/
      population_100k.parquet   # 100k household synthetic population
    references/
      carbon_tax_benchmarks.yaml  # Reference values with sources

src/reformlab/
  benchmarks/                # New module
    __init__.py
    types.py                 # BenchmarkResult, BenchmarkSuiteResult
    runner.py                # BenchmarkSuite class
    references.py            # Reference value loading
```

### Testing Standards

**Performance measurement:**
```python
import time

start = time.perf_counter()
# ... operation ...
elapsed = time.perf_counter() - start
assert elapsed < 10.0, f"Benchmark exceeded 10s limit: {elapsed:.2f}s"
```

**Tolerance comparison:**
```python
def within_tolerance(expected: float, actual: float, tolerance: float) -> bool:
    """Check if actual is within relative tolerance of expected."""
    if expected == 0:
        return abs(actual) <= tolerance
    return abs(actual - expected) / abs(expected) <= tolerance
```

**Pytest marker for benchmarks:**
```python
import pytest

pytestmark = pytest.mark.benchmark

def test_fiscal_aggregate_benchmark(benchmark_population):
    """Aggregate carbon tax revenue matches reference."""
    ...
```

### Reference Value Documentation

Each benchmark reference value must include:
1. **Value**: The expected numeric result
2. **Tolerance**: Acceptable deviation (relative, e.g., 0.01 = 1%)
3. **Source**: One of:
   - Published study citation (author, year, table/figure number)
   - Official statistics source (INSEE/Eurostat reference)
   - Calculation method if derived (formula + inputs used)
4. **Notes**: Any caveats or assumptions

Example YAML structure:
```yaml
fiscal_aggregates:
  carbon_tax_revenue_44_euro:
    value: 8_200_000_000  # EUR/year for 100k households (scaled from national)
    tolerance: 0.02  # ±2%
    source: "Derived from CGDD (2021) national estimate scaled to 100k population"
    notes: "Assumes average household emissions from synthetic population generator"

distributional_shares:
  decile_1_share:
    value: 0.065  # 6.5% of total tax burden
    tolerance: 0.10  # ±10% (wider tolerance for distributional)
    source: "Pottier (2022) Fig 3, French household carbon tax incidence"
```

### Performance Targets (from NFR)

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Full simulation (100k households) | < 10 seconds | `time.perf_counter()` |
| Distributional indicators | < 5 seconds | `time.perf_counter()` |
| Full benchmark suite | < 15 seconds | Total elapsed |

### Project Structure Notes

- New `src/reformlab/benchmarks/` module follows existing subsystem pattern
- Benchmark fixtures use Parquet (consistent with data layer contracts)
- Reference values in YAML (consistent with scenario/template configuration)
- Tests in `tests/benchmarks/` parallel to `tests/indicators/`, `tests/governance/`

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-701] - Story requirements
- [Source: _bmad-output/planning-artifacts/prd.md#NFR1] - Performance target: 100k in <10s
- [Source: _bmad-output/planning-artifacts/prd.md#NFR5] - Indicator computation: <5s for 100k
- [Source: _bmad-output/planning-artifacts/prd.md#Scientific-Rigor-&-Validation] - Benchmark validation requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#Reproducibility-&-Governance] - Manifest and verification patterns
- [Source: src/reformlab/governance/reproducibility.py] - Pattern for structured verification results
- [Source: src/reformlab/indicators/distributional.py] - Decile indicator computation
- [Source: src/reformlab/interfaces/api.py] - Public API patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

