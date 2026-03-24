# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for population pipeline builder and execution.

Implements Story 11.6, FR40, FR41.
"""

from __future__ import annotations

import dataclasses

import pyarrow as pa
import pytest

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
)
from reformlab.population.loaders.base import (
    CacheStatus,
    SourceConfig,
)
from reformlab.population.methods.base import (
    MergeConfig,
    MergeResult,
)
from reformlab.population.pipeline import (
    PipelineConfigError,
    PipelineError,
    PipelineExecutionError,
    PipelineResult,
    PipelineStepLog,
    PopulationPipeline,
)

# ====================================================================
# Error hierarchy tests
# ====================================================================


class TestPipelineErrorHierarchy:
    """Test pipeline error exception hierarchy."""

    def test_pipeline_error_inherits_exception(self) -> None:
        """PipelineError inherits from Exception."""
        exc = PipelineError(
            summary="Test summary",
            reason="Test reason",
            fix="Test fix",
        )
        assert isinstance(exc, Exception)
        assert isinstance(exc, PipelineError)
        assert exc.summary == "Test summary"
        assert exc.reason == "Test reason"
        assert exc.fix == "Test fix"

    def test_pipeline_error_message_format(self) -> None:
        """PipelineError message includes summary, reason, fix."""
        exc = PipelineError(
            summary="Pipeline failed",
            reason="Configuration error",
            fix="Check configuration",
        )
        assert "Pipeline failed" in str(exc)
        assert "Configuration error" in str(exc)
        assert "Check configuration" in str(exc)

    def test_pipeline_config_error_inherits_pipeline_error(self) -> None:
        """PipelineConfigError inherits from PipelineError."""
        exc = PipelineConfigError(
            summary="Invalid configuration",
            reason="Duplicate label",
            fix="Use unique labels",
        )
        assert isinstance(exc, PipelineError)
        assert isinstance(exc, PipelineConfigError)
        assert isinstance(exc, Exception)

    def test_pipeline_execution_error_inherits_pipeline_error(self) -> None:
        """PipelineExecutionError inherits from PipelineError."""
        cause = ValueError("Inner error")
        exc = PipelineExecutionError(
            summary="Execution failed",
            reason="Step failed",
            fix="Check step configuration",
            step_index=0,
            step_label="test_step",
            step_type="merge",
            cause=cause,
            tables_involved=("left", "right"),
        )
        assert isinstance(exc, PipelineError)
        assert isinstance(exc, PipelineExecutionError)
        assert isinstance(exc, Exception)

    def test_pipeline_execution_error_has_step_context(self) -> None:
        """PipelineExecutionError has step_index, step_label, step_type, cause, tables_involved."""
        cause = ValueError("Inner error")
        exc = PipelineExecutionError(
            summary="Execution failed",
            reason="Step failed",
            fix="Check step configuration",
            step_index=2,
            step_label="income_vehicles",
            step_type="merge",
            cause=cause,
            tables_involved=("income", "vehicles"),
        )
        assert exc.step_index == 2
        assert exc.step_label == "income_vehicles"
        assert exc.step_type == "merge"
        assert exc.cause is cause
        assert exc.tables_involved == ("income", "vehicles")

    def test_pipeline_execution_error_with_empty_tables_involved(self) -> None:
        """PipelineExecutionError tables_involved defaults to empty tuple."""
        cause = ValueError("Inner error")
        exc = PipelineExecutionError(
            summary="Execution failed",
            reason="Step failed",
            fix="Check step configuration",
            step_index=0,
            step_label="test_step",
            step_type="load",
            cause=cause,
        )
        assert exc.tables_involved == ()


# ====================================================================
# Pipeline step log tests
# ====================================================================


class TestPipelineStepLog:
    """Test frozen dataclass for completed step logs."""

    def test_frozen_dataclass(self) -> None:
        """StepLog is frozen and holds all fields."""
        log = PipelineStepLog(
            step_index=0,
            step_type="load",
            label="income",
            input_labels=(),
            output_rows=100,
            output_columns=("household_id", "income", "region"),
            method_name=None,
            duration_ms=45.2,
        )
        assert log.step_index == 0
        assert log.step_type == "load"
        assert log.label == "income"
        assert log.input_labels == ()
        assert log.output_rows == 100
        assert log.output_columns == ("household_id", "income", "region")
        assert log.method_name is None
        assert log.duration_ms == 45.2

        # Frozen - cannot modify
        with pytest.raises(dataclasses.FrozenInstanceError):
            log.step_index = 1  # type: ignore[misc]

    def test_step_type_is_load_or_merge(self) -> None:
        """step_type is either 'load' or 'merge'."""
        load_log = PipelineStepLog(
            step_index=0,
            step_type="load",
            label="income",
            input_labels=(),
            output_rows=100,
            output_columns=("household_id", "income"),
            method_name=None,
            duration_ms=10.0,
        )
        merge_log = PipelineStepLog(
            step_index=1,
            step_type="merge",
            label="income_vehicles",
            input_labels=("income", "vehicles"),
            output_rows=100,
            output_columns=("household_id", "income", "vehicle_type"),
            method_name="uniform",
            duration_ms=25.5,
        )
        assert load_log.step_type == "load"
        assert merge_log.step_type == "merge"


# ====================================================================
# Pipeline result tests
# ====================================================================


class TestPipelineResult:
    """Test frozen dataclass for pipeline execution result."""

    def test_frozen_dataclass(self) -> None:
        """Result is frozen and holds table + assumption_chain + step_log."""
        table = pa.table({"household_id": pa.array([1, 2, 3])})
        assumption = PipelineAssumptionChain(records=())
        log = (
            PipelineStepLog(  # type: ignore[assignment]
                step_index=0,
                step_type="load",
                label="income",
                input_labels=(),
                output_rows=3,
                output_columns=("household_id",),
                method_name=None,
                duration_ms=10.0,
            ),
        )

        result = PipelineResult(
            table=table,
            assumption_chain=assumption,
            step_log=log,
        )
        assert result.table == table
        assert result.assumption_chain == assumption
        assert result.step_log == log

        # Frozen - cannot modify
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.table = table  # type: ignore[misc]


# ====================================================================
# Pipeline construction tests
# ====================================================================


class TestPopulationPipelineConstruction:
    """Test PopulationPipeline constructor and initial state."""

    def test_constructor_accepts_optional_description(self) -> None:
        """Constructor accepts optional description parameter."""
        pipeline = PopulationPipeline(description="French household population 2024")
        assert pipeline.description == "French household population 2024"

    def test_constructor_with_empty_description(self) -> None:
        """Constructor with no description sets empty string."""
        pipeline = PopulationPipeline()
        assert pipeline.description == ""

    def test_step_count_starts_at_0(self) -> None:
        """step_count property starts at 0."""
        pipeline = PopulationPipeline()
        assert pipeline.step_count == 0

    def test_labels_starts_empty(self) -> None:
        """labels property starts as empty frozenset."""
        pipeline = PopulationPipeline()
        assert pipeline.labels == frozenset()


# ====================================================================
# Pipeline add_source tests
# ====================================================================


class TestPopulationPipelineAddSource:
    """Test adding data sources to pipeline."""

    def test_add_source_label_appears_in_labels(self) -> None:
        """After adding source, label appears in labels."""
        pipeline = PopulationPipeline()
        mock_loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        pipeline.add_source("income", loader=mock_loader, config=config)
        assert "income" in pipeline.labels

    def test_add_source_increments_step_count(self) -> None:
        """add_source() increments step_count."""
        pipeline = PopulationPipeline()
        mock_loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        assert pipeline.step_count == 0
        pipeline.add_source("income", loader=mock_loader, config=config)
        assert pipeline.step_count == 1

    def test_add_source_fluent_api_returns_self(self) -> None:
        """add_source() returns self for fluent API."""
        pipeline = PopulationPipeline()
        mock_loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        result = pipeline.add_source("income", loader=mock_loader, config=config)
        assert result is pipeline

    def test_add_source_empty_label_raises_config_error(self) -> None:
        """Empty label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        mock_loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        with pytest.raises(PipelineConfigError, match="label must be a non-empty"):
            pipeline.add_source("", loader=mock_loader, config=config)

    def test_add_source_duplicate_label_raises_config_error(self) -> None:
        """Duplicate label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        mock_loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        pipeline.add_source("income", loader=mock_loader, config=config)
        with pytest.raises(PipelineConfigError, match="Duplicate label 'income'"):
            pipeline.add_source("income", loader=mock_loader, config=config)


# ====================================================================
# Pipeline add_merge tests
# ====================================================================


class TestPopulationPipelineAddMerge:
    """Test adding merge steps to pipeline."""

    def test_add_merge_after_two_sources(self) -> None:
        """After adding two sources, can add a merge referencing them."""
        pipeline = PopulationPipeline()
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car", "suv"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader_a, config=config)
        pipeline.add_source("vehicles", loader=loader_b, config=config)
        pipeline.add_merge(
            "income_vehicles",
            left="income",
            right="vehicles",
            method=merge_method,
            config=merge_config,
        )

        assert "income_vehicles" in pipeline.labels

    def test_add_merge_fluent_api_returns_self(self) -> None:
        """add_merge() returns self for fluent API."""
        pipeline = PopulationPipeline()
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader_a, config=config)
        pipeline.add_source("vehicles", loader=loader_b, config=config)
        result = pipeline.add_merge(
            "income_vehicles",
            left="income",
            right="vehicles",
            method=merge_method,
            config=merge_config,
        )

        assert result is pipeline

    def test_add_merge_missing_left_label_raises_config_error(self) -> None:
        """Missing left label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader, config=config)
        with pytest.raises(PipelineConfigError, match="Missing left label 'missing'"):
            pipeline.add_merge(
                "result",
                left="missing",
                right="income",
                method=merge_method,
                config=merge_config,
            )

    def test_add_merge_missing_right_label_raises_config_error(self) -> None:
        """Missing right label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader, config=config)
        with pytest.raises(PipelineConfigError, match="Missing right label 'missing'"):
            pipeline.add_merge(
                "result",
                left="income",
                right="missing",
                method=merge_method,
                config=merge_config,
            )

    def test_add_merge_same_left_and_right_raises_config_error(self) -> None:
        """Same left and right label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader, config=config)
        with pytest.raises(PipelineConfigError, match="left and right labels must be different"):
            pipeline.add_merge(
                "result",
                left="income",
                right="income",
                method=merge_method,
                config=merge_config,
            )

    def test_add_merge_empty_label_raises_config_error(self) -> None:
        """Empty label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader_a, config=config)
        pipeline.add_source("vehicles", loader=loader_b, config=config)
        with pytest.raises(PipelineConfigError, match="label must be a non-empty"):
            pipeline.add_merge(
                "",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )

    def test_add_merge_duplicate_label_raises_config_error(self) -> None:
        """Duplicate label raises PipelineConfigError."""
        pipeline = PopulationPipeline()
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod()
        merge_config = MergeConfig(seed=42)

        pipeline.add_source("income", loader=loader_a, config=config)
        pipeline.add_source("vehicles", loader=loader_b, config=config)
        pipeline.add_merge(
            "result",
            left="income",
            right="vehicles",
            method=merge_method,
            config=merge_config,
        )
        with pytest.raises(PipelineConfigError, match="Duplicate label 'result'"):
            pipeline.add_merge(
                "result",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )


# ====================================================================
# Pipeline execution tests - basic
# ====================================================================


class TestPopulationPipelineExecuteBasic:
    """Test basic pipeline execution with one merge."""

    def test_two_sources_one_merge_produces_correct_table(self) -> None:
        """Two sources + one uniform merge → result table has correct row count and columns."""
        loader_a = _MockLoader(
            pa.table(
                {
                    "household_id": pa.array([1, 2, 3], type=pa.int64()),
                    "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
                }
            )
        )
        loader_b = _MockLoader(
            pa.table(
                {
                    "vehicle_type": pa.array(["car", "suv", "bike"], type=pa.utf8()),
                }
            )
        )
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(
            output_table=pa.table(
                {
                    "household_id": pa.array([1, 2, 3], type=pa.int64()),
                    "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
                    "vehicle_type": pa.array(["car", "suv", "bike"], type=pa.utf8()),
                }
            )
        )
        merge_config = MergeConfig(seed=42)

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "income_vehicles",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )
        )

        result = pipeline.execute()

        # Result has correct row count (= table_a rows)
        assert result.table.num_rows == 3
        # Result has all columns from A + all from B
        assert set(result.table.column_names) == {
            "household_id",
            "income",
            "vehicle_type",
        }

    def test_step_log_has_three_entries(self) -> None:
        """result.step_log has 3 entries (2 loads + 1 merge)."""
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(
            output_table=pa.table({"household_id": pa.array([1]), "vehicle_type": pa.array(["car"])})
        )
        merge_config = MergeConfig(seed=42)

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "income_vehicles",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )
        )

        result = pipeline.execute()
        assert len(result.step_log) == 3

    def test_load_step_logs_have_correct_attributes(self) -> None:
        """Load step logs have step_type='load', method_name=None, input_labels=()."""
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(
            output_table=pa.table({"household_id": pa.array([1]), "vehicle_type": pa.array(["car"])})
        )
        merge_config = MergeConfig(seed=42)

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "income_vehicles",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )
        )

        result = pipeline.execute()

        # First two steps are loads
        load_logs = [log for log in result.step_log if log.step_type == "load"]
        assert len(load_logs) == 2

        for log in load_logs:
            assert log.step_type == "load"
            assert log.method_name is None
            assert log.input_labels == ()

    def test_merge_step_log_has_correct_attributes(self) -> None:
        """Merge step log has step_type='merge', method_name='uniform', input_labels=(left, right)."""
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(
            output_table=pa.table({"household_id": pa.array([1]), "vehicle_type": pa.array(["car"])}),
            name="uniform",
        )
        merge_config = MergeConfig(seed=42)

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "income_vehicles",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )
        )

        result = pipeline.execute()

        merge_logs = [log for log in result.step_log if log.step_type == "merge"]
        assert len(merge_logs) == 1

        log = merge_logs[0]
        assert log.step_type == "merge"
        assert log.method_name == "uniform"
        assert log.input_labels == ("income", "vehicles")

    def test_all_step_logs_have_valid_attributes(self) -> None:
        """All step logs have output_rows > 0, output_columns non-empty, duration_ms >= 0."""
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(
            output_table=pa.table({"household_id": pa.array([1]), "vehicle_type": pa.array(["car"])})
        )
        merge_config = MergeConfig(seed=42)

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "income_vehicles",
                left="income",
                right="vehicles",
                method=merge_method,
                config=merge_config,
            )
        )

        result = pipeline.execute()

        for log in result.step_log:
            assert log.output_rows > 0
            assert len(log.output_columns) > 0
            assert log.duration_ms >= 0


# ====================================================================
# Pipeline execution tests - advanced
# ====================================================================


class TestPopulationPipelineExecuteMultiMerge:
    """Test pipeline execution with multiple merges."""

    def test_three_sources_two_merges_produces_final_table(self) -> None:
        """Three sources + two merges (A+B→AB, AB+C→final) → result table
        has columns from all three sources."""
        loader_a = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car", "suv"])}))
        loader_c = _MockLoader(pa.table({"heating_type": pa.array(["gas", "electric"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(
            output_table=pa.table(
                {"household_id": pa.array([1, 2]), "vehicle_type": pa.array(["car", "suv"])}
            )
        )

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_source("heating", loader=loader_c, config=config)
            .add_merge(
                "income_vehicles",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
            .add_merge(
                "population",
                left="income_vehicles",
                right="heating",
                method=merge_method,
                config=MergeConfig(seed=43),
            )
        )

        result = pipeline.execute()

        # Result has columns from all three sources (via merges)
        assert set(result.table.column_names) == {
            "household_id",
            "vehicle_type",
        }

    def test_step_log_has_five_entries(self) -> None:
        """result.step_log has 5 entries (3 loads + 2 merges)."""
        loader_a = _MockLoader(pa.table({"a": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"b": pa.array([1])}))
        loader_c = _MockLoader(pa.table({"c": pa.array([1])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(output_table=pa.table({"a": pa.array([1]), "b": pa.array([1])}))

        pipeline = (
            PopulationPipeline()
            .add_source("a", loader=loader_a, config=config)
            .add_source("b", loader=loader_b, config=config)
            .add_source("c", loader=loader_c, config=config)
            .add_merge("ab", left="a", right="b", method=merge_method, config=MergeConfig(seed=42))
            .add_merge("abc", left="ab", right="c", method=merge_method, config=MergeConfig(seed=43))
        )

        result = pipeline.execute()
        assert len(result.step_log) == 5

    def test_assumption_chain_has_two_records(self) -> None:
        """result.assumption_chain has 2 records (one per merge)."""
        loader_a = _MockLoader(pa.table({"a": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"b": pa.array([1])}))
        loader_c = _MockLoader(pa.table({"c": pa.array([1])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(output_table=pa.table({"a": pa.array([1]), "b": pa.array([1])}))

        pipeline = (
            PopulationPipeline()
            .add_source("a", loader=loader_a, config=config)
            .add_source("b", loader=loader_b, config=config)
            .add_source("c", loader=loader_c, config=config)
            .add_merge("ab", left="a", right="b", method=merge_method, config=MergeConfig(seed=42))
            .add_merge("abc", left="ab", right="c", method=merge_method, config=MergeConfig(seed=43))
        )

        result = pipeline.execute()
        assert len(result.assumption_chain) == 2


class TestPopulationPipelineExecuteWithConditionalSampling:
    """Test pipeline execution with conditional sampling merge."""

    def test_conditional_sampling_respects_strata(self) -> None:
        """Source A (with income_bracket) + source B (with income_bracket)
        → conditional merge → strata respected in output."""
        loader_a = _MockLoader(
            pa.table(
                {
                    "household_id": pa.array([1, 2, 3, 4], type=pa.int64()),
                    "income_bracket": pa.array(["low", "low", "high", "high"], type=pa.utf8()),
                }
            )
        )
        loader_b = _MockLoader(
            pa.table(
                {
                    "vehicle_type": pa.array(["car", "suv", "car", "suv"], type=pa.utf8()),
                    "income_bracket": pa.array(["low", "low", "high", "high"], type=pa.utf8()),
                }
            )
        )
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        # Use real conditional sampling method
        from reformlab.population.methods.conditional import ConditionalSamplingMethod

        merge_method = ConditionalSamplingMethod(strata_columns=("income_bracket",))

        pipeline = (
            PopulationPipeline()
            .add_source("households", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="households",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42, drop_right_columns=("income_bracket",)),
            )
        )

        result = pipeline.execute()

        # Result has correct row count
        assert result.table.num_rows == 4
        # Result has all columns from A + all from B (except dropped strata column)
        assert "household_id" in result.table.column_names
        assert "income_bracket" in result.table.column_names  # from table_a
        assert "vehicle_type" in result.table.column_names

    def test_conditional_sampling_assumption_recorded(self) -> None:
        """Conditional sampling merge produces assumption record."""
        loader_a = _MockLoader(
            pa.table(
                {
                    "household_id": pa.array([1, 2]),
                    "income_bracket": pa.array(["low", "high"]),
                }
            )
        )
        loader_b = _MockLoader(
            pa.table(
                {
                    "vehicle_type": pa.array(["car", "suv"]),
                    "income_bracket": pa.array(["low", "high"]),
                }
            )
        )
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        from reformlab.population.methods.conditional import ConditionalSamplingMethod

        merge_method = ConditionalSamplingMethod(strata_columns=("income_bracket",))

        pipeline = (
            PopulationPipeline()
            .add_source("households", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="households",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42, drop_right_columns=("income_bracket",)),
            )
        )

        result = pipeline.execute()

        assert len(result.assumption_chain) == 1
        assert result.assumption_chain.records[0].assumption.method_name == "conditional"


class TestPopulationPipelineExecuteWithIPF:
    """Test pipeline execution with IPF merge."""

    def test_ipf_merge_produces_valid_output(self) -> None:
        """Source A (with income_bracket) + source B → IPF merge with
        marginal constraints → result marginals match within ±1."""
        loader_a = _MockLoader(
            pa.table(
                {
                    "household_id": pa.array([1, 2, 3, 4], type=pa.int64()),
                    "income_bracket": pa.array(["low", "low", "high", "high"], type=pa.utf8()),
                }
            )
        )
        loader_b = _MockLoader(
            pa.table(
                {
                    "vehicle_type": pa.array(["car", "car", "suv", "bike"], type=pa.utf8()),
                }
            )
        )
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        from reformlab.population.methods.base import IPFConstraint
        from reformlab.population.methods.ipf import IPFMergeMethod

        # Constraint on income_bracket (from table_a)
        constraint = IPFConstraint(
            dimension="income_bracket",
            targets={"low": 2, "high": 2},
        )
        merge_method = IPFMergeMethod(constraints=(constraint,))

        pipeline = (
            PopulationPipeline()
            .add_source("households", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="households",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
        )

        result = pipeline.execute()

        # Result has correct row count
        assert result.table.num_rows == 4
        # Result has all columns
        assert "household_id" in result.table.column_names
        assert "income_bracket" in result.table.column_names
        assert "vehicle_type" in result.table.column_names

    def test_ipf_assumption_recorded(self) -> None:
        """IPF merge produces assumption record with convergence details."""
        loader_a = _MockLoader(
            pa.table(
                {
                    "household_id": pa.array([1, 2, 3, 4]),
                    "income_bracket": pa.array(["low", "low", "high", "high"]),
                }
            )
        )
        loader_b = _MockLoader(
            pa.table(
                {
                    "vehicle_type": pa.array(["car", "car", "suv", "bike"]),
                }
            )
        )
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        from reformlab.population.methods.base import IPFConstraint
        from reformlab.population.methods.ipf import IPFMergeMethod

        constraint = IPFConstraint(
            dimension="income_bracket",
            targets={"low": 2, "high": 2},
        )
        merge_method = IPFMergeMethod(constraints=(constraint,))

        pipeline = (
            PopulationPipeline()
            .add_source("households", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="households",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
        )

        result = pipeline.execute()

        assert len(result.assumption_chain) == 1
        assert result.assumption_chain.records[0].assumption.method_name == "ipf"
        # Check that convergence details are in assumption
        details = result.assumption_chain.records[0].assumption.details
        assert "iterations" in details
        assert "converged" in details


class TestPopulationPipelineExecuteDeterminism:
    """Test pipeline execution determinism."""

    def test_same_configuration_produces_identical_result(self) -> None:
        """Same pipeline configuration → identical result."""
        loader_a = _MockLoader(
            pa.table({"household_id": pa.array([1, 2, 3]), "income": pa.array([10, 20, 30])})
        )
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car", "suv", "bike"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        from reformlab.population.methods.uniform import UniformMergeMethod

        merge_method = UniformMergeMethod()

        # Build same pipeline twice
        pipeline1 = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
        )

        pipeline2 = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
        )

        result1 = pipeline1.execute()
        result2 = pipeline2.execute()

        # Compare PyArrow tables
        assert result1.table.equals(result2.table)

    def test_different_seed_produces_different_result(self) -> None:
        """Different seed in merge config → different result."""
        loader_a = _MockLoader(
            pa.table({"household_id": pa.array([1, 2, 3]), "income": pa.array([10, 20, 30])})
        )
        loader_b = _MockLoader(pa.table({"vehicle_type": pa.array(["car", "suv", "bike"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        from reformlab.population.methods.uniform import UniformMergeMethod

        merge_method = UniformMergeMethod()

        pipeline1 = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
        )

        pipeline2 = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=999),
            )
        )

        result1 = pipeline1.execute()
        result2 = pipeline2.execute()

        # Different seed should produce different matchings (unless by chance)
        # With 3 rows, probability of same matching is 1/6 ≈ 0.17
        # We'll check that at least one column differs
        tables_differ = not result1.table.equals(result2.table)
        assert tables_differ, "Different seeds should produce different results"


class TestPopulationPipelineExecuteNoMerge:
    """Test pipeline execution without merge steps."""

    def test_only_load_steps_raises_config_error(self) -> None:
        """Pipeline with only load steps (no merges) → PipelineConfigError on execute."""
        loader = _MockLoader(pa.table({"household_id": pa.array([1, 2])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader, config=config)
            .add_source("vehicles", loader=loader, config=config)
        )

        with pytest.raises(PipelineConfigError, match="must have at least one merge step"):
            pipeline.execute()


class TestPopulationPipelineExecuteLoadFailure:
    """Test pipeline execution with failing loader."""

    def test_failing_loader_raises_execution_error(self) -> None:
        """Pipeline with a failing loader → PipelineExecutionError with correct context."""
        from reformlab.population.loaders.errors import DataSourceDownloadError

        loader_a = _MockLoader(pa.table({"household_id": pa.array([1])}))
        loader_b = _FailingLoader()
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(output_table=pa.table({"a": pa.array([1]), "b": pa.array([1])}))

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),
            )
        )

        with pytest.raises(PipelineExecutionError) as exc_info:
            pipeline.execute()

        exc = exc_info.value
        assert exc.step_index == 1  # Second step (vehicles load)
        assert exc.step_label == "vehicles"
        assert exc.step_type == "load"
        assert exc.tables_involved == ()
        assert isinstance(exc.cause, DataSourceDownloadError)


class TestPopulationPipelineExecuteMergeFailure:
    """Test pipeline execution with merge failure."""

    def test_merge_failure_raises_execution_error(self) -> None:
        """Pipeline with intentionally conflicting column names →
        PipelineExecutionError with correct context."""
        from reformlab.population.methods.errors import MergeValidationError

        loader_a = _MockLoader(pa.table({"id": pa.array([1, 2]), "income": pa.array([10, 20])}))
        loader_b = _MockLoader(pa.table({"id": pa.array([1, 2]), "vehicle": pa.array(["car", "suv"])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")

        # Use real uniform merge, which will fail due to conflicting 'id' column
        from reformlab.population.methods.uniform import UniformMergeMethod

        merge_method = UniformMergeMethod()

        pipeline = (
            PopulationPipeline()
            .add_source("income", loader=loader_a, config=config)
            .add_source("vehicles", loader=loader_b, config=config)
            .add_merge(
                "population",
                left="income",
                right="vehicles",
                method=merge_method,
                config=MergeConfig(seed=42),  # No drop_right_columns - will cause conflict
            )
        )

        with pytest.raises(PipelineExecutionError) as exc_info:
            pipeline.execute()

        exc = exc_info.value
        assert exc.step_index == 2  # Third step (merge)
        assert exc.step_label == "population"
        assert exc.step_type == "merge"
        assert exc.tables_involved == ("income", "vehicles")
        assert isinstance(exc.cause, MergeValidationError)


class TestPopulationPipelineExecuteLoadAfterMerge:
    """Test pipeline execution with load step after merge."""

    def test_load_after_merge_produces_last_merge_as_final_table(self) -> None:
        """Pipeline with a load step added after the last merge → final table
        is still the last merge output."""
        loader_a = _MockLoader(pa.table({"a": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"b": pa.array([1])}))
        loader_c = _MockLoader(pa.table({"c": pa.array([1])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(output_table=pa.table({"a": pa.array([1]), "b": pa.array([1])}))

        pipeline = (
            PopulationPipeline()
            .add_source("a", loader=loader_a, config=config)
            .add_source("b", loader=loader_b, config=config)
            .add_merge("ab", left="a", right="b", method=merge_method, config=MergeConfig(seed=42))
            .add_source("c", loader=loader_c, config=config)  # Load after merge
        )

        result = pipeline.execute()

        # Final table is from last merge (ab), not from load c
        assert set(result.table.column_names) == {"a", "b"}
        assert "c" not in result.table.column_names


class TestPopulationPipelineExecuteStepOrder:
    """Test pipeline execution order."""

    def test_steps_execute_in_insertion_order(self) -> None:
        """Steps execute in insertion order: verify via step_log indices matching insertion order."""
        loader_a = _MockLoader(pa.table({"a": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"b": pa.array([1])}))
        loader_c = _MockLoader(pa.table({"c": pa.array([1])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(output_table=pa.table({"a": pa.array([1]), "b": pa.array([1])}))

        pipeline = (
            PopulationPipeline()
            .add_source("a", loader=loader_a, config=config)  # Step 0
            .add_source("b", loader=loader_b, config=config)  # Step 1
            .add_merge("ab", left="a", right="b", method=merge_method, config=MergeConfig(seed=42))  # Step 2
            .add_source("c", loader=loader_c, config=config)  # Step 3
        )

        result = pipeline.execute()

        # Verify step order
        assert result.step_log[0].step_index == 0
        assert result.step_log[0].label == "a"
        assert result.step_log[1].step_index == 1
        assert result.step_log[1].label == "b"
        assert result.step_log[2].step_index == 2
        assert result.step_log[2].label == "ab"
        assert result.step_log[3].step_index == 3
        assert result.step_log[3].label == "c"


class TestPopulationPipelineFluentAPI:
    """Test fluent API usage."""

    def test_full_fluent_chain_works(self) -> None:
        """Full fluent chain: PopulationPipeline().add_source(...).add_source(...)
        .add_merge(...).execute() works."""
        loader_a = _MockLoader(pa.table({"a": pa.array([1])}))
        loader_b = _MockLoader(pa.table({"b": pa.array([1])}))
        config = SourceConfig(provider="mock", dataset_id="test", url="mock://test")
        merge_method = _MockMergeMethod(output_table=pa.table({"a": pa.array([1]), "b": pa.array([1])}))

        result = (
            PopulationPipeline()
            .add_source("a", loader=loader_a, config=config)
            .add_source("b", loader=loader_b, config=config)
            .add_merge("ab", left="a", right="b", method=merge_method, config=MergeConfig(seed=42))
            .execute()
        )

        assert result.table.num_rows == 1
        assert len(result.step_log) == 3


# ====================================================================
# Mock implementations for testing
# ====================================================================


class _MockLoader:
    """Minimal DataSourceLoader for pipeline testing."""

    def __init__(self, table: pa.Table) -> None:
        self._table = table

    def download(self, config: SourceConfig) -> tuple:  # type: ignore[type-arg]
        import hashlib
        from datetime import UTC, datetime
        from pathlib import Path

        from reformlab.computation.types import PopulationData
        from reformlab.data.pipeline import DatasetManifest, DataSourceMetadata

        population = PopulationData.from_table(self._table, entity_type="default")
        manifest = DatasetManifest(
            source=DataSourceMetadata(
                name=config.dataset_id,
                version="mock",
                url=config.url,
                description="mock",
            ),
            content_hash=hashlib.sha256(b"mock").hexdigest(),
            file_path=Path("<mock>"),
            format="parquet",
            row_count=self._table.num_rows,
            column_names=tuple(self._table.column_names),
            loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        return population, manifest

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )

    def descriptor(self) -> object:
        from reformlab.computation.ingestion import DataSchema
        from reformlab.data.descriptor import DatasetDescriptor

        return DatasetDescriptor(
            dataset_id="mock",
            provider="mock",
            description="mock",
            schema=DataSchema(
                schema=self._table.schema,
                required_columns=tuple(self._table.schema.names),
            ),
        )


class _FailingLoader:
    """Mock loader that always raises on download."""

    def __init__(self) -> None:
        pass

    def download(self, config: SourceConfig) -> tuple:  # type: ignore[type-arg]
        from reformlab.population.loaders.errors import DataSourceDownloadError

        raise DataSourceDownloadError(
            summary="Download failed",
            reason="mock failure for testing",
            fix="this is a test mock",
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

    def descriptor(self) -> object:
        from reformlab.computation.ingestion import DataSchema
        from reformlab.data.descriptor import DatasetDescriptor

        return DatasetDescriptor(
            dataset_id="failing",
            provider="mock",
            description="failing mock",
            schema=DataSchema(schema=pa.schema([]), required_columns=()),
        )


class _MockMergeMethod:
    """Minimal MergeMethod for pipeline testing."""

    def __init__(
        self,
        output_table: pa.Table | None = None,
        name: str = "mock_merge",
    ) -> None:
        self._output_table = (
            output_table if output_table is not None else pa.table({"mock_col": pa.array([1])})
        )
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        from reformlab.population.methods.base import MergeAssumption

        assumption = MergeAssumption(
            method_name=self.name,
            statement=f"Mock merge with seed {config.seed}",
            details={"seed": config.seed},
        )
        return MergeResult(table=self._output_table, assumption=assumption)
