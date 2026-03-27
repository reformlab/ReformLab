# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

from reformlab.data.assets import (
    CalibrationAsset,
    CalibrationTargetType,
    ExogenousAsset,
    StructuralAsset,
    ValidationAsset,
    ValidationBenchmarkStatus,
    ValidationType,
    create_calibration_asset,
    create_exogenous_asset,
    create_structural_asset,
    create_validation_asset,
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

__all__ = [
    "EMISSION_FACTOR_SCHEMA",
    "CalibrationAsset",
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
    "SYNTHETIC_POPULATION_SCHEMA",
    "StructuralAsset",
    "ValidationAsset",
    "ValidationBenchmarkStatus",
    "ValidationType",
    "build_emission_factor_index",
    "create_calibration_asset",
    "create_exogenous_asset",
    "create_structural_asset",
    "create_validation_asset",
    "generate_synthetic_population",
    "hash_file",
    "load_dataset",
    "load_population_folder",
    "save_synthetic_population",
]
