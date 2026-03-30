# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for exogenous asset routes — Story 21.6, AC8, Task 8."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def exogenous_assets_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped tmp_path for exogenous assets across all test fixtures."""
    exogenous_dir = tmp_path_factory.mktemp("exogenous", numbered=False)
    return exogenous_dir


@pytest.fixture()
def client(exogenous_assets_path: Path) -> Generator[TestClient, Any, None]:
    """TestClient with patched exogenous assets base path."""
    # Patch the base path to use tmp_path
    import reformlab.data.exogenous_loader as loader_module

    original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
    loader_module._EXOGENOUS_ASSETS_BASE_PATH = exogenous_assets_path

    from reformlab.server.app import create_app

    app = create_app()
    yield TestClient(app)

    # Restore original path
    loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Return auth headers for authenticated requests."""
    response = client.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture()
def sample_asset(exogenous_assets_path: Path) -> None:
    """Create a sample exogenous asset for testing."""
    asset_folder = exogenous_assets_path / "sample_energy_price"
    asset_folder.mkdir(exist_ok=True)

    # Write descriptor.json
    descriptor = {
        "asset_id": "sample_energy_price",
        "name": "Sample Energy Price",
        "description": "Test energy price asset",
        "data_class": "exogenous",
        "origin": "open-official",
        "access_mode": "bundled",
        "trust_status": "production-safe",
        "source_url": "https://example.com",
        "license": "CC-BY-4.0",
        "version": "2024",
        "geographic_coverage": ["FR"],
        "years": [2020, 2025, 2030],
        "intended_use": "Testing",
        "redistribution_allowed": True,
        "redistribution_notes": "",
        "update_cadence": "annual",
        "quality_notes": "Test data",
        "references": [],
    }
    with (asset_folder / "descriptor.json").open("w") as f:
        json.dump(descriptor, f)

    # Write values.json
    values = {"2020": 0.185, "2025": 0.195, "2030": 0.205}
    with (asset_folder / "values.json").open("w") as f:
        json.dump(values, f)

    # Write metadata.json
    metadata = {
        "unit": "EUR/kWh",
        "frequency": "annual",
        "source": "Test Source",
        "vintage": "2024-Q2",
        "interpolation_method": "linear",
        "aggregation_method": "mean",
        "revision_policy": "latest",
    }
    with (asset_folder / "metadata.json").open("w") as f:
        json.dump(metadata, f)


_VALID_CREATE_REQUEST = {
    "name": "new_energy_price",
    "description": "New energy price asset",
    "origin": "open-official",
    "access_mode": "fetched",
    "trust_status": "exploratory",
    "source_url": "",
    "license": "",
    "version": "",
    "geographic_coverage": [],
    "years": [],
    "intended_use": "Testing",
    "redistribution_allowed": True,
    "redistribution_notes": "",
    "update_cadence": "",
    "quality_notes": "Test asset",
    "references": [],
    "unit": "EUR/kWh",
    "values": {"2020": 0.2, "2025": 0.21, "2030": 0.22},
    "frequency": "annual",
    "source": "Test",
    "vintage": "2024",
    "interpolation_method": "linear",
    "aggregation_method": "mean",
    "revision_policy": "latest",
}


class TestListExogenousSeries:
    """GET /api/exogenous/series."""

    def test_list_returns_empty_when_no_assets(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return empty list when no assets exist."""
        response = client.get("/api/exogenous/series", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_all_assets(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should return all exogenous assets."""
        response = client.get("/api/exogenous/series", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["asset_id"] == "sample_energy_price"
        assert data[0]["unit"] == "EUR/kWh"

    def test_list_filters_by_unit(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should filter assets by unit."""
        response = client.get(
            "/api/exogenous/series?unit=EUR%2FkWh", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["unit"] == "EUR/kWh"

    def test_list_filters_by_origin(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should filter assets by origin."""
        response = client.get(
            "/api/exogenous/series?origin=open-official", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_filters_by_source_substring(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should filter assets by source substring."""
        response = client.get(
            "/api/exogenous/series?source=Test", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_returns_empty_for_non_matching_filter(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should return empty list when filter doesn't match."""
        response = client.get(
            "/api/exogenous/series?unit=EUR%2Flitre", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []


class TestGetExogenousSeries:
    """GET /api/exogenous/series/{series_name}."""

    def test_get_returns_asset(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should return the requested asset."""
        response = client.get(
            "/api/exogenous/series/sample_energy_price", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == "sample_energy_price"
        assert data["unit"] == "EUR/kWh"
        assert data["values"]["2020"] == 0.185

    def test_get_returns_404_for_nonexistent(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 404 for nonexistent asset."""
        response = client.get(
            "/api/exogenous/series/nonexistent", headers=auth_headers
        )
        assert response.status_code == 404
        data = response.json()["detail"]
        assert "what" in data
        assert "nonexistent" in data["what"]


class TestCreateExogenousSeries:
    """POST /api/exogenous/series."""

    def test_create_returns_200(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should create asset and return 200."""
        response = client.post(
            "/api/exogenous/series", headers=auth_headers, json=_VALID_CREATE_REQUEST
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == "new_energy_price"
        assert data["unit"] == "EUR/kWh"

    def test_create_creates_files(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        exogenous_assets_path: Path,
    ) -> None:
        """Should create asset folder with all required files."""
        client.post(
            "/api/exogenous/series", headers=auth_headers, json=_VALID_CREATE_REQUEST
        )

        # Check files were created
        asset_folder = exogenous_assets_path / "new_energy_price"
        assert asset_folder.exists()
        assert (asset_folder / "descriptor.json").exists()
        assert (asset_folder / "values.json").exists()
        assert (asset_folder / "metadata.json").exists()

    def test_create_returns_409_for_duplicate(
        self, client: TestClient, auth_headers: dict[str, str], sample_asset: None
    ) -> None:
        """Should return 409 when asset already exists."""
        response = client.post(
            "/api/exogenous/series",
            headers=auth_headers,
            json={
                **_VALID_CREATE_REQUEST,
                "name": "sample_energy_price",
            },
        )
        assert response.status_code == 409
        data = response.json()["detail"]
        assert "already exists" in data["what"]

    def test_create_rejects_invalid_name(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should reject names with path traversal characters."""
        invalid_names = ["../etc/passwd", "foo/bar", "foo\\bar"]
        for invalid_name in invalid_names:
            response = client.post(
                "/api/exogenous/series",
                headers=auth_headers,
                json={**_VALID_CREATE_REQUEST, "name": invalid_name},
            )
            assert response.status_code == 400
            data = response.json()["detail"]
            assert "Invalid series name" in data["what"]

    def test_created_asset_appears_in_listing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should include newly created asset in listing."""
        client.post(
            "/api/exogenous/series", headers=auth_headers, json=_VALID_CREATE_REQUEST
        )
        response = client.get("/api/exogenous/series", headers=auth_headers)
        assert response.status_code == 200
        assets = response.json()
        new_assets = [a for a in assets if a["asset_id"] == "new_energy_price"]
        assert len(new_assets) == 1
