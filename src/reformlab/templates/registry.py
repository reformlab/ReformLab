"""Scenario and portfolio registry with immutable versioning.

This module provides a file-based registry that stores versioned scenario
definitions and policy portfolios with content-addressable version IDs.

Key features:
- Content-addressable version IDs (SHA-256 prefix)
- Immutable artifacts: once saved, a version cannot be modified
- Version history tracking with timestamps and change descriptions
- File-based persistence for portability and version control
- Portfolio support: PolicyPortfolio objects alongside BaselineScenario/ReformScenario
- Type-distinguishable listing via entry_type field and list_portfolios()

Story 12.4: Extend Scenario Registry with Portfolio Versioning
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from reformlab.templates.loader import SCHEMA_VERSION, _policy_to_dict
from reformlab.templates.migration import (
    CompatibilityStatus,
    MigrationReport,
    migrate_scenario_dict,
)
from reformlab.templates.portfolios.composition import (
    dict_to_portfolio,
    portfolio_to_dict,
)
from reformlab.templates.portfolios.portfolio import PolicyPortfolio
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    SubsidyParameters,
    YearSchedule,
)

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Base exception for registry operations.

    Provides actionable error messages with:
    - summary: Brief description of what failed
    - reason: Technical explanation of why it failed
    - fix: Actionable guidance on how to resolve the issue
    - scenario_name: Name of the scenario involved (if applicable)
    - version_id: Version ID involved (if applicable)
    """

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        scenario_name: str = "",
        version_id: str = "",
    ) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        self.scenario_name = scenario_name
        self.version_id = version_id
        message = f"{summary}: {reason}"
        if scenario_name:
            message += f" (scenario: {scenario_name})"
        if version_id:
            message += f" (version: {version_id})"
        super().__init__(message)


class ScenarioNotFoundError(RegistryError):
    """Exception raised when a scenario is not found in the registry."""

    def __init__(
        self,
        scenario_name: str,
        available_scenarios: list[str] | None = None,
    ) -> None:
        available = available_scenarios or []
        suggestion = ""
        if available:
            suggestion = f" Available scenarios: {', '.join(available[:5])}"
            if len(available) > 5:
                suggestion += f" (and {len(available) - 5} more)"
        super().__init__(
            summary="Scenario not found",
            reason=f"No scenario named '{scenario_name}' exists in the registry",
            fix=f"Use list_scenarios() to see available scenarios.{suggestion}",
            scenario_name=scenario_name,
        )


class VersionNotFoundError(RegistryError):
    """Exception raised when a version is not found for a scenario."""

    def __init__(
        self,
        scenario_name: str,
        version_id: str,
        available_versions: list[str] | None = None,
    ) -> None:
        available = available_versions or []
        suggestion = ""
        if available:
            suggestion = f" Available versions: {', '.join(available[:5])}"
            if len(available) > 5:
                suggestion += f" (and {len(available) - 5} more)"
        super().__init__(
            summary="Version not found",
            reason=(
                f"Version '{version_id}' does not exist for scenario '{scenario_name}'"
            ),
            fix=(
                f"Use list_versions('{scenario_name}') to see "
                f"available versions.{suggestion}"
            ),
            scenario_name=scenario_name,
            version_id=version_id,
        )


@dataclass(frozen=True)
class ScenarioVersion:
    """Metadata for a single scenario version."""

    version_id: str
    timestamp: datetime
    parent_version: str | None
    change_description: str


@dataclass(frozen=True)
class RegistryEntry:
    """Metadata for a registry entry (scenario or portfolio).

    Attributes:
        entry_type: One of "baseline", "reform", "portfolio", or "scenario"
            (default for backward compatibility).
    """

    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]
    entry_type: str = "scenario"


# Default registry location
_DEFAULT_REGISTRY_PATH = Path.home() / ".reformlab" / "registry"


def _get_default_registry_path() -> Path:
    """Get the default registry path, checking environment variable first."""
    env_path = os.environ.get("REFORMLAB_REGISTRY_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_REGISTRY_PATH


def _scenario_to_dict_for_registry(
    scenario: BaselineScenario | ReformScenario,
) -> dict[str, Any]:
    """Convert a scenario to a dictionary for registry storage.

    Unlike the loader's _scenario_to_dict, this preserves the exact
    schema_ref value (including empty string) for round-trip fidelity.
    """
    data: dict[str, Any] = {}

    # Preserve exact schema_ref value (don't default)
    data["$schema"] = scenario.schema_ref

    data["version"] = scenario.version
    data["name"] = scenario.name
    if scenario.description:
        data["description"] = scenario.description
    assert scenario.policy_type is not None  # Always set after __post_init__
    data["policy_type"] = scenario.policy_type.value

    # Add baseline_ref for reforms
    if isinstance(scenario, ReformScenario):
        data["baseline_ref"] = scenario.baseline_ref
        if scenario.year_schedule:
            data["year_schedule"] = {
                "start_year": scenario.year_schedule.start_year,
                "end_year": scenario.year_schedule.end_year,
            }
    else:
        data["year_schedule"] = {
            "start_year": scenario.year_schedule.start_year,
            "end_year": scenario.year_schedule.end_year,
        }

    # Serialize policy
    data["policy"] = _policy_to_dict(scenario.policy)

    return data


def _portfolio_to_dict_for_registry(portfolio: PolicyPortfolio) -> dict[str, Any]:
    """Convert a portfolio to a dictionary for registry storage.

    Uses portfolio_to_dict() as base but normalizes $schema to a stable
    relative path for cross-machine version ID determinism, and adds
    _registry_type marker for type discrimination.
    """
    data = portfolio_to_dict(portfolio)
    # Normalize $schema to stable relative path (portfolio_to_dict emits
    # machine-specific absolute path via Path(__file__))
    data["$schema"] = "portfolio.schema.json"
    # Add registry type marker for standalone version file identification
    data["_registry_type"] = "portfolio"
    return data


def _dict_to_portfolio_from_registry(data: dict[str, Any]) -> PolicyPortfolio:
    """Reconstruct a PolicyPortfolio from registry YAML dict.

    Strips _registry_type marker before delegating to dict_to_portfolio().
    """
    clean = {k: v for k, v in data.items() if k != "_registry_type"}
    return dict_to_portfolio(clean)


def _generate_portfolio_version_id(portfolio: PolicyPortfolio) -> str:
    """Generate deterministic version ID from portfolio content.

    Uses SHA-256 hash of the serialized portfolio content (with sorted keys)
    to produce a 12-character version ID. Includes _registry_type in the hash
    to prevent collisions with scenario version IDs.

    Args:
        portfolio: The portfolio to hash.

    Returns:
        A 12-character hexadecimal version ID.
    """
    content = _portfolio_to_dict_for_registry(portfolio)
    yaml_str = yaml.dump(content, sort_keys=True)
    return hashlib.sha256(yaml_str.encode("utf-8")).hexdigest()[:12]


def _infer_registry_type(scenario_name: str, metadata: dict[str, Any], registry_path: Path) -> str:
    """Infer _registry_type for legacy entries without the field.

    Loads the latest version file and checks for baseline_ref to determine
    if the entry is a baseline or reform scenario.

    Args:
        scenario_name: The entry name.
        metadata: The metadata dict.
        registry_path: The registry root path.

    Returns:
        "reform" if baseline_ref present, "baseline" otherwise.
    """
    latest_version = metadata.get("latest_version", "")
    if not latest_version:
        return "baseline"

    version_file = registry_path / scenario_name / "versions" / f"{latest_version}.yaml"
    if not version_file.exists():
        return "baseline"

    with open(version_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict) and data.get("baseline_ref"):
        return "reform"
    return "baseline"


def _get_registry_type_for_artifact(
    artifact: BaselineScenario | ReformScenario | PolicyPortfolio,
) -> str:
    """Determine _registry_type string for an artifact."""
    if isinstance(artifact, PolicyPortfolio):
        return "portfolio"
    if isinstance(artifact, ReformScenario):
        return "reform"
    return "baseline"


def _validate_scenario_name(name: str) -> str:
    """Validate and normalize a scenario key used as a registry directory."""
    normalized = name.strip()
    if not normalized:
        raise RegistryError(
            summary="Invalid scenario name",
            reason="Scenario name must be a non-empty string",
            fix="Provide a non-empty scenario name, for example: 'carbon-tax-2026'",
            scenario_name=name,
        )

    if "/" in normalized or "\\" in normalized:
        raise RegistryError(
            summary="Invalid scenario name",
            reason="Scenario name cannot include path separators",
            fix="Use a plain name without '/' or '\\\\' characters",
            scenario_name=normalized,
        )

    path = Path(normalized)
    if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        raise RegistryError(
            summary="Invalid scenario name",
            reason="Scenario name cannot be absolute or use path traversal",
            fix="Use a simple relative name, for example: 'scenario-alpha'",
            scenario_name=normalized,
        )

    return normalized


def _generate_version_id(scenario: BaselineScenario | ReformScenario) -> str:
    """Generate deterministic version ID from scenario content.

    Uses SHA-256 hash of the serialized scenario content (with sorted keys)
    to produce a 12-character version ID.

    Args:
        scenario: The scenario to hash.

    Returns:
        A 12-character hexadecimal version ID.
    """
    content = _scenario_to_dict_for_registry(scenario)
    yaml_str = yaml.dump(content, sort_keys=True)
    hash_bytes = hashlib.sha256(yaml_str.encode("utf-8")).hexdigest()[:12]
    return hash_bytes


class ScenarioRegistry:
    """File-based scenario registry with immutable versioning.

    The registry stores scenarios in a structured directory format:
        {registry_path}/
        ├── {scenario_name}/
        │   ├── metadata.yaml
        │   └── versions/
        │       ├── {version_id}.yaml
        │       └── ...
        └── ...

    Scenarios are immutable: once saved, a version cannot be modified.
    Modifying a scenario creates a new version with a new version ID.
    """

    def __init__(self, registry_path: Path | str | None = None) -> None:
        """Initialize the registry at the given path.

        Args:
            registry_path: Path to the registry directory. If None, uses
                environment variable REFORMLAB_REGISTRY_PATH or defaults
                to ~/.reformlab/registry/.
        """
        if registry_path is None:
            self._path = _get_default_registry_path()
        else:
            self._path = Path(registry_path)

    @property
    def path(self) -> Path:
        """Return the registry path."""
        return self._path

    def initialize(self) -> None:
        """Initialize the registry directory structure.

        Creates the registry directory if it doesn't exist.
        """
        self._path.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        scenario: BaselineScenario | ReformScenario | PolicyPortfolio,
        name: str,
        change_description: str = "",
    ) -> str:
        """Save a scenario or portfolio to the registry.

        If the content matches an existing version, the existing
        version ID is returned (idempotent save).

        Args:
            scenario: The scenario or portfolio to save.
            name: The name to store the entry under.
            change_description: Optional description of changes from the
                previous version.

        Returns:
            The version ID of the saved entry.

        Raises:
            RegistryError: If there's a conflict with existing data.
        """
        self.initialize()

        scenario_name = _validate_scenario_name(name)
        is_portfolio = isinstance(scenario, PolicyPortfolio)
        incoming_type = _get_registry_type_for_artifact(scenario)

        # Generate version ID based on artifact type
        if isinstance(scenario, PolicyPortfolio):
            version_id = _generate_portfolio_version_id(scenario)
        else:
            version_id = _generate_version_id(scenario)

        scenario_dir = self._path / scenario_name
        versions_dir = scenario_dir / "versions"
        version_file = versions_dir / f"{version_id}.yaml"
        metadata_file = scenario_dir / "metadata.yaml"

        # Type-consistency guard: reject type mismatches with existing entries
        if metadata_file.exists():
            existing_metadata = self._load_metadata(metadata_file)
            stored_type = existing_metadata.get("_registry_type")
            if stored_type is None:
                # Legacy entry: infer type
                stored_type = _infer_registry_type(
                    scenario_name, existing_metadata, self._path
                )
            if stored_type != incoming_type:
                raise RegistryError(
                    summary="Entry type mismatch",
                    reason=(
                        f"Registry entry '{scenario_name}' is a {stored_type}, "
                        f"but received a {incoming_type}"
                    ),
                    fix="Use a different name or save as the correct type",
                    scenario_name=scenario_name,
                )

        # Check if this exact version already exists
        if version_file.exists():
            # Verify content matches (idempotent save)
            existing = self._load_entry_file(version_file)
            self._ensure_version_integrity(
                artifact=existing,
                expected_version_id=version_id,
                scenario_name=scenario_name,
            )
            if existing == scenario:
                return version_id
            else:
                raise RegistryError(
                    summary="Version conflict",
                    reason="A version with this ID exists but has different content",
                    fix=(
                        "This should not happen with content-addressable IDs. "
                        "Check for hash collisions."
                    ),
                    scenario_name=scenario_name,
                    version_id=version_id,
                )

        # Create directory structure
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Get previous version info if exists
        parent_version: str | None = None
        now = datetime.now(timezone.utc)

        if metadata_file.exists():
            metadata = self._load_metadata(metadata_file)
            metadata_name = str(metadata.get("name", ""))
            if metadata_name and metadata_name != scenario_name:
                raise RegistryError(
                    summary="Corrupted registry metadata",
                    reason=(
                        f"Scenario metadata name '{metadata_name}' does not match "
                        f"directory name '{scenario_name}'"
                    ),
                    fix="Repair or recreate metadata.yaml for this scenario",
                    scenario_name=scenario_name,
                )
            parent_version = metadata["latest_version"]
            created = datetime.fromisoformat(metadata["created"])
        else:
            created = now

        # Save the version file atomically
        self._save_entry_file(scenario, version_file)

        # Build version entry
        new_version = {
            "version_id": version_id,
            "timestamp": now.isoformat(),
            "parent_version": parent_version,
            "change_description": change_description,
        }

        # Update metadata
        if metadata_file.exists():
            metadata = self._load_metadata(metadata_file)
            metadata["latest_version"] = version_id
            metadata["_registry_type"] = incoming_type
            metadata["versions"].append(new_version)
        else:
            metadata = {
                "name": scenario_name,
                "created": created.isoformat(),
                "latest_version": version_id,
                "_registry_type": incoming_type,
                "versions": [new_version],
            }

        self._save_metadata(metadata, metadata_file)

        return version_id

    def get(
        self,
        name: str,
        version_id: str | None = None,
    ) -> BaselineScenario | ReformScenario | PolicyPortfolio:
        """Get a scenario or portfolio by name and optional version.

        Args:
            name: The entry name.
            version_id: The version ID. If None, returns the latest version.

        Returns:
            The scenario or portfolio.

        Raises:
            ScenarioNotFoundError: If the entry doesn't exist.
            VersionNotFoundError: If the version doesn't exist.
        """
        scenario_name = _validate_scenario_name(name)
        scenario_dir = self._path / scenario_name

        if not scenario_dir.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(scenario_name, available)

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(scenario_name, available)

        metadata = self._load_metadata(metadata_file)
        versions = self._versions_from_metadata(metadata, scenario_name=scenario_name)
        available_versions = [v.version_id for v in versions]

        if version_id is None:
            latest_version = metadata.get("latest_version")
            if not isinstance(latest_version, str) or not latest_version:
                raise RegistryError(
                    summary="Corrupted registry metadata",
                    reason="Missing or invalid latest_version in metadata",
                    fix="Repair metadata.yaml for this scenario",
                    scenario_name=scenario_name,
                )
            version_id = latest_version

        if version_id not in available_versions:
            raise VersionNotFoundError(scenario_name, version_id, available_versions)

        version_file = scenario_dir / "versions" / f"{version_id}.yaml"
        if not version_file.exists():
            raise RegistryError(
                summary="Registry data missing",
                reason=(
                    f"Metadata references version '{version_id}' but the version "
                    "file is missing"
                ),
                fix="Restore the missing version file or repair metadata.yaml",
                scenario_name=scenario_name,
                version_id=version_id,
            )

        loaded = self._load_entry_file(version_file)
        self._ensure_version_integrity(
            artifact=loaded,
            expected_version_id=version_id,
            scenario_name=scenario_name,
        )
        return loaded

    def list_scenarios(self) -> list[str]:
        """List all entry names in the registry (scenarios and portfolios).

        Returns all registry entries regardless of type. Use list_portfolios()
        or get_entry_type() to filter by type.

        Returns:
            List of entry names.
        """
        if not self._path.exists():
            return []

        scenarios = []
        for item in self._path.iterdir():
            if item.is_dir() and (item / "metadata.yaml").exists():
                scenarios.append(item.name)

        return sorted(scenarios)

    def list_versions(self, name: str) -> list[ScenarioVersion]:
        """List version history for a scenario.

        Args:
            name: The scenario name.

        Returns:
            List of ScenarioVersion objects, ordered by timestamp (oldest first).

        Raises:
            ScenarioNotFoundError: If the scenario doesn't exist.
        """
        scenario_name = _validate_scenario_name(name)
        scenario_dir = self._path / scenario_name

        if not scenario_dir.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(scenario_name, available)

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(scenario_name, available)

        metadata = self._load_metadata(metadata_file)
        return self._versions_from_metadata(metadata, scenario_name=scenario_name)

    def exists(self, name: str, version_id: str | None = None) -> bool:
        """Check if a scenario or version exists.

        Args:
            name: The scenario name.
            version_id: Optional version ID. If None, checks if the scenario
                exists at all.

        Returns:
            True if the scenario/version exists, False otherwise.
        """
        try:
            scenario_name = _validate_scenario_name(name)
        except RegistryError:
            return False

        scenario_dir = self._path / scenario_name
        if not scenario_dir.exists():
            return False

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            return False

        if version_id is None:
            return True

        version_file = scenario_dir / "versions" / f"{version_id}.yaml"
        return version_file.exists()

    def get_entry(self, name: str) -> RegistryEntry:
        """Get full registry entry metadata for a scenario or portfolio.

        Args:
            name: The entry name.

        Returns:
            RegistryEntry with full metadata including entry_type.

        Raises:
            ScenarioNotFoundError: If the entry doesn't exist.
        """
        scenario_name = _validate_scenario_name(name)
        scenario_dir = self._path / scenario_name

        if not scenario_dir.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(scenario_name, available)

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(scenario_name, available)

        metadata = self._load_metadata(metadata_file)
        versions = self._versions_from_metadata(metadata, scenario_name=scenario_name)

        entry_type = self.get_entry_type(name)

        return RegistryEntry(
            name=metadata["name"],
            created=datetime.fromisoformat(metadata["created"]),
            latest_version=metadata["latest_version"],
            versions=tuple(versions),
            entry_type=entry_type,
        )

    def get_entry_type(self, name: str) -> str:
        """Get the entry type for a registry entry.

        Args:
            name: The entry name.

        Returns:
            One of "baseline", "reform", or "portfolio".

        Raises:
            ScenarioNotFoundError: If the entry doesn't exist.
        """
        scenario_name = _validate_scenario_name(name)
        scenario_dir = self._path / scenario_name
        metadata_file = scenario_dir / "metadata.yaml"

        if not metadata_file.exists():
            raise ScenarioNotFoundError(scenario_name, self.list_scenarios())

        metadata = self._load_metadata(metadata_file)
        stored_type = metadata.get("_registry_type")

        if stored_type is not None:
            return str(stored_type)

        # Legacy entry: infer type from content
        inferred = _infer_registry_type(scenario_name, metadata, self._path)

        # Persist inferred type for future reads
        metadata["_registry_type"] = inferred
        self._save_metadata(metadata, metadata_file)

        return inferred

    def list_portfolios(self) -> list[str]:
        """List all portfolio names in the registry.

        Returns:
            List of portfolio entry names.
        """
        result = []
        for entry_name in self.list_scenarios():
            try:
                if self.get_entry_type(entry_name) == "portfolio":
                    result.append(entry_name)
            except RegistryError:
                logger.warning(
                    "event=list_portfolios_skip entry=%s reason=corrupted_metadata",
                    entry_name,
                )
                continue
        return result

    def clone(
        self,
        name: str,
        version_id: str | None = None,
        new_name: str | None = None,
    ) -> BaselineScenario | ReformScenario | PolicyPortfolio:
        """Clone a scenario or portfolio with a new identity.

        Creates an in-memory copy with a new name. The clone is independent
        of the original and can be modified and saved as a new entry.

        Args:
            name: Source entry name.
            version_id: Source version ID (None = latest version).
            new_name: Name for the clone (None = auto-generate as "{name}-clone").

        Returns:
            A new instance with identical parameters but new identity.

        Raises:
            ScenarioNotFoundError: If the source entry doesn't exist.
            VersionNotFoundError: If the specified version doesn't exist.
        """
        original = self.get(name, version_id)
        clone_name = new_name or f"{name}-clone"

        # Use dataclasses.replace for frozen dataclass copy with new name
        return replace(original, name=clone_name)

    def _parse_baseline_ref(self, baseline_ref: str) -> tuple[str, str | None]:
        """Parse baseline_ref into (name, version_id).

        Supports formats:
        - "scenario-name" -> ("scenario-name", None) - latest version
        - "scenario-name@abc123def" -> ("scenario-name", "abc123def") - specific version

        Args:
            baseline_ref: The baseline reference string.

        Returns:
            Tuple of (scenario_name, version_id or None).

        Raises:
            RegistryError: If baseline_ref is malformed.
        """
        normalized = baseline_ref.strip()
        if not normalized:
            raise RegistryError(
                summary="Invalid baseline reference",
                reason="baseline_ref cannot be empty",
                fix=(
                    "Use baseline_ref in the form 'scenario-name' or "
                    "'scenario-name@version_id'"
                ),
            )

        if normalized.startswith("@"):
            raise RegistryError(
                summary="Invalid baseline reference",
                reason=f"baseline_ref '{baseline_ref}' is missing a scenario name",
                fix=(
                    "Use baseline_ref in the form 'scenario-name' or "
                    "'scenario-name@version_id'"
                ),
            )

        if normalized.endswith("@"):
            raise RegistryError(
                summary="Invalid baseline reference",
                reason=f"baseline_ref '{baseline_ref}' is missing a version ID",
                fix=(
                    "Use baseline_ref in the form 'scenario-name' or "
                    "'scenario-name@version_id'"
                ),
            )

        if "@" not in normalized:
            return (_validate_scenario_name(normalized), None)

        name, version = normalized.rsplit("@", 1)
        return (_validate_scenario_name(name), version)

    def get_baseline(
        self,
        reform_name: str,
        version_id: str | None = None,
    ) -> BaselineScenario:
        """Get the baseline scenario linked from a reform.

        Navigates from a reform scenario to its linked baseline using
        the reform's baseline_ref field.

        Args:
            reform_name: Name of the reform scenario.
            version_id: Reform version ID (None = latest version).

        Returns:
            The linked baseline scenario.

        Raises:
            ScenarioNotFoundError: If reform or baseline not found.
            VersionNotFoundError: If specified version not found.
            RegistryError: If the scenario is not a reform (no baseline_ref).

        Example:
            >>> registry.save(baseline, "carbon-tax-2026")
            >>> registry.save(reform, "progressive")  # baseline_ref="carbon-tax-2026"
            >>> baseline = registry.get_baseline("progressive")
        """
        reform = self.get(reform_name, version_id)

        if not isinstance(reform, ReformScenario):
            raise RegistryError(
                summary="Not a reform scenario",
                reason=f"'{reform_name}' is a baseline, not a reform",
                fix="Use get_baseline() only on reform scenarios with baseline_ref",
                scenario_name=reform_name,
            )

        # Parse baseline_ref (supports "name" or "name@version")
        baseline_name, baseline_version = self._parse_baseline_ref(reform.baseline_ref)
        try:
            result = self.get(baseline_name, baseline_version)
        except (ScenarioNotFoundError, VersionNotFoundError):
            ref_display = (
                f"{baseline_name}@{baseline_version}"
                if baseline_version is not None
                else baseline_name
            )
            raise RegistryError(
                summary="Broken baseline link",
                reason=(
                    f"Reform '{reform_name}' references baseline '{ref_display}', "
                    "but that target does not exist"
                ),
                fix=(
                    "Update baseline_ref to an existing baseline scenario "
                    "(optionally pinned with @version_id)"
                ),
                scenario_name=reform_name,
            ) from None

        # Type narrowing: baseline should be BaselineScenario
        if not isinstance(result, BaselineScenario):
            raise RegistryError(
                summary="Invalid baseline reference",
                reason=(
                    f"baseline_ref '{reform.baseline_ref}' points to "
                    "another reform, not a baseline"
                ),
                fix="Update baseline_ref to point to a baseline scenario",
                scenario_name=reform_name,
            )

        return result

    def list_reforms(
        self,
        baseline_name: str,
        version_id: str | None = None,
    ) -> list[tuple[str, str]]:
        """List all reforms that reference a baseline.

        Scans the registry to find all reform scenarios that link to
        the specified baseline (optionally filtered by baseline version).

        Args:
            baseline_name: Name of the baseline scenario.
            version_id: Baseline version ID to match (None = any version referencing
                this baseline name, regardless of pinned version).

        Returns:
            List of (reform_name, reform_version_id) tuples for reforms
            that reference the specified baseline.

        Example:
            >>> reforms = registry.list_reforms("carbon-tax-2026")
            >>> # Returns: [("progressive-dividend", "abc123"), ("lump-sum", "def456")]
        """
        baseline = self.get(baseline_name, version_id)
        if not isinstance(baseline, BaselineScenario):
            raise RegistryError(
                summary="Not a baseline scenario",
                reason=f"'{baseline_name}' is a reform, not a baseline",
                fix=(
                    "Use list_reforms() only with a baseline scenario name "
                    "(and optional baseline version ID)"
                ),
                scenario_name=baseline_name,
                version_id=version_id or "",
            )

        reforms: list[tuple[str, str]] = []

        for scenario_name in self.list_scenarios():
            for version in self.list_versions(scenario_name):
                scenario = self.get(scenario_name, version.version_id)

                if isinstance(scenario, ReformScenario):
                    baseline_ref = scenario.baseline_ref
                    ref_name, ref_version = self._parse_baseline_ref(baseline_ref)

                    if ref_name == baseline_name:
                        # If version_id filter is provided, check if it matches
                        if version_id is None or ref_version == version_id:
                            reforms.append((scenario_name, version.version_id))

        return reforms

    def migrate(
        self,
        name: str,
        version_id: str | None = None,
        *,
        dry_run: bool = True,
    ) -> MigrationReport:
        """Migrate a scenario to the current schema version.

        Args:
            name: Scenario name.
            version_id: Version ID to migrate (None = latest version).
            dry_run: If True, return report without saving. If False, save
                migrated scenario as a new version.

        Returns:
            MigrationReport describing the migration result.

        Raises:
            ScenarioNotFoundError: If scenario doesn't exist.
            VersionNotFoundError: If version doesn't exist.
            RegistryError: If migration fails or entry is a portfolio.
        """
        # Portfolio migration guard
        try:
            entry_type = self.get_entry_type(name)
        except ScenarioNotFoundError:
            entry_type = None

        if entry_type == "portfolio":
            raise RegistryError(
                summary="Migration not supported for portfolios",
                reason=(
                    f"Registry entry '{name}' is a portfolio. "
                    "Portfolio migration is not yet implemented"
                ),
                fix="Portfolio entries cannot be migrated in this version",
                scenario_name=name,
            )

        # Get the scenario (portfolio case is guarded above)
        scenario = self.get(name, version_id)
        assert not isinstance(scenario, PolicyPortfolio)  # Guarded above
        scenario_name = _validate_scenario_name(name)

        # Convert to dict for migration
        data = _scenario_to_dict_for_registry(scenario)

        # Perform migration
        try:
            migrated_data, report = migrate_scenario_dict(
                data, target_version=SCHEMA_VERSION
            )
        except ValueError as exc:
            # Convert ValueError from migrate_scenario_dict to RegistryError
            raise RegistryError(
                summary="Migration failed",
                reason=str(exc),
                fix=(
                    f"Schema version {scenario.version} cannot be migrated to "
                    f"{SCHEMA_VERSION}. Manual conversion may be required."
                ),
                scenario_name=scenario_name,
                version_id=version_id or "",
            ) from exc

        # In dry-run mode, just return the report
        if dry_run:
            return report

        # In apply mode, save the migrated scenario if there were changes
        if report.status == CompatibilityStatus.MIGRATION_AVAILABLE:
            migrated_scenario = self._dict_to_scenario(migrated_data)

            # Determine source version_id for lineage
            if version_id is None:
                entry = self.get_entry(name)
                source_version_id = entry.latest_version
            else:
                source_version_id = version_id

            change_description = (
                f"Migrated from schema version {report.source_version} to "
                f"{report.target_version} (source version: {source_version_id})"
            )

            self.save(migrated_scenario, name, change_description)

        return report

    def set_validated(
        self,
        name: str,
        version_id: str | None = None,
        *,
        validated: bool = True,
    ) -> None:
        """Set validation status for a scenario version.

        Args:
            name: Scenario name.
            version_id: Version ID (None = latest version).
            validated: Whether to mark as validated.

        Raises:
            ScenarioNotFoundError: If scenario doesn't exist.
            VersionNotFoundError: If version doesn't exist.
        """
        scenario_name = _validate_scenario_name(name)
        scenario_dir = self._path / scenario_name
        metadata_file = scenario_dir / "metadata.yaml"

        if not metadata_file.exists():
            raise ScenarioNotFoundError(scenario_name, self.list_scenarios())

        metadata = self._load_metadata(metadata_file)
        versions = metadata.get("versions", [])

        # Resolve version_id
        if version_id is None:
            version_id = metadata.get("latest_version")

        # Find and update the version entry
        for version in versions:
            if version.get("version_id") == version_id:
                version["is_validated"] = validated
                break
        else:
            raise VersionNotFoundError(
                scenario_name,
                version_id or "",
                [v.get("version_id", "") for v in versions],
            )

        self._save_metadata(metadata, metadata_file)

    def is_validated(self, name: str, version_id: str | None = None) -> bool:
        """Check validation status for a scenario version.

        Args:
            name: Scenario name.
            version_id: Version ID (None = latest version).

        Returns:
            True if scenario version is marked as validated, False otherwise.
            Returns False for scenarios without explicit validation status.
        """
        try:
            scenario_name = _validate_scenario_name(name)
        except RegistryError:
            return False

        scenario_dir = self._path / scenario_name
        metadata_file = scenario_dir / "metadata.yaml"

        if not metadata_file.exists():
            return False

        metadata = self._load_metadata(metadata_file)

        if version_id is None:
            version_id = metadata.get("latest_version")

        for version in metadata.get("versions", []):
            if version.get("version_id") == version_id:
                return bool(version.get("is_validated", False))

        return False

    def _ensure_version_integrity(
        self,
        *,
        artifact: BaselineScenario | ReformScenario | PolicyPortfolio,
        expected_version_id: str,
        scenario_name: str,
    ) -> None:
        """Verify artifact content still matches its content-addressable ID."""
        if isinstance(artifact, PolicyPortfolio):
            actual_version_id = _generate_portfolio_version_id(artifact)
        else:
            actual_version_id = _generate_version_id(artifact)

        if actual_version_id != expected_version_id:
            raise RegistryError(
                summary="Registry integrity check failed",
                reason=(
                    f"Version file content hashes to '{actual_version_id}', expected "
                    f"'{expected_version_id}'"
                ),
                fix=(
                    "Restore the original immutable version file content or create "
                    "a new version with save()"
                ),
                scenario_name=scenario_name,
                version_id=expected_version_id,
            )

    def _versions_from_metadata(
        self,
        metadata: dict[str, Any],
        *,
        scenario_name: str,
    ) -> list[ScenarioVersion]:
        """Parse and normalize version metadata records."""
        raw_versions = metadata.get("versions")
        if not isinstance(raw_versions, list):
            raise RegistryError(
                summary="Corrupted registry metadata",
                reason="Metadata field 'versions' must be a list",
                fix="Repair metadata.yaml to include a valid versions list",
                scenario_name=scenario_name,
            )

        versions: list[ScenarioVersion] = []
        for raw_version in raw_versions:
            if not isinstance(raw_version, dict):
                raise RegistryError(
                    summary="Corrupted registry metadata",
                    reason="Version entries must be mapping objects",
                    fix=(
                        "Repair metadata.yaml to ensure each version entry is a mapping"
                    ),
                    scenario_name=scenario_name,
                )

            try:
                parsed = ScenarioVersion(
                    version_id=str(raw_version["version_id"]),
                    timestamp=datetime.fromisoformat(str(raw_version["timestamp"])),
                    parent_version=raw_version.get("parent_version"),
                    change_description=str(raw_version.get("change_description", "")),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise RegistryError(
                    summary="Corrupted registry metadata",
                    reason=f"Invalid version metadata entry: {exc}",
                    fix="Repair metadata.yaml with valid version_id/timestamp fields",
                    scenario_name=scenario_name,
                ) from None

            versions.append(parsed)

        versions.sort(key=lambda entry: entry.timestamp)
        return versions

    def _save_entry_file(
        self,
        artifact: BaselineScenario | ReformScenario | PolicyPortfolio,
        path: Path,
    ) -> None:
        """Save a scenario or portfolio to a YAML file atomically.

        Uses atomic write pattern (temp file + replace) for single-machine safety.
        """
        if isinstance(artifact, PolicyPortfolio):
            data = _portfolio_to_dict_for_registry(artifact)
        else:
            data = _scenario_to_dict_for_registry(artifact)

        # Write to temp file first, then replace
        fd, tmp_path = tempfile.mkstemp(
            suffix=".yaml",
            prefix=".tmp_",
            dir=path.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            os.replace(tmp_path, path)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _load_entry_file(
        self, path: Path,
    ) -> BaselineScenario | ReformScenario | PolicyPortfolio:
        """Load a scenario or portfolio from a YAML file.

        Dispatches to portfolio or scenario deserializer based on
        _registry_type marker in the stored data.
        """
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict) and data.get("_registry_type") == "portfolio":
            return _dict_to_portfolio_from_registry(data)
        return self._dict_to_scenario(data)

    def _save_metadata(self, metadata: dict[str, Any], path: Path) -> None:
        """Save registry metadata atomically."""
        fd, tmp_path = tempfile.mkstemp(
            suffix=".yaml",
            prefix=".tmp_",
            dir=path.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(metadata, f, default_flow_style=False, sort_keys=False)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _load_metadata(self, path: Path) -> dict[str, Any]:
        """Load registry metadata from a YAML file."""
        with open(path, encoding="utf-8") as f:
            result: dict[str, Any] = yaml.safe_load(f)
            return result

    def _dict_to_scenario(
        self,
        data: dict[str, Any],
    ) -> BaselineScenario | ReformScenario:
        """Convert a dictionary to a scenario object.

        This mirrors the loader logic but without file handling.
        """
        policy_type = PolicyType(data["policy_type"])
        name = str(data["name"])
        version = str(data.get("version", "1.0"))
        description = str(data.get("description", ""))
        schema_ref = str(data.get("$schema", ""))
        baseline_ref = data.get("baseline_ref")

        # Parse year_schedule
        year_schedule = None
        if "year_schedule" in data:
            ys = data["year_schedule"]
            year_schedule = YearSchedule(
                start_year=int(ys["start_year"]),
                end_year=int(ys["end_year"]),
            )

        # Parse policy
        params = self._dict_to_policy(policy_type, data.get("policy", {}))

        if baseline_ref:
            return ReformScenario(
                name=name,
                policy_type=policy_type,
                baseline_ref=str(baseline_ref),
                policy=params,
                description=description,
                version=version,
                schema_ref=schema_ref,
                year_schedule=year_schedule,
            )
        else:
            if year_schedule is None:
                raise RegistryError(
                    summary="Invalid scenario data",
                    reason="Baseline scenarios require year_schedule",
                    fix="Ensure the stored scenario has a valid year_schedule",
                    scenario_name=name,
                )
            return BaselineScenario(
                name=name,
                policy_type=policy_type,
                year_schedule=year_schedule,
                policy=params,
                description=description,
                version=version,
                schema_ref=schema_ref,
            )

    def _dict_to_policy(
        self,
        policy_type: PolicyType,
        raw: dict[str, Any],
    ) -> PolicyParameters:
        """Convert a dictionary to policy parameters."""
        # Parse rate_schedule
        rate_schedule: dict[int, float] = {}
        if "rate_schedule" in raw:
            for k, v in raw["rate_schedule"].items():
                rate_schedule[int(k)] = float(v)

        # Parse common fields
        exemptions = tuple(raw.get("exemptions", []))
        thresholds = tuple(raw.get("thresholds", []))
        covered_categories = tuple(raw.get("covered_categories", []))

        if policy_type == PolicyType.CARBON_TAX:
            redistribution_type = ""
            income_weights: dict[str, float] = {}
            if "redistribution" in raw:
                redist = raw["redistribution"]
                if "type" in redist:
                    redistribution_type = str(redist["type"])
                if "income_weights" in redist:
                    for k, v in redist["income_weights"].items():
                        income_weights[str(k)] = float(v)
            return CarbonTaxParameters(
                rate_schedule=rate_schedule,
                exemptions=exemptions,
                thresholds=thresholds,
                covered_categories=covered_categories,
                redistribution_type=redistribution_type,
                income_weights=income_weights,
            )
        elif policy_type == PolicyType.SUBSIDY:
            eligible_categories = tuple(raw.get("eligible_categories", []))
            income_caps: dict[int, float] = {}
            if "income_caps" in raw:
                for k, v in raw["income_caps"].items():
                    income_caps[int(k)] = float(v)
            return SubsidyParameters(
                rate_schedule=rate_schedule,
                exemptions=exemptions,
                thresholds=thresholds,
                covered_categories=covered_categories,
                eligible_categories=eligible_categories,
                income_caps=income_caps,
            )
        elif policy_type == PolicyType.REBATE:
            rebate_type = ""
            rebate_income_weights: dict[str, float] = {}
            if "rebate_type" in raw:
                rebate_type = str(raw["rebate_type"])
            if "income_weights" in raw:
                for k, v in raw["income_weights"].items():
                    rebate_income_weights[str(k)] = float(v)
            if "redistribution" in raw:
                redist = raw["redistribution"]
                if "type" in redist:
                    rebate_type = str(redist["type"])
                if "income_weights" in redist:
                    for k, v in redist["income_weights"].items():
                        rebate_income_weights[str(k)] = float(v)
            return RebateParameters(
                rate_schedule=rate_schedule,
                exemptions=exemptions,
                thresholds=thresholds,
                covered_categories=covered_categories,
                rebate_type=rebate_type,
                income_weights=rebate_income_weights,
            )
        elif policy_type == PolicyType.FEEBATE:
            pivot_point_set = "pivot_point" in raw
            fee_rate_set = "fee_rate" in raw
            rebate_rate_set = "rebate_rate" in raw
            pivot_point = float(raw.get("pivot_point", 0.0))
            fee_rate = float(raw.get("fee_rate", 0.0))
            rebate_rate = float(raw.get("rebate_rate", 0.0))
            return FeebateParameters(
                rate_schedule=rate_schedule,
                exemptions=exemptions,
                thresholds=thresholds,
                covered_categories=covered_categories,
                pivot_point=pivot_point,
                fee_rate=fee_rate,
                rebate_rate=rebate_rate,
                _pivot_point_set=pivot_point_set,
                _fee_rate_set=fee_rate_set,
                _rebate_rate_set=rebate_rate_set,
            )
        else:
            return PolicyParameters(
                rate_schedule=rate_schedule,
                exemptions=exemptions,
                thresholds=thresholds,
                covered_categories=covered_categories,
            )
