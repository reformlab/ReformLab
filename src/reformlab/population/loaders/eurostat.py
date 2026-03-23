# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Eurostat institutional data source loader.

Downloads, caches, and schema-validates Eurostat SDMX-CSV datasets
(EU-SILC income distribution, household energy consumption). Concrete
implementation of the ``DataSourceLoader`` protocol via ``CachedLoader``.

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
References: FR36 (download and cache public datasets), FR37 (browse
available datasets).
"""

from __future__ import annotations

import gzip
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
# Eurostat dataset metadata
# ====================================================================


@dataclass(frozen=True)
class EurostatDataset:
    """Metadata for a known Eurostat dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_sdmx_column_name, project_column_name)``.
    """

    dataset_id: str
    description: str
    url: str
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("", ":")
    columns: tuple[tuple[str, str], ...] = ()


# ====================================================================
# Dataset catalog
# ====================================================================

_ILC_DI01_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("quantile", "quantile"),
    ("indic_il", "indicator"),
    ("currency", "currency"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)

_NRG_D_HHQ_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("nrg_bal", "energy_balance"),
    ("siec", "energy_product"),
    ("unit", "unit"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)

EUROSTAT_CATALOG: dict[str, EurostatDataset] = {
    "ilc_di01": EurostatDataset(
        dataset_id="ilc_di01",
        description="Income distribution by quantile (EU-SILC deciles D1-D10, shares/EUR)",
        url="https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/ilc_di01?format=SDMX-CSV&compressed=true",
        columns=_ILC_DI01_COLUMNS,
    ),
    "nrg_d_hhq": EurostatDataset(
        dataset_id="nrg_d_hhq",
        description="Disaggregated final energy consumption in households",
        url="https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_d_hhq?format=SDMX-CSV&compressed=true",
        columns=_NRG_D_HHQ_COLUMNS,
    ),
}

EUROSTAT_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(EUROSTAT_CATALOG.keys()))
"""Available Eurostat dataset identifiers for discovery."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================


def _ilc_di01_schema() -> pa.Schema:
    return pa.schema([
        pa.field("frequency", pa.utf8()),
        pa.field("quantile", pa.utf8()),
        pa.field("indicator", pa.utf8()),
        pa.field("currency", pa.utf8()),
        pa.field("country", pa.utf8()),
        pa.field("time_period", pa.utf8()),
        pa.field("value", pa.float64()),
        pa.field("obs_flag", pa.utf8()),
    ])


def _nrg_d_hhq_schema() -> pa.Schema:
    return pa.schema([
        pa.field("frequency", pa.utf8()),
        pa.field("energy_balance", pa.utf8()),
        pa.field("energy_product", pa.utf8()),
        pa.field("unit", pa.utf8()),
        pa.field("country", pa.utf8()),
        pa.field("time_period", pa.utf8()),
        pa.field("value", pa.float64()),
        pa.field("obs_flag", pa.utf8()),
    ])


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "ilc_di01": _ilc_di01_schema(),
    "nrg_d_hhq": _nrg_d_hhq_schema(),
}


# ====================================================================
# EurostatLoader
# ====================================================================

_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for Eurostat HTTP downloads (5 minutes)."""


class EurostatLoader(CachedLoader):
    """Concrete loader for Eurostat institutional data sources.

    Extends ``CachedLoader`` with Eurostat-specific gzip-compressed SDMX-CSV
    parsing, column selection and renaming, and null marker handling
    (empty string and ``":"``) .

    Each loader instance handles one ``EurostatDataset``. Use
    ``get_eurostat_loader`` factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: EurostatDataset,
    ) -> None:
        self._dataset = dataset
        super().__init__(cache=cache, logger=logger)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's dataset."""
        return _DATASET_SCHEMAS[self._dataset.dataset_id]

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse a Eurostat SDMX-CSV dataset.

        Downloads gzip-compressed CSV, decompresses, parses with pyarrow,
        selects and renames columns. Re-raises all network errors as
        ``OSError`` so ``CachedLoader.download()`` can handle stale-cache
        fallback.
        """
        self._logger.debug(
            "event=fetch_start provider=eurostat dataset_id=%s url=%s",
            self._dataset.dataset_id,
            config.url,
        )

        try:
            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download eurostat/{self._dataset.dataset_id} "
                f"from {config.url}: {exc}"
            ) from exc

        # Decompress gzip (file-level, NOT http-level).
        # CRITICAL: gzip.BadGzipFile inherits from OSError. If not caught
        # explicitly here, it propagates as OSError and CachedLoader.download()
        # triggers stale-cache fallback instead of raising a validation error.
        try:
            csv_bytes = gzip.decompress(raw_bytes)
        except (OSError, gzip.BadGzipFile) as exc:
            raise DataSourceValidationError(
                summary="Gzip decompression failed",
                reason=f"Downloaded content for eurostat/{self._dataset.dataset_id} "
                f"is not valid gzip: {exc}",
                fix="Check the Eurostat API URL and compressed=true parameter",
            ) from exc

        table = self._parse_csv(csv_bytes)

        self._logger.debug(
            "event=fetch_complete provider=eurostat dataset_id=%s rows=%d columns=%d",
            self._dataset.dataset_id,
            table.num_rows,
            table.num_columns,
        )
        return table

    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
        """Parse SDMX-CSV bytes into a pa.Table with schema enforcement."""
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
        read_options = pcsv.ReadOptions(encoding=ds.encoding)

        table = pcsv.read_csv(
            io.BytesIO(csv_bytes),
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options,
        )

        # Rename columns from raw SDMX names to project names
        table = table.rename_columns(project_names)
        return table


# ====================================================================
# Factory and helper functions
# ====================================================================


def get_eurostat_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
) -> EurostatLoader:
    """Factory: construct an ``EurostatLoader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``EUROSTAT_AVAILABLE_DATASETS`` (e.g. ``"ilc_di01"``).
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to ``reformlab.population.loaders.eurostat``.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in EUROSTAT_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown Eurostat dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the Eurostat catalog",
            fix=f"Available datasets: {', '.join(EUROSTAT_AVAILABLE_DATASETS)}",
        )
    if logger is None:
        logger = logging.getLogger("reformlab.population.loaders.eurostat")
    return EurostatLoader(
        cache=cache,
        logger=logger,
        dataset=EUROSTAT_CATALOG[dataset_id],
    )


def make_eurostat_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``EUROSTAT_AVAILABLE_DATASETS``.
    **params : str
        Additional parameters used to differentiate cache slots only.
        These are NOT appended to the download URL — the full dataset is
        always downloaded from the catalog URL regardless of params values.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in EUROSTAT_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown Eurostat dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the Eurostat catalog",
            fix=f"Available datasets: {', '.join(EUROSTAT_AVAILABLE_DATASETS)}",
        )
    ds = EUROSTAT_CATALOG[dataset_id]
    return SourceConfig(
        provider="eurostat",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )
