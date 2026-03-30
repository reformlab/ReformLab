# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

from reformlab.data.assets import (
    CalibrationAsset,
    CalibrationMethod,
    CalibrationTargetType,
    ExogenousAsset,
    HoldoutGroup,
    StructuralAsset,
    ValidationAsset,
    ValidationBenchmarkStatus,
    ValidationMethod,
    ValidationType,
    create_calibration_asset,
    create_exogenous_asset,
    create_structural_asset,
    create_validation_asset,
    load_calibration_asset,
    load_validation_asset,
)
from reformlab.data.comparison import (
    NumericColumnComparison,
    PopulationComparison,
    compare_populations,
)
from reformlab.data.descriptor import (
    DataAssetAccessMode,
    DataAssetClass,
    DataAssetDescriptor,
    DataAssetOrigin,
    DataAssetTrustStatus,
    DatasetDescriptor,
)
from reformlab.data.emission_factors import (
    EmissionFactorIndex,
    build_emission_factor_index,
)
from reformlab.data.errors import EvidenceAssetError
from reformlab.data.exogenous_loader import load_exogenous_asset
from reformlab.data.pipeline import (
    DatasetManifest,
    DatasetRegistry,
    DataSourceMetadata,
    hash_file,
    load_dataset,
    load_population_folder,
)
from reformlab.data.schemas import EMISSION_FACTOR_SCHEMA, SYNTHETIC_POPULATION_SCHEMA
from reformlab.data.synthetic import generate_synthetic_population, save_synthetic_population
from reformlab.data.synthetic_catalog import (
    SyntheticAssetRegistry,
    get_synthetic_registry,
)

__all__ = [
    "EMISSION_FACTOR_SCHEMA",
    "CalibrationAsset",
    "CalibrationMethod",
    "CalibrationTargetType",
    "DataAssetAccessMode",
    "DataAssetClass",
    "DataAssetDescriptor",
    "DataAssetOrigin",
    "DataAssetTrustStatus",
    "DatasetDescriptor",
    "DatasetManifest",
    "DatasetRegistry",
    "DataSourceMetadata",
    "EmissionFactorIndex",
    "EvidenceAssetError",
    "ExogenousAsset",
    "HoldoutGroup",
    "NumericColumnComparison",
    "PopulationComparison",
    "SYNTHETIC_POPULATION_SCHEMA",
    "StructuralAsset",
    "SyntheticAssetRegistry",
    "ValidationAsset",
    "ValidationBenchmarkStatus",
    "ValidationMethod",
    "ValidationType",
    "build_emission_factor_index",
    "compare_populations",
    "create_calibration_asset",
    "create_exogenous_asset",
    "create_structural_asset",
    "create_validation_asset",
    "generate_synthetic_population",
    "get_synthetic_registry",
    "hash_file",
    "load_calibration_asset",
    "load_dataset",
    "load_exogenous_asset",
    "load_population_folder",
    "load_validation_asset",
    "save_synthetic_population",
]
