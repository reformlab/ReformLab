"""Scenario registry with immutable versioning.

This module provides a file-based scenario registry that stores versioned
scenario definitions with content-addressable version IDs.

Key features:
- Content-addressable version IDs (SHA-256 prefix)
- Immutable scenarios: once saved, definitions cannot be modified
- Version history tracking with timestamps and change descriptions
- File-based persistence for portability and version control
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from reformlab.templates.loader import _parameters_to_dict
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
                f"Version '{version_id}' does not exist "
                f"for scenario '{scenario_name}'"
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
    """Metadata for a scenario in the registry."""

    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]


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

    # Serialize parameters
    data["parameters"] = _parameters_to_dict(scenario.parameters)

    return data


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
        scenario: BaselineScenario | ReformScenario,
        name: str,
        change_description: str = "",
    ) -> str:
        """Save a scenario to the registry.

        If the scenario content matches an existing version, the existing
        version ID is returned (idempotent save).

        Args:
            scenario: The scenario to save.
            name: The name to store the scenario under.
            change_description: Optional description of changes from the
                previous version.

        Returns:
            The version ID of the saved scenario.

        Raises:
            RegistryError: If there's a conflict with existing data.
        """
        self.initialize()

        version_id = _generate_version_id(scenario)
        scenario_dir = self._path / name
        versions_dir = scenario_dir / "versions"
        version_file = versions_dir / f"{version_id}.yaml"
        metadata_file = scenario_dir / "metadata.yaml"

        # Check if this exact version already exists
        if version_file.exists():
            # Verify content matches (idempotent save)
            existing = self._load_scenario_file(version_file)
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
                    scenario_name=name,
                    version_id=version_id,
                )

        # Create directory structure
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Get previous version info if exists
        parent_version: str | None = None
        now = datetime.now(timezone.utc)

        if metadata_file.exists():
            metadata = self._load_metadata(metadata_file)
            parent_version = metadata["latest_version"]
            created = datetime.fromisoformat(metadata["created"])
        else:
            created = now

        # Save the scenario file atomically
        self._save_scenario_file(scenario, version_file)

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
            metadata["versions"].append(new_version)
        else:
            metadata = {
                "name": name,
                "created": created.isoformat(),
                "latest_version": version_id,
                "versions": [new_version],
            }

        self._save_metadata(metadata, metadata_file)

        return version_id

    def get(
        self,
        name: str,
        version_id: str | None = None,
    ) -> BaselineScenario | ReformScenario:
        """Get a scenario by name and optional version.

        Args:
            name: The scenario name.
            version_id: The version ID. If None, returns the latest version.

        Returns:
            The scenario.

        Raises:
            ScenarioNotFoundError: If the scenario doesn't exist.
            VersionNotFoundError: If the version doesn't exist.
        """
        scenario_dir = self._path / name

        if not scenario_dir.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(name, available)

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(name, available)

        metadata = self._load_metadata(metadata_file)

        if version_id is None:
            version_id = metadata["latest_version"]

        version_file = scenario_dir / "versions" / f"{version_id}.yaml"
        if not version_file.exists():
            available_versions = [v["version_id"] for v in metadata["versions"]]
            raise VersionNotFoundError(name, version_id, available_versions)

        return self._load_scenario_file(version_file)

    def list_scenarios(self) -> list[str]:
        """List all scenario names in the registry.

        Returns:
            List of scenario names.
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
        scenario_dir = self._path / name

        if not scenario_dir.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(name, available)

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(name, available)

        metadata = self._load_metadata(metadata_file)
        versions = []
        for v in metadata["versions"]:
            versions.append(
                ScenarioVersion(
                    version_id=v["version_id"],
                    timestamp=datetime.fromisoformat(v["timestamp"]),
                    parent_version=v.get("parent_version"),
                    change_description=v.get("change_description", ""),
                )
            )
        return versions

    def exists(self, name: str, version_id: str | None = None) -> bool:
        """Check if a scenario or version exists.

        Args:
            name: The scenario name.
            version_id: Optional version ID. If None, checks if the scenario
                exists at all.

        Returns:
            True if the scenario/version exists, False otherwise.
        """
        scenario_dir = self._path / name
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
        """Get full registry entry metadata for a scenario.

        Args:
            name: The scenario name.

        Returns:
            RegistryEntry with full metadata.

        Raises:
            ScenarioNotFoundError: If the scenario doesn't exist.
        """
        scenario_dir = self._path / name

        if not scenario_dir.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(name, available)

        metadata_file = scenario_dir / "metadata.yaml"
        if not metadata_file.exists():
            available = self.list_scenarios()
            raise ScenarioNotFoundError(name, available)

        metadata = self._load_metadata(metadata_file)
        versions = []
        for v in metadata["versions"]:
            versions.append(
                ScenarioVersion(
                    version_id=v["version_id"],
                    timestamp=datetime.fromisoformat(v["timestamp"]),
                    parent_version=v.get("parent_version"),
                    change_description=v.get("change_description", ""),
                )
            )

        return RegistryEntry(
            name=metadata["name"],
            created=datetime.fromisoformat(metadata["created"]),
            latest_version=metadata["latest_version"],
            versions=tuple(versions),
        )

    def _save_scenario_file(
        self,
        scenario: BaselineScenario | ReformScenario,
        path: Path,
    ) -> None:
        """Save a scenario to a YAML file atomically.

        Uses atomic write pattern (temp file + replace) for single-machine safety.
        """
        data = _scenario_to_dict_for_registry(scenario)

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

    def _load_scenario_file(self, path: Path) -> BaselineScenario | ReformScenario:
        """Load a scenario from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

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

        # Parse parameters
        params = self._dict_to_parameters(policy_type, data.get("parameters", {}))

        if baseline_ref:
            return ReformScenario(
                name=name,
                policy_type=policy_type,
                baseline_ref=str(baseline_ref),
                parameters=params,
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
                parameters=params,
                description=description,
                version=version,
                schema_ref=schema_ref,
            )

    def _dict_to_parameters(
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
