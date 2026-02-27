"""Tests for lineage graph query and validation.

Test coverage:
- LineageGraph creation and properties
- Lineage extraction from manifests
- Parent/child traversal methods
- Bidirectional lineage validation
- Integrity error detection
"""

from __future__ import annotations

import pytest

from reformlab.governance import (
    LineageGraph,
    LineageIntegrityError,
    RunManifest,
    get_lineage,
    validate_lineage,
)


class TestLineageGraph:
    """Test LineageGraph creation and query methods."""

    def test_create_root_lineage_graph(self) -> None:
        """LineageGraph can represent a root manifest (no parent)."""
        graph = LineageGraph(
            manifest_id="root-manifest-001",
            parent_id=None,
            child_ids={2025: "child-2025", 2026: "child-2026"},
        )
        assert graph.manifest_id == "root-manifest-001"
        assert graph.parent_id is None
        assert graph.child_ids == {2025: "child-2025", 2026: "child-2026"}

    def test_create_child_lineage_graph(self) -> None:
        """LineageGraph can represent a child manifest (has parent, no children)."""
        graph = LineageGraph(
            manifest_id="child-manifest-001",
            parent_id="parent-manifest-001",
            child_ids={},
        )
        assert graph.manifest_id == "child-manifest-001"
        assert graph.parent_id == "parent-manifest-001"
        assert graph.child_ids == {}

    def test_child_ids_are_detached_on_construction(self) -> None:
        """LineageGraph detaches child_ids from caller-owned dictionaries."""
        child_ids = {2025: "child-2025"}
        graph = LineageGraph(
            manifest_id="root-manifest-001",
            parent_id=None,
            child_ids=child_ids,
        )
        child_ids[2026] = "child-2026"
        assert graph.child_ids == {2025: "child-2025"}

    def test_is_root_property(self) -> None:
        """is_root returns True when parent_id is None."""
        root_graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000007",
            parent_id=None,
            child_ids={},
        )
        assert root_graph.is_root is True

        child_graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000004",
            parent_id="00000000-0000-0000-0000-000000000005",
            child_ids={},
        )
        assert child_graph.is_root is False

    def test_is_leaf_property(self) -> None:
        """is_leaf returns True when child_ids is empty."""
        leaf_graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000006",
            parent_id="00000000-0000-0000-0000-000000000005",
            child_ids={},
        )
        assert leaf_graph.is_leaf is True

        parent_graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000005",
            parent_id=None,
            child_ids={2025: "00000000-0000-0000-0000-000000000004"},
        )
        assert parent_graph.is_leaf is False

    def test_get_parent_returns_parent_id(self) -> None:
        """get_parent() returns parent manifest ID."""
        graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000004",
            parent_id="00000000-0000-0000-0000-000000000011",
            child_ids={},
        )
        assert graph.get_parent() == "00000000-0000-0000-0000-000000000011"

    def test_get_parent_returns_none_for_root(self) -> None:
        """get_parent() returns None for root manifests."""
        graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000007",
            parent_id=None,
            child_ids={},
        )
        assert graph.get_parent() is None

    def test_get_children_returns_child_mapping(self) -> None:
        """get_children() returns year-to-child-ID mapping."""
        graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000005",
            parent_id=None,
            child_ids={2024: "child-2024", 2025: "child-2025", 2026: "child-2026"},
        )
        children = graph.get_children()
        assert children == {2024: "child-2024", 2025: "child-2025", 2026: "child-2026"}

    def test_get_children_returns_copy(self) -> None:
        """get_children() returns an independent copy."""
        graph = LineageGraph(
            manifest_id="00000000-0000-0000-0000-000000000005",
            parent_id=None,
            child_ids={2025: "00000000-0000-0000-0000-000000000004"},
        )
        children = graph.get_children()
        children[2026] = "child-002"  # Mutate returned dict
        # Original should be unchanged
        assert graph.child_ids == {2025: "00000000-0000-0000-0000-000000000004"}


class TestGetLineage:
    """Test get_lineage() factory function."""

    def test_get_lineage_from_root_manifest(self) -> None:
        """get_lineage() extracts lineage from a root manifest."""
        manifest = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000001",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",  # Root manifest
            child_manifests={
                2025: "00000000-0000-0000-0000-000000000002",
                2026: "00000000-0000-0000-0000-000000000003",
            },
        )
        lineage = get_lineage(manifest)
        assert lineage.manifest_id == "00000000-0000-0000-0000-000000000001"
        assert lineage.parent_id is None
        assert lineage.child_ids == {
            2025: "00000000-0000-0000-0000-000000000002",
            2026: "00000000-0000-0000-0000-000000000003",
        }
        assert lineage.is_root is True
        assert lineage.is_leaf is False

    def test_get_lineage_from_child_manifest(self) -> None:
        """get_lineage() extracts lineage from a child manifest."""
        manifest = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000002",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="00000000-0000-0000-0000-000000000010",
            child_manifests={},  # Leaf manifest
        )
        lineage = get_lineage(manifest)
        assert lineage.manifest_id == "00000000-0000-0000-0000-000000000002"
        assert lineage.parent_id == "00000000-0000-0000-0000-000000000010"
        assert lineage.child_ids == {}
        assert lineage.is_root is False
        assert lineage.is_leaf is True

    def test_get_lineage_from_orphan_manifest(self) -> None:
        """get_lineage() handles manifests with no parent or children."""
        manifest = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000008",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={},
        )
        lineage = get_lineage(manifest)
        assert lineage.manifest_id == "00000000-0000-0000-0000-000000000008"
        assert lineage.parent_id is None
        assert lineage.child_ids == {}
        assert lineage.is_root is True
        assert lineage.is_leaf is True


class TestValidateLineage:
    """Test validate_lineage() bidirectional integrity validation."""

    def test_valid_lineage_passes_validation(self) -> None:
        """validate_lineage() succeeds for consistent parent-child links."""
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={
                2025: "00000000-0000-0000-0000-000000000002",
                2026: "00000000-0000-0000-0000-000000000003",
            },
        )
        children = {
            2025: RunManifest(
                manifest_id="00000000-0000-0000-0000-000000000002",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            ),
            2026: RunManifest(
                manifest_id="00000000-0000-0000-0000-000000000003",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            ),
        }
        # Should not raise
        validate_lineage(parent, children)

    def test_empty_children_passes_validation(self) -> None:
        """validate_lineage() succeeds for parent with no children."""
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={},
        )
        children: dict[int, RunManifest] = {}
        # Should not raise
        validate_lineage(parent, children)

    def test_parent_references_missing_child(self) -> None:
        """validate_lineage() fails when parent references a missing child."""
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={
                2025: "00000000-0000-0000-0000-000000000002",
                2026: "00000000-0000-0000-0000-000000000003",
            },
        )
        children = {
            2025: RunManifest(
                manifest_id="00000000-0000-0000-0000-000000000002",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            ),
            # Missing year 2026
        }
        with pytest.raises(
            LineageIntegrityError,
            match=(
                r"Parent manifest .* references child for year 2026 .* "
                r"but no child manifest was provided"
            ),
        ):
            validate_lineage(parent, children)

    def test_child_manifest_id_mismatch(self) -> None:
        """validate_lineage() fails when child ID doesn't match parent."""
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={2025: "00000000-0000-0000-0000-000000000020"},
        )
        children = {
            2025: RunManifest(
                manifest_id="00000000-0000-0000-0000-000000000021",  # Mismatch
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            ),
        }
        with pytest.raises(
            LineageIntegrityError,
            match=(
                r"Parent manifest .* references child for year 2025 with ID "
                r"'00000000-0000-0000-0000-000000000020', but provided child has ID "
                r"'00000000-0000-0000-0000-000000000021'"
            ),
        ):
            validate_lineage(parent, children)

    def test_child_provided_but_not_in_parent(self) -> None:
        """validate_lineage() fails when child provided but not in parent."""
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={2025: "00000000-0000-0000-0000-000000000002"},
        )
        children = {
            2025: RunManifest(
                manifest_id="00000000-0000-0000-0000-000000000002",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            ),
            2026: RunManifest(  # Extra child not referenced by parent
                manifest_id="00000000-0000-0000-0000-000000000003",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            ),
        }
        with pytest.raises(
            LineageIntegrityError,
            match=(
                r"Child manifest .* provided for year 2026, but parent "
                r"manifest .* has no child reference for that year"
            ),
        ):
            validate_lineage(parent, children)

    def test_child_parent_id_mismatch(self) -> None:
        """validate_lineage() fails when child's parent ID doesn't match."""
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={2025: "00000000-0000-0000-0000-000000000002"},
        )
        children = {
            2025: RunManifest(
                manifest_id="00000000-0000-0000-0000-000000000002",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000022",  # Mismatch
                child_manifests={},
            ),
        }
        with pytest.raises(
            LineageIntegrityError,
            match=(
                r"Child manifest .* for year 2025 has "
                r"parent_manifest_id='00000000-0000-0000-0000-000000000022', "
                r"but expected '00000000-0000-0000-0000-000000000010'"
            ),
        ):
            validate_lineage(parent, children)

    def test_ten_year_projection_lineage(self) -> None:
        """validate_lineage() handles 10-year projection shape (AC-1)."""
        years = list(range(2024, 2034))  # 2024-2033 (10 years)
        # Generate valid UUID for each year
        child_uuids = {
            year: f"00000000-0000-0000-0000-{year:012d}"
            for year in years
        }
        parent = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000010",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests=child_uuids,
        )
        children = {
            year: RunManifest(
                manifest_id=child_uuids[year],
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parent_manifest_id="00000000-0000-0000-0000-000000000010",
                child_manifests={},
            )
            for year in years
        }
        # Should not raise
        validate_lineage(parent, children)

        # Verify parent manifest has 10 child references
        assert len(parent.child_manifests) == 10
        assert list(parent.child_manifests.keys()) == years


class TestLineageIntegrationWithManifest:
    """Test lineage fields integrate correctly with RunManifest."""

    def test_manifest_with_lineage_fields_serializes_to_json(self) -> None:
        """Manifest with lineage fields serializes to valid JSON."""
        manifest = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000099",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="00000000-0000-0000-0000-000000000010",
            child_manifests={2025: "00000000-0000-0000-0000-000000000002"},
        )
        json_str = manifest.to_json()
        assert "00000000-0000-0000-0000-000000000010" in json_str
        assert "00000000-0000-0000-0000-000000000002" in json_str

    def test_manifest_with_lineage_fields_deserializes_from_json(self) -> None:
        """Manifest with lineage fields can be deserialized from JSON."""
        manifest = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000099",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="00000000-0000-0000-0000-000000000010",
            child_manifests={
                2025: "00000000-0000-0000-0000-000000000002",
                2026: "00000000-0000-0000-0000-000000000003",
            },
        )
        json_str = manifest.to_json()
        restored = RunManifest.from_json(json_str)
        assert restored.parent_manifest_id == "00000000-0000-0000-0000-000000000010"
        assert restored.child_manifests == {
            2025: "00000000-0000-0000-0000-000000000002",
            2026: "00000000-0000-0000-0000-000000000003",
        }

    def test_manifest_lineage_fields_included_in_integrity_hash(self) -> None:
        """Lineage fields are included in integrity hash computation."""
        manifest1 = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000099",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="",
            child_manifests={},
        )
        manifest2 = RunManifest(
            manifest_id="00000000-0000-0000-0000-000000000099",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            # Different lineage:
            parent_manifest_id="00000000-0000-0000-0000-000000000010",
            child_manifests={},
        )
        # Different lineage should produce different hashes
        assert manifest1.compute_integrity_hash() != manifest2.compute_integrity_hash()
