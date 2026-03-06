"""Tests for discrete choice core types.

Story 14-1, AC-2, AC-4: Frozen dataclass validation, CostMatrix construction,
Alternative immutability, ChoiceSet validation.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.discrete_choice.errors import ExpansionError
from reformlab.discrete_choice.types import (
    Alternative,
    ChoiceSet,
    CostMatrix,
    ExpansionResult,
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
            population=None,  # type: ignore[arg-type]
            n_households=3,
            n_alternatives=3,
            alternative_ids=("a", "b", "c"),
        )
        assert er.n_households == 3
        assert er.n_alternatives == 3
        assert er.alternative_ids == ("a", "b", "c")

    def test_expansion_result_immutable(self) -> None:
        er = ExpansionResult(
            population=None,  # type: ignore[arg-type]
            n_households=1,
            n_alternatives=1,
            alternative_ids=("a",),
        )
        with pytest.raises(AttributeError):
            er.n_households = 5  # type: ignore[misc]
