"""Test fixtures for server API tests."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_test_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the shared password env var for all server tests."""
    monkeypatch.setenv("REFORMLAB_PASSWORD", "test-password-123")


@pytest.fixture()
def client() -> TestClient:
    """Create a FastAPI test client."""
    from reformlab.server.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture()
def auth_token(client: TestClient) -> str:
    """Authenticate and return a valid session token."""
    response = client.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture()
def auth_headers(auth_token: str) -> dict[str, str]:
    """Return headers with a valid auth token."""
    return {"Authorization": f"Bearer {auth_token}"}
