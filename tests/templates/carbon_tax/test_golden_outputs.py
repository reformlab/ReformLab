# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Golden-file tests for carbon tax computation.

These tests verify that computation outputs match expected values,
ensuring correctness and detecting regressions.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.data.emission_factors import build_emission_factor_index
from reformlab.templates import load_carbon_tax_template
from reformlab.templates.carbon_tax import (
    aggregate_by_decile,
    compute_carbon_tax,
)


class TestGoldenTaxBurden:
    """Golden-file tests for tax burden computation."""

    @pytest.fixture()
    def golden_population(self) -> pa.Table:
        """Population with known values for deterministic testing."""
        return pa.table(
            {
                "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
                "income": pa.array(
                    [20000.0, 40000.0, 60000.0, 80000.0, 100000.0], type=pa.float64()
                ),
                # Transport: 1000 L gasoline each
                "energy_transport_fuel": pa.array(
                    [1000.0, 1000.0, 1000.0, 1000.0, 1000.0], type=pa.float64()
                ),
                # Heating: 500 L heating oil each
                "energy_heating_fuel": pa.array(
                    [500.0, 500.0, 500.0, 500.0, 500.0], type=pa.float64()
                ),
                # Gas: 800 m3 each
                "energy_natural_gas": pa.array(
                    [800.0, 800.0, 800.0, 800.0, 800.0], type=pa.float64()
                ),
            }
        )

    @pytest.fixture()
    def golden_emission_factors(self) -> pa.Table:
        """Emission factors with known values."""
        return pa.table(
            {
                "category": pa.array(
                    ["transport_fuel", "heating_fuel", "natural_gas"],
                    type=pa.utf8(),
                ),
                "factor_value": pa.array(
                    [2.31, 2.68, 2.0],  # kg CO2 per unit
                    type=pa.float64(),
                ),
                "unit": pa.array(
                    ["kg_co2_per_liter", "kg_co2_per_liter", "kg_co2_per_m3"],
                    type=pa.utf8(),
                ),
                "year": pa.array([2026, 2026, 2026], type=pa.int64()),
            }
        )

    def test_golden_tax_burden_no_redistribution(
        self,
        golden_population: pa.Table,
        golden_emission_factors: pa.Table,
    ) -> None:
        """Verify tax burden matches expected golden values."""
        emission_index = build_emission_factor_index(golden_emission_factors)
        template = load_carbon_tax_template("carbon-tax-flat-no-redistribution")

        result = compute_carbon_tax(
            population=golden_population,
            policy=template.policy,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )

        # Expected calculation per household:
        # Transport: 1000 L * 2.31 kg/L / 1000 * 44.60 EUR/t = 103.03 EUR
        # Heating: 500 L * 2.68 kg/L / 1000 * 44.60 EUR/t = 59.77 EUR
        # Gas: 800 m3 * 2.0 kg/m3 / 1000 * 44.60 EUR/t = 71.36 EUR
        # Total: 234.16 EUR per household
        expected_per_household = (
            1000.0 * 2.31 / 1000 * 44.60
            + 500.0 * 2.68 / 1000 * 44.60
            + 800.0 * 2.0 / 1000 * 44.60
        )

        for i in range(5):
            actual = result.tax_burden[i].as_py()
            assert abs(actual - expected_per_household) < 0.01, (
                f"Household {i + 1}: expected {expected_per_household:.2f}, got {actual:.2f}"
            )

        # Total revenue should be 5 * expected_per_household
        expected_total = 5 * expected_per_household
        assert abs(result.total_revenue - expected_total) < 0.01

    def test_golden_lump_sum_redistribution(
        self,
        golden_population: pa.Table,
        golden_emission_factors: pa.Table,
    ) -> None:
        """Verify lump sum redistribution matches expected values."""
        emission_index = build_emission_factor_index(golden_emission_factors)
        template = load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend")

        result = compute_carbon_tax(
            population=golden_population,
            policy=template.policy,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )

        # All households should receive equal redistribution
        redistributions = result.redistribution.to_pylist()
        expected_redist = result.total_revenue / 5

        for i, redist in enumerate(redistributions):
            assert abs(redist - expected_redist) < 0.01, (
                f"Household {i + 1}: expected {expected_redist:.2f}, got {redist:.2f}"
            )

        # Net impact should be 0 for uniform consumption
        # (everyone pays same, everyone gets same back)
        for i in range(5):
            net = result.net_impact[i].as_py()
            assert abs(net) < 0.01, f"Household {i + 1}: expected 0, got {net:.2f}"

    def test_golden_progressive_redistribution(
        self,
        golden_population: pa.Table,
        golden_emission_factors: pa.Table,
    ) -> None:
        """Verify progressive redistribution favors lower deciles."""
        emission_index = build_emission_factor_index(golden_emission_factors)
        template = load_carbon_tax_template("carbon-tax-flat-progressive-dividend")

        result = compute_carbon_tax(
            population=golden_population,
            policy=template.policy,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )

        # Lower income households should receive more redistribution
        redistributions = result.redistribution.to_pylist()
        incomes = golden_population.column("income").to_pylist()

        # Sort by income to verify progressive nature
        income_redist_pairs = list(zip(incomes, redistributions))
        income_redist_pairs.sort(key=lambda x: x[0])

        # First household (lowest income) should get more than last (highest)
        assert income_redist_pairs[0][1] > income_redist_pairs[-1][1], (
            "Progressive redistribution should favor lower incomes"
        )


class TestGoldenDecileAggregation:
    """Golden-file tests for per-decile aggregation."""

    @pytest.fixture()
    def decile_population(self) -> pa.Table:
        """Population with exactly 10 households for clean decile testing."""
        return pa.table(
            {
                "household_id": pa.array(list(range(1, 11)), type=pa.int64()),
                # Incomes from 10k to 100k, 10k increments
                "income": pa.array(
                    [
                        10000.0,
                        20000.0,
                        30000.0,
                        40000.0,
                        50000.0,
                        60000.0,
                        70000.0,
                        80000.0,
                        90000.0,
                        100000.0,
                    ],
                    type=pa.float64(),
                ),
                # Energy increases with income (realistic pattern)
                "energy_transport_fuel": pa.array(
                    [
                        500.0,
                        750.0,
                        1000.0,
                        1250.0,
                        1500.0,
                        1750.0,
                        2000.0,
                        2250.0,
                        2500.0,
                        3000.0,
                    ],
                    type=pa.float64(),
                ),
                "energy_heating_fuel": pa.array(
                    [
                        400.0,
                        450.0,
                        500.0,
                        550.0,
                        600.0,
                        650.0,
                        700.0,
                        750.0,
                        800.0,
                        900.0,
                    ],
                    type=pa.float64(),
                ),
                "energy_natural_gas": pa.array(
                    [
                        500.0,
                        600.0,
                        700.0,
                        800.0,
                        900.0,
                        1000.0,
                        1100.0,
                        1200.0,
                        1300.0,
                        1500.0,
                    ],
                    type=pa.float64(),
                ),
            }
        )

    @pytest.fixture()
    def simple_emission_factors(self) -> pa.Table:
        """Simple emission factors for testing."""
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

    def test_golden_decile_mean_tax_increases(
        self,
        decile_population: pa.Table,
        simple_emission_factors: pa.Table,
    ) -> None:
        """Higher deciles should have higher mean tax burden (more consumption)."""
        emission_index = build_emission_factor_index(simple_emission_factors)
        template = load_carbon_tax_template("carbon-tax-flat-no-redistribution")

        result = compute_carbon_tax(
            population=decile_population,
            policy=template.policy,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )

        decile_results = aggregate_by_decile(result)

        # Find first and last non-empty deciles
        non_empty = [
            (d, m)
            for d, m, c in zip(
                decile_results.decile,
                decile_results.mean_tax_burden,
                decile_results.household_count,
            )
            if c > 0
        ]

        if len(non_empty) >= 2:
            first_decile_mean = non_empty[0][1]
            last_decile_mean = non_empty[-1][1]
            assert last_decile_mean > first_decile_mean, (
                "Higher income deciles should have higher mean tax burden"
            )

    def test_golden_decile_net_impact_progressive(
        self,
        decile_population: pa.Table,
        simple_emission_factors: pa.Table,
    ) -> None:
        """With progressive dividend, lower deciles should have positive net impact."""
        emission_index = build_emission_factor_index(simple_emission_factors)
        template = load_carbon_tax_template("carbon-tax-flat-progressive-dividend")

        result = compute_carbon_tax(
            population=decile_population,
            policy=template.policy,
            emission_index=emission_index,
            year=2026,
            template_name=template.name,
        )

        decile_results = aggregate_by_decile(result)

        # Find first non-empty decile
        for i, count in enumerate(decile_results.household_count):
            if count > 0:
                first_net = decile_results.mean_net_impact[i]
                break

        # Find last non-empty decile
        for i in range(len(decile_results.household_count) - 1, -1, -1):
            if decile_results.household_count[i] > 0:
                last_net = decile_results.mean_net_impact[i]
                break

        # First decile should have better net impact than last
        assert first_net > last_net, (
            "Progressive dividend should result in better net impact for lower deciles"
        )
