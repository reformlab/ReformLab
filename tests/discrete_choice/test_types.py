# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for discrete choice core types.

Story 14-1, AC-2, AC-4: Frozen dataclass validation, CostMatrix construction,
Alternative immutability, ChoiceSet validation.
Story 14-2, AC-6: TasteParameters and ChoiceResult frozen dataclasses.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.errors import ExpansionError
from reformlab.discrete_choice.types import (
    Alternative,
    ChoiceResult,
    ChoiceSet,
    CostMatrix,
    ExpansionResult,
    TasteParameters,
)

_DUMMY_POPULATION = PopulationData(
    tables={"menage": pa.table({"id": pa.array([0], type=pa.int64())})},
)


class TestAlternative:
    """Tests for Alternative frozen dataclass."""

    def test_alternative_creation(self) -> None:
        alt = Alternative(id="ev", name="Electric Vehicle", attributes={"fuel_cost": 0.05})
        assert alt.id == "ev"
        assert alt.name == "Electric Vehicle"
        assert alt.attributes == {"fuel_cost": 0.05}

    def test_alternative_immutable(self) -> None:
        alt = Alternative(id="ev", name="EV", attributes={})
        with pytest.raises(AttributeError):
            alt.id = "gas"  # type: ignore[misc]

    def test_alternative_default_attributes(self) -> None:
        alt = Alternative(id="x", name="X")
        assert alt.attributes == {}

    def test_alternative_equality(self) -> None:
        a1 = Alternative(id="ev", name="EV", attributes={"x": 1})
        a2 = Alternative(id="ev", name="EV", attributes={"x": 1})
        assert a1 == a2


class TestChoiceSet:
    """Tests for ChoiceSet frozen dataclass with validation."""

    def test_choice_set_creation(self, sample_choice_set: ChoiceSet) -> None:
        assert sample_choice_set.size == 3
        assert sample_choice_set.alternative_ids == ("option_a", "option_b", "option_c")

    def test_choice_set_single_alternative(self) -> None:
        cs = ChoiceSet(alternatives=(Alternative(id="only", name="Only"),))
        assert cs.size == 1

    def test_choice_set_empty_raises(self) -> None:
        with pytest.raises(ExpansionError, match="at least 1 alternative"):
            ChoiceSet(alternatives=())

    def test_choice_set_duplicate_ids_raises(self) -> None:
        with pytest.raises(ExpansionError, match="Duplicate alternative IDs"):
            ChoiceSet(
                alternatives=(
                    Alternative(id="a", name="A"),
                    Alternative(id="a", name="A2"),
                )
            )

    def test_choice_set_immutable(self, sample_choice_set: ChoiceSet) -> None:
        with pytest.raises(AttributeError):
            sample_choice_set.alternatives = ()  # type: ignore[misc]


class TestCostMatrix:
    """Tests for CostMatrix frozen dataclass."""

    def test_cost_matrix_creation(self) -> None:
        table = pa.table({
            "option_a": pa.array([100.0, 200.0]),
            "option_b": pa.array([150.0, 250.0]),
        })
        cm = CostMatrix(table=table, alternative_ids=("option_a", "option_b"))
        assert cm.n_households == 2
        assert cm.n_alternatives == 2

    def test_cost_matrix_empty(self) -> None:
        table = pa.table({
            "option_a": pa.array([], type=pa.float64()),
            "option_b": pa.array([], type=pa.float64()),
        })
        cm = CostMatrix(table=table, alternative_ids=("option_a", "option_b"))
        assert cm.n_households == 0
        assert cm.n_alternatives == 2

    def test_cost_matrix_immutable(self) -> None:
        table = pa.table({"a": pa.array([1.0])})
        cm = CostMatrix(table=table, alternative_ids=("a",))
        with pytest.raises(AttributeError):
            cm.table = pa.table({"a": pa.array([2.0])})  # type: ignore[misc]


class TestExpansionResult:
    """Tests for ExpansionResult frozen dataclass."""

    def test_expansion_result_creation(self) -> None:
        er = ExpansionResult(
            population=_DUMMY_POPULATION,
            n_households=3,
            n_alternatives=3,
            alternative_ids=("a", "b", "c"),
        )
        assert er.n_households == 3
        assert er.n_alternatives == 3
        assert er.alternative_ids == ("a", "b", "c")

    def test_expansion_result_immutable(self) -> None:
        er = ExpansionResult(
            population=_DUMMY_POPULATION,
            n_households=1,
            n_alternatives=1,
            alternative_ids=("a",),
        )
        with pytest.raises(AttributeError):
            er.n_households = 5  # type: ignore[misc]


# ============================================================================
# Story 14-2: TasteParameters and ChoiceResult
# ============================================================================


class TestTasteParameters:
    """Tests for TasteParameters frozen dataclass (AC-6)."""

    def test_creation(self) -> None:
        tp = TasteParameters(beta_cost=-0.5)
        assert tp.beta_cost == -0.5

    def test_immutable(self) -> None:
        tp = TasteParameters(beta_cost=-1.0)
        with pytest.raises(AttributeError):
            tp.beta_cost = 0.0  # type: ignore[misc]

    def test_zero_beta(self) -> None:
        tp = TasteParameters(beta_cost=0.0)
        assert tp.beta_cost == 0.0

    def test_positive_beta(self) -> None:
        tp = TasteParameters(beta_cost=1.5)
        assert tp.beta_cost == 1.5


class TestChoiceResult:
    """Tests for ChoiceResult frozen dataclass (AC-6, AC-5)."""

    def _make_valid_result(
        self,
        n: int = 3,
        alt_ids: tuple[str, ...] = ("a", "b"),
        seed: int | None = 42,
    ) -> ChoiceResult:
        """Helper to build a valid ChoiceResult for testing."""
        # Uniform probabilities
        prob = 1.0 / len(alt_ids)
        prob_table = pa.table({
            aid: pa.array([prob] * n) for aid in alt_ids
        })
        util_table = pa.table({
            aid: pa.array([0.0] * n) for aid in alt_ids
        })
        chosen = pa.array([alt_ids[0]] * n)
        return ChoiceResult(
            chosen=chosen,
            probabilities=prob_table,
            utilities=util_table,
            alternative_ids=alt_ids,
            seed=seed,
        )

    def test_creation(self) -> None:
        result = self._make_valid_result()
        assert len(result.chosen) == 3
        assert result.seed == 42
        assert result.alternative_ids == ("a", "b")

    def test_immutable(self) -> None:
        result = self._make_valid_result()
        with pytest.raises(AttributeError):
            result.seed = 99  # type: ignore[misc]

    def test_seed_none(self) -> None:
        result = self._make_valid_result(seed=None)
        assert result.seed is None

    def test_probability_sum_validation_passes(self) -> None:
        """Valid probabilities sum to 1.0 within tolerance."""
        result = self._make_valid_result()
        assert result.probabilities.num_rows == 3

    def test_probability_sum_validation_fails(self) -> None:
        """Invalid probability sums raise LogitError."""
        from reformlab.discrete_choice.errors import LogitError

        bad_prob_table = pa.table({
            "a": pa.array([0.3, 0.5]),
            "b": pa.array([0.3, 0.5]),
        })
        util_table = pa.table({
            "a": pa.array([0.0, 0.0]),
            "b": pa.array([0.0, 0.0]),
        })
        chosen = pa.array(["a", "b"])
        with pytest.raises(LogitError, match="probability"):
            ChoiceResult(
                chosen=chosen,
                probabilities=bad_prob_table,
                utilities=util_table,
                alternative_ids=("a", "b"),
                seed=42,
            )

    def test_column_mismatch_raises(self) -> None:
        """Column names not matching alternative_ids raises LogitError."""
        from reformlab.discrete_choice.errors import LogitError

        prob_table = pa.table({
            "x": pa.array([0.5]),
            "y": pa.array([0.5]),
        })
        util_table = pa.table({
            "x": pa.array([0.0]),
            "y": pa.array([0.0]),
        })
        chosen = pa.array(["a"])
        with pytest.raises(LogitError, match="column"):
            ChoiceResult(
                chosen=chosen,
                probabilities=prob_table,
                utilities=util_table,
                alternative_ids=("a", "b"),
                seed=42,
            )

    def test_wrong_chosen_length_raises(self) -> None:
        """Chosen array length != N raises LogitError."""
        from reformlab.discrete_choice.errors import LogitError

        prob_table = pa.table({
            "a": pa.array([0.5, 0.5]),
            "b": pa.array([0.5, 0.5]),
        })
        util_table = pa.table({
            "a": pa.array([0.0, 0.0]),
            "b": pa.array([0.0, 0.0]),
        })
        # chosen has 3 elements but prob table has 2 rows
        chosen = pa.array(["a", "b", "a"])
        with pytest.raises(LogitError, match="chosen"):
            ChoiceResult(
                chosen=chosen,
                probabilities=prob_table,
                utilities=util_table,
                alternative_ids=("a", "b"),
                seed=42,
            )
