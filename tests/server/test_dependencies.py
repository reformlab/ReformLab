# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for server dependency data-dir resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.server.dependencies import _resolve_adapter_data_dir


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
