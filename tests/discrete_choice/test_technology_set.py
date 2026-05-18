# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for technology set value objects.

Story 28.1, AC-2: Backend value object with DomainTechnologySet and TechnologySet
frozen dataclasses, to_choice_set method, version validation.
"""

from __future__ import annotations

import pytest

from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.technology_set import (
    DEFAULT_HEATING_TECHNOLOGY_SET,
    DEFAULT_TECHNOLOGY_SET,
    DEFAULT_VEHICLE_TECHNOLOGY_SET,
    DomainTechnologySet,
    TechnologySet,
)
from reformlab.discrete_choice.types import Alternative, ChoiceSet


class TestDomainTechnologySet:
    """Tests for DomainTechnologySet frozen dataclass."""

    def test_domain_technology_set_creation_heating(self) -> None:
        """DomainTechnologySet for heating domain with 5 alternatives."""
        alternatives = (
            Alternative(id="keep_current", name="Keep Current", attributes={}),
            Alternative(id="condensing_boiler", name="Condensing Boiler", attributes={}),
            Alternative(id="heat_pump_air", name="Air Source Heat Pump", attributes={}),
            Alternative(id="heat_pump_ground", name="Ground Source Heat Pump", attributes={}),
            Alternative(id="district_heating", name="District Heating", attributes={}),
        )
        dts = DomainTechnologySet(
            domain="heating",
            enabled=True,
            alternatives=alternatives,
            reference_alternative_id="keep_current",
            cost_column="heating_cost",
        )
        assert dts.domain == "heating"
        assert dts.enabled is True
        assert len(dts.alternatives) == 5
        assert dts.reference_alternative_id == "keep_current"
        assert dts.cost_column == "heating_cost"

    def test_domain_technology_set_creation_vehicle(self) -> None:
        """DomainTechnologySet for vehicle domain with 6 alternatives."""
        alternatives = (
            Alternative(id="keep_current", name="Keep Current", attributes={}),
            Alternative(id="petrol", name="Petrol Car", attributes={}),
            Alternative(id="diesel", name="Diesel Car", attributes={}),
            Alternative(id="hybrid", name="Hybrid Car", attributes={}),
            Alternative(id="ev", name="Electric Vehicle", attributes={}),
            Alternative(id="plug_in_hybrid", name="Plug-in Hybrid", attributes={}),
        )
        dts = DomainTechnologySet(
            domain="vehicle",
            enabled=True,
            alternatives=alternatives,
            reference_alternative_id="keep_current",
            cost_column="total_vehicle_cost",
        )
        assert dts.domain == "vehicle"
        assert len(dts.alternatives) == 6
        assert dts.cost_column == "total_vehicle_cost"

    def test_domain_technology_set_immutable(self) -> None:
        """DomainTechnologySet is frozen (immutable)."""
        dts = DomainTechnologySet(
            domain="heating",
            enabled=True,
            alternatives=(Alternative(id="x", name="X", attributes={}),),
            reference_alternative_id="x",
        )
        with pytest.raises(AttributeError):
            dts.domain = "vehicle"  # type: ignore[misc]

    def test_domain_technology_set_disabled(self) -> None:
        """DomainTechnologySet can be disabled."""
        dts = DomainTechnologySet(
            domain="heating",
            enabled=False,
            alternatives=(Alternative(id="x", name="X", attributes={}),),
            reference_alternative_id="x",
        )
        assert dts.enabled is False


class TestTechnologySet:
    """Tests for TechnologySet frozen dataclass."""

    def test_technology_set_creation(self) -> None:
        """TechnologySet with version and domains dict."""
        heating_dts = DomainTechnologySet(
            domain="heating",
            enabled=True,
            alternatives=(Alternative(id="h1", name="H1", attributes={}),),
            reference_alternative_id="h1",
        )
        vehicle_dts = DomainTechnologySet(
            domain="vehicle",
            enabled=True,
            alternatives=(Alternative(id="v1", name="V1", attributes={}),),
            reference_alternative_id="v1",
        )
        ts = TechnologySet(
            version="fr-default-2026-04-26",
            domains={"heating": heating_dts, "vehicle": vehicle_dts},
        )
        assert ts.version == "fr-default-2026-04-26"
        assert len(ts.domains) == 2
        assert "heating" in ts.domains
        assert "vehicle" in ts.domains

    def test_technology_set_version_format_valid(self) -> None:
        """Valid version formats: {cc}-default-{YYYY}-{MM}-{DD}."""
        ts = TechnologySet(
            version="fr-default-2026-04-26",
            domains={},
        )
        assert ts.version == "fr-default-2026-04-26"

    def test_technology_set_version_format_invalid_raises(self) -> None:
        """Invalid version format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            TechnologySet(
                version="invalid-version",
                domains={},
            )

    def test_technology_set_immutable(self) -> None:
        """TechnologySet is frozen (immutable)."""
        ts = TechnologySet(version="fr-default-2026-04-26", domains={})
        with pytest.raises(AttributeError):
            ts.version = "other"  # type: ignore[misc]

    def test_to_choice_set_valid_domain(self) -> None:
        """to_choice_set returns ChoiceSet for enabled domain."""
        alternatives = (
            Alternative(id="keep_current", name="Keep Current", attributes={}),
            Alternative(id="heat_pump", name="Heat Pump", attributes={}),
        )
        dts = DomainTechnologySet(
            domain="heating",
            enabled=True,
            alternatives=alternatives,
            reference_alternative_id="keep_current",
        )
        ts = TechnologySet(
            version="fr-default-2026-04-26",
            domains={"heating": dts},
        )

        choice_set = ts.to_choice_set("heating")
        assert isinstance(choice_set, ChoiceSet)
        assert choice_set.size == 2
        assert choice_set.alternative_ids == ("keep_current", "heat_pump")

    def test_to_choice_set_unknown_domain_raises(self) -> None:
        """to_choice_set for unknown domain raises DiscreteChoiceError."""
        ts = TechnologySet(version="fr-default-2026-04-26", domains={})
        with pytest.raises(DiscreteChoiceError, match="Domain 'unknown' not in technology_set"):
            ts.to_choice_set("unknown")

    def test_to_choice_set_disabled_domain_raises(self) -> None:
        """to_choice_set for disabled domain raises DiscreteChoiceError."""
        dts = DomainTechnologySet(
            domain="heating",
            enabled=False,
            alternatives=(Alternative(id="x", name="X", attributes={}),),
            reference_alternative_id="x",
        )
        ts = TechnologySet(version="fr-default-2026-04-26", domains={"heating": dts})
        with pytest.raises(DiscreteChoiceError, match="Domain 'heating' is disabled"):
            ts.to_choice_set("heating")


class TestDefaultTechnologySets:
    """Tests for default technology set constants."""

    def test_default_technology_set_version(self) -> None:
        """DEFAULT_TECHNOLOGY_SET has correct version format."""
        assert DEFAULT_TECHNOLOGY_SET.version == "fr-default-2026-04-26"

    def test_default_technology_set_has_heating(self) -> None:
        """DEFAULT_TECHNOLOGY_SET includes heating domain."""
        assert "heating" in DEFAULT_TECHNOLOGY_SET.domains
        heating_dts = DEFAULT_TECHNOLOGY_SET.domains["heating"]
        assert heating_dts.enabled is True
        assert len(heating_dts.alternatives) == 5
        assert heating_dts.reference_alternative_id == "keep_current"
        assert heating_dts.cost_column == "heating_cost"

    def test_default_technology_set_has_vehicle(self) -> None:
        """DEFAULT_TECHNOLOGY_SET includes vehicle domain."""
        assert "vehicle" in DEFAULT_TECHNOLOGY_SET.domains
        vehicle_dts = DEFAULT_TECHNOLOGY_SET.domains["vehicle"]
        assert vehicle_dts.enabled is True
        assert len(vehicle_dts.alternatives) == 6
        assert vehicle_dts.reference_alternative_id == "keep_current"
        assert vehicle_dts.cost_column == "total_vehicle_cost"

    def test_default_heating_alternatives_ids(self) -> None:
        """DEFAULT_HEATING_TECHNOLOGY_SET has expected alternative IDs."""
        expected_ids = (
            "keep_current",
            "condensing_boiler",
            "heat_pump_air",
            "heat_pump_ground",
            "district_heating",
        )
        assert DEFAULT_HEATING_TECHNOLOGY_SET.alternative_ids == expected_ids

    def test_default_vehicle_alternatives_ids(self) -> None:
        """DEFAULT_VEHICLE_TECHNOLOGY_SET has expected alternative IDs."""
        expected_ids = (
            "keep_current",
            "petrol",
            "diesel",
            "hybrid",
            "ev",
            "plug_in_hybrid",
        )
        assert DEFAULT_VEHICLE_TECHNOLOGY_SET.alternative_ids == expected_ids


class TestTechnologySetToApiDict:
    """Tests for to_api_dict serialization method."""

    def test_to_api_dict_structure(self) -> None:
        """to_api_dict returns dict with version and nested domains."""
        dts = DomainTechnologySet(
            domain="heating",
            enabled=True,
            alternatives=(Alternative(id="h1", name="H1", attributes={"x": 1}),),
            reference_alternative_id="h1",
            cost_column="heating_cost",
        )
        ts = TechnologySet(
            version="fr-default-2026-04-26",
            domains={"heating": dts},
        )

        result = ts.to_api_dict()
        assert result["version"] == "fr-default-2026-04-26"
        assert "domains" in result
        assert "heating" in result["domains"]
        assert result["domains"]["heating"]["domain"] == "heating"
        assert result["domains"]["heating"]["enabled"] is True
        expected_alternatives = [{"id": "h1", "name": "H1", "attributes": {"x": 1}}]
        assert result["domains"]["heating"]["alternatives"] == expected_alternatives
        assert result["domains"]["heating"]["referenceAlternativeId"] == "h1"
        assert result["domains"]["heating"]["costColumn"] == "heating_cost"
