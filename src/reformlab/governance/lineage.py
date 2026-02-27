"""Lineage graph query and validation for run manifests.

This module provides:
- LineageGraph: Query model for parent-child relationships
- get_lineage(): Factory function to extract lineage from a manifest
- validate_lineage(): Bidirectional integrity validation

Lineage enables tracing the execution history of scenario runs across
yearly iterations, supporting reproducibility and auditability (FR29).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from reformlab.governance.errors import LineageIntegrityError

if TYPE_CHECKING:
    from reformlab.governance.manifest import RunManifest


@dataclass(frozen=True)
class LineageGraph:
    """Lineage graph for a single manifest with parent/child relationships.

    Provides convenient access to lineage structure and traversal methods.

    Attributes:
        manifest_id: The manifest ID this lineage graph represents.
        parent_id: Parent manifest UUID, or None if this is a root manifest.
        child_ids: Mapping of year to child manifest UUID.
    """

    manifest_id: str
    parent_id: str | None
    child_ids: dict[int, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Copy mutable containers to avoid external aliasing."""
        object.__setattr__(self, "child_ids", dict(self.child_ids))

    @property
    def is_root(self) -> bool:
        """Check if this manifest is a root (no parent)."""
        return self.parent_id is None

    @property
    def is_leaf(self) -> bool:
        """Check if this manifest is a leaf (no children)."""
        return len(self.child_ids) == 0

    def get_parent(self) -> str | None:
        """Get parent manifest ID.

        Returns:
            Parent manifest UUID string, or None if this is a root manifest.
        """
        return self.parent_id

    def get_children(self) -> dict[int, str]:
        """Get child manifest IDs mapped by year.

        Returns:
            Dictionary mapping year (int) to child manifest UUID (str).
        """
        return dict(self.child_ids)


def get_lineage(manifest: RunManifest) -> LineageGraph:
    """Extract lineage graph from a run manifest.

    Args:
        manifest: The manifest to extract lineage from.

    Returns:
        LineageGraph with parent/child relationships.
    """
    parent_id = manifest.parent_manifest_id if manifest.parent_manifest_id else None
    return LineageGraph(
        manifest_id=manifest.manifest_id,
        parent_id=parent_id,
        child_ids=dict(manifest.child_manifests),
    )


def validate_lineage(
    parent: RunManifest,
    children: dict[int, RunManifest],
) -> None:
    """Validate bidirectional lineage integrity between parent and children.

    Ensures:
    - Parent's child_manifests[year] matches child.manifest_id
    - Child's parent_manifest_id matches parent.manifest_id

    Args:
        parent: Parent manifest containing child references.
        children: Dictionary of year to child manifest.

    Raises:
        LineageIntegrityError: If any lineage link is broken or mismatched.
    """
    # Check parent->child consistency
    for year, expected_child_id in parent.child_manifests.items():
        if year not in children:
            raise LineageIntegrityError(
                f"Parent manifest {parent.manifest_id!r} references child for "
                f"year {year} with ID {expected_child_id!r}, but no child manifest "
                f"was provided for that year"
            )
        actual_child_id = children[year].manifest_id
        if actual_child_id != expected_child_id:
            raise LineageIntegrityError(
                f"Parent manifest {parent.manifest_id!r} references child for "
                f"year {year} with ID {expected_child_id!r}, but provided child "
                f"has ID {actual_child_id!r}"
            )

    # Check child->parent consistency
    for year, child in children.items():
        if year not in parent.child_manifests:
            raise LineageIntegrityError(
                f"Child manifest {child.manifest_id!r} provided for year {year}, "
                f"but parent manifest {parent.manifest_id!r} has no child reference "
                f"for that year"
            )
        if child.parent_manifest_id != parent.manifest_id:
            raise LineageIntegrityError(
                f"Child manifest {child.manifest_id!r} for year {year} has "
                f"parent_manifest_id={child.parent_manifest_id!r}, but expected "
                f"{parent.manifest_id!r}"
            )
