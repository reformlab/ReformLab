# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Assumption recording for governance integration.

Bridges population pipeline merge assumptions to the governance layer's
``RunManifest.assumptions`` format. Provides structured records for
each merge step in a pipeline, with execution context (step index, step label)
that enables full traceability from raw data sources to final merged population.

Implements Story 11.6, FR41.

The bridge works as follows:
- ``PipelineAssumptionRecord`` wraps a single merge assumption with step context
- ``PipelineAssumptionChain`` collects all assumptions from a pipeline execution
- ``to_governance_entries()`` produces dicts matching ``AssumptionEntry`` format
- These dicts are appended directly to ``RunManifest.assumptions``

Note: This module does NOT use ``capture_assumptions()`` from
``governance/capture.py`` — that function expects flat key-value pairs,
while merge assumptions are structured with nested metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from reformlab.population.methods.base import MergeAssumption

# ====================================================================
# Pipeline assumption types
# ====================================================================


@dataclass(frozen=True)
class PipelineAssumptionRecord:
    """Records a single assumption from a pipeline step with execution context.

    Wraps a ``MergeAssumption`` produced by a merge method and adds pipeline
    execution context (step index, step label) that enables traceability
    back to the specific merge operation in the pipeline.

    Attributes:
        step_index: Zero-based index of the merge step in the pipeline.
        step_label: Human-readable label for the step's output table.
        assumption: The ``MergeAssumption`` produced by the merge method.
    """

    step_index: int
    step_label: str
    assumption: MergeAssumption

    def __post_init__(self) -> None:
        if self.step_index < 0:
            msg = f"step_index must be >= 0, got {self.step_index}"
            raise ValueError(msg)
        if not self.step_label or self.step_label.strip() == "":
            msg = "step_label must be a non-empty string"
            raise ValueError(msg)


@dataclass(frozen=True)
class PipelineAssumptionChain:
    """Complete assumption chain from a pipeline execution.

    Collects all merge assumptions from a pipeline run and provides
    a single method to convert them to governance-compatible format
    for appending to ``RunManifest.assumptions``.

    The chain preserves execution order, so assumptions are traceable
    by step index and label.

    Attributes:
        records: Ordered tuple of assumption records from each merge step.
        pipeline_description: Human-readable description of the pipeline.
    """

    records: tuple[PipelineAssumptionRecord, ...]
    pipeline_description: str = ""

    def __post_init__(self) -> None:
        # Coerce to tuple to ensure immutability (caller may pass a list)
        # Deep-copy is unnecessary since all contents are frozen dataclasses
        object.__setattr__(self, "records", tuple(self.records))

    def to_governance_entries(self, *, source_label: str = "population_pipeline") -> list[dict[str, Any]]:
        """Convert all assumptions to governance-compatible AssumptionEntry format.

        Each entry is a dict with keys: ``key``, ``value``, ``source``, ``is_default``.
        The ``value`` dict includes pipeline step context (step_index, step_label).

        The returned list can be directly appended to ``RunManifest.assumptions``.
        Due to mypy strict mode, callers should use ``cast(AssumptionEntry, entry)``
        when appending to typed manifest fields.

        Args:
            source_label: Label for the ``source`` field in each entry.
                Defaults to ``"population_pipeline"``.

        Returns:
            List of assumption entry dicts, ordered by step_index.

        Note on key uniqueness:
            The ``key`` field is ``merge_{method_name}`` inherited from
            ``MergeAssumption.to_governance_entry()``. When the same method
            is used multiple times (e.g., two uniform merges), multiple entries
            share the same ``key`` — this is intentional and accepted by
            ``RunManifest`` validation. Downstream consumers should use
            ``pipeline_step_index`` within each entry's ``value`` to
            distinguish entries.
        """
        entries: list[dict[str, Any]] = []
        for record in self.records:
            entry = record.assumption.to_governance_entry(
                source_label=source_label,
            )
            # Enrich with pipeline step context
            entry["value"]["pipeline_step_index"] = record.step_index
            entry["value"]["pipeline_step_label"] = record.step_label
            if self.pipeline_description:
                entry["value"]["pipeline_description"] = self.pipeline_description
            entries.append(entry)
        return entries

    def __len__(self) -> int:
        """Return number of assumption records."""
        return len(self.records)

    def __iter__(self) -> Iterator[PipelineAssumptionRecord]:
        """Iterate over assumption records."""
        return iter(self.records)
