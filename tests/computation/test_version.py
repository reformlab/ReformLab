# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test 5.2: OpenFiscaAdapter version check tests (supported + unsupported).

Tests verify that runtime version checks are strict (only matrix-supported
versions pass) and that the existing import path contract from
``openfisca_adapter`` is preserved after the matrix refactor.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from reformlab.computation.exceptions import CompatibilityError
from reformlab.computation.openfisca_adapter import (
    COMPAT_MATRIX_URL,
    SUPPORTED_VERSIONS,
    OpenFiscaAdapter,
    _check_version,
)


class TestVersionCheck:
    """AC-3: Given an unsupported OpenFisca version, when the adapter is
    initialized, then it raises CompatibilityError with version details."""

    def test_supported_version_passes(self) -> None:
        """Given a supported version, when checked, then no error is raised."""
        _check_version("44.2.2")

    def test_supported_minor_version_passes(self) -> None:
        _check_version(SUPPORTED_VERSIONS[0])

    def test_old_major_version_raises(self) -> None:
        """Given major version < 44, then CompatibilityError is raised."""
        with pytest.raises(CompatibilityError) as exc_info:
            _check_version("43.0.0")
        assert "43.0.0" in str(exc_info.value)
        assert exc_info.value.actual == "43.0.0"
        assert "44.2.2" in exc_info.value.expected

    def test_not_installed_raises(self) -> None:
        """Given openfisca-core is not installed, then CompatibilityError
        is raised with installation instructions."""
        with pytest.raises(CompatibilityError) as exc_info:
            _check_version("not-installed")
        assert "not installed" in str(exc_info.value).lower()
        assert COMPAT_MATRIX_URL in str(exc_info.value)

    def test_unparseable_version_raises(self) -> None:
        with pytest.raises(CompatibilityError):
            _check_version("abc")

    def test_adapter_init_with_unsupported_version(self, tmp_path: Path) -> None:
        """Given an unsupported OpenFisca version on the system, when
        OpenFiscaAdapter is created, then CompatibilityError is raised."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="30.0.0",
        ):
            with pytest.raises(CompatibilityError):
                OpenFiscaAdapter(data_dir=tmp_path)

    def test_adapter_init_with_supported_version(self, tmp_path: Path) -> None:
        """Given a supported OpenFisca version, when OpenFiscaAdapter is
        created, then it initialises successfully."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=tmp_path)
            assert adapter.version() == "44.2.2"

    def test_adapter_skip_version_check(self, tmp_path: Path) -> None:
        """Given skip_version_check=True, when OpenFiscaAdapter is created,
        then no version validation occurs."""
        adapter = OpenFiscaAdapter(data_dir=tmp_path, skip_version_check=True)
        assert adapter.version() == "unknown"

    def test_future_major_version_raises(self) -> None:
        """Given an unlisted future major version, then it is rejected."""
        with pytest.raises(CompatibilityError):
            _check_version("45.0.0")


class TestMatrixDrivenVersionChecks:
    """Verify that version checks derive from the compatibility matrix,
    not a hardcoded list (AC 4, Story 1-7)."""

    def test_supported_versions_match_matrix(self) -> None:
        """SUPPORTED_VERSIONS (imported from openfisca_adapter) must reflect
        the matrix-supported versions."""
        from reformlab.computation.compat_matrix import load_matrix

        matrix = load_matrix()
        expected = [
            v
            for v, entry in matrix["versions"].items()
            if entry.get("status") == "supported"
        ]
        assert SUPPORTED_VERSIONS == expected

    def test_compat_matrix_url_is_project_owned(self) -> None:
        """AC 9: COMPAT_MATRIX_URL points to project-owned docs, not
        upstream OpenFisca changelog."""
        url = COMPAT_MATRIX_URL.lower()
        assert "your-org" not in url
        assert url.endswith("docs/compatibility.md")

    def test_error_includes_matrix_url(self) -> None:
        """AC 2: CompatibilityError includes actionable matrix link."""
        with pytest.raises(CompatibilityError) as exc_info:
            _check_version("43.0.0")
        assert COMPAT_MATRIX_URL in str(exc_info.value)

    def test_untested_version_still_rejected_at_runtime(self) -> None:
        """Untested versions (in matrix but not supported) are rejected
        by the strict runtime check."""
        with pytest.raises(CompatibilityError):
            _check_version("44.0.3")  # untested in matrix


class TestImportPathRegression:
    """AC 7: Verify existing import expectations from openfisca_adapter.py
    continue to work after the matrix refactor (Story 1-7 subtask 5.4)."""

    def test_import_supported_versions(self) -> None:
        from reformlab.computation.openfisca_adapter import SUPPORTED_VERSIONS as SV

        assert isinstance(SV, list)
        assert len(SV) > 0

    def test_import_min_supported(self) -> None:
        from reformlab.computation.openfisca_adapter import MIN_SUPPORTED as MS

        assert isinstance(MS, str)
        assert MS == "44.0.0"

    def test_import_compat_matrix_url(self) -> None:
        from reformlab.computation.openfisca_adapter import COMPAT_MATRIX_URL as URL

        assert isinstance(URL, str)
        assert URL.endswith("docs/compatibility.md")

    def test_import_check_version(self) -> None:
        from reformlab.computation.openfisca_adapter import _check_version as cv

        assert callable(cv)

    def test_import_detect_version(self) -> None:
        from reformlab.computation.openfisca_adapter import (
            _detect_openfisca_version as dv,
        )

        assert callable(dv)

    def test_import_from_init_package(self) -> None:
        """CompatibilityInfo and get_compatibility_info are accessible
        from the package __init__."""
        from reformlab.computation import CompatibilityInfo, get_compatibility_info

        info = get_compatibility_info("44.2.2")
        assert isinstance(info, CompatibilityInfo)
