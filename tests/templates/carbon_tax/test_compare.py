# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import pyarrow as pa

from reformlab.data.emission_factors import build_emission_factor_index
from reformlab.templates import list_carbon_tax_templates, load_carbon_tax_template
from reformlab.templates.carbon_tax import (
    ComparisonResult,
    compare_decile_impacts,
    decile_results_to_table,
    run_carbon_tax_batch,
)


class TestRunCarbonTaxBatch:
    """Tests for run_carbon_tax_batch function."""

    def test_batch_returns_dict(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Batch run returns dict mapping names to results."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        assert isinstance(results, dict)
        assert len(results) == 2

    def test_batch_result_keys_are_scenario_names(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Result keys match scenario names."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        expected_names = {s.name for s in scenarios}
        assert set(results.keys()) == expected_names

    def test_batch_all_scenarios(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Batch can run all available templates."""
        emission_index = build_emission_factor_index(emission_factor_table)
        variants = list_carbon_tax_templates()
        scenarios = [load_carbon_tax_template(v) for v in variants]

        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        assert len(results) == len(variants)


class TestCompareDecileImpacts:
    """Tests for compare_decile_impacts function."""

    def test_compare_returns_comparison_result(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Comparison returns ComparisonResult dataclass."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        assert isinstance(comparison, ComparisonResult)

    def test_comparison_has_scenarios_tuple(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """ComparisonResult has scenarios tuple."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        assert len(comparison.scenarios) == 2

    def test_comparison_has_decile_results(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """ComparisonResult has decile_results dict."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        assert len(comparison.decile_results) == 2

    def test_comparison_table_is_pyarrow(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """ComparisonResult has pa.Table comparison_table (AC-4)."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
            load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        assert isinstance(comparison.comparison_table, pa.Table)

    def test_comparison_table_has_decile_column(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Comparison table has decile column."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        assert "decile" in comparison.comparison_table.column_names

    def test_comparison_table_has_10_rows(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Comparison table has 10 rows (one per decile)."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenarios = [
            load_carbon_tax_template("carbon-tax-flat-no-redistribution"),
        ]
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=scenarios,
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)
        assert comparison.comparison_table.num_rows == 10

    def test_comparison_table_includes_required_mean_metrics(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Comparison table exposes mean tax, redistribution, and net impact columns (AC-4)."""
        emission_index = build_emission_factor_index(emission_factor_table)
        scenario = load_carbon_tax_template("carbon-tax-flat-no-redistribution")
        results = run_carbon_tax_batch(
            population=sample_population,
            scenarios=[scenario],
            emission_index=emission_index,
            year=2026,
        )
        comparison = compare_decile_impacts(results)

        prefix = scenario.name.replace(" ", "_").replace("-", "_").replace(",", "")
        expected = {
            f"{prefix}_mean_tax_burden",
            f"{prefix}_mean_redistribution",
            f"{prefix}_mean_net_impact",
        }
        assert expected.issubset(set(comparison.comparison_table.column_names))


class TestDecileResultsToTable:
    """Tests for decile_results_to_table function."""

    def test_returns_pyarrow_table(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
        flat_rate_params,
    ) -> None:
        """Function returns PyArrow table."""
        from reformlab.templates.carbon_tax.compute import (
            aggregate_by_decile,
            compute_carbon_tax,
        )

        emission_index = build_emission_factor_index(emission_factor_table)
        result = compute_carbon_tax(
            population=sample_population,
            policy=flat_rate_params,
            emission_index=emission_index,
            year=2026,
        )
        decile_results = aggregate_by_decile(result)
        table = decile_results_to_table(decile_results)
        assert isinstance(table, pa.Table)

    def test_table_has_expected_columns(
        self,
        sample_population: pa.Table,
        emission_factor_table: pa.Table,
        flat_rate_params,
    ) -> None:
        """Table has expected metric columns."""
        from reformlab.templates.carbon_tax.compute import (
            aggregate_by_decile,
            compute_carbon_tax,
        )

        emission_index = build_emission_factor_index(emission_factor_table)
        result = compute_carbon_tax(
            population=sample_population,
            policy=flat_rate_params,
            emission_index=emission_index,
            year=2026,
        )
        decile_results = aggregate_by_decile(result)
        table = decile_results_to_table(decile_results)

        expected_columns = {
            "decile",
            "household_count",
            "mean_tax_burden",
            "mean_redistribution",
            "mean_net_impact",
            "total_tax_burden",
            "total_redistribution",
            "total_net_impact",
        }
        assert set(table.column_names) == expected_columns
