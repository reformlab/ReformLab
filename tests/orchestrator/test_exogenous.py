# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for ExogenousContext - Story 21.6, AC1."""

from __future__ import annotations

import pytest

from reformlab.data.assets import ExogenousAsset
from reformlab.data.descriptor import (
    DataAssetDescriptor,
)
from reformlab.data.errors import EvidenceAssetError
from reformlab.orchestrator.errors import OrchestratorError

# Story 21.6 / AC1: Create ExogenousContext frozen dataclass
# Tests will be enabled once ExogenousContext is implemented


def _create_test_descriptor(asset_id: str, name: str) -> DataAssetDescriptor:
    """Helper to create test DataAssetDescriptor instances."""
    return DataAssetDescriptor(
        asset_id=asset_id,
        name=name,
        description=f"Test asset {name}",
        data_class="exogenous",
        origin="open-official",
        access_mode="bundled",
        trust_status="exploratory",
        source_url="",
        license="",
        version="2024",
        geographic_coverage=(),
        years=(),
        intended_use="testing",
        redistribution_allowed=True,
        redistribution_notes="",
        update_cadence="",
        quality_notes="",
        references=(),
    )


class TestExogenousContextCreation:
    """Test ExogenousContext creation and factory methods."""

    def test_from_assets_creates_context_with_single_asset(self):
        """from_assets() should create context with one ExogenousAsset."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset-1", "Test Asset 1")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="energy_price_electricity",
            values={2020: 0.185, 2025: 0.195, 2030: 0.205},
            unit="EUR/kWh",
        )

        # Act - Will fail until ExogenousContext exists
        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Assert
        assert context.series_names == ("energy_price_electricity",)
        assert context.get_asset("energy_price_electricity") is asset

    def test_from_assets_creates_context_with_multiple_assets(self):
        """from_assets() should create context with multiple ExogenousAssets."""
        # Arrange
        descriptor1 = _create_test_descriptor("test-asset-1", "Test Asset 1")
        asset1 = ExogenousAsset(
            descriptor=descriptor1,
            name="energy_price_electricity",
            values={2020: 0.185, 2025: 0.195},
            unit="EUR/kWh",
        )

        descriptor2 = _create_test_descriptor("test-asset-2", "Test Asset 2")
        asset2 = ExogenousAsset(
            descriptor=descriptor2,
            name="energy_price_petrol",
            values={2020: 1.45, 2025: 1.55},
            unit="EUR/litre",
        )

        # Act
        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset1, asset2))

        # Assert
        assert set(context.series_names) == {
            "energy_price_electricity",
            "energy_price_petrol",
        }
        assert context.get_asset("energy_price_electricity") is asset1
        assert context.get_asset("energy_price_petrol") is asset2

    def test_from_assets_rejects_duplicate_series_names(self):
        """from_assets() should raise ValueError for duplicate series names."""
        # Arrange
        descriptor1 = _create_test_descriptor("test-asset-1", "Test Asset 1")
        asset1 = ExogenousAsset(
            descriptor=descriptor1,
            name="energy_price_electricity",
            values={2020: 0.185},
            unit="EUR/kWh",
        )

        descriptor2 = _create_test_descriptor("test-asset-2", "Test Asset 2")
        asset2 = ExogenousAsset(
            descriptor=descriptor2,
            name="energy_price_electricity",  # Duplicate!
            values={2020: 0.195},
            unit="EUR/kWh",
        )

        # Act & Assert
        from reformlab.orchestrator.exogenous import ExogenousContext

        with pytest.raises(ValueError, match="Duplicate series name"):
            ExogenousContext.from_assets((asset1, asset2))


class TestExogenousContextLookup:
    """Test ExogenousContext.get_value() with interpolation."""

    def test_get_value_returns_exact_year_value(self):
        """get_value() should return exact value when year exists."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_series",
            values={2020: 100.0, 2025: 150.0, 2030: 200.0},
            unit="EUR",
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Act & Assert
        assert context.get_value("test_series", 2020) == 100.0
        assert context.get_value("test_series", 2025) == 150.0
        assert context.get_value("test_series", 2030) == 200.0

    def test_get_value_with_linear_interpolation(self):
        """get_value() should interpolate linearly between years."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_series",
            values={2020: 100.0, 2030: 200.0},
            unit="EUR",
            interpolation_method="linear",
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Act & Assert
        # Midpoint should be 150.0
        assert context.get_value("test_series", 2025) == 150.0

    def test_get_value_with_step_interpolation(self):
        """get_value() should use step interpolation (previous year)."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_series",
            values={2020: 100.0, 2030: 200.0},
            unit="EUR",
            interpolation_method="step",
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Act & Assert
        # Should use 2020 value until 2030
        assert context.get_value("test_series", 2025) == 100.0
        assert context.get_value("test_series", 2029) == 100.0
        assert context.get_value("test_series", 2030) == 200.0

    def test_get_value_raises_keyerror_for_unknown_series(self):
        """get_value() should raise KeyError for unknown series name."""
        # Arrange
        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets(())

        # Act & Assert
        with pytest.raises(KeyError, match="unknown_series"):
            context.get_value("unknown_series", 2025)

    def test_get_value_propagates_asset_errors(self):
        """get_value() should propagate EvidenceAssetError from asset."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_series",
            values={2020: 100.0},
            unit="EUR",
            interpolation_method="none",  # No interpolation
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Act & Assert - Year 2025 not in values
        with pytest.raises(EvidenceAssetError, match="no data for year 2025"):
            context.get_value("test_series", 2025)


class TestExogenousContextCoverage:
    """Test ExogenousContext.validate_coverage()."""

    def test_validate_coverage_passes_with_complete_data(self):
        """validate_coverage() should pass when all series have coverage."""
        # Arrange
        descriptor1 = _create_test_descriptor("test-asset-1", "Test Asset 1")
        asset1 = ExogenousAsset(
            descriptor=descriptor1,
            name="series1",
            values={2020: 100.0, 2021: 110.0, 2022: 120.0, 2023: 130.0,
                    2024: 140.0, 2025: 150.0, 2026: 160.0, 2027: 170.0,
                    2028: 180.0, 2029: 190.0, 2030: 200.0},
            unit="EUR",
        )

        descriptor2 = _create_test_descriptor("test-asset-2", "Test Asset 2")
        asset2 = ExogenousAsset(
            descriptor=descriptor2,
            name="series2",
            values={2020: 10.0, 2021: 11.0, 2022: 12.0, 2023: 13.0,
                    2024: 14.0, 2025: 15.0, 2026: 16.0, 2027: 17.0,
                    2028: 18.0, 2029: 19.0, 2030: 20.0},
            unit="EUR",
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset1, asset2))

        # Act & Assert - Should not raise
        context.validate_coverage(2020, 2030)

    def test_validate_coverage_fails_for_missing_years(self):
        """validate_coverage() should fail for series with gaps."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_series",
            values={2020: 100.0, 2030: 200.0},  # Gap - missing years in between
            unit="EUR",
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Act & Assert
        with pytest.raises(OrchestratorError, match="Missing exogenous coverage"):
            context.validate_coverage(2020, 2030)

    def test_validate_coverage_validates_year_order(self):
        """validate_coverage() should validate start_year <= end_year."""
        # Arrange
        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets(())

        # Act & Assert
        with pytest.raises(ValueError, match="start_year.*end_year"):
            context.validate_coverage(2030, 2020)


class TestExogenousContextAssetAccess:
    """Test ExogenousContext.get_asset() and properties."""

    def test_get_asset_returns_full_asset(self):
        """get_asset() should return the full ExogenousAsset."""
        # Arrange
        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_series",
            values={2020: 100.0},
            unit="EUR",
        )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets((asset,))

        # Act
        result = context.get_asset("test_series")

        # Assert
        assert result is asset
        assert result.name == "test_series"
        assert result.unit == "EUR"

    def test_get_asset_raises_keyerror_for_unknown_series(self):
        """get_asset() should raise KeyError for unknown series name."""
        # Arrange
        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets(())

        # Act & Assert
        with pytest.raises(KeyError, match="unknown_series"):
            context.get_asset("unknown_series")

    def test_series_names_returns_sorted_tuple(self):
        """series_names property should return sorted tuple of names."""
        # Arrange
        assets = []
        for name in ["zebra", "apple", "banana"]:
            descriptor = _create_test_descriptor(f"test-{name}", name)
            assets.append(
                ExogenousAsset(
                    descriptor=descriptor,
                    name=name,
                    values={2020: 100.0},
                    unit="EUR",
                )
            )

        from reformlab.orchestrator.exogenous import ExogenousContext

        context = ExogenousContext.from_assets(tuple(assets))

        # Act & Assert
        assert context.series_names == ("apple", "banana", "zebra")


# ============================================================================
# Orchestrator Integration Tests — Story 21.6, AC2
# ============================================================================


class TestOrchestratorExogenousIntegration:
    """Test OrchestratorConfig exogenous field propagation through YearState."""

    def test_orchestrator_config_exogenous_field_propagates_to_state(self):
        """OrchestratorConfig.exogenous should flow through YearState.data."""
        # Arrange
        from reformlab.orchestrator import ExogenousContext, Orchestrator, OrchestratorConfig

        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="fuel_price",
            values={2025: 1.55, 2026: 1.60, 2027: 1.65},
            unit="EUR/litre",
        )
        exogenous = ExogenousContext.from_assets((asset,))

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            seed=42,
            step_pipeline=(),
            exogenous=exogenous,
        )

        # Act
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Assert - ExogenousContext should be accessible in YearState.data
        assert result.success is True
        # Check first year's state has exogenous context
        first_year_state = result.yearly_states[2025]
        assert "exogenous_context" in first_year_state.data
        assert first_year_state.data["exogenous_context"] is exogenous

    def test_steps_can_access_exogenous_context_from_state(self):
        """Steps should be able to access exogenous values via state.data["exogenous_context"]."""
        # Arrange
        from reformlab.orchestrator import (
            ExogenousContext,
            Orchestrator,
            OrchestratorConfig,
            YearState,
        )

        descriptor = _create_test_descriptor("test-asset", "Test Asset")
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test_value",
            values={2025: 100.0, 2026: 110.0, 2027: 120.0},
            unit="USD",
        )
        exogenous = ExogenousContext.from_assets((asset,))

        # Step that reads exogenous value
        def exogenous_reader_step(year: int, state: YearState) -> YearState:
            from dataclasses import replace

            context = state.data.get("exogenous_context")
            assert context is not None, "ExogenousContext not found in state"
            value = context.get_value("test_value", year)
            return replace(state, data={**state.data, "read_value": value})

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            seed=42,
            step_pipeline=(exogenous_reader_step,),
            exogenous=exogenous,
        )

        # Act
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Assert - Step should have read values from exogenous context
        assert result.success is True
        assert result.yearly_states[2025].data["read_value"] == 100.0
        assert result.yearly_states[2026].data["read_value"] == 110.0
        assert result.yearly_states[2027].data["read_value"] == 120.0

    def test_backward_compatibility_without_exogenous(self):
        """Scenarios without exogenous field should continue to work (None default)."""
        # Arrange
        from reformlab.orchestrator import Orchestrator, OrchestratorConfig

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            seed=42,
            step_pipeline=(),
            # No exogenous field - defaults to None
        )

        # Act
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Assert - Should run without error
        assert result.success is True
        # Exogenous context should not be in state data
        first_year_state = result.yearly_states[2025]
        assert "exogenous_context" not in first_year_state.data

