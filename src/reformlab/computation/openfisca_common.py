"""Shared OpenFisca version detection and validation utilities.

Used by both ``OpenFiscaAdapter`` (pre-computed mode) and
``OpenFiscaApiAdapter`` (live API mode).

Version compatibility data is derived from the compatibility matrix
(``compat_matrix.yaml``) — this module no longer hardcodes a static
supported-versions list.
"""

from __future__ import annotations

from reformlab.computation.compat_matrix import load_matrix
from reformlab.computation.exceptions import CompatibilityError


def _supported_versions() -> list[str]:
    """Return the list of supported versions from the compatibility matrix."""
    matrix = load_matrix()
    return [
        v
        for v, entry in matrix["versions"].items()
        if entry.get("status") == "supported"
    ]


# Module-level attributes kept for backward-compatible import access.
# These are properties of the matrix, not hardcoded constants.
SUPPORTED_VERSIONS: list[str] = _supported_versions()
MIN_SUPPORTED: str = load_matrix()["min_supported"]
COMPAT_MATRIX_URL: str = load_matrix()["matrix_url"]


def _detect_openfisca_version() -> str:
    """Detect the installed OpenFisca-Core version via importlib.metadata."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("openfisca-core")
    except PackageNotFoundError:
        return "not-installed"


def _check_version(actual: str) -> None:
    """Raise CompatibilityError if *actual* is not in the supported set."""
    supported = _supported_versions()
    expected_versions = ", ".join(supported)

    if actual == "not-installed":
        raise CompatibilityError(
            expected=expected_versions,
            actual=actual,
            details=(
                "openfisca-core is not installed. "
                f"Install it with: uv add 'openfisca-core>={MIN_SUPPORTED}'. "
                f"See {COMPAT_MATRIX_URL}"
            ),
        )

    if actual not in supported:
        raise CompatibilityError(
            expected=expected_versions,
            actual=actual,
            details=(
                f"Unsupported version. Supported versions: {expected_versions}. "
                f"See {COMPAT_MATRIX_URL}"
            ),
        )
