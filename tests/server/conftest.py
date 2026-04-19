# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test fixtures for server API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True, scope="session")
def _cleanup_test_registry() -> None:
    """Clean up test registry before the test session starts.

    Removes leftover portfolios and templates that reference custom policy types
    which may not be registered in all test contexts.
    """
    import shutil

    from reformlab.server.dependencies import get_registry

    registry = get_registry()
    registry_path = registry.path

    # List of test portfolio/template names to clean up
    test_names = [
        "carbon-plus-rebate",
        "carbon-tax-flat-rate-plus-2-more",
        "test-check",
        "test-live-ready-portfolio",
        "test-clone-source-17-6",
        "test-detail-scenario-17-6",
        "test-template",
        "test-scenario-create",
        "test-scenario-visible-pack-24-1",
        "test-type-discriminator",
        "a1",
        "ab",
        "abc",
        "green-transition-2030",
        "my-portfolio",
        "portfolio",
        "second-portfolio",
    ]

    # Also clean up dynamically named test entries from previous interrupted runs.
    for entry in registry_path.iterdir():
        if entry.is_dir() and (
            entry.name.startswith("rest-smoke-")
            or entry.name.startswith("test-unavail-rt-")
        ):
            shutil.rmtree(entry)

    for name in test_names:
        entry_path = registry_path / name
        if entry_path.exists():
            shutil.rmtree(entry_path)


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
    uploaded_dir = str(tmp_path / ".reformlab" / "uploaded-populations")
    monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", uploaded_dir)

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
