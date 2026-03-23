# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for calibration provenance capture, reference, and extraction — Story 15.4 / FR52."""

from __future__ import annotations

import pytest

from reformlab.calibration.errors import CalibrationProvenanceError
from reformlab.calibration.provenance import (
    capture_calibration_provenance,
    extract_calibrated_parameters,
    make_calibration_reference,
)
from reformlab.calibration.validation import validate_holdout
from reformlab.governance.manifest import RunManifest
from tests.calibration.conftest import (
    make_holdout_cost_matrix,
    make_holdout_from_states,
    make_holdout_target_set,
    make_sample_engine,
    make_sample_target_set,
)

# ============================== TestCaptureCalibrationProvenance ==============================


class TestCaptureCalibrationProvenance:
    """AC-1: Calibration provenance is captured with all required entries."""

    def test_result_only_returns_one_entry(self) -> None:
        """Given only CalibrationResult, capture returns exactly 1 assumption entry."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        assert len(entries) == 1
        assert entries[0]["key"] == "calibration_result"

    def test_result_plus_target_set_returns_two_entries(self) -> None:
        """Given CalibrationResult + CalibrationTargetSet, capture returns 2 entries."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result, target_set=make_sample_target_set())
        assert len(entries) == 2
        keys = [e["key"] for e in entries]
        assert "calibration_result" in keys
        assert "calibration_targets" in keys

    def test_result_plus_holdout_returns_two_entries(self) -> None:
        """Given CalibrationResult + HoldoutValidationResult, capture returns 2 entries."""
        cal_result = make_sample_engine().calibrate()
        holdout = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )
        entries = capture_calibration_provenance(cal_result, holdout_result=holdout)
        assert len(entries) == 2
        keys = [e["key"] for e in entries]
        assert "calibration_result" in keys
        assert "holdout_validation" in keys

    def test_all_three_returns_three_sorted_entries(self) -> None:
        """Given result + target_set + holdout, capture returns 3 entries sorted by key."""
        cal_result = make_sample_engine().calibrate()
        holdout = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )
        entries = capture_calibration_provenance(
            cal_result,
            target_set=make_sample_target_set(),
            holdout_result=holdout,
        )
        assert len(entries) == 3
        keys = [e["key"] for e in entries]
        # Alphabetically sorted: calibration_result, calibration_targets, holdout_validation
        assert keys == sorted(keys)

    def test_entries_have_correct_keys(self) -> None:
        """Given all three inputs, entries have keys: calibration_result, calibration_targets,
        holdout_validation."""
        cal_result = make_sample_engine().calibrate()
        holdout = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )
        entries = capture_calibration_provenance(
            cal_result,
            target_set=make_sample_target_set(),
            holdout_result=holdout,
        )
        keys = {e["key"] for e in entries}
        assert keys == {"calibration_result", "calibration_targets", "holdout_validation"}

    def test_entries_are_assumption_entry_compatible(self) -> None:
        """Given CalibrationResult, entries have key/value/source/is_default fields."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        for entry in entries:
            assert "key" in entry
            assert "value" in entry
            assert "source" in entry
            assert "is_default" in entry
            assert isinstance(entry["key"], str)
            assert isinstance(entry["source"], str)
            assert isinstance(entry["is_default"], bool)

    def test_custom_source_label_propagated(self) -> None:
        """Given source_label='my_engine', all entries have source='my_engine'."""
        cal_result = make_sample_engine().calibrate()
        holdout = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )
        entries = capture_calibration_provenance(
            cal_result,
            target_set=make_sample_target_set(),
            holdout_result=holdout,
            source_label="my_engine",
        )
        for entry in entries:
            assert entry["source"] == "my_engine"

    def test_calibration_result_value_contains_gradient_norm(self) -> None:
        """Given CalibrationResult, the calibration_result entry value includes gradient_norm (AC-1)."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        result_entry = next(e for e in entries if e["key"] == "calibration_result")
        assert "gradient_norm" in result_entry["value"]
        # gradient_norm can be float or None (None for gradient-free methods)
        gn = result_entry["value"]["gradient_norm"]
        assert gn is None or isinstance(gn, float)

    def test_calibration_result_value_contains_all_required_fields(self) -> None:
        """Given CalibrationResult, value has all AC-1 required fields."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        value = next(e for e in entries if e["key"] == "calibration_result")["value"]
        required_fields = {
            "domain",
            "optimized_beta_cost",
            "objective_type",
            "final_objective_value",
            "convergence_flag",
            "iterations",
            "gradient_norm",
            "method",
            "all_within_tolerance",
            "n_targets",
        }
        assert set(value.keys()) >= required_fields


# ============================== TestCaptureCalibrationProvenanceValidation ==============================


class TestCaptureCalibrationProvenanceValidation:
    """AC-1: Input validation for capture_calibration_provenance."""

    def test_invalid_calibration_result_type_raises_type_error(self) -> None:
        """Given calibration_result is not CalibrationResult, raises TypeError."""
        with pytest.raises(TypeError, match="CalibrationResult"):
            capture_calibration_provenance("not_a_result")  # type: ignore[arg-type]

    def test_dict_instead_of_result_raises_type_error(self) -> None:
        """Given a dict instead of CalibrationResult, raises TypeError."""
        with pytest.raises(TypeError, match="CalibrationResult"):
            capture_calibration_provenance({"domain": "vehicle"})  # type: ignore[arg-type]


# ============================== TestMakeCalibrationReference ==============================


class TestMakeCalibrationReference:
    """AC-2: Calibration run reference creation."""

    def test_manifest_id_only_returns_correct_structure(self) -> None:
        """Given manifest_id only, returns AssumptionEntry-compatible dict."""
        ref = make_calibration_reference("abc-123-uuid")
        assert ref["key"] == "calibration_reference"
        assert ref["value"]["calibration_manifest_id"] == "abc-123-uuid"
        assert "calibration_integrity_hash" not in ref["value"]
        assert ref["source"] == "calibration_provenance"
        assert ref["is_default"] is False

    def test_manifest_id_with_integrity_hash(self) -> None:
        """Given manifest_id + integrity_hash, both fields are in the value dict."""
        ref = make_calibration_reference("abc-123-uuid", calibration_integrity_hash="sha256abc")
        assert ref["value"]["calibration_manifest_id"] == "abc-123-uuid"
        assert ref["value"]["calibration_integrity_hash"] == "sha256abc"

    def test_empty_manifest_id_raises_provenance_error(self) -> None:
        """Given empty manifest_id, raises CalibrationProvenanceError."""
        with pytest.raises(CalibrationProvenanceError, match="manifest_id"):
            make_calibration_reference("")

    def test_whitespace_only_manifest_id_raises_provenance_error(self) -> None:
        """Given whitespace-only manifest_id, raises CalibrationProvenanceError."""
        with pytest.raises(CalibrationProvenanceError, match="manifest_id"):
            make_calibration_reference("   ")

    def test_entry_has_all_assumption_entry_fields(self) -> None:
        """Given manifest_id, entry has key/value/source/is_default fields."""
        ref = make_calibration_reference("some-id")
        assert "key" in ref
        assert "value" in ref
        assert "source" in ref
        assert "is_default" in ref


# ============================== TestExtractCalibratedParameters ==============================


class TestExtractCalibratedParameters:
    """AC-3: Parameter extraction from manifest assumptions."""

    def test_round_trip_preserves_exact_beta(self) -> None:
        """Given calibrated result → capture → extract, beta_cost is identical."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        extracted = extract_calibrated_parameters(entries, "vehicle")
        assert extracted.beta_cost == cal_result.optimized_parameters.beta_cost

    def test_extracted_taste_parameters_has_exact_beta_cost(self) -> None:
        """Given an entry with optimized_beta_cost=-0.05, extract returns TasteParameters(beta_cost=-0.05)."""
        assumptions = [
            {
                "key": "calibration_result",
                "value": {
                    "domain": "vehicle",
                    "optimized_beta_cost": -0.05,
                },
                "source": "calibration_engine",
                "is_default": False,
            }
        ]
        from reformlab.discrete_choice.types import TasteParameters
        result = extract_calibrated_parameters(assumptions, "vehicle")
        assert result == TasteParameters(beta_cost=-0.05)

    def test_missing_domain_raises_provenance_error(self) -> None:
        """Given no entry for domain 'heating', raises CalibrationProvenanceError."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        with pytest.raises(CalibrationProvenanceError, match="heating"):
            extract_calibrated_parameters(entries, "heating")

    def test_empty_assumptions_raises_provenance_error(self) -> None:
        """Given empty assumptions list, raises CalibrationProvenanceError."""
        with pytest.raises(CalibrationProvenanceError, match="empty"):
            extract_calibrated_parameters([], "vehicle")

    def test_no_calibration_result_key_raises_provenance_error(self) -> None:
        """Given assumptions with no calibration_result key, raises CalibrationProvenanceError."""
        assumptions = [
            {
                "key": "calibration_targets",
                "value": {"domains": ["vehicle"]},
                "source": "test",
                "is_default": False,
            }
        ]
        with pytest.raises(CalibrationProvenanceError, match="vehicle"):
            extract_calibrated_parameters(assumptions, "vehicle")

    def test_multiple_domains_returns_correct_one(self) -> None:
        """Given entries for vehicle and heating, extract returns the correct domain's beta."""
        assumptions = [
            {
                "key": "calibration_result",
                "value": {"domain": "vehicle", "optimized_beta_cost": -0.01},
                "source": "calibration_engine",
                "is_default": False,
            },
            {
                "key": "calibration_result",
                "value": {"domain": "heating", "optimized_beta_cost": -0.03},
                "source": "calibration_engine",
                "is_default": False,
            },
        ]
        extracted_vehicle = extract_calibrated_parameters(assumptions, "vehicle")
        extracted_heating = extract_calibrated_parameters(assumptions, "heating")
        assert extracted_vehicle.beta_cost == -0.01
        assert extracted_heating.beta_cost == -0.03

    def test_duplicate_domain_entries_raise_provenance_error_with_count(self) -> None:
        """Given 2 calibration_result entries for same domain, raises
        CalibrationProvenanceError with count."""
        assumptions = [
            {
                "key": "calibration_result",
                "value": {"domain": "vehicle", "optimized_beta_cost": -0.01},
                "source": "calibration_engine",
                "is_default": False,
            },
            {
                "key": "calibration_result",
                "value": {"domain": "vehicle", "optimized_beta_cost": -0.02},
                "source": "calibration_engine",
                "is_default": False,
            },
        ]
        with pytest.raises(CalibrationProvenanceError, match="2"):
            extract_calibrated_parameters(assumptions, "vehicle")

    def test_non_numeric_beta_cost_raises_provenance_error(self) -> None:
        """Given optimized_beta_cost='not_a_float', raises CalibrationProvenanceError."""
        assumptions = [
            {
                "key": "calibration_result",
                "value": {"domain": "vehicle", "optimized_beta_cost": "not_a_float"},
                "source": "calibration_engine",
                "is_default": False,
            }
        ]
        with pytest.raises(CalibrationProvenanceError, match="float or int"):
            extract_calibrated_parameters(assumptions, "vehicle")

    def test_non_dict_value_raises_provenance_error(self) -> None:
        """Given a calibration_result entry with a non-dict value, raises CalibrationProvenanceError."""
        # AC-3: malformed manifest entry must raise CalibrationProvenanceError, not AttributeError
        assumptions = [
            {
                "key": "calibration_result",
                "value": "not-a-dict",
                "source": "calibration_engine",
                "is_default": False,
            }
        ]
        with pytest.raises(CalibrationProvenanceError, match="non-dict"):
            extract_calibrated_parameters(assumptions, "vehicle")

    def test_integer_beta_cost_is_accepted(self) -> None:
        """Given optimized_beta_cost as int, extract returns TasteParameters with float beta."""
        assumptions = [
            {
                "key": "calibration_result",
                "value": {"domain": "vehicle", "optimized_beta_cost": -1},
                "source": "calibration_engine",
                "is_default": False,
            }
        ]
        from reformlab.discrete_choice.types import TasteParameters
        result = extract_calibrated_parameters(assumptions, "vehicle")
        assert result == TasteParameters(beta_cost=-1.0)
        assert isinstance(result.beta_cost, float)


# ============================== TestRoundTrip ==============================


class TestRoundTrip:
    """AC: End-to-end integration — calibrate → capture → manifest → extract."""

    def test_captured_entries_pass_manifest_validation(self) -> None:
        """Given captured provenance entries, they pass RunManifest assumption validation."""
        cal_result = make_sample_engine().calibrate()
        entries = capture_calibration_provenance(cal_result)
        # Construct manifest with these assumptions — must not raise
        manifest = RunManifest(
            manifest_id="test-manifest-id",
            created_at="2026-03-07T12:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            assumptions=entries,  # type: ignore[arg-type]
        )
        assert len(manifest.assumptions) == 1

    def test_full_provenance_passes_manifest_validation(self) -> None:
        """Given result + target_set + holdout entries, all pass RunManifest validation."""
        cal_result = make_sample_engine().calibrate()
        holdout = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )
        entries = capture_calibration_provenance(
            cal_result,
            target_set=make_sample_target_set(),
            holdout_result=holdout,
        )
        manifest = RunManifest(
            manifest_id="test-manifest-id",
            created_at="2026-03-07T12:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            assumptions=entries,  # type: ignore[arg-type]
        )
        assert len(manifest.assumptions) == 3

    def test_end_to_end_calibrate_capture_extract_round_trip(self) -> None:
        """Given full pipeline: calibrate → capture → extract, returns identical TasteParameters."""
        engine = make_sample_engine()
        cal_result = engine.calibrate()
        entries = capture_calibration_provenance(cal_result)
        extracted = extract_calibrated_parameters(entries, cal_result.domain)
        # Exact equality — no approximation
        assert extracted.beta_cost == cal_result.optimized_parameters.beta_cost

    def test_calibration_reference_passes_manifest_validation(self) -> None:
        """Given a calibration_reference entry, it passes RunManifest assumption validation."""
        ref = make_calibration_reference("11111111-2222-3333-4444-555555555555")
        manifest = RunManifest(
            manifest_id="test-manifest-id",
            created_at="2026-03-07T12:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            assumptions=[ref],  # type: ignore[arg-type]
        )
        assert manifest.assumptions[0]["key"] == "calibration_reference"
