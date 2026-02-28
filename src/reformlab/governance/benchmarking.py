"""Benchmark verification for simulation outputs against published reference values.

Story 7.1: Verify Simulation Outputs Against Published Benchmarks

This module provides:
- BenchmarkResult: Result of a single benchmark test
- BenchmarkSuiteResult: Result of running the complete benchmark suite
- run_benchmark_suite: Orchestrate benchmark checks
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

import pyarrow.compute as pc
import yaml

if TYPE_CHECKING:
    from reformlab.indicators.types import DecileIndicators
    from reformlab.orchestrator.panel import PanelOutput


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of a single benchmark test.

    Attributes:
        passed: Whether the benchmark check passed.
        metric_name: Name of the metric being benchmarked.
        expected: Expected value from reference.
        actual: Actual value from simulation.
        tolerance: Tolerance used for comparison (relative).
        deviation: Relative deviation from expected value.
        source: Reference source documentation.
    """

    passed: bool
    metric_name: str
    expected: float
    actual: float
    tolerance: float
    deviation: float
    source: str

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


@dataclass(frozen=True)
class BenchmarkSuiteResult:
    """Result of running the complete benchmark suite.

    Attributes:
        passed: Whether all benchmarks passed.
        results: List of individual benchmark results.
        total_time_seconds: Total wall time for benchmark suite.
    """

    passed: bool
    results: list[BenchmarkResult]
    total_time_seconds: float

    def __repr__(self) -> str:
        """Return notebook-friendly representation showing pass/fail count and timing."""
        passed_count = sum(1 for r in self.results if r.passed)
        return (
            f"BenchmarkSuiteResult({passed_count}/{len(self.results)} passed, "
            f"{self.total_time_seconds:.2f}s)"
        )


def within_tolerance(expected: float, actual: float, tolerance: float) -> bool:
    """Check if actual value is within relative tolerance of expected value.

    Args:
        expected: Expected reference value.
        actual: Actual simulated value.
        tolerance: Relative tolerance (e.g., 0.02 = ±2%).

    Returns:
        True if actual is within tolerance of expected.
    """
    if expected == 0:
        return abs(actual) <= tolerance
    return abs(actual - expected) / abs(expected) <= tolerance


def run_benchmark_suite(
    panel: PanelOutput,
    reference_path: Path | None = None,
    *,
    carbon_tax_field: str = "carbon_tax",
    income_field: str = "income",
) -> BenchmarkSuiteResult:
    """Run the complete benchmark suite against simulation outputs.

    Args:
        panel: Panel output from simulation run.
        reference_path: Path to benchmark reference YAML file.
            If None, uses default location: tests/benchmarks/references/carbon_tax_benchmarks.yaml
        carbon_tax_field: Name of carbon tax field in panel (default: "carbon_tax").
        income_field: Name of income field in panel (default: "income").

    Returns:
        BenchmarkSuiteResult with all benchmark results and timing.

    Raises:
        FileNotFoundError: If reference file is not found.
        ValueError: If reference file format is invalid.
    """
    start_time = time.perf_counter()
    results: list[BenchmarkResult] = []

    # Load reference values
    if reference_path is None:
        reference_path = _default_reference_path()

    if not reference_path.exists():
        raise FileNotFoundError(
            f"Benchmark reference file not found: {reference_path}. "
            "Ensure the reference file exists at the specified location."
        )

    with open(reference_path, encoding="utf-8") as f:
        references = yaml.safe_load(f)

    if not isinstance(references, dict):
        raise ValueError(
            f"Invalid reference file format: expected YAML mapping, got {type(references).__name__}"
        )

    # Run fiscal aggregate benchmarks
    fiscal_benchmarks = references.get("fiscal_aggregates", {})
    if not isinstance(fiscal_benchmarks, dict):
        raise ValueError(
            "Invalid benchmark reference format: 'fiscal_aggregates' must be a mapping"
        )

    for metric_name, ref_data in fiscal_benchmarks.items():
        result = _check_fiscal_aggregate(
            panel=panel,
            metric_name=metric_name,
            reference=_validate_reference(metric_name, ref_data),
            carbon_tax_field=carbon_tax_field,
        )
        results.append(result)

    # Run distributional benchmarks
    distributional_benchmarks = references.get("distributional_shares", {})
    if not isinstance(distributional_benchmarks, dict):
        raise ValueError(
            "Invalid benchmark reference format: 'distributional_shares' must be a mapping"
        )

    if not fiscal_benchmarks and not distributional_benchmarks:
        raise ValueError(
            "Benchmark reference file contains no benchmarks. "
            "Expected at least one metric under 'fiscal_aggregates' or "
            "'distributional_shares'."
        )

    if distributional_benchmarks:
        from reformlab.indicators import compute_distributional_indicators
        from reformlab.indicators.types import DecileIndicators as DecileIndicatorsType
        from reformlab.indicators.types import DistributionalConfig

        # Compute distributional indicators
        config = DistributionalConfig(income_field=income_field, by_year=False)
        dist_result = compute_distributional_indicators(panel, config)
        decile_indicators = [
            ind for ind in dist_result.indicators if isinstance(ind, DecileIndicatorsType)
        ]

        for metric_name, ref_data in distributional_benchmarks.items():
            result = _check_distributional_share(
                indicators=decile_indicators,
                metric_name=metric_name,
                reference=_validate_reference(metric_name, ref_data),
                carbon_tax_field=carbon_tax_field,
            )
            results.append(result)

    elapsed = time.perf_counter() - start_time

    # All benchmarks must pass for suite to pass
    passed = all(r.passed for r in results)

    return BenchmarkSuiteResult(
        passed=passed,
        results=results,
        total_time_seconds=elapsed,
    )


def _default_reference_path() -> Path:
    """Return default benchmark reference file path relative to repository root."""
    return (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "benchmarks"
        / "references"
        / "carbon_tax_benchmarks.yaml"
    )


def _validate_reference(metric_name: str, reference: Any) -> dict[str, Any]:
    """Validate benchmark reference entry has required fields."""
    if not isinstance(reference, dict):
        raise ValueError(
            f"Invalid reference for '{metric_name}': expected mapping, got "
            f"{type(reference).__name__}"
        )

    required_fields = ("value", "tolerance", "source")
    missing = [field for field in required_fields if field not in reference]
    if missing:
        raise ValueError(
            f"Invalid reference for '{metric_name}': missing required field(s): "
            + ", ".join(missing)
        )

    return reference


def _check_fiscal_aggregate(
    panel: PanelOutput,
    metric_name: str,
    reference: dict[str, Any],
    carbon_tax_field: str,
) -> BenchmarkResult:
    """Check fiscal aggregate benchmark against reference value.

    Args:
        panel: Panel output from simulation.
        metric_name: Name of the benchmark metric.
        reference: Reference data dictionary with value, tolerance, and source.
        carbon_tax_field: Name of carbon tax field in panel.

    Returns:
        BenchmarkResult for this fiscal aggregate check.
    """
    expected = float(reference["value"])
    tolerance = float(reference["tolerance"])
    source = str(reference["source"])

    # Compute actual aggregate from panel
    if carbon_tax_field not in panel.table.column_names:
        actual = 0.0
        deviation = 1.0 if expected != 0 else 0.0
        passed = False
    else:
        carbon_tax_col = panel.table.column(carbon_tax_field)
        actual = float(pc.sum(carbon_tax_col).as_py() or 0.0)
        passed = within_tolerance(expected, actual, tolerance)
        deviation = (
            (actual - expected) / abs(expected) if expected != 0 else float("inf")
        )

    return BenchmarkResult(
        passed=passed,
        metric_name=metric_name,
        expected=expected,
        actual=actual,
        tolerance=tolerance,
        deviation=deviation,
        source=source,
    )


def _check_distributional_share(
    indicators: Sequence[DecileIndicators],
    metric_name: str,
    reference: dict[str, Any],
    carbon_tax_field: str,
) -> BenchmarkResult:
    """Check distributional share benchmark against reference value.

    Args:
        indicators: List of DecileIndicators from distributional computation.
        metric_name: Name of the benchmark metric (e.g., "decile_1_share").
        reference: Reference data dictionary with value, tolerance, and source.
        carbon_tax_field: Name of carbon tax field being analyzed.

    Returns:
        BenchmarkResult for this distributional share check.
    """
    expected = float(reference["value"])
    tolerance = float(reference["tolerance"])
    source = str(reference["source"])

    # Extract decile number from metric name (e.g., "decile_1_share" -> 1)
    try:
        decile_num = int(metric_name.split("_")[1])
    except (IndexError, ValueError):
        # Invalid metric name format
        return BenchmarkResult(
            passed=False,
            metric_name=metric_name,
            expected=expected,
            actual=0.0,
            tolerance=tolerance,
            deviation=1.0,
            source=source,
        )

    # Find the carbon_tax indicator for this decile
    carbon_tax_indicators = [
        ind for ind in indicators if ind.field_name == carbon_tax_field
    ]

    # Compute total carbon tax across all deciles
    total_tax = sum(ind.sum for ind in carbon_tax_indicators)

    # Find indicator for target decile
    target_indicator = None
    for ind in carbon_tax_indicators:
        if ind.decile == decile_num:
            target_indicator = ind
            break

    if target_indicator is None or total_tax == 0:
        actual = 0.0
        deviation = 1.0 if expected != 0 else 0.0
        passed = False
    else:
        # Compute share (fraction of total)
        actual = target_indicator.sum / total_tax
        passed = within_tolerance(expected, actual, tolerance)
        deviation = (
            (actual - expected) / abs(expected) if expected != 0 else float("inf")
        )

    return BenchmarkResult(
        passed=passed,
        metric_name=metric_name,
        expected=expected,
        actual=actual,
        tolerance=tolerance,
        deviation=deviation,
        source=source,
    )
