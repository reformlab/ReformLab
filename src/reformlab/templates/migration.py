"""Schema migration helper for scenario templates.

This module provides utilities for detecting schema compatibility and
migrating scenario templates between schema versions.

Key components:
- SchemaVersion: Parse and compare semantic version strings
- CompatibilityStatus: Enum for compatibility check results
- check_compatibility: Compare source and target versions
- MigrationChange/MigrationReport: Immutable migration result types
- migrate_scenario_dict: Pure function for migrating scenario data
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any

from reformlab.templates.loader import SCHEMA_VERSION


class CompatibilityStatus(Enum):
    """Result of schema version compatibility check.

    Values:
        COMPATIBLE: Versions are compatible, no migration needed.
        MIGRATION_AVAILABLE: Migration is possible (same major version).
        BREAKING: Major version mismatch, migration not supported.
    """

    COMPATIBLE = "compatible"
    MIGRATION_AVAILABLE = "migration_available"
    BREAKING = "breaking"

    @property
    def needs_migration(self) -> bool:
        """Return True if migration is needed."""
        return self == CompatibilityStatus.MIGRATION_AVAILABLE

    @property
    def is_breaking(self) -> bool:
        """Return True if this is a breaking change."""
        return self == CompatibilityStatus.BREAKING


@dataclass(frozen=True, order=True)
class SchemaVersion:
    """Semantic version for schema compatibility.

    Supports parsing version strings like "1.0" or "2.3" and comparing
    versions for ordering and equality.
    """

    major: int
    minor: int = 0

    def __str__(self) -> str:
        """Return version as string in major.minor format."""
        return f"{self.major}.{self.minor}"

    @classmethod
    def parse(cls, version: str) -> SchemaVersion:
        """Parse a version string into a SchemaVersion.

        Args:
            version: Version string like "1.0" or "2".

        Returns:
            SchemaVersion instance.

        Raises:
            ValueError: If version string is invalid.
        """
        if not version or not version.strip():
            raise ValueError(f"Invalid version: '{version}'")

        parts = version.strip().split(".")
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid version: '{version}'") from exc

        return cls(major=major, minor=minor)

    @classmethod
    def current(cls) -> SchemaVersion:
        """Return the current schema version from loader.SCHEMA_VERSION."""
        return cls.parse(SCHEMA_VERSION)


@dataclass(frozen=True)
class MigrationChange:
    """Record of a single field change during migration.

    Attributes:
        field_path: Dot-separated path to the changed field.
        old_value: Previous value (None if field was added).
        new_value: New value after migration.
        reason: Human-readable explanation of the change.
    """

    field_path: str
    old_value: Any
    new_value: Any
    reason: str


@dataclass(frozen=True)
class MigrationReport:
    """Result of a migration operation.

    Attributes:
        source_version: Original schema version.
        target_version: Target schema version after migration.
        status: Compatibility status.
        changes: Tuple of MigrationChange records.
        warnings: Tuple of warning messages for analyst review.
    """

    source_version: SchemaVersion
    target_version: SchemaVersion
    status: CompatibilityStatus
    changes: tuple[MigrationChange, ...]
    warnings: tuple[str, ...]

    @property
    def success(self) -> bool:
        """Return True if migration succeeded (status is not BREAKING)."""
        return self.status != CompatibilityStatus.BREAKING


def check_compatibility(
    source: str | SchemaVersion,
    target: str | SchemaVersion,
) -> CompatibilityStatus:
    """Check compatibility between source and target schema versions.

    Uses semantic versioning rules:
    - Same major.minor: COMPATIBLE (no migration needed)
    - Same major, different minor: MIGRATION_AVAILABLE
    - Different major: BREAKING (migration not supported)

    Args:
        source: Source schema version (string or SchemaVersion).
        target: Target schema version (string or SchemaVersion).

    Returns:
        CompatibilityStatus indicating migration requirements.
    """
    if isinstance(source, str):
        source = SchemaVersion.parse(source)
    if isinstance(target, str):
        target = SchemaVersion.parse(target)

    # Different major version is a breaking change
    if source.major != target.major:
        return CompatibilityStatus.BREAKING

    # Same major and minor: compatible, no migration
    if source.minor == target.minor:
        return CompatibilityStatus.COMPATIBLE

    # Same major, source minor < target minor: migration available
    if source.minor < target.minor:
        return CompatibilityStatus.MIGRATION_AVAILABLE

    # Same major, source minor > target minor: forward compatible
    return CompatibilityStatus.COMPATIBLE


def migrate_scenario_dict(
    data: dict[str, Any],
    target_version: str | None = None,
) -> tuple[dict[str, Any], MigrationReport]:
    """Migrate a scenario dictionary to a target schema version.

    This is a pure function that does not mutate the input dictionary.
    It returns a new dictionary with the migrated data and a report
    describing all changes made.

    Args:
        data: Scenario dictionary to migrate.
        target_version: Target schema version (defaults to current SCHEMA_VERSION).

    Returns:
        Tuple of (migrated_dict, MigrationReport).

    Raises:
        ValueError: If migration requires a breaking major version change.
    """
    # Parse versions
    source_str = str(data.get("version", "1.0"))
    source_ver = SchemaVersion.parse(source_str)

    if target_version is None:
        target_ver = SchemaVersion.current()
    else:
        target_ver = SchemaVersion.parse(target_version)

    # Check compatibility
    status = check_compatibility(source_ver, target_ver)

    if status == CompatibilityStatus.BREAKING:
        raise ValueError(
            f"Breaking schema change: cannot migrate from {source_ver} to "
            f"{target_ver}. Major version mismatch requires manual conversion."
        )

    # Deep copy to avoid mutating input
    result = copy.deepcopy(data)
    changes: list[MigrationChange] = []
    warnings: list[str] = []

    # Apply migrations
    if status == CompatibilityStatus.MIGRATION_AVAILABLE:
        # Update version field
        old_version = result.get("version", "1.0")
        new_version = str(target_ver)
        result["version"] = new_version
        changes.append(
            MigrationChange(
                field_path="version",
                old_value=old_version,
                new_value=new_version,
                reason=f"Updated schema version from {old_version} to {new_version}",
            )
        )

        # Apply version-specific migrations
        # (Currently no specific 1.x migrations defined, but structure is ready)
        _apply_1x_migrations(result, source_ver, target_ver, changes, warnings)

    elif status == CompatibilityStatus.COMPATIBLE:
        # Ensure version field is set even if same version
        if "version" not in result:
            result["version"] = str(target_ver)

    return result, MigrationReport(
        source_version=source_ver,
        target_version=target_ver,
        status=status,
        changes=tuple(changes),
        warnings=tuple(warnings),
    )


def _apply_1x_migrations(
    data: dict[str, Any],
    source: SchemaVersion,
    target: SchemaVersion,
    changes: list[MigrationChange],
    warnings: list[str],
) -> None:
    """Apply migrations for 1.x schema versions.

    This function mutates the data dict in-place and appends to changes/warnings.
    It is called from migrate_scenario_dict after the deep copy.

    Args:
        data: Scenario dict to modify in-place.
        source: Source schema version.
        target: Target schema version.
        changes: List to append MigrationChange records to.
        warnings: List to append warning messages to.
    """
    # Placeholder for future 1.x migrations
    # Example migrations that could be added:
    # - 1.0 -> 1.1: Rename field X to Y
    # - 1.1 -> 1.2: Add default value for new optional field Z
    pass
