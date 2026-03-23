# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for shared domain utility functions.

Tests infer_pa_type, apply_choices_to_population, and create_vintage_entries
extracted from vehicle.py into domain_utils.py.

Story 14-3/14-4: Shared utilities for decision domain implementations.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.domain_utils import (
    apply_choices_to_population,
    create_vintage_entries,
    infer_pa_type,
)
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.types import Alternative, ChoiceResult

# ============================================================================
# TestInferPaType
# ============================================================================


class TestInferPaType:
    """Tests for infer_pa_type type inference function."""

    def test_str_returns_utf8(self) -> None:
        assert infer_pa_type("hello") == pa.utf8()

    def test_int_returns_int64(self) -> None:
        assert infer_pa_type(42) == pa.int64()

    def test_float_returns_float64(self) -> None:
        assert infer_pa_type(3.14) == pa.float64()

    def test_bool_raises(self) -> None:
        with pytest.raises(DiscreteChoiceError, match="Unsupported attribute type"):
            infer_pa_type(True)

    def test_false_raises(self) -> None:
        with pytest.raises(DiscreteChoiceError, match="bool"):
            infer_pa_type(False)

    def test_list_raises(self) -> None:
        with pytest.raises(DiscreteChoiceError, match="Unsupported attribute type"):
            infer_pa_type([1, 2, 3])

    def test_none_raises(self) -> None:
        with pytest.raises(DiscreteChoiceError, match="Unsupported attribute type"):
            infer_pa_type(None)

    def test_dict_raises(self) -> None:
        with pytest.raises(DiscreteChoiceError, match="Unsupported attribute type"):
            infer_pa_type({"key": "value"})

    def test_zero_int_returns_int64(self) -> None:
        assert infer_pa_type(0) == pa.int64()

    def test_zero_float_returns_float64(self) -> None:
        assert infer_pa_type(0.0) == pa.float64()

    def test_empty_str_returns_utf8(self) -> None:
        assert infer_pa_type("") == pa.utf8()


# ============================================================================
# TestApplyChoicesToPopulation
# ============================================================================


class TestApplyChoicesToPopulationUtils:
    """Tests for apply_choices_to_population from domain_utils."""

    @staticmethod
    def _make_alternatives() -> tuple[Alternative, ...]:
        return (
            Alternative(id="keep", name="Keep", attributes={}),
            Alternative(
                id="switch_a",
                name="Switch A",
                attributes={"attr_str": "a", "attr_int": 1, "attr_float": 1.0},
            ),
            Alternative(
                id="switch_b",
                name="Switch B",
                attributes={"attr_str": "b", "attr_int": 2, "attr_float": 2.0},
            ),
        )

    @staticmethod
    def _make_choice_result(
        chosen: list[str], alternatives: tuple[Alternative, ...]
    ) -> ChoiceResult:
        n = len(chosen)
        alt_ids = tuple(a.id for a in alternatives)
        return ChoiceResult(
            chosen=pa.array(chosen),
            probabilities=pa.table(
                {aid: pa.array([1.0 / len(alt_ids)] * n) for aid in alt_ids}
            ),
            utilities=pa.table(
                {aid: pa.array([-1.0] * n) for aid in alt_ids}
            ),
            alternative_ids=alt_ids,
            seed=42,
        )

    def test_per_household_application(self) -> None:
        """Each row gets its chosen alternative's attributes."""
        alts = self._make_alternatives()
        table = pa.table({
            "id": pa.array([0, 1, 2], type=pa.int64()),
            "attr_str": pa.array(["x", "y", "z"]),
            "attr_int": pa.array([10, 20, 30], type=pa.int64()),
            "attr_float": pa.array([10.0, 20.0, 30.0]),
        })
        pop = PopulationData(tables={"menage": table}, metadata={})
        cr = self._make_choice_result(["keep", "switch_a", "switch_b"], alts)
        result = apply_choices_to_population(pop, cr, alts, "menage")
        t = result.tables["menage"]
        # Row 0: keep → original values
        assert t.column("attr_str")[0].as_py() == "x"
        assert t.column("attr_int")[0].as_py() == 10
        # Row 1: switch_a
        assert t.column("attr_str")[1].as_py() == "a"
        assert t.column("attr_int")[1].as_py() == 1
        assert t.column("attr_float")[1].as_py() == 1.0
        # Row 2: switch_b
        assert t.column("attr_str")[2].as_py() == "b"
        assert t.column("attr_int")[2].as_py() == 2

    def test_keep_no_op(self) -> None:
        """Keep alternative with empty attributes preserves all values."""
        alts = self._make_alternatives()
        table = pa.table({
            "attr_str": pa.array(["x", "y"]),
            "attr_int": pa.array([10, 20], type=pa.int64()),
            "attr_float": pa.array([10.0, 20.0]),
        })
        pop = PopulationData(tables={"menage": table}, metadata={})
        cr = self._make_choice_result(["keep", "keep"], alts)
        result = apply_choices_to_population(pop, cr, alts, "menage")
        t = result.tables["menage"]
        assert t.column("attr_str").to_pylist() == ["x", "y"]
        assert t.column("attr_int").to_pylist() == [10, 20]

    def test_length_mismatch_raises(self) -> None:
        alts = self._make_alternatives()
        table = pa.table({"attr_str": pa.array(["x", "y", "z"])})
        pop = PopulationData(tables={"menage": table}, metadata={})
        cr = self._make_choice_result(["keep", "keep"], alts)
        with pytest.raises(DiscreteChoiceError, match="length"):
            apply_choices_to_population(pop, cr, alts, "menage")

    def test_unknown_id_raises(self) -> None:
        alts = self._make_alternatives()
        table = pa.table({"attr_str": pa.array(["x"])})
        pop = PopulationData(tables={"menage": table}, metadata={})
        cr = self._make_choice_result(["nonexistent"], alts)
        with pytest.raises(DiscreteChoiceError, match="Unknown alternative"):
            apply_choices_to_population(pop, cr, alts, "menage")

    def test_entity_key_not_found_raises(self) -> None:
        alts = self._make_alternatives()
        table = pa.table({"x": pa.array([1])})
        pop = PopulationData(tables={"other": table}, metadata={})
        cr = self._make_choice_result(["keep"], alts)
        with pytest.raises(DiscreteChoiceError, match="Entity key"):
            apply_choices_to_population(pop, cr, alts, "menage")

    def test_empty_population(self) -> None:
        alts = self._make_alternatives()
        table = pa.table({
            "attr_str": pa.array([], type=pa.utf8()),
            "attr_int": pa.array([], type=pa.int64()),
        })
        pop = PopulationData(tables={"menage": table}, metadata={})
        cr = self._make_choice_result([], alts)
        result = apply_choices_to_population(pop, cr, alts, "menage")
        assert result.tables["menage"].num_rows == 0


# ============================================================================
# TestCreateVintageEntries
# ============================================================================


class TestCreateVintageEntries:
    """Tests for create_vintage_entries parameterized function."""

    @staticmethod
    def _make_alternatives() -> tuple[Alternative, ...]:
        return (
            Alternative(id="keep", name="Keep", attributes={}),
            Alternative(id="buy_a", name="A", attributes={"type_key": "alpha"}),
            Alternative(id="buy_b", name="B", attributes={"type_key": "beta"}),
        )

    @staticmethod
    def _make_choice_result(
        chosen: list[str], alternatives: tuple[Alternative, ...]
    ) -> ChoiceResult:
        n = len(chosen)
        alt_ids = tuple(a.id for a in alternatives)
        return ChoiceResult(
            chosen=pa.array(chosen),
            probabilities=pa.table(
                {aid: pa.array([1.0 / len(alt_ids)] * n) for aid in alt_ids}
            ),
            utilities=pa.table(
                {aid: pa.array([-1.0] * n) for aid in alt_ids}
            ),
            alternative_ids=alt_ids,
            seed=42,
        )

    def test_basic_counts(self) -> None:
        """Cohorts are created with correct counts per asset type."""
        alts = self._make_alternatives()
        cr = self._make_choice_result(["buy_a", "buy_a", "buy_b"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="type_key"
        )
        assert len(result) == 2
        # Sorted: alpha, beta
        assert result[0].count == 2
        assert result[0].attributes == {"type_key": "alpha"}
        assert result[1].count == 1
        assert result[1].attributes == {"type_key": "beta"}

    def test_non_purchase_ids_excluded(self) -> None:
        """Non-purchase IDs are excluded from vintage entries."""
        alts = self._make_alternatives()
        cr = self._make_choice_result(["keep", "keep", "buy_a"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="type_key"
        )
        assert len(result) == 1
        assert result[0].count == 1

    def test_all_keep_returns_empty(self) -> None:
        """All keep → empty tuple."""
        alts = self._make_alternatives()
        cr = self._make_choice_result(["keep", "keep"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="type_key"
        )
        assert result == ()

    def test_all_age_zero(self) -> None:
        """All new cohorts have age=0."""
        alts = self._make_alternatives()
        cr = self._make_choice_result(["buy_a", "buy_b"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="type_key"
        )
        for cohort in result:
            assert cohort.age == 0

    def test_sorted_output(self) -> None:
        """Output is sorted by asset type name."""
        alts = self._make_alternatives()
        cr = self._make_choice_result(["buy_b", "buy_a"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="type_key"
        )
        types = [c.attributes["type_key"] for c in result]
        assert types == sorted(types)

    def test_vehicle_type_key(self) -> None:
        """Vehicle domain uses asset_type_key='vehicle_type'."""
        alts = (
            Alternative(id="keep", name="Keep", attributes={}),
            Alternative(id="buy_ev", name="EV", attributes={"vehicle_type": "ev"}),
        )
        cr = self._make_choice_result(["buy_ev"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="vehicle_type"
        )
        assert len(result) == 1
        assert result[0].attributes == {"vehicle_type": "ev"}

    def test_heating_type_key(self) -> None:
        """Heating domain uses asset_type_key='heating_type'."""
        alts = (
            Alternative(id="keep", name="Keep", attributes={}),
            Alternative(id="hp", name="HP", attributes={"heating_type": "heat_pump"}),
        )
        cr = self._make_choice_result(["hp"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="heating_type"
        )
        assert len(result) == 1
        assert result[0].attributes == {"heating_type": "heat_pump"}

    def test_fallback_to_chosen_id_when_key_missing(self) -> None:
        """If asset_type_key not in attributes, falls back to chosen ID."""
        alts = (
            Alternative(id="keep", name="Keep", attributes={}),
            Alternative(id="custom", name="Custom", attributes={"other": "val"}),
        )
        cr = self._make_choice_result(["custom"], alts)
        result = create_vintage_entries(
            cr, alts, frozenset({"keep"}), asset_type_key="missing_key"
        )
        assert len(result) == 1
        assert result[0].attributes == {"missing_key": "custom"}
