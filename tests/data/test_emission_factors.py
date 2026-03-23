# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.data.emission_factors import (
    build_emission_factor_index,
)


@pytest.fixture()
def emission_table() -> pa.Table:
    """Small emission factor table for testing lookups."""
    return pa.table(
        {
            "category": pa.array(
                ["transport", "transport", "housing", "housing", "food"],
                type=pa.utf8(),
            ),
            "factor_value": pa.array(
                [0.21, 0.19, 0.15, 0.14, 0.08], type=pa.float64()
            ),
            "unit": pa.array(
                [
                    "kgCO2/km",
                    "kgCO2/km",
                    "kgCO2/kWh",
                    "kgCO2/kWh",
                    "kgCO2/kg",
                ],
                type=pa.utf8(),
            ),
            "year": pa.array(
                [2024, 2025, 2024, 2025, 2024], type=pa.int64()
            ),
        }
    )


class TestEmissionFactorIndex:
    """Tests for EmissionFactorIndex lookups."""

    def test_by_category(
        self, emission_table: pa.Table
    ) -> None:
        """Given factors, when filtering by category,
        then returns correct subset."""
        index = build_emission_factor_index(emission_table)
        result = index.by_category("transport")
        assert result.num_rows == 2
        assert all(
            v == "transport"
            for v in result.column("category").to_pylist()
        )

    def test_by_category_and_year(
        self, emission_table: pa.Table
    ) -> None:
        """Given factors, when filtering by category+year,
        then returns correct subset."""
        index = build_emission_factor_index(emission_table)
        result = index.by_category_and_year("transport", 2024)
        assert result.num_rows == 1
        assert result.column("factor_value").to_pylist() == [0.21]

    def test_by_category_no_match(
        self, emission_table: pa.Table
    ) -> None:
        """Given factors, when filtering by unknown category,
        then returns empty table."""
        index = build_emission_factor_index(emission_table)
        result = index.by_category("nonexistent")
        assert result.num_rows == 0

    def test_categories_sorted_unique(
        self, emission_table: pa.Table
    ) -> None:
        """Given factors, when calling categories(),
        then returns sorted unique names."""
        index = build_emission_factor_index(emission_table)
        cats = index.categories()
        assert isinstance(cats, tuple)
        assert cats == ("food", "housing", "transport")

    def test_by_category_and_year_missing_year_column(self) -> None:
        """Given table without year column, year lookup raises actionable ValueError."""
        table = pa.table(
            {
                "category": pa.array(["transport"], type=pa.utf8()),
                "factor_value": pa.array([0.21], type=pa.float64()),
                "unit": pa.array(["kgCO2/km"], type=pa.utf8()),
            }
        )
        index = build_emission_factor_index(table)
        with pytest.raises(ValueError, match="missing required 'year' column"):
            index.by_category_and_year("transport", 2024)

    def test_categories_ignores_null_values(self) -> None:
        """Given nullable categories, categories() ignores nulls and sorts names."""
        table = pa.table(
            {
                "category": pa.array(
                    ["transport", None, "housing"], type=pa.utf8()
                ),
                "factor_value": pa.array([0.21, 0.18, 0.15], type=pa.float64()),
                "unit": pa.array(
                    ["kgCO2/km", "kgCO2/km", "kgCO2/kWh"], type=pa.utf8()
                ),
                "year": pa.array([2024, 2024, 2024], type=pa.int64()),
            }
        )
        index = build_emission_factor_index(table)
        assert index.categories() == ("housing", "transport")

    def test_frozen(
        self, emission_table: pa.Table
    ) -> None:
        """Given an index, when mutating,
        then raises FrozenInstanceError."""
        index = build_emission_factor_index(emission_table)
        with pytest.raises(AttributeError):
            index._table = emission_table  # type: ignore[misc]
