"""Shared fixtures for merge method tests.

Provides small PyArrow tables and default configuration objects
used across test_base.py, test_uniform.py, and test_errors.py.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.methods.base import MergeConfig


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
