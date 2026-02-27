from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import FeebateParameters


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population with vehicle emissions data."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "income": pa.array(
                [
                    15000.0,  # decile 1
                    25000.0,  # decile 2-3
                    35000.0,  # decile 4
                    45000.0,  # decile 5
                    55000.0,  # decile 6
                    65000.0,  # decile 7
                    75000.0,  # decile 8
                    90000.0,  # decile 9
                    120000.0,  # decile 10
                    40000.0,  # around decile 4
                ],
                type=pa.float64(),
            ),
            "vehicle_emissions_gkm": pa.array(
                [
                    80.0,  # Below pivot - gets rebate
                    100.0,  # Below pivot - gets rebate
                    120.0,  # At pivot - no fee/rebate
                    140.0,  # Above pivot - pays fee
                    160.0,  # Above pivot - pays fee
                    90.0,  # Below pivot - gets rebate
                    130.0,  # Above pivot - pays fee
                    150.0,  # Above pivot - pays fee
                    200.0,  # Well above pivot - pays large fee
                    110.0,  # Below pivot - gets small rebate
                ],
                type=pa.float64(),
            ),
        }
    )


@pytest.fixture()
def small_population() -> pa.Table:
    """Create a minimal population for simple tests."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([20000.0, 50000.0, 100000.0], type=pa.float64()),
            "vehicle_emissions_gkm": pa.array([80.0, 120.0, 160.0], type=pa.float64()),
        }
    )


@pytest.fixture()
def symmetric_feebate_params() -> FeebateParameters:
    """Feebate parameters with symmetric fee and rebate rates."""
    return FeebateParameters(
        rate_schedule={2026: 0.0},  # Base class required field
        pivot_point=120.0,  # g CO2/km
        fee_rate=50.0,  # EUR per g/km above pivot
        rebate_rate=50.0,  # EUR per g/km below pivot
        covered_categories=("passenger_vehicle",),
    )


@pytest.fixture()
def asymmetric_feebate_params() -> FeebateParameters:
    """Feebate parameters with different fee and rebate rates."""
    return FeebateParameters(
        rate_schedule={2026: 0.0},
        pivot_point=120.0,
        fee_rate=75.0,  # Higher fee rate
        rebate_rate=25.0,  # Lower rebate rate
    )


@pytest.fixture()
def zero_rate_feebate_params() -> FeebateParameters:
    """Feebate parameters with zero rates (no impact)."""
    return FeebateParameters(
        rate_schedule={2026: 0.0},
        pivot_point=120.0,
        fee_rate=0.0,
        rebate_rate=0.0,
    )
