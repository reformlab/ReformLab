from __future__ import annotations

import time
from pathlib import Path

import pyarrow as pa

from reformlab.computation.exceptions import CompatibilityError
from reformlab.computation.ingestion import DEFAULT_OPENFISCA_OUTPUT_SCHEMA, ingest
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

SUPPORTED_VERSIONS: list[str] = [
    "44.0.0",
    "44.0.1",
    "44.1.0",
    "44.2.0",
    "44.2.1",
    "44.2.2",
]

MIN_SUPPORTED = "44.0.0"
COMPAT_MATRIX_URL = (
    "https://github.com/openfisca/openfisca-core/blob/master/CHANGELOG.md"
)


def _detect_openfisca_version() -> str:
    """Detect the installed OpenFisca-Core version via importlib.metadata."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("openfisca-core")
    except PackageNotFoundError:
        return "not-installed"


def _check_version(actual: str) -> None:
    """Raise CompatibilityError if *actual* is not in the supported set."""
    expected_versions = ", ".join(SUPPORTED_VERSIONS)

    if actual == "not-installed":
        raise CompatibilityError(
            expected=expected_versions,
            actual=actual,
            details=(
                "openfisca-core is not installed. "
                "Install it with: uv add 'openfisca-core>=44.0.0'. "
                f"See {COMPAT_MATRIX_URL}"
            ),
        )

    if actual not in SUPPORTED_VERSIONS:
        raise CompatibilityError(
            expected=expected_versions,
            actual=actual,
            details=(
                f"Unsupported version. Supported versions: {expected_versions}. "
                f"See {COMPAT_MATRIX_URL}"
            ),
        )


class OpenFiscaAdapter:
    """Adapter that reads pre-computed OpenFisca outputs from CSV/Parquet files.

    Phase 1 primary mode: the adapter does **not** execute OpenFisca live.
    Instead it reads pre-computed result files and maps them into
    ``ComputationResult`` objects.

    Version validation happens at construction time - if the installed
    OpenFisca-Core version is unsupported, ``CompatibilityError`` is raised
    immediately.
    """

    def __init__(
        self,
        data_dir: str | Path,
        *,
        skip_version_check: bool = False,
    ) -> None:
        self._data_dir = Path(data_dir)
        if not skip_version_check:
            self._version = _detect_openfisca_version()
            _check_version(self._version)
        else:
            self._version = "unknown"

    def version(self) -> str:
        """Return the detected OpenFisca-Core version string."""
        return self._version

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Read pre-computed outputs for the given period.

        Looks for files named ``<period>.csv`` or ``<period>.parquet``
        inside ``data_dir``. CSV is tried first; if not found, Parquet
        is tried.

        The population and policy arguments are recorded in metadata but
        are **not** used to drive a live computation - that is Story 1-6.
        """
        start = time.monotonic()
        table = self._load_period_file(period)
        elapsed = time.monotonic() - start

        return ComputationResult(
            output_fields=table,
            adapter_version=self._version,
            period=period,
            metadata={
                "timing_seconds": round(elapsed, 4),
                "row_count": table.num_rows,
                "source": "pre-computed",
                "policy_name": policy.name,
            },
        )

    def _load_period_file(self, period: int) -> pa.Table:
        """Load a CSV or Parquet file for *period* from the data directory."""
        csv_path = self._data_dir / f"{period}.csv"
        parquet_path = self._data_dir / f"{period}.parquet"

        if csv_path.exists():
            return ingest(csv_path, DEFAULT_OPENFISCA_OUTPUT_SCHEMA).table
        if parquet_path.exists():
            return ingest(parquet_path, DEFAULT_OPENFISCA_OUTPUT_SCHEMA).table

        raise FileNotFoundError(
            f"No pre-computed output file found for period {period}. "
            f"Expected {csv_path} or {parquet_path}."
        )
