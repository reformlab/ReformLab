"""Tests for the compatibility matrix loader and query API."""

from __future__ import annotations

import importlib.resources
from pathlib import Path
from unittest.mock import patch

import pytest

from reformlab.computation.compat_matrix import (
    CompatibilityInfo,
    _clear_cache,
    get_compatibility_info,
    load_matrix,
)


@pytest.fixture(autouse=True)
def _clear_matrix_cache() -> None:
    """Ensure each test starts with a fresh cache."""
    _clear_cache()


class TestLoadMatrix:
    """Tests for YAML loading and caching."""

    def test_load_returns_dict(self) -> None:
        matrix = load_matrix()
        assert isinstance(matrix, dict)

    def test_schema_version_present(self) -> None:
        matrix = load_matrix()
        assert "schema_version" in matrix
        assert matrix["schema_version"] == "1.0"

    def test_min_supported_present(self) -> None:
        matrix = load_matrix()
        assert matrix["min_supported"] == "44.0.0"

    def test_versions_section_present(self) -> None:
        matrix = load_matrix()
        assert "versions" in matrix
        assert isinstance(matrix["versions"], dict)

    def test_matrix_url_present(self) -> None:
        matrix = load_matrix()
        assert "matrix_url" in matrix
        assert matrix["matrix_url"].endswith("docs/compatibility.md")

    def test_caching_returns_same_object(self) -> None:
        m1 = load_matrix()
        m2 = load_matrix()
        assert m1 is m2

    def test_clear_cache_invalidates(self) -> None:
        m1 = load_matrix()
        _clear_cache()
        m2 = load_matrix()
        assert m1 is not m2


class TestCompatibilityInfo:
    """Tests for the CompatibilityInfo dataclass."""

    def test_is_frozen(self) -> None:
        info = CompatibilityInfo(
            version="44.0.0",
            status="supported",
            modes_tested=("pre-computed", "api"),
            known_issues=(),
            tested_date="2026-02-25",
            guidance="OK",
            matrix_url="http://example.com",
        )
        with pytest.raises(AttributeError):
            info.status = "unsupported"  # type: ignore[misc]

    def test_fields(self) -> None:
        info = CompatibilityInfo(
            version="44.2.2",
            status="supported",
            modes_tested=("pre-computed",),
            known_issues=(),
            tested_date="2026-02-26",
            guidance="Latest",
            matrix_url="http://example.com",
        )
        assert info.version == "44.2.2"
        assert info.status == "supported"
        assert info.modes_tested == ("pre-computed",)
        assert info.known_issues == ()
        assert info.tested_date == "2026-02-26"
        assert info.guidance == "Latest"


class TestGetCompatibilityInfo:
    """Tests for get_compatibility_info() query function."""

    def test_supported_version(self) -> None:
        info = get_compatibility_info("44.2.2")
        assert info.status == "supported"
        assert "pre-computed" in info.modes_tested
        assert "api" in info.modes_tested

    def test_all_supported_versions(self) -> None:
        supported = ["44.0.0", "44.0.1", "44.1.0", "44.2.0", "44.2.1", "44.2.2"]
        for v in supported:
            info = get_compatibility_info(v)
            assert info.status == "supported", f"{v} should be supported"

    def test_untested_version_in_matrix(self) -> None:
        info = get_compatibility_info("44.0.3")
        assert info.status == "untested"

    def test_unlisted_version_above_min(self) -> None:
        """Versions >= min_supported but not in matrix are 'untested'."""
        info = get_compatibility_info("44.3.0")
        assert info.status == "untested"
        guidance = info.guidance.lower()
        assert "not listed" in guidance or "untested" in guidance

    def test_unsupported_old_version(self) -> None:
        """Versions below min_supported are 'unsupported'."""
        info = get_compatibility_info("43.0.0")
        assert info.status == "unsupported"

    def test_unsupported_version_has_guidance(self) -> None:
        info = get_compatibility_info("43.0.0")
        assert info.guidance
        assert info.matrix_url

    def test_not_installed_version(self) -> None:
        info = get_compatibility_info("not-installed")
        assert info.status == "unsupported"

    def test_whitespace_trimmed(self) -> None:
        info = get_compatibility_info("  44.2.2  ")
        assert info.status == "supported"

    def test_invalid_version_string(self) -> None:
        info = get_compatibility_info("abc")
        assert info.status == "unsupported"

    def test_matrix_url_in_result(self) -> None:
        info = get_compatibility_info("44.2.2")
        assert info.matrix_url.endswith("docs/compatibility.md")

    def test_version_field_matches_query(self) -> None:
        info = get_compatibility_info("44.2.2")
        assert info.version == "44.2.2"


class TestMalformedMatrix:
    """Tests for defensive validation when YAML is malformed."""

    def test_missing_versions_key(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(
            "schema_version: '1.0'\n"
            "matrix_url: 'https://example.test/compat'\n"
            "min_supported: '44.0.0'\n"
        )
        with patch(
            "reformlab.computation.compat_matrix._MATRIX_PATH", bad_yaml
        ):
            with pytest.raises(ValueError, match="versions"):
                load_matrix()

    def test_missing_min_supported(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(
            "schema_version: '1.0'\n"
            "matrix_url: 'https://example.test/compat'\n"
            "versions:\n"
            "  '44.0.0':\n"
            "    status: supported\n"
        )
        with patch(
            "reformlab.computation.compat_matrix._MATRIX_PATH", bad_yaml
        ):
            with pytest.raises(ValueError, match="min_supported"):
                load_matrix()

    def test_missing_schema_version(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(
            "min_supported: '44.0.0'\nversions:\n  '44.0.0':\n    status: supported\n"
        )
        with patch(
            "reformlab.computation.compat_matrix._MATRIX_PATH", bad_yaml
        ):
            with pytest.raises(ValueError, match="schema_version"):
                load_matrix()

    def test_missing_matrix_url(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(
            "schema_version: '1.0'\n"
            "min_supported: '44.0.0'\n"
            "versions:\n"
            "  '44.0.0':\n"
            "    status: supported\n"
        )
        with patch(
            "reformlab.computation.compat_matrix._MATRIX_PATH", bad_yaml
        ):
            with pytest.raises(ValueError, match="matrix_url"):
                load_matrix()

    def test_blank_matrix_url(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(
            "schema_version: '1.0'\n"
            "matrix_url: ''\n"
            "min_supported: '44.0.0'\n"
            "versions:\n"
            "  '44.0.0':\n"
            "    status: supported\n"
        )
        with patch(
            "reformlab.computation.compat_matrix._MATRIX_PATH", bad_yaml
        ):
            with pytest.raises(ValueError, match="non-empty"):
                load_matrix()


class TestPackagingResourceAccess:
    """Task 6.2: Verify compat_matrix.yaml is discoverable as a package
    resource so missing data files fail CI."""

    def test_yaml_accessible_via_importlib_resources(self) -> None:
        files = importlib.resources.files("reformlab.computation")
        yaml_resource = files.joinpath("compat_matrix.yaml")
        content = yaml_resource.read_text(encoding="utf-8")
        assert "schema_version" in content
        assert "versions" in content

    def test_yaml_path_exists_on_disk(self) -> None:
        from reformlab.computation.compat_matrix import _MATRIX_PATH

        assert _MATRIX_PATH.exists()
        assert _MATRIX_PATH.suffix == ".yaml"
