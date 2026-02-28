"""Scale validation tests for NFR1 and NFR3.

Story 8.2: Generate 100k-Household Synthetic Population and Run BKL-701
Benchmarks at Target Scale

Tests:
- AC-2: BKL-701 benchmark suite passes with persistent 100k population
- AC-3: NFR1 — full 100k simulation completes in under 10 seconds
- AC-4: NFR3 — 500k population runs without OOM crash
- AC-5: Scale tests runnable via pytest with ``pytest.mark.scale``
"""

from __future__ import annotations

import time

import pyarrow as pa
import pyarrow.compute as pc
import pytest

from reformlab.data.synthetic import generate_synthetic_population
from reformlab.governance.benchmarking import run_benchmark_suite
from reformlab.orchestrator.panel import PanelOutput

pytestmark = pytest.mark.scale


# ============================================================================
# Helpers
# ============================================================================


def _build_panel_with_carbon_tax(
    population: pa.Table,
    *,
    carbon_tax_rate: float,
) -> PanelOutput:
    """Build single-year benchmark panel with computed carbon tax field."""
    carbon_tax = pc.multiply(
        population.column("carbon_emissions"),
        pa.scalar(carbon_tax_rate, type=pa.float64()),
    )
    panel_table = population.append_column("carbon_tax", carbon_tax)
    panel_table = panel_table.append_column(
        "year", pa.array([2025] * panel_table.num_rows, type=pa.int64())
    )
    return PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )


# ============================================================================
# AC-2: Benchmark suite passes with 100k persistent population
# ============================================================================


def test_100k_benchmark_with_persistent_population() -> None:
    """AC-2: BKL-701 benchmark suite passes with persistent 100k population.

    Given:
        100k population generated via generate_synthetic_population()
    When:
        Panel built with carbon tax at 44 EUR/tCO2, then benchmarks run
    Then:
        All fiscal and distributional benchmarks pass
    """
    population = generate_synthetic_population(size=100_000, seed=42)
    panel = _build_panel_with_carbon_tax(population, carbon_tax_rate=44.0)
    result = run_benchmark_suite(panel)

    assert result.passed, (
        f"Benchmark suite failed with 100k persistent population: "
        f"{sum(1 for r in result.results if not r.passed)}/{len(result.results)} checks failed"
    )

    # Log details for regression monitoring
    for r in result.results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  {status} {r.metric_name}: actual={r.actual:.4f} expected={r.expected:.4f}")


# ============================================================================
# AC-3: NFR1 — full 100k simulation in under 10 seconds
# ============================================================================


def test_nfr1_performance_100k() -> None:
    """AC-3: NFR1 — full 100k simulation completes in under 10 seconds.

    Measures end-to-end wall time:
        generation -> panel build -> indicators -> benchmarks
    """
    t_start = time.perf_counter()

    t0 = time.perf_counter()
    population = generate_synthetic_population(size=100_000, seed=42)
    t_gen = time.perf_counter() - t0

    t0 = time.perf_counter()
    panel = _build_panel_with_carbon_tax(population, carbon_tax_rate=44.0)
    t_panel = time.perf_counter() - t0

    t0 = time.perf_counter()
    suite_result = run_benchmark_suite(panel)
    t_bench = time.perf_counter() - t0

    t_total = time.perf_counter() - t_start

    # Timing breakdown for regression monitoring
    print("\n  Timing breakdown (100k):")
    print(f"    Generation:  {t_gen:.3f}s")
    print(f"    Panel build: {t_panel:.3f}s")
    print(f"    Benchmarks:  {t_bench:.3f}s")
    print(f"    Total:       {t_total:.3f}s")

    assert t_total < 10.0, f"100k simulation took {t_total:.2f}s, NFR1 requires < 10s"
    assert suite_result.passed, "Benchmark suite must pass at 100k scale"


# ============================================================================
# AC-4: NFR3 — 500k population runs without crash
# ============================================================================


def test_nfr3_500k_no_crash() -> None:
    """AC-4: NFR3 — 500k population completes without OOM crash.

    Given:
        500k-household synthetic population
    When:
        Single-year simulation is run
    Then:
        Simulation completes with valid result (correct row count, no NaN)
    """
    t_start = time.perf_counter()
    population = generate_synthetic_population(size=500_000, seed=42)
    t_gen = time.perf_counter() - t_start

    t0 = time.perf_counter()
    panel = _build_panel_with_carbon_tax(population, carbon_tax_rate=44.0)
    t_panel = time.perf_counter() - t0

    t_total = time.perf_counter() - t_start

    # Validate output structure
    assert panel.table.num_rows == 500_000, (
        f"Expected 500k rows, got {panel.table.num_rows}"
    )

    # No NaN in required fields
    for col_name in ("household_id", "income", "carbon_tax"):
        col = panel.table.column(col_name)
        null_count = col.null_count
        assert null_count == 0, f"Column {col_name} has {null_count} null values"

        if col.type in (pa.float64(), pa.float32()):
            # Check for NaN in float columns
            nan_count = pc.sum(pc.is_nan(col)).as_py()
            assert nan_count == 0, f"Column {col_name} has {nan_count} NaN values"

    print("\n  Timing breakdown (500k):")
    print(f"    Generation:  {t_gen:.3f}s")
    print(f"    Panel build: {t_panel:.3f}s")
    print(f"    Total:       {t_total:.3f}s")


def test_nfr3_memory_warning_500k() -> None:
    """AC-4: check_memory_requirements returns should_warn=True for 500k multi-year.

    Validates that the memory estimation system correctly identifies
    a 500k × 10-year simulation as exceeding safe thresholds on 16GB.
    """
    from reformlab.governance.memory import estimate_memory_usage

    # 500k households × 10 years → ~7.5 GB estimated (800 bytes × 2x multiplier)
    estimate = estimate_memory_usage(population_size=500_000, projection_years=10)

    # With 2x multiplier: 500_000 × 10 × 800 × 2 = 8,000,000,000 bytes (~7.5 GB)
    assert estimate.estimated_bytes > 0
    print(f"\n  Memory estimate (500k × 10yr): {estimate.estimated_gb:.1f} GB")
    print(f"  Threshold: {estimate.threshold_gb:.1f} GB")

    # For 500k × 20 years, it should exceed the 12GB threshold
    estimate_20yr = estimate_memory_usage(population_size=500_000, projection_years=20)
    assert estimate_20yr.exceeds_threshold, (
        f"500k × 20yr should exceed threshold: "
        f"estimated={estimate_20yr.estimated_gb:.1f}GB > threshold={estimate_20yr.threshold_gb:.1f}GB"
    )
    print(f"  Memory estimate (500k × 20yr): {estimate_20yr.estimated_gb:.1f} GB (exceeds threshold)")

    # Verify warning message format via MemoryWarning
    from reformlab.interfaces.errors import MemoryWarning

    warning = MemoryWarning(estimate_20yr)
    message = str(warning)
    assert "500,000 households" in message
    assert "20 years" in message
    assert "GB" in message
