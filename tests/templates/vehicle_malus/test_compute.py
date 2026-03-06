"""Tests for vehicle malus computation module.

Story 13.2 — AC #1, #2, #3, #4.
"""

from __future__ import annotations

import dataclasses

import pyarrow as pa
import pytest

from reformlab.templates.schema import PolicyParameters, infer_policy_type
from reformlab.templates.vehicle_malus.compute import (
    VehicleMalusDecileResults,
    VehicleMalusParameters,
    VehicleMalusResult,
    aggregate_vehicle_malus_by_decile,
    compute_vehicle_malus,
)


class TestVehicleMalusParameters:
    """AC #1: VehicleMalusParameters frozen dataclass subclassing PolicyParameters."""

    def test_is_frozen_dataclass(self) -> None:
        params = VehicleMalusParameters(rate_schedule={2026: 50.0})
        with pytest.raises(dataclasses.FrozenInstanceError):
            params.emission_threshold = 100.0  # type: ignore[misc]

    def test_inherits_policy_parameters(self) -> None:
        params = VehicleMalusParameters(rate_schedule={2026: 50.0})
        assert isinstance(params, PolicyParameters)

    def test_custom_fields_accessible(self) -> None:
        params = VehicleMalusParameters(
            rate_schedule={2026: 50.0},
            emission_threshold=108.0,
            malus_rate_per_gkm=75.0,
            threshold_schedule={2027: 105.0},
        )
        assert params.emission_threshold == 108.0
        assert params.malus_rate_per_gkm == 75.0
        assert params.threshold_schedule == {2027: 105.0}

    def test_default_values(self) -> None:
        params = VehicleMalusParameters(rate_schedule={})
        assert params.emission_threshold == 118.0
        assert params.malus_rate_per_gkm == 50.0
        assert params.threshold_schedule == {}

    def test_infer_policy_type_resolves(self) -> None:
        """AC #1: infer_policy_type() resolves to 'vehicle_malus'."""
        params = VehicleMalusParameters(rate_schedule={2026: 50.0})
        policy_type = infer_policy_type(params)
        assert policy_type.value == "vehicle_malus"


class TestComputeVehicleMalus:
    """AC #2, #3: Malus computation and year-indexed schedules."""

    def test_basic_computation_hand_values(
        self, small_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        """AC #2: Golden value test with hand-computed expected values.

        threshold=120, rate=50:
        - HH1: 80 gkm -> below -> malus=0
        - HH2: 120 gkm -> at threshold -> malus=0
        - HH3: 160 gkm -> (160-120)*50 = 2000 EUR
        """
        result = compute_vehicle_malus(
            small_population, flat_rate_params, year=2026, template_name="test"
        )
        malus = result.malus_amount.to_pylist()
        assert malus[0] == 0.0
        assert malus[1] == 0.0
        assert malus[2] == pytest.approx(2000.0)

    def test_total_revenue_correctness(
        self, small_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        """AC #2: total_revenue equals sum of all malus amounts."""
        result = compute_vehicle_malus(
            small_population, flat_rate_params, year=2026
        )
        assert result.total_revenue == pytest.approx(2000.0)

    def test_above_threshold_pays_malus(
        self, sample_population: pa.Table
    ) -> None:
        """AC #2: Households above threshold pay malus."""
        params = VehicleMalusParameters(
            rate_schedule={}, emission_threshold=120.0, malus_rate_per_gkm=50.0
        )
        result = compute_vehicle_malus(sample_population, params, year=2026)
        malus = result.malus_amount.to_pylist()
        emissions = result.vehicle_emissions.to_pylist()
        for i, em in enumerate(emissions):
            if em > 120.0:
                assert malus[i] > 0.0, f"HH at {em} gkm should pay malus"
            else:
                assert malus[i] == 0.0, f"HH at {em} gkm should pay no malus"

    def test_zero_emissions_no_malus(self) -> None:
        """AC #2: Households with 0 emissions pay no malus."""
        pop = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "income": pa.array([50000.0], type=pa.float64()),
                "vehicle_emissions_gkm": pa.array([0.0], type=pa.float64()),
            }
        )
        params = VehicleMalusParameters(rate_schedule={})
        result = compute_vehicle_malus(pop, params, year=2026)
        assert result.malus_amount.to_pylist() == [0.0]

    def test_missing_emissions_column_treated_as_zero(self) -> None:
        """AC #2: Missing vehicle_emissions_gkm column → 0 emissions → no malus."""
        pop = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "income": pa.array([30000.0, 60000.0], type=pa.float64()),
            }
        )
        params = VehicleMalusParameters(rate_schedule={})
        result = compute_vehicle_malus(pop, params, year=2026)
        assert result.malus_amount.to_pylist() == [0.0, 0.0]
        assert result.total_revenue == 0.0

    def test_year_indexed_rate_schedule(
        self, small_population: pa.Table
    ) -> None:
        """AC #3: rate_schedule overrides malus_rate_per_gkm for that year."""
        params = VehicleMalusParameters(
            rate_schedule={2027: 100.0},
            emission_threshold=120.0,
            malus_rate_per_gkm=50.0,
        )
        # Year 2027: rate = 100 from schedule
        result_2027 = compute_vehicle_malus(small_population, params, year=2027)
        # Year 2026: rate = 50 (default, absent from schedule)
        result_2026 = compute_vehicle_malus(small_population, params, year=2026)

        # HH3: 160 gkm, threshold 120 → excess 40
        assert result_2027.malus_amount.to_pylist()[2] == pytest.approx(4000.0)
        assert result_2026.malus_amount.to_pylist()[2] == pytest.approx(2000.0)

    def test_year_indexed_threshold_schedule(
        self, small_population: pa.Table
    ) -> None:
        """AC #3: threshold_schedule overrides emission_threshold for that year."""
        params = VehicleMalusParameters(
            rate_schedule={},
            emission_threshold=120.0,
            malus_rate_per_gkm=50.0,
            threshold_schedule={2027: 100.0},
        )
        # Year 2027: threshold = 100 from schedule
        result_2027 = compute_vehicle_malus(small_population, params, year=2027)
        # Year 2026: threshold = 120 (default, absent from schedule)
        result_2026 = compute_vehicle_malus(small_population, params, year=2026)

        malus_2027 = result_2027.malus_amount.to_pylist()
        malus_2026 = result_2026.malus_amount.to_pylist()

        # HH2: 120 gkm. In 2026 (threshold 120): 0. In 2027 (threshold 100): 20*50=1000
        assert malus_2026[1] == 0.0
        assert malus_2027[1] == pytest.approx(1000.0)

    def test_income_decile_assignment(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        """AC #2: Income deciles (1-10) assigned using assign_income_deciles."""
        result = compute_vehicle_malus(
            sample_population, flat_rate_params, year=2026
        )
        deciles = result.income_decile.to_pylist()
        assert all(1 <= d <= 10 for d in deciles)
        assert len(deciles) == 10


class TestVehicleMalusResult:
    """AC #2: VehicleMalusResult frozen dataclass."""

    def test_is_frozen(
        self, small_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        result = compute_vehicle_malus(
            small_population, flat_rate_params, year=2026
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.year = 2030  # type: ignore[misc]

    def test_fields_present(
        self, small_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        result = compute_vehicle_malus(
            small_population, flat_rate_params, year=2026, template_name="test"
        )
        assert isinstance(result, VehicleMalusResult)
        assert isinstance(result.household_ids, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.malus_amount, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.vehicle_emissions, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.income_decile, (pa.Array, pa.ChunkedArray))
        assert isinstance(result.total_revenue, float)
        assert result.year == 2026
        assert result.template_name == "test"


class TestAggregateVehicleMalusByDecile:
    """AC #4: Decile aggregation."""

    def test_returns_decile_results(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        result = compute_vehicle_malus(
            sample_population, flat_rate_params, year=2026
        )
        decile_results = aggregate_vehicle_malus_by_decile(result)
        assert isinstance(decile_results, VehicleMalusDecileResults)
        assert decile_results.decile == tuple(range(1, 11))
        assert len(decile_results.household_count) == 10
        assert len(decile_results.mean_malus) == 10
        assert len(decile_results.total_malus) == 10

    def test_mean_and_total_consistency(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        """mean_malus * count == total_malus for each decile."""
        result = compute_vehicle_malus(
            sample_population, flat_rate_params, year=2026
        )
        decile_results = aggregate_vehicle_malus_by_decile(result)
        for i in range(10):
            count = decile_results.household_count[i]
            if count > 0:
                expected_total = decile_results.mean_malus[i] * count
                assert decile_results.total_malus[i] == pytest.approx(expected_total)

    def test_empty_decile_handling(self) -> None:
        """Deciles with no households have count=0, mean=0, total=0."""
        # 3 households → most deciles will be empty
        pop = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "income": pa.array([10000.0, 50000.0, 90000.0], type=pa.float64()),
                "vehicle_emissions_gkm": pa.array(
                    [150.0, 150.0, 150.0], type=pa.float64()
                ),
            }
        )
        params = VehicleMalusParameters(
            rate_schedule={}, emission_threshold=120.0, malus_rate_per_gkm=50.0
        )
        result = compute_vehicle_malus(pop, params, year=2026)
        decile_results = aggregate_vehicle_malus_by_decile(result)

        empty_count = sum(1 for c in decile_results.household_count if c == 0)
        assert empty_count >= 7  # Most deciles empty with only 3 HHs
        for i in range(10):
            if decile_results.household_count[i] == 0:
                assert decile_results.mean_malus[i] == 0.0
                assert decile_results.total_malus[i] == 0.0

    def test_is_frozen(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        result = compute_vehicle_malus(
            sample_population, flat_rate_params, year=2026
        )
        decile_results = aggregate_vehicle_malus_by_decile(result)
        with pytest.raises(dataclasses.FrozenInstanceError):
            decile_results.decile = (1,)  # type: ignore[misc]
