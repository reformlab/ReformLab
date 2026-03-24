# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""SDES institutional data source loader.

Downloads, caches, and schema-validates SDES vehicle fleet composition
datasets (communal-level data from data.gouv.fr). Concrete implementation
of the ``DataSourceLoader`` protocol via ``CachedLoader``.

Handles DiDo CSV format with UTF-8 encoding, semicolon separator, and
optional header row skipping for description rows.

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

from reformlab.computation.ingestion import DataSchema
from reformlab.data.descriptor import DatasetDescriptor
from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.errors import DataSourceValidationError

if TYPE_CHECKING:
    from reformlab.population.loaders.cache import SourceCache


# ====================================================================
# SDES dataset metadata
# ====================================================================


@dataclass(frozen=True)
class SDESDataset:
    """Metadata for a known SDES dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_column_name, project_column_name)``.

    The ``skip_rows`` field specifies the number of header rows to skip
    before the column name row (DiDo CSVs may have description rows).
    """

    dataset_id: str
    description: str
    url: str
    encoding: str = "utf-8"
    separator: str = ";"
    null_markers: tuple[str, ...] = ("",)
    columns: tuple[tuple[str, str], ...] = ()
    skip_rows: int = 0


# ====================================================================
# Dataset catalog
# ====================================================================

_VEHICLE_FLEET_COLUMNS: tuple[tuple[str, str], ...] = (
    ("REGION_CODE", "region_code"),
    ("REGION_LIBELLE", "region_name"),
    ("CLASSE_VEHICULE", "vehicle_class"),
    ("CATEGORIE_VEHICULE", "vehicle_category"),
    ("CARBURANT", "fuel_type"),
    ("AGE", "vehicle_age"),
    ("CRITAIR", "critair_sticker"),
    ("PARC_2022", "fleet_count_2022"),
)

SDES_CATALOG: dict[str, SDESDataset] = {
    "vehicle_fleet": SDESDataset(
        dataset_id="vehicle_fleet",
        description=(
            "Vehicle fleet composition by fuel type, age, "
            "Crit'Air, region (communal-level data from data.gouv.fr)"
        ),
        url="https://www.data.gouv.fr/api/1/datasets/r/2f9fd9c8-e6e1-450e-8548-f479b8a401cd",
        columns=_VEHICLE_FLEET_COLUMNS,
    ),
}

SDES_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(SDES_CATALOG.keys()))
"""Available SDES dataset identifiers for discovery."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================


def _vehicle_fleet_schema() -> pa.Schema:
    return pa.schema([
        pa.field("region_code", pa.utf8()),
        pa.field("region_name", pa.utf8()),
        pa.field("vehicle_class", pa.utf8()),
        pa.field("vehicle_category", pa.utf8()),
        pa.field("fuel_type", pa.utf8()),
        pa.field("vehicle_age", pa.utf8()),
        pa.field("critair_sticker", pa.utf8()),
        pa.field("fleet_count_2022", pa.float64()),
    ])


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "vehicle_fleet": _vehicle_fleet_schema(),
}


# ====================================================================
# SDESLoader
# ====================================================================

_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for SDES HTTP downloads (5 minutes)."""


class SDESLoader(CachedLoader):
    """Concrete loader for SDES institutional data sources.

    Extends ``CachedLoader`` with SDES-specific DiDo CSV parsing, UTF-8
    encoding, semicolon separator, and optional header row skipping.

    Each loader instance handles one ``SDESDataset``. Use
    ``get_sdes_loader`` factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: SDESDataset,
    ) -> None:
        self._dataset = dataset
        super().__init__(cache=cache, logger=logger)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's dataset."""
        return _DATASET_SCHEMAS[self._dataset.dataset_id]

    def descriptor(self) -> DatasetDescriptor:
        """Return the ``DatasetDescriptor`` for this loader's SDES dataset."""
        ds = self._dataset
        pa_schema = self.schema()
        all_cols = tuple(pa_schema.names)
        return DatasetDescriptor(
            dataset_id=ds.dataset_id,
            provider="sdes",
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
            skip_rows=ds.skip_rows,
        )

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse an SDES dataset from its URL.

        Handles DiDo CSV format with optional header row skipping.
        Re-raises all network errors as ``OSError`` so
        ``CachedLoader.download()`` can handle stale-cache fallback.
        """
        self._logger.debug(
            "event=fetch_start provider=sdes dataset_id=%s url=%s",
            self._dataset.dataset_id,
            config.url,
        )

        try:
            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download sdes/{self._dataset.dataset_id} "
                f"from {config.url}: {exc}"
            ) from exc

        table = self._parse_csv(raw_bytes)

        self._logger.debug(
            "event=fetch_complete provider=sdes dataset_id=%s rows=%d columns=%d",
            self._dataset.dataset_id,
            table.num_rows,
            table.num_columns,
        )
        return table

    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
        """Parse DiDo CSV bytes into a pa.Table with schema enforcement."""
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
        read_options = pcsv.ReadOptions(
            encoding=ds.encoding,
            skip_rows=ds.skip_rows,
        )

        table = pcsv.read_csv(
            io.BytesIO(csv_bytes),
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options,
        )

        # Rename columns from raw DiDo names to project names
        table = table.rename_columns(project_names)
        return table


# ====================================================================
# Factory and helper functions
# ====================================================================


def get_sdes_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
) -> SDESLoader:
    """Factory: construct an ``SDESLoader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``SDES_AVAILABLE_DATASETS`` (e.g. ``"vehicle_fleet"``).
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to ``reformlab.population.loaders.sdes``.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in SDES_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown SDES dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the SDES catalog",
            fix=f"Available datasets: {', '.join(SDES_AVAILABLE_DATASETS)}",
        )
    if logger is None:
        logger = logging.getLogger("reformlab.population.loaders.sdes")
    return SDESLoader(
        cache=cache,
        logger=logger,
        dataset=SDES_CATALOG[dataset_id],
    )


def make_sdes_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``SDES_AVAILABLE_DATASETS``.
    **params : str
        Additional parameters used to differentiate cache slots only.
        These are NOT appended to the download URL — the full dataset is
        always downloaded from the catalog URL regardless of params values.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in SDES_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown SDES dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the SDES catalog",
            fix=f"Available datasets: {', '.join(SDES_AVAILABLE_DATASETS)}",
        )
    ds = SDES_CATALOG[dataset_id]
    return SourceConfig(
        provider="sdes",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )
