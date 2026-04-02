# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Unit tests for PopulationResolver — Story 23.2.

AC-1: Bundled populations are resolved and executable.
AC-2: Uploaded populations are resolved and executable.
AC-3: Generated populations (with manifest) are resolved and executable.
AC-4: Missing/unresolvable populations raise a clear error.
AC-5: Resolved population metadata includes source classification.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reformlab.server.population_resolver import (
    PopulationResolutionError,
    PopulationResolver,
    ResolvedPopulation,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create data_dir and uploaded_dir with test populations.

    Layout:
        data_dir/
            bundled.csv             — bundled population
            generated.csv           — generated population
            generated.manifest.json — marks generated as generated
            folder-pop/
                descriptor.json     — folder-based bundled population
                data.csv
        uploaded_dir/
            uploaded.csv            — uploaded population
    """
    data_dir = tmp_path / "populations"
    data_dir.mkdir()
    uploaded_dir = tmp_path / "uploaded"
    uploaded_dir.mkdir()

    # Bundled (single-file)
    (data_dir / "bundled.csv").write_text("household_id,income\n1,50000\n", encoding="utf-8")

    # Generated (file + manifest sidecar)
    (data_dir / "generated.csv").write_text("household_id,income\n3,70000\n", encoding="utf-8")
    (data_dir / "generated.manifest.json").write_text(
        json.dumps({"generated": True, "seed": 42}), encoding="utf-8"
    )

    # Uploaded
    (uploaded_dir / "uploaded.csv").write_text(
        "household_id,income\n2,60000\n", encoding="utf-8"
    )

    # Folder-based bundled population
    folder = data_dir / "folder-pop"
    folder.mkdir()
    (folder / "descriptor.json").write_text(
        json.dumps({"data_file": "data.csv", "description": "Test folder population"}),
        encoding="utf-8",
    )
    (folder / "data.csv").write_text("household_id,income\n4,80000\n", encoding="utf-8")

    return data_dir, uploaded_dir


# ---------------------------------------------------------------------------
# Story 23.2 / AC-1: Bundled population resolution
# ---------------------------------------------------------------------------


class TestResolveBundled:
    """AC-1: Bundled populations resolve correctly."""

    def test_resolve_bundled_csv(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("bundled")

        assert isinstance(result, ResolvedPopulation)
        assert result.population_id == "bundled"
        assert result.source == "bundled"
        assert result.data_path.name == "bundled.csv"
        assert result.data_path.exists()

    def test_resolve_bundled_parquet(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        # Add a parquet bundled population
        (data_dir / "bundled-parquet.parquet").write_bytes(b"PAR1")  # minimal header
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("bundled-parquet")

        assert result.source == "bundled"
        assert result.data_path.suffix == ".parquet"

    def test_resolve_folder_based_bundled(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("folder-pop")

        assert result.population_id == "folder-pop"
        assert result.source == "bundled"
        assert result.data_path.name == "data.csv"
        assert result.metadata is not None
        assert result.metadata.get("description") == "Test folder population"


# ---------------------------------------------------------------------------
# Story 23.2 / AC-2: Uploaded population resolution
# ---------------------------------------------------------------------------


class TestResolveUploaded:
    """AC-2: Uploaded populations resolve correctly."""

    def test_resolve_uploaded_csv(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("uploaded")

        assert isinstance(result, ResolvedPopulation)
        assert result.population_id == "uploaded"
        assert result.source == "uploaded"
        assert result.data_path.name == "uploaded.csv"
        assert result.data_path.exists()

    def test_resolve_uploaded_parquet(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        (uploaded_dir / "uploaded-parquet.parquet").write_bytes(b"PAR1")
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("uploaded-parquet")

        assert result.source == "uploaded"
        assert result.data_path.suffix == ".parquet"


# ---------------------------------------------------------------------------
# Story 23.2 / AC-3: Generated population resolution
# ---------------------------------------------------------------------------


class TestResolveGenerated:
    """AC-3: Generated populations resolve correctly."""

    def test_resolve_generated_population(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("generated")

        assert isinstance(result, ResolvedPopulation)
        assert result.population_id == "generated"
        assert result.source == "generated"
        assert result.data_path.name == "generated.csv"
        assert result.data_path.exists()


# ---------------------------------------------------------------------------
# Story 23.2 / AC-4: Error handling for missing/unresolvable populations
# ---------------------------------------------------------------------------


class TestResolveErrors:
    """AC-4: Missing or unresolvable populations raise clear errors."""

    def test_missing_population_raises_error(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        with pytest.raises(PopulationResolutionError) as exc_info:
            resolver.resolve("does-not-exist")

        err = exc_info.value
        assert err.population_id == "does-not-exist"

    def test_error_includes_available_ids(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        with pytest.raises(PopulationResolutionError) as exc_info:
            resolver.resolve("nonexistent-pop")

        err = exc_info.value
        # Should list available population IDs
        assert len(err.available_ids) > 0
        assert "bundled" in err.available_ids

    def test_error_has_what_why_fix_format(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        with pytest.raises(PopulationResolutionError) as exc_info:
            resolver.resolve("missing-id")

        err = exc_info.value
        # args[0] should be a dict with what/why/fix
        assert isinstance(err.args[0], dict)
        detail = err.args[0]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_folder_without_descriptor_not_resolvable(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        # Create folder without descriptor.json
        no_desc = data_dir / "no-descriptor"
        no_desc.mkdir()
        (no_desc / "data.csv").write_text("household_id\n1\n", encoding="utf-8")
        resolver = PopulationResolver(data_dir, uploaded_dir)

        # Should fall through to error since no descriptor.json
        with pytest.raises(PopulationResolutionError):
            resolver.resolve("no-descriptor")


# ---------------------------------------------------------------------------
# Story 23.2 / AC-5: Resolution metadata and source classification
# ---------------------------------------------------------------------------


class TestResolvedPopulationFields:
    """AC-5: Resolved population has correct metadata fields."""

    def test_resolved_population_has_all_fields(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("bundled")

        assert result.population_id == "bundled"
        assert result.source in ("bundled", "uploaded", "generated")
        assert isinstance(result.data_path, Path)

    def test_bundled_source_classification(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)
        result = resolver.resolve("bundled")
        assert result.source == "bundled"

    def test_uploaded_source_classification(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)
        result = resolver.resolve("uploaded")
        assert result.source == "uploaded"

    def test_generated_source_classification(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        resolver = PopulationResolver(data_dir, uploaded_dir)
        result = resolver.resolve("generated")
        assert result.source == "generated"


# ---------------------------------------------------------------------------
# Resolution priority order
# ---------------------------------------------------------------------------


class TestResolutionOrder:
    """Bundled populations take priority over uploaded if IDs clash."""

    def test_bundled_shadows_uploaded_on_duplicate_id(self, dirs: tuple[Path, Path]) -> None:
        data_dir, uploaded_dir = dirs
        # Create uploaded population with same ID as bundled
        (uploaded_dir / "bundled.csv").write_text(
            "household_id,income\n99,9999\n", encoding="utf-8"
        )
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("bundled")

        # Should resolve to bundled (data_dir), not uploaded
        assert result.source == "bundled"
        assert result.data_path.parent == data_dir


# ---------------------------------------------------------------------------
# Missing or non-existent directories
# ---------------------------------------------------------------------------


class TestMissingDirectories:
    """Resolver handles missing directories gracefully."""

    def test_resolve_with_nonexistent_data_dir(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "nonexistent-data"
        uploaded_dir = tmp_path / "nonexistent-uploaded"
        resolver = PopulationResolver(data_dir, uploaded_dir)

        with pytest.raises(PopulationResolutionError) as exc_info:
            resolver.resolve("any-id")

        err = exc_info.value
        assert err.population_id == "any-id"

    def test_list_available_ids_with_empty_dirs(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "empty-data"
        data_dir.mkdir()
        uploaded_dir = tmp_path / "empty-uploaded"
        uploaded_dir.mkdir()
        resolver = PopulationResolver(data_dir, uploaded_dir)

        ids = resolver._list_available_ids()
        assert ids == []
