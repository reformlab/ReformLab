from __future__ import annotations

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.exceptions import CompatibilityError
from reformlab.computation.ingestion import (
    DEFAULT_OPENFISCA_OUTPUT_SCHEMA,
    DataSchema,
    IngestionError,
    IngestionResult,
    TypeMismatch,
    ingest,
    ingest_csv,
    ingest_parquet,
)
from reformlab.computation.mapping import (
    FieldMapping,
    MappingConfig,
    MappingError,
    MappingValidationResult,
    apply_input_mapping,
    apply_output_mapping,
    load_mapping,
    load_mappings,
    merge_mappings,
    validate_mapping,
)
from reformlab.computation.quality import (
    DataQualityError,
    QualityCheckResult,
    QualityIssue,
    RangeRule,
    validate_output,
)
from reformlab.computation.types import (
    ComputationResult,
    OutputFields,
    PolicyConfig,
    PopulationData,
)

__all__ = [
    "ComputationAdapter",
    "ComputationResult",
    "CompatibilityError",
    "DEFAULT_OPENFISCA_OUTPUT_SCHEMA",
    "DataQualityError",
    "DataSchema",
    "FieldMapping",
    "IngestionError",
    "IngestionResult",
    "MappingConfig",
    "MappingError",
    "MappingValidationResult",
    "OutputFields",
    "PolicyConfig",
    "PopulationData",
    "QualityCheckResult",
    "QualityIssue",
    "RangeRule",
    "TypeMismatch",
    "apply_input_mapping",
    "apply_output_mapping",
    "ingest",
    "ingest_csv",
    "ingest_parquet",
    "load_mapping",
    "load_mappings",
    "merge_mappings",
    "validate_mapping",
    "validate_output",
]
