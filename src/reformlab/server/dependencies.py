# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Dependency injection for FastAPI route handlers.

Provides global singletons for the result cache, result store, and computation adapter.
"""

from __future__ import annotations

import logging
import os
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.interfaces.api import SimulationResult
    from reformlab.server.population_resolver import PopulationResolver
    from reformlab.server.result_store import ResultStore
    from reformlab.templates.registry import ScenarioRegistry

logger = logging.getLogger(__name__)


class ResultCache:
    """In-memory LRU cache for SimulationResult objects."""

    def __init__(self, max_size: int = 10) -> None:
        self._cache: OrderedDict[str, SimulationResult] = OrderedDict()
        self._max_size = max_size

    def store(self, run_id: str, result: SimulationResult) -> None:
        if run_id not in self._cache and len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)  # Evict oldest
        self._cache[run_id] = result

    def get(self, run_id: str) -> SimulationResult | None:
        result = self._cache.get(run_id)
        if result is not None:
            self._cache.move_to_end(run_id)  # Mark as recently used
        return result

    def delete(self, run_id: str) -> None:
        """Remove a result from the cache if present."""
        self._cache.pop(run_id, None)

    def get_or_load(
        self, run_id: str, store: ResultStore
    ) -> SimulationResult | None:
        """Return cached result or load from disk on cache miss.

        Checks cache first. On miss, calls store.load_from_disk(), stores the
        result in cache, and returns it. Returns None only if neither cache
        nor disk has data.

        Args:
            run_id: Unique run identifier.
            store: ResultStore to load from on cache miss.

        Returns:
            SimulationResult if available, None otherwise.
        """
        result = self.get(run_id)
        if result is not None:
            return result
        disk_result = store.load_from_disk(run_id)
        if disk_result is not None:
            logger.info("event=cache_miss_disk_load run_id=%s", run_id)
            self.store(run_id, disk_result)
        else:
            logger.debug("event=disk_load_miss run_id=%s", run_id)
        return disk_result


# Global singletons
_result_cache = ResultCache(max_size=10)
_adapter: ComputationAdapter | None = None
_result_store: ResultStore | None = None
_registry: ScenarioRegistry | None = None
_population_resolver: PopulationResolver | None = None


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


def get_registry() -> ScenarioRegistry:
    """Return the global scenario registry (lazy-initialized)."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        from reformlab.templates.registry import ScenarioRegistry

        _registry = ScenarioRegistry()
    return _registry


def get_population_resolver() -> PopulationResolver:
    """Return the global population resolver (lazy-initialized).

    Reads directory paths from environment variables:
    - ``REFORMLAB_DATA_DIR`` (default: ``data``) — bundled populations
    - ``REFORMLAB_UPLOADED_POPULATIONS_DIR`` (default: ``~/.reformlab/uploaded-populations``)
    """
    global _population_resolver  # noqa: PLW0603
    if _population_resolver is None:
        from reformlab.server.population_resolver import PopulationResolver

        data_dir = Path(os.environ.get("REFORMLAB_DATA_DIR", "data")) / "populations"
        uploaded_dir = Path(
            os.environ.get(
                "REFORMLAB_UPLOADED_POPULATIONS_DIR",
                "~/.reformlab/uploaded-populations",
            )
        ).expanduser()
        _population_resolver = PopulationResolver(data_dir, uploaded_dir)
    return _population_resolver


def get_adapter() -> ComputationAdapter:
    """Return the global computation adapter (lazy-initialized)."""
    global _adapter  # noqa: PLW0603
    if _adapter is None:
        _adapter = _create_adapter()
    return _adapter


def _create_adapter() -> ComputationAdapter:
    """Create the default computation adapter based on REFORMLAB_RUNTIME_MODE.

    Story 23.4: Defaults to live OpenFiscaApiAdapter, supports replay mode
    via REFORMLAB_RUNTIME_MODE env var, falls back to MockAdapter for dev.
    """
    runtime_mode = os.environ.get("REFORMLAB_RUNTIME_MODE", "live")
    if runtime_mode not in ("live", "replay"):
        logger.warning("Invalid REFORMLAB_RUNTIME_MODE=%s, defaulting to 'live'", runtime_mode)
        runtime_mode = "live"

    if runtime_mode == "replay":
        try:
            logger.info("Using replay adapter (REFORMLAB_RUNTIME_MODE=replay)")
            return _create_replay_adapter()
        except (FileNotFoundError, OSError):
            from reformlab.computation.mock_adapter import MockAdapter

            logger.warning("Replay adapter failed (precomputed data not found), using MockAdapter")
            return MockAdapter()
        except Exception:
            from reformlab.computation.mock_adapter import MockAdapter

            logger.warning("Replay adapter failed, using MockAdapter")
            return MockAdapter()

    # Default: live mode
    try:
        adapter = _create_live_adapter()
        logger.info("Using live OpenFiscaApiAdapter (default)")
        return adapter
    except ImportError:
        from reformlab.computation.mock_adapter import MockAdapter

        logger.info("OpenFisca not installed — using MockAdapter (dev mode)")
        return MockAdapter()
    except (OSError, RuntimeError) as exc:
        from reformlab.computation.mock_adapter import MockAdapter

        logger.warning("Live adapter init failed (%s) — using MockAdapter", exc)
        return MockAdapter()


def _create_live_adapter() -> ComputationAdapter:
    """Create the live OpenFiscaApiAdapter for default web execution.

    Story 23.4: Live adapter uses OpenFiscaApiAdapter with default
    output variables matching the normalizer's mapping.
    """
    from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
    from reformlab.computation.result_normalizer import _DEFAULT_LIVE_OUTPUT_VARIABLES

    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=_DEFAULT_LIVE_OUTPUT_VARIABLES,
    )


def _create_replay_adapter() -> ComputationAdapter:
    """Create the precomputed OpenFiscaAdapter for explicit replay mode.

    Story 23.4: Replay adapter reads precomputed CSV/Parquet files.
    Raises FileNotFoundError eagerly when data_dir is missing or empty.
    """
    from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

    data_dir = _resolve_adapter_data_dir()
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Replay data directory does not exist: {data_dir}")
    if not any(data_dir.glob("*.csv")) and not any(data_dir.glob("*.parquet")):
        raise FileNotFoundError(f"No precomputed data files (CSV/Parquet) in {data_dir}")
    return OpenFiscaAdapter(data_dir)


def _resolve_adapter_data_dir() -> Path:
    """Resolve the server-side OpenFisca data directory.

    Precedence:
    1. ``REFORMLAB_OPENFISCA_DATA_DIR`` when explicitly provided.
    2. ``<REFORMLAB_DATA_DIR>/openfisca`` when that subdirectory exists.
    3. ``REFORMLAB_DATA_DIR`` (or ``data`` by default) for backward compatibility.
    """
    explicit_dir = os.environ.get("REFORMLAB_OPENFISCA_DATA_DIR")
    if explicit_dir:
        return Path(explicit_dir)

    base_dir = Path(os.environ.get("REFORMLAB_DATA_DIR", "data"))
    nested_dir = base_dir / "openfisca"
    if nested_dir.is_dir():
        return nested_dir

    return base_dir
