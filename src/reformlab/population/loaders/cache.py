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

from reformlab.population.loaders.base import CacheStatus, SourceConfig

# Default cache root under user home directory
_DEFAULT_CACHE_ROOT = Path.home() / ".reformlab" / "cache" / "sources"

# 64KB chunks for memory-efficient hashing (matches governance/hashing.py)
_CHUNK_SIZE = 65536


def _hash_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file using streaming reads."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()


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

        Looks for any cached Parquet file for this provider/dataset_id.
        If the current-month key matches, the cache is fresh.
        If a different key is found, the cache is stale but returned.

        Returns
        -------
        tuple[pa.Table, CacheStatus] | None
            Cached table and status if a cache file exists, ``None`` if miss.
        """
        current_key = self.cache_key(config)
        dataset_dir = self._cache_root / config.provider / config.dataset_id

        if not dataset_dir.exists():
            return None

        # Check for current (fresh) cache first
        current_path = dataset_dir / f"{current_key}.parquet"
        current_meta = Path(str(current_path) + ".meta.json")

        if current_path.exists() and current_meta.exists():
            table = pq.read_table(current_path)
            status = self._read_metadata(current_meta, current_path, stale=False)
            return table, status

        # Check for any stale cache
        parquet_files = sorted(dataset_dir.glob("*.parquet"))
        for pf in parquet_files:
            meta_file = Path(str(pf) + ".meta.json")
            if meta_file.exists():
                table = pq.read_table(pf)
                status = self._read_metadata(meta_file, pf, stale=True)
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

        # Write Parquet
        pq.write_table(table, path)

        # Compute content hash
        content_hash = _hash_file(path)

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
        current_key = self.cache_key(config)
        dataset_dir = self._cache_root / config.provider / config.dataset_id

        if not dataset_dir.exists():
            return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

        # Check fresh cache
        current_path = dataset_dir / f"{current_key}.parquet"
        current_meta = Path(str(current_path) + ".meta.json")

        if current_path.exists() and current_meta.exists():
            return self._read_metadata(current_meta, current_path, stale=False)

        # Check stale cache
        parquet_files = sorted(dataset_dir.glob("*.parquet"))
        for pf in parquet_files:
            meta_file = Path(str(pf) + ".meta.json")
            if meta_file.exists():
                return self._read_metadata(meta_file, pf, stale=True)

        return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

    def is_offline(self) -> bool:
        """Check if offline mode is enabled via ``REFORMLAB_OFFLINE`` env var.

        Truthy values: ``"1"``, ``"true"``, ``"yes"`` (case-insensitive).
        """
        value = os.environ.get("REFORMLAB_OFFLINE", "").strip().lower()
        return value in ("1", "true", "yes")

    def _read_metadata(self, meta_path: Path, cache_path: Path, *, stale: bool) -> CacheStatus:
        """Read metadata JSON and build a CacheStatus."""
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        downloaded_at_str = raw.get("downloaded_at")
        downloaded_at = (
            datetime.fromisoformat(downloaded_at_str) if downloaded_at_str else None
        )
        return CacheStatus(
            cached=True,
            path=cache_path,
            downloaded_at=downloaded_at,
            hash=raw.get("content_hash"),
            stale=stale,
        )
