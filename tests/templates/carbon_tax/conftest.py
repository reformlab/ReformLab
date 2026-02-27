from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import CarbonTaxParameters


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population table with energy consumption data."""
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
                    80000.0,  # decile 8
                ],
                type=pa.float64(),
            ),
            "energy_transport_fuel": pa.array(
                [
                    800.0,
                    1000.0,
                    1200.0,
                    1400.0,
                    1600.0,
                    1800.0,
                    2000.0,
                    2200.0,
                    2500.0,
                    2100.0,
                ],
                type=pa.float64(),
            ),
            "energy_heating_fuel": pa.array(
                [
                    400.0,
                    500.0,
                    600.0,
                    700.0,
                    800.0,
                    900.0,
                    1000.0,
                    1100.0,
                    1200.0,
                    1050.0,
                ],
                type=pa.float64(),
            ),
            "energy_natural_gas": pa.array(
                [
                    600.0,
                    750.0,
                    900.0,
                    1050.0,
                    1200.0,
                    1350.0,
                    1500.0,
                    1650.0,
                    1800.0,
                    1575.0,
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
            "energy_transport_fuel": pa.array(
                [1000.0, 1500.0, 2000.0], type=pa.float64()
            ),
            "energy_heating_fuel": pa.array([500.0, 750.0, 1000.0], type=pa.float64()),
            "energy_natural_gas": pa.array([800.0, 1200.0, 1600.0], type=pa.float64()),
        }
    )


@pytest.fixture()
def emission_factor_table() -> pa.Table:
    """Create emission factor table for carbon tax computation."""
    return pa.table(
        {
            "category": pa.array(
                [
                    "transport_fuel",
                    "transport_fuel",
                    "heating_fuel",
                    "heating_fuel",
                    "natural_gas",
                    "natural_gas",
                ],
                type=pa.utf8(),
            ),
            "factor_value": pa.array(
                [
                    2.31,  # kg CO2 per liter of gasoline (2026)
                    2.31,  # kg CO2 per liter of gasoline (2027)
                    2.68,  # kg CO2 per liter of heating oil (2026)
                    2.68,  # kg CO2 per liter of heating oil (2027)
                    2.0,  # kg CO2 per m3 of natural gas (2026)
                    2.0,  # kg CO2 per m3 of natural gas (2027)
                ],
                type=pa.float64(),
            ),
            "unit": pa.array(
                [
                    "kg_co2_per_liter",
                    "kg_co2_per_liter",
                    "kg_co2_per_liter",
                    "kg_co2_per_liter",
                    "kg_co2_per_m3",
                    "kg_co2_per_m3",
                ],
                type=pa.utf8(),
            ),
            "year": pa.array([2026, 2027, 2026, 2027, 2026, 2027], type=pa.int64()),
        }
    )


@pytest.fixture()
def flat_rate_params() -> CarbonTaxParameters:
    """Carbon tax parameters with flat rate, no redistribution."""
    return CarbonTaxParameters(
        rate_schedule={2026: 44.60, 2027: 50.00},
        covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        exemptions=(),
    )


@pytest.fixture()
def flat_rate_with_exemption_params() -> CarbonTaxParameters:
    """Carbon tax parameters with flat rate and partial exemption."""
    return CarbonTaxParameters(
        rate_schedule={2026: 44.60, 2027: 50.00},
        covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        exemptions=({"category": "heating_fuel", "rate_reduction": 0.5},),
    )


@pytest.fixture()
def lump_sum_redistribution_params() -> CarbonTaxParameters:
    """Carbon tax parameters with lump sum redistribution."""
    return CarbonTaxParameters(
        rate_schedule={2026: 44.60, 2027: 50.00},
        covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        exemptions=(),
        redistribution_type="lump_sum",
    )


@pytest.fixture()
def progressive_redistribution_params() -> CarbonTaxParameters:
    """Carbon tax parameters with progressive redistribution."""
    return CarbonTaxParameters(
        rate_schedule={2026: 44.60, 2027: 50.00},
        covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        exemptions=(),
        redistribution_type="progressive_dividend",
        income_weights={
            "decile_1": 1.5,
            "decile_2": 1.3,
            "decile_3": 1.2,
            "decile_4": 1.1,
            "decile_5": 1.0,
            "decile_6": 0.9,
            "decile_7": 0.8,
            "decile_8": 0.7,
            "decile_9": 0.5,
            "decile_10": 0.2,
        },
    )
