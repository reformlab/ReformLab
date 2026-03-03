"""Institutional data source loaders with disk-based caching.

Provides the ``DataSourceLoader`` protocol, ``SourceCache`` for
offline-first caching, and ``CachedLoader`` base class for building
concrete loaders (INSEE, Eurostat, ADEME, SDES).

Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).
Implements Story 11.2 (INSEE data source loader).
"""

from __future__ import annotations

from reformlab.population.loaders.base import (
    CachedLoader,
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceError,
    DataSourceOfflineError,
    DataSourceValidationError,
)
from reformlab.population.loaders.insee import (
    AVAILABLE_DATASETS,
    INSEEDataset,
    INSEELoader,
    get_insee_loader,
    make_insee_config,
)

__all__ = [
    "AVAILABLE_DATASETS",
    "CachedLoader",
    "CacheStatus",
    "DataSourceDownloadError",
    "DataSourceError",
    "DataSourceLoader",
    "DataSourceOfflineError",
    "DataSourceValidationError",
    "INSEEDataset",
    "INSEELoader",
    "SourceCache",
    "SourceConfig",
    "get_insee_loader",
    "make_insee_config",
]
