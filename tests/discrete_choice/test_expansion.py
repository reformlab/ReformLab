# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for population expansion logic.

Story 14-1, AC-2: Row cloning correctness, attribute override application,
tracking column presence, N×M dimensions, determinism.
"""

from __future__ import annotations

import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
    expand_population,
)
from reformlab.discrete_choice.types import ChoiceSet
from tests.discrete_choice.conftest import MockDomain, NoOverrideDomain, SingleAlternativeDomain


class TestPopulationExpansion:
    """Tests for expand_population function."""

    def test_expansion_dimensions(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """N=3 households × M=3 alternatives = 9 expanded rows."""
        result = expand_population(sample_population, sample_choice_set, mock_domain)

        assert result.n_households == 3
        assert result.n_alternatives == 3
        assert result.alternative_ids == ("option_a", "option_b", "option_c")

        expanded_table = result.population.tables["menage"]
        assert expanded_table.num_rows == 9  # 3 × 3

    def test_tracking_columns_present(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Tracking columns _alternative_id and _original_household_index are added."""
        result = expand_population(sample_population, sample_choice_set, mock_domain)
        expanded = result.population.tables["menage"]

        assert TRACKING_COL_ALTERNATIVE_ID in expanded.column_names
        assert TRACKING_COL_ORIGINAL_INDEX in expanded.column_names

    def test_tracking_column_values(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Tracking columns have correct values for reshape mapping."""
        result = expand_population(sample_population, sample_choice_set, mock_domain)
        expanded = result.population.tables["menage"]

        alt_ids = expanded.column(TRACKING_COL_ALTERNATIVE_ID).to_pylist()
        orig_idx = expanded.column(TRACKING_COL_ORIGINAL_INDEX).to_pylist()

        # 3 households × 3 alternatives: alt_ids = [0,0,0, 1,1,1, 2,2,2]
        assert alt_ids == [0, 0, 0, 1, 1, 1, 2, 2, 2]
        # orig_idx = [0,1,2, 0,1,2, 0,1,2]
        assert orig_idx == [0, 1, 2, 0, 1, 2, 0, 1, 2]

    def test_attribute_overrides_applied(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Alternative-specific attribute overrides are applied to cloned rows."""
        result = expand_population(sample_population, sample_choice_set, mock_domain)
        expanded = result.population.tables["menage"]

        fuel_costs = expanded.column("fuel_cost").to_pylist()

        # Option A: fuel_cost=0.10 for all 3 households
        assert fuel_costs[0:3] == [0.10, 0.10, 0.10]
        # Option B: fuel_cost=0.20 for all 3 households
        assert fuel_costs[3:6] == [0.20, 0.20, 0.20]
        # Option C: fuel_cost=0.30 for all 3 households
        assert fuel_costs[6:9] == [0.30, 0.30, 0.30]

    def test_non_overridden_columns_preserved(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Columns not in attribute overrides retain original values."""
        result = expand_population(sample_population, sample_choice_set, mock_domain)
        expanded = result.population.tables["menage"]

        incomes = expanded.column("income").to_pylist()
        # Each block of 3 should have original incomes [30000, 45000, 60000]
        for block_start in range(0, 9, 3):
            assert incomes[block_start : block_start + 3] == [30000.0, 45000.0, 60000.0]

    def test_determinism(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Same inputs produce identical outputs across runs."""
        r1 = expand_population(sample_population, sample_choice_set, mock_domain)
        r2 = expand_population(sample_population, sample_choice_set, mock_domain)

        t1 = r1.population.tables["menage"]
        t2 = r2.population.tables["menage"]
        assert t1.equals(t2)

    def test_empty_population(
        self,
        empty_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Empty population (N=0) produces 0 expanded rows with tracking columns."""
        result = expand_population(empty_population, sample_choice_set, mock_domain)

        assert result.n_households == 0
        assert result.n_alternatives == 3
        expanded = result.population.tables["menage"]
        assert expanded.num_rows == 0
        assert TRACKING_COL_ALTERNATIVE_ID in expanded.column_names
        assert TRACKING_COL_ORIGINAL_INDEX in expanded.column_names

    def test_single_alternative(
        self,
        sample_population: PopulationData,
        single_alt_domain: SingleAlternativeDomain,
    ) -> None:
        """Single alternative (M=1): expansion is identity with tracking columns."""
        choice_set = ChoiceSet(alternatives=single_alt_domain.alternatives)
        result = expand_population(sample_population, choice_set, single_alt_domain)

        assert result.n_alternatives == 1
        expanded = result.population.tables["menage"]
        assert expanded.num_rows == 3  # N=3, M=1

    def test_single_household(
        self,
        single_household_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Single household (N=1) × M=3 alternatives = 3 rows."""
        result = expand_population(
            single_household_population, sample_choice_set, mock_domain
        )

        expanded = result.population.tables["menage"]
        assert expanded.num_rows == 3
        assert result.n_households == 1

    def test_no_attribute_overrides(
        self,
        sample_population: PopulationData,
        no_override_domain: NoOverrideDomain,
    ) -> None:
        """Alternatives with no overrides: cloned rows identical to original."""
        choice_set = ChoiceSet(alternatives=no_override_domain.alternatives)
        result = expand_population(sample_population, choice_set, no_override_domain)

        expanded = result.population.tables["menage"]
        assert expanded.num_rows == 6  # 3 × 2

        # fuel_cost should be unchanged from original
        fuel_costs = expanded.column("fuel_cost").to_pylist()
        assert fuel_costs[0:3] == [0.15, 0.18, 0.12]
        assert fuel_costs[3:6] == [0.15, 0.18, 0.12]

    def test_multi_entity_population(
        self,
        multi_entity_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Multiple entity tables are all expanded with tracking columns."""
        result = expand_population(
            multi_entity_population, sample_choice_set, mock_domain
        )

        # individu: 3 persons × 3 alternatives = 9
        individu = result.population.tables["individu"]
        assert individu.num_rows == 9
        assert TRACKING_COL_ALTERNATIVE_ID in individu.column_names
        assert TRACKING_COL_ORIGINAL_INDEX in individu.column_names

        # menage: 2 households × 3 alternatives = 6
        menage = result.population.tables["menage"]
        assert menage.num_rows == 6

    def test_golden_value_3x3(
        self,
        sample_population: PopulationData,
        sample_choice_set: ChoiceSet,
        mock_domain: MockDomain,
    ) -> None:
        """Hand-computed golden value test: N=3, M=3.

        Original population:
          hh_id=0, income=30000, fuel_cost=0.15
          hh_id=1, income=45000, fuel_cost=0.18
          hh_id=2, income=60000, fuel_cost=0.12

        After expansion with overrides:
          Option A (fuel_cost=0.10): rows 0-2
          Option B (fuel_cost=0.20): rows 3-5
          Option C (fuel_cost=0.30): rows 6-8
        """
        result = expand_population(sample_population, sample_choice_set, mock_domain)
        t = result.population.tables["menage"]

        assert t.num_rows == 9

        hh_ids = t.column("household_id").to_pylist()
        incomes = t.column("income").to_pylist()
        fuel_costs = t.column("fuel_cost").to_pylist()
        alt_ids = t.column(TRACKING_COL_ALTERNATIVE_ID).to_pylist()
        orig_idx = t.column(TRACKING_COL_ORIGINAL_INDEX).to_pylist()

        # Row-by-row golden values
        expected = [
            # (hh_id, income, fuel_cost, alt_id, orig_idx)
            (0, 30000.0, 0.10, 0, 0),
            (1, 45000.0, 0.10, 0, 1),
            (2, 60000.0, 0.10, 0, 2),
            (0, 30000.0, 0.20, 1, 0),
            (1, 45000.0, 0.20, 1, 1),
            (2, 60000.0, 0.20, 1, 2),
            (0, 30000.0, 0.30, 2, 0),
            (1, 45000.0, 0.30, 2, 1),
            (2, 60000.0, 0.30, 2, 2),
        ]

        for i, (exp_hh, exp_inc, exp_fc, exp_alt, exp_orig) in enumerate(expected):
            assert hh_ids[i] == exp_hh, f"Row {i}: hh_id"
            assert incomes[i] == exp_inc, f"Row {i}: income"
            assert fuel_costs[i] == pytest.approx(exp_fc), f"Row {i}: fuel_cost"
            assert alt_ids[i] == exp_alt, f"Row {i}: alt_id"
            assert orig_idx[i] == exp_orig, f"Row {i}: orig_idx"
