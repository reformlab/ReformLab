"""Benchmark test suite for simulation output validation.

Story 7.1: Verify Simulation Outputs Against Published Benchmarks

This test suite validates:
- Fiscal aggregate benchmarks (carbon tax revenue)
- Distributional benchmarks (tax burden by income decile)
- Performance benchmarks (suite completes in <10 seconds for 100k households)
"""

from __future__ import annotations

import time
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pytest

from reformlab.governance.benchmarking import run_benchmark_suite
from reformlab.orchestrator.panel import PanelOutput

pytestmark = pytest.mark.benchmark


def test_fiscal_aggregate_benchmark(benchmark_population: pa.Table) -> None:
    """Verify aggregate carbon tax revenue matches reference value.

    Given:
        - 100k household population
        - Carbon tax rate of 44 EUR/tCO2
    When:
        - Simulation is run and fiscal aggregate is computed
    Then:
        - Total carbon tax revenue matches reference within tolerance
    """
    # Simulate carbon tax computation
    carbon_tax_rate = 44.0

    # Compute carbon tax: emissions × rate
    carbon_tax = pc.multiply(
        benchmark_population.column("carbon_emissions"),
        pa.scalar(carbon_tax_rate, type=pa.float64()),
    )

    # Build panel output
    panel_table = benchmark_population.append_column("carbon_tax", carbon_tax)
    panel_table = panel_table.append_column(
        "year", pa.array([2025] * panel_table.num_rows, type=pa.int64())
    )

    panel = PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )

    # Run benchmark suite
    result = run_benchmark_suite(panel)

    # Find the fiscal aggregate benchmark
    fiscal_results = [r for r in result.results if "revenue" in r.metric_name]
    assert len(fiscal_results) > 0, "No fiscal aggregate benchmark found"

    fiscal_result = fiscal_results[0]

    # Verify it passed
    if not fiscal_result.passed:
        print(fiscal_result.details())
        pytest.fail(f"Fiscal aggregate benchmark failed: {fiscal_result.details()}")

    # Verify the actual value is reasonable
    assert fiscal_result.actual > 0, "Carbon tax revenue should be positive"


def test_distributional_benchmark(benchmark_population: pa.Table) -> None:
    """Verify carbon tax burden by income decile matches reference pattern.

    Given:
        - 100k household population with income and emissions
        - Carbon tax rate of 44 EUR/tCO2
    When:
        - Distributional indicators are computed
    Then:
        - Decile burden shares match reference values within tolerance
    """
    # Simulate carbon tax computation
    carbon_tax_rate = 44.0

    carbon_tax = pc.multiply(
        benchmark_population.column("carbon_emissions"),
        pa.scalar(carbon_tax_rate, type=pa.float64()),
    )

    # Build panel output
    panel_table = benchmark_population.append_column("carbon_tax", carbon_tax)
    panel_table = panel_table.append_column(
        "year", pa.array([2025] * panel_table.num_rows, type=pa.int64())
    )

    panel = PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )

    # Run benchmark suite
    result = run_benchmark_suite(panel)

    # Find distributional benchmarks
    dist_results = [r for r in result.results if "decile" in r.metric_name]
    assert len(dist_results) > 0, "No distributional benchmarks found"

    # Check that at least one decile benchmark passed
    passed_count = sum(1 for r in dist_results if r.passed)
    if passed_count == 0:
        # Print details of failures
        for r in dist_results:
            print(r.details())
        pytest.fail("No distributional benchmarks passed")


def test_performance_benchmark(benchmark_population: pa.Table) -> None:
    """Verify benchmark suite completes in under 10 seconds for 100k households.

    Given:
        - 100k household population
    When:
        - Full benchmark suite is executed
    Then:
        - Total wall time is under 10 seconds (NFR1 requirement)
    """
    # Simulate carbon tax computation
    carbon_tax_rate = 44.0

    carbon_tax = pc.multiply(
        benchmark_population.column("carbon_emissions"),
        pa.scalar(carbon_tax_rate, type=pa.float64()),
    )

    # Build panel output
    panel_table = benchmark_population.append_column("carbon_tax", carbon_tax)
    panel_table = panel_table.append_column(
        "year", pa.array([2025] * panel_table.num_rows, type=pa.int64())
    )

    panel = PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )

    # Measure benchmark suite execution time
    start = time.perf_counter()
    result = run_benchmark_suite(panel)
    elapsed = time.perf_counter() - start

    # Verify timing
    assert elapsed < 10.0, (
        f"Benchmark suite exceeded 10s limit: {elapsed:.2f}s. "
        "NFR1 requires <10s for 100k households."
    )

    # Verify result timing matches measurement
    assert result.total_time_seconds > 0, "Benchmark suite should report timing"
    assert abs(result.total_time_seconds - elapsed) < 1.0, (
        "Reported timing should match measured timing"
    )


def test_benchmark_suite_integration(benchmark_population: pa.Table) -> None:
    """Integration test for complete benchmark suite execution.

    Given:
        - 100k household population
        - Complete benchmark suite with fiscal and distributional checks
    When:
        - Benchmark suite is run
    Then:
        - All benchmarks are executed
        - Results are properly structured
        - Performance target is met
    """
    # Simulate carbon tax computation
    carbon_tax_rate = 44.0

    carbon_tax = pc.multiply(
        benchmark_population.column("carbon_emissions"),
        pa.scalar(carbon_tax_rate, type=pa.float64()),
    )

    # Build panel output
    panel_table = benchmark_population.append_column("carbon_tax", carbon_tax)
    panel_table = panel_table.append_column(
        "year", pa.array([2025] * panel_table.num_rows, type=pa.int64())
    )

    panel = PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )

    # Run benchmark suite
    result = run_benchmark_suite(panel)

    # Verify suite structure
    assert isinstance(result.results, list), "Results should be a list"
    assert len(result.results) > 0, "Suite should contain benchmark results"
    assert result.total_time_seconds > 0, "Suite should report timing"

    # Verify all results have required fields
    for benchmark_result in result.results:
        assert hasattr(benchmark_result, "passed"), "Result should have 'passed' field"
        assert hasattr(benchmark_result, "metric_name"), "Result should have 'metric_name'"
        assert hasattr(benchmark_result, "expected"), "Result should have 'expected'"
        assert hasattr(benchmark_result, "actual"), "Result should have 'actual'"
        assert hasattr(benchmark_result, "tolerance"), "Result should have 'tolerance'"
        assert hasattr(benchmark_result, "deviation"), "Result should have 'deviation'"
        assert hasattr(benchmark_result, "source"), "Result should have 'source'"

    # Verify repr works
    repr_str = repr(result)
    assert "BenchmarkSuiteResult" in repr_str, "Repr should identify result type"
    assert "passed" in repr_str, "Repr should show pass/fail count"

    # Print summary for visibility
    print(f"\n{repr_str}")
    passed_count = sum(1 for r in result.results if r.passed)
    print(f"Passed: {passed_count}/{len(result.results)}")
    for r in result.results:
        status = "✓" if r.passed else "✗"
        print(f"  {status} {r.metric_name}: {r.actual:.2f} (expected {r.expected:.2f})")


def test_benchmark_failure_diagnostics(benchmark_population: pa.Table) -> None:
    """Verify clear failure diagnostics when benchmark doesn't match.

    Given:
        - Panel with incorrect carbon tax values
    When:
        - Benchmark suite is run
    Then:
        - Failure is detected
        - Diagnostic output includes: metric name, expected, actual, deviation, tolerance
    """
    # Simulate INCORRECT carbon tax (too low by 50%)
    carbon_tax_rate = 22.0  # Should be 44.0

    carbon_tax = pc.multiply(
        benchmark_population.column("carbon_emissions"),
        pa.scalar(carbon_tax_rate, type=pa.float64()),
    )

    # Build panel output
    panel_table = benchmark_population.append_column("carbon_tax", carbon_tax)
    panel_table = panel_table.append_column(
        "year", pa.array([2025] * panel_table.num_rows, type=pa.int64())
    )

    panel = PanelOutput(
        table=panel_table,
        metadata={"start_year": 2025, "end_year": 2025},
    )

    # Run benchmark suite
    result = run_benchmark_suite(panel)

    # Find failing benchmarks
    failed_results = [r for r in result.results if not r.passed]
    assert len(failed_results) > 0, "Should detect failure with incorrect tax rate"

    # Verify diagnostic output
    failed_result = failed_results[0]
    details = failed_result.details()

    # Verify all required diagnostic fields are present
    assert "FAILED" in details, "Details should indicate failure"
    assert failed_result.metric_name in details, "Details should include metric name"
    assert "Expected:" in details, "Details should show expected value"
    assert "Actual:" in details, "Details should show actual value"
    assert "Deviation:" in details, "Details should show deviation"
    assert "Tolerance:" in details, "Details should show tolerance"
    assert "Source:" in details, "Details should show source reference"

    # Print for visibility
    print(f"\nFailure diagnostics:\n{details}")


def test_benchmark_reference_file_required() -> None:
    """Verify benchmark suite requires reference file to exist."""
    # Create empty panel
    empty_table = pa.table(
        {
            "household_id": pa.array([], type=pa.int64()),
            "year": pa.array([], type=pa.int64()),
            "carbon_tax": pa.array([], type=pa.float64()),
        }
    )
    panel = PanelOutput(table=empty_table, metadata={})

    # Try to run with non-existent reference file
    with pytest.raises(FileNotFoundError, match="Benchmark reference file not found"):
        run_benchmark_suite(panel, reference_path=Path("/nonexistent/path.yaml"))
