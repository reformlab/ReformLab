from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import FeebateParameters
from reformlab.templates.feebate.compute import (
    FeebateDecileResults,
    FeebateResult,
    aggregate_feebate_by_decile,
    compute_feebate,
    compute_fee_amount,
    compute_rebate_amount,
)


class TestComputeFeeAmount:
    """Tests for fee amount computation."""

    def test_fee_above_pivot(self) -> None:
        """Household above pivot pays fee."""
        fee = compute_fee_amount(
            metric_value=140.0,
            pivot_point=120.0,
            fee_rate=50.0,
        )
        # (140 - 120) * 50 = 1000
        assert fee == 1000.0

    def test_fee_at_pivot(self) -> None:
        """Household exactly at pivot pays no fee."""
        fee = compute_fee_amount(
            metric_value=120.0,
            pivot_point=120.0,
            fee_rate=50.0,
        )
        assert fee == 0.0

    def test_fee_below_pivot(self) -> None:
        """Household below pivot pays no fee."""
        fee = compute_fee_amount(
            metric_value=100.0,
            pivot_point=120.0,
            fee_rate=50.0,
        )
        assert fee == 0.0


class TestComputeRebateAmount:
    """Tests for rebate amount computation."""

    def test_rebate_below_pivot(self) -> None:
        """Household below pivot receives rebate."""
        rebate = compute_rebate_amount(
            metric_value=80.0,
            pivot_point=120.0,
            rebate_rate=50.0,
        )
        # (120 - 80) * 50 = 2000
        assert rebate == 2000.0

    def test_rebate_at_pivot(self) -> None:
        """Household exactly at pivot receives no rebate."""
        rebate = compute_rebate_amount(
            metric_value=120.0,
            pivot_point=120.0,
            rebate_rate=50.0,
        )
        assert rebate == 0.0

    def test_rebate_above_pivot(self) -> None:
        """Household above pivot receives no rebate."""
        rebate = compute_rebate_amount(
            metric_value=140.0,
            pivot_point=120.0,
            rebate_rate=50.0,
        )
        assert rebate == 0.0


class TestComputeFeebate:
    """Tests for complete feebate computation."""

    def test_compute_feebate_basic(
        self,
        small_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Feebate computation returns correct result structure."""
        result = compute_feebate(
            population=small_population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test-feebate",
        )

        assert isinstance(result, FeebateResult)
        assert len(result.household_ids) == 3
        assert len(result.fee_amount) == 3
        assert len(result.rebate_amount) == 3
        assert len(result.net_impact) == 3
        assert len(result.metric_value) == 3
        assert result.year == 2026
        assert result.template_name == "test-feebate"

    def test_compute_feebate_fee_and_rebate_values(
        self,
        small_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Correct fee and rebate amounts for each household."""
        result = compute_feebate(
            population=small_population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test",
        )

        fees = result.fee_amount.to_pylist()
        rebates = result.rebate_amount.to_pylist()

        # HH1: 80 g/km - below pivot - rebate = (120-80)*50 = 2000
        assert fees[0] == 0.0
        assert rebates[0] == 2000.0

        # HH2: 120 g/km - at pivot - no fee/rebate
        assert fees[1] == 0.0
        assert rebates[1] == 0.0

        # HH3: 160 g/km - above pivot - fee = (160-120)*50 = 2000
        assert fees[2] == 2000.0
        assert rebates[2] == 0.0

    def test_compute_feebate_net_impact(
        self,
        small_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Net impact = rebate - fee."""
        result = compute_feebate(
            population=small_population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test",
        )

        nets = result.net_impact.to_pylist()

        # HH1: rebate 2000, fee 0 -> net +2000
        assert nets[0] == 2000.0
        # HH2: rebate 0, fee 0 -> net 0
        assert nets[1] == 0.0
        # HH3: rebate 0, fee 2000 -> net -2000
        assert nets[2] == -2000.0

    def test_compute_feebate_fiscal_balance(
        self,
        small_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Net fiscal balance = total_fees - total_rebates."""
        result = compute_feebate(
            population=small_population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test",
        )

        # With symmetric rates: HH1 rebate 2000, HH3 fee 2000
        # Balance = 2000 - 2000 = 0
        assert result.total_fees == 2000.0
        assert result.total_rebates == 2000.0
        assert result.net_fiscal_balance == 0.0

    def test_compute_feebate_asymmetric_rates(
        self,
        small_population: pa.Table,
        asymmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Asymmetric rates produce different fee/rebate magnitudes."""
        result = compute_feebate(
            population=small_population,
            parameters=asymmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test",
        )

        fees = result.fee_amount.to_pylist()
        rebates = result.rebate_amount.to_pylist()

        # HH1: 80 g/km - rebate = (120-80)*25 = 1000
        assert rebates[0] == 1000.0

        # HH3: 160 g/km - fee = (160-120)*75 = 3000
        assert fees[2] == 3000.0

        # Net positive fiscal balance (fees > rebates)
        assert result.net_fiscal_balance > 0

    def test_compute_feebate_missing_metric_column(
        self,
        small_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Missing metric column treats everyone at pivot."""
        result = compute_feebate(
            population=small_population,
            parameters=symmetric_feebate_params,
            metric_column="nonexistent_column",
            year=2026,
            template_name="test",
        )

        # Everyone at pivot = no fees or rebates
        assert all(f == 0.0 for f in result.fee_amount.to_pylist())
        assert all(r == 0.0 for r in result.rebate_amount.to_pylist())

    def test_compute_feebate_null_metric_is_neutral(
        self,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Null metric values are treated as pivot-point (no fee/rebate)."""
        population = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "income": pa.array([20000.0, 50000.0, 100000.0], type=pa.float64()),
                "vehicle_emissions_gkm": pa.array([80.0, None, 160.0], type=pa.float64()),
            }
        )
        result = compute_feebate(
            population=population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="null-metric",
        )

        assert result.fee_amount.to_pylist() == [0.0, 0.0, 2000.0]
        assert result.rebate_amount.to_pylist() == [2000.0, 0.0, 0.0]

    def test_compute_feebate_empty_population(
        self,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Empty population returns zero totals and empty arrays."""
        empty_pop = pa.table(
            {
                "household_id": pa.array([], type=pa.int64()),
                "income": pa.array([], type=pa.float64()),
                "vehicle_emissions_gkm": pa.array([], type=pa.float64()),
            }
        )
        result = compute_feebate(
            population=empty_pop,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="empty",
        )

        assert result.total_fees == 0.0
        assert result.total_rebates == 0.0
        assert result.net_fiscal_balance == 0.0
        assert len(result.household_ids) == 0
        assert len(result.fee_amount) == 0
        assert len(result.rebate_amount) == 0
        assert len(result.net_impact) == 0


class TestFeebateResult:
    """Tests for FeebateResult dataclass."""

    def test_feebate_result_creation(self) -> None:
        """FeebateResult can be created with all fields."""
        result = FeebateResult(
            household_ids=pa.array([1, 2, 3]),
            fee_amount=pa.array([0.0, 0.0, 2000.0]),
            rebate_amount=pa.array([2000.0, 0.0, 0.0]),
            net_impact=pa.array([2000.0, 0.0, -2000.0]),
            metric_value=pa.array([80.0, 120.0, 160.0]),
            income_decile=pa.array([1, 5, 10]),
            total_fees=2000.0,
            total_rebates=2000.0,
            net_fiscal_balance=0.0,
            year=2026,
            template_name="test-template",
        )
        assert len(result.household_ids) == 3
        assert result.net_fiscal_balance == 0.0
        assert result.year == 2026

    def test_feebate_result_is_frozen(self) -> None:
        """FeebateResult is immutable."""
        result = FeebateResult(
            household_ids=pa.array([1]),
            fee_amount=pa.array([0.0]),
            rebate_amount=pa.array([1000.0]),
            net_impact=pa.array([1000.0]),
            metric_value=pa.array([100.0]),
            income_decile=pa.array([5]),
            total_fees=0.0,
            total_rebates=1000.0,
            net_fiscal_balance=-1000.0,
            year=2026,
            template_name="test",
        )
        with pytest.raises(AttributeError):
            result.year = 2027  # type: ignore[misc]


class TestAggregateFeebateByDecile:
    """Tests for feebate decile aggregation."""

    def test_aggregate_by_decile(
        self,
        sample_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Aggregation produces correct decile structure."""
        result = compute_feebate(
            population=sample_population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test",
        )
        decile_results = aggregate_feebate_by_decile(result)

        assert isinstance(decile_results, FeebateDecileResults)
        assert len(decile_results.decile) == 10
        assert decile_results.decile == tuple(range(1, 11))

    def test_aggregate_preserves_totals(
        self,
        sample_population: pa.Table,
        symmetric_feebate_params: FeebateParameters,
    ) -> None:
        """Total fees/rebates across deciles equals total from result."""
        result = compute_feebate(
            population=sample_population,
            parameters=symmetric_feebate_params,
            metric_column="vehicle_emissions_gkm",
            year=2026,
            template_name="test",
        )
        decile_results = aggregate_feebate_by_decile(result)

        total_fee_from_deciles = sum(decile_results.total_fee)
        total_rebate_from_deciles = sum(decile_results.total_rebate)

        assert abs(total_fee_from_deciles - result.total_fees) < 0.01
        assert abs(total_rebate_from_deciles - result.total_rebates) < 0.01


class TestFeebateDecileResults:
    """Tests for FeebateDecileResults dataclass."""

    def test_decile_results_creation(self) -> None:
        """FeebateDecileResults can be created with aggregated metrics."""
        result = FeebateDecileResults(
            decile=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            household_count=(10, 10, 10, 10, 10, 10, 10, 10, 10, 10),
            mean_fee=(0.0, 0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0),
            mean_rebate=(800.0, 700.0, 600.0, 500.0, 400.0, 300.0, 200.0, 100.0, 0.0, 0.0),
            mean_net_impact=(800.0, 700.0, 500.0, 300.0, 100.0, -100.0, -300.0, -500.0, -700.0, -800.0),
            total_fee=(0.0, 0.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0),
            total_rebate=(8000.0, 7000.0, 6000.0, 5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 0.0, 0.0),
            total_net_impact=(8000.0, 7000.0, 5000.0, 3000.0, 1000.0, -1000.0, -3000.0, -5000.0, -7000.0, -8000.0),
        )
        assert len(result.decile) == 10
        assert result.mean_fee[0] == 0.0
        assert result.mean_rebate[0] == 800.0

    def test_decile_results_is_frozen(self) -> None:
        """FeebateDecileResults is immutable."""
        result = FeebateDecileResults(
            decile=(1,),
            household_count=(10,),
            mean_fee=(0.0,),
            mean_rebate=(500.0,),
            mean_net_impact=(500.0,),
            total_fee=(0.0,),
            total_rebate=(5000.0,),
            total_net_impact=(5000.0,),
        )
        with pytest.raises(AttributeError):
            result.decile = (2,)  # type: ignore[misc]
