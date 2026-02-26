"""Compatibility matrix loader and query API for OpenFisca version support.

Provides ``get_compatibility_info()`` to query structured compatibility
details for any OpenFisca-Core version, and ``load_matrix()`` to access
the raw YAML data.

The matrix YAML file (``compat_matrix.yaml``) is the single source of
truth for supported-version policy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_MATRIX_PATH = Path(__file__).parent / "compat_matrix.yaml"
_REQUIRED_KEYS = ("schema_version", "matrix_url", "min_supported", "versions")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

_cache: dict[str, Any] | None = None


@dataclass(frozen=True)
class CompatibilityInfo:
    """Structured compatibility details for an OpenFisca-Core version."""

    version: str
    status: str  # "supported", "untested", or "unsupported"
    modes_tested: tuple[str, ...]
    known_issues: tuple[str, ...]
    tested_date: str | None
    guidance: str
    matrix_url: str


def load_matrix() -> dict[str, Any]:
    """Load and cache the compatibility matrix from YAML.

    Raises ``ValueError`` if required keys are missing.
    """
    global _cache  # noqa: PLW0603
    if _cache is not None:
        return _cache

    with open(_MATRIX_PATH) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        msg = "Compatibility matrix YAML must be a mapping"
        raise ValueError(msg)

    for key in _REQUIRED_KEYS:
        if key not in data:
            msg = f"Compatibility matrix missing required key: {key}"
            raise ValueError(msg)

    matrix_url = data["matrix_url"]
    if not isinstance(matrix_url, str) or not matrix_url.strip():
        msg = "Compatibility matrix key 'matrix_url' must be a non-empty string"
        raise ValueError(msg)

    _cache = data
    return data


def _clear_cache() -> None:
    """Clear the cached matrix data (for testing)."""
    global _cache  # noqa: PLW0603
    _cache = None


def get_compatibility_info(version: str) -> CompatibilityInfo:
    """Return structured compatibility details for *version*.

    - Versions explicitly listed in the matrix return their stored metadata.
    - Versions >= ``min_supported`` but not listed are ``untested``.
    - Versions below ``min_supported`` or invalid are ``unsupported``.
    """
    version = version.strip()
    matrix = load_matrix()
    matrix_url: str = matrix["matrix_url"]
    min_supported: str = matrix["min_supported"]
    versions: dict[str, Any] = matrix["versions"]

    # Explicit entry in matrix
    if version in versions:
        entry = versions[version]
        return CompatibilityInfo(
            version=version,
            status=entry.get("status", "untested"),
            modes_tested=tuple(entry.get("modes_tested", ())),
            known_issues=tuple(entry.get("known_issues", ())),
            tested_date=entry.get("tested_date"),
            guidance=entry.get("guidance", ""),
            matrix_url=matrix_url,
        )

    # Not in matrix — classify based on version comparison
    if _is_valid_semver(version) and _version_gte(version, min_supported):
        return CompatibilityInfo(
            version=version,
            status="untested",
            modes_tested=(),
            known_issues=(),
            tested_date=None,
            guidance=(
                f"Version {version} is not listed in the compatibility matrix. "
                f"It may work but has not been validated. "
                f"See {matrix_url}"
            ),
            matrix_url=matrix_url,
        )

    # Below min_supported, invalid, or special strings like "not-installed"
    return CompatibilityInfo(
        version=version,
        status="unsupported",
        modes_tested=(),
        known_issues=(),
        tested_date=None,
        guidance=(
            f"Version {version} is unsupported. "
            f"Minimum supported version is {min_supported}. "
            f"See {matrix_url}"
        ),
        matrix_url=matrix_url,
    )


def _is_valid_semver(version: str) -> bool:
    """Check if *version* looks like a semantic version string."""
    return bool(_SEMVER_RE.match(version))


def _version_gte(a: str, b: str) -> bool:
    """Return True if semver *a* >= semver *b*."""
    return _parse_version(a) >= _parse_version(b)


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a dotted version string into a tuple of ints."""
    return tuple(int(x) for x in v.split("."))
