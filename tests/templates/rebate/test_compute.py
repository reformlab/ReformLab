from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import RebateParameters
from reformlab.templates.rebate.compute import (
    RebateDecileResults,
    RebateResult,
    aggregate_rebate_by_decile,
    compute_lump_sum_rebate,
    compute_progressive_rebate,
    compute_rebate,
)


class TestComputeLumpSumRebate:
    """Tests for lump sum rebate computation."""

    def test_lump_sum_equal_distribution(self) -> None:
        """Lump sum distributes total pool equally."""
        rebate_pool = 10000.0
        num_households = 5
        rebates = compute_lump_sum_rebate(rebate_pool, num_households)
        assert len(rebates) == 5
        assert all(v == 2000.0 for v in rebates.to_pylist())

    def test_lump_sum_preserves_total(self) -> None:
        """Total distributed equals rebate pool."""
        rebate_pool = 12345.67
        num_households = 10
        rebates = compute_lump_sum_rebate(rebate_pool, num_households)
        total = sum(rebates.to_pylist())
        assert abs(total - rebate_pool) < 0.01

    def test_lump_sum_empty_population(self) -> None:
        """Empty population returns empty array."""
        rebates = compute_lump_sum_rebate(10000.0, 0)
        assert len(rebates) == 0


class TestComputeProgressiveRebate:
    """Tests for progressive rebate computation."""

    def test_progressive_lower_deciles_get_more(
        self,
        progressive_rebate_params: RebateParameters,
    ) -> None:
        """Lower income deciles receive higher rebate amounts."""
        rebate_pool = 10000.0
        deciles = pa.array([1, 5, 10])  # Low, middle, high income
        income_weights = progressive_rebate_params.income_weights

        rebates = compute_progressive_rebate(
            rebate_pool=rebate_pool,
            deciles=deciles,
            income_weights=income_weights,
        )
        result = rebates.to_pylist()
        # Decile 1 (weight 2.0) should get more than decile 5 (weight 1.1)
        # which should get more than decile 10 (weight 0.2)
        assert result[0] > result[1] > result[2]

    def test_progressive_preserves_total(
        self,
        progressive_rebate_params: RebateParameters,
    ) -> None:
        """Total progressive distribution equals rebate pool."""
        rebate_pool = 50000.0
        deciles = pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        income_weights = progressive_rebate_params.income_weights

        rebates = compute_progressive_rebate(
            rebate_pool=rebate_pool,
            deciles=deciles,
            income_weights=income_weights,
        )
        total = sum(rebates.to_pylist())
        assert abs(total - rebate_pool) < 0.01

    def test_progressive_empty_population(
        self,
        progressive_rebate_params: RebateParameters,
    ) -> None:
        """Empty population returns empty array."""
        rebates = compute_progressive_rebate(
            rebate_pool=10000.0,
            deciles=pa.array([], type=pa.int64()),
            income_weights=progressive_rebate_params.income_weights,
        )
        assert len(rebates) == 0

    def test_progressive_missing_weight_uses_default(self) -> None:
        """Missing decile weight defaults to 1.0."""
        rebate_pool = 3000.0
        deciles = pa.array([1, 5, 10])
        # Only provide weight for decile_1
        income_weights = {"decile_1": 2.0}

        rebates = compute_progressive_rebate(
            rebate_pool=rebate_pool,
            deciles=deciles,
            income_weights=income_weights,
        )
        result = rebates.to_pylist()
        # With weights 2.0, 1.0, 1.0 (total 4.0):
        # decile_1 gets 2.0/4.0 * 3000 = 1500
        # decile_5 gets 1.0/4.0 * 3000 = 750
        # decile_10 gets 1.0/4.0 * 3000 = 750
        assert abs(result[0] - 1500.0) < 0.01
        assert abs(result[1] - 750.0) < 0.01
        assert abs(result[2] - 750.0) < 0.01


class TestComputeRebate:
    """Tests for complete rebate computation."""

    def test_compute_rebate_lump_sum(
        self,
        sample_population: pa.Table,
        lump_sum_rebate_params: RebateParameters,
    ) -> None:
        """Lump sum rebate computation returns correct result."""
        rebate_pool = 10000.0
        result = compute_rebate(
            population=sample_population,
            parameters=lump_sum_rebate_params,
            rebate_pool=rebate_pool,
            year=2026,
            template_name="test-lump-sum",
        )

        assert isinstance(result, RebateResult)
        assert len(result.household_ids) == 10
        assert len(result.rebate_amount) == 10
        assert result.year == 2026
        assert result.template_name == "test-lump-sum"

        # All rebates should be equal (lump sum)
        rebates = result.rebate_amount.to_pylist()
        assert all(abs(r - 1000.0) < 0.01 for r in rebates)

    def test_compute_rebate_progressive(
        self,
        sample_population: pa.Table,
        progressive_rebate_params: RebateParameters,
    ) -> None:
        """Progressive rebate computation returns correct result."""
        rebate_pool = 10000.0
        result = compute_rebate(
            population=sample_population,
            parameters=progressive_rebate_params,
            rebate_pool=rebate_pool,
            year=2026,
            template_name="test-progressive",
        )

        assert isinstance(result, RebateResult)
        assert len(result.rebate_amount) == 10

        # Rebates should vary (progressive)
        rebates = result.rebate_amount.to_pylist()
        assert max(rebates) > min(rebates)

    def test_compute_rebate_total_distributed(
        self,
        sample_population: pa.Table,
        lump_sum_rebate_params: RebateParameters,
    ) -> None:
        """Total distributed equals rebate pool."""
        rebate_pool = 15000.0
        result = compute_rebate(
            population=sample_population,
            parameters=lump_sum_rebate_params,
            rebate_pool=rebate_pool,
            year=2026,
            template_name="test",
        )

        assert abs(result.total_distributed - rebate_pool) < 0.01

    def test_compute_rebate_no_type_defaults_to_lump_sum(
        self,
        sample_population: pa.Table,
        no_type_rebate_params: RebateParameters,
    ) -> None:
        """Missing rebate_type defaults to lump sum distribution."""
        rebate_pool = 10000.0
        result = compute_rebate(
            population=sample_population,
            parameters=no_type_rebate_params,
            rebate_pool=rebate_pool,
            year=2026,
            template_name="test",
        )

        # All rebates should be equal (lump sum default)
        rebates = result.rebate_amount.to_pylist()
        assert all(abs(r - 1000.0) < 0.01 for r in rebates)


class TestRebateResult:
    """Tests for RebateResult dataclass."""

    def test_rebate_result_creation(self) -> None:
        """RebateResult can be created with all fields."""
        result = RebateResult(
            household_ids=pa.array([1, 2, 3]),
            rebate_amount=pa.array([1000.0, 1000.0, 1000.0]),
            income_decile=pa.array([1, 5, 10]),
            total_distributed=3000.0,
            year=2026,
            template_name="test-template",
        )
        assert len(result.household_ids) == 3
        assert result.total_distributed == 3000.0
        assert result.year == 2026

    def test_rebate_result_is_frozen(self) -> None:
        """RebateResult is immutable."""
        result = RebateResult(
            household_ids=pa.array([1]),
            rebate_amount=pa.array([1000.0]),
            income_decile=pa.array([5]),
            total_distributed=1000.0,
            year=2026,
            template_name="test",
        )
        with pytest.raises(AttributeError):
            result.year = 2027  # type: ignore[misc]


class TestAggregateRebateByDecile:
    """Tests for rebate decile aggregation."""

    def test_aggregate_by_decile(
        self,
        sample_population: pa.Table,
        lump_sum_rebate_params: RebateParameters,
    ) -> None:
        """Aggregation produces correct decile structure."""
        result = compute_rebate(
            population=sample_population,
            parameters=lump_sum_rebate_params,
            rebate_pool=10000.0,
            year=2026,
            template_name="test",
        )
        decile_results = aggregate_rebate_by_decile(result)

        assert isinstance(decile_results, RebateDecileResults)
        assert len(decile_results.decile) == 10
        assert decile_results.decile == tuple(range(1, 11))

    def test_aggregate_preserves_total(
        self,
        sample_population: pa.Table,
        lump_sum_rebate_params: RebateParameters,
    ) -> None:
        """Total rebate across deciles equals total distributed."""
        rebate_pool = 25000.0
        result = compute_rebate(
            population=sample_population,
            parameters=lump_sum_rebate_params,
            rebate_pool=rebate_pool,
            year=2026,
            template_name="test",
        )
        decile_results = aggregate_rebate_by_decile(result)

        total_from_deciles = sum(decile_results.total_rebate)
        assert abs(total_from_deciles - result.total_distributed) < 0.01


class TestRebateDecileResults:
    """Tests for RebateDecileResults dataclass."""

    def test_decile_results_creation(self) -> None:
        """RebateDecileResults can be created with aggregated metrics."""
        result = RebateDecileResults(
            decile=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            household_count=(10, 10, 10, 10, 10, 10, 10, 10, 10, 10),
            mean_rebate=(2000.0, 1800.0, 1500.0, 1300.0, 1100.0, 900.0, 700.0, 500.0, 300.0, 200.0),
            total_rebate=(20000.0, 18000.0, 15000.0, 13000.0, 11000.0, 9000.0, 7000.0, 5000.0, 3000.0, 2000.0),
        )
        assert len(result.decile) == 10
        assert result.mean_rebate[0] == 2000.0

    def test_decile_results_is_frozen(self) -> None:
        """RebateDecileResults is immutable."""
        result = RebateDecileResults(
            decile=(1,),
            household_count=(10,),
            mean_rebate=(1000.0,),
            total_rebate=(10000.0,),
        )
        with pytest.raises(AttributeError):
            result.decile = (2,)  # type: ignore[misc]
