# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for trust-status rule evaluation.

Story 21.5 — trust-status rules enforcement.
"""

from __future__ import annotations

from reformlab.data.descriptor import DataAssetDescriptor
from reformlab.data.trust_rules import (
    check_asset_trust,
    check_multiple_assets,
    summarize_trust_warnings,
)


def _make_descriptor(
    trust_status: str,
    *,
    asset_id: str = "test-asset",
    name: str = "Test Asset",
    origin: str = "synthetic-public",
    access_mode: str = "bundled",
) -> DataAssetDescriptor:
    """Create a minimal valid DataAssetDescriptor for testing."""
    # open-official only supports production-safe and exploratory
    if origin == "open-official" and trust_status not in ("production-safe", "exploratory"):
        origin = "synthetic-public"
    # synthetic-public does not support production-safe
    if origin == "synthetic-public" and trust_status == "production-safe":
        origin = "open-official"
    return DataAssetDescriptor(
        asset_id=asset_id,
        name=name,
        description="Test description",
        data_class="exogenous",
        origin=origin,
        access_mode=access_mode,
        trust_status=trust_status,
    )


class TestCheckAssetTrust:
    """Tests for check_asset_trust() with each trust status."""

    def test_production_safe_returns_ok(self) -> None:
        descriptor = _make_descriptor("production-safe")
        result = check_asset_trust(descriptor)
        assert result.status == "ok"
        assert result.asset_id == descriptor.asset_id
        assert result.trust_status == "production-safe"
        assert "production-safe" in result.message

    def test_exploratory_returns_warning(self) -> None:
        descriptor = _make_descriptor("exploratory")
        result = check_asset_trust(descriptor)
        assert result.status == "warning"
        assert result.trust_status == "exploratory"
        assert "exploratory" in result.message

    def test_demo_only_returns_warning(self) -> None:
        descriptor = _make_descriptor("demo-only")
        result = check_asset_trust(descriptor)
        assert result.status == "warning"
        assert result.trust_status == "demo-only"
        assert "demo-only" in result.message

    def test_validation_pending_returns_warning(self) -> None:
        descriptor = _make_descriptor("validation-pending")
        result = check_asset_trust(descriptor)
        assert result.status == "warning"
        assert result.trust_status == "validation-pending"
        assert "validation-pending" in result.message

    def test_not_for_public_inference_returns_warning(self) -> None:
        descriptor = _make_descriptor("not-for-public-inference")
        result = check_asset_trust(descriptor)
        assert result.status == "warning"
        assert result.trust_status == "not-for-public-inference"
        assert "not-for-public-inference" in result.message

    def test_message_includes_asset_name(self) -> None:
        descriptor = _make_descriptor("exploratory", name="Energy Prices 2024")
        result = check_asset_trust(descriptor)
        assert "Energy Prices 2024" in result.message


class TestCheckMultipleAssets:
    """Tests for check_multiple_assets() with mixed statuses."""

    def test_all_production_safe(self) -> None:
        descriptors = (
            _make_descriptor("production-safe", asset_id="a1"),
            _make_descriptor("production-safe", asset_id="a2"),
        )
        results = check_multiple_assets(descriptors)
        assert len(results) == 2
        assert all(r.status == "ok" for r in results)

    def test_all_warnings(self) -> None:
        descriptors = (
            _make_descriptor("exploratory", asset_id="a1"),
            _make_descriptor("demo-only", asset_id="a2"),
        )
        results = check_multiple_assets(descriptors)
        assert len(results) == 2
        assert all(r.status == "warning" for r in results)

    def test_mixed_statuses(self) -> None:
        descriptors = (
            _make_descriptor("production-safe", asset_id="a1"),
            _make_descriptor("exploratory", asset_id="a2"),
        )
        results = check_multiple_assets(descriptors)
        assert results[0].status == "ok"
        assert results[1].status == "warning"

    def test_empty_tuple(self) -> None:
        results = check_multiple_assets(())
        assert results == ()


class TestSummarizeTrustWarnings:
    """Tests for summarize_trust_warnings()."""

    def test_no_warnings_returns_none(self) -> None:
        descriptors = (
            _make_descriptor("production-safe", asset_id="a1"),
            _make_descriptor("production-safe", asset_id="a2"),
        )
        results = check_multiple_assets(descriptors)
        assert summarize_trust_warnings(results) is None

    def test_single_warning(self) -> None:
        descriptors = (_make_descriptor("exploratory", asset_id="a1"),)
        results = check_multiple_assets(descriptors)
        summary = summarize_trust_warnings(results)
        assert summary is not None
        assert "exploratory" in summary

    def test_multiple_warnings_joined(self) -> None:
        descriptors = (
            _make_descriptor("exploratory", asset_id="a1"),
            _make_descriptor("demo-only", asset_id="a2"),
        )
        results = check_multiple_assets(descriptors)
        summary = summarize_trust_warnings(results)
        assert summary is not None
        assert "exploratory" in summary
        assert "demo-only" in summary
        assert "; " in summary

    def test_empty_results_returns_none(self) -> None:
        assert summarize_trust_warnings(()) is None
