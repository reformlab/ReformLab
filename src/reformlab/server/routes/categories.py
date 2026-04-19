# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Categories API routes — Story 25.1."""

from __future__ import annotations

from fastapi import APIRouter

from reformlab.server.models import CategoryItem

router = APIRouter()

# Story 25.1 / Task 1.2: Category definitions constant
# From UX spec Revision 4.1
_CATEGORY_DEFINITIONS: list[CategoryItem] = [
    CategoryItem(
        id="carbon_emissions",
        label="Carbon Emissions",
        columns=["emissions_co2"],
        compatible_types=["tax", "subsidy", "transfer"],
        formula_explanation="emissions_co2 × tax_rate",
        description="Applies to household CO₂ emissions (tonnes/year)",
    ),
    CategoryItem(
        id="energy_consumption",
        label="Energy Consumption",
        columns=["energy_kwh", "energy_cost"],
        compatible_types=["tax", "subsidy", "transfer"],
        formula_explanation="energy_kwh × rate_per_kwh",
        description="Applies to household energy consumption",
    ),
    CategoryItem(
        id="vehicle_emissions",
        label="Vehicle Emissions",
        columns=["vehicle_co2", "vehicle_type"],
        compatible_types=["tax", "subsidy"],
        formula_explanation="vehicle_co2 × malus_rate",
        description="Applies to vehicle emission levels",
    ),
    CategoryItem(
        id="housing",
        label="Housing",
        columns=["housing_type", "housing_efficiency"],
        compatible_types=["subsidy", "transfer"],
        formula_explanation="renovation_cost × subsidy_rate",
        description="Applies to housing characteristics and efficiency",
    ),
    CategoryItem(
        id="income",
        label="Income",
        columns=["disposable_income", "decile"],
        compatible_types=["transfer"],
        formula_explanation="max(0, ceiling − disposable_income)",
        description="Applies to household income for means-tested transfers",
    ),
]


# Story 25.1 / AC-1, Task 1.3: GET /api/categories endpoint
@router.get("", response_model=list[CategoryItem])
async def list_categories() -> list[CategoryItem]:
    """List all policy categories with metadata."""
    return _CATEGORY_DEFINITIONS
