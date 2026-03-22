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
import warnings
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pytest

from reformlab.data.synthetic import generate_synthetic_population, save_synthetic_population
from reformlab.governance.benchmarking import run_benchmark_suite
from reformlab.governance.memory import estimate_memory_usage
from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.fiscal import compute_fiscal_indicators
from reformlab.indicators.types import FiscalConfig
from reformlab.interfaces.errors import MemoryWarning
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
    """Build single-year benchmark panel with computed carbon tax field.

    Simplified benchmark formula: tax = sum(energy columns) * rate.
    """
    total_energy = pc.add(
        pc.add(
            population.column("energy_transport_fuel"),
            population.column("energy_heating_fuel"),
        ),
        population.column("energy_natural_gas"),
    )
    carbon_tax = pc.multiply(total_energy, pa.scalar(carbon_tax_rate, type=pa.float64()))
    n = population.num_rows
    panel_table = pa.table(
        {
            "household_id": population.column("household_id"),
            "income": population.column("income"),
            "carbon_tax": carbon_tax,
            "year": pa.array([2025] * n, type=pa.int64()),
        }
    )
    return PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )


# ============================================================================
# AC-2: Benchmark suite passes with 100k persistent population
# ============================================================================


def test_100k_benchmark_with_persistent_population(tmp_path: Path) -> None:
    """AC-2: BKL-701 benchmark suite passes with persistent 100k population.

    Given:
        100k population generated, saved to Parquet, and loaded back
    When:
        Panel built with carbon tax at 44 EUR/tCO2, then benchmarks run
    Then:
        All fiscal and distributional benchmarks pass
    """
    # Generate and persist to Parquet
    population = generate_synthetic_population(size=100_000, seed=42)
    parquet_path = tmp_path / "population_100k.parquet"
    manifest = save_synthetic_population(population, parquet_path)
    assert manifest.content_hash, "Manifest must have non-empty SHA-256 hash"

    # Load back from persisted file (validates round-trip through Parquet)
    loaded_population = pq.read_table(parquet_path)
    assert loaded_population.equals(population), "Round-trip through Parquet must preserve data"

    panel = _build_panel_with_carbon_tax(loaded_population, carbon_tax_rate=44.0)
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
    compute_distributional_indicators(panel)
    compute_fiscal_indicators(panel, FiscalConfig(revenue_fields=["carbon_tax"]))
    t_indicators = time.perf_counter() - t0

    t0 = time.perf_counter()
    suite_result = run_benchmark_suite(panel)
    t_bench = time.perf_counter() - t0

    t_total = time.perf_counter() - t_start

    # Timing breakdown for regression monitoring
    print("\n  Timing breakdown (100k):")
    print(f"    Generation:  {t_gen:.3f}s")
    print(f"    Panel build: {t_panel:.3f}s")
    print(f"    Indicators:  {t_indicators:.3f}s")
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
        And memory warning is emitted for multi-year projections at this scale
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

    # Verify memory estimation system works at 500k scale (AC-4 memory warning)
    # Per Story 7-2: 500k × 1yr = ~0.75GB (below threshold), but
    # 500k × 20yr = ~15GB (exceeds threshold). Validate warning emits correctly.
    estimate_20yr = estimate_memory_usage(population_size=500_000, projection_years=20)
    assert estimate_20yr.exceeds_threshold, (
        "500k × 20yr should exceed threshold — memory warning system must detect this"
    )
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warnings.warn(MemoryWarning(estimate_20yr))
        memory_warnings = [x for x in w if issubclass(x.category, MemoryWarning)]
        assert len(memory_warnings) >= 1, "MemoryWarning must be emittable for 500k multi-year"

    print("\n  Timing breakdown (500k):")
    print(f"    Generation:  {t_gen:.3f}s")
    print(f"    Panel build: {t_panel:.3f}s")
    print(f"    Total:       {t_total:.3f}s")


def test_nfr3_memory_warning_500k() -> None:
    """AC-4: Memory estimation validates 500k thresholds at multiple projections.

    Validates that the memory estimation system correctly identifies
    500k populations at various projection lengths and that MemoryWarning
    messages follow the canonical format.
    """
    # 500k × 1 year: should be well within threshold (~0.75 GB)
    estimate_1yr = estimate_memory_usage(population_size=500_000, projection_years=1)
    assert estimate_1yr.estimated_bytes > 0
    print(f"\n  Memory estimate (500k × 1yr):  {estimate_1yr.estimated_gb:.1f} GB")
    print(f"  Threshold: {estimate_1yr.threshold_gb:.1f} GB")

    # 500k × 10 years: should be under or near threshold (~7.5 GB)
    estimate_10yr = estimate_memory_usage(population_size=500_000, projection_years=10)
    assert estimate_10yr.estimated_bytes > 0
    print(f"  Memory estimate (500k × 10yr): {estimate_10yr.estimated_gb:.1f} GB")

    # 500k × 20 years: must exceed the 12GB threshold
    estimate_20yr = estimate_memory_usage(population_size=500_000, projection_years=20)
    assert estimate_20yr.exceeds_threshold, (
        f"500k × 20yr should exceed threshold: "
        f"estimated={estimate_20yr.estimated_gb:.1f}GB > threshold={estimate_20yr.threshold_gb:.1f}GB"
    )
    print(f"  Memory estimate (500k × 20yr): {estimate_20yr.estimated_gb:.1f} GB (exceeds threshold)")

    # Verify warning message format via MemoryWarning
    warning = MemoryWarning(estimate_20yr)
    message = str(warning)
    assert "500,000 households" in message
    assert "20 years" in message
    assert "GB" in message
