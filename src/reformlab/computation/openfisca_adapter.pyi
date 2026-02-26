from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

SUPPORTED_VERSIONS: list[str]
MIN_SUPPORTED: str
COMPAT_MATRIX_URL: str


def _detect_openfisca_version() -> str: ...


def _check_version(actual: str) -> None: ...


class OpenFiscaAdapter:
    def __init__(
        self,
        data_dir: str | Path,
        *,
        skip_version_check: bool = False,
    ) -> None: ...

    def version(self) -> str: ...

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult: ...

    def _load_period_file(self, period: int) -> pa.Table: ...
