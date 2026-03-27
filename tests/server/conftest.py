# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test fixtures for server API tests."""

from __future__ import annotations

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
def client_with_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    """Create a FastAPI test client with custom data directories."""
    from reformlab.server.app import create_app

    monkeypatch.setenv("REFORMLAB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv(
        "REFORMLAB_UPLOADED_POPULATIONS_DIR",
        str(tmp_path / ".reformlab" / "uploaded-populations"),
    )

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


# Import Path for type hints
from pathlib import Path  # noqa: E402
