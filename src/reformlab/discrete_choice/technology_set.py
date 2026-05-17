# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Technology set value objects for investment decision scenarios.

Defines frozen dataclasses for technology sets that name which technologies
are in scope per domain, with stable versioning and fully-embedded snapshots
for reproducibility. Provides a canonical contract for scenarios, populations,
choice writeback, wizard UI, and multi-period regression.

Story 28.1, AC-2: Backend value object with DomainTechnologySet and TechnologySet
frozen dataclasses, to_choice_set method, version validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from reformlab.discrete_choice.types import Alternative, ChoiceSet

if TYPE_CHECKING:
    pass

_VERSION_RE = re.compile(r"^[a-z]{2}-default-\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class DomainTechnologySet:
    """Per-domain technology configuration for investment decisions.

    Defines the alternatives available in a decision domain, whether the
    domain is enabled, and the cost column name for computation results.

    Attributes:
        domain: Domain identifier (e.g., "heating", "vehicle").
        enabled: Whether this domain is active in the scenario.
        alternatives: Tuple of alternatives available in this domain.
        reference_alternative_id: ID of the reference alternative (e.g., "keep_current").
        cost_column: Column name for cost metric in computation results.

    Story 28.1, AC-2: DomainTechnologySet frozen dataclass.
    """

    domain: str
    enabled: bool
    alternatives: tuple[Alternative, ...]
    reference_alternative_id: str
    cost_column: str | None = None

    @property
    def alternative_ids(self) -> tuple[str, ...]:
        """Alternative IDs in deterministic order."""
        return tuple(alt.id for alt in self.alternatives)


@dataclass(frozen=True)
class TechnologySet:
    """Technology set for investment decision scenarios.

    Defines which technologies are in scope per domain, with a stable version
    for reproducibility and a fully-embedded snapshot of all alternatives.

    Attributes:
        version: Version string in format "{cc}-default-{YYYY}-{MM}-{DD}"
            (e.g., "fr-default-2026-04-26").
        domains: Dict mapping domain names to DomainTechnologySet instances.

    Story 28.1, AC-2: TechnologySet frozen dataclass with to_choice_set method.
    """

    version: str
    domains: dict[str, DomainTechnologySet]

    def __post_init__(self) -> None:
        """Validate version format."""
        if not _VERSION_RE.match(self.version):
            raise ValueError(
                f"Invalid version format: {self.version}. "
                f"Expected format: 'cc-default-YYYY-MM-DD' (e.g., 'fr-default-2026-04-26')"
            )

    def to_choice_set(self, domain: str) -> ChoiceSet:
        """Materialize ChoiceSet for domain from stored alternatives.

        Validates that the domain exists in the technology set and is enabled,
        then returns a ChoiceSet containing the domain's alternatives.

        Args:
            domain: Domain identifier (e.g., "heating", "vehicle").

        Returns:
            ChoiceSet with the domain's alternatives.

        Raises:
            DiscreteChoiceError: If domain not found or disabled.

        Story 28.1, AC-2: to_choice_set method that materializes ChoiceSet.
        """
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        if domain not in self.domains:
            raise DiscreteChoiceError(
                f"Domain '{domain}' not in technology_set. "
                f"Available domains: {', '.join(self.domains.keys())}"
            )

        selection = self.domains[domain]
        if not selection.enabled:
            raise DiscreteChoiceError(f"Domain '{domain}' is disabled in technology_set")

        return ChoiceSet(alternatives=selection.alternatives)

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API-safe dict for JSON serialization.

        Returns a dict with camelCase keys matching the frontend TypeScript
        interface, suitable for Pydantic response models.

        Story 28.1 / AC-3: Convert frozen dataclass to dict for Pydantic response.
        """
        return {
            "version": self.version,
            "domains": {
                domain: {
                    "domain": dts.domain,
                    "enabled": dts.enabled,
                    "alternatives": [
                        {"id": alt.id, "name": alt.name, "attributes": alt.attributes}
                        for alt in dts.alternatives
                    ],
                    "referenceAlternativeId": dts.reference_alternative_id,
                    "costColumn": dts.cost_column,
                }
                for domain, dts in self.domains.items()
            },
        }


# ============================================================================
# Default technology set constants
# ============================================================================


def _default_heating_domain_config() -> DomainTechnologySet:
    """Factory returning French market default heating domain technology set.

    Emission values from ADEME Base Carbone V23.6:
    - Gas boiler: 0.227 kgCO2e/kWh PCI (natural gas combustion)
    - Heat pump: 0.057 kgCO2e/kWh (French electricity grid)
    - Electric resistance: 0.057 kgCO2e/kWh (same French grid factor)
    - Wood/pellet: 0.030 kgCO2e/kWh PCI (near carbon-neutral biogenic)

    Oil heating is NOT an alternative — banned for new installations
    in France since July 2022 (RE2020 regulation).

    Returns:
        DomainTechnologySet with 5 alternatives.

    Story 28.1, AC-3: Canonical French heating set for default API endpoint.
    """
    return DomainTechnologySet(
        domain="heating",
        enabled=True,
        alternatives=(
            Alternative(
                id="keep_current",
                name="Keep Current Heating",
                attributes={},
            ),
            Alternative(
                id="condensing_boiler",
                name="Condensing Boiler",
                attributes={
                    "heating_type": "gas",
                    "heating_age": 0,
                    "heating_emissions_kgco2_kwh": 0.227,
                },
            ),
            Alternative(
                id="heat_pump_air",
                name="Air Source Heat Pump",
                attributes={
                    "heating_type": "heat_pump",
                    "heating_age": 0,
                    "heating_emissions_kgco2_kwh": 0.057,
                },
            ),
            Alternative(
                id="heat_pump_ground",
                name="Ground Source Heat Pump",
                attributes={
                    "heating_type": "heat_pump",
                    "heating_age": 0,
                    "heating_emissions_kgco2_kwh": 0.057,
                },
            ),
            Alternative(
                id="district_heating",
                name="District Heating",
                attributes={
                    "heating_type": "district",
                    "heating_age": 0,
                },
            ),
        ),
        reference_alternative_id="keep_current",
        cost_column="heating_cost",
    )


def _default_vehicle_domain_config() -> DomainTechnologySet:
    """Factory returning French market default vehicle domain technology set.

    Returns:
        DomainTechnologySet with 6 alternatives.

    Story 28.1, AC-3: Canonical French vehicle set for default API endpoint.
    """
    return DomainTechnologySet(
        domain="vehicle",
        enabled=True,
        alternatives=(
            Alternative(
                id="keep_current",
                name="Keep Current Vehicle",
                attributes={},
            ),
            Alternative(
                id="petrol",
                name="Petrol Car",
                attributes={"vehicle_type": "petrol"},
            ),
            Alternative(
                id="diesel",
                name="Diesel Car",
                attributes={"vehicle_type": "diesel"},
            ),
            Alternative(
                id="hybrid",
                name="Hybrid Car",
                attributes={"vehicle_type": "hybrid"},
            ),
            Alternative(
                id="ev",
                name="Electric Vehicle",
                attributes={"vehicle_type": "ev"},
            ),
            Alternative(
                id="plug_in_hybrid",
                name="Plug-in Hybrid",
                attributes={"vehicle_type": "plug_in_hybrid"},
            ),
        ),
        reference_alternative_id="keep_current",
        cost_column="total_vehicle_cost",
    )


# Module-level constants for re-export
DEFAULT_HEATING_TECHNOLOGY_SET = _default_heating_domain_config()
DEFAULT_VEHICLE_TECHNOLOGY_SET = _default_vehicle_domain_config()

DEFAULT_TECHNOLOGY_SET = TechnologySet(
    version="fr-default-2026-04-26",
    domains={
        "heating": DEFAULT_HEATING_TECHNOLOGY_SET,
        "vehicle": DEFAULT_VEHICLE_TECHNOLOGY_SET,
    },
)


__all__ = [
    "DomainTechnologySet",
    "TechnologySet",
    "DEFAULT_HEATING_TECHNOLOGY_SET",
    "DEFAULT_VEHICLE_TECHNOLOGY_SET",
    "DEFAULT_TECHNOLOGY_SET",
]
