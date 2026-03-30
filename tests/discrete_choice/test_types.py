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


# ============================================================================
# Story 21.7: Generalized TasteParameters with ASCs and betas
# ============================================================================


class TestTasteParametersGeneralized:
    """Tests for generalized TasteParameters with ASCs and named betas (Story 21.7 / AC1)."""

    def test_from_beta_cost_factory_creates_generalized_structure(self) -> None:
        """from_beta_cost(-0.01) creates instance with asc={}, betas={'cost': -0.01}."""
        tp = TasteParameters.from_beta_cost(-0.01)
        assert tp.beta_cost == -0.01  # legacy field retained
        assert tp.asc == {}
        assert tp.betas == {"cost": -0.01}
        assert tp.calibrate == frozenset(["cost"])
        assert tp.fixed == frozenset()

    def test_from_beta_cost_creates_legacy_mode_instance(self) -> None:
        """from_beta_cost() creates instance with is_legacy_mode=True."""
        tp = TasteParameters.from_beta_cost(-0.01)
        assert tp.is_legacy_mode is True

    def test_is_legacy_mode_true_for_empty_asc_and_single_cost_beta(self) -> None:
        """is_legacy_mode=True when asc empty and betas has only 'cost' key."""
        tp = TasteParameters(beta_cost=-0.5, asc={}, betas={"cost": -0.5})
        assert tp.is_legacy_mode is True

    def test_is_legacy_mode_false_for_non_empty_asc(self) -> None:
        """is_legacy_mode=False when asc is non-empty with calibrate/fixed specified."""
        tp = TasteParameters(
            beta_cost=0.0,
            asc={"ev": 0.0, "petrol": -0.5},
            betas={"cost": -0.01},
            calibrate=frozenset(["ev"]),
            fixed=frozenset(["petrol", "cost"]),
        )
        assert tp.is_legacy_mode is False

    def test_is_legacy_mode_false_for_multiple_betas(self) -> None:
        """is_legacy_mode=False when betas has more than just 'cost' key."""
        tp = TasteParameters(beta_cost=0.0, asc={}, betas={"cost": -0.01, "time": -0.05})
        assert tp.is_legacy_mode is False

    def test_generalized_construction_with_ascs_only(self) -> None:
        """Construction with ASCs only (all betas fixed)."""
        tp = TasteParameters(
            beta_cost=0.0,  # unused in generalized mode
            asc={"ev": 0.0, "petrol": -0.5, "diesel": -0.6},
            betas={"cost": -0.01},
            calibrate=frozenset(["ev", "petrol"]),
            fixed=frozenset(["cost", "diesel"]),
            reference_alternative="ev",
        )
        assert tp.asc == {"ev": 0.0, "petrol": -0.5, "diesel": -0.6}
        assert tp.betas == {"cost": -0.01}
        assert tp.calibrate == frozenset(["ev", "petrol"])
        assert tp.fixed == frozenset(["cost", "diesel"])
        assert tp.reference_alternative == "ev"
        assert tp.is_legacy_mode is False

    def test_generalized_construction_with_betas_only(self) -> None:
        """Construction with multiple betas (all ASCs fixed)."""
        tp = TasteParameters(
            beta_cost=0.0,
            asc={"ev": 0.0, "petrol": -0.5},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions", "ev", "petrol"]),
            reference_alternative="ev",
        )
        assert tp.asc == {"ev": 0.0, "petrol": -0.5}
        assert tp.betas == {"cost": -0.01, "emissions": -0.05}
        assert "cost" in tp.calibrate
        assert "emissions" in tp.fixed

    def test_generalized_construction_with_ascs_and_betas(self) -> None:
        """Full generalized mode with ASCs + multiple betas."""
        tp = TasteParameters(
            beta_cost=0.0,
            asc={"ev": 0.0, "petrol": -0.5, "hybrid": -0.3},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["ev", "cost"]),
            fixed=frozenset(["petrol", "hybrid", "emissions"]),
            reference_alternative="ev",
            literature_sources={"emissions": "Dargay & Gately 1999"},
        )
        assert len(tp.asc) == 3
        assert len(tp.betas) == 2
        assert len(tp.calibrate) == 2
        assert len(tp.fixed) == 3
        assert tp.literature_sources == {"emissions": "Dargay & Gately 1999"}

    def test_calibrate_and_fixed_must_be_disjoint(self) -> None:
        """Overlapping calibrate and fixed sets raise DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="disjoint"):
            TasteParameters(
                beta_cost=0.0,
                asc={"ev": 0.0},
                betas={"cost": -0.01},
                calibrate=frozenset(["cost"]),
                fixed=frozenset(["cost"]),  # overlap!
            )

    def test_calibrate_must_be_subset_of_asc_or_betas_keys(self) -> None:
        """calibrate containing unknown parameter names raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="Invalid in calibrate"):
            TasteParameters(
                beta_cost=0.0,
                asc={"ev": 0.0},
                betas={"cost": -0.01},
                calibrate=frozenset(["unknown_param"]),
            )

    def test_fixed_must_be_subset_of_asc_or_betas_keys(self) -> None:
        """fixed containing unknown parameter names raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="Invalid in fixed"):
            TasteParameters(
                beta_cost=0.0,
                asc={"ev": 0.0},
                betas={"cost": -0.01},
                fixed=frozenset(["unknown_param"]),
            )

    def test_at_least_one_parameter_must_be_calibrated_or_fixed(self) -> None:
        """Empty calibrate and fixed with non-empty asc and single cost beta raises error."""
        # When using single "cost" beta with non-empty asc, must specify calibrate or fixed
        # to avoid ambiguous legacy/generalized mode.
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="is_legacy_mode.*asc is non-empty"):
            TasteParameters(
                beta_cost=0.0,
                asc={"ev": 0.0},
                betas={"cost": -0.01},
                calibrate=frozenset(),
                fixed=frozenset(),
            )

    def test_reference_alternative_must_exist_in_asc(self) -> None:
        """reference_alternative not in asc keys raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="not found in asc"):
            TasteParameters(
                beta_cost=0.0,
                asc={"ev": 0.0, "petrol": -0.5},
                betas={"cost": -0.01},
                calibrate=frozenset(["ev"]),
                fixed=frozenset(),
                reference_alternative="diesel",  # not in asc
            )

    def test_reference_alternative_asc_must_be_zero(self) -> None:
        """reference_alternative with ASC != 0.0 raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="must have ASC=0\\.0"):
            TasteParameters(
                beta_cost=0.0,
                asc={"ev": 0.5, "petrol": -0.5},  # ev ASC is 0.5, not 0.0
                betas={"cost": -0.01},
                calibrate=frozenset(["ev"]),  # Add calibrate to avoid special case
                fixed=frozenset(),
                reference_alternative="ev",
            )

    def test_legacy_mode_requires_empty_asc(self) -> None:
        """is_legacy_mode=True with non-empty asc raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="is_legacy_mode.*asc is non-empty"):
            TasteParameters(
                beta_cost=-0.01,
                asc={"ev": 0.0},  # non-empty asc
                betas={"cost": -0.01},
            )

    def test_legacy_mode_requires_none_reference_alternative(self) -> None:
        """is_legacy_mode=True with reference_alternative raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        with pytest.raises(DiscreteChoiceError, match="is_legacy_mode.*reference_alternative"):
            TasteParameters(
                beta_cost=-0.01,
                asc={},
                betas={"cost": -0.01},
                reference_alternative="ev",
            )

    def test_backward_compatibility_legacy_construction_still_works(self) -> None:
        """Legacy single-beta construction still works without new fields."""
        tp = TasteParameters(beta_cost=-0.01)
        assert tp.beta_cost == -0.01
        assert tp.asc == {}
        assert tp.betas == {}
        # Empty betas with empty asc is treated as legacy mode for backward compatibility
        assert tp.is_legacy_mode is True


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
