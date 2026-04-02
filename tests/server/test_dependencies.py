# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for server dependency data-dir resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.server.dependencies import _resolve_adapter_data_dir, get_population_resolver


class TestResolveAdapterDataDir:
    def test_prefers_explicit_openfisca_env_var(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        openfisca_dir = tmp_path / "explicit-openfisca"
        monkeypatch.setenv("REFORMLAB_OPENFISCA_DATA_DIR", str(openfisca_dir))
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(tmp_path / "data-root"))

        assert _resolve_adapter_data_dir() == openfisca_dir

    def test_prefers_openfisca_subdirectory_when_present(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_root = tmp_path / "data-root"
        nested = data_root / "openfisca"
        nested.mkdir(parents=True)
        monkeypatch.delenv("REFORMLAB_OPENFISCA_DATA_DIR", raising=False)
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(data_root))

        assert _resolve_adapter_data_dir() == nested

    def test_falls_back_to_data_root_for_backward_compatibility(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_root = tmp_path / "data-root"
        data_root.mkdir()
        monkeypatch.delenv("REFORMLAB_OPENFISCA_DATA_DIR", raising=False)
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(data_root))

        assert _resolve_adapter_data_dir() == data_root


class TestGetPopulationResolver:
    """Story 23.2: get_population_resolver() dependency function."""

    def test_resolver_singleton_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_population_resolver() returns a PopulationResolver."""
        import reformlab.server.dependencies as deps
        from reformlab.server.population_resolver import PopulationResolver

        # Clear cached singleton so we test fresh init
        monkeypatch.setattr(deps, "_population_resolver", None)

        resolver = get_population_resolver()
        assert isinstance(resolver, PopulationResolver)

    def test_resolver_uses_data_dir_env_var(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Resolver reads REFORMLAB_DATA_DIR to find bundled populations."""
        import reformlab.server.dependencies as deps

        data_root = tmp_path / "my-data"
        monkeypatch.setattr(deps, "_population_resolver", None)
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(data_root))
        monkeypatch.delenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", raising=False)

        resolver = get_population_resolver()

        assert resolver._data_dir == data_root / "populations"

    def test_resolver_uses_uploaded_dir_env_var(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Resolver reads REFORMLAB_UPLOADED_POPULATIONS_DIR env var."""
        import reformlab.server.dependencies as deps

        uploaded_root = tmp_path / "my-uploads"
        monkeypatch.setattr(deps, "_population_resolver", None)
        monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", str(uploaded_root))

        resolver = get_population_resolver()

        assert resolver._uploaded_dir == uploaded_root

    def test_resolver_is_cached_after_first_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Calling get_population_resolver() twice returns the same instance."""
        import reformlab.server.dependencies as deps

        monkeypatch.setattr(deps, "_population_resolver", None)

        resolver1 = get_population_resolver()
        resolver2 = get_population_resolver()

        assert resolver1 is resolver2
