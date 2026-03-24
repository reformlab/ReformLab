# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""EU-SILC synthetic Public Use File data source loader.

Downloads, caches, and schema-validates Eurostat EU-SILC synthetic PUF
datasets (household register and household data). Concrete implementation
of the ``DataSourceLoader`` protocol via ``CachedLoader``.

Handles ZIP-wrapped CSV format with comma separator and UTF-8 encoding.
These are **fully synthetic** microdata published by Eurostat — they must
not be used for statistical inference or publication analysis.

Data source: https://ec.europa.eu/eurostat/web/microdata/public-microdata/statistics-on-income-and-living-conditions
"""

from __future__ import annotations

import http.client
import io
import logging
import urllib.error
import urllib.request
import zipfile
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
# EU-SILC dataset metadata
# ====================================================================


@dataclass(frozen=True)
class EuSilcDataset:
    """Metadata for a known EU-SILC PUF dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_column_name, project_column_name)``.
    """

    dataset_id: str
    description: str
    url: str
    file_suffix: str
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("",)
    columns: tuple[tuple[str, str], ...] = ()


# ====================================================================
# Dataset catalog
# ====================================================================

_SILC_PUF_D_COLUMNS: tuple[tuple[str, str], ...] = (
    ("DB010", "survey_year"),
    ("DB020", "country"),
    ("DB030", "household_id"),
    ("DB040", "region"),
    ("DB090", "household_weight"),
)

_SILC_PUF_H_COLUMNS: tuple[tuple[str, str], ...] = (
    ("HB010", "survey_year"),
    ("HB020", "country"),
    ("HB030", "household_id"),
    ("HY010", "total_gross_income"),
    ("HY020", "total_disposable_income"),
    ("HY022", "disposable_income_before_social_transfers"),
    ("HY023", "disposable_income_before_social_transfers_except_pensions"),
    ("HX010", "change_in_household_income"),
    ("HX040", "household_size"),
    ("HX050", "equivalised_household_size"),
    ("HX060", "household_type"),
    ("HX080", "poverty_indicator"),
    ("HX090", "equivalised_disposable_income"),
    ("HH050", "ability_keep_home_warm"),
)

EU_SILC_CATALOG: dict[str, EuSilcDataset] = {
    "silc_puf_d_fr": EuSilcDataset(
        dataset_id="silc_puf_d_fr",
        description="EU-SILC synthetic PUF household register (France, 2007-2013)",
        url="https://ec.europa.eu/eurostat/documents/203647/16979414/FR_PUF_EUSILC.zip",
        file_suffix="d",
        columns=_SILC_PUF_D_COLUMNS,
    ),
    "silc_puf_h_fr": EuSilcDataset(
        dataset_id="silc_puf_h_fr",
        description="EU-SILC synthetic PUF household data — income, deprivation, housing (France, 2007-2013)",
        url="https://ec.europa.eu/eurostat/documents/203647/16979414/FR_PUF_EUSILC.zip",
        file_suffix="h",
        columns=_SILC_PUF_H_COLUMNS,
    ),
}

EU_SILC_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(EU_SILC_CATALOG.keys()))
"""Available EU-SILC PUF dataset identifiers for discovery."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================


def _silc_puf_d_fr_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("survey_year", pa.int64()),
            pa.field("country", pa.utf8()),
            pa.field("household_id", pa.int64()),
            pa.field("region", pa.utf8()),
            pa.field("household_weight", pa.float64()),
        ]
    )


def _silc_puf_h_fr_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("survey_year", pa.int64()),
            pa.field("country", pa.utf8()),
            pa.field("household_id", pa.int64()),
            pa.field("total_gross_income", pa.float64()),
            pa.field("total_disposable_income", pa.float64()),
            pa.field("disposable_income_before_social_transfers", pa.float64()),
            pa.field("disposable_income_before_social_transfers_except_pensions", pa.float64()),
            pa.field("change_in_household_income", pa.float64()),
            pa.field("household_size", pa.int64()),
            pa.field("equivalised_household_size", pa.float64()),
            pa.field("household_type", pa.int64()),
            pa.field("poverty_indicator", pa.int64()),
            pa.field("equivalised_disposable_income", pa.float64()),
            pa.field("ability_keep_home_warm", pa.int64()),
        ]
    )


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "silc_puf_d_fr": _silc_puf_d_fr_schema(),
    "silc_puf_h_fr": _silc_puf_h_fr_schema(),
}


# ====================================================================
# EuSilcLoader
# ====================================================================

_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for EU-SILC HTTP downloads (5 minutes)."""


class EuSilcLoader(CachedLoader):
    """Concrete loader for EU-SILC synthetic PUF data sources.

    Extends ``CachedLoader`` with EU-SILC-specific ZIP-wrapped CSV parsing,
    multi-year file extraction, column selection and renaming.

    Each loader instance handles one ``EuSilcDataset``. Use
    ``get_eu_silc_loader`` factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: EuSilcDataset,
        year: int = 2013,
    ) -> None:
        self._dataset = dataset
        self._year = year
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
            provider="eu_silc",
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
            file_format="zip",
        )

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse an EU-SILC PUF dataset from its ZIP archive.

        Downloads the country ZIP, extracts the CSV matching the requested
        file type and year, then parses with PyArrow. Re-raises all network
        errors as ``OSError`` so ``CachedLoader.download()`` can handle
        stale-cache fallback.
        """
        self._logger.debug(
            "event=fetch_start provider=eu_silc dataset_id=%s url=%s year=%d",
            self._dataset.dataset_id,
            config.url,
            self._year,
        )

        try:
            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download eu_silc/{self._dataset.dataset_id} from {config.url}: {exc}"
            ) from exc

        csv_bytes = self._extract_csv_from_zip(raw_bytes)
        table = self._parse_csv(csv_bytes)

        self._logger.debug(
            "event=fetch_complete provider=eu_silc dataset_id=%s rows=%d columns=%d year=%d",
            self._dataset.dataset_id,
            table.num_rows,
            table.num_columns,
            self._year,
        )
        return table

    def _extract_csv_from_zip(self, zip_bytes: bytes) -> bytes:
        """Extract the target CSV from the ZIP archive.

        Looks for a file matching the pattern ``{CC}_{YYYY}{suffix}_EUSILC.csv``
        where CC is the country code derived from the URL, YYYY is the year,
        and suffix is the file type (d, h, r, p).
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                suffix = self._dataset.file_suffix
                target_pattern = f"_{self._year}{suffix}_EUSILC.csv"
                matching = [n for n in zf.namelist() if n.endswith(target_pattern)]
                if not matching:
                    available = [n for n in zf.namelist() if n.endswith(f"{suffix}_EUSILC.csv")]
                    available_years = sorted(n.split("_")[1][:4] for n in available)
                    raise DataSourceValidationError(
                        summary="Year not found in EU-SILC archive",
                        reason=(
                            f"No file matching '*{target_pattern}' in archive. "
                            f"Available years for file type '{suffix}': "
                            f"{', '.join(available_years)}"
                        ),
                        fix=(f"Use one of the available years: {', '.join(available_years)}"),
                    )
                return zf.read(matching[0])
        except zipfile.BadZipFile as exc:
            raise DataSourceValidationError(
                summary="Corrupt ZIP archive",
                reason=(
                    f"Downloaded content for eu_silc/{self._dataset.dataset_id} "
                    f"is not a valid ZIP file: {exc}"
                ),
                fix="Check the Eurostat download URL and try again",
            ) from exc

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


def get_eu_silc_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
    year: int = 2013,
) -> EuSilcLoader:
    """Factory: construct an ``EuSilcLoader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``EU_SILC_AVAILABLE_DATASETS``.
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to
        ``reformlab.population.loaders.eu_silc``.
    year : int
        Survey year to extract from the ZIP archive (2007-2013).

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in EU_SILC_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown EU-SILC dataset",
            reason=(f"Requested dataset '{dataset_id}' is not in the EU-SILC catalog"),
            fix=(f"Available datasets: {', '.join(EU_SILC_AVAILABLE_DATASETS)}"),
        )
    if logger is None:
        logger = logging.getLogger("reformlab.population.loaders.eu_silc")
    return EuSilcLoader(
        cache=cache,
        logger=logger,
        dataset=EU_SILC_CATALOG[dataset_id],
        year=year,
    )


def make_eu_silc_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``EU_SILC_AVAILABLE_DATASETS``.
    **params : str
        Additional parameters used to differentiate cache slots only.
        These are NOT appended to the download URL.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in EU_SILC_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown EU-SILC dataset",
            reason=(f"Requested dataset '{dataset_id}' is not in the EU-SILC catalog"),
            fix=(f"Available datasets: {', '.join(EU_SILC_AVAILABLE_DATASETS)}"),
        )
    ds = EU_SILC_CATALOG[dataset_id]
    return SourceConfig(
        provider="eu_silc",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )
