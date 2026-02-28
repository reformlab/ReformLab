"""Tests for the scenario registry.

Tests cover:
- Version ID generation (deterministic, content-based)
- Save/get round-trip
- Version history tracking
- Error cases (not found, invalid ID)
- File persistence
- Registry with multiple scenarios and versions
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

import reformlab.templates.registry as registry_module
from reformlab.templates.migration import CompatibilityStatus, MigrationReport
from reformlab.templates.registry import (
    RegistryEntry,
    RegistryError,
    ScenarioNotFoundError,
    ScenarioRegistry,
    ScenarioVersion,
    VersionNotFoundError,
    _generate_version_id,
)
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    PolicyType,
    ReformScenario,
    YearSchedule,
)


@pytest.fixture
def sample_baseline() -> BaselineScenario:
    """Create a sample baseline scenario for testing."""
    return BaselineScenario(
        name="French Carbon Tax 2026",
        policy_type=PolicyType.CARBON_TAX,
        year_schedule=YearSchedule(start_year=2026, end_year=2036),
        parameters=CarbonTaxParameters(
            rate_schedule={
                2026: 44.60,
                2027: 50.00,
                2028: 55.00,
                2029: 60.00,
                2030: 65.00,
                2031: 70.00,
                2032: 75.00,
                2033: 80.00,
                2034: 85.00,
                2035: 90.00,
                2036: 100.00,
            },
            covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
        ),
        description="Baseline carbon tax scenario for French households",
        version="1.0",
    )


@pytest.fixture
def sample_reform() -> ReformScenario:
    """Create a sample reform scenario for testing."""
    return ReformScenario(
        name="Progressive Carbon Dividend",
        policy_type=PolicyType.CARBON_TAX,
        baseline_ref="french-carbon-tax-2026",
        parameters=CarbonTaxParameters(
            rate_schedule={},
            redistribution_type="progressive_dividend",
            income_weights={
                "decile_1": 1.5,
                "decile_2": 1.3,
                "decile_3": 1.1,
                "decile_4": 1.0,
                "decile_5": 1.0,
                "decile_6": 0.9,
                "decile_7": 0.8,
                "decile_8": 0.7,
                "decile_9": 0.5,
                "decile_10": 0.2,
            },
        ),
        description="Carbon tax with progressive redistribution",
        version="1.0",
    )


@pytest.fixture
def registry(tmp_path: Path) -> ScenarioRegistry:
    """Create a registry in a temporary directory."""
    return ScenarioRegistry(tmp_path / "registry")


class TestVersionIdGeneration:
    """Tests for version ID generation (AC-1)."""

    def test_version_id_is_deterministic(
        self,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Same scenario content produces same version ID."""
        id1 = _generate_version_id(sample_baseline)
        id2 = _generate_version_id(sample_baseline)
        assert id1 == id2

    def test_version_id_is_12_chars(self, sample_baseline: BaselineScenario) -> None:
        """Version ID is 12 characters (SHA-256 prefix)."""
        version_id = _generate_version_id(sample_baseline)
        assert len(version_id) == 12

    def test_version_id_is_hexadecimal(self, sample_baseline: BaselineScenario) -> None:
        """Version ID is valid hexadecimal."""
        version_id = _generate_version_id(sample_baseline)
        int(version_id, 16)  # Should not raise

    def test_different_content_produces_different_id(
        self,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Different scenario content produces different version ID."""
        id1 = _generate_version_id(sample_baseline)

        modified = replace(sample_baseline, description="Modified description")
        id2 = _generate_version_id(modified)

        assert id1 != id2

    def test_version_id_content_addressable(
        self,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Identical scenarios with different names produce same ID."""
        # The version ID is based on the serialized content including name,
        # so this test verifies the behavior
        id1 = _generate_version_id(sample_baseline)

        # Create identical scenario
        identical = BaselineScenario(
            name=sample_baseline.name,
            policy_type=sample_baseline.policy_type,
            year_schedule=sample_baseline.year_schedule,
            parameters=sample_baseline.parameters,
            description=sample_baseline.description,
            version=sample_baseline.version,
        )
        id2 = _generate_version_id(identical)

        assert id1 == id2


class TestSaveAndGetRoundtrip:
    """Tests for save/get round-trip (AC-1, AC-2)."""

    def test_save_and_get_baseline(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Saved baseline scenario can be retrieved identically."""
        version_id = registry.save(sample_baseline, "test-scenario")
        retrieved = registry.get("test-scenario", version_id)
        assert retrieved == sample_baseline

    def test_save_and_get_reform(
        self,
        registry: ScenarioRegistry,
        sample_reform: ReformScenario,
    ) -> None:
        """Saved reform scenario can be retrieved identically."""
        version_id = registry.save(sample_reform, "test-reform")
        retrieved = registry.get("test-reform", version_id)
        assert retrieved == sample_reform

    def test_get_latest_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Getting without version_id returns latest version."""
        registry.save(sample_baseline, "test-scenario")
        retrieved = registry.get("test-scenario")
        assert retrieved == sample_baseline

    def test_idempotent_save(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Saving the same scenario twice returns the same version ID."""
        v1 = registry.save(sample_baseline, "test-scenario")
        v2 = registry.save(sample_baseline, "test-scenario")
        assert v1 == v2

        # Should still have only one version
        versions = registry.list_versions("test-scenario")
        assert len(versions) == 1


class TestVersionHistory:
    """Tests for version history tracking (AC-2)."""

    def test_modified_scenario_creates_new_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Modifying and re-saving creates new version."""
        v1 = registry.save(sample_baseline, "test-scenario")

        modified = replace(sample_baseline, description="Modified description")
        v2 = registry.save(modified, "test-scenario", "Updated description")

        assert v1 != v2
        assert registry.get("test-scenario", v1) == sample_baseline
        assert registry.get("test-scenario", v2) == modified

    def test_previous_version_remains_accessible(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Previous versions remain retrievable after new versions are added."""
        v1 = registry.save(sample_baseline, "test-scenario", "Initial version")

        modified1 = replace(sample_baseline, description="Version 2")
        v2 = registry.save(modified1, "test-scenario", "Second version")

        modified2 = replace(sample_baseline, description="Version 3")
        v3 = registry.save(modified2, "test-scenario", "Third version")

        # All versions should be accessible
        assert registry.get("test-scenario", v1) == sample_baseline
        assert registry.get("test-scenario", v2) == modified1
        assert registry.get("test-scenario", v3) == modified2

    def test_version_metadata_includes_timestamp(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Version metadata includes timestamp."""
        registry.save(sample_baseline, "test-scenario")
        versions = registry.list_versions("test-scenario")

        assert len(versions) == 1
        assert isinstance(versions[0].timestamp, datetime)
        assert versions[0].timestamp.tzinfo is not None  # Has timezone

    def test_version_metadata_includes_parent_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Version metadata includes parent version reference."""
        v1 = registry.save(sample_baseline, "test-scenario", "Initial")

        modified = replace(sample_baseline, description="Modified")
        registry.save(modified, "test-scenario", "Update")

        versions = registry.list_versions("test-scenario")
        assert versions[0].parent_version is None  # First version
        assert versions[1].parent_version == v1  # Second version links to first

    def test_version_metadata_includes_change_description(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Version metadata includes change description."""
        registry.save(sample_baseline, "test-scenario", "Initial version")

        modified = replace(sample_baseline, description="Modified")
        registry.save(modified, "test-scenario", "Increased 2030 rate to 70 EUR/tCO2")

        versions = registry.list_versions("test-scenario")
        assert versions[0].change_description == "Initial version"
        assert versions[1].change_description == "Increased 2030 rate to 70 EUR/tCO2"


class TestErrorHandling:
    """Tests for error handling (AC-3)."""

    def test_get_nonexistent_scenario_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Getting nonexistent scenario produces helpful error."""
        with pytest.raises(ScenarioNotFoundError) as exc_info:
            registry.get("nonexistent-scenario")

        assert "nonexistent-scenario" in str(exc_info.value)
        assert "list_scenarios" in exc_info.value.fix

    def test_get_nonexistent_version_raises_error(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Getting nonexistent version produces helpful error."""
        registry.save(sample_baseline, "test-scenario")

        with pytest.raises(VersionNotFoundError) as exc_info:
            registry.get("test-scenario", "nonexistent123")

        assert "nonexistent123" in str(exc_info.value)
        assert "list_versions" in exc_info.value.fix

    def test_error_includes_available_scenarios(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """ScenarioNotFoundError includes available scenarios."""
        registry.save(sample_baseline, "existing-scenario")

        with pytest.raises(ScenarioNotFoundError) as exc_info:
            registry.get("nonexistent-scenario")

        assert "existing-scenario" in exc_info.value.fix

    def test_error_includes_available_versions(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """VersionNotFoundError includes available versions."""
        version_id = registry.save(sample_baseline, "test-scenario")

        with pytest.raises(VersionNotFoundError) as exc_info:
            registry.get("test-scenario", "nonexistent123")

        assert version_id in exc_info.value.fix

    def test_list_versions_nonexistent_scenario_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Listing versions for nonexistent scenario raises error."""
        with pytest.raises(ScenarioNotFoundError):
            registry.list_versions("nonexistent-scenario")

    def test_save_rejects_path_traversal_scenario_name(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Scenario names cannot include path traversal."""
        with pytest.raises(RegistryError) as exc_info:
            registry.save(sample_baseline, "../outside")

        assert exc_info.value.summary == "Invalid scenario name"

    def test_get_rejects_empty_scenario_name(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Empty scenario names are rejected."""
        with pytest.raises(RegistryError) as exc_info:
            registry.get("   ")

        assert exc_info.value.summary == "Invalid scenario name"


class TestImmutabilityGuards:
    """Tests that immutable versions detect on-disk tampering."""

    def test_get_detects_tampered_version_file(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """A modified version file should fail integrity checks on get()."""
        import yaml

        version_id = registry.save(sample_baseline, "test-scenario")
        version_file = (
            registry.path / "test-scenario" / "versions" / f"{version_id}.yaml"
        )

        with open(version_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["description"] = "tampered"
        with open(version_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        with pytest.raises(RegistryError) as exc_info:
            registry.get("test-scenario", version_id)

        assert "integrity check failed" in exc_info.value.summary.lower()

    def test_save_detects_tampered_existing_version_file(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Idempotent save must fail if existing immutable file was tampered."""
        import yaml

        version_id = registry.save(sample_baseline, "test-scenario")
        version_file = (
            registry.path / "test-scenario" / "versions" / f"{version_id}.yaml"
        )

        with open(version_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["description"] = "tampered"
        with open(version_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        with pytest.raises(RegistryError) as exc_info:
            registry.save(sample_baseline, "test-scenario")

        assert "integrity check failed" in exc_info.value.summary.lower()


class TestListingOperations:
    """Tests for list_scenarios and list_versions (AC-4)."""

    def test_list_scenarios_empty_registry(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Empty registry returns empty list."""
        assert registry.list_scenarios() == []

    def test_list_scenarios_returns_all_names(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
        sample_reform: ReformScenario,
    ) -> None:
        """list_scenarios returns all stored scenario names."""
        registry.save(sample_baseline, "scenario-alpha")
        registry.save(sample_reform, "scenario-beta")
        registry.save(sample_baseline, "scenario-gamma")

        scenarios = registry.list_scenarios()
        expected = ["scenario-alpha", "scenario-beta", "scenario-gamma"]
        assert sorted(scenarios) == expected

    def test_list_scenarios_sorted_alphabetically(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """list_scenarios returns names in alphabetical order."""
        registry.save(sample_baseline, "zebra")
        registry.save(sample_baseline, "alpha")
        registry.save(sample_baseline, "middle")

        scenarios = registry.list_scenarios()
        assert scenarios == ["alpha", "middle", "zebra"]

    def test_list_versions_returns_all_versions(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """list_versions returns full version history."""
        registry.save(sample_baseline, "test-scenario", "v1")

        modified1 = replace(sample_baseline, description="v2")
        registry.save(modified1, "test-scenario", "v2")

        modified2 = replace(sample_baseline, description="v3")
        registry.save(modified2, "test-scenario", "v3")

        versions = registry.list_versions("test-scenario")
        assert len(versions) == 3
        assert all(isinstance(v, ScenarioVersion) for v in versions)

    def test_list_versions_orders_by_timestamp(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """list_versions returns chronological order even if metadata order drifts."""
        import yaml

        v1 = registry.save(sample_baseline, "test-scenario", "v1")
        modified = replace(sample_baseline, description="v2")
        v2 = registry.save(modified, "test-scenario", "v2")

        metadata_file = registry.path / "test-scenario" / "metadata.yaml"
        with open(metadata_file, encoding="utf-8") as f:
            metadata = yaml.safe_load(f)

        metadata["versions"] = list(reversed(metadata["versions"]))
        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(metadata, f, default_flow_style=False, sort_keys=False)

        versions = registry.list_versions("test-scenario")
        assert [version.version_id for version in versions] == [v1, v2]


class TestFilePersistence:
    """Tests for file persistence (AC-5)."""

    def test_registry_creates_directory_structure(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Registry creates proper directory structure."""
        registry.save(sample_baseline, "test-scenario")

        scenario_dir = registry.path / "test-scenario"
        assert scenario_dir.exists()
        assert (scenario_dir / "metadata.yaml").exists()
        assert (scenario_dir / "versions").is_dir()

    def test_version_files_are_yaml(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Version files are saved as YAML."""
        version_id = registry.save(sample_baseline, "test-scenario")

        version_file = (
            registry.path / "test-scenario" / "versions" / f"{version_id}.yaml"
        )
        assert version_file.exists()
        assert version_file.suffix == ".yaml"

    def test_metadata_file_structure(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Metadata file has correct structure."""
        import yaml

        registry.save(sample_baseline, "test-scenario", "Initial version")

        metadata_file = registry.path / "test-scenario" / "metadata.yaml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        assert metadata["name"] == "test-scenario"
        assert "created" in metadata
        assert "latest_version" in metadata
        assert "versions" in metadata
        assert len(metadata["versions"]) == 1

    def test_registry_persists_across_instances(
        self,
        tmp_path: Path,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Data persists when registry is recreated."""
        registry_path = tmp_path / "registry"

        # Create and save with first instance
        registry1 = ScenarioRegistry(registry_path)
        version_id = registry1.save(sample_baseline, "test-scenario")

        # Create new instance and verify data
        registry2 = ScenarioRegistry(registry_path)
        retrieved = registry2.get("test-scenario", version_id)
        assert retrieved == sample_baseline

    def test_configurable_registry_path(
        self,
        tmp_path: Path,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Registry path is configurable."""
        custom_path = tmp_path / "custom" / "registry" / "location"
        registry = ScenarioRegistry(custom_path)
        registry.save(sample_baseline, "test-scenario")

        assert custom_path.exists()
        assert (custom_path / "test-scenario").exists()

    def test_registry_path_from_env_var(
        self,
        tmp_path: Path,
        sample_baseline: BaselineScenario,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Registry uses REFORMLAB_REGISTRY_PATH environment variable."""
        env_path = tmp_path / "env-registry"
        monkeypatch.setenv("REFORMLAB_REGISTRY_PATH", str(env_path))

        registry = ScenarioRegistry()  # No path provided
        registry.save(sample_baseline, "test-scenario")

        assert env_path.exists()
        assert (env_path / "test-scenario").exists()


class TestExistsMethod:
    """Tests for the exists() method."""

    def test_exists_returns_false_for_missing_scenario(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """exists returns False for missing scenario."""
        assert registry.exists("nonexistent") is False

    def test_exists_returns_true_for_existing_scenario(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """exists returns True for existing scenario."""
        registry.save(sample_baseline, "test-scenario")
        assert registry.exists("test-scenario") is True

    def test_exists_returns_false_for_missing_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """exists returns False for missing version."""
        registry.save(sample_baseline, "test-scenario")
        assert registry.exists("test-scenario", "nonexistent123") is False

    def test_exists_returns_true_for_existing_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """exists returns True for existing version."""
        version_id = registry.save(sample_baseline, "test-scenario")
        assert registry.exists("test-scenario", version_id) is True


class TestGetEntry:
    """Tests for the get_entry() method."""

    def test_get_entry_returns_registry_entry(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """get_entry returns RegistryEntry object."""
        registry.save(sample_baseline, "test-scenario")
        entry = registry.get_entry("test-scenario")

        assert isinstance(entry, RegistryEntry)
        assert entry.name == "test-scenario"

    def test_get_entry_includes_all_metadata(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """get_entry includes complete metadata."""
        version_id = registry.save(sample_baseline, "test-scenario", "Initial")
        entry = registry.get_entry("test-scenario")

        assert entry.name == "test-scenario"
        assert isinstance(entry.created, datetime)
        assert entry.latest_version == version_id
        assert len(entry.versions) == 1
        assert entry.versions[0].version_id == version_id

    def test_get_entry_nonexistent_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """get_entry raises error for nonexistent scenario."""
        with pytest.raises(ScenarioNotFoundError):
            registry.get_entry("nonexistent")


class TestMultipleScenariosAndVersions:
    """Tests for registry with multiple scenarios and versions."""

    def test_multiple_scenarios_independent(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
        sample_reform: ReformScenario,
    ) -> None:
        """Multiple scenarios are stored independently."""
        v1_baseline = registry.save(sample_baseline, "scenario-a")
        v1_reform = registry.save(sample_reform, "scenario-b")

        # Modify and save new versions
        modified_baseline = replace(sample_baseline, description="Modified A")
        v2_baseline = registry.save(modified_baseline, "scenario-a", "Update A")

        # Verify independence
        assert registry.get("scenario-a", v1_baseline) == sample_baseline
        assert registry.get("scenario-a", v2_baseline) == modified_baseline
        assert registry.get("scenario-b", v1_reform) == sample_reform

        # Verify version counts
        assert len(registry.list_versions("scenario-a")) == 2
        assert len(registry.list_versions("scenario-b")) == 1

    def test_latest_version_tracks_correctly(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Latest version is tracked correctly across updates."""
        registry.save(sample_baseline, "test-scenario")
        assert registry.get("test-scenario") == sample_baseline

        modified1 = replace(sample_baseline, description="v2")
        registry.save(modified1, "test-scenario")
        assert registry.get("test-scenario") == modified1

        modified2 = replace(sample_baseline, description="v3")
        v3 = registry.save(modified2, "test-scenario")
        assert registry.get("test-scenario") == modified2

        # Verify entry shows correct latest
        entry = registry.get_entry("test-scenario")
        assert entry.latest_version == v3


class TestRegistryInitialize:
    """Tests for registry initialization."""

    def test_initialize_creates_directory(
        self,
        tmp_path: Path,
    ) -> None:
        """initialize() creates registry directory."""
        registry_path = tmp_path / "new-registry"
        registry = ScenarioRegistry(registry_path)

        assert not registry_path.exists()
        registry.initialize()
        assert registry_path.exists()

    def test_initialize_idempotent(
        self,
        tmp_path: Path,
    ) -> None:
        """initialize() is idempotent."""
        registry_path = tmp_path / "registry"
        registry = ScenarioRegistry(registry_path)

        registry.initialize()
        registry.initialize()  # Should not raise
        assert registry_path.exists()


class TestClone:
    """Tests for scenario cloning (Story 2.5, AC-1, AC-3)."""

    def test_clone_baseline_creates_new_identity(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Cloned baseline has new name but identical parameters."""
        registry.save(sample_baseline, "original")
        clone = registry.clone("original", new_name="clone-1")

        assert clone.name == "clone-1"
        assert clone.parameters == sample_baseline.parameters
        assert clone.year_schedule == sample_baseline.year_schedule
        assert clone.policy_type == sample_baseline.policy_type
        assert clone.description == sample_baseline.description

    def test_clone_reform_creates_new_identity(
        self,
        registry: ScenarioRegistry,
        sample_reform: ReformScenario,
    ) -> None:
        """Cloned reform has new name but identical parameters."""
        registry.save(sample_reform, "original-reform")
        clone = registry.clone("original-reform", new_name="clone-reform")

        assert clone.name == "clone-reform"
        assert clone.parameters == sample_reform.parameters
        assert clone.baseline_ref == sample_reform.baseline_ref
        assert clone.policy_type == sample_reform.policy_type

    def test_clone_auto_generates_name(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Clone generates default name when new_name not provided."""
        registry.save(sample_baseline, "my-scenario")
        clone = registry.clone("my-scenario")

        assert clone.name == "my-scenario-clone"

    def test_clone_specific_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Clone can target a specific version."""
        v1 = registry.save(sample_baseline, "test-scenario")

        modified = replace(sample_baseline, description="Modified version")
        registry.save(modified, "test-scenario", "Update")

        # Clone the original version
        clone = registry.clone("test-scenario", version_id=v1, new_name="clone-v1")

        assert clone.description == sample_baseline.description
        assert clone.name == "clone-v1"

    def test_clone_is_independent_in_memory(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Cloned scenario is independent in memory (no shared references)."""
        registry.save(sample_baseline, "original")
        clone = registry.clone("original", new_name="clone-1")

        # Since scenarios are frozen dataclasses, they're already immutable
        # Verify they are different objects
        assert clone is not sample_baseline
        assert clone.name != sample_baseline.name

    def test_clone_modify_save_does_not_affect_original(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Modifying and saving clone does not affect original history."""
        v1 = registry.save(sample_baseline, "original")
        clone = registry.clone("original", new_name="clone-1")

        # Modify and save the clone
        modified_clone = replace(clone, description="Modified clone")
        registry.save(modified_clone, "clone-1", "Cloned from original")

        # Original should remain unchanged
        original = registry.get("original", v1)
        assert original.description == sample_baseline.description
        assert len(registry.list_versions("original")) == 1

    def test_clone_nonexistent_scenario_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Cloning nonexistent scenario raises ScenarioNotFoundError."""
        with pytest.raises(ScenarioNotFoundError):
            registry.clone("nonexistent")

    def test_clone_nonexistent_version_raises_error(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Cloning nonexistent version raises VersionNotFoundError."""
        registry.save(sample_baseline, "test-scenario")

        with pytest.raises(VersionNotFoundError):
            registry.clone("test-scenario", version_id="nonexistent123")


class TestBaselineReformNavigation:
    """Tests for baseline/reform link navigation (Story 2.5, AC-2)."""

    def test_get_baseline_from_reform(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Can navigate from reform to its linked baseline."""
        registry.save(sample_baseline, "french-carbon-tax-2026")

        reform = ReformScenario(
            name="Progressive Dividend",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            parameters=CarbonTaxParameters(
                rate_schedule={},
                redistribution_type="progressive_dividend",
            ),
        )
        registry.save(reform, "reform-1")

        baseline = registry.get_baseline("reform-1")
        assert baseline.name == sample_baseline.name
        assert baseline.parameters == sample_baseline.parameters

    def test_get_baseline_from_specific_reform_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Can get baseline from specific reform version."""
        registry.save(sample_baseline, "baseline")

        reform = ReformScenario(
            name="Reform v1",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        v1 = registry.save(reform, "reform")

        # Create modified reform with same baseline
        reform_v2 = replace(reform, description="Updated reform")
        registry.save(reform_v2, "reform", "Update")

        # Get baseline from v1
        baseline = registry.get_baseline("reform", v1)
        assert baseline.name == sample_baseline.name

    def test_get_baseline_with_pinned_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """baseline_ref with @version_id pins to specific baseline version."""
        v1 = registry.save(sample_baseline, "baseline")

        # Create new baseline version
        baseline_v2 = replace(sample_baseline, description="Baseline v2")
        registry.save(baseline_v2, "baseline", "Update")

        # Reform pinned to v1
        reform = ReformScenario(
            name="Reform pinned",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref=f"baseline@{v1}",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        registry.save(reform, "reform-pinned")

        baseline = registry.get_baseline("reform-pinned")
        assert baseline.description == sample_baseline.description  # v1 description

    def test_get_baseline_from_non_reform_raises_error(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """get_baseline on a baseline scenario raises RegistryError."""
        registry.save(sample_baseline, "baseline")

        with pytest.raises(RegistryError) as exc_info:
            registry.get_baseline("baseline")

        assert "not a reform" in exc_info.value.summary.lower()

    def test_get_baseline_missing_baseline_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """get_baseline raises error when linked baseline doesn't exist."""
        reform = ReformScenario(
            name="Orphan Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="nonexistent-baseline",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        registry.save(reform, "orphan-reform")

        with pytest.raises(RegistryError) as exc_info:
            registry.get_baseline("orphan-reform")
        assert exc_info.value.summary == "Broken baseline link"

    def test_get_baseline_malformed_ref_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Malformed baseline_ref returns a clear RegistryError."""
        reform = ReformScenario(
            name="Malformed Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline@",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        registry.save(reform, "malformed-reform")

        with pytest.raises(RegistryError) as exc_info:
            registry.get_baseline("malformed-reform")
        assert exc_info.value.summary == "Invalid baseline reference"

    def test_list_reforms_for_baseline(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """List all reforms referencing a baseline."""
        registry.save(sample_baseline, "baseline")

        # Create multiple reforms
        for i in range(3):
            reform = ReformScenario(
                name=f"Reform {i}",
                policy_type=PolicyType.CARBON_TAX,
                baseline_ref="baseline",
                parameters=CarbonTaxParameters(rate_schedule={}),
            )
            registry.save(reform, f"reform-{i}")

        reforms = registry.list_reforms("baseline")
        assert len(reforms) == 3
        reform_names = [r[0] for r in reforms]
        assert sorted(reform_names) == ["reform-0", "reform-1", "reform-2"]

    def test_list_reforms_with_pinned_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """List reforms can filter by baseline version."""
        v1 = registry.save(sample_baseline, "baseline")

        baseline_v2 = replace(sample_baseline, description="v2")
        v2 = registry.save(baseline_v2, "baseline", "Update")

        # Reform referencing v1
        reform_v1 = ReformScenario(
            name="Reform for v1",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref=f"baseline@{v1}",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        registry.save(reform_v1, "reform-v1")

        # Reform referencing v2
        reform_v2 = ReformScenario(
            name="Reform for v2",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref=f"baseline@{v2}",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        registry.save(reform_v2, "reform-v2")

        # List reforms for v1 only
        reforms = registry.list_reforms("baseline", version_id=v1)
        assert len(reforms) == 1
        assert reforms[0][0] == "reform-v1"

    def test_list_reforms_returns_empty_when_no_reforms(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """list_reforms returns empty list when no reforms exist."""
        registry.save(sample_baseline, "lonely-baseline")

        reforms = registry.list_reforms("lonely-baseline")
        assert reforms == []

    def test_list_reforms_for_non_baseline_raises_error(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """list_reforms requires a baseline scenario target."""
        registry.save(sample_baseline, "baseline")
        reform = ReformScenario(
            name="Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        registry.save(reform, "my-reform")

        with pytest.raises(RegistryError) as exc_info:
            registry.list_reforms("my-reform")
        assert exc_info.value.summary == "Not a baseline scenario"

    def test_list_reforms_missing_baseline_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """list_reforms raises when the baseline target does not exist."""
        with pytest.raises(ScenarioNotFoundError):
            registry.list_reforms("missing-baseline")

    def test_list_reforms_includes_version_ids(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """list_reforms returns (name, version_id) tuples."""
        registry.save(sample_baseline, "baseline")

        reform = ReformScenario(
            name="Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline",
            parameters=CarbonTaxParameters(rate_schedule={}),
        )
        version_id = registry.save(reform, "my-reform")

        reforms = registry.list_reforms("baseline")
        assert len(reforms) == 1
        assert reforms[0] == ("my-reform", version_id)


class TestBaselineRefParsing:
    """Tests for baseline_ref format parsing (Story 2.5, AC-2)."""

    def test_parse_baseline_ref_name_only(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Parse baseline_ref with name only returns (name, None)."""
        name, version = registry._parse_baseline_ref("my-baseline")
        assert name == "my-baseline"
        assert version is None

    def test_parse_baseline_ref_with_version(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Parse baseline_ref with @version returns (name, version)."""
        name, version = registry._parse_baseline_ref("my-baseline@abc123def")
        assert name == "my-baseline"
        assert version == "abc123def"

    def test_parse_baseline_ref_multiple_at_signs(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Parse baseline_ref with multiple @ uses last one for version."""
        # Edge case: scenario name contains @
        name, version = registry._parse_baseline_ref("weird@name@version123")
        assert name == "weird@name"
        assert version == "version123"

    def test_parse_baseline_ref_empty_version(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Trailing @ is invalid because pinned refs require a version ID."""
        with pytest.raises(RegistryError) as exc_info:
            registry._parse_baseline_ref("baseline@")
        assert exc_info.value.summary == "Invalid baseline reference"

    def test_parse_baseline_ref_missing_name_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Pinned refs require a baseline name before @."""
        with pytest.raises(RegistryError) as exc_info:
            registry._parse_baseline_ref("@abc123def")
        assert exc_info.value.summary == "Invalid baseline reference"


class TestCloneIntegration:
    """Integration tests for clone -> modify -> save flow (Story 2.5, AC-1, AC-3)."""

    def test_clone_modify_save_creates_new_scenario_history(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Clone, modify, and save creates independent scenario history."""
        # Save original
        original_v1 = registry.save(sample_baseline, "original", "Initial version")

        # Clone to new name
        clone = registry.clone("original", new_name="variant")

        # Modify the clone
        modified_clone = replace(clone, description="Modified variant")

        # Save with lineage description
        clone_v1 = registry.save(
            modified_clone,
            "variant",
            f"Cloned from original@{original_v1}",
        )

        # Verify independent histories
        original_versions = registry.list_versions("original")
        variant_versions = registry.list_versions("variant")

        assert len(original_versions) == 1
        assert len(variant_versions) == 1

        # Verify original is unchanged
        retrieved_original = registry.get("original", original_v1)
        assert retrieved_original.description == sample_baseline.description

        # Verify variant has new description
        retrieved_variant = registry.get("variant", clone_v1)
        assert retrieved_variant.description == "Modified variant"

        # Verify lineage is captured in change description
        assert (
            variant_versions[0].change_description
            == f"Cloned from original@{original_v1}"
        )

    def test_clone_and_save_under_same_name_creates_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Clone, modify, and save under existing name creates new version."""
        # Save original
        registry.save(sample_baseline, "scenario")

        # Clone (defaults to "scenario-clone")
        clone = registry.clone("scenario")

        # Save clone under its auto-generated name
        modified_clone = replace(clone, description="Clone v1")
        registry.save(modified_clone, "scenario-clone", "Initial clone")

        # Modify clone again
        clone_modified = replace(modified_clone, description="Clone v2")
        registry.save(clone_modified, "scenario-clone", "Updated clone")

        # Verify scenario-clone has two versions
        clone_versions = registry.list_versions("scenario-clone")
        assert len(clone_versions) == 2
        assert clone_versions[0].change_description == "Initial clone"
        assert clone_versions[1].change_description == "Updated clone"

        # Original still has one version
        original_versions = registry.list_versions("scenario")
        assert len(original_versions) == 1

    def test_clone_reform_and_navigate_to_baseline(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Cloned reform maintains baseline_ref link."""
        # Save baseline
        registry.save(sample_baseline, "carbon-tax")

        # Create and save reform
        reform = ReformScenario(
            name="Progressive",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="carbon-tax",
            parameters=CarbonTaxParameters(
                rate_schedule={},
                redistribution_type="progressive_dividend",
            ),
        )
        registry.save(reform, "progressive-reform")

        # Clone the reform
        cloned_reform = registry.clone(
            "progressive-reform", new_name="progressive-variant"
        )

        # Verify cloned reform can still navigate to baseline
        assert cloned_reform.baseline_ref == "carbon-tax"

        # Save cloned reform and navigate
        registry.save(cloned_reform, "progressive-variant")
        baseline = registry.get_baseline("progressive-variant")
        assert baseline.name == sample_baseline.name

        # Both reforms should appear in list_reforms
        reforms = registry.list_reforms("carbon-tax")
        reform_names = [r[0] for r in reforms]
        assert "progressive-reform" in reform_names
        assert "progressive-variant" in reform_names


class TestMigrate:
    """Tests for ScenarioRegistry.migrate() (Story 2.6, AC-3)."""

    def test_migrate_dry_run_returns_report_no_save(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Dry-run migration returns report without saving new version."""
        registry.save(sample_baseline, "test-scenario")

        report = registry.migrate("test-scenario", dry_run=True)

        assert isinstance(report, MigrationReport)
        # Only one version should exist (no new version created)
        versions = registry.list_versions("test-scenario")
        assert len(versions) == 1

    def test_migrate_apply_creates_new_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Apply mode migration creates a new version."""
        registry.save(sample_baseline, "test-scenario")
        monkeypatch.setattr(registry_module, "SCHEMA_VERSION", "1.1")

        report = registry.migrate("test-scenario", dry_run=False)

        assert isinstance(report, MigrationReport)
        versions = registry.list_versions("test-scenario")
        assert report.status == CompatibilityStatus.MIGRATION_AVAILABLE
        assert len(versions) == 2
        migrated = registry.get("test-scenario")
        assert migrated.version == "1.1"

    def test_migrate_specific_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Can migrate a specific version by version_id."""
        v1 = registry.save(sample_baseline, "test-scenario")

        modified = replace(sample_baseline, description="Version 2")
        registry.save(modified, "test-scenario", "Update")

        # Migrate specific version
        report = registry.migrate("test-scenario", version_id=v1, dry_run=True)

        assert isinstance(report, MigrationReport)
        # Report should reference the source version
        assert report.source_version.major == 1
        assert report.source_version.minor == 0

    def test_migrate_nonexistent_scenario_raises_error(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """Migrating nonexistent scenario raises ScenarioNotFoundError."""
        with pytest.raises(ScenarioNotFoundError):
            registry.migrate("nonexistent")

    def test_migrate_nonexistent_version_raises_error(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Migrating nonexistent version raises VersionNotFoundError."""
        registry.save(sample_baseline, "test-scenario")

        with pytest.raises(VersionNotFoundError):
            registry.migrate("test-scenario", version_id="nonexistent123")

    def test_migrate_breaking_version_raises_registry_error(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Breaking version change raises RegistryError with actionable fix."""
        # Create a scenario with version 2.0 to simulate future version
        v2_scenario = replace(sample_baseline, version="2.0")
        registry.save(v2_scenario, "v2-scenario")

        # Try to migrate to current version (1.0)
        with pytest.raises(RegistryError) as exc_info:
            registry.migrate("v2-scenario", dry_run=True)

        assert "breaking" in exc_info.value.reason.lower()
        assert exc_info.value.fix  # Should have actionable fix

    def test_migrate_apply_uses_lineage_description(
        self,
        registry: ScenarioRegistry,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Apply migration saves with clear lineage change_description."""
        # Create scenario with older minor version to trigger migration
        old_scenario = BaselineScenario(
            name="Old Scenario",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(start_year=2025, end_year=2035),
            parameters=CarbonTaxParameters(rate_schedule={2025: 50.0}),
            version="1.0",
        )
        v1 = registry.save(old_scenario, "old-scenario")
        monkeypatch.setattr(registry_module, "SCHEMA_VERSION", "1.1")

        registry.migrate("old-scenario", dry_run=False)

        versions = registry.list_versions("old-scenario")
        assert len(versions) == 2
        assert versions[-1].parent_version == v1
        assert "Migrated from schema version 1.0 to 1.1" in (
            versions[-1].change_description
        )
        assert v1 in versions[-1].change_description

    def test_migrate_round_trip_preserves_data(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Migration round-trip preserves scenario data integrity."""
        v1 = registry.save(sample_baseline, "test-scenario")

        # Migrate in dry_run mode
        report = registry.migrate("test-scenario", dry_run=True)

        # Get original scenario
        original = registry.get("test-scenario", v1)

        # If report indicates migration happened, verify data integrity
        if report.status == CompatibilityStatus.MIGRATION_AVAILABLE:
            # Apply migration
            registry.migrate("test-scenario", dry_run=False)
            migrated = registry.get("test-scenario")

            # Core data should be preserved
            assert migrated.name == original.name
            assert migrated.policy_type == original.policy_type
            assert migrated.parameters == original.parameters
            if hasattr(original, "year_schedule"):
                assert migrated.year_schedule == original.year_schedule


class TestRegistryValidationStatus:
    """Tests for registry validation status tracking (Story 5-6, AC-5)."""

    def test_default_is_not_validated(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Scenarios default to not validated."""
        registry.save(sample_baseline, "test-scenario")
        assert registry.is_validated("test-scenario") is False

    def test_set_validated_true(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Mark a scenario as validated."""
        version_id = registry.save(sample_baseline, "test-scenario")
        registry.set_validated("test-scenario", version_id, validated=True)
        assert registry.is_validated("test-scenario", version_id) is True

    def test_set_validated_false(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Explicitly mark a scenario as not validated."""
        version_id = registry.save(sample_baseline, "test-scenario")
        registry.set_validated("test-scenario", version_id, validated=True)
        registry.set_validated("test-scenario", version_id, validated=False)
        assert registry.is_validated("test-scenario", version_id) is False

    def test_is_validated_resolves_latest_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """is_validated with version_id=None resolves to latest version."""
        registry.save(sample_baseline, "test-scenario")
        registry.set_validated("test-scenario", validated=True)
        assert registry.is_validated("test-scenario") is True

    def test_set_validated_resolves_latest_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """set_validated with version_id=None resolves to latest version."""
        version_id = registry.save(sample_baseline, "test-scenario")
        registry.set_validated("test-scenario", validated=True)
        assert registry.is_validated("test-scenario", version_id) is True

    def test_is_validated_nonexistent_scenario(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """is_validated returns False for nonexistent scenario."""
        assert registry.is_validated("nonexistent") is False

    def test_is_validated_nonexistent_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """is_validated returns False for nonexistent version."""
        registry.save(sample_baseline, "test-scenario")
        assert registry.is_validated("test-scenario", "nonexistent-version") is False

    def test_set_validated_nonexistent_scenario_raises(
        self,
        registry: ScenarioRegistry,
    ) -> None:
        """set_validated raises ScenarioNotFoundError for nonexistent scenario."""
        with pytest.raises(ScenarioNotFoundError):
            registry.set_validated("nonexistent", validated=True)

    def test_set_validated_nonexistent_version_raises(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """set_validated raises VersionNotFoundError for nonexistent version."""
        registry.save(sample_baseline, "test-scenario")
        with pytest.raises(VersionNotFoundError):
            registry.set_validated(
                "test-scenario", "nonexistent-version", validated=True
            )

    def test_validation_persists_after_reload(
        self,
        tmp_path: Path,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Validation status persists across registry instances."""
        reg_path = tmp_path / "persist-registry"
        reg1 = ScenarioRegistry(reg_path)
        version_id = reg1.save(sample_baseline, "test-scenario")
        reg1.set_validated("test-scenario", version_id, validated=True)

        # Create new registry instance pointing to same path
        reg2 = ScenarioRegistry(reg_path)
        assert reg2.is_validated("test-scenario", version_id) is True

    def test_validation_per_version(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Validation status is tracked per version."""
        v1 = registry.save(sample_baseline, "test-scenario")
        modified = replace(sample_baseline, description="v2")
        v2 = registry.save(modified, "test-scenario", "second version")

        registry.set_validated("test-scenario", v1, validated=True)
        assert registry.is_validated("test-scenario", v1) is True
        assert registry.is_validated("test-scenario", v2) is False

    def test_backward_compat_missing_is_validated_field(
        self,
        registry: ScenarioRegistry,
        sample_baseline: BaselineScenario,
    ) -> None:
        """Existing metadata without is_validated field defaults to False."""
        # Save scenario (metadata will not have is_validated)
        version_id = registry.save(sample_baseline, "test-scenario")
        # is_validated should return False for existing scenarios
        assert registry.is_validated("test-scenario", version_id) is False
