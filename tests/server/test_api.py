"""Tests for the ReformLab FastAPI server routes.

Tests use the FastAPI TestClient with the real app factory.
The MockAdapter is used automatically when OpenFisca is not installed.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuthRoutes:
    """AC-7: Shared-password authentication."""

    def test_login_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": "test-password-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_login_wrong_password(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": "wrong"},
        )
        assert response.status_code == 401

    def test_unauthenticated_request_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/templates")
        assert response.status_code == 401

    def test_authenticated_request_succeeds(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200


class TestTemplateRoutes:
    """AC-1: Template listing and selection."""

    def test_list_templates(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

    def test_get_template_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/templates/nonexistent-template", headers=auth_headers
        )
        assert response.status_code in (404, 500)


class TestPopulationRoutes:
    """Population listing."""

    def test_list_populations(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/populations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "populations" in data
        assert isinstance(data["populations"], list)


class TestScenarioRoutes:
    """AC-1, AC-2: Scenario CRUD operations."""

    def test_list_scenarios(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/scenarios", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)


class TestErrorHandling:
    """AC-6: Error responses use structured format."""

    def test_login_error_structure(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": "wrong"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
