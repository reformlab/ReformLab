# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import RebateParameters


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population table with income data."""
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
        }
    )


@pytest.fixture()
def small_population() -> pa.Table:
    """Create a minimal population for simple tests."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([20000.0, 50000.0, 100000.0], type=pa.float64()),
        }
    )


@pytest.fixture()
def lump_sum_rebate_params() -> RebateParameters:
    """Rebate parameters with lump sum distribution."""
    return RebateParameters(
        rate_schedule={2026: 100.0, 2027: 110.0},
        rebate_type="lump_sum",
    )


@pytest.fixture()
def progressive_rebate_params() -> RebateParameters:
    """Rebate parameters with progressive dividend distribution."""
    return RebateParameters(
        rate_schedule={2026: 100.0, 2027: 110.0},
        rebate_type="progressive_dividend",
        income_weights={
            "decile_1": 2.0,
            "decile_2": 1.8,
            "decile_3": 1.5,
            "decile_4": 1.3,
            "decile_5": 1.1,
            "decile_6": 0.9,
            "decile_7": 0.7,
            "decile_8": 0.5,
            "decile_9": 0.3,
            "decile_10": 0.2,
        },
    )


@pytest.fixture()
def no_type_rebate_params() -> RebateParameters:
    """Rebate parameters without rebate_type specified."""
    return RebateParameters(
        rate_schedule={2026: 100.0},
    )
