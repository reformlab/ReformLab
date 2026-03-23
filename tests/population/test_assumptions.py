# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for pipeline assumption recording and governance integration.

Implements Story 11.6, FR41.
"""

from __future__ import annotations

import dataclasses

import pytest

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
    PipelineAssumptionRecord,
)
from reformlab.population.methods.base import MergeAssumption


class TestPipelineAssumptionRecord:
    """Test frozen dataclass for single assumption with execution context."""

    def test_frozen_dataclass(self) -> None:
        """Record is frozen and holds all fields."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42, "matches": 100},
        )
        record = PipelineAssumptionRecord(
            step_index=0,
            step_label="income_vehicles",
            assumption=assumption,
        )
        assert record.step_index == 0
        assert record.step_label == "income_vehicles"
        assert record.assumption == assumption

        # Frozen - cannot modify
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.step_index = 1  # type: ignore[misc]

    def test_negative_step_index_raises_value_error(self) -> None:
        """Negative step_index is invalid."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        with pytest.raises(ValueError, match="step_index must be >= 0"):
            PipelineAssumptionRecord(
                step_index=-1,
                step_label="income_vehicles",
                assumption=assumption,
            )

    def test_empty_step_label_raises_value_error(self) -> None:
        """Empty step_label is invalid."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        with pytest.raises(ValueError, match="step_label must be a non-empty string"):
            PipelineAssumptionRecord(
                step_index=0,
                step_label="",
                assumption=assumption,
            )

    def test_whitespace_only_step_label_raises_value_error(self) -> None:
        """Whitespace-only step_label is invalid."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        with pytest.raises(ValueError, match="step_label must be a non-empty string"):
            PipelineAssumptionRecord(
                step_index=0,
                step_label="   ",
                assumption=assumption,
            )


class TestPipelineAssumptionChain:
    """Test frozen dataclass for complete assumption chain from pipeline."""

    def test_frozen_dataclass(self) -> None:
        """Chain is frozen and holds all fields."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={"iterations": 10},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="population", assumption=assumption2)

        chain = PipelineAssumptionChain(
            records=(record1, record2),
            pipeline_description="French household population 2024",
        )

        assert len(chain.records) == 2
        assert chain.records[0] == record1
        assert chain.records[1] == record2
        assert chain.pipeline_description == "French household population 2024"

        # Frozen - cannot modify
        with pytest.raises(dataclasses.FrozenInstanceError):
            chain.records = ()  # type: ignore[misc]

    def test_empty_records_tuple_is_valid(self) -> None:
        """Empty records tuple is valid (no merge steps = no assumptions)."""
        chain = PipelineAssumptionChain(records=())
        assert len(chain.records) == 0
        assert chain.pipeline_description == ""

    def test_records_coerced_to_tuple_in_post_init(self) -> None:
        """Records list is converted to tuple for immutability."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)

        # Pass list - should be coerced to tuple
        chain = PipelineAssumptionChain(records=[record])
        assert isinstance(chain.records, tuple)
        assert len(chain.records) == 1

    def test_pipeline_description_defaults_to_empty_string(self) -> None:
        """pipeline_description has default empty string."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)

        chain = PipelineAssumptionChain(records=(record,))
        assert chain.pipeline_description == ""

    def test_len_returns_record_count(self) -> None:
        """len(chain) returns number of records."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="population", assumption=assumption2)

        chain = PipelineAssumptionChain(records=(record1, record2))
        assert len(chain) == 2

    def test_iterable_over_records(self) -> None:
        """Chain is iterable over records."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="population", assumption=assumption2)

        chain = PipelineAssumptionChain(records=(record1, record2))
        records_list = list(chain)
        assert records_list == [record1, record2]

    def test_ordered_records_preserved(self) -> None:
        """Records maintain insertion order."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        assumption3 = MergeAssumption(
            method_name="conditional",
            statement="Stratum-based sampling",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="step1", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="step2", assumption=assumption2)
        record3 = PipelineAssumptionRecord(step_index=2, step_label="step3", assumption=assumption3)

        chain = PipelineAssumptionChain(records=(record1, record2, record3))
        assert list(chain) == [record1, record2, record3]


class TestPipelineAssumptionChainGovernanceEntries:
    """Test to_governance_entries() method for governance integration."""

    def test_returns_list_of_dicts(self) -> None:
        """to_governance_entries() returns list of dict entries."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42, "matches": 100},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(records=(record,))

        entries = chain.to_governance_entries()
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert isinstance(entries[0], dict)

    def test_each_dict_has_required_fields(self) -> None:
        """Each entry has key, value, source, is_default fields."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(records=(record,))

        entries = chain.to_governance_entries()
        entry = entries[0]

        assert "key" in entry
        assert "value" in entry
        assert "source" in entry
        assert "is_default" in entry

    def test_is_default_is_false_for_all_entries(self) -> None:
        """is_default is always False (assumptions are explicit)."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="step1", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="step2", assumption=assumption2)
        chain = PipelineAssumptionChain(records=(record1, record2))

        entries = chain.to_governance_entries()
        assert all(entry["is_default"] is False for entry in entries)

    def test_default_source_is_population_pipeline(self) -> None:
        """Default source label is 'population_pipeline'."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(records=(record,))

        entries = chain.to_governance_entries()
        assert entries[0]["source"] == "population_pipeline"

    def test_custom_source_label_is_respected(self) -> None:
        """Custom source_label parameter overrides default."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(records=(record,))

        entries = chain.to_governance_entries(source_label="custom_source")
        assert entries[0]["source"] == "custom_source"

    def test_each_entry_contains_pipeline_step_context(self) -> None:
        """Each entry's value dict contains pipeline_step_index and pipeline_step_label."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={"iterations": 10},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="population", assumption=assumption2)
        chain = PipelineAssumptionChain(records=(record1, record2))

        entries = chain.to_governance_entries()

        assert entries[0]["value"]["pipeline_step_index"] == 0
        assert entries[0]["value"]["pipeline_step_label"] == "income_vehicles"
        assert entries[1]["value"]["pipeline_step_index"] == 1
        assert entries[1]["value"]["pipeline_step_label"] == "population"

    def test_pipeline_description_in_entry_when_set(self) -> None:
        """pipeline_description appears in each entry's value when set."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(
            records=(record,),
            pipeline_description="French household population 2024",
        )

        entries = chain.to_governance_entries()
        assert entries[0]["value"]["pipeline_description"] == "French household population 2024"

    def test_pipeline_description_not_in_entry_when_empty(self) -> None:
        """pipeline_description does NOT appear in entry when empty string."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(
            records=(record,),
            pipeline_description="",
        )

        entries = chain.to_governance_entries()
        assert "pipeline_description" not in entries[0]["value"]

    def test_entries_ordered_by_step_index(self) -> None:
        """Entries are returned in step_index order."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        assumption3 = MergeAssumption(
            method_name="conditional",
            statement="Stratum-based sampling",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="step1", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="step2", assumption=assumption2)
        record3 = PipelineAssumptionRecord(step_index=2, step_label="step3", assumption=assumption3)

        chain = PipelineAssumptionChain(records=(record1, record2, record3))
        entries = chain.to_governance_entries()

        assert entries[0]["value"]["pipeline_step_index"] == 0
        assert entries[1]["value"]["pipeline_step_index"] == 1
        assert entries[2]["value"]["pipeline_step_index"] == 2

    def test_each_entry_key_matches_merge_method_name_pattern(self) -> None:
        """Each entry's key matches 'merge_{method_name}' pattern."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="step1", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="step2", assumption=assumption2)
        chain = PipelineAssumptionChain(records=(record1, record2))

        entries = chain.to_governance_entries()
        assert entries[0]["key"] == "merge_uniform"
        assert entries[1]["key"] == "merge_ipf"

    def test_duplicate_method_names_produce_duplicate_keys(self) -> None:
        """Same method used multiple times produces same key (intentional)."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="First uniform merge",
            details={"seed": 42},
        )
        assumption2 = MergeAssumption(
            method_name="uniform",
            statement="Second uniform merge",
            details={"seed": 43},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="step1", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="step2", assumption=assumption2)
        chain = PipelineAssumptionChain(records=(record1, record2))

        entries = chain.to_governance_entries()
        # Both entries have the same key - this is intentional
        assert entries[0]["key"] == "merge_uniform"
        assert entries[1]["key"] == "merge_uniform"
        # But they are distinguished by pipeline_step_index
        assert entries[0]["value"]["pipeline_step_index"] == 0
        assert entries[1]["value"]["pipeline_step_index"] == 1

    def test_entry_value_contains_merge_details(self) -> None:
        """Entry value dict contains all details from MergeAssumption."""
        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42, "matches": 100, "strata": ["low", "high"]},
        )
        record = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption)
        chain = PipelineAssumptionChain(records=(record,))

        entries = chain.to_governance_entries()
        value = entries[0]["value"]

        # Original details are included
        assert value["seed"] == 42
        assert value["matches"] == 100
        assert value["strata"] == ["low", "high"]
        # Plus method and statement from MergeAssumption.to_governance_entry()
        assert value["method"] == "uniform"
        assert value["statement"] == "Uniform random matching"

    def test_multiple_records_produce_multiple_entries(self) -> None:
        """Chain with 2 records produces 2 entries."""
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="step1", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="step2", assumption=assumption2)
        chain = PipelineAssumptionChain(records=(record1, record2))

        entries = chain.to_governance_entries()
        assert len(entries) == 2


class TestPipelineAssumptionChainIntegrationWithManifest:
    """Test integration with governance manifest validation."""

    def test_governance_entries_pass_manifest_validation(self) -> None:
        """Given governance entries from chain, when validated against
        RunManifest assumptions schema, then all entries pass validation."""
        from typing import cast

        from reformlab.governance.manifest import (
            AssumptionEntry,
            RunManifest,
        )

        # Create assumption chain with 2 records
        assumption1 = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42, "matches": 100},
        )
        assumption2 = MergeAssumption(
            method_name="ipf",
            statement="IPF reweighting",
            details={"iterations": 10, "converged": True},
        )
        record1 = PipelineAssumptionRecord(step_index=0, step_label="income_vehicles", assumption=assumption1)
        record2 = PipelineAssumptionRecord(step_index=1, step_label="population", assumption=assumption2)
        chain = PipelineAssumptionChain(
            records=(record1, record2),
            pipeline_description="French household population 2024",
        )

        # Get governance entries
        governance_entries = chain.to_governance_entries()
        assert len(governance_entries) == 2

        # Construct a minimal RunManifest with the pipeline entries as assumptions
        manifest = RunManifest(
            manifest_id="test-pipeline-001",
            created_at="2026-01-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="v1",
            assumptions=[cast(AssumptionEntry, e) for e in governance_entries],
        )

        # Verify manifest structure
        assert manifest.manifest_id == "test-pipeline-001"
        assert len(manifest.assumptions) == 2

        # Verify each assumption entry structure
        for entry in manifest.assumptions:
            assert isinstance(entry["key"], str) and entry["key"] != ""
            assert isinstance(entry["value"], dict)
            assert isinstance(entry["source"], str) and entry["source"] != ""
            assert isinstance(entry["is_default"], bool)

    def test_manifest_entries_contain_pipeline_context(self) -> None:
        """Manifest assumptions contain pipeline step context."""
        from typing import cast

        from reformlab.governance.manifest import (
            AssumptionEntry,
            RunManifest,
        )

        assumption = MergeAssumption(
            method_name="uniform",
            statement="Uniform random matching",
            details={"seed": 42},
        )
        record = PipelineAssumptionRecord(
            step_index=0,
            step_label="income_vehicles",
            assumption=assumption,
        )
        chain = PipelineAssumptionChain(
            records=(record,),
            pipeline_description="French household population 2024",
        )

        governance_entries = chain.to_governance_entries()
        manifest = RunManifest(
            manifest_id="test-pipeline-002",
            created_at="2026-01-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="v1",
            assumptions=[cast(AssumptionEntry, governance_entries[0])],
        )

        entry = manifest.assumptions[0]
        assert entry["value"]["pipeline_step_index"] == 0
        assert entry["value"]["pipeline_step_label"] == "income_vehicles"
        assert entry["value"]["pipeline_description"] == "French household population 2024"

