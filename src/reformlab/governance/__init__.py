"""Governance subsystem for reproducibility, lineage, and auditability.

This module provides immutable run manifests for documenting all parameters,
data sources, and assumptions used in simulation runs. Manifests support
integrity verification, deterministic serialization, and tamper detection.

Public API:
    RunManifest: Immutable manifest schema with integrity hashing
    ManifestIntegrityError: Raised on tampering detection
    ManifestValidationError: Raised on schema validation failures
"""

from reformlab.governance.errors import (
    ManifestIntegrityError,
    ManifestValidationError,
)
from reformlab.governance.manifest import RunManifest

__all__ = [
    "RunManifest",
    "ManifestIntegrityError",
    "ManifestValidationError",
]
