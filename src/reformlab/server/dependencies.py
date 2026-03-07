"""Dependency injection for FastAPI route handlers.

Provides global singletons for the result cache, result store, and computation adapter.
"""

from __future__ import annotations

import logging
import os
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.interfaces.api import SimulationResult
    from reformlab.server.result_store import ResultStore

logger = logging.getLogger(__name__)


class ResultCache:
    """In-memory LRU cache for SimulationResult objects."""

    def __init__(self, max_size: int = 10) -> None:
        self._cache: OrderedDict[str, SimulationResult] = OrderedDict()
        self._max_size = max_size

    def store(self, run_id: str, result: SimulationResult) -> None:
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)  # Evict oldest
        self._cache[run_id] = result

    def get(self, run_id: str) -> SimulationResult | None:
        result = self._cache.get(run_id)
        if result is not None:
            self._cache.move_to_end(run_id)  # Mark as recently used
        return result


# Global singletons
_result_cache = ResultCache(max_size=10)
_adapter: ComputationAdapter | None = None
_result_store: ResultStore | None = None


def get_result_cache() -> ResultCache:
    """Return the global result cache."""
    return _result_cache


def get_result_store() -> ResultStore:
    """Return the global result store (lazy-initialized)."""
    global _result_store  # noqa: PLW0603
    if _result_store is None:
        from reformlab.server.result_store import ResultStore

        _result_store = ResultStore()
    return _result_store


def get_adapter() -> ComputationAdapter:
    """Return the global computation adapter (lazy-initialized)."""
    global _adapter  # noqa: PLW0603
    if _adapter is None:
        _adapter = _create_adapter()
    return _adapter


def _create_adapter() -> ComputationAdapter:
    """Create the default computation adapter.

    Uses MockAdapter in dev if OpenFisca is not available,
    otherwise uses OpenFiscaAdapter.
    """
    try:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        data_dir = os.environ.get("REFORMLAB_DATA_DIR", "data")
        logger.info("Using OpenFiscaAdapter, data_dir=%s", data_dir)
        return OpenFiscaAdapter(data_dir)
    except ImportError:
        from reformlab.computation.mock_adapter import MockAdapter

        logger.info("OpenFisca not available — using MockAdapter")
        return MockAdapter()
