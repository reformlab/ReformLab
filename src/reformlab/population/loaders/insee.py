# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""INSEE institutional data source loader.

Downloads, caches, and schema-validates key INSEE Filosofi income
distribution datasets (commune-level and IRIS-level). Concrete
implementation of the ``DataSourceLoader`` protocol via ``CachedLoader``.

This is the first concrete loader in the population subsystem, establishing
the pattern for Eurostat, ADEME, and SDES loaders (Story 11.3).

Implements Story 11.2 (Implement INSEE data source loader).
References: FR36 (download and cache public datasets), FR37 (browse
available datasets).
"""

from __future__ import annotations

import http.client
import io
import logging
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import pyarrow as pa
import pyarrow.csv as pcsv

from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.errors import DataSourceValidationError

if TYPE_CHECKING:
    from reformlab.population.loaders.cache import SourceCache


# ====================================================================
# INSEE dataset metadata
# ====================================================================


@dataclass(frozen=True)
class INSEEDataset:
    """Metadata for a known INSEE dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_insee_column_name, project_column_name)``.
    """

    dataset_id: str
    description: str
    url: str
    file_format: Literal["csv", "zip"]
    encoding: str = "utf-8"
    separator: str = ";"
    null_markers: tuple[str, ...] = ("s", "nd", "")
    columns: tuple[tuple[str, str], ...] = ()


# ====================================================================
# Dataset catalog
# ====================================================================

_FILOSOFI_2021_COMMUNE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("CODGEO", "commune_code"),
    ("LIBGEO", "commune_name"),
    ("NBMENFISC21", "nb_fiscal_households"),
    ("MED21", "median_income"),
    ("D121", "decile_1"),
    ("D221", "decile_2"),
    ("D321", "decile_3"),
    ("D421", "decile_4"),
    ("D521", "decile_5"),
    ("D621", "decile_6"),
    ("D721", "decile_7"),
    ("D821", "decile_8"),
    ("D921", "decile_9"),
)

_FILOSOFI_2021_IRIS_DECLARED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("IRIS", "iris_code"),
    ("LIBIRIS", "iris_name"),
    ("COM", "commune_code"),
    ("LIBCOM", "commune_name"),
    ("DEC_MED21", "median_declared_income"),
    ("DEC_D121", "decile_1"),
    ("DEC_D221", "decile_2"),
    ("DEC_D321", "decile_3"),
    ("DEC_D421", "decile_4"),
    ("DEC_D521", "decile_5"),
    ("DEC_D621", "decile_6"),
    ("DEC_D721", "decile_7"),
    ("DEC_D821", "decile_8"),
    ("DEC_D921", "decile_9"),
)

_FILOSOFI_2021_IRIS_DISPOSABLE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("IRIS", "iris_code"),
    ("LIBIRIS", "iris_name"),
    ("COM", "commune_code"),
    ("LIBCOM", "commune_name"),
    ("DISP_MED21", "median_disposable_income"),
    ("DISP_D121", "decile_1"),
    ("DISP_D221", "decile_2"),
    ("DISP_D321", "decile_3"),
    ("DISP_D421", "decile_4"),
    ("DISP_D521", "decile_5"),
    ("DISP_D621", "decile_6"),
    ("DISP_D721", "decile_7"),
    ("DISP_D821", "decile_8"),
    ("DISP_D921", "decile_9"),
)


INSEE_CATALOG: dict[str, INSEEDataset] = {
    "filosofi_2021_commune": INSEEDataset(
        dataset_id="filosofi_2021_commune",
        description="Filosofi 2021 commune-level income data (deciles D1-D9, median, poverty rate)",
        url="https://www.insee.fr/fr/statistiques/fichier/7758831/indic-struct-distrib-revenu-2021-COMMUNES.zip",
        file_format="zip",
        encoding="utf-8",
        separator=";",
        columns=_FILOSOFI_2021_COMMUNE_COLUMNS,
    ),
    "filosofi_2021_iris_declared": INSEEDataset(
        dataset_id="filosofi_2021_iris_declared",
        description="Filosofi 2021 IRIS-level declared income (quartiles/deciles)",
        url="https://www.insee.fr/fr/statistiques/fichier/8229323/BASE_TD_FILO_IRIS_2021_DEC_CSV.zip",
        file_format="zip",
        encoding="utf-8",
        separator=";",
        columns=_FILOSOFI_2021_IRIS_DECLARED_COLUMNS,
    ),
    "filosofi_2021_iris_disposable": INSEEDataset(
        dataset_id="filosofi_2021_iris_disposable",
        description="Filosofi 2021 IRIS-level disposable income (quartiles/deciles)",
        url="https://www.insee.fr/fr/statistiques/fichier/8229323/BASE_TD_FILO_IRIS_2021_DISP_CSV.zip",
        file_format="zip",
        encoding="utf-8",
        separator=";",
        columns=_FILOSOFI_2021_IRIS_DISPOSABLE_COLUMNS,
    ),
}

INSEE_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(INSEE_CATALOG.keys()))
"""Available INSEE dataset identifiers for discovery."""

AVAILABLE_DATASETS = INSEE_AVAILABLE_DATASETS
"""Backward-compatible alias for ``INSEE_AVAILABLE_DATASETS``."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================


def _commune_schema() -> pa.Schema:
    return pa.schema([
        pa.field("commune_code", pa.utf8()),
        pa.field("commune_name", pa.utf8()),
        pa.field("nb_fiscal_households", pa.float64()),
        pa.field("median_income", pa.float64()),
        pa.field("decile_1", pa.float64()),
        pa.field("decile_2", pa.float64()),
        pa.field("decile_3", pa.float64()),
        pa.field("decile_4", pa.float64()),
        pa.field("decile_5", pa.float64()),
        pa.field("decile_6", pa.float64()),
        pa.field("decile_7", pa.float64()),
        pa.field("decile_8", pa.float64()),
        pa.field("decile_9", pa.float64()),
    ])


def _iris_declared_schema() -> pa.Schema:
    return pa.schema([
        pa.field("iris_code", pa.utf8()),
        pa.field("iris_name", pa.utf8()),
        pa.field("commune_code", pa.utf8()),
        pa.field("commune_name", pa.utf8()),
        pa.field("median_declared_income", pa.float64()),
        pa.field("decile_1", pa.float64()),
        pa.field("decile_2", pa.float64()),
        pa.field("decile_3", pa.float64()),
        pa.field("decile_4", pa.float64()),
        pa.field("decile_5", pa.float64()),
        pa.field("decile_6", pa.float64()),
        pa.field("decile_7", pa.float64()),
        pa.field("decile_8", pa.float64()),
        pa.field("decile_9", pa.float64()),
    ])


def _iris_disposable_schema() -> pa.Schema:
    return pa.schema([
        pa.field("iris_code", pa.utf8()),
        pa.field("iris_name", pa.utf8()),
        pa.field("commune_code", pa.utf8()),
        pa.field("commune_name", pa.utf8()),
        pa.field("median_disposable_income", pa.float64()),
        pa.field("decile_1", pa.float64()),
        pa.field("decile_2", pa.float64()),
        pa.field("decile_3", pa.float64()),
        pa.field("decile_4", pa.float64()),
        pa.field("decile_5", pa.float64()),
        pa.field("decile_6", pa.float64()),
        pa.field("decile_7", pa.float64()),
        pa.field("decile_8", pa.float64()),
        pa.field("decile_9", pa.float64()),
    ])


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "filosofi_2021_commune": _commune_schema(),
    "filosofi_2021_iris_declared": _iris_declared_schema(),
    "filosofi_2021_iris_disposable": _iris_disposable_schema(),
}


# ====================================================================
# INSEELoader
# ====================================================================

# Network-error types caught in _fetch and re-raised as OSError
_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for INSEE HTTP downloads (5 minutes, accommodates large IRIS files)."""


class INSEELoader(CachedLoader):
    """Concrete loader for INSEE institutional data sources.

    Extends ``CachedLoader`` with INSEE-specific CSV parsing, ZIP extraction,
    encoding fallback (UTF-8 → Latin-1), and null marker handling (``"s"``,
    ``"nd"``).

    Each loader instance handles one ``INSEEDataset``. Use ``get_insee_loader``
    factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: INSEEDataset,
    ) -> None:
        self._dataset = dataset
        super().__init__(cache=cache, logger=logger)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's dataset."""
        return _DATASET_SCHEMAS[self._dataset.dataset_id]

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse an INSEE dataset from its URL.

        Handles ZIP-wrapped CSVs, encoding fallback, and INSEE null markers.
        Re-raises all network errors as ``OSError`` so ``CachedLoader.download()``
        can handle stale-cache fallback.
        """
        self._logger.debug(
            "event=fetch_start provider=%s dataset_id=%s url=%s",
            config.provider,
            self._dataset.dataset_id,
            config.url,
        )

        try:
            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download insee/{self._dataset.dataset_id} "
                f"from {config.url}: {exc}"
            ) from exc

        # Extract CSV from ZIP if needed
        csv_bytes = self._extract_csv_bytes(raw_bytes)

        # Parse CSV with encoding fallback
        table = self._parse_csv(csv_bytes)

        self._logger.debug(
            "event=fetch_complete provider=%s dataset_id=%s url=%s rows=%d columns=%d",
            config.provider,
            self._dataset.dataset_id,
            config.url,
            table.num_rows,
            table.num_columns,
        )
        return table

    def _extract_csv_bytes(self, raw_bytes: bytes) -> bytes:
        """Extract CSV bytes, handling ZIP-wrapped files."""
        if self._dataset.file_format != "zip":
            return raw_bytes

        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                csv_entries = [
                    name for name in zf.namelist()
                    if name.lower().endswith(".csv")
                ]
                if len(csv_entries) == 0:
                    raise DataSourceValidationError(
                        summary="No CSV file in ZIP archive",
                        reason=f"ZIP archive for insee/{self._dataset.dataset_id} "
                        f"contains no .csv files. Archive contents: {zf.namelist()}",
                        fix="Check the INSEE download URL — the archive format may have changed",
                    )
                if len(csv_entries) > 1:
                    raise DataSourceValidationError(
                        summary="Multiple CSV files in ZIP archive",
                        reason=f"ZIP archive for insee/{self._dataset.dataset_id} "
                        f"contains {len(csv_entries)} CSV files: {csv_entries}",
                        fix="Update the loader to select the correct CSV file from the archive",
                    )
                return zf.read(csv_entries[0])
        except zipfile.BadZipFile as exc:
            raise DataSourceValidationError(
                summary="Invalid ZIP archive",
                reason=f"Downloaded file for insee/{self._dataset.dataset_id} "
                f"is not a valid ZIP archive: {exc}",
                fix="Check the INSEE download URL — the file may have moved or changed format",
            ) from exc

    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
        """Parse CSV bytes into a pa.Table with schema enforcement.

        Tries UTF-8 first, falls back to Latin-1 on decode error.
        """
        ds = self._dataset
        raw_names = [col[0] for col in ds.columns]
        project_names = [col[1] for col in ds.columns]
        expected_schema = self.schema()

        # Build column_types mapping using RAW column names
        column_types: dict[str, pa.DataType] = {}
        for raw_name, proj_name in ds.columns:
            field = expected_schema.field(proj_name)
            column_types[raw_name] = field.type

        convert_options = pcsv.ConvertOptions(
            null_values=list(ds.null_markers),
            column_types=column_types,
            include_columns=raw_names,
        )
        parse_options = pcsv.ParseOptions(delimiter=ds.separator)

        # Try primary encoding, fallback to latin-1 on decode error
        read_options = pcsv.ReadOptions(encoding=ds.encoding)
        try:
            table = pcsv.read_csv(
                io.BytesIO(csv_bytes),
                read_options=read_options,
                parse_options=parse_options,
                convert_options=convert_options,
            )
        except pa.ArrowInvalid:
            self._logger.debug(
                "event=encoding_fallback provider=insee dataset_id=%s "
                "primary=%s fallback=latin-1",
                ds.dataset_id,
                ds.encoding,
            )
            fallback_options = pcsv.ReadOptions(encoding="latin-1")
            table = pcsv.read_csv(
                io.BytesIO(csv_bytes),
                read_options=fallback_options,
                parse_options=parse_options,
                convert_options=convert_options,
            )

        # Rename columns from raw INSEE names to project names
        table = table.rename_columns(project_names)
        return table


# ====================================================================
# Factory and helper functions
# ====================================================================


def get_insee_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
) -> INSEELoader:
    """Factory: construct an ``INSEELoader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``AVAILABLE_DATASETS`` (e.g. ``"filosofi_2021_commune"``).
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to ``reformlab.population.loaders.insee``.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in INSEE_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown INSEE dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the INSEE catalog",
            fix=f"Available datasets: {', '.join(INSEE_AVAILABLE_DATASETS)}",
        )
    if logger is None:
        logger = logging.getLogger("reformlab.population.loaders.insee")
    return INSEELoader(
        cache=cache,
        logger=logger,
        dataset=INSEE_CATALOG[dataset_id],
    )


def make_insee_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``AVAILABLE_DATASETS``.
    **params : str
        Additional query parameters for the download request.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in INSEE_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown INSEE dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the INSEE catalog",
            fix=f"Available datasets: {', '.join(INSEE_AVAILABLE_DATASETS)}",
        )
    ds = INSEE_CATALOG[dataset_id]
    return SourceConfig(
        provider="insee",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )
