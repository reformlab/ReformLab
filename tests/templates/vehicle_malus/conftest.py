from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population with 10 households and varying emissions."""
    return pa.table(
        {
            "household_id": pa.array(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()
            ),
            "income": pa.array(
                [
                    15000.0,
                    25000.0,
                    35000.0,
                    45000.0,
                    55000.0,
                    65000.0,
                    75000.0,
                    90000.0,
                    120000.0,
                    40000.0,
                ],
                type=pa.float64(),
            ),
            "vehicle_emissions_gkm": pa.array(
                [
                    80.0,   # Below threshold
                    100.0,  # Below threshold
                    120.0,  # At default threshold (118) -> above
                    140.0,  # Above threshold
                    160.0,  # Above threshold
                    90.0,   # Below threshold
                    130.0,  # Above threshold
                    150.0,  # Above threshold
                    200.0,  # Well above threshold
                    110.0,  # Below threshold
                ],
                type=pa.float64(),
            ),
        }
    )


@pytest.fixture()
def small_population() -> pa.Table:
    """Create a minimal population for simple hand-computed tests."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([20000.0, 50000.0, 100000.0], type=pa.float64()),
            "vehicle_emissions_gkm": pa.array(
                [80.0, 120.0, 160.0], type=pa.float64()
            ),
        }
    )


@pytest.fixture()
def flat_rate_params() -> VehicleMalusParameters:
    """Flat-rate vehicle malus with threshold 120, rate 50."""
    return VehicleMalusParameters(
        rate_schedule={2026: 50.0},
        emission_threshold=120.0,
        malus_rate_per_gkm=50.0,
        covered_categories=("passenger_vehicle",),
    )


@pytest.fixture()
def french_style_params() -> VehicleMalusParameters:
    """French-style progressive vehicle malus with year-indexed schedules."""
    return VehicleMalusParameters(
        rate_schedule={2026: 50.0, 2027: 55.0, 2028: 60.0},
        emission_threshold=108.0,
        malus_rate_per_gkm=50.0,
        threshold_schedule={2026: 108.0, 2027: 105.0, 2028: 102.0},
        covered_categories=("passenger_vehicle",),
    )
