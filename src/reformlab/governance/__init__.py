"""Governance subsystem for reproducibility, lineage, and auditability.

This module provides immutable run manifests for documenting all parameters,
data sources, and assumptions used in simulation runs. Manifests support
integrity verification, deterministic serialization, and tamper detection.

Public API:
    RunManifest: Immutable manifest schema with integrity hashing
    ManifestIntegrityError: Raised on tampering detection
    ManifestValidationError: Raised on schema validation failures
    capture_assumptions: Capture structured assumption entries
    capture_mappings: Capture mapping configuration
    capture_parameters: Capture parameter snapshot
    capture_warnings: Capture warnings for manifest
"""

from reformlab.governance.capture import (
    capture_assumptions,
    capture_mappings,
    capture_parameters,
    capture_warnings,
)
from reformlab.governance.errors import (
    ManifestIntegrityError,
    ManifestValidationError,
)
from reformlab.governance.manifest import RunManifest

__all__ = [
    "RunManifest",
    "ManifestIntegrityError",
    "ManifestValidationError",
    "capture_assumptions",
    "capture_mappings",
    "capture_parameters",
    "capture_warnings",
]
