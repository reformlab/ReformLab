# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for trust-status preflight validation check.

Story 21.5 — trust-status rules preflight integration.
"""

from __future__ import annotations

from unittest.mock import patch

from reformlab.data.assets import ExogenousAsset
from reformlab.data.descriptor import DataAssetDescriptor
from reformlab.data.errors import EvidenceAssetError
from reformlab.server.models import PreflightRequest, ValidationCheckResult
from reformlab.server.validation import _check_trust_status


def _make_exogenous_asset(
    series_name: str,
    trust_status: str,
) -> ExogenousAsset:
    """Create a minimal ExogenousAsset for testing."""
    # open-official supports production-safe/exploratory; synthetic-public for the rest
    if trust_status == "production-safe":
        origin = "open-official"
    else:
        origin = "synthetic-public"
    descriptor = DataAssetDescriptor(
        asset_id=f"test-{series_name}",
        name=f"Test {series_name}",
        description="Test exogenous asset",
        data_class="exogenous",
        origin=origin,
        access_mode="bundled",
        trust_status=trust_status,
    )
    return ExogenousAsset(
        descriptor=descriptor,
        name=series_name,
        values={2024: 100.0, 2025: 105.0},
        unit="EUR/MWh",
    )


def _make_request(exogenous_series: list[str] | None = None) -> PreflightRequest:
    """Create a PreflightRequest with optional exogenous series."""
    engine_config: dict[str, object] = {
        "startYear": 2024,
        "endYear": 2030,
    }
    if exogenous_series is not None:
        engine_config["exogenousSeries"] = exogenous_series
    return PreflightRequest(
        scenario={"engineConfig": engine_config},
        population_id="test-pop",
        template_name="test-template",
    )


class TestTrustStatusPreflightCheck:
    """Tests for _check_trust_status preflight check."""

    @patch("reformlab.data.exogenous_loader.load_exogenous_asset")
    def test_all_production_safe_passes(self, mock_load: object) -> None:
        mock_load.side_effect = lambda name: _make_exogenous_asset(name, "production-safe")  # type: ignore[attr-defined]
        request = _make_request(["energy_price", "carbon_tax"])

        result = _check_trust_status(request)

        assert isinstance(result, ValidationCheckResult)
        assert result.id == "trust-status"
        assert result.passed is True
        assert result.severity == "warning"
        assert "production-safe" in result.message

    @patch("reformlab.data.exogenous_loader.load_exogenous_asset")
    def test_mixed_statuses_warns(self, mock_load: object) -> None:
        def side_effect(name: str) -> ExogenousAsset:
            if name == "energy_price":
                return _make_exogenous_asset(name, "production-safe")
            return _make_exogenous_asset(name, "exploratory")

        mock_load.side_effect = side_effect  # type: ignore[attr-defined]
        request = _make_request(["energy_price", "co2_factor"])

        result = _check_trust_status(request)

        assert result.passed is False
        assert result.severity == "warning"
        assert "exploratory" in result.message

    def test_no_exogenous_series_passes(self) -> None:
        request = _make_request()

        result = _check_trust_status(request)

        assert result.passed is True
        assert result.severity == "warning"

    def test_empty_exogenous_series_passes(self) -> None:
        request = _make_request([])

        result = _check_trust_status(request)

        assert result.passed is True

    @patch("reformlab.data.exogenous_loader.load_exogenous_asset")
    def test_unloadable_asset_graceful(self, mock_load: object) -> None:
        mock_load.side_effect = EvidenceAssetError("not found")  # type: ignore[attr-defined]
        request = _make_request(["missing_series"])

        result = _check_trust_status(request)

        assert result.passed is True
        assert "Could not verify" in result.message

    def test_missing_engine_config_passes(self) -> None:
        request = PreflightRequest(scenario={})

        result = _check_trust_status(request)

        assert result.passed is True
