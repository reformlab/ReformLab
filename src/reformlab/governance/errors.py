"""Governance-layer errors for manifest integrity and validation.

This module defines explicit error types for manifest operations:
- ManifestIntegrityError: Detected tampering or hash mismatches
- ManifestValidationError: Schema validation failures, missing fields, invalid formats
"""

from __future__ import annotations


class ManifestIntegrityError(Exception):
    """Raised when manifest integrity verification fails.

    Indicates that manifest content has been altered after integrity hash
    computation, or the integrity hash does not match the manifest content.
    """

    pass


class ManifestValidationError(Exception):
    """Raised when manifest validation fails.

    Indicates missing required fields, invalid field types, invalid hash
    formats, or other structural validation issues.
    """

    pass


class LineageIntegrityError(Exception):
    """Raised when lineage integrity validation fails.

    Indicates that parent-child manifest relationships are broken or
    inconsistent, such as mismatched lineage IDs between parent and child
    manifests.
    """

    pass


class ReproducibilityValidationError(Exception):
    """Raised when reproducibility check inputs violate contract requirements.

    Indicates invalid tolerance settings, missing required artifact path mappings,
    or other reproducibility harness precondition failures.
    """

    pass


class ReplicationPackageError(Exception):
    """Raised when replication package export fails.

    Indicates invalid simulation result state, missing required artifacts,
    or invalid output path configuration.

    Story 16.1 / FR54.
    """

    pass
