# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

from reformlab.data.descriptor import DatasetDescriptor
from reformlab.data.emission_factors import (
    EmissionFactorIndex,
    build_emission_factor_index,
)
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
    "DatasetDescriptor",
    "DatasetManifest",
    "DatasetRegistry",
    "DataSourceMetadata",
    "EmissionFactorIndex",
    "SYNTHETIC_POPULATION_SCHEMA",
    "build_emission_factor_index",
    "generate_synthetic_population",
    "hash_file",
    "load_dataset",
    "load_population_folder",
    "save_synthetic_population",
]
