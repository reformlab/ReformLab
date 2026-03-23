# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for custom template CRUD endpoints — Story 4.

Verifies POST /api/templates/custom and DELETE /api/templates/custom/{name}.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with clean custom template registrations."""
    # Reset custom registrations before each test
    from reformlab.templates.schema import _reset_custom_registrations

    _reset_custom_registrations()

    from reformlab.server.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


_VALID_BODY = {
    "name": "my_custom_tax",
    "description": "A custom tax template",
    "parameters": [
        {"name": "rate", "type": "float", "default": 10.0, "unit": "EUR/t"},
        {"name": "threshold", "type": "int", "default": 100},
    ],
}


class TestCreateCustomTemplate:
    """POST /api/templates/custom."""

    def test_create_returns_201(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=_VALID_BODY
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "my_custom_tax"
        assert data["parameter_count"] == 2
        assert data["is_custom"] is True

    def test_created_template_appears_in_listing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        custom = [t for t in templates if t["name"] == "my_custom_tax"]
        assert len(custom) == 1
        assert custom[0]["is_custom"] is True

    def test_reject_non_snake_case_name(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_VALID_BODY, "name": "MyCustomTax"}
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=body
        )
        assert response.status_code == 422

    def test_reject_builtin_name_collision(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_VALID_BODY, "name": "carbon_tax"}
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=body
        )
        assert response.status_code == 409

    def test_reject_empty_parameters(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_VALID_BODY, "parameters": []}
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=body
        )
        assert response.status_code == 422

    def test_reject_duplicate_registration(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=_VALID_BODY
        )
        assert response.status_code == 409


class TestDeleteCustomTemplate:
    """DELETE /api/templates/custom/{name}."""

    def test_delete_returns_204(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        response = client.delete(
            "/api/templates/custom/my_custom_tax", headers=auth_headers
        )
        assert response.status_code == 204

    def test_delete_removes_from_listing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        client.delete("/api/templates/custom/my_custom_tax", headers=auth_headers)
        response = client.get("/api/templates", headers=auth_headers)
        templates = response.json()["templates"]
        custom = [t for t in templates if t["name"] == "my_custom_tax"]
        assert len(custom) == 0

    def test_delete_builtin_returns_403(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.delete(
            "/api/templates/custom/carbon_tax", headers=auth_headers
        )
        assert response.status_code == 403

    def test_delete_nonexistent_returns_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.delete(
            "/api/templates/custom/nonexistent", headers=auth_headers
        )
        assert response.status_code == 404
