# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for server dependency data-dir resolution and adapter selection.

Story 23.4: Tests for adapter selection based on REFORMLAB_RUNTIME_MODE.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.result_normalizer import _DEFAULT_LIVE_OUTPUT_VARIABLES
from reformlab.server.dependencies import (
    _create_adapter,
    _create_replay_adapter,
    _resolve_adapter_data_dir,
    get_adapter,
    get_population_resolver,
)


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


# ===========================================================================
# Story 23.4: Adapter selection tests
# ===========================================================================


class TestDefaultLiveOutputVariables:
    """Story 23.4: _DEFAULT_LIVE_OUTPUT_VARIABLES constant."""

    def test_default_live_output_variables_are_french_names(self) -> None:
        """Default live output variables are French OpenFisca variable names."""
        # These are the keys from _DEFAULT_OUTPUT_MAPPING
        assert "revenu_disponible" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "irpp" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "impots_directs" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "revenu_net" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "salaire_net" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "revenu_brut" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "prestations_sociales" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "taxe_carbone" in _DEFAULT_LIVE_OUTPUT_VARIABLES

    def test_default_live_output_variables_is_tuple(self) -> None:
        """_DEFAULT_LIVE_OUTPUT_VARIABLES is an immutable tuple."""
        assert isinstance(_DEFAULT_LIVE_OUTPUT_VARIABLES, tuple)


class TestCreateLiveAdapter:
    """Story 23.4: _create_live_adapter() factory."""

    def test_creates_live_adapter_returns_mock_via_get_adapter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_create_adapter() defaults to using _create_live_adapter()."""
        import reformlab.server.dependencies as deps

        # Clear singleton and ensure default mode
        monkeypatch.delenv("REFORMLAB_RUNTIME_MODE", raising=False)
        monkeypatch.setattr(deps, "_adapter", None)

        # Patch _create_live_adapter to return MockAdapter
        monkeypatch.setattr(
            deps, "_create_live_adapter", lambda: MockAdapter()  # type: ignore[return-value]
        )

        adapter = deps._create_adapter()
        assert isinstance(adapter, MockAdapter)


class TestCreateReplayAdapter:
    """Story 23.4: _create_replay_adapter() factory."""

    def test_creates_openfisca_adapter_with_data_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """_create_replay_adapter() creates OpenFiscaAdapter with resolved data_dir."""
        import reformlab.server.dependencies as deps

        # Set up temp data directory with a precomputed file
        data_dir = tmp_path / "openfisca"
        data_dir.mkdir()
        (data_dir / "2025.csv").write_text(
            "household_id,income_tax,carbon_tax\n1,1000,50\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("REFORMLAB_OPENFISCA_DATA_DIR", str(data_dir))
        # Clear cached adapter singleton
        monkeypatch.setattr(deps, "_adapter", None)

        # Patch OpenFiscaAdapter to return MockAdapter (avoid real import)
        def mock_openfisca_adapter(*args: object, **kwargs: object) -> MockAdapter:
            return MockAdapter()

        monkeypatch.setattr(
            "reformlab.computation.openfisca_adapter.OpenFiscaAdapter",
            mock_openfisca_adapter,
        )

        adapter = _create_replay_adapter()
        assert isinstance(adapter, MockAdapter)


class TestCreateAdapterDefaultMode:
    """Story 23.4: _create_adapter() defaults to live mode."""

    def test_defaults_to_live_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without REFORMLAB_RUNTIME_MODE, defaults to live adapter."""
        import reformlab.server.dependencies as deps

        # Ensure no env var is set
        monkeypatch.delenv("REFORMLAB_RUNTIME_MODE", raising=False)
        # Clear cached adapter singleton
        monkeypatch.setattr(deps, "_adapter", None)

        # Patch _create_live_adapter to return MockAdapter
        def mock_live_adapter() -> MockAdapter:
            return MockAdapter()

        monkeypatch.setattr(deps, "_create_live_adapter", mock_live_adapter)

        adapter = _create_adapter()
        assert isinstance(adapter, MockAdapter)

    def test_invalid_runtime_mode_defaults_to_live(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid REFORMLAB_RUNTIME_MODE value defaults to live."""
        import reformlab.server.dependencies as deps

        monkeypatch.setenv("REFORMLAB_RUNTIME_MODE", "invalid")
        monkeypatch.setattr(deps, "_adapter", None)

        def mock_live_adapter() -> MockAdapter:
            return MockAdapter()

        monkeypatch.setattr(deps, "_create_live_adapter", mock_live_adapter)

        adapter = _create_adapter()
        assert isinstance(adapter, MockAdapter)


class TestCreateAdapterReplayMode:
    """Story 23.4: _create_adapter() with REFORMLAB_RUNTIME_MODE=replay."""

    def test_replay_mode_creates_replay_adapter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REFORMLAB_RUNTIME_MODE=replay creates replay adapter."""
        import reformlab.server.dependencies as deps

        monkeypatch.setenv("REFORMLAB_RUNTIME_MODE", "replay")
        monkeypatch.setattr(deps, "_adapter", None)

        def mock_replay_adapter() -> MockAdapter:
            return MockAdapter()

        monkeypatch.setattr(deps, "_create_replay_adapter", mock_replay_adapter)

        adapter = _create_adapter()
        assert isinstance(adapter, MockAdapter)


class TestCreateAdapterFallback:
    """Story 23.4: _create_adapter() falls back to MockAdapter."""

    def test_live_mode_falls_back_to_mock_on_import_error(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Live mode falls back to MockAdapter when OpenFisca import fails."""
        import reformlab.server.dependencies as deps

        # Enable logging capture at INFO level
        caplog.set_level(logging.INFO, logger="reformlab.server.dependencies")
        monkeypatch.delenv("REFORMLAB_RUNTIME_MODE", raising=False)
        monkeypatch.setattr(deps, "_adapter", None)

        # Make _create_live_adapter raise ImportError
        def failing_live_adapter() -> MockAdapter:
            raise ImportError("No OpenFisca")

        monkeypatch.setattr(deps, "_create_live_adapter", failing_live_adapter)

        adapter = deps._create_adapter()
        assert isinstance(adapter, MockAdapter)
        assert "OpenFisca not installed" in caplog.text

    def test_replay_mode_falls_back_to_mock_on_missing_data(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Replay mode falls back to MockAdapter when data dir not found."""
        import reformlab.server.dependencies as deps

        # Enable logging capture at WARNING level
        caplog.set_level(logging.WARNING, logger="reformlab.server.dependencies")

        # Set replay mode but ensure no data dir exists
        monkeypatch.setenv("REFORMLAB_RUNTIME_MODE", "replay")
        # Point to non-existent directory
        monkeypatch.setenv("REFORMLAB_OPENFISCA_DATA_DIR", "/nonexistent/path")
        monkeypatch.setattr(deps, "_adapter", None)

        # Patch _create_replay_adapter to raise FileNotFoundError
        def failing_replay_adapter() -> MockAdapter:
            raise FileNotFoundError("No data dir")

        monkeypatch.setattr(deps, "_create_replay_adapter", failing_replay_adapter)

        adapter = deps._create_adapter()
        assert isinstance(adapter, MockAdapter)
        assert "precomputed data not found" in caplog.text or "Replay adapter failed" in caplog.text


class TestGetAdapterSingleton:
    """Story 23.4: get_adapter() returns cached singleton."""

    def test_adapter_singleton_cached(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_adapter() returns same instance on subsequent calls."""
        import reformlab.server.dependencies as deps

        # Clear cached adapter
        monkeypatch.setattr(deps, "_adapter", None)

        # Patch to return a fresh MockAdapter each time
        call_count = 0

        def counting_create() -> MockAdapter:
            nonlocal call_count
            call_count += 1
            return MockAdapter()

        monkeypatch.setattr(deps, "_create_adapter", counting_create)
        monkeypatch.setattr(deps, "_adapter", None)

        adapter1 = get_adapter()
        adapter2 = get_adapter()

        # _create_adapter should only be called once due to singleton caching
        assert call_count == 1
        assert adapter1 is adapter2
