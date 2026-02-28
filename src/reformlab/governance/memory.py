"""Memory estimation and warning for simulation runs.

Story 7.2: Warn Before Exceeding Memory Limits

This module provides:
- MemoryEstimate: Dataclass with memory usage estimates
- estimate_memory_usage: Heuristic memory estimation
- get_available_memory: System memory detection
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Try to import psutil for system memory detection
try:
    import psutil  # type: ignore[import-untyped]

    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


@dataclass(frozen=True)
class MemoryEstimate:
    """Memory usage estimate for a simulation run.

    Attributes:
        population_size: Number of households in the simulation.
        projection_years: Number of years to project.
        estimated_bytes: Estimated memory required for the simulation.
        available_bytes: Available system memory.
        threshold_bytes: Safe threshold for the target environment.
    """

    population_size: int
    projection_years: int
    estimated_bytes: int
    available_bytes: int
    threshold_bytes: int

    @property
    def exceeds_threshold(self) -> bool:
        """Check if estimated usage exceeds safe threshold."""
        return self.estimated_bytes > min(self.available_bytes, self.threshold_bytes)

    @property
    def estimated_gb(self) -> float:
        """Return estimated memory in gigabytes."""
        return self.estimated_bytes / (1024**3)

    @property
    def available_gb(self) -> float:
        """Return available memory in gigabytes."""
        return self.available_bytes / (1024**3)

    @property
    def threshold_gb(self) -> float:
        """Return threshold memory in gigabytes."""
        return self.threshold_bytes / (1024**3)

    def __repr__(self) -> str:
        """Return notebook-friendly representation showing threshold status."""
        status = "EXCEEDS THRESHOLD" if self.exceeds_threshold else "OK"
        return (
            f"MemoryEstimate({status}, population={self.population_size:,}, "
            f"years={self.projection_years}, est={self.estimated_gb:.1f}GB, "
            f"avail={self.available_gb:.1f}GB)"
        )


def estimate_memory_usage(
    population_size: int,
    projection_years: int,
) -> MemoryEstimate:
    """Estimate memory usage for a simulation run.

    Uses heuristic-based estimation derived from Story 7.1 benchmarks:
    - Base: ~800 bytes per household-year (state arrays, indicators, output buffers)
    - Safety multiplier: 2x (configurable via REFORMLAB_MEMORY_MULTIPLIER)

    Args:
        population_size: Number of households in the simulation.
        projection_years: Number of years to project.

    Returns:
        MemoryEstimate with estimated and available memory.

    Example:
        >>> estimate = estimate_memory_usage(100_000, 10)
        >>> print(estimate.estimated_gb)
        1.5
    """
    # Heuristic from Story 7.1 benchmarks:
    # ~200 bytes for core state arrays (income, carbon_tax, etc.)
    # ~100 bytes for indicator buffers during computation
    # ~500 bytes for PyArrow panel output (including schema overhead)
    # = ~800 bytes per household-year base
    base_bytes_per_household_year = 800

    # Apply configurable safety multiplier (default 2.0)
    multiplier_env = os.environ.get("REFORMLAB_MEMORY_MULTIPLIER")
    if multiplier_env:
        try:
            multiplier = float(multiplier_env)
        except ValueError:
            multiplier = 2.0
    else:
        multiplier = 2.0

    # Calculate estimated memory
    base_bytes = population_size * projection_years * base_bytes_per_household_year
    estimated_bytes = int(base_bytes * multiplier)

    # Get available system memory
    available_bytes = get_available_memory()

    # Calculate safe threshold (75% of 16GB for target machine)
    # This leaves room for OS and other processes
    target_machine_bytes = 16 * (1024**3)  # 16 GB
    threshold_bytes = int(target_machine_bytes * 0.75)  # 12 GB

    return MemoryEstimate(
        population_size=population_size,
        projection_years=projection_years,
        estimated_bytes=estimated_bytes,
        available_bytes=available_bytes,
        threshold_bytes=threshold_bytes,
    )


def get_available_memory() -> int:
    """Get available system memory in bytes.

    Returns:
        Available memory in bytes. Falls back to conservative estimate
        if psutil is not available.

    Example:
        >>> available = get_available_memory()
        >>> print(f"{available / (1024**3):.1f} GB")
        8.0 GB
    """
    if _PSUTIL_AVAILABLE:
        try:
            # Use psutil to get available memory
            virtual_memory = psutil.virtual_memory()
            return int(virtual_memory.available)
        except Exception:
            # Fall back to conservative estimate on error
            pass

    # Conservative fallback: assume 8GB available
    # This is appropriate for laptop/desktop environments
    fallback_bytes = 8 * (1024**3)
    return fallback_bytes
