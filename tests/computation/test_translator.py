# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for domain-layer translation (Story 24.2)."""

from __future__ import annotations

import pytest

from reformlab.computation.translator import (
    TranslationError,
    _translate_energy_poverty_aid_policy,
    _translate_subsidy_policy,
    _translate_vehicle_malus_policy,
    translate_policy,
)
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    RebateParameters,
    SubsidyParameters,
)


# Ensure custom types are registered before tests run
@pytest.fixture(autouse=True)
def _register_custom_types() -> None:
    """Ensure vehicle_malus and energy_poverty_aid types are registered."""
    import reformlab.templates.energy_poverty_aid  # noqa: F401
    import reformlab.templates.vehicle_malus  # noqa: F401


# ============================================================================
# TranslationError
# ============================================================================


class TestTranslationError:
    """Tests for TranslationError exception."""

    def test_error_has_structured_fields(self) -> None:
        err = TranslationError(what="w", why="y", fix="f")
        assert err.what == "w"
        assert err.why == "y"
        assert err.fix == "f"

    def test_error_message_format(self) -> None:
        err = TranslationError(what="A", why="B", fix="C")
        assert str(err) == "A — B — C"


# ============================================================================
# Subsidy translation
# ============================================================================


class TestSubsidyTranslation:
    """Tests for subsidy policy translation."""

    def test_subsidy_parameters_translated_correctly(self) -> None:
        policy = SubsidyParameters(
            rate_schedule={2025: 5000.0},
            income_caps={2025: 30000.0},
            eligible_categories=("low_income",),
        )
        result = _translate_subsidy_policy(policy, "test-subsidy")
        assert result is policy

    def test_subsidy_via_translate_policy(self) -> None:
        policy = SubsidyParameters(
            rate_schedule={2025: 5000.0},
            income_caps={2025: 30000.0},
        )
        result = translate_policy(policy, "test-subsidy")
        assert result is policy

    def test_subsidy_empty_rate_schedule_raises(self) -> None:
        policy = SubsidyParameters(rate_schedule={})
        with pytest.raises(TranslationError, match="rate_schedule"):
            _translate_subsidy_policy(policy, "test-subsidy")

    def test_subsidy_wrong_type_raises(self) -> None:
        policy = CarbonTaxParameters(rate_schedule={2025: 44.6})
        with pytest.raises(TranslationError, match="SubsidyParameters"):
            _translate_subsidy_policy(policy, "test-subsidy")


# ============================================================================
# Vehicle malus translation
# ============================================================================


class TestVehicleMalusTranslation:
    """Tests for vehicle malus policy translation."""

    def test_malus_parameters_translated_correctly(self) -> None:
        from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

        policy = VehicleMalusParameters(
            rate_schedule={2025: 50.0},
            emission_threshold=118.0,
            malus_rate_per_gkm=50.0,
        )
        result = _translate_vehicle_malus_policy(policy, "test-malus")
        assert result is policy

    def test_malus_via_translate_policy(self) -> None:
        from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

        policy = VehicleMalusParameters(
            rate_schedule={2025: 50.0},
            emission_threshold=118.0,
            malus_rate_per_gkm=50.0,
        )
        result = translate_policy(policy, "test-malus")
        assert result is policy

    def test_malus_negative_threshold_raises(self) -> None:
        from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

        policy = VehicleMalusParameters(
            rate_schedule={2025: 50.0},
            emission_threshold=-1.0,
            malus_rate_per_gkm=50.0,
        )
        with pytest.raises(TranslationError, match="emission_threshold"):
            _translate_vehicle_malus_policy(policy, "test-malus")

    def test_malus_negative_rate_raises(self) -> None:
        from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

        policy = VehicleMalusParameters(
            rate_schedule={2025: 50.0},
            emission_threshold=118.0,
            malus_rate_per_gkm=-1.0,
        )
        with pytest.raises(TranslationError, match="malus_rate_per_gkm"):
            _translate_vehicle_malus_policy(policy, "test-malus")

    def test_malus_wrong_type_raises(self) -> None:
        policy = CarbonTaxParameters(rate_schedule={2025: 44.6})
        with pytest.raises(TranslationError, match="VehicleMalusParameters"):
            _translate_vehicle_malus_policy(policy, "test-malus")

    def test_malus_threshold_schedule_year_mapping(self) -> None:
        from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

        policy = VehicleMalusParameters(
            rate_schedule={2025: 50.0, 2026: 60.0},
            emission_threshold=118.0,
            malus_rate_per_gkm=50.0,
            threshold_schedule={2025: 120.0, 2026: 115.0},
        )
        result = _translate_vehicle_malus_policy(policy, "test-malus")
        assert result.threshold_schedule == {2025: 120.0, 2026: 115.0}


# ============================================================================
# Energy poverty aid translation
# ============================================================================


class TestEnergyPovertyAidTranslation:
    """Tests for energy poverty aid policy translation."""

    def test_aid_parameters_translated_correctly(self) -> None:
        from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters

        policy = EnergyPovertyAidParameters(
            rate_schedule={2025: 150.0},
            income_ceiling=11000.0,
            base_aid_amount=150.0,
        )
        result = _translate_energy_poverty_aid_policy(policy, "test-aid")
        assert result is policy

    def test_aid_via_translate_policy(self) -> None:
        from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters

        policy = EnergyPovertyAidParameters(
            rate_schedule={2025: 150.0},
            income_ceiling=11000.0,
            base_aid_amount=150.0,
        )
        result = translate_policy(policy, "test-aid")
        assert result is policy

    def test_aid_negative_ceiling_raises(self) -> None:
        """EnergyPovertyAidParameters raises on init for income_ceiling <= 0."""
        from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters
        from reformlab.templates.exceptions import TemplateError

        with pytest.raises(TemplateError, match="income_ceiling"):
            EnergyPovertyAidParameters(
                rate_schedule={2025: 150.0},
                income_ceiling=-1.0,
                base_aid_amount=150.0,
            )

    def test_aid_negative_base_amount_raises(self) -> None:
        from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters

        policy = EnergyPovertyAidParameters(
            rate_schedule={2025: 150.0},
            income_ceiling=11000.0,
            base_aid_amount=-1.0,
        )
        with pytest.raises(TranslationError, match="base_aid_amount"):
            _translate_energy_poverty_aid_policy(policy, "test-aid")

    def test_aid_wrong_type_raises(self) -> None:
        policy = CarbonTaxParameters(rate_schedule={2025: 44.6})
        with pytest.raises(TranslationError, match="EnergyPovertyAidParameters"):
            _translate_energy_poverty_aid_policy(policy, "test-aid")


# ============================================================================
# Passthrough types (carbon_tax, rebate, feebate)
# ============================================================================


class TestPassthroughTranslation:
    """Tests for policy types that pass through without translation."""

    def test_carbon_tax_passes_through(self) -> None:
        policy = CarbonTaxParameters(rate_schedule={2025: 44.6})
        result = translate_policy(policy, "test-carbon")
        assert result is policy

    def test_rebate_passes_through(self) -> None:
        policy = RebateParameters(rate_schedule={2025: 100.0}, rebate_type="lump_sum")
        result = translate_policy(policy, "test-rebate")
        assert result is policy

    def test_feebate_passes_through(self) -> None:
        policy = FeebateParameters(
            rate_schedule={2025: 1.0},
            pivot_point=100.0,
            fee_rate=0.5,
            rebate_rate=0.3,
        )
        result = translate_policy(policy, "test-feebate")
        assert result is policy


# ============================================================================
# Unsupported policy types
# ============================================================================


class TestUnsupportedPolicyTypes:
    """Tests for unsupported policy type rejection."""

    def test_base_policy_parameters_raises(self) -> None:
        """Base PolicyParameters is not a registered type and raises."""
        from reformlab.templates.exceptions import TemplateError

        policy = PolicyParameters(rate_schedule={2025: 1.0})
        with pytest.raises(TemplateError, match="Cannot infer"):
            translate_policy(policy, "test-unknown")

    def test_translation_error_for_unregistered_custom_type(self) -> None:
        """A custom registered type not in the translator map raises TranslationError."""
        import dataclasses

        from reformlab.templates.schema import (
            register_custom_template,
            register_policy_type,
        )

        # Register a temporary custom type
        try:
            custom_type = register_policy_type("test_custom_policy_24_2")

            @dataclasses.dataclass(frozen=True)
            class TestCustomParams(PolicyParameters):
                custom_field: float = 0.0

            register_custom_template(custom_type, TestCustomParams)

            policy = TestCustomParams(rate_schedule={2025: 1.0}, custom_field=42.0)
            with pytest.raises(TranslationError, match="not supported"):
                translate_policy(policy, "test-custom")
        finally:
            from reformlab.templates.schema import unregister_policy_type

            try:
                unregister_policy_type("test_custom_policy_24_2")
            except Exception:
                pass
