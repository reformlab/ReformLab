# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Population pipeline builder and execution.

Provides a composable builder for constructing populations from multiple
institutional data sources using statistical merge methods. Each step
produces a labeled intermediate table. The pipeline executes sequentially,
merging sources in insertion order, and produces a final merged population.

The pipeline records every merge step's assumption for governance integration
via ``PipelineAssumptionChain``, enabling full traceability from raw data
to final population.

Implements Story 11.6, FR40, FR41.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
    PipelineAssumptionRecord,
)
from reformlab.population.loaders.base import (
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.methods.base import (
    MergeConfig,
    MergeMethod,
)

if TYPE_CHECKING:
    import pyarrow as pa


_logger = logging.getLogger(__name__)


# ====================================================================
# Pipeline error hierarchy
# ====================================================================


class PipelineError(Exception):
    """Base exception for population pipeline operations.

    All pipeline-specific errors inherit from this base class.
    Follows the summary-reason-fix pattern for consistent error messaging.

    Args:
        summary: Brief description of the error.
        reason: Detailed explanation of why the error occurred.
        fix: Suggested resolution or workaround.

    Attributes:
        summary: Brief description of the error.
        reason: Detailed explanation of why the error occurred.
        fix: Suggested resolution or workaround.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class PipelineConfigError(PipelineError):
    """Raised for invalid pipeline configuration.

    Raised when the pipeline structure is invalid, such as duplicate
    labels, missing references, or empty pipelines.
    """


class PipelineExecutionError(PipelineError):
    """Raised when a pipeline step fails during execution.

    Wraps the underlying cause and adds step context so the analyst
    can identify exactly which step, which tables, and which error
    caused the failure.

    Args:
        summary: Brief description of the error.
        reason: Detailed explanation of why the error occurred.
        fix: Suggested resolution or workaround.
        step_index: Zero-based index of the failing step in the pipeline.
        step_label: Human-readable label for the failing step's output.
        step_type: Either "load" or "merge".
        cause: The original exception that caused the failure.
        tables_involved: Tuple of label names involved in the step.
            Empty tuple for load steps, (left, right) for merge steps.

    Attributes:
        step_index: Zero-based index of the failing step.
        step_label: Human-readable label for the failing step.
        step_type: Either "load" or "merge".
        cause: The original exception that caused the failure.
        tables_involved: Tuple of label names involved in the step.
    """

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        step_index: int,
        step_label: str,
        step_type: str,
        cause: Exception,
        tables_involved: tuple[str, ...] = (),
    ) -> None:
        self.step_index = step_index
        self.step_label = step_label
        self.step_type = step_type
        self.cause = cause
        self.tables_involved = tables_involved
        super().__init__(summary=summary, reason=reason, fix=fix)


# ====================================================================
# Pipeline step types
# ====================================================================


@dataclass(frozen=True)
class PipelineStepLog:
    """Log entry for a completed pipeline step.

    Records the outcome of each step for traceability (AC #3).

    Attributes:
        step_index: Zero-based position in execution order.
        step_type: Either "load" or "merge".
        label: Human-readable label for this step's output.
        input_labels: Empty tuple for load steps; (left, right) for merge steps.
        output_rows: Number of rows in the step's output table.
        output_columns: Column names in the step's output table.
        method_name: Merge method name (None for load steps).
        duration_ms: Execution time in milliseconds.
    """

    step_index: int
    step_type: str
    label: str
    input_labels: tuple[str, ...]
    output_rows: int
    output_columns: tuple[str, ...]
    method_name: str | None
    duration_ms: float


@dataclass(frozen=True)
class PipelineResult:
    """Immutable result of a population pipeline execution.

    Attributes:
        table: The final merged population table.
        assumption_chain: All merge assumptions with step context.
        step_log: Ordered log of all completed steps.
    """

    table: pa.Table
    assumption_chain: PipelineAssumptionChain
    step_log: tuple[PipelineStepLog, ...]


# ====================================================================
# Internal step definition types (NOT public API)
# ====================================================================


@dataclass(frozen=True)
class _LoadStepDef:
    """Internal definition for a data source loading step."""

    label: str
    loader: DataSourceLoader
    config: SourceConfig


@dataclass(frozen=True)
class _MergeStepDef:
    """Internal definition for a merge step."""

    label: str
    left_label: str
    right_label: str
    method: MergeMethod
    config: MergeConfig


_PipelineStepDef = _LoadStepDef | _MergeStepDef


# ====================================================================
# Population pipeline builder
# ====================================================================


class PopulationPipeline:
    """Composable builder for population generation pipelines.

    Provides a fluent API for chaining data source loading and
    statistical merging operations. Each step produces a labeled
    intermediate table. The final population is the output of
    the last merge step.

    The pipeline records every merge step's assumption for
    governance integration via ``PipelineAssumptionChain``.

    Example:
        >>> pipeline = (
        ...     PopulationPipeline(description="French household population 2024")
        ...     .add_source("income", loader=insee_loader, config=insee_config)
        ...     .add_source("vehicles", loader=sdes_loader, config=sdes_config)
        ...     .add_merge(
        ...         "income_vehicles",
        ...         left="income", right="vehicles",
        ...         method=ConditionalSamplingMethod(strata_columns=("income_bracket",)),
        ...         config=MergeConfig(seed=42),
        ...     )
        ... )
        >>> result = pipeline.execute()
        >>> result.table  # final merged population (pa.Table)
        >>> result.assumption_chain  # all merge assumptions
        >>> result.step_log  # execution trace
    """

    def __init__(self, *, description: str = "") -> None:
        """Initialize a new pipeline.

        Args:
            description: Human-readable description of the pipeline.
                Used in governance entries when set.
        """
        self._description = description
        self._steps: list[_PipelineStepDef] = []
        self._labels: set[str] = set()

    @property
    def description(self) -> str:
        """Human-readable description of the pipeline."""
        return self._description

    @property
    def step_count(self) -> int:
        """Number of steps in the pipeline."""
        return len(self._steps)

    @property
    def labels(self) -> frozenset[str]:
        """Set of all labels produced by steps in the pipeline."""
        return frozenset(self._labels)

    def add_source(
        self,
        label: str,
        loader: DataSourceLoader,
        config: SourceConfig,
    ) -> PopulationPipeline:
        """Add a data source loading step to the pipeline.

        Args:
            label: Human-readable label for the loaded table.
                Must be unique across all steps.
            loader: Data source loader to use.
            config: Configuration for the data source.

        Returns:
            ``self`` for fluent API chaining.

        Raises:
            PipelineConfigError: If label is empty or duplicate.
        """
        if not label or label.strip() == "":
            msg = "label must be a non-empty string"
            raise PipelineConfigError(
                summary="Invalid source label",
                reason=msg,
                fix="Provide a non-empty label for the source",
            )
        if label in self._labels:
            msg = f"Duplicate label {label!r}"
            raise PipelineConfigError(
                summary="Duplicate label",
                reason=msg,
                fix=f"Use a unique label (existing: {sorted(self._labels)})",
            )

        self._steps.append(_LoadStepDef(label=label, loader=loader, config=config))
        self._labels.add(label)
        return self

    def add_merge(
        self,
        label: str,
        left: str,
        right: str,
        method: MergeMethod,
        config: MergeConfig,
    ) -> PopulationPipeline:
        """Add a merge step to the pipeline.

        Args:
            label: Human-readable label for the merged table.
                Must be unique across all steps.
            left: Label of the left input table (must exist).
            right: Label of the right input table (must exist).
            method: Merge method to apply.
            config: Configuration for the merge operation.

        Returns:
            ``self`` for fluent API chaining.

        Raises:
            PipelineConfigError: If label is invalid, left/right don't exist,
                or left == right.
        """
        if not label or label.strip() == "":
            msg = "label must be a non-empty string"
            raise PipelineConfigError(
                summary="Invalid merge label",
                reason=msg,
                fix="Provide a non-empty label for the merge output",
            )
        if label in self._labels:
            msg = f"Duplicate label {label!r}"
            raise PipelineConfigError(
                summary="Duplicate label",
                reason=msg,
                fix=f"Use a unique label (existing: {sorted(self._labels)})",
            )
        if left not in self._labels:
            msg = f"Missing left label {left!r}"
            raise PipelineConfigError(
                summary="Merge references non-existent left table",
                reason=msg,
                fix=f"Add a source step with label {left!r} before this merge",
            )
        if right not in self._labels:
            msg = f"Missing right label {right!r}"
            raise PipelineConfigError(
                summary="Merge references non-existent right table",
                reason=msg,
                fix=f"Add a source step with label {right!r} before this merge",
            )
        if left == right:
            msg = f"left and right labels must be different, got {left!r}"
            raise PipelineConfigError(
                summary="Invalid merge: same left and right label",
                reason=msg,
                fix=f"Use two different labels (e.g., left={left!r}, right=other)",
            )

        self._steps.append(
            _MergeStepDef(
                label=label,
                left_label=left,
                right_label=right,
                method=method,
                config=config,
            )
        )
        self._labels.add(label)
        return self

    def execute(self) -> PipelineResult:
        """Execute the pipeline and return the final result.

        Executes all steps in insertion order. Load steps download
        data from sources. Merge steps apply statistical methods to
        combine tables. The final population is the output of the
        last merge step.

        Returns:
            ``PipelineResult`` containing the final table, assumption
            chain, and step log.

        Raises:
            PipelineConfigError: If pipeline has no merge steps.
            PipelineExecutionError: If any step fails during execution.
        """

        # Validate pipeline has at least one merge step
        has_merge = any(isinstance(step, _MergeStepDef) for step in self._steps)
        if not has_merge:
            msg = "Pipeline must have at least one merge step"
            raise PipelineConfigError(
                summary="Invalid pipeline configuration",
                reason=msg,
                fix="Add at least one merge step to the pipeline",
            )

        _logger.info(
            "event=pipeline_execute_start steps=%d description=%s",
            len(self._steps),
            self._description or "<no description>",
        )

        tables: dict[str, pa.Table] = {}
        assumptions: list[PipelineAssumptionRecord] = []
        step_logs: list[PipelineStepLog] = []
        step_index = 0

        start_time_total = time.monotonic()

        for step in self._steps:
            _logger.info(
                "event=pipeline_step_start step_index=%d step_type=%s label=%s",
                step_index,
                "load" if isinstance(step, _LoadStepDef) else "merge",
                step.label,
            )

            step_start = time.monotonic()

            try:
                if isinstance(step, _LoadStepDef):
                    # Execute load step — download returns (PopulationData, DatasetManifest)
                    pop_data, _manifest = step.loader.download(step.config)
                    table = pop_data.primary_table
                    tables[step.label] = table

                    output_columns = tuple(table.column_names)
                    step_logs.append(
                        PipelineStepLog(
                            step_index=step_index,
                            step_type="load",
                            label=step.label,
                            input_labels=(),
                            output_rows=table.num_rows,
                            output_columns=output_columns,
                            method_name=None,
                            duration_ms=(time.monotonic() - step_start) * 1000.0,
                        )
                    )

                elif isinstance(step, _MergeStepDef):
                    # Execute merge step
                    table_a = tables[step.left_label]
                    table_b = tables[step.right_label]

                    merge_result = step.method.merge(table_a, table_b, step.config)
                    tables[step.label] = merge_result.table

                    assumptions.append(
                        PipelineAssumptionRecord(
                            step_index=step_index,
                            step_label=step.label,
                            assumption=merge_result.assumption,
                        )
                    )

                    output_columns = tuple(merge_result.table.column_names)
                    step_logs.append(
                        PipelineStepLog(
                            step_index=step_index,
                            step_type="merge",
                            label=step.label,
                            input_labels=(step.left_label, step.right_label),
                            output_rows=merge_result.table.num_rows,
                            output_columns=output_columns,
                            method_name=step.method.name,
                            duration_ms=(time.monotonic() - step_start) * 1000.0,
                        )
                    )

            except Exception as exc:
                # Determine step type for error reporting
                step_type = "load" if isinstance(step, _LoadStepDef) else "merge"
                tables_involved = (
                    () if isinstance(step, _LoadStepDef) else (step.left_label, step.right_label)
                )

                _logger.error(
                    "event=pipeline_step_error step_index=%d label=%s error=%s",
                    step_index,
                    step.label,
                    type(exc).__name__,
                )

                raise PipelineExecutionError(
                    summary=f"Pipeline step {step_index} failed",
                    reason=f"{step_type.capitalize()} step {step.label!r} failed: {exc}",
                    fix=(
                        f"Check {step_type} configuration and data availability. "
                        f"Tables involved: {tables_involved}"
                    ),
                    step_index=step_index,
                    step_label=step.label,
                    step_type=step_type,
                    cause=exc,
                    tables_involved=tables_involved,
                ) from exc

            _logger.info(
                "event=pipeline_step_complete step_index=%d label=%s rows=%d cols=%d duration_ms=%.2f",
                step_index,
                step.label,
                tables[step.label].num_rows,
                len(tables[step.label].column_names),
                step_logs[-1].duration_ms,
            )

            step_index += 1

        # Find the last merge step in insertion order
        last_merge_step = None
        for step in reversed(self._steps):
            if isinstance(step, _MergeStepDef):
                last_merge_step = step
                break

        if last_merge_step is None:
            # This should never happen due to the has_merge check above
            msg = "No merge step found in pipeline"
            raise PipelineConfigError(
                summary="Invalid pipeline configuration",
                reason=msg,
                fix="Add at least one merge step to the pipeline",
            )

        final_table = tables[last_merge_step.label]

        # Build assumption chain
        assumption_chain = PipelineAssumptionChain(
            records=tuple(assumptions),
            pipeline_description=self._description,
        )

        total_duration_ms = (time.monotonic() - start_time_total) * 1000.0

        _logger.info(
            "event=pipeline_execute_complete total_steps=%d final_rows=%d assumptions=%d duration_ms=%.2f",
            step_index,
            final_table.num_rows,
            len(assumptions),
            total_duration_ms,
        )

        return PipelineResult(
            table=final_table,
            assumption_chain=assumption_chain,
            step_log=tuple(step_logs),
        )
