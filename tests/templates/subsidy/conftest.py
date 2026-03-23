# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import SubsidyParameters


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population table with income and category data."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "income": pa.array(
                [
                    15000.0,  # decile 1 - below cap
                    25000.0,  # decile 2-3 - below cap
                    35000.0,  # decile 4 - below cap
                    45000.0,  # decile 5 - at cap
                    55000.0,  # decile 6 - above cap
                    65000.0,  # decile 7 - above cap
                    75000.0,  # decile 8 - above cap
                    90000.0,  # decile 9 - above cap
                    120000.0,  # decile 10 - above cap
                    40000.0,  # below cap
                ],
                type=pa.float64(),
            ),
            "owner_occupier": pa.array(
                [True, False, True, True, False, True, False, True, True, False],
                type=pa.bool_(),
            ),
            "low_efficiency_home": pa.array(
                [True, True, False, True, False, False, True, False, True, True],
                type=pa.bool_(),
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
def basic_subsidy_params() -> SubsidyParameters:
    """Subsidy parameters with income cap only, no category restrictions."""
    return SubsidyParameters(
        rate_schedule={2026: 5000.0, 2027: 4500.0},
        income_caps={2026: 45000.0, 2027: 42000.0},
    )


@pytest.fixture()
def category_subsidy_params() -> SubsidyParameters:
    """Subsidy parameters with income cap and category eligibility."""
    return SubsidyParameters(
        rate_schedule={2026: 5000.0, 2027: 4500.0},
        income_caps={2026: 45000.0, 2027: 42000.0},
        eligible_categories=("owner_occupier", "low_efficiency_home"),
    )


@pytest.fixture()
def no_cap_subsidy_params() -> SubsidyParameters:
    """Subsidy parameters without income cap (universal)."""
    return SubsidyParameters(
        rate_schedule={2026: 1000.0, 2027: 1000.0},
    )
