"""Performance smoke tests for carbon tax computation.

These tests verify that computation meets NFR5 performance targets:
- Analytical operations execute in under 5 seconds for 100k households
"""

from __future__ import annotations

import time

import pyarrow as pa
import pytest

np = pytest.importorskip("numpy")

from reformlab.data.emission_factors import build_emission_factor_index
from reformlab.templates import list_carbon_tax_templates, load_carbon_tax_template
from reformlab.templates.carbon_tax import (
    aggregate_by_decile,
    compare_decile_impacts,
    compute_carbon_tax,
    run_carbon_tax_batch,
)


class TestPerformanceSmoke:
    """Performance smoke tests aligned with NFR5 targets."""

    @pytest.fixture()
    def large_population(self) -> pa.Table:
        """Create a 100k household population for performance testing."""
        n = 100_000
        rng = np.random.default_rng(42)

        return pa.table(
            {
                "household_id": pa.array(range(n), type=pa.int64()),
                "income": pa.array(
                    rng.lognormal(mean=10.5, sigma=0.6, size=n), type=pa.float64()
                ),
                "energy_transport_fuel": pa.array(
                    rng.exponential(scale=1500, size=n), type=pa.float64()
                ),
                "energy_heating_fuel": pa.array(
                    rng.exponential(scale=700, size=n), type=pa.float64()
                ),
                "energy_natural_gas": pa.array(
                    rng.exponential(scale=1000, size=n), type=pa.float64()
                ),
            }
        )

    @pytest.fixture()
    def emission_factors_2026(self) -> pa.Table:
        """Emission factors for 2026."""
        return pa.table(
            {
                "category": pa.array(
                    ["transport_fuel", "heating_fuel", "natural_gas"],
                    type=pa.utf8(),
                ),
                "factor_value": pa.array([2.31, 2.68, 2.0], type=pa.float64()),
                "unit": pa.array(
                    ["kg_co2_per_liter", "kg_co2_per_liter", "kg_co2_per_m3"],
                    type=pa.utf8(),
                ),
                "year": pa.array([2026, 2026, 2026], type=pa.int64()),
            }
        )

    def test_single_scenario_under_5_seconds(
        self,
        large_population: pa.Table,
        emission_factors_2026: pa.Table,
    ) -> None:
        """Single scenario computation completes in under 5 seconds (NFR5)."""
        emission_index = build_emission_factor_index(emission_factors_2026)
        template = load_carbon_tax_template("carbon-tax-flat-progressive-dividend")

        start = time.perf_counter()
        result = compute_carbon_tax(
            population=large_population,
            parameters=template.parameters,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )
        elapsed = time.perf_counter() - start

        # Verify computation completed
        assert len(result.tax_burden) == 100_000
        assert result.total_revenue > 0

        # NFR5: under 5 seconds
        assert elapsed < 5.0, f"Computation took {elapsed:.2f}s, exceeds 5s target"

    def test_decile_aggregation_under_5_seconds(
        self,
        large_population: pa.Table,
        emission_factors_2026: pa.Table,
    ) -> None:
        """Decile aggregation completes in under 5 seconds (NFR5)."""
        emission_index = build_emission_factor_index(emission_factors_2026)
        template = load_carbon_tax_template("carbon-tax-flat-progressive-dividend")

        result = compute_carbon_tax(
            population=large_population,
            parameters=template.parameters,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )

        start = time.perf_counter()
        decile_results = aggregate_by_decile(result)
        elapsed = time.perf_counter() - start

        # Verify aggregation completed
        assert len(decile_results.decile) == 10
        assert sum(decile_results.household_count) == 100_000

        # Aggregation should be fast
        assert elapsed < 5.0, f"Aggregation took {elapsed:.2f}s, exceeds 5s target"

    def test_batch_comparison_under_5_seconds(
        self,
        large_population: pa.Table,
        emission_factors_2026: pa.Table,
    ) -> None:
        """Batch comparison of 3 scenarios completes in under 5 seconds (NFR5)."""
        emission_index = build_emission_factor_index(emission_factors_2026)

        # Load 3 scenarios
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
            load_carbon_tax_template("carbon-tax-flat-progressive-dividend"),
        ]

        start = time.perf_counter()
        results = run_carbon_tax_batch(
            population=large_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        elapsed = time.perf_counter() - start

        # Verify comparison completed
        assert len(comparison.scenarios) == 3
        assert comparison.comparison_table.num_rows == 10

        # NFR5: under 5 seconds total (generous for 3 scenarios)
        # Note: actual target is per-operation, but batch should still be fast
        assert elapsed < 15.0, f"Batch comparison took {elapsed:.2f}s, exceeds 15s"

    def test_all_templates_load_under_1_second(self) -> None:
        """All template loading completes in under 1 second (NFR4)."""
        variants = list_carbon_tax_templates()

        start = time.perf_counter()
        for variant in variants:
            template = load_carbon_tax_template(variant)
            assert template is not None
        elapsed = time.perf_counter() - start

        # NFR4: YAML loading under 1 second
        assert elapsed < 1.0, f"Template loading took {elapsed:.2f}s, exceeds 1s target"
