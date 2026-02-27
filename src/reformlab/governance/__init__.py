"""Governance subsystem for reproducibility, lineage, and auditability.

This module provides immutable run manifests for documenting all parameters,
data sources, and assumptions used in simulation runs. Manifests support
integrity verification, deterministic serialization, and tamper detection.

Public API:
    RunManifest: Immutable manifest schema with integrity hashing
    ManifestIntegrityError: Raised on tampering detection
    ManifestValidationError: Raised on schema validation failures
    LineageIntegrityError: Raised on lineage validation failures
    LineageGraph: Lineage graph query model
    get_lineage: Extract lineage graph from manifest
    validate_lineage: Validate bidirectional lineage integrity
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
    LineageIntegrityError,
    ManifestIntegrityError,
    ManifestValidationError,
)
from reformlab.governance.lineage import (
    LineageGraph,
    get_lineage,
    validate_lineage,
)
from reformlab.governance.manifest import RunManifest

__all__ = [
    "RunManifest",
    "ManifestIntegrityError",
    "ManifestValidationError",
    "LineageIntegrityError",
    "LineageGraph",
    "get_lineage",
    "validate_lineage",
    "capture_assumptions",
    "capture_mappings",
    "capture_parameters",
    "capture_warnings",
]
