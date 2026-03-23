# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population with 10 households and varying income/energy."""
    return pa.table(
        {
            "household_id": pa.array(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()
            ),
            "income": pa.array(
                [
                    5000.0,    # Very low income, eligible
                    8000.0,    # Low income, eligible
                    10000.0,   # Below ceiling, eligible
                    11000.0,   # At ceiling, NOT eligible (strict <)
                    15000.0,   # Above ceiling
                    3000.0,    # Very low income
                    20000.0,   # Above ceiling
                    7000.0,    # Low income
                    50000.0,   # High income
                    9000.0,    # Below ceiling
                ],
                type=pa.float64(),
            ),
            "energy_expenditure": pa.array(
                [
                    600.0,    # share = 0.12 (>= 0.08)
                    800.0,    # share = 0.10 (>= 0.08)
                    500.0,    # share = 0.05 (< 0.08, NOT eligible)
                    1000.0,   # share = 0.09 (irrelevant, at ceiling)
                    1500.0,   # share = 0.10 (irrelevant, above ceiling)
                    400.0,    # share = 0.13 (>= 0.08)
                    2000.0,   # share = 0.10 (irrelevant, above ceiling)
                    700.0,    # share = 0.10 (>= 0.08)
                    5000.0,   # share = 0.10 (irrelevant, above ceiling)
                    720.0,    # share = 0.08 (exactly at threshold, eligible)
                ],
                type=pa.float64(),
            ),
        }
    )


@pytest.fixture()
def small_population() -> pa.Table:
    """Create a minimal population for hand-computed golden value tests.

    3 households:
    - HH1: income=5000, energy_exp=600 -> eligible, golden value = 122.73 EUR
    - HH2: income=11000, energy_exp=1000 -> at ceiling, NOT eligible
    - HH3: income=8000, energy_exp=400 -> share=0.05 < 0.08, NOT eligible
    """
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([5000.0, 11000.0, 8000.0], type=pa.float64()),
            "energy_expenditure": pa.array(
                [600.0, 1000.0, 400.0], type=pa.float64()
            ),
        }
    )


@pytest.fixture()
def cheque_energie_params() -> EnergyPovertyAidParameters:
    """Cheque-energie-style parameters: ceiling 11,000, threshold 8%, base 150."""
    return EnergyPovertyAidParameters(
        rate_schedule={},
        income_ceiling=11000.0,
        energy_share_threshold=0.08,
        base_aid_amount=150.0,
        max_energy_factor=2.0,
    )


@pytest.fixture()
def generous_params() -> EnergyPovertyAidParameters:
    """Generous parameters: ceiling 15,000, threshold 10%, base 300."""
    return EnergyPovertyAidParameters(
        rate_schedule={},
        income_ceiling=15000.0,
        energy_share_threshold=0.10,
        base_aid_amount=300.0,
        max_energy_factor=2.0,
    )
