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

from reformlab.templates.registry import (
    RegistryEntry,
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
