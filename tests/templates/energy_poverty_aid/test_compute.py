# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for energy poverty aid computation module.

Story 13.3 — AC #1, #2, #3, #4.
"""

from __future__ import annotations

import dataclasses

import pyarrow as pa
import pytest

from reformlab.templates.energy_poverty_aid.compute import (
    EnergyPovertyAidDecileResults,
    EnergyPovertyAidParameters,
    EnergyPovertyAidResult,
    aggregate_energy_poverty_aid_by_decile,
    compute_energy_poverty_aid,
)
from reformlab.templates.exceptions import TemplateError
from reformlab.templates.schema import PolicyParameters, infer_policy_type


class TestEnergyPovertyAidParameters:
    """AC #1: EnergyPovertyAidParameters frozen dataclass subclassing PolicyParameters."""

    def test_is_frozen_dataclass(self) -> None:
        params = EnergyPovertyAidParameters(rate_schedule={})
        with pytest.raises(dataclasses.FrozenInstanceError):
            params.income_ceiling = 5000.0  # type: ignore[misc]

    def test_inherits_policy_parameters(self) -> None:
        params = EnergyPovertyAidParameters(rate_schedule={})
        assert isinstance(params, PolicyParameters)

    def test_custom_fields_accessible(self) -> None:
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            income_ceiling=15000.0,
            energy_share_threshold=0.10,
            base_aid_amount=300.0,
            max_energy_factor=3.0,
            income_ceiling_schedule={2027: 16000.0},
            energy_share_schedule={2028: 0.09},
            aid_schedule={2029: 350.0},
        )
        assert params.income_ceiling == 15000.0
        assert params.energy_share_threshold == 0.10
        assert params.base_aid_amount == 300.0
        assert params.max_energy_factor == 3.0
        assert params.income_ceiling_schedule == {2027: 16000.0}
        assert params.energy_share_schedule == {2028: 0.09}
        assert params.aid_schedule == {2029: 350.0}

    def test_default_values(self) -> None:
        params = EnergyPovertyAidParameters(rate_schedule={})
        assert params.income_ceiling == 11000.0
        assert params.energy_share_threshold == 0.08
        assert params.base_aid_amount == 150.0
        assert params.max_energy_factor == 2.0
        assert params.income_ceiling_schedule == {}
        assert params.energy_share_schedule == {}
        assert params.aid_schedule == {}

    def test_infer_policy_type_resolves(self) -> None:
        """AC #1: infer_policy_type() resolves to 'energy_poverty_aid'."""
        params = EnergyPovertyAidParameters(rate_schedule={})
        policy_type = infer_policy_type(params)
        assert policy_type.value == "energy_poverty_aid"

    def test_invalid_income_ceiling_raises(self) -> None:
        with pytest.raises(TemplateError, match="income_ceiling must be > 0"):
            EnergyPovertyAidParameters(rate_schedule={}, income_ceiling=0.0)

    def test_negative_income_ceiling_raises(self) -> None:
        with pytest.raises(TemplateError, match="income_ceiling must be > 0"):
            EnergyPovertyAidParameters(rate_schedule={}, income_ceiling=-1000.0)

    def test_invalid_energy_share_threshold_raises(self) -> None:
        with pytest.raises(TemplateError, match="energy_share_threshold must be > 0"):
            EnergyPovertyAidParameters(
                rate_schedule={}, energy_share_threshold=0.0
            )

    def test_invalid_max_energy_factor_raises(self) -> None:
        with pytest.raises(TemplateError, match="max_energy_factor must be > 0"):
            EnergyPovertyAidParameters(rate_schedule={}, max_energy_factor=0.0)


class TestComputeEnergyPovertyAid:
    """AC #2, #3: Aid computation and year-indexed schedules."""

    def test_basic_computation_golden_values(
        self,
        small_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: Golden value test with hand-computed expected values.

        ceiling=11000, threshold=0.08, base_aid=150, max_factor=2.0:
        - HH1: income=5000, energy_exp=600
          - share = 600/5000 = 0.12 >= 0.08 -> eligible
          - income_ratio = (11000-5000)/11000 = 0.5454...
          - energy_factor = min(0.12/0.08, 2.0) = min(1.5, 2.0) = 1.5
          - aid = 150 * 0.5454... * 1.5 = 122.727... EUR
        - HH2: income=11000, at ceiling -> NOT eligible -> aid=0
        - HH3: income=8000, energy_exp=400
          - share = 400/8000 = 0.05 < 0.08 -> NOT eligible -> aid=0
        """
        result = compute_energy_poverty_aid(
            small_population,
            cheque_energie_params,
            year=2026,
            template_name="test",
        )
        aid = result.aid_amount.to_pylist()
        assert aid[0] == pytest.approx(122.727, abs=0.01)
        assert aid[1] == 0.0
        assert aid[2] == 0.0

    def test_eligibility_dual_condition(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: Both income < ceiling AND energy_share >= threshold required."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        eligible = result.is_eligible.to_pylist()

        # HH1: income=5000 < 11000, share=0.12 >= 0.08 -> eligible
        assert eligible[0] is True
        # HH2: income=8000 < 11000, share=0.10 >= 0.08 -> eligible
        assert eligible[1] is True
        # HH3: income=10000 < 11000, share=0.05 < 0.08 -> NOT eligible
        assert eligible[2] is False
        # HH4: income=11000 == ceiling -> NOT eligible (strict <)
        assert eligible[3] is False
        # HH5: income=15000 > 11000 -> NOT eligible
        assert eligible[4] is False

    def test_ineligible_households_get_zero(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: Ineligible households receive 0 aid."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        aid = result.aid_amount.to_pylist()
        eligible = result.is_eligible.to_pylist()
        for i in range(len(aid)):
            if not eligible[i]:
                assert aid[i] == 0.0

    def test_missing_energy_expenditure_column(self) -> None:
        """AC #2: Missing energy_expenditure column -> 0 expenditure -> no one eligible."""
        pop = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "income": pa.array([5000.0, 8000.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        result = compute_energy_poverty_aid(pop, params, year=2026)
        assert result.eligible_count == 0
        assert result.total_cost == 0.0
        assert all(a == 0.0 for a in result.aid_amount.to_pylist())

    def test_zero_income_edge_case(self) -> None:
        """AC #2: income=0 -> income_ratio=1.0, energy_share exceeds threshold -> eligible."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([0.0], type=pa.float64()),
                "energy_expenditure": pa.array([500.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            income_ceiling=11000.0,
            energy_share_threshold=0.08,
            base_aid_amount=150.0,
            max_energy_factor=2.0,
        )
        result = compute_energy_poverty_aid(pop, params, year=2026)
        assert result.eligible_count == 1
        # income_ratio = 1.0, energy_factor capped at max_energy_factor = 2.0
        # aid = 150 * 1.0 * 2.0 = 300.0
        assert result.aid_amount.to_pylist()[0] == pytest.approx(300.0)

    def test_zero_energy_expenditure_not_eligible(self) -> None:
        """AC #2: energy_expenditure=0 -> share=0.0 < threshold -> NOT eligible."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                "energy_expenditure": pa.array([0.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        result = compute_energy_poverty_aid(pop, params, year=2026)
        assert result.eligible_count == 0
        assert result.aid_amount.to_pylist()[0] == 0.0

    def test_zero_income_zero_energy_not_eligible(self) -> None:
        """AC #2: income=0, energy_expenditure=0 -> NOT eligible (energy takes precedence)."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([0.0], type=pa.float64()),
                "energy_expenditure": pa.array([0.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        result = compute_energy_poverty_aid(pop, params, year=2026)
        assert result.eligible_count == 0

    def test_year_indexed_ceiling_schedule(self) -> None:
        """AC #3: income_ceiling_schedule overrides income_ceiling for that year."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([12000.0], type=pa.float64()),
                "energy_expenditure": pa.array([2000.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            income_ceiling=11000.0,
            income_ceiling_schedule={2027: 15000.0},
        )
        # Year 2026: ceiling=11000 -> income 12000 >= ceiling -> NOT eligible
        r2026 = compute_energy_poverty_aid(pop, params, year=2026)
        assert r2026.eligible_count == 0

        # Year 2027: ceiling=15000 -> income 12000 < ceiling -> eligible
        r2027 = compute_energy_poverty_aid(pop, params, year=2027)
        assert r2027.eligible_count == 1

    def test_year_indexed_threshold_schedule(self) -> None:
        """AC #3: energy_share_schedule overrides energy_share_threshold."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                "energy_expenditure": pa.array([400.0], type=pa.float64()),
                # share = 400/5000 = 0.08
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            energy_share_threshold=0.10,  # 10% default -> 0.08 < 0.10 -> not eligible
            energy_share_schedule={2027: 0.05},  # override to 5% -> 0.08 >= 0.05 -> eligible
        )
        r2026 = compute_energy_poverty_aid(pop, params, year=2026)
        assert r2026.eligible_count == 0

        r2027 = compute_energy_poverty_aid(pop, params, year=2027)
        assert r2027.eligible_count == 1

    def test_year_indexed_aid_schedule(self) -> None:
        """AC #3: aid_schedule overrides base_aid_amount for that year."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                "energy_expenditure": pa.array([600.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            base_aid_amount=150.0,
            aid_schedule={2027: 300.0},
        )
        r2026 = compute_energy_poverty_aid(pop, params, year=2026)
        r2027 = compute_energy_poverty_aid(pop, params, year=2027)

        # Same household, same eligibility, but different base aid
        # 2027 aid should be 2x 2026 aid
        aid_2026 = r2026.aid_amount.to_pylist()[0]
        aid_2027 = r2027.aid_amount.to_pylist()[0]
        assert aid_2027 == pytest.approx(aid_2026 * 2.0)

    def test_total_cost_correctness(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: total_cost equals sum of all aid amounts."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        expected_total = sum(result.aid_amount.to_pylist())
        assert result.total_cost == pytest.approx(expected_total)

    def test_income_decile_assignment(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: Income deciles (1-10) assigned using assign_income_deciles."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        deciles = result.income_decile.to_pylist()
        assert all(1 <= d <= 10 for d in deciles)
        assert len(deciles) == 10

    def test_eligible_count_correctness(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: eligible_count matches number of True in is_eligible."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        expected_count = sum(1 for e in result.is_eligible.to_pylist() if e)
        assert result.eligible_count == expected_count

    def test_null_values_filled_with_zero(self) -> None:
        """AC #2: Null values in income/energy_expenditure filled with 0."""
        pop = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "income": pa.array([None, 5000.0], type=pa.float64()),
                "energy_expenditure": pa.array([500.0, None], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        result = compute_energy_poverty_aid(pop, params, year=2026)
        # HH1: income=None->0, energy_exp=500 -> eligible (income=0 case)
        # HH2: income=5000, energy_exp=None->0 -> NOT eligible (0 energy)
        assert result.is_eligible.to_pylist()[0] is True
        assert result.is_eligible.to_pylist()[1] is False

    def test_energy_expenditure_share_computed(
        self,
        small_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """AC #2: energy_expenditure_share is correctly computed."""
        result = compute_energy_poverty_aid(
            small_population, cheque_energie_params, year=2026
        )
        shares = result.energy_expenditure_share.to_pylist()
        # HH1: 600/5000 = 0.12
        assert shares[0] == pytest.approx(0.12)
        # HH3: 400/8000 = 0.05
        assert shares[2] == pytest.approx(0.05)

    def test_energy_factor_capped_at_max(self) -> None:
        """AC #2: energy_burden_factor capped at max_energy_factor."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                # Very high energy expenditure -> share = 2000/5000 = 0.40
                # factor = 0.40 / 0.08 = 5.0, capped at 2.0
                "energy_expenditure": pa.array([2000.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            max_energy_factor=2.0,
        )
        result = compute_energy_poverty_aid(pop, params, year=2026)
        # income_ratio = (11000-5000)/11000 = 0.5454...
        # energy_factor = min(0.40/0.08, 2.0) = min(5.0, 2.0) = 2.0
        # aid = 150 * 0.5454 * 2.0 = 163.636...
        expected = 150.0 * (6000.0 / 11000.0) * 2.0
        assert result.aid_amount.to_pylist()[0] == pytest.approx(expected, abs=0.01)

    def test_schedule_zero_ceiling_raises(self) -> None:
        """Schedule value of 0 for income_ceiling raises TemplateError at compute time."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                "energy_expenditure": pa.array([600.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            income_ceiling_schedule={2027: 0.0},
        )
        with pytest.raises(TemplateError, match="Effective income_ceiling"):
            compute_energy_poverty_aid(pop, params, year=2027)

    def test_schedule_zero_threshold_raises(self) -> None:
        """Schedule value of 0 for energy_share_threshold raises TemplateError."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                "energy_expenditure": pa.array([600.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(
            rate_schedule={},
            energy_share_schedule={2027: 0.0},
        )
        with pytest.raises(TemplateError, match="Effective energy_share_threshold"):
            compute_energy_poverty_aid(pop, params, year=2027)

    def test_uncastable_energy_expenditure_raises(self) -> None:
        """Non-numeric energy_expenditure column raises TemplateError."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([5000.0], type=pa.float64()),
                "energy_expenditure": pa.array(["not_a_number"], type=pa.string()),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        with pytest.raises(TemplateError, match="cannot be cast to float64"):
            compute_energy_poverty_aid(pop, params, year=2026)

    def test_boundary_income_at_ceiling_not_eligible(self) -> None:
        """AC #2: income == income_ceiling -> NOT eligible (strict < comparison)."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([11000.0], type=pa.float64()),
                "energy_expenditure": pa.array([1000.0], type=pa.float64()),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        result = compute_energy_poverty_aid(pop, params, year=2026)
        assert result.eligible_count == 0
        assert result.aid_amount.to_pylist()[0] == 0.0


class TestEnergyPovertyAidResult:
    """AC #2: EnergyPovertyAidResult frozen dataclass."""

    def test_is_frozen(
        self,
        small_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        result = compute_energy_poverty_aid(
            small_population, cheque_energie_params, year=2026
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.year = 2030  # type: ignore[misc]

    def test_fields_present(
        self,
        small_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        result = compute_energy_poverty_aid(
            small_population, cheque_energie_params, year=2026, template_name="test"
        )
        assert isinstance(result, EnergyPovertyAidResult)
        assert isinstance(result.household_ids, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.aid_amount, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.is_eligible, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.energy_expenditure_share, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.income_decile, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.total_cost, float)
        assert isinstance(result.eligible_count, int)
        assert result.year == 2026
        assert result.template_name == "test"


class TestAggregateEnergyPovertyAidByDecile:
    """AC #4: Decile aggregation."""

    def test_returns_decile_results(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        decile_results = aggregate_energy_poverty_aid_by_decile(result)
        assert isinstance(decile_results, EnergyPovertyAidDecileResults)
        assert decile_results.decile == tuple(range(1, 11))
        assert len(decile_results.household_count) == 10
        assert len(decile_results.eligible_count) == 10
        assert len(decile_results.mean_aid) == 10
        assert len(decile_results.total_aid) == 10

    def test_mean_and_total_consistency(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """mean_aid * count == total_aid for each decile."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        decile_results = aggregate_energy_poverty_aid_by_decile(result)
        for i in range(10):
            count = decile_results.household_count[i]
            if count > 0:
                expected_total = decile_results.mean_aid[i] * count
                assert decile_results.total_aid[i] == pytest.approx(expected_total)

    def test_eligible_count_per_decile(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """eligible_count tracks actual eligible households per decile."""
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        decile_results = aggregate_energy_poverty_aid_by_decile(result)
        total_eligible = sum(decile_results.eligible_count)
        assert total_eligible == result.eligible_count

    def test_empty_decile_handling(self) -> None:
        """Deciles with no households have count=0, eligible=0, mean=0, total=0."""
        pop = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "income": pa.array([5000.0, 6000.0, 7000.0], type=pa.float64()),
                "energy_expenditure": pa.array(
                    [600.0, 700.0, 800.0], type=pa.float64()
                ),
            }
        )
        params = EnergyPovertyAidParameters(rate_schedule={})
        result = compute_energy_poverty_aid(pop, params, year=2026)
        decile_results = aggregate_energy_poverty_aid_by_decile(result)

        empty_count = sum(1 for c in decile_results.household_count if c == 0)
        assert empty_count >= 7  # Most deciles empty with only 3 HHs
        for i in range(10):
            if decile_results.household_count[i] == 0:
                assert decile_results.eligible_count[i] == 0
                assert decile_results.mean_aid[i] == 0.0
                assert decile_results.total_aid[i] == 0.0

    def test_is_frozen(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        decile_results = aggregate_energy_poverty_aid_by_decile(result)
        with pytest.raises(dataclasses.FrozenInstanceError):
            decile_results.decile = (1,)  # type: ignore[misc]
