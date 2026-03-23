# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for schema migration helper."""

from __future__ import annotations

import copy

import pytest

from reformlab.templates.loader import SCHEMA_VERSION
from reformlab.templates.migration import (
    CompatibilityStatus,
    MigrationChange,
    MigrationReport,
    SchemaVersion,
    check_compatibility,
    migrate_scenario_dict,
)


class TestSchemaVersion:
    """Tests for SchemaVersion parsing and comparison."""

    def test_parse_valid_version(self) -> None:
        """Parse valid version strings."""
        v = SchemaVersion.parse("1.0")
        assert v.major == 1
        assert v.minor == 0

        v2 = SchemaVersion.parse("2.3")
        assert v2.major == 2
        assert v2.minor == 3

    def test_parse_major_only(self) -> None:
        """Parse version with only major component."""
        v = SchemaVersion.parse("1")
        assert v.major == 1
        assert v.minor == 0

    def test_parse_invalid_raises(self) -> None:
        """Invalid version strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid version"):
            SchemaVersion.parse("")
        with pytest.raises(ValueError, match="Invalid version"):
            SchemaVersion.parse("abc")
        with pytest.raises(ValueError, match="Invalid version"):
            SchemaVersion.parse("1.x")
        with pytest.raises(ValueError, match="Invalid version"):
            SchemaVersion.parse("1.2.3")
        with pytest.raises(ValueError, match="Invalid version"):
            SchemaVersion.parse("-1.0")

    def test_str_representation(self) -> None:
        """String representation matches input format."""
        assert str(SchemaVersion(1, 0)) == "1.0"
        assert str(SchemaVersion(2, 3)) == "2.3"

    def test_equality(self) -> None:
        """Version equality comparison."""
        v1 = SchemaVersion(1, 0)
        v2 = SchemaVersion(1, 0)
        v3 = SchemaVersion(1, 1)
        assert v1 == v2
        assert v1 != v3

    def test_comparison(self) -> None:
        """Version ordering comparison."""
        v1_0 = SchemaVersion(1, 0)
        v1_1 = SchemaVersion(1, 1)
        v2_0 = SchemaVersion(2, 0)

        assert v1_0 < v1_1
        assert v1_1 < v2_0
        assert v2_0 > v1_1

    def test_current_returns_loader_version(self) -> None:
        """current() returns version from loader.SCHEMA_VERSION."""
        current = SchemaVersion.current()
        expected = SchemaVersion.parse(SCHEMA_VERSION)
        assert current == expected


class TestCheckCompatibility:
    """Tests for schema compatibility checking."""

    def test_same_version_is_compatible(self) -> None:
        """Same major.minor is compatible, no migration needed."""
        result = check_compatibility("1.0", "1.0")
        assert result == CompatibilityStatus.COMPATIBLE
        assert result.needs_migration is False
        assert result.is_breaking is False

    def test_same_major_higher_minor_needs_migration(self) -> None:
        """Same major, higher target minor requires migration."""
        result = check_compatibility("1.0", "1.1")
        assert result == CompatibilityStatus.MIGRATION_AVAILABLE
        assert result.needs_migration is True
        assert result.is_breaking is False

    def test_same_major_lower_minor_is_compatible(self) -> None:
        """Same major, lower target minor is forward-compatible."""
        result = check_compatibility("1.1", "1.0")
        assert result == CompatibilityStatus.COMPATIBLE
        assert result.needs_migration is False

    def test_different_major_is_breaking(self) -> None:
        """Different major version is a breaking change."""
        result = check_compatibility("1.0", "2.0")
        assert result == CompatibilityStatus.BREAKING
        assert result.is_breaking is True

        result2 = check_compatibility("2.0", "1.0")
        assert result2 == CompatibilityStatus.BREAKING
        assert result2.is_breaking is True

    def test_accepts_schema_version_objects(self) -> None:
        """Accepts SchemaVersion objects as input."""
        source = SchemaVersion(1, 0)
        target = SchemaVersion(1, 1)
        result = check_compatibility(source, target)
        assert result == CompatibilityStatus.MIGRATION_AVAILABLE


class TestMigrationChange:
    """Tests for MigrationChange data structure."""

    def test_immutable(self) -> None:
        """MigrationChange is immutable (frozen dataclass)."""
        change = MigrationChange(
            field_path="policy.rate_schedule",
            old_value=None,
            new_value={},
            reason="Added default empty rate_schedule",
        )
        with pytest.raises(AttributeError):
            change.field_path = "other"  # type: ignore[misc]


class TestMigrationReport:
    """Tests for MigrationReport data structure."""

    def test_immutable(self) -> None:
        """MigrationReport is immutable (frozen dataclass)."""
        report = MigrationReport(
            source_version=SchemaVersion(1, 0),
            target_version=SchemaVersion(1, 1),
            status=CompatibilityStatus.MIGRATION_AVAILABLE,
            changes=(),
            warnings=(),
        )
        with pytest.raises(AttributeError):
            report.status = CompatibilityStatus.COMPATIBLE  # type: ignore[misc]

    def test_success_property(self) -> None:
        """success property is True when status is not BREAKING."""
        compatible_report = MigrationReport(
            source_version=SchemaVersion(1, 0),
            target_version=SchemaVersion(1, 0),
            status=CompatibilityStatus.COMPATIBLE,
            changes=(),
            warnings=(),
        )
        assert compatible_report.success is True

        migration_report = MigrationReport(
            source_version=SchemaVersion(1, 0),
            target_version=SchemaVersion(1, 1),
            status=CompatibilityStatus.MIGRATION_AVAILABLE,
            changes=(),
            warnings=(),
        )
        assert migration_report.success is True

        breaking_report = MigrationReport(
            source_version=SchemaVersion(1, 0),
            target_version=SchemaVersion(2, 0),
            status=CompatibilityStatus.BREAKING,
            changes=(),
            warnings=(),
        )
        assert breaking_report.success is False


class TestMigrateScenarioDict:
    """Tests for migrate_scenario_dict pure function."""

    def test_does_not_mutate_input(self) -> None:
        """Migration does not mutate the input dictionary."""
        original = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {"rate_schedule": {2025: 50.0}},
        }
        original_copy = copy.deepcopy(original)

        migrate_scenario_dict(original)

        assert original == original_copy

    def test_same_version_returns_unchanged(self) -> None:
        """Same source and target version returns unchanged dict."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {"rate_schedule": {2025: 50.0}},
        }

        result, report = migrate_scenario_dict(data, target_version="1.0")

        assert result == data
        assert report.status == CompatibilityStatus.COMPATIBLE
        assert len(report.changes) == 0

    def test_breaking_version_raises(self) -> None:
        """Breaking major version difference raises ValueError."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        with pytest.raises(ValueError, match="Breaking schema change"):
            migrate_scenario_dict(data, target_version="2.0")

    def test_updates_version_field(self) -> None:
        """Migration updates version field to target version."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        result, report = migrate_scenario_dict(data, target_version="1.1")

        assert result["version"] == "1.1"
        assert report.source_version == SchemaVersion(1, 0)
        assert report.target_version == SchemaVersion(1, 1)

    def test_defaults_to_current_schema_version(self) -> None:
        """Target version defaults to current SCHEMA_VERSION."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        result, report = migrate_scenario_dict(data)

        assert result["version"] == SCHEMA_VERSION
        assert report.target_version == SchemaVersion.current()

    def test_report_contains_change_entries(self) -> None:
        """Report includes MigrationChange entries for version update."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        _, report = migrate_scenario_dict(data, target_version="1.1")

        # Should have at least version update change
        version_changes = [c for c in report.changes if c.field_path == "version"]
        assert len(version_changes) == 1
        assert version_changes[0].old_value == "1.0"
        assert version_changes[0].new_value == "1.1"

    def test_missing_version_uses_default(self) -> None:
        """Scenario without version field is treated as 1.0."""
        data = {
            "name": "test-scenario",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        result, report = migrate_scenario_dict(data, target_version="1.0")

        assert result["version"] == "1.0"
        assert report.source_version == SchemaVersion(1, 0)

    def test_returns_new_dict_instance(self) -> None:
        """Migration returns a new dict instance, not the original."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        result, _ = migrate_scenario_dict(data, target_version="1.0")

        assert result is not data

    def test_rebate_legacy_shape_is_normalized_for_1x_migration(self) -> None:
        """Rebate redistribution legacy fields are normalized to current shape."""
        data = {
            "name": "rebate-legacy",
            "version": "1.0",
            "policy_type": "rebate",
            "policy": {
                "redistribution": {
                    "type": "progressive_dividend",
                    "income_weights": {"decile_1": 1.4},
                }
            },
        }

        result, report = migrate_scenario_dict(data, target_version="1.1")

        assert result["version"] == "1.1"
        assert result["policy"]["rebate_type"] == "progressive_dividend"
        assert result["policy"]["income_weights"] == {"decile_1": 1.4}
        assert "redistribution" not in result["policy"]
        change_paths = {change.field_path for change in report.changes}
        assert "policy.rebate_type" in change_paths
        assert "policy.income_weights" in change_paths
        assert "policy.redistribution" in change_paths
        assert report.warnings

    def test_migration_inserts_default_schema_ref_when_missing(self) -> None:
        """Migration inserts default $schema when absent for newer 1.x shapes."""
        data = {
            "name": "test-scenario",
            "version": "1.0",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        result, report = migrate_scenario_dict(data, target_version="1.1")

        assert result["$schema"] == "./schema/scenario-template.schema.json"
        schema_changes = [c for c in report.changes if c.field_path == "$schema"]
        assert len(schema_changes) == 1
        assert schema_changes[0].old_value is None

    def test_forward_compatible_newer_minor_returns_warning(self) -> None:
        """Newer source minor stays compatible but warns for analyst review."""
        data = {
            "name": "future-scenario",
            "version": "1.2",
            "policy_type": "carbon_tax",
            "policy": {},
        }

        result, report = migrate_scenario_dict(data, target_version="1.1")

        assert result["version"] == "1.2"
        assert report.status == CompatibilityStatus.COMPATIBLE
        assert report.warnings
