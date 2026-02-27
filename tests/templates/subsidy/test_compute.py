from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import SubsidyParameters
from reformlab.templates.subsidy.compute import (
    SubsidyDecileResults,
    SubsidyResult,
    aggregate_subsidy_by_decile,
    compute_subsidy,
    compute_subsidy_amount,
    compute_subsidy_eligibility,
)


class TestComputeSubsidyEligibility:
    """Tests for subsidy eligibility computation."""

    def test_eligibility_with_income_cap(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Households below income cap are eligible."""
        eligibility = compute_subsidy_eligibility(
            sample_population, basic_subsidy_params, 2026
        )
        result = eligibility.to_pylist()

        # Incomes: 15k, 25k, 35k, 45k, 55k, 65k, 75k, 90k, 120k, 40k
        # Cap: 45000 - so first 4 and last should be eligible
        assert result[0] is True  # 15k
        assert result[1] is True  # 25k
        assert result[2] is True  # 35k
        assert result[3] is True  # 45k (at cap)
        assert result[4] is False  # 55k (above cap)
        assert result[5] is False  # 65k
        assert result[6] is False  # 75k
        assert result[7] is False  # 90k
        assert result[8] is False  # 120k
        assert result[9] is True  # 40k

    def test_eligibility_with_category(
        self,
        sample_population: pa.Table,
        category_subsidy_params: SubsidyParameters,
    ) -> None:
        """Households must be both below income cap AND have eligible category."""
        eligibility = compute_subsidy_eligibility(
            sample_population, category_subsidy_params, 2026
        )
        result = eligibility.to_pylist()

        # Households must have income <= 45000 AND (owner_occupier OR low_efficiency_home)
        # HH1: 15k, owner=T, low_eff=T -> eligible
        # HH2: 25k, owner=F, low_eff=T -> eligible
        # HH3: 35k, owner=T, low_eff=F -> eligible
        # HH4: 45k, owner=T, low_eff=T -> eligible
        # HH5: 55k (above cap) -> ineligible
        # HH10: 40k, owner=F, low_eff=T -> eligible
        assert result[0] is True
        assert result[1] is True
        assert result[2] is True
        assert result[3] is True
        assert result[4] is False  # above income cap
        assert result[9] is True

    def test_eligibility_no_income_cap(
        self,
        sample_population: pa.Table,
        no_cap_subsidy_params: SubsidyParameters,
    ) -> None:
        """Without income cap, all households are eligible."""
        eligibility = compute_subsidy_eligibility(
            sample_population, no_cap_subsidy_params, 2026
        )
        result = eligibility.to_pylist()

        # All should be eligible when no income cap
        assert all(result)

    def test_eligibility_missing_category_columns(
        self,
        small_population: pa.Table,
        category_subsidy_params: SubsidyParameters,
    ) -> None:
        """Required categories missing from data make all households ineligible."""
        eligibility = compute_subsidy_eligibility(
            small_population, category_subsidy_params, 2026
        )
        assert eligibility.to_pylist() == [False, False, False]

    def test_eligibility_empty_population(
        self,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Empty population returns empty eligibility array."""
        empty_pop = pa.table(
            {
                "household_id": pa.array([], type=pa.int64()),
                "income": pa.array([], type=pa.float64()),
            }
        )
        eligibility = compute_subsidy_eligibility(empty_pop, basic_subsidy_params, 2026)
        assert len(eligibility) == 0


class TestComputeSubsidyAmount:
    """Tests for subsidy amount computation."""

    def test_subsidy_amount_for_eligible(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Eligible households receive full subsidy amount."""
        eligibility = pa.array(
            [True, True, False, True, False] + [False] * 5, type=pa.bool_()
        )
        amounts = compute_subsidy_amount(
            sample_population, basic_subsidy_params, eligibility, 2026
        )
        result = amounts.to_pylist()

        assert result[0] == 5000.0  # Eligible
        assert result[1] == 5000.0  # Eligible
        assert result[2] == 0.0  # Ineligible
        assert result[3] == 5000.0  # Eligible
        assert result[4] == 0.0  # Ineligible

    def test_subsidy_amount_varies_by_year(
        self,
        small_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Subsidy amount changes based on rate_schedule year."""
        eligibility = pa.array([True, True, True], type=pa.bool_())

        amounts_2026 = compute_subsidy_amount(
            small_population, basic_subsidy_params, eligibility, 2026
        )
        amounts_2027 = compute_subsidy_amount(
            small_population, basic_subsidy_params, eligibility, 2027
        )

        assert all(a == 5000.0 for a in amounts_2026.to_pylist())
        assert all(a == 4500.0 for a in amounts_2027.to_pylist())

    def test_subsidy_amount_missing_year(
        self,
        small_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Missing year in rate_schedule defaults to 0."""
        eligibility = pa.array([True, True, True], type=pa.bool_())
        amounts = compute_subsidy_amount(
            small_population, basic_subsidy_params, eligibility, 2030
        )
        assert all(a == 0.0 for a in amounts.to_pylist())

    def test_subsidy_amount_raises_on_length_mismatch(
        self,
        small_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Eligibility mask length must match household count."""
        eligibility = pa.array([True, False], type=pa.bool_())
        with pytest.raises(ValueError, match="eligibility mask length"):
            compute_subsidy_amount(
                small_population, basic_subsidy_params, eligibility, 2026
            )


class TestComputeSubsidy:
    """Tests for complete subsidy computation."""

    def test_compute_subsidy_basic(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Subsidy computation returns correct result structure."""
        result = compute_subsidy(
            population=sample_population,
            parameters=basic_subsidy_params,
            year=2026,
            template_name="test-subsidy",
        )

        assert isinstance(result, SubsidyResult)
        assert len(result.household_ids) == 10
        assert len(result.subsidy_amount) == 10
        assert len(result.is_eligible) == 10
        assert len(result.income_decile) == 10
        assert result.year == 2026
        assert result.template_name == "test-subsidy"

    def test_compute_subsidy_total_cost(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Total cost equals sum of all subsidy amounts."""
        result = compute_subsidy(
            population=sample_population,
            parameters=basic_subsidy_params,
            year=2026,
            template_name="test",
        )

        expected_total = sum(result.subsidy_amount.to_pylist())
        assert result.total_cost == expected_total

    def test_compute_subsidy_eligible_count(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Correct number of households are eligible."""
        result = compute_subsidy(
            population=sample_population,
            parameters=basic_subsidy_params,
            year=2026,
            template_name="test",
        )

        eligible_count = sum(result.is_eligible.to_pylist())
        # 5 households below or at 45k cap
        assert eligible_count == 5

    def test_compute_subsidy_empty_population(
        self,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Empty population returns zero totals and empty arrays."""
        empty_pop = pa.table(
            {
                "household_id": pa.array([], type=pa.int64()),
                "income": pa.array([], type=pa.float64()),
            }
        )
        result = compute_subsidy(
            population=empty_pop,
            parameters=basic_subsidy_params,
            year=2026,
            template_name="empty",
        )

        assert result.total_cost == 0.0
        assert len(result.household_ids) == 0
        assert len(result.subsidy_amount) == 0
        assert len(result.is_eligible) == 0
        assert len(result.income_decile) == 0


class TestSubsidyResult:
    """Tests for SubsidyResult dataclass."""

    def test_subsidy_result_creation(self) -> None:
        """SubsidyResult can be created with all fields."""
        result = SubsidyResult(
            household_ids=pa.array([1, 2, 3]),
            subsidy_amount=pa.array([5000.0, 5000.0, 0.0]),
            is_eligible=pa.array([True, True, False]),
            income_decile=pa.array([1, 5, 10]),
            total_cost=10000.0,
            year=2026,
            template_name="test-template",
        )
        assert len(result.household_ids) == 3
        assert result.total_cost == 10000.0
        assert result.year == 2026

    def test_subsidy_result_is_frozen(self) -> None:
        """SubsidyResult is immutable."""
        result = SubsidyResult(
            household_ids=pa.array([1]),
            subsidy_amount=pa.array([5000.0]),
            is_eligible=pa.array([True]),
            income_decile=pa.array([5]),
            total_cost=5000.0,
            year=2026,
            template_name="test",
        )
        with pytest.raises(AttributeError):
            result.year = 2027  # type: ignore[misc]


class TestAggregateSubsidyByDecile:
    """Tests for subsidy decile aggregation."""

    def test_aggregate_by_decile(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Aggregation produces correct decile structure."""
        result = compute_subsidy(
            population=sample_population,
            parameters=basic_subsidy_params,
            year=2026,
            template_name="test",
        )
        decile_results = aggregate_subsidy_by_decile(result)

        assert isinstance(decile_results, SubsidyDecileResults)
        assert len(decile_results.decile) == 10
        assert decile_results.decile == tuple(range(1, 11))

    def test_aggregate_preserves_total(
        self,
        sample_population: pa.Table,
        basic_subsidy_params: SubsidyParameters,
    ) -> None:
        """Total subsidy across deciles equals total cost."""
        result = compute_subsidy(
            population=sample_population,
            parameters=basic_subsidy_params,
            year=2026,
            template_name="test",
        )
        decile_results = aggregate_subsidy_by_decile(result)

        total_from_deciles = sum(decile_results.total_subsidy)
        assert abs(total_from_deciles - result.total_cost) < 0.01


class TestSubsidyDecileResults:
    """Tests for SubsidyDecileResults dataclass."""

    def test_decile_results_creation(self) -> None:
        """SubsidyDecileResults can be created with aggregated metrics."""
        result = SubsidyDecileResults(
            decile=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            household_count=(10, 10, 10, 10, 10, 10, 10, 10, 10, 10),
            eligible_count=(10, 10, 8, 5, 3, 2, 1, 0, 0, 0),
            mean_subsidy=(
                5000.0,
                5000.0,
                4000.0,
                2500.0,
                1500.0,
                1000.0,
                500.0,
                0.0,
                0.0,
                0.0,
            ),
            total_subsidy=(
                50000.0,
                50000.0,
                40000.0,
                25000.0,
                15000.0,
                10000.0,
                5000.0,
                0.0,
                0.0,
                0.0,
            ),
        )
        assert len(result.decile) == 10
        assert result.mean_subsidy[0] == 5000.0

    def test_decile_results_is_frozen(self) -> None:
        """SubsidyDecileResults is immutable."""
        result = SubsidyDecileResults(
            decile=(1,),
            household_count=(10,),
            eligible_count=(5,),
            mean_subsidy=(2500.0,),
            total_subsidy=(25000.0,),
        )
        with pytest.raises(AttributeError):
            result.decile = (2,)  # type: ignore[misc]
