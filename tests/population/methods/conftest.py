"""Shared fixtures for merge method tests.

Provides small PyArrow tables and default configuration objects
used across test_base.py, test_uniform.py, test_ipf.py,
test_conditional.py, and test_errors.py.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.methods.base import IPFConstraint, MergeConfig


@pytest.fixture()
def income_table() -> pa.Table:
    """INSEE-style income table (5 households)."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "income": pa.array(
                [18000.0, 25000.0, 32000.0, 45000.0, 72000.0],
                type=pa.float64(),
            ),
            "region_code": pa.array(
                ["84", "11", "84", "75", "11"], type=pa.utf8()
            ),
        }
    )


@pytest.fixture()
def vehicle_table() -> pa.Table:
    """SDES-style vehicle table (8 vehicles)."""
    return pa.table(
        {
            "vehicle_type": pa.array(
                [
                    "diesel",
                    "essence",
                    "ev",
                    "diesel",
                    "hybrid",
                    "essence",
                    "ev",
                    "diesel",
                ],
                type=pa.utf8(),
            ),
            "vehicle_age": pa.array(
                [3, 7, 1, 12, 2, 9, 0, 15], type=pa.int64()
            ),
            "fuel_type": pa.array(
                [
                    "diesel",
                    "petrol",
                    "electric",
                    "diesel",
                    "hybrid",
                    "petrol",
                    "electric",
                    "diesel",
                ],
                type=pa.utf8(),
            ),
        }
    )


@pytest.fixture()
def overlapping_table() -> pa.Table:
    """Table with column name conflicting with income_table."""
    return pa.table(
        {
            "region_code": pa.array(["84", "11", "75"], type=pa.utf8()),
            "heating_type": pa.array(
                ["gas", "electric", "heat_pump"], type=pa.utf8()
            ),
        }
    )


@pytest.fixture()
def empty_table() -> pa.Table:
    """Table with schema but zero rows."""
    return pa.table(
        {
            "x": pa.array([], type=pa.int64()),
            "y": pa.array([], type=pa.float64()),
        }
    )


@pytest.fixture()
def default_config() -> MergeConfig:
    """Default merge config with seed 42."""
    return MergeConfig(seed=42)


# ====================================================================
# IPF and conditional sampling fixtures (Story 11.5)
# ====================================================================


@pytest.fixture()
def region_income_table() -> pa.Table:
    """Table with known income_bracket and region_code distributions (10 rows).

    Distribution: income_bracket: low=3, medium=4, high=3
                  region_code: 84=4, 11=3, 75=3
    """
    return pa.table(
        {
            "household_id": pa.array(
                list(range(1, 11)), type=pa.int64()
            ),
            "income_bracket": pa.array(
                [
                    "low", "low", "low",
                    "medium", "medium", "medium", "medium",
                    "high", "high", "high",
                ],
                type=pa.utf8(),
            ),
            "region_code": pa.array(
                [
                    "84", "84", "11",
                    "84", "11", "75", "84",
                    "11", "75", "75",
                ],
                type=pa.utf8(),
            ),
        }
    )


@pytest.fixture()
def energy_vehicle_table() -> pa.Table:
    """Table with income_bracket (shared), vehicle_type, energy_kwh (12 rows).

    Covers all 3 income brackets: low=4, medium=4, high=4.
    """
    return pa.table(
        {
            "income_bracket": pa.array(
                [
                    "low", "low", "low", "low",
                    "medium", "medium", "medium", "medium",
                    "high", "high", "high", "high",
                ],
                type=pa.utf8(),
            ),
            "vehicle_type": pa.array(
                [
                    "diesel", "diesel", "essence", "ev",
                    "essence", "hybrid", "ev", "diesel",
                    "ev", "ev", "hybrid", "essence",
                ],
                type=pa.utf8(),
            ),
            "energy_kwh": pa.array(
                [
                    8500.0, 9200.0, 7800.0, 3200.0,
                    7200.0, 5100.0, 3000.0, 8800.0,
                    2800.0, 3100.0, 4900.0, 6500.0,
                ],
                type=pa.float64(),
            ),
        }
    )


@pytest.fixture()
def simple_constraints() -> tuple[IPFConstraint, ...]:
    """Single IPF constraint shifting income_bracket distribution."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
    )


@pytest.fixture()
def multi_constraints() -> tuple[IPFConstraint, ...]:
    """Two IPF constraints: income_bracket + region_code."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 3.0, "11": 4.0, "75": 3.0},
        ),
    )


@pytest.fixture()
def inconsistent_constraints() -> tuple[IPFConstraint, ...]:
    """Two constraints with mismatched grand totals — reliably causes non-convergence.

    income_bracket targets sum to 10 (matches 10-row table).
    region_code targets sum to 30 (3x mismatch forces perpetual oscillation).
    With 100 iterations at tolerance=1e-6, IPF cannot converge.
    """
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 10.0, "11": 10.0, "75": 10.0},
        ),
    )
