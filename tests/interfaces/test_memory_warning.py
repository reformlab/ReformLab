"""Integration tests for memory warning flow.

Story 7.2: Warn Before Exceeding Memory Limits

Tests:
- Large population triggers warning via run_scenario()
- Small population does not trigger warning
- skip_memory_check=True suppresses warning
- REFORMLAB_SKIP_MEMORY_WARNING env var suppresses warning
- Warning appears in run manifest warnings field
"""

import warnings
from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.interfaces.api import (
    MemoryCheckResult,
    ScenarioConfig,
    check_memory_requirements,
    run_scenario,
)
from reformlab.interfaces.errors import MemoryWarning


@pytest.fixture
def small_population_config(tmp_path: Path) -> ScenarioConfig:
    """Create a scenario config with small population."""
    # Create a small test population file
    population_path = tmp_path / "small_population.parquet"
    small_table = pa.table(
        {
            "household_id": pa.array(range(1000), type=pa.int64()),
            "income": pa.array([30000.0] * 1000, type=pa.float64()),
        }
    )
    import pyarrow.parquet as pq

    pq.write_table(small_table, population_path)

    return ScenarioConfig(
        template_name="test-scenario",
        parameters={},
        start_year=2025,
        end_year=2030,
        population_path=population_path,
    )


@pytest.fixture
def large_population_config(tmp_path: Path) -> ScenarioConfig:
    """Create a scenario config with large population (600k rows)."""
    # Create a large test population file
    population_path = tmp_path / "large_population.parquet"
    large_table = pa.table(
        {
            "household_id": pa.array(range(600_000), type=pa.int64()),
            "income": pa.array([30000.0] * 600_000, type=pa.float64()),
        }
    )
    import pyarrow.parquet as pq

    pq.write_table(large_table, population_path)

    return ScenarioConfig(
        template_name="test-scenario",
        parameters={},
        start_year=2025,
        end_year=2035,  # 11 years
        population_path=population_path,
    )


def test_check_memory_requirements_small_population(small_population_config):
    """Small population does not trigger warning."""
    result = check_memory_requirements(small_population_config)

    assert isinstance(result, MemoryCheckResult)
    assert not result.should_warn
    assert result.message == ""
    assert result.estimate.population_size == 1000
    assert result.estimate.projection_years == 6


def test_check_memory_requirements_large_population(
    large_population_config, monkeypatch
):
    """Large population on a 16GB machine triggers warning."""
    monkeypatch.setattr(
        "reformlab.governance.memory.get_available_memory",
        lambda: 16 * (1024**3),
    )

    result = check_memory_requirements(large_population_config)

    assert isinstance(result, MemoryCheckResult)
    assert result.should_warn
    assert result.estimate.population_size == 600_000
    assert result.estimate.projection_years == 11
    assert "600,000 households" in result.message
    assert "11 years" in result.message
    assert "GB" in result.message
    assert "reduce projection horizon" in result.message.lower()
    assert "skip_memory_check=True" in result.message


def test_check_memory_requirements_skip_check(large_population_config):
    """skip_check=True suppresses warning."""
    result = check_memory_requirements(large_population_config, skip_check=True)

    assert isinstance(result, MemoryCheckResult)
    assert not result.should_warn
    assert result.message == ""


def test_check_memory_requirements_env_var_skip(large_population_config, monkeypatch):
    """REFORMLAB_SKIP_MEMORY_WARNING env var suppresses warning."""
    monkeypatch.setenv("REFORMLAB_SKIP_MEMORY_WARNING", "true")

    result = check_memory_requirements(large_population_config)

    assert isinstance(result, MemoryCheckResult)
    assert not result.should_warn
    assert result.message == ""


def test_check_memory_requirements_env_var_variations(
    large_population_config, monkeypatch
):
    """Test various env var values that should skip check."""
    for value in ["true", "True", "TRUE", "1", "yes", "YES"]:
        monkeypatch.setenv("REFORMLAB_SKIP_MEMORY_WARNING", value)
        result = check_memory_requirements(large_population_config)
        assert not result.should_warn, f"Failed for value: {value}"


def test_check_memory_requirements_no_population_path():
    """No population path uses default population size."""
    config = ScenarioConfig(
        template_name="test-scenario",
        parameters={},
        start_year=2025,
        end_year=2030,
        population_path=None,
    )

    result = check_memory_requirements(config)

    assert isinstance(result, MemoryCheckResult)
    # Default is 100k households
    assert result.estimate.population_size == 100_000
    assert result.estimate.projection_years == 6


def test_memory_warning_class():
    """MemoryWarning follows canonical format."""
    from reformlab.governance.memory import estimate_memory_usage

    estimate = estimate_memory_usage(population_size=600_000, projection_years=11)

    warning = MemoryWarning(estimate)

    assert isinstance(warning, UserWarning)
    assert hasattr(warning, "estimate")
    assert warning.estimate == estimate

    message = str(warning)
    assert "Memory warning" in message
    assert "600,000 households" in message
    assert "11 years" in message
    assert "GB" in message
    assert "reduce projection horizon" in message.lower()
    assert "skip_memory_check=True" in message
    assert "REFORMLAB_SKIP_MEMORY_WARNING" in message


def test_memory_warning_integration_with_mock_adapter(
    large_population_config, monkeypatch
):
    """Large population triggers MemoryWarning via run_scenario with mock adapter."""
    # Mock available memory to 8GB to ensure warning triggers
    monkeypatch.setattr(
        "reformlab.governance.memory.get_available_memory",
        lambda: 8 * (1024**3),
    )

    adapter = MockAdapter(version_string="test-v1")

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        result = run_scenario(large_population_config, adapter=adapter)
        assert result.success

        # Check that warning was emitted
        memory_warnings = [
            warning for warning in w if issubclass(warning.category, MemoryWarning)
        ]
        assert len(memory_warnings) == 1

        # Check warning content
        warning_message = str(memory_warnings[0].message)
        assert "600,000 households" in warning_message
        assert "11 years" in warning_message


def test_memory_warning_is_captured_in_manifest(
    large_population_config, monkeypatch
):
    """Preflight memory warning is persisted to workflow metadata and manifest."""
    monkeypatch.setattr(
        "reformlab.governance.memory.get_available_memory",
        lambda: 8 * (1024**3),
    )

    result = run_scenario(large_population_config, adapter=MockAdapter())
    assert result.success

    metadata_warnings = result.metadata.get("warnings")
    assert isinstance(metadata_warnings, list)
    assert any(
        "Memory warning — Population of 600,000 households" in w
        for w in metadata_warnings
    )
    assert result.manifest.warnings == metadata_warnings
    assert any(
        "Memory warning — Population of 600,000 households" in w
        for w in result.manifest.warnings
    )


def test_memory_warning_suppression_via_parameter(
    large_population_config, monkeypatch
):
    """skip_memory_check parameter suppresses warning."""
    # Mock available memory to 8GB to ensure warning would trigger
    monkeypatch.setattr(
        "reformlab.governance.memory.get_available_memory",
        lambda: 8 * (1024**3),
    )

    adapter = MockAdapter(version_string="test-v1")

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        result = run_scenario(
            large_population_config,
            adapter=adapter,
            skip_memory_check=True,
        )
        assert result.success

        # No memory warnings should be emitted
        memory_warnings = [
            warning for warning in w if issubclass(warning.category, MemoryWarning)
        ]
        assert len(memory_warnings) == 0


def test_memory_warning_suppression_via_env_var(
    large_population_config, monkeypatch
):
    """REFORMLAB_SKIP_MEMORY_WARNING env var suppresses warning."""
    monkeypatch.setenv("REFORMLAB_SKIP_MEMORY_WARNING", "true")

    # Mock available memory to 8GB to ensure warning would trigger
    monkeypatch.setattr(
        "reformlab.governance.memory.get_available_memory",
        lambda: 8 * (1024**3),
    )

    adapter = MockAdapter(version_string="test-v1")

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        result = run_scenario(large_population_config, adapter=adapter)
        assert result.success

        # No memory warnings should be emitted
        memory_warnings = [
            warning for warning in w if issubclass(warning.category, MemoryWarning)
        ]
        assert len(memory_warnings) == 0


def test_small_population_no_warning(small_population_config):
    """Small population does not trigger warning."""
    adapter = MockAdapter(version_string="test-v1")

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        result = run_scenario(small_population_config, adapter=adapter)
        assert result.success

        # No memory warnings should be emitted for small population
        memory_warnings = [
            warning for warning in w if issubclass(warning.category, MemoryWarning)
        ]
        assert len(memory_warnings) == 0
