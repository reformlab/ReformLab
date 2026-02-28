"""Unit tests for memory estimation.

Story 7.2: Warn Before Exceeding Memory Limits

Tests:
- estimate_memory_usage() returns reasonable estimates
- Threshold comparison logic
- Performance: estimation completes in < 100ms for 1M households
- get_available_memory() returns positive integer
"""

import os
import time

import pytest

from reformlab.governance.memory import (
    MemoryEstimate,
    estimate_memory_usage,
    get_available_memory,
)


def test_estimate_memory_usage_small_population():
    """Small populations produce reasonable memory estimates."""
    estimate = estimate_memory_usage(population_size=10_000, projection_years=5)

    assert isinstance(estimate, MemoryEstimate)
    assert estimate.population_size == 10_000
    assert estimate.projection_years == 5
    assert estimate.estimated_bytes > 0
    assert estimate.available_bytes > 0
    assert estimate.threshold_bytes > 0

    # With default 2x multiplier: 10k * 5 * 800 * 2 = 80 MB
    expected_bytes = 10_000 * 5 * 800 * 2
    assert estimate.estimated_bytes == expected_bytes

    # Should not exceed threshold for small population
    assert not estimate.exceeds_threshold


def test_estimate_memory_usage_large_population():
    """Large populations produce appropriate warnings."""
    estimate = estimate_memory_usage(population_size=1_000_000, projection_years=20)

    assert isinstance(estimate, MemoryEstimate)
    assert estimate.population_size == 1_000_000
    assert estimate.projection_years == 20

    # With default 2x multiplier: 1M * 20 * 800 * 2 = 32 GB
    expected_bytes = 1_000_000 * 20 * 800 * 2
    assert estimate.estimated_bytes == expected_bytes

    # Large population should exceed 12GB threshold
    assert estimate.exceeds_threshold


def test_estimate_memory_usage_threshold_boundary():
    """Test behavior at threshold boundary."""
    # Calculate population size that produces ~12GB estimate
    # 12 GB = population * years * 800 * 2
    # population = 12 * 1024^3 / (years * 800 * 2)
    threshold_gb = 12
    threshold_bytes = threshold_gb * (1024**3)
    years = 10
    base_bytes_per_household_year = 800
    multiplier = 2.0

    population_at_threshold = int(
        threshold_bytes / (years * base_bytes_per_household_year * multiplier)
    )

    # Just below threshold
    estimate_below = estimate_memory_usage(
        population_size=population_at_threshold - 10_000,
        projection_years=years,
    )
    # Might not exceed if available memory is high
    # Just test that estimate is calculated correctly

    # Just above threshold
    estimate_above = estimate_memory_usage(
        population_size=population_at_threshold + 10_000,
        projection_years=years,
    )
    assert estimate_above.estimated_bytes > estimate_below.estimated_bytes


def test_memory_estimate_properties():
    """Test MemoryEstimate property calculations."""
    estimate = estimate_memory_usage(population_size=100_000, projection_years=10)

    # Test GB conversions
    assert estimate.estimated_gb == estimate.estimated_bytes / (1024**3)
    assert estimate.available_gb == estimate.available_bytes / (1024**3)
    assert estimate.threshold_gb == estimate.threshold_bytes / (1024**3)

    # Test exceeds_threshold property
    exceeds = estimate.estimated_bytes > min(
        estimate.available_bytes, estimate.threshold_bytes
    )
    assert estimate.exceeds_threshold == exceeds


def test_memory_estimate_repr():
    """Test MemoryEstimate string representation."""
    estimate = estimate_memory_usage(population_size=100_000, projection_years=10)

    repr_str = repr(estimate)
    assert "MemoryEstimate" in repr_str
    assert "population=100,000" in repr_str
    assert "years=10" in repr_str
    assert "GB" in repr_str

    # Status should be either OK or EXCEEDS THRESHOLD
    assert "OK" in repr_str or "EXCEEDS THRESHOLD" in repr_str


def test_memory_estimation_performance():
    """Memory estimation completes in under 100ms for large populations."""
    start = time.perf_counter()
    estimate = estimate_memory_usage(population_size=1_000_000, projection_years=20)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1, f"Memory estimation took {elapsed:.3f}s, expected < 0.1s"
    assert estimate.population_size == 1_000_000
    assert estimate.projection_years == 20


def test_get_available_memory():
    """get_available_memory() returns positive integer."""
    available = get_available_memory()

    assert isinstance(available, int)
    assert available > 0

    # Should be at least 1 GB (conservative)
    assert available >= 1 * (1024**3)


def test_estimate_memory_usage_with_custom_multiplier(monkeypatch):
    """Custom multiplier via environment variable."""
    monkeypatch.setenv("REFORMLAB_MEMORY_MULTIPLIER", "3.0")

    estimate = estimate_memory_usage(population_size=10_000, projection_years=5)

    # With custom 3x multiplier: 10k * 5 * 800 * 3 = 120 MB
    expected_bytes = 10_000 * 5 * 800 * 3
    assert estimate.estimated_bytes == expected_bytes


def test_estimate_memory_usage_invalid_multiplier(monkeypatch):
    """Invalid multiplier falls back to default."""
    monkeypatch.setenv("REFORMLAB_MEMORY_MULTIPLIER", "invalid")

    estimate = estimate_memory_usage(population_size=10_000, projection_years=5)

    # Should fall back to default 2x multiplier
    expected_bytes = 10_000 * 5 * 800 * 2
    assert estimate.estimated_bytes == expected_bytes


def test_memory_estimate_frozen():
    """MemoryEstimate is immutable (frozen dataclass)."""
    estimate = estimate_memory_usage(population_size=10_000, projection_years=5)

    with pytest.raises(AttributeError):
        estimate.population_size = 20_000  # type: ignore


def test_estimate_memory_usage_zero_population():
    """Zero population produces zero estimate."""
    estimate = estimate_memory_usage(population_size=0, projection_years=5)

    assert estimate.population_size == 0
    assert estimate.estimated_bytes == 0
    assert not estimate.exceeds_threshold


def test_estimate_memory_usage_zero_years():
    """Zero years produces zero estimate."""
    estimate = estimate_memory_usage(population_size=10_000, projection_years=0)

    assert estimate.projection_years == 0
    assert estimate.estimated_bytes == 0
    assert not estimate.exceeds_threshold


def test_threshold_calculation():
    """Threshold is set to 75% of 16GB."""
    estimate = estimate_memory_usage(population_size=10_000, projection_years=5)

    expected_threshold = int(16 * (1024**3) * 0.75)  # 12 GB
    assert estimate.threshold_bytes == expected_threshold
    assert estimate.threshold_gb == 12.0
