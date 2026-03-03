"""Institutional data source loaders with disk-based caching.

Provides the ``DataSourceLoader`` protocol, ``SourceCache`` for
offline-first caching, and ``CachedLoader`` base class for building
concrete loaders (INSEE, Eurostat, ADEME, SDES).

Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).
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

__all__ = [
    "CachedLoader",
    "CacheStatus",
    "DataSourceDownloadError",
    "DataSourceError",
    "DataSourceLoader",
    "DataSourceOfflineError",
    "DataSourceValidationError",
    "SourceCache",
    "SourceConfig",
]
