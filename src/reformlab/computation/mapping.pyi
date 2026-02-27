from pathlib import Path
from typing import Literal

import pyarrow as pa

class FieldMapping:
    openfisca_name: str
    project_name: str
    direction: Literal["input", "output", "both"]
    pa_type: pa.DataType
    description: str
    def __init__(
        self,
        openfisca_name: str,
        project_name: str,
        direction: Literal["input", "output", "both"],
        pa_type: pa.DataType,
        description: str = "",
    ) -> None: ...

class MappingConfig:
    mappings: tuple[FieldMapping, ...]
    source_path: Path | None
    def __init__(
        self,
        mappings: tuple[FieldMapping, ...],
        source_path: Path | None = None,
    ) -> None: ...
    def by_openfisca_name(self, name: str) -> FieldMapping | None: ...
    def by_project_name(self, name: str) -> FieldMapping | None: ...
    @property
    def input_mappings(self) -> tuple[FieldMapping, ...]: ...
    @property
    def output_mappings(self) -> tuple[FieldMapping, ...]: ...

class MappingError(Exception):
    file_path: Path
    invalid_fields: tuple[str, ...]
    def __init__(
        self,
        *,
        file_path: Path,
        summary: str,
        reason: str,
        fix: str,
        invalid_fields: tuple[str, ...] = (),
    ) -> None: ...

class MappingValidationResult:
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    def __init__(
        self,
        warnings: tuple[str, ...],
        errors: tuple[str, ...],
    ) -> None: ...

def load_mapping(path: str | Path) -> MappingConfig: ...
def apply_output_mapping(table: pa.Table, config: MappingConfig) -> pa.Table: ...
def apply_input_mapping(table: pa.Table, config: MappingConfig) -> pa.Table: ...
def validate_mapping(
    config: MappingConfig,
    available_columns: tuple[str, ...],
) -> MappingValidationResult: ...
def merge_mappings(*configs: MappingConfig) -> MappingConfig: ...
def load_mappings(*paths: str | Path) -> MappingConfig: ...
