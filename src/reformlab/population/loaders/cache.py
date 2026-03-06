"""Disk-based caching infrastructure for data source downloads.

Implements a two-layer cache (Parquet data + JSON metadata) with
hash-based freshness using monthly granularity. Supports offline-first
operation via ``REFORMLAB_OFFLINE`` environment variable.

Cache layout::

    {cache_root}/
        {provider}/
            {dataset_id}/
                {cache_key}.parquet           <- cached data
                {cache_key}.parquet.meta.json  <- metadata

Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from reformlab.governance.hashing import hash_file
from reformlab.population.loaders.base import CacheStatus, SourceConfig

# Default cache root under user home directory
_DEFAULT_CACHE_ROOT = Path.home() / ".reformlab" / "cache" / "sources"


class SourceCache:
    """Disk-based cache for institutional data source downloads.

    Stores schema-validated Parquet files alongside JSON metadata.
    Uses SHA-256 hash-based keys with monthly freshness granularity.

    Parameters
    ----------
    cache_root : Path | None
        Root directory for cache storage. Defaults to
        ``~/.reformlab/cache/sources``. Directories are created
        on first write, not at construction time.
    """

    def __init__(self, cache_root: Path | None = None) -> None:
        self._cache_root = cache_root or _DEFAULT_CACHE_ROOT

    @property
    def cache_root(self) -> Path:
        """Return the cache root directory path."""
        return self._cache_root

    def cache_key(self, config: SourceConfig) -> str:
        """Compute a deterministic cache key from source config + date prefix.

        Uses monthly granularity: data older than the current month
        is considered stale (but still usable as fallback).

        Returns
        -------
        str
            First 16 characters of SHA-256 hex digest.
        """
        date_prefix = datetime.now(UTC).strftime("%Y-%m")
        raw = (
            f"{config.url}"
            f"|{'|'.join(f'{k}={v}' for k, v in sorted(config.params.items()))}"
            f"|{date_prefix}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def cache_path(self, config: SourceConfig) -> Path:
        """Return the Parquet file path for a given config.

        Layout: ``{cache_root}/{provider}/{dataset_id}/{cache_key}.parquet``
        """
        return (
            self._cache_root
            / config.provider
            / config.dataset_id
            / f"{self.cache_key(config)}.parquet"
        )

    def metadata_path(self, config: SourceConfig) -> Path:
        """Return the metadata JSON path for a given config.

        Layout: ``{cache_root}/{provider}/{dataset_id}/{cache_key}.parquet.meta.json``
        """
        return Path(str(self.cache_path(config)) + ".meta.json")

    def get(self, config: SourceConfig) -> tuple[pa.Table, CacheStatus] | None:
        """Retrieve a cached table and its status.

        Looks for a cache entry matching the requested URL + params.
        If the current-month key matches, the cache is fresh.
        If an older matching key is found, the cache is stale but returned.

        Returns
        -------
        tuple[pa.Table, CacheStatus] | None
            Cached table and status if a cache file exists, ``None`` if miss.
        """
        current_path, current_meta = self._fresh_entry_paths(config)
        if current_path.exists() and current_meta.exists():
            table = pq.read_table(current_path)
            status = self._read_metadata(current_meta, current_path, stale=False)
            return table, status

        stale_entry = self._find_stale_entry(config)
        if stale_entry is not None:
            stale_path, stale_meta = stale_entry
            table = pq.read_table(stale_path)
            status = self._read_metadata(stale_meta, stale_path, stale=True)
            return table, status

        return None

    def put(self, config: SourceConfig, table: pa.Table) -> CacheStatus:
        """Write a table to cache with metadata.

        Creates cache directories on first write. Computes SHA-256
        of the written Parquet file for integrity verification.

        Returns
        -------
        CacheStatus
            Status of the newly cached data (always fresh, never stale).
        """
        path = self.cache_path(config)
        meta_path = self.metadata_path(config)

        # Create directories on first write
        path.parent.mkdir(parents=True, exist_ok=True)
        self._prune_matching_entries(config, keep_path=path)

        # Write Parquet
        pq.write_table(table, path)

        # Compute content hash
        content_hash = hash_file(path)

        # Write metadata
        now = datetime.now(UTC)
        date_prefix = now.strftime("%Y-%m")
        metadata = {
            "url": config.url,
            "params": config.params,
            "downloaded_at": now.isoformat(timespec="seconds"),
            "content_hash": content_hash,
            "date_prefix": date_prefix,
            "provider": config.provider,
            "dataset_id": config.dataset_id,
        }
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return CacheStatus(
            cached=True,
            path=path,
            downloaded_at=now,
            hash=content_hash,
            stale=False,
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        """Check cache status without loading the table.

        Returns
        -------
        CacheStatus
            Current cache state for the given config.
        """
        current_path, current_meta = self._fresh_entry_paths(config)
        if current_path.exists() and current_meta.exists():
            return self._read_metadata(current_meta, current_path, stale=False)

        stale_entry = self._find_stale_entry(config)
        if stale_entry is not None:
            stale_path, stale_meta = stale_entry
            return self._read_metadata(stale_meta, stale_path, stale=True)

        return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

    def is_offline(self) -> bool:
        """Check if offline mode is enabled via ``REFORMLAB_OFFLINE`` env var.

        Truthy values: ``"1"``, ``"true"``, ``"yes"`` (case-insensitive).
        """
        value = os.environ.get("REFORMLAB_OFFLINE", "").strip().lower()
        return value in ("1", "true", "yes")

    def _read_metadata(self, meta_path: Path, cache_path: Path, *, stale: bool) -> CacheStatus:
        """Read metadata JSON and build a CacheStatus."""
        raw = self._load_metadata_dict(meta_path) or {}
        downloaded_at = self._parse_downloaded_at(raw)
        content_hash = raw.get("content_hash")
        return CacheStatus(
            cached=True,
            path=cache_path,
            downloaded_at=downloaded_at,
            hash=content_hash if isinstance(content_hash, str) else None,
            stale=stale,
        )

    def _fresh_entry_paths(self, config: SourceConfig) -> tuple[Path, Path]:
        """Compute the expected fresh cache + metadata paths for a config."""
        cache_path = self.cache_path(config)
        return cache_path, Path(str(cache_path) + ".meta.json")

    def _find_stale_entry(self, config: SourceConfig) -> tuple[Path, Path] | None:
        """Find the newest stale entry matching URL and params for a config."""
        dataset_dir = self._cache_root / config.provider / config.dataset_id
        if not dataset_dir.exists():
            return None

        candidates: list[tuple[float, Path, Path]] = []
        for meta_path in dataset_dir.glob("*.parquet.meta.json"):
            cache_path = Path(str(meta_path).removesuffix(".meta.json"))
            if not cache_path.exists():
                continue

            metadata = self._load_metadata_dict(meta_path)
            if metadata is None or not self._metadata_matches_config(metadata, config):
                continue

            downloaded_at = self._parse_downloaded_at(metadata)
            if downloaded_at is not None:
                sort_key = downloaded_at.timestamp()
            else:
                try:
                    sort_key = cache_path.stat().st_mtime
                except OSError:
                    sort_key = 0.0

            candidates.append((sort_key, cache_path, meta_path))

        if not candidates:
            return None

        _sort_key, selected_path, selected_meta = max(candidates, key=lambda item: item[0])
        return selected_path, selected_meta

    def _prune_matching_entries(self, config: SourceConfig, *, keep_path: Path) -> None:
        """Remove older cache entries for the same URL + params."""
        dataset_dir = keep_path.parent
        if not dataset_dir.exists():
            return

        for meta_path in dataset_dir.glob("*.parquet.meta.json"):
            cache_path = Path(str(meta_path).removesuffix(".meta.json"))
            if cache_path == keep_path:
                continue

            metadata = self._load_metadata_dict(meta_path)
            if metadata is None or not self._metadata_matches_config(metadata, config):
                continue

            try:
                cache_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
            except OSError:
                continue

    def _load_metadata_dict(self, meta_path: Path) -> dict[str, object] | None:
        """Best-effort JSON metadata read."""
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _metadata_matches_config(self, metadata: dict[str, object], config: SourceConfig) -> bool:
        """Ensure stale fallback reuses only the same source URL + params."""
        params = metadata.get("params")
        return (
            metadata.get("provider") == config.provider
            and metadata.get("dataset_id") == config.dataset_id
            and metadata.get("url") == config.url
            and isinstance(params, dict)
            and params == config.params
        )

    def _parse_downloaded_at(self, metadata: dict[str, object]) -> datetime | None:
        """Parse metadata timestamp while tolerating legacy/invalid payloads."""
        downloaded_at_str = metadata.get("downloaded_at")
        if not isinstance(downloaded_at_str, str) or not downloaded_at_str:
            return None
        try:
            parsed = datetime.fromisoformat(downloaded_at_str)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
