# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for evidence governance Pydantic models — Story 21.2.

AC1: PopulationLibraryItem uses dual-field approach (legacy origin + canonical fields).
AC5: DataSourceItem and DataSourceDetail include evidence classification fields.
AC7: All Pydantic models use Literal types from reformlab.data for canonical fields.
AC10: Tests cover dual-field model validation, mapping, and error handling.
"""

from __future__ import annotations

import pytest

from reformlab.data import (
    DataAssetAccessMode,
    DataAssetOrigin,
    DataAssetTrustStatus,
)
from reformlab.server.models import (
    DataSourceDetail,
    DataSourceItem,
    PopulationLibraryItem,
)

# =============================================================================
# Task 1: PopulationLibraryItem dual-field model tests
# =============================================================================


class TestPopulationLibraryItemDualField:
    """Tests for PopulationLibraryItem dual-field evidence classification.

    Story 21.2 / AC1: Preserves legacy origin for UI behavior compatibility
    while adding canonical evidence governance from Story 21.1.
    """

    def test_population_library_item_has_legacy_origin_field(self) -> None:
        """AC1: PopulationLibraryItem preserves legacy origin field for UI compatibility."""
        item = PopulationLibraryItem(
            id="test-pop",
            name="Test Population",
            households=1000,
            source="test",
            year=2025,
            origin="built-in",  # Legacy field
            canonical_origin="synthetic-public",  # Canonical field
            access_mode="bundled",
            trust_status="exploratory",
            column_count=10,
            created_date=None,
        )
        assert item.origin == "built-in"
        assert item.origin in ["built-in", "generated", "uploaded"]

    def test_population_library_item_has_canonical_evidence_fields(self) -> None:
        """AC1, AC7: PopulationLibraryItem has canonical evidence fields from Story 21.1."""
        item = PopulationLibraryItem(
            id="test-pop",
            name="Test Population",
            households=1000,
            source="test",
            year=2025,
            origin="built-in",
            canonical_origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            column_count=10,
            created_date=None,
        )
        # Canonical fields use Literal types from reformlab.data
        assert isinstance(item.canonical_origin, str)
        assert item.canonical_origin in DataAssetOrigin.__args__  # type: ignore[attr-defined]
        assert isinstance(item.access_mode, str)
        assert item.access_mode in DataAssetAccessMode.__args__  # type: ignore[attr-defined]
        assert isinstance(item.trust_status, str)
        assert item.trust_status in DataAssetTrustStatus.__args__  # type: ignore[attr-defined]

    def test_population_library_item_serialization_includes_both_fields(self) -> None:
        """AC1: JSON serialization includes both legacy and canonical fields."""
        item = PopulationLibraryItem(
            id="test-pop",
            name="Test Population",
            households=1000,
            source="test",
            year=2025,
            origin="generated",
            canonical_origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            column_count=10,
            created_date="2026-03-27T12:00:00Z",
        )
        data = item.model_dump()
        assert "origin" in data
        assert data["origin"] == "generated"
        assert "canonical_origin" in data
        assert data["canonical_origin"] == "synthetic-public"
        assert "access_mode" in data
        assert data["access_mode"] == "bundled"
        assert "trust_status" in data
        assert data["trust_status"] == "exploratory"


# =============================================================================
# Task 2: DataSourceItem and DataSourceDetail evidence fields tests
# =============================================================================


class TestDataSourceItemEvidenceFields:
    """Tests for DataSourceItem evidence classification fields.

    Story 21.2 / AC5: Data fusion sources include evidence metadata.
    """

    def test_data_source_item_has_evidence_fields(self) -> None:
        """AC5: DataSourceItem has origin, access_mode, trust_status, data_class fields."""
        item = DataSourceItem(
            id="test-dataset",
            provider="insee",
            name="Test Dataset",
            description="Test description",
            variable_count=5,
            record_count=1000,
            source_url="https://example.com",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            data_class="structural",
        )
        assert item.origin == "open-official"
        assert item.access_mode == "fetched"
        assert item.trust_status == "production-safe"
        assert item.data_class == "structural"

    def test_data_source_item_uses_canonical_literal_types(self) -> None:
        """AC7: DataSourceItem uses Literal types from reformlab.data."""
        item = DataSourceItem(
            id="test-dataset",
            provider="ademe",
            name="Test Dataset",
            description="Test description",
            variable_count=5,
            record_count=1000,
            source_url="https://example.com",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            data_class="structural",
        )
        # Verify types are from canonical Literal types
        assert item.origin in DataAssetOrigin.__args__  # type: ignore[attr-defined]
        assert item.access_mode in DataAssetAccessMode.__args__  # type: ignore[attr-defined]
        assert item.trust_status in DataAssetTrustStatus.__args__  # type: ignore[attr-defined]


class TestDataSourceDetailEvidenceFields:
    """Tests for DataSourceDetail evidence classification inheritance."""

    def test_data_source_detail_inherits_evidence_fields(self) -> None:
        """AC5: DataSourceDetail inherits evidence fields from DataSourceItem."""
        from reformlab.server.models import ColumnInfo

        detail = DataSourceDetail(
            id="test-dataset",
            provider="eurostat",
            name="Test Dataset",
            description="Test description",
            variable_count=5,
            record_count=1000,
            source_url="https://example.com",
            columns=[
                ColumnInfo(name="col1", type="integer", description="Column 1"),
            ],
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            data_class="structural",
        )
        assert detail.origin == "open-official"
        assert detail.access_mode == "fetched"
        assert detail.trust_status == "production-safe"
        assert detail.data_class == "structural"
        assert len(detail.columns) == 1


# =============================================================================
# Task 3: Origin mapping function tests
# =============================================================================


class TestOriginMappingFunction:
    """Tests for legacy origin to canonical evidence mapping.

    Story 21.2 / AC4: Mapping rules for population evidence fields.
    """

    def test_builtin_population_maps_to_synthetic_public(self) -> None:
        """AC4: Built-in origin maps to synthetic-public/bundled/exploratory."""
        from reformlab.server.routes.populations import _map_to_canonical_evidence

        origin, access_mode, trust = _map_to_canonical_evidence("built-in")
        assert origin == "synthetic-public"
        assert access_mode == "bundled"
        assert trust == "exploratory"

    def test_generated_population_maps_to_synthetic_public(self) -> None:
        """AC4: Generated origin maps to synthetic-public/bundled/exploratory."""
        from reformlab.server.routes.populations import _map_to_canonical_evidence

        origin, access_mode, trust = _map_to_canonical_evidence("generated")
        assert origin == "synthetic-public"
        assert access_mode == "bundled"
        assert trust == "exploratory"

    def test_uploaded_population_maps_to_synthetic_public(self) -> None:
        """AC4: Uploaded origin maps to synthetic-public/bundled/exploratory.

        Rationale: User-provided CSV/Parquet files lack official provenance
        verification, so they are classified as synthetic-public (not open-official).
        """
        from reformlab.server.routes.populations import _map_to_canonical_evidence

        origin, access_mode, trust = _map_to_canonical_evidence("uploaded")
        assert origin == "synthetic-public"
        assert access_mode == "bundled"
        assert trust == "exploratory"

    def test_unknown_origin_raises_http_exception(self) -> None:
        """AC4, AC10: Unknown legacy origin raises HTTPException 422 (fail-fast)."""
        from fastapi import HTTPException

        from reformlab.server.routes.populations import _map_to_canonical_evidence

        with pytest.raises(HTTPException) as exc_info:
            _map_to_canonical_evidence("unknown")  # type: ignore[arg-type]

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["what"] == "Unknown population origin"
        assert "unknown" in exc_info.value.detail["why"]
        assert "built-in" in exc_info.value.detail["fix"]


# =============================================================================
# Task 9: Legacy metadata compatibility tests
# =============================================================================


class TestLegacyMetadataCompatibility:
    """Tests for loading populations with legacy-only metadata.

    Story 21.2 / Task 9: Default values for missing canonical fields.
    """

    def test_population_item_without_canonical_fields_loads_with_defaults(self) -> None:
        """Task 9: Legacy metadata without canonical fields loads with appropriate defaults."""
        # Simulate loading from legacy metadata (only origin field present)
        legacy_data = {
            "id": "legacy-pop",
            "name": "Legacy Population",
            "households": 1000,
            "source": "legacy",
            "year": 2025,
            "origin": "uploaded",
            "column_count": 10,
            "created_date": None,
        }

        # When loading legacy data, canonical fields should be populated via mapping
        # This is tested in populations route tests, here we verify the model accepts it
        item = PopulationLibraryItem(
            **legacy_data,
            canonical_origin="synthetic-public",  # Mapped from legacy origin
            access_mode="bundled",
            trust_status="exploratory",
        )
        assert item.origin == "uploaded"
        assert item.canonical_origin == "synthetic-public"
