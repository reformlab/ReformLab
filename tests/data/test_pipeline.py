# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pcsv
import pytest

import reformlab.data.pipeline as pipeline_module
from reformlab.computation.ingestion import DataSchema, IngestionError
from reformlab.data.pipeline import (
    DatasetManifest,
    DatasetRegistry,
    DataSourceMetadata,
    hash_file,
    load_dataset,
    load_population,
)


class TestDataSourceMetadata:
    """Tests for DataSourceMetadata frozen dataclass."""

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created,
        then all fields are accessible."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="https://example.com",
            description="Test dataset",
            license="MIT",
        )
        assert source.name == "test"
        assert source.version == "1.0"
        assert source.url == "https://example.com"
        assert source.description == "Test dataset"
        assert source.license == "MIT"

    def test_license_defaults_to_empty(self) -> None:
        """Given no license, when created,
        then license defaults to empty string."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="https://example.com",
            description="Test",
        )
        assert source.license == ""

    def test_frozen(self) -> None:
        """Given a DataSourceMetadata, when mutating,
        then raises FrozenInstanceError."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="https://example.com",
            description="Test",
        )
        with pytest.raises(AttributeError):
            source.name = "mutated"  # type: ignore[misc]


class TestDatasetManifest:
    """Tests for DatasetManifest frozen dataclass."""

    def test_create_with_all_fields(
        self, tmp_path: Path
    ) -> None:
        """Given all fields, when created,
        then all fields are accessible."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="https://example.com",
            description="Test",
        )
        manifest = DatasetManifest(
            source=source,
            content_hash="abc123",
            file_path=tmp_path / "test.csv",
            format="csv",
            row_count=100,
            column_names=("col1", "col2"),
            loaded_at="2026-02-25T00:00:00+00:00",
        )
        assert manifest.source is source
        assert manifest.content_hash == "abc123"
        assert manifest.row_count == 100
        assert manifest.column_names == ("col1", "col2")
        assert manifest.format == "csv"

    def test_dataset_key(self, tmp_path: Path) -> None:
        """Given a manifest, when checking dataset_key,
        then it follows the expected pattern."""
        source = DataSourceMetadata(
            name="insee-pop",
            version="2024-v1",
            url="https://example.com",
            description="Test",
        )
        manifest = DatasetManifest(
            source=source,
            content_hash="abcdef123456789xyz",
            file_path=tmp_path / "test.csv",
            format="csv",
            row_count=10,
            column_names=("a",),
            loaded_at="2026-02-25T00:00:00+00:00",
        )
        expected = "insee-pop@2024-v1:abcdef123456"
        assert manifest.dataset_key == expected

    def test_frozen(self, tmp_path: Path) -> None:
        """Given a DatasetManifest, when mutating,
        then raises FrozenInstanceError."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="https://example.com",
            description="Test",
        )
        manifest = DatasetManifest(
            source=source,
            content_hash="abc",
            file_path=tmp_path / "test.csv",
            format="csv",
            row_count=5,
            column_names=("a",),
            loaded_at="2026-02-25T00:00:00+00:00",
        )
        with pytest.raises(AttributeError):
            manifest.row_count = 999  # type: ignore[misc]


class TestDatasetRegistry:
    """Tests for DatasetRegistry operations."""

    def _make_manifest(
        self,
        tmp_path: Path,
        name: str = "test",
        version: str = "1.0",
        content_hash: str = "abc123456789",
    ) -> DatasetManifest:
        source = DataSourceMetadata(
            name=name,
            version=version,
            url="https://example.com",
            description="Test",
        )
        return DatasetManifest(
            source=source,
            content_hash=content_hash,
            file_path=tmp_path / "test.csv",
            format="csv",
            row_count=10,
            column_names=("a", "b"),
            loaded_at="2026-02-25T00:00:00+00:00",
        )

    def test_register_and_get(
        self, tmp_path: Path
    ) -> None:
        """Given a manifest, when registered,
        then it is retrievable by dataset_key."""
        registry = DatasetRegistry()
        manifest = self._make_manifest(tmp_path)
        registry.register(manifest)
        result = registry.get(manifest.dataset_key)
        assert result is manifest

    def test_get_unknown_returns_none(self) -> None:
        """Given empty registry, when getting unknown key,
        then returns None."""
        registry = DatasetRegistry()
        assert registry.get("unknown-key") is None

    def test_all_returns_tuple(
        self, tmp_path: Path
    ) -> None:
        """Given registered manifests, when calling all(),
        then returns tuple of all manifests."""
        registry = DatasetRegistry()
        m1 = self._make_manifest(
            tmp_path, name="a", content_hash="hash_a_12345"
        )
        m2 = self._make_manifest(
            tmp_path, name="b", content_hash="hash_b_12345"
        )
        registry.register(m1)
        registry.register(m2)
        result = registry.all()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert m1 in result
        assert m2 in result

    def test_duplicate_key_raises_valueerror(
        self, tmp_path: Path
    ) -> None:
        """Given a registered manifest, when registering
        same key again, then raises ValueError."""
        registry = DatasetRegistry()
        manifest = self._make_manifest(tmp_path)
        registry.register(manifest)
        with pytest.raises(
            ValueError, match="already registered"
        ):
            registry.register(manifest)

    def test_find_by_source(
        self, tmp_path: Path
    ) -> None:
        """Given manifests from same source, when finding
        by source, then returns all matching."""
        registry = DatasetRegistry()
        m1 = self._make_manifest(
            tmp_path,
            name="insee",
            version="v1",
            content_hash="hash111111111",
        )
        m2 = self._make_manifest(
            tmp_path,
            name="insee",
            version="v2",
            content_hash="hash222222222",
        )
        m3 = self._make_manifest(
            tmp_path,
            name="ademe",
            version="v1",
            content_hash="hash333333333",
        )
        registry.register(m1)
        registry.register(m2)
        registry.register(m3)
        result = registry.find_by_source("insee")
        assert len(result) == 2
        assert m1 in result
        assert m2 in result

    def test_find_by_source_no_match(self) -> None:
        """Given empty registry, when finding by source,
        then returns empty tuple."""
        registry = DatasetRegistry()
        assert registry.find_by_source("unknown") == ()

    def test_to_dict_serializable(
        self, tmp_path: Path
    ) -> None:
        """Given registered manifests, when to_dict(),
        then returns JSON-serializable dict."""
        import json

        registry = DatasetRegistry()
        manifest = self._make_manifest(tmp_path)
        registry.register(manifest)
        result = registry.to_dict()
        serialized = json.dumps(result)
        assert isinstance(serialized, str)
        assert manifest.dataset_key in result


class TestHashFile:
    """Tests for hash_file() SHA-256 hashing."""

    def test_deterministic(self, tmp_path: Path) -> None:
        """Given same file hashed twice,
        then produces identical SHA-256."""
        f = tmp_path / "test.txt"
        f.write_text("hello world\n")
        h1 = hash_file(f)
        h2 = hash_file(f)
        assert h1 == h2
        assert len(h1) == 64

    def test_different_files_different_hashes(
        self, tmp_path: Path
    ) -> None:
        """Given different files, when hashed,
        then produce different SHA-256 values."""
        f1 = tmp_path / "a.txt"
        f1.write_text("content a")
        f2 = tmp_path / "b.txt"
        f2.write_text("content b")
        assert hash_file(f1) != hash_file(f2)

    def test_matches_stdlib(
        self, tmp_path: Path
    ) -> None:
        """Given a file, when hashed,
        then matches hashlib.sha256 directly."""
        f = tmp_path / "test.bin"
        data = b"test data for hashing"
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert hash_file(f) == expected


class TestLoadDataset:
    """Tests for load_dataset() pipeline entry point."""

    def test_csv_population_load(
        self,
        population_csv: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given a valid population CSV, when loaded,
        then returns table and manifest with hash."""
        source = DataSourceMetadata(
            name="test-population",
            version="2024-v1",
            url="https://example.com/population.csv",
            description="Test synthetic population",
        )
        table, manifest = load_dataset(
            population_csv, population_schema, source
        )
        assert isinstance(table, pa.Table)
        assert table.num_rows == 5
        assert manifest.source is source
        assert len(manifest.content_hash) == 64
        assert manifest.row_count == 5
        assert manifest.format == "csv"
        assert "household_id" in manifest.column_names

    def test_parquet_population_load(
        self,
        population_parquet: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given a valid Parquet, when loaded,
        then returns table and manifest."""
        source = DataSourceMetadata(
            name="test-population",
            version="2024-v1",
            url="https://example.com/pop.parquet",
            description="Test parquet",
        )
        table, manifest = load_dataset(
            population_parquet, population_schema, source
        )
        assert isinstance(table, pa.Table)
        assert table.num_rows == 5
        assert manifest.format == "parquet"
        assert len(manifest.content_hash) == 64

    def test_emission_factor_load(
        self,
        emission_csv: Path,
        emission_schema: DataSchema,
    ) -> None:
        """Given a valid emission factor CSV, when loaded,
        then returns table with category access."""
        source = DataSourceMetadata(
            name="ademe-base-carbone",
            version="2024",
            url="https://example.com/factors.csv",
            description="ADEME emission factors",
        )
        table, manifest = load_dataset(
            emission_csv, emission_schema, source
        )
        assert table.num_rows == 5
        assert manifest.source.name == "ademe-base-carbone"
        assert "category" in manifest.column_names

    def test_missing_columns_error(
        self,
        tmp_path: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given CSV missing required columns, when loaded,
        then raises IngestionError."""
        table = pa.table(
            {"household_id": pa.array([1], type=pa.int64())}
        )
        csv_path = tmp_path / "incomplete.csv"
        pcsv.write_csv(table, csv_path)
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="",
            description="",
        )
        with pytest.raises(
            IngestionError, match="missing required columns"
        ):
            load_dataset(csv_path, population_schema, source)

    def test_corrupted_file_error(
        self,
        tmp_path: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given a corrupted file, when loaded,
        then raises actionable IngestionError."""
        bad_file = tmp_path / "corrupted.csv"
        bad_file.write_bytes(
            b"\x00\x01\x02\x03truncated garbage"
        )
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="",
            description="",
        )
        with pytest.raises(IngestionError) as exc_info:
            load_dataset(
                bad_file, population_schema, source
            )
        message = str(exc_info.value)
        assert message.count(" - ") >= 2
        assert "(file:" in message

    def test_path_outside_allowed_roots(
        self,
        tmp_path: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given a path outside allowed roots, when loaded,
        then raises IngestionError."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="",
            description="",
        )
        with pytest.raises(
            IngestionError, match="outside allowed"
        ):
            load_dataset(
                Path("/etc/hosts"),
                population_schema,
                source,
                allowed_roots=(tmp_path,),
            )

    def test_manifest_loaded_at_iso(
        self,
        population_csv: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given a loaded dataset, when checking manifest,
        then loaded_at is ISO 8601 format."""
        from datetime import datetime

        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="",
            description="",
        )
        _, manifest = load_dataset(
            population_csv, population_schema, source
        )
        dt = datetime.fromisoformat(manifest.loaded_at)
        assert dt is not None

    def test_hash_read_failure_wrapped_as_ingestion_error(
        self,
        population_csv: Path,
        population_schema: DataSchema,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given hash read failure, loading raises actionable IngestionError."""

        def _raise_permission_error(_: Path) -> str:
            raise PermissionError("permission denied")

        monkeypatch.setattr(
            pipeline_module,
            "hash_file",
            _raise_permission_error,
        )
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="",
            description="",
        )
        with pytest.raises(
            IngestionError, match="unable to read file for hashing"
        ) as exc_info:
            load_dataset(population_csv, population_schema, source)
        assert "Ensure the file is readable and retry" in str(exc_info.value)


class TestLoadPopulation:
    """Tests for load_population() convenience wrapper."""

    def test_returns_population_data(
        self,
        population_csv: Path,
        population_schema: DataSchema,
    ) -> None:
        """Given a valid CSV, load_population returns PopulationData."""
        from reformlab.computation.types import PopulationData

        source = DataSourceMetadata(
            name="households",
            version="1.0",
            url="",
            description="",
        )
        pop = load_population(population_csv, population_schema, source)
        assert isinstance(pop, PopulationData)
        assert pop.row_count == 5

    def test_entity_type_from_source_name(
        self,
        population_csv: Path,
        population_schema: DataSchema,
    ) -> None:
        """Entity type key derived from source name when valid identifier."""
        source = DataSourceMetadata(
            name="individu",
            version="1.0",
            url="",
            description="",
        )
        pop = load_population(population_csv, population_schema, source)
        assert "individu" in pop.tables

    def test_primary_table_accessible(
        self,
        population_csv: Path,
        population_schema: DataSchema,
    ) -> None:
        """Primary table is accessible regardless of entity key."""
        source = DataSourceMetadata(
            name="households",
            version="1.0",
            url="",
            description="",
        )
        pop = load_population(population_csv, population_schema, source)
        assert pop.primary_table.num_rows == 5
