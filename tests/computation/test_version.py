"""Test 5.2: OpenFiscaAdapter version check tests (supported + unsupported)."""

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
