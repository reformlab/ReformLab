from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.data.emission_factors import build_emission_factor_index
from reformlab.templates.carbon_tax.compute import (
    CarbonTaxResult,
    DecileResults,
    assign_income_deciles,
    compute_lump_sum_redistribution,
    compute_progressive_redistribution,
    compute_tax_burden,
    get_exemption_rate,
)
from reformlab.templates.schema import CarbonTaxParameters


class TestAssignIncomeDeciles:
    """Tests for income decile assignment function."""

    def test_assign_deciles_basic(self) -> None:
        """Deciles are assigned 1-10 based on income percentiles."""
        incomes = pa.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        deciles = assign_income_deciles(incomes)
        result = deciles.to_pylist()
        # Each income should be in a different decile
        assert sorted(result) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_assign_deciles_equal_incomes(self) -> None:
        """Equal incomes get assigned to deciles based on position."""
        incomes = pa.array([50000.0] * 10)
        deciles = assign_income_deciles(incomes)
        result = deciles.to_pylist()
        # All should be spread across deciles
        assert len(result) == 10
        assert all(1 <= d <= 10 for d in result)

    def test_assign_deciles_returns_int_array(self) -> None:
        """Result is an int64 array."""
        incomes = pa.array([10.0, 20.0, 30.0])
        deciles = assign_income_deciles(incomes)
        assert deciles.type == pa.int64()

    def test_assign_deciles_small_population(self) -> None:
        """Small populations still get valid decile assignments."""
        incomes = pa.array([20000.0, 50000.0, 100000.0])
        deciles = assign_income_deciles(incomes)
        result = deciles.to_pylist()
        # Smallest income should be lower decile, largest should be higher
        assert result[0] < result[2]


class TestGetExemptionRate:
    """Tests for exemption rate lookup."""

    def test_no_exemptions_returns_zero(self) -> None:
        """No exemptions means 0.0 rate reduction."""
        exemptions: tuple[dict[str, object], ...] = ()
        rate = get_exemption_rate("transport_fuel", exemptions)
        assert rate == 0.0

    def test_full_exemption(self) -> None:
        """Category with full exemption returns 1.0."""
        exemptions = ({"category": "agricultural_fuel", "rate_reduction": 1.0},)
        rate = get_exemption_rate("agricultural_fuel", exemptions)
        assert rate == 1.0

    def test_partial_exemption(self) -> None:
        """Category with partial exemption returns correct rate."""
        exemptions = ({"category": "heating_fuel", "rate_reduction": 0.5},)
        rate = get_exemption_rate("heating_fuel", exemptions)
        assert rate == 0.5

    def test_unexempted_category(self) -> None:
        """Category not in exemptions returns 0.0."""
        exemptions = ({"category": "heating_fuel", "rate_reduction": 0.5},)
        rate = get_exemption_rate("transport_fuel", exemptions)
        assert rate == 0.0


class TestComputeTaxBurden:
    """Tests for tax burden computation."""

    def test_compute_tax_burden_basic(
        self,
        small_population: pa.Table,
        emission_factor_table: pa.Table,
        flat_rate_params: CarbonTaxParameters,
    ) -> None:
        """Tax burden computed correctly for each household."""
        emission_index = build_emission_factor_index(emission_factor_table)
        tax_burden = compute_tax_burden(
            population=small_population,
            parameters=flat_rate_params,
            emission_index=emission_index,
            year=2026,
        )
        assert len(tax_burden) == 3
        # Tax burden should be positive for all households
        assert all(v > 0 for v in tax_burden.to_pylist())

    def test_tax_burden_kg_to_tonne_conversion(
        self,
        small_population: pa.Table,
        emission_factor_table: pa.Table,
        flat_rate_params: CarbonTaxParameters,
    ) -> None:
        """Emission factors (kg CO2) are converted to tonnes before rate application."""
        emission_index = build_emission_factor_index(emission_factor_table)
        tax_burden = compute_tax_burden(
            population=small_population,
            parameters=flat_rate_params,
            emission_index=emission_index,
            year=2026,
        )
        # Manual calculation for household 1:
        # transport: 1000 L * 2.31 kg/L / 1000 * 44.60 EUR/t = 103.03 EUR
        # heating: 500 L * 2.68 kg/L / 1000 * 44.60 EUR/t = 59.77 EUR
        # gas: 800 m3 * 2.0 kg/m3 / 1000 * 44.60 EUR/t = 71.36 EUR
        # Total: ~234.16 EUR
        expected_household_1 = (
            1000.0 * 2.31 / 1000 * 44.60 +
            500.0 * 2.68 / 1000 * 44.60 +
            800.0 * 2.0 / 1000 * 44.60
        )
        assert abs(tax_burden[0].as_py() - expected_household_1) < 0.01

    def test_tax_burden_with_exemption(
        self,
        small_population: pa.Table,
        emission_factor_table: pa.Table,
        flat_rate_with_exemption_params: CarbonTaxParameters,
    ) -> None:
        """Exemptions reduce tax burden for exempted categories."""
        emission_index = build_emission_factor_index(emission_factor_table)

        # Compute without exemption
        no_exemption_params = CarbonTaxParameters(
            rate_schedule={2026: 44.60},
            covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
            exemptions=(),
        )
        tax_no_exemption = compute_tax_burden(
            population=small_population,
            parameters=no_exemption_params,
            emission_index=emission_index,
            year=2026,
        )

        # Compute with 50% heating exemption
        tax_with_exemption = compute_tax_burden(
            population=small_population,
            parameters=flat_rate_with_exemption_params,
            emission_index=emission_index,
            year=2026,
        )

        # Tax with exemption should be lower
        for i in range(len(tax_no_exemption)):
            assert tax_with_exemption[i].as_py() < tax_no_exemption[i].as_py()

    def test_tax_burden_increases_with_higher_rate(
        self,
        small_population: pa.Table,
        emission_factor_table: pa.Table,
    ) -> None:
        """Higher carbon tax rates produce higher tax burdens."""
        emission_index = build_emission_factor_index(emission_factor_table)

        low_rate_params = CarbonTaxParameters(
            rate_schedule={2026: 44.60},
            covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        )
        high_rate_params = CarbonTaxParameters(
            rate_schedule={2026: 100.0},
            covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        )

        tax_low = compute_tax_burden(small_population, low_rate_params, emission_index, 2026)
        tax_high = compute_tax_burden(small_population, high_rate_params, emission_index, 2026)

        for i in range(len(tax_low)):
            assert tax_high[i].as_py() > tax_low[i].as_py()


class TestComputeLumpSumRedistribution:
    """Tests for lump sum redistribution computation."""

    def test_lump_sum_equal_distribution(self) -> None:
        """Lump sum distributes total revenue equally."""
        total_revenue = 10000.0
        num_households = 5
        redistribution = compute_lump_sum_redistribution(total_revenue, num_households)
        assert len(redistribution) == 5
        assert all(v == 2000.0 for v in redistribution.to_pylist())

    def test_lump_sum_preserves_total(self) -> None:
        """Total redistribution equals total revenue."""
        total_revenue = 12345.67
        num_households = 10
        redistribution = compute_lump_sum_redistribution(total_revenue, num_households)
        total_redist = sum(redistribution.to_pylist())
        assert abs(total_redist - total_revenue) < 0.01


class TestComputeProgressiveRedistribution:
    """Tests for progressive redistribution computation."""

    def test_progressive_lower_deciles_get_more(
        self,
        progressive_redistribution_params: CarbonTaxParameters,
    ) -> None:
        """Lower income deciles receive higher redistribution amounts."""
        total_revenue = 10000.0
        deciles = pa.array([1, 5, 10])  # Low, middle, high income
        income_weights = progressive_redistribution_params.income_weights

        redistribution = compute_progressive_redistribution(
            total_revenue=total_revenue,
            deciles=deciles,
            income_weights=income_weights,
        )
        result = redistribution.to_pylist()
        # Decile 1 should get more than decile 5, which should get more than decile 10
        assert result[0] > result[1] > result[2]

    def test_progressive_preserves_total(
        self,
        progressive_redistribution_params: CarbonTaxParameters,
    ) -> None:
        """Total progressive redistribution equals total revenue."""
        total_revenue = 50000.0
        deciles = pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        income_weights = progressive_redistribution_params.income_weights

        redistribution = compute_progressive_redistribution(
            total_revenue=total_revenue,
            deciles=deciles,
            income_weights=income_weights,
        )
        total_redist = sum(redistribution.to_pylist())
        assert abs(total_redist - total_revenue) < 0.01


class TestCarbonTaxResult:
    """Tests for CarbonTaxResult dataclass."""

    def test_carbon_tax_result_creation(self) -> None:
        """CarbonTaxResult can be created with all fields."""
        result = CarbonTaxResult(
            household_ids=pa.array([1, 2, 3]),
            tax_burden=pa.array([100.0, 200.0, 300.0]),
            redistribution=pa.array([150.0, 150.0, 150.0]),
            net_impact=pa.array([50.0, -50.0, -150.0]),
            income_decile=pa.array([1, 5, 10]),
            total_revenue=600.0,
            total_redistribution=450.0,
            year=2026,
            template_name="test-template",
        )
        assert len(result.household_ids) == 3
        assert result.total_revenue == 600.0
        assert result.year == 2026

    def test_carbon_tax_result_is_frozen(self) -> None:
        """CarbonTaxResult is immutable."""
        result = CarbonTaxResult(
            household_ids=pa.array([1]),
            tax_burden=pa.array([100.0]),
            redistribution=pa.array([100.0]),
            net_impact=pa.array([0.0]),
            income_decile=pa.array([5]),
            total_revenue=100.0,
            total_redistribution=100.0,
            year=2026,
            template_name="test",
        )
        with pytest.raises(AttributeError):
            result.year = 2027  # type: ignore[misc]


class TestDecileResults:
    """Tests for DecileResults dataclass."""

    def test_decile_results_creation(self) -> None:
        """DecileResults can be created with aggregated metrics."""
        result = DecileResults(
            decile=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            household_count=(10, 10, 10, 10, 10, 10, 10, 10, 10, 10),
            mean_tax_burden=(100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0),
            mean_redistribution=(200.0, 180.0, 160.0, 140.0, 120.0, 100.0, 80.0, 60.0, 40.0, 20.0),
            mean_net_impact=(100.0, 60.0, 20.0, -20.0, -60.0, -100.0, -140.0, -180.0, -220.0, -260.0),
            total_tax_burden=(1000.0, 1200.0, 1400.0, 1600.0, 1800.0, 2000.0, 2200.0, 2400.0, 2600.0, 2800.0),
            total_redistribution=(2000.0, 1800.0, 1600.0, 1400.0, 1200.0, 1000.0, 800.0, 600.0, 400.0, 200.0),
            total_net_impact=(1000.0, 600.0, 200.0, -200.0, -600.0, -1000.0, -1400.0, -1800.0, -2200.0, -2600.0),
        )
        assert len(result.decile) == 10
        assert result.mean_tax_burden[0] == 100.0

    def test_decile_results_is_frozen(self) -> None:
        """DecileResults is immutable."""
        result = DecileResults(
            decile=(1,),
            household_count=(10,),
            mean_tax_burden=(100.0,),
            mean_redistribution=(100.0,),
            mean_net_impact=(0.0,),
            total_tax_burden=(1000.0,),
            total_redistribution=(1000.0,),
            total_net_impact=(0.0,),
        )
        with pytest.raises(AttributeError):
            result.decile = (2,)  # type: ignore[misc]
