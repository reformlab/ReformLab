# ReformLab Data Source Loader Pattern

This is the authoritative skeleton for generating new data source loaders.
Every new loader MUST follow this pattern exactly. No creative deviations.

Extracted from the existing INSEE, Eurostat, ADEME, and SDES loaders.

---

## File Locations

```
src/reformlab/population/loaders/{provider}.py      <- loader module
tests/population/loaders/test_{provider}.py          <- unit tests
tests/population/loaders/test_{provider}_network.py  <- optional network tests
src/reformlab/population/loaders/__init__.py          <- exports (update)
```

---

## Loader Module Skeleton

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""{Provider} institutional data source loader.

Downloads, caches, and schema-validates {Provider} {description}
datasets. Concrete implementation of the ``DataSourceLoader`` protocol
via ``CachedLoader``.

Handles {format} format with {encoding} encoding, {separator} separator,
and {special handling notes}.
"""

from __future__ import annotations

# Add format-specific imports as needed:
# import gzip          # for .gz files
# import zipfile       # for .zip files
import http.client
import io
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.csv as pcsv

from reformlab.computation.ingestion import DataSchema
from reformlab.data.descriptor import DatasetDescriptor
from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.errors import DataSourceValidationError

if TYPE_CHECKING:
    from reformlab.population.loaders.cache import SourceCache


# ====================================================================
# {Provider} dataset metadata
# ====================================================================


@dataclass(frozen=True)
class {Provider}Dataset:
    """Metadata for a known {Provider} dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_column_name, project_column_name)``.
    """

    dataset_id: str
    description: str
    url: str
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("",)
    columns: tuple[tuple[str, str], ...] = ()
    # Add provider-specific fields as needed:
    # skip_rows: int = 0              # for DiDo CSVs with description rows
    # archive_member: str | None = None  # for ZIP archives


# ====================================================================
# Dataset catalog
# ====================================================================

_DATASET_ID_COLUMNS: tuple[tuple[str, str], ...] = (
    ("RAW_COL_1", "project_col_1"),
    ("RAW_COL_2", "project_col_2"),
    # ... one tuple per selected column
)

{PROVIDER}_CATALOG: dict[str, {Provider}Dataset] = {
    "dataset_id": {Provider}Dataset(
        dataset_id="dataset_id",
        description="Human-readable description of the dataset",
        url="https://direct-download-url",
        columns=_DATASET_ID_COLUMNS,
    ),
}

{PROVIDER}_AVAILABLE_DATASETS: tuple[str, ...] = tuple(
    sorted({PROVIDER}_CATALOG.keys())
)
"""Available {Provider} dataset identifiers for discovery."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================

# CRITICAL: Field names use PROJECT names (right side of column mapping),
# NOT raw source names.

def _dataset_id_schema() -> pa.Schema:
    return pa.schema([
        pa.field("project_col_1", pa.utf8()),
        pa.field("project_col_2", pa.float64()),
    ])


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "dataset_id": _dataset_id_schema(),
}


# ====================================================================
# {Provider}Loader
# ====================================================================

_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for {Provider} HTTP downloads (5 minutes)."""


class {Provider}Loader(CachedLoader):
    """Concrete loader for {Provider} institutional data sources.

    Extends ``CachedLoader`` with {Provider}-specific {format} parsing,
    {encoding} encoding, and {column handling details}.

    Each loader instance handles one ``{Provider}Dataset``. Use
    ``get_{provider}_loader`` factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: {Provider}Dataset,
    ) -> None:
        self._dataset = dataset
        super().__init__(cache=cache, logger=logger)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's dataset."""
        return _DATASET_SCHEMAS[self._dataset.dataset_id]

    def descriptor(self) -> DatasetDescriptor:
        """Return the ``DatasetDescriptor`` for this loader's dataset."""
        ds = self._dataset
        pa_schema = self.schema()
        all_cols = tuple(pa_schema.names)
        return DatasetDescriptor(
            dataset_id=ds.dataset_id,
            provider="{provider}",
            description=ds.description,
            schema=DataSchema(
                schema=pa_schema,
                required_columns=all_cols,
            ),
            url=ds.url,
            column_mapping=ds.columns,
            encoding=ds.encoding,
            separator=ds.separator,
            null_markers=ds.null_markers,
        )

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse a {Provider} dataset from its URL.

        Re-raises all network errors as ``OSError`` so
        ``CachedLoader.download()`` can handle stale-cache fallback.
        """
        self._logger.debug(
            "event=fetch_start provider={provider} dataset_id=%s url=%s",
            self._dataset.dataset_id,
            config.url,
        )

        try:
            with urllib.request.urlopen(
                config.url, timeout=_HTTP_TIMEOUT_SECONDS
            ) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download {provider}/{self._dataset.dataset_id} "
                f"from {config.url}: {exc}"
            ) from exc

        # === FORMAT-SPECIFIC DECOMPRESSION ===
        # For gzip: csv_bytes = gzip.decompress(raw_bytes)
        #   CRITICAL: catch gzip.BadGzipFile and raise DataSourceValidationError
        #   (NOT OSError — it must not trigger stale-cache fallback)
        # For zip: use zipfile.ZipFile(io.BytesIO(raw_bytes))
        # For plain CSV: csv_bytes = raw_bytes

        table = self._parse_csv(raw_bytes)

        self._logger.debug(
            "event=fetch_complete provider={provider} dataset_id=%s "
            "rows=%d columns=%d",
            self._dataset.dataset_id,
            table.num_rows,
            table.num_columns,
        )
        return table

    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
        """Parse CSV bytes into a pa.Table with schema enforcement."""
        ds = self._dataset
        raw_names = [col[0] for col in ds.columns]
        project_names = [col[1] for col in ds.columns]
        expected_schema = self.schema()

        # CRITICAL: column_types uses RAW column names as keys,
        # but looks up types from expected_schema using PROJECT names
        column_types: dict[str, pa.DataType] = {}
        for raw_name, proj_name in ds.columns:
            column_types[raw_name] = expected_schema.field(proj_name).type

        convert_options = pcsv.ConvertOptions(
            null_values=list(ds.null_markers),
            column_types=column_types,
            include_columns=raw_names,
        )
        parse_options = pcsv.ParseOptions(delimiter=ds.separator)
        read_options = pcsv.ReadOptions(encoding=ds.encoding)

        table = pcsv.read_csv(
            io.BytesIO(csv_bytes),
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options,
        )

        # CRITICAL: rename from raw source names to project names
        table = table.rename_columns(project_names)
        return table


# ====================================================================
# Factory and helper functions
# ====================================================================


def get_{provider}_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
) -> {Provider}Loader:
    """Factory: construct a ``{Provider}Loader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``{PROVIDER}_AVAILABLE_DATASETS``.
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to
        ``reformlab.population.loaders.{provider}``.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in {PROVIDER}_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown {Provider} dataset",
            reason=(
                f"Requested dataset '{dataset_id}' is not in "
                "the {Provider} catalog"
            ),
            fix=(
                "Available datasets: "
                f"{', '.join({PROVIDER}_AVAILABLE_DATASETS)}"
            ),
        )
    if logger is None:
        logger = logging.getLogger(
            "reformlab.population.loaders.{provider}"
        )
    return {Provider}Loader(
        cache=cache,
        logger=logger,
        dataset={PROVIDER}_CATALOG[dataset_id],
    )


def make_{provider}_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``{PROVIDER}_AVAILABLE_DATASETS``.
    **params : str
        Additional parameters used to differentiate cache slots only.
        These are NOT appended to the download URL.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in {PROVIDER}_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown {Provider} dataset",
            reason=(
                f"Requested dataset '{dataset_id}' is not in "
                "the {Provider} catalog"
            ),
            fix=(
                "Available datasets: "
                f"{', '.join({PROVIDER}_AVAILABLE_DATASETS)}"
            ),
        )
    ds = {PROVIDER}_CATALOG[dataset_id]
    return SourceConfig(
        provider="{provider}",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )
```

---

## Test Module Skeleton

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the {Provider} data source loader.

Covers protocol compliance, schema correctness, {format} parsing
(including missing value handling), factory functions, and the full
CachedLoader download lifecycle.
"""

from __future__ import annotations

import logging
import urllib.error
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError
from reformlab.population.loaders.{provider} import (
    _DATASET_SCHEMAS,
    {PROVIDER}_AVAILABLE_DATASETS,
    {PROVIDER}_CATALOG,
    {Provider}Dataset,
    {Provider}Loader,
    get_{provider}_loader,
    make_{provider}_config,
)


# ====================================================================
# Helpers
# ====================================================================


def _mock_urlopen(data: bytes) -> MagicMock:
    """Create a mock context manager for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.read.return_value = data
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def _make_loader(
    dataset_id: str = "FIRST_DATASET_ID",
) -> {Provider}Loader:
    """Create a {Provider}Loader with a mock cache."""
    cache = MagicMock(spec=SourceCache)
    cache.get.return_value = None  # cache miss
    return get_{provider}_loader(dataset_id, cache=cache)


# Generate realistic CSV fixture bytes matching the actual format.
# Use the actual separator, encoding, and null markers.

_FIXTURE_CSV = (
    "RAW_COL_1{sep}RAW_COL_2\n"
    "value1{sep}1.0\n"
    "value2{sep}2.0\n"
).format(sep="{separator}").encode("{encoding}")


# ====================================================================
# Protocol compliance
# ====================================================================


class Test{Provider}LoaderProtocol:
    """{Provider}Loader satisfies DataSourceLoader protocol."""

    def test_isinstance(self) -> None:
        loader = _make_loader()
        assert isinstance(loader, DataSourceLoader)

    def test_has_download_method(self) -> None:
        loader = _make_loader()
        assert hasattr(loader, "download")

    def test_has_status_method(self) -> None:
        loader = _make_loader()
        assert hasattr(loader, "status")

    def test_has_schema_method(self) -> None:
        loader = _make_loader()
        assert hasattr(loader, "schema")


# ====================================================================
# Schema
# ====================================================================


class Test{Provider}LoaderSchema:
    """schema() returns valid pa.Schema."""

    def test_schema_fields(self) -> None:
        loader = _make_loader()
        schema = loader.schema()
        assert isinstance(schema, pa.Schema)
        # Verify expected field names
        assert "project_col_1" in schema.names

    def test_schema_types(self) -> None:
        loader = _make_loader()
        schema = loader.schema()
        assert schema.field("project_col_1").type == pa.utf8()

    def test_all_datasets_have_schemas(self) -> None:
        for ds_id in {PROVIDER}_AVAILABLE_DATASETS:
            assert ds_id in _DATASET_SCHEMAS


# ====================================================================
# Fetch / parsing
# ====================================================================


class Test{Provider}LoaderFetch:
    """_fetch() correctly parses {format} fixtures."""

    @patch("reformlab.population.loaders.{provider}.urllib.request.urlopen")
    def test_parse_dataset(self, mock_urlopen_fn: MagicMock) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(_FIXTURE_CSV)
        loader = _make_loader()
        config = make_{provider}_config("FIRST_DATASET_ID")
        table = loader._fetch(config)
        assert table.num_rows == 2
        # Verify columns are PROJECT names (not raw)
        assert "project_col_1" in table.column_names


# ====================================================================
# HTTP errors
# ====================================================================


class Test{Provider}LoaderFetchHTTPError:
    """Network errors are caught and re-raised as OSError."""

    @patch("reformlab.population.loaders.{provider}.urllib.request.urlopen")
    def test_http_error_raises_oserror(
        self, mock_urlopen_fn: MagicMock
    ) -> None:
        mock_urlopen_fn.side_effect = urllib.error.HTTPError(
            "url", 404, "Not Found", {}, None  # type: ignore[arg-type]
        )
        loader = _make_loader()
        config = make_{provider}_config("FIRST_DATASET_ID")
        with pytest.raises(OSError, match="Failed to download"):
            loader._fetch(config)

    @patch("reformlab.population.loaders.{provider}.urllib.request.urlopen")
    def test_urlerror_raises_oserror(
        self, mock_urlopen_fn: MagicMock
    ) -> None:
        mock_urlopen_fn.side_effect = urllib.error.URLError("timeout")
        loader = _make_loader()
        config = make_{provider}_config("FIRST_DATASET_ID")
        with pytest.raises(OSError, match="Failed to download"):
            loader._fetch(config)


# ====================================================================
# Download integration (cache lifecycle)
# ====================================================================


class Test{Provider}LoaderDownloadIntegration:
    """Full download() cycle: cache miss -> fetch -> cache -> hit."""

    @patch("reformlab.population.loaders.{provider}.urllib.request.urlopen")
    def test_cache_miss_then_hit(
        self, mock_urlopen_fn: MagicMock
    ) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(_FIXTURE_CSV)
        cache = MagicMock(spec=SourceCache)
        cache.get.return_value = None  # miss
        loader = get_{provider}_loader(
            "FIRST_DATASET_ID", cache=cache
        )
        config = make_{provider}_config("FIRST_DATASET_ID")
        pop_data, manifest = loader.download(config)
        assert pop_data is not None
        cache.put.assert_called_once()


# ====================================================================
# Catalog
# ====================================================================


class Test{Provider}LoaderCatalog:
    """Catalog and factory function behavior."""

    def test_available_datasets_not_empty(self) -> None:
        assert len({PROVIDER}_AVAILABLE_DATASETS) >= 1

    def test_catalog_entries_are_datasets(self) -> None:
        for ds in {PROVIDER}_CATALOG.values():
            assert isinstance(ds, {Provider}Dataset)

    def test_factory_returns_loader(self) -> None:
        loader = _make_loader()
        assert isinstance(loader, {Provider}Loader)

    def test_factory_invalid_id_raises(self) -> None:
        cache = MagicMock(spec=SourceCache)
        with pytest.raises(DataSourceValidationError):
            get_{provider}_loader("nonexistent", cache=cache)

    def test_factory_default_logger(self) -> None:
        loader = _make_loader()
        assert loader._logger.name == (
            "reformlab.population.loaders.{provider}"
        )

    def test_factory_custom_logger(self) -> None:
        cache = MagicMock(spec=SourceCache)
        custom = logging.getLogger("custom")
        loader = get_{provider}_loader(
            "FIRST_DATASET_ID", cache=cache, logger=custom
        )
        assert loader._logger is custom


# ====================================================================
# make_config
# ====================================================================


class TestMake{Provider}Config:
    """make_{provider}_config produces correct SourceConfig."""

    def test_basic_config(self) -> None:
        config = make_{provider}_config("FIRST_DATASET_ID")
        assert isinstance(config, SourceConfig)
        assert config.provider == "{provider}"
        assert config.dataset_id == "FIRST_DATASET_ID"

    def test_config_with_params(self) -> None:
        config = make_{provider}_config(
            "FIRST_DATASET_ID", year="2023"
        )
        assert config.params == {{"year": "2023"}}

    def test_all_catalog_entries_produce_config(self) -> None:
        for ds_id in {PROVIDER}_AVAILABLE_DATASETS:
            config = make_{provider}_config(ds_id)
            assert config.provider == "{provider}"

    def test_invalid_id_raises(self) -> None:
        with pytest.raises(DataSourceValidationError):
            make_{provider}_config("nonexistent")


# ====================================================================
# Dataset dataclass
# ====================================================================


class Test{Provider}Dataset:
    """{Provider}Dataset is a frozen dataclass."""

    def test_frozen(self) -> None:
        ds = list({PROVIDER}_CATALOG.values())[0]
        with pytest.raises(AttributeError):
            ds.dataset_id = "mutated"  # type: ignore[misc]

    def test_defaults(self) -> None:
        ds = {Provider}Dataset(
            dataset_id="test",
            description="test",
            url="https://example.com",
        )
        assert ds.encoding == "{encoding}"
        assert ds.separator == "{separator}"
```

---

## Export Registration Pattern

In `__init__.py`, add a block like:

```python
from reformlab.population.loaders.{provider} import (
    {PROVIDER}_AVAILABLE_DATASETS,
    {PROVIDER}_CATALOG,
    {Provider}Dataset,
    {Provider}Loader,
    get_{provider}_loader,
    make_{provider}_config,
)
```

And add all six names to `__all__`.

---

## Format-Specific Variations

### Plain CSV (SDES pattern)
- `raw_bytes` passed directly to `_parse_csv()`
- ReadOptions may include `skip_rows`

### Gzip-compressed CSV (Eurostat pattern)
```python
import gzip

# In _fetch(), after downloading raw_bytes:
try:
    csv_bytes = gzip.decompress(raw_bytes)
except gzip.BadGzipFile as exc:
    # CRITICAL: raise DataSourceValidationError, NOT OSError
    # BadGzipFile must NOT trigger stale-cache fallback
    raise DataSourceValidationError(
        summary="Corrupt gzip archive",
        reason=f"...: {exc}",
        fix="...",
    ) from exc
```

### ZIP-wrapped CSV (INSEE pattern)
```python
import zipfile

# In _fetch(), after downloading raw_bytes:
with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
    names = zf.namelist()
    csv_name = next(n for n in names if n.endswith(".csv"))
    csv_bytes = zf.read(csv_name)
```

### Encoding fallback (ADEME pattern)
```python
# In _parse_csv(), wrap the pcsv.read_csv call:
try:
    table = pcsv.read_csv(...)
except (pa.ArrowInvalid, pa.lib.ArrowKeyError):
    self._logger.debug(
        "event=encoding_fallback provider={provider} "
        "dataset_id=%s primary=%s fallback=utf-8",
        ds.dataset_id, ds.encoding,
    )
    read_options = pcsv.ReadOptions(encoding="utf-8")
    table = pcsv.read_csv(
        io.BytesIO(csv_bytes),
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options,
    )
```

---

## Quality Check Commands

```bash
uv run ruff check src/reformlab/population/loaders/{provider}.py tests/population/loaders/test_{provider}.py
uv run ruff format --check src/reformlab/population/loaders/{provider}.py tests/population/loaders/test_{provider}.py
uv run mypy src/reformlab/population/loaders/{provider}.py
uv run pytest tests/population/loaders/test_{provider}.py -v
```

All must pass with zero errors before the loader is considered complete.

---

## Naming Conventions

| Concept | Convention | Example |
|---------|-----------|---------|
| Provider (code) | lowercase snake_case | `world_bank` |
| Provider (class prefix) | PascalCase | `WorldBank` |
| Provider (constant prefix) | UPPER_SNAKE | `WORLD_BANK` |
| Dataset ID | lowercase snake_case | `eu_silc_puf` |
| Column constant | `_{DATASET_ID}_COLUMNS` | `_EU_SILC_PUF_COLUMNS` |
| Schema function | `_{dataset_id}_schema()` | `_eu_silc_puf_schema()` |
| Logger name | `reformlab.population.loaders.{provider}` | `reformlab.population.loaders.world_bank` |

---

## Existing Loaders Reference

| Provider | Module | Datasets | Format | Encoding | Separator | Null Markers |
|----------|--------|----------|--------|----------|-----------|--------------|
| insee | insee.py | 3 (Filosofi income) | ZIP→CSV | UTF-8 (Latin-1 fallback) | `;` | `s`, `nd`, `` |
| eurostat | eurostat.py | 2 (income, energy) | CSV.GZ | UTF-8 | `,` | ``, `:` |
| ademe | ademe.py | 1 (emission factors) | CSV | Windows-1252 (UTF-8 fallback) | `;` | `` |
| sdes | sdes.py | 1 (vehicle fleet) | CSV | UTF-8 | `;` | `` |
