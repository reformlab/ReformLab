"""ADEME institutional data source loader.

Downloads, caches, and schema-validates ADEME Base Carbone emission factor
datasets. Concrete implementation of the ``DataSourceLoader`` protocol via
``CachedLoader``.

Handles Windows-1252 encoding (primary) with UTF-8 fallback, semicolon
separator, and French-language column names with accents.

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
References: FR36 (download and cache public datasets), FR37 (browse
available datasets).
"""

from __future__ import annotations

import http.client
import io
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.csv as pcsv

from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.errors import DataSourceValidationError

if TYPE_CHECKING:
    from reformlab.population.loaders.cache import SourceCache


# ====================================================================
# ADEME dataset metadata
# ====================================================================


@dataclass(frozen=True)
class ADEMEDataset:
    """Metadata for a known ADEME dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_column_name, project_column_name)``.
    """

    dataset_id: str
    description: str
    url: str
    encoding: str = "windows-1252"
    separator: str = ";"
    null_markers: tuple[str, ...] = ("",)
    columns: tuple[tuple[str, str], ...] = ()


# ====================================================================
# Dataset catalog
# ====================================================================

_BASE_CARBONE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Identifiant de l'\xe9l\xe9ment", "element_id"),
    ("Nom base fran\xe7ais", "name_fr"),
    ("Nom attribut fran\xe7ais", "attribute_name_fr"),
    ("Type Ligne", "line_type"),
    ("Unit\xe9 fran\xe7ais", "unit_fr"),
    ("Total poste non d\xe9compos\xe9", "total_co2e"),
    ("CO2f", "co2_fossil"),
    ("CH4f", "ch4_fossil"),
    ("CH4b", "ch4_biogenic"),
    ("N2O", "n2o"),
    ("CO2b", "co2_biogenic"),
    ("Autre GES", "other_ghg"),
    ("Localisation g\xe9ographique", "geography"),
    ("Sous-localisation g\xe9ographique fran\xe7ais", "sub_geography"),
    ("Contributeur", "contributor"),
)

ADEME_CATALOG: dict[str, ADEMEDataset] = {
    "base_carbone": ADEMEDataset(
        dataset_id="base_carbone",
        description="Base Carbone V23.6 emission factors (CSV from data.gouv.fr)",
        url="https://www.data.gouv.fr/api/1/datasets/r/ac6a3044-459c-4520-b85a-7e1740f7cd1f",
        columns=_BASE_CARBONE_COLUMNS,
    ),
}

ADEME_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(ADEME_CATALOG.keys()))
"""Available ADEME dataset identifiers for discovery."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================


def _base_carbone_schema() -> pa.Schema:
    return pa.schema([
        pa.field("element_id", pa.int64()),
        pa.field("name_fr", pa.utf8()),
        pa.field("attribute_name_fr", pa.utf8()),
        pa.field("line_type", pa.utf8()),
        pa.field("unit_fr", pa.utf8()),
        pa.field("total_co2e", pa.float64()),
        pa.field("co2_fossil", pa.float64()),
        pa.field("ch4_fossil", pa.float64()),
        pa.field("ch4_biogenic", pa.float64()),
        pa.field("n2o", pa.float64()),
        pa.field("co2_biogenic", pa.float64()),
        pa.field("other_ghg", pa.float64()),
        pa.field("geography", pa.utf8()),
        pa.field("sub_geography", pa.utf8()),
        pa.field("contributor", pa.utf8()),
    ])


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "base_carbone": _base_carbone_schema(),
}


# ====================================================================
# ADEMELoader
# ====================================================================

_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for ADEME HTTP downloads (5 minutes)."""


class ADEMELoader(CachedLoader):
    """Concrete loader for ADEME institutional data sources.

    Extends ``CachedLoader`` with ADEME-specific CSV parsing, Windows-1252
    encoding (primary) with UTF-8 fallback, semicolon separator, and
    French-language column names.

    Each loader instance handles one ``ADEMEDataset``. Use
    ``get_ademe_loader`` factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: ADEMEDataset,
    ) -> None:
        self._dataset = dataset
        super().__init__(cache=cache, logger=logger)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's dataset."""
        return _DATASET_SCHEMAS[self._dataset.dataset_id]

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse an ADEME dataset from its URL.

        Handles Windows-1252 encoding with UTF-8 fallback and semicolon
        separator. Re-raises all network errors as ``OSError`` so
        ``CachedLoader.download()`` can handle stale-cache fallback.
        """
        self._logger.debug(
            "event=fetch_start provider=ademe dataset_id=%s url=%s",
            self._dataset.dataset_id,
            config.url,
        )

        try:
            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download ademe/{self._dataset.dataset_id} "
                f"from {config.url}: {exc}"
            ) from exc

        table = self._parse_csv(raw_bytes)

        self._logger.debug(
            "event=fetch_complete provider=ademe dataset_id=%s rows=%d columns=%d",
            self._dataset.dataset_id,
            table.num_rows,
            table.num_columns,
        )
        return table

    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
        """Parse CSV bytes into a pa.Table with schema enforcement.

        Tries Windows-1252 first, falls back to UTF-8 on decode error.
        """
        ds = self._dataset
        raw_names = [col[0] for col in ds.columns]
        project_names = [col[1] for col in ds.columns]
        expected_schema = self.schema()

        # Build column_types mapping using RAW column names
        column_types: dict[str, pa.DataType] = {}
        for raw_name, proj_name in ds.columns:
            column_types[raw_name] = expected_schema.field(proj_name).type

        convert_options = pcsv.ConvertOptions(
            null_values=list(ds.null_markers),
            column_types=column_types,
            include_columns=raw_names,
        )
        parse_options = pcsv.ParseOptions(delimiter=ds.separator)

        # Try primary encoding (Windows-1252), fallback to UTF-8 on decode error.
        # ArrowInvalid: byte sequence invalid for the encoding.
        # ArrowKeyError: decoding succeeded but column names are garbled
        # (UTF-8 multi-byte chars decoded as Windows-1252 produce different names).
        read_options = pcsv.ReadOptions(encoding=ds.encoding)
        try:
            table = pcsv.read_csv(
                io.BytesIO(csv_bytes),
                read_options=read_options,
                parse_options=parse_options,
                convert_options=convert_options,
            )
        except (pa.ArrowInvalid, pa.lib.ArrowKeyError):
            self._logger.debug(
                "event=encoding_fallback provider=ademe dataset_id=%s "
                "primary=%s fallback=utf-8",
                ds.dataset_id,
                ds.encoding,
            )
            fallback_options = pcsv.ReadOptions(encoding="utf-8")
            try:
                table = pcsv.read_csv(
                    io.BytesIO(csv_bytes),
                    read_options=fallback_options,
                    parse_options=parse_options,
                    convert_options=convert_options,
                )
            except (pa.ArrowInvalid, pa.lib.ArrowKeyError) as exc2:
                raise DataSourceValidationError(
                    summary="CSV parsing failed",
                    reason=f"ademe/{ds.dataset_id} could not be decoded as "
                    f"{ds.encoding} or utf-8: {exc2}",
                    fix="Check the ADEME source URL — the file encoding "
                    "may have changed",
                ) from exc2

        # Rename columns from raw French names to project names
        table = table.rename_columns(project_names)
        return table


# ====================================================================
# Factory and helper functions
# ====================================================================


def get_ademe_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
) -> ADEMELoader:
    """Factory: construct an ``ADEMELoader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``ADEME_AVAILABLE_DATASETS`` (e.g. ``"base_carbone"``).
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to ``reformlab.population.loaders.ademe``.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in ADEME_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown ADEME dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the ADEME catalog",
            fix=f"Available datasets: {', '.join(ADEME_AVAILABLE_DATASETS)}",
        )
    if logger is None:
        logger = logging.getLogger("reformlab.population.loaders.ademe")
    return ADEMELoader(
        cache=cache,
        logger=logger,
        dataset=ADEME_CATALOG[dataset_id],
    )


def make_ademe_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``ADEME_AVAILABLE_DATASETS``.
    **params : str
        Additional parameters used to differentiate cache slots only.
        These are NOT appended to the download URL — the full dataset is
        always downloaded from the catalog URL regardless of params values.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in ADEME_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown ADEME dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the ADEME catalog",
            fix=f"Available datasets: {', '.join(ADEME_AVAILABLE_DATASETS)}",
        )
    ds = ADEME_CATALOG[dataset_id]
    return SourceConfig(
        provider="ademe",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )
