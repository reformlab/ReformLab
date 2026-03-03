"""Tests for MergeMethod protocol and supporting types.

Story 11.4 — AC #1: MergeMethod protocol accepts two pa.Table inputs
plus a config, returns merged table plus assumption record.
AC #3: Assumption record includes governance-compatible entry.
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa
import pytest

from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.uniform import UniformMergeMethod

# ====================================================================
# MergeConfig tests
# ====================================================================


class TestMergeConfig:
    """AC #1: Immutable configuration for merge operations."""

    def test_frozen(self) -> None:
        cfg = MergeConfig(seed=42)
        with pytest.raises(AttributeError):
            cfg.seed = 99  # type: ignore[misc]

    def test_default_values(self) -> None:
        cfg = MergeConfig(seed=0)
        assert cfg.seed == 0
        assert cfg.description == ""
        assert cfg.drop_right_columns == ()

    def test_custom_values(self) -> None:
        cfg = MergeConfig(
            seed=123,
            description="test merge",
            drop_right_columns=("col_a", "col_b"),
        )
        assert cfg.seed == 123
        assert cfg.description == "test merge"
        assert cfg.drop_right_columns == ("col_a", "col_b")

    def test_negative_seed_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative integer"):
            MergeConfig(seed=-1)

    def test_bool_seed_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative integer"):
            MergeConfig(seed=True)  # type: ignore[arg-type]

    def test_bool_false_seed_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative integer"):
            MergeConfig(seed=False)  # type: ignore[arg-type]

    def test_drop_right_columns_deep_copied(self) -> None:
        original: list[str] = ["a", "b"]
        cfg = MergeConfig(seed=42, drop_right_columns=tuple(original))
        original.append("c")
        assert cfg.drop_right_columns == ("a", "b")

    def test_drop_right_columns_accepts_list_input(self) -> None:
        cfg = MergeConfig(seed=42, drop_right_columns=("x",))
        assert cfg.drop_right_columns == ("x",)


# ====================================================================
# MergeAssumption tests
# ====================================================================


class TestMergeAssumption:
    """AC #3: Assumption record with governance integration."""

    def test_frozen(self) -> None:
        assumption = MergeAssumption(
            method_name="test", statement="test statement", details={}
        )
        with pytest.raises(AttributeError):
            assumption.method_name = "other"  # type: ignore[misc]

    def test_details_deep_copied(self) -> None:
        original: dict[str, Any] = {"key": "value", "nested": [1, 2]}
        assumption = MergeAssumption(
            method_name="test",
            statement="test statement",
            details=original,
        )
        original["key"] = "mutated"
        original["nested"].append(3)
        assert assumption.details["key"] == "value"
        assert assumption.details["nested"] == [1, 2]

    def test_to_governance_entry_structure(self) -> None:
        assumption = MergeAssumption(
            method_name="uniform",
            statement="independence assumption",
            details={"seed": 42, "rows": 100},
        )
        entry = assumption.to_governance_entry()
        assert entry["key"] == "merge_uniform"
        assert entry["source"] == "merge_step"
        assert entry["is_default"] is False
        assert isinstance(entry["value"], dict)
        assert entry["value"]["method"] == "uniform"
        assert entry["value"]["statement"] == "independence assumption"
        assert entry["value"]["seed"] == 42
        assert entry["value"]["rows"] == 100

    def test_to_governance_entry_custom_source_label(self) -> None:
        assumption = MergeAssumption(
            method_name="ipf", statement="balancing", details={}
        )
        entry = assumption.to_governance_entry(source_label="custom_step")
        assert entry["source"] == "custom_step"

    def test_to_governance_entry_details_override(self) -> None:
        """Details with 'method' key are overridden by actual method_name."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="real statement",
            details={"method": "should_be_overridden", "statement": "old"},
        )
        entry = assumption.to_governance_entry()
        assert entry["value"]["method"] == "uniform"
        assert entry["value"]["statement"] == "real statement"


# ====================================================================
# MergeResult tests
# ====================================================================


class TestMergeResult:
    """AC #1: Immutable merge result holding table + assumption."""

    def test_frozen(self) -> None:
        table = pa.table({"x": [1, 2]})
        assumption = MergeAssumption(
            method_name="test", statement="test", details={}
        )
        result = MergeResult(table=table, assumption=assumption)
        with pytest.raises(AttributeError):
            result.table = pa.table({"y": [3]})  # type: ignore[misc]

    def test_holds_table_and_assumption(self) -> None:
        table = pa.table({"x": [1, 2]})
        assumption = MergeAssumption(
            method_name="test", statement="test", details={}
        )
        result = MergeResult(table=table, assumption=assumption)
        assert result.table.equals(table)
        assert result.assumption is assumption


# ====================================================================
# MergeMethod protocol tests
# ====================================================================


class TestMergeMethodProtocol:
    """AC #1: Runtime-checkable protocol for merge methods."""

    def test_uniform_satisfies_protocol(self) -> None:
        method = UniformMergeMethod()
        assert isinstance(method, MergeMethod)

    def test_non_conforming_class_fails(self) -> None:
        class NotAMergeMethod:
            pass

        assert not isinstance(NotAMergeMethod(), MergeMethod)

    def test_partial_conformance_fails(self) -> None:
        class OnlyName:
            @property
            def name(self) -> str:
                return "partial"

        assert not isinstance(OnlyName(), MergeMethod)
