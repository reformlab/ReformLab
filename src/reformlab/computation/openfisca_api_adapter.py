"""Adapter that executes OpenFisca computations via the Python API.

Unlike ``OpenFiscaAdapter`` (pre-computed file mode), this adapter
runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.

All OpenFisca imports are lazy since ``openfisca-core`` is an optional
dependency.

Story 9.2: Added entity-aware result extraction to correctly handle
output variables belonging to different entity types (individu, menage,
famille, foyer_fiscal).

Story 9.3: Added periodicity-aware calculation dispatch. Monthly variables
use ``calculate_add()`` to sum sub-period values; yearly and eternity
variables use ``calculate()``. Period validation ensures valid 4-digit year.

Story 9.4: Added 4-entity PopulationData format support. Membership columns
on the person entity table (``{entity_key}_id`` and ``{entity_key}_role``)
express entity relationships for multi-person populations. The adapter
detects these columns, validates relationships, and produces a valid entity
dict passable to ``SimulationBuilder.build_from_entities()``.
"""

from __future__ import annotations

import difflib
import logging
import time
from typing import Any

import pyarrow as pa

from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_common import (
    _check_version,
    _detect_openfisca_version,
)
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

logger = logging.getLogger(__name__)

# Story 9.3: Valid OpenFisca DateUnit periodicity values (StrEnum).
# Sub-yearly periodicities use calculate_add(); year/eternity use calculate().
_VALID_PERIODICITIES = frozenset({
    "month", "year", "eternity", "day", "week", "weekday",
})
_CALCULATE_ADD_PERIODICITIES = frozenset({
    "month", "day", "week", "weekday",
})


def _periodicity_to_method_name(periodicity: str) -> str:
    """Map a DateUnit periodicity string to the OpenFisca calculation method name.

    Single source of truth for the ``calculate`` vs ``calculate_add`` dispatch
    decision. Sub-yearly periodicities (month, day, week, weekday) aggregate
    via ``calculate_add``; year and eternity use ``calculate`` directly.
    """
    return "calculate_add" if periodicity in _CALCULATE_ADD_PERIODICITIES else "calculate"


class OpenFiscaApiAdapter:
    """Adapter that executes OpenFisca computations via the Python API.

    Unlike ``OpenFiscaAdapter`` (pre-computed file mode), this adapter
    runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.
    """

    def __init__(
        self,
        *,
        country_package: str = "openfisca_france",
        output_variables: tuple[str, ...],
        skip_version_check: bool = False,
    ) -> None:
        if not output_variables:
            raise ApiMappingError(
                summary="Empty output_variables",
                reason="output_variables tuple is empty — no variables to compute",
                fix="Provide at least one valid output variable name.",
                invalid_names=(),
                valid_names=(),
            )
        self._country_package = country_package
        self._output_variables = output_variables

        if not skip_version_check:
            self._version = _detect_openfisca_version()
            _check_version(self._version)
        else:
            self._version = "unknown"

        self._tax_benefit_system: Any = None

    def version(self) -> str:
        """Return the detected OpenFisca-Core version string."""
        return self._version

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Run a live OpenFisca computation for the given inputs.

        Args:
            population: Input population data with entity tables.
            policy: Scenario parameters (applied as input-variable values).
            period: Computation period (integer year, e.g. 2025).

        Returns:
            A ``ComputationResult`` with output variables as a PyArrow Table.
            When output variables span multiple entities, ``entity_tables``
            contains per-entity tables keyed by entity plural name.

        Raises:
            ApiMappingError: If the period is invalid (not a 4-digit year
                in range [1000, 9999]).
        """
        # Story 9.3 AC-3: Period validation — FIRST check before any TBS operations.
        self._validate_period(period)

        start = time.monotonic()

        tbs = self._get_tax_benefit_system()
        self._validate_output_variables(tbs)

        # Story 9.2: Resolve entity grouping before building simulation (fail fast —
        # avoid expensive SimulationBuilder.build_from_entities() if entity
        # resolution fails due to incompatible country package).
        vars_by_entity = self._resolve_variable_entities(tbs)

        # Story 9.3 AC-1, AC-2, AC-6: Resolve periodicities before simulation
        # (fail fast — detect unsupported periodicity values early).
        var_periodicities = self._resolve_variable_periodicities(tbs)

        simulation = self._build_simulation(population, policy, period, tbs)
        entity_tables = self._extract_results_by_entity(
            simulation, period, vars_by_entity, var_periodicities
        )

        # Determine primary output_fields table for backward compatibility:
        # - Single entity → that entity's table
        # - Multiple entities → person-entity table (or first entity's table)
        output_fields = self._select_primary_output(entity_tables, tbs)

        elapsed = time.monotonic() - start

        # Only expose entity_tables for multi-entity results — keeps metadata
        # consistent with entity_tables (single-entity uses {} for backward compat).
        result_entity_tables = entity_tables if len(entity_tables) > 1 else {}
        output_entities = sorted(result_entity_tables.keys())
        entity_row_counts = {
            entity: table.num_rows for entity, table in result_entity_tables.items()
        }

        # Story 9.3 AC-5: Build calculation methods mapping from periodicities.
        # Uses _periodicity_to_method_name() — single source of truth for the
        # calculate vs calculate_add dispatch decision.
        calculation_methods: dict[str, str] = {
            var_name: _periodicity_to_method_name(periodicity)
            for var_name, periodicity in var_periodicities.items()
        }

        return ComputationResult(
            output_fields=output_fields,
            adapter_version=self._version,
            period=period,
            metadata={
                "timing_seconds": round(elapsed, 4),
                "row_count": output_fields.num_rows,
                "source": "api",
                "policy_name": policy.name,
                "country_package": self._country_package,
                "output_variables": list(self._output_variables),
                "output_entities": output_entities,
                "entity_row_counts": entity_row_counts,
                "variable_periodicities": dict(var_periodicities),
                "calculation_methods": calculation_methods,
            },
            entity_tables=result_entity_tables,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_tax_benefit_system(self) -> Any:
        """Lazily import the country package and cache the TaxBenefitSystem."""
        if self._tax_benefit_system is not None:
            return self._tax_benefit_system

        try:
            import importlib

            module = importlib.import_module(self._country_package)
        except ImportError:
            raise CompatibilityError(
                expected=self._country_package,
                actual="not-installed",
                details=(
                    f"Country package '{self._country_package}' is not installed. "
                    f"Install it with: uv add '{self._country_package}'. "
                    "See https://openfisca.org/doc/ for available country packages."
                ),
            )

        # Country packages expose the TBS via a conventional attribute.
        # openfisca_france → FranceTaxBenefitSystem (via CountryTaxBenefitSystem)
        tbs_class = getattr(module, "CountryTaxBenefitSystem", None)
        if tbs_class is None:
            # Fallback: try the generic TaxBenefitSystem attribute
            tbs_class = getattr(module, "TaxBenefitSystem", None)
        if tbs_class is None:
            raise CompatibilityError(
                expected=f"TaxBenefitSystem in {self._country_package}",
                actual="not found",
                details=(
                    f"Package '{self._country_package}' does not expose "
                    "'CountryTaxBenefitSystem' or 'TaxBenefitSystem'. "
                    "Verify the package is a valid OpenFisca country package."
                ),
            )

        self._tax_benefit_system = tbs_class()
        return self._tax_benefit_system

    def _validate_output_variables(self, tbs: Any) -> None:
        """Check that all requested output variables exist in the TBS."""
        known_variables = set(tbs.variables.keys())
        invalid = [v for v in self._output_variables if v not in known_variables]

        if not invalid:
            return

        suggestions: dict[str, list[str]] = {}
        known_list = sorted(known_variables)
        for name in invalid:
            matches = difflib.get_close_matches(name, known_list, n=3, cutoff=0.6)
            if matches:
                suggestions[name] = matches

        suggestion_lines = []
        for name in invalid:
            if name in suggestions:
                suggestion_lines.append(
                    f"  '{name}' → did you mean: {', '.join(suggestions[name])}?"
                )
            else:
                suggestion_lines.append(f"  '{name}' → no close matches found")

        raise ApiMappingError(
            summary="Unknown output variables",
            reason=(
                f"{len(invalid)} variable(s) not found in "
                f"{self._country_package} TaxBenefitSystem: "
                f"{', '.join(invalid)}"
            ),
            fix=(
                "Check variable names against the country package. "
                "Suggestions:\n" + "\n".join(suggestion_lines)
            ),
            invalid_names=tuple(invalid),
            valid_names=tuple(sorted(known_variables)),
            suggestions=suggestions,
        )

    # ------------------------------------------------------------------
    # Story 9.3: Period validation and periodicity-aware dispatch
    # ------------------------------------------------------------------

    def _validate_period(self, period: int) -> None:
        """Validate that the period is a 4-digit year in [1000, 9999].

        Story 9.3 AC-3: Called as the FIRST operation in ``compute()``,
        before any TBS queries or simulation construction.

        Raises:
            ApiMappingError: If the period is invalid.
        """
        if not (1000 <= period <= 9999):
            raise ApiMappingError(
                summary="Invalid period",
                reason=(
                    f"Period {period!r} is not a valid 4-digit year"
                ),
                fix=(
                    "Provide a positive integer year in range [1000, 9999], "
                    "e.g. 2024"
                ),
                invalid_names=(),
                valid_names=(),
            )

    def _resolve_variable_periodicities(
        self, tbs: Any
    ) -> dict[str, str]:
        """Detect the periodicity of each output variable from the TBS.

        Story 9.3 AC-1, AC-2, AC-6: Queries
        ``tbs.variables[var_name].definition_period`` for each output variable
        to determine whether ``calculate()`` or ``calculate_add()`` should
        be used.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping variable name to periodicity string
            (e.g. ``{"salaire_net": "month", "irpp": "year"}``).

        Raises:
            ApiMappingError: If a variable's periodicity cannot be determined
                or has an unexpected value.
        """
        periodicities: dict[str, str] = {}

        for var_name in self._output_variables:
            variable = tbs.variables.get(var_name)
            if variable is None:
                # Defensive — _validate_output_variables should have caught this.
                raise ApiMappingError(
                    summary="Cannot resolve variable periodicity",
                    reason=(
                        f"Variable '{var_name}' not found in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "Ensure the variable exists in the country package. "
                        "This may indicate the TBS was modified after validation."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            definition_period = getattr(variable, "definition_period", None)
            if definition_period is None:
                raise ApiMappingError(
                    summary="Cannot determine periodicity for variable",
                    reason=(
                        f"Variable '{var_name}' has no .definition_period "
                        f"attribute in {self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "This variable may not be properly defined in the "
                        "country package. Check the variable definition."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            # DateUnit is a StrEnum — string comparison works directly.
            periodicity_str = str(definition_period)
            if periodicity_str not in _VALID_PERIODICITIES:
                raise ApiMappingError(
                    summary="Unexpected periodicity for variable",
                    reason=(
                        f"Variable '{var_name}' has definition_period="
                        f"'{periodicity_str}', expected one of: "
                        f"{', '.join(sorted(_VALID_PERIODICITIES))}"
                    ),
                    fix=(
                        "This may indicate an incompatible OpenFisca version. "
                        "Check the OpenFisca compatibility matrix."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            periodicities[var_name] = periodicity_str

        logger.debug(
            "variable_periodicities=%s output_variables=%s",
            periodicities,
            list(self._output_variables),
        )

        return periodicities

    def _calculate_variable(
        self,
        simulation: Any,
        var_name: str,
        period_str: str,
        periodicity: str,
    ) -> Any:
        """Dispatch to the correct OpenFisca calculation method.

        Story 9.3 AC-1, AC-2, AC-6:
        - ``"month"``, ``"day"``, ``"week"``, ``"weekday"``
          → ``simulation.calculate_add(var, period)``
        - ``"year"``, ``"eternity"``
          → ``simulation.calculate(var, period)``

        Args:
            simulation: The OpenFisca simulation.
            var_name: Variable name to compute.
            period_str: Period string (e.g. "2024").
            periodicity: The variable's definition_period string.

        Returns:
            numpy.ndarray of computed values.
        """
        method = _periodicity_to_method_name(periodicity)
        logger.debug(
            "var=%s periodicity=%s method=%s period=%s",
            var_name, periodicity, method, period_str,
        )
        if method == "calculate_add":
            return simulation.calculate_add(var_name, period_str)
        else:
            return simulation.calculate(var_name, period_str)

    def _validate_policy_parameters(self, policy: PolicyConfig, tbs: Any) -> None:
        """Check that all policy parameter keys are valid input variables."""
        if not policy.policy:
            return

        known_variables = set(tbs.variables.keys())
        invalid = [k for k in policy.policy if k not in known_variables]

        if not invalid:
            return

        suggestions: dict[str, list[str]] = {}
        known_list = sorted(known_variables)
        for name in invalid:
            matches = difflib.get_close_matches(name, known_list, n=3, cutoff=0.6)
            if matches:
                suggestions[name] = matches

        suggestion_lines = []
        for name in invalid:
            if name in suggestions:
                suggestion_lines.append(
                    f"  '{name}' → did you mean: {', '.join(suggestions[name])}?"
                )
            else:
                suggestion_lines.append(f"  '{name}' → no close matches found")

        raise ApiMappingError(
            summary="Unknown policy parameter keys",
            reason=(
                f"{len(invalid)} parameter key(s) not found as variables in "
                f"{self._country_package} TaxBenefitSystem: "
                f"{', '.join(invalid)}"
            ),
            fix=(
                "PolicyConfig.policy keys must be valid OpenFisca variable names. "
                "Suggestions:\n" + "\n".join(suggestion_lines)
            ),
            invalid_names=tuple(invalid),
            valid_names=tuple(sorted(known_variables)),
            suggestions=suggestions,
        )

    def _build_simulation(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
        tbs: Any,
    ) -> Any:
        """Construct an OpenFisca Simulation from population and policy data."""
        from openfisca_core.simulation_builder import SimulationBuilder

        # Validate entity keys against TBS (accept both singular and plural)
        tbs_entity_keys = {entity.key for entity in tbs.entities}
        tbs_entity_plurals = {entity.plural for entity in tbs.entities}
        valid_names = tbs_entity_keys | tbs_entity_plurals
        unknown_entities = [
            key for key in population.tables if key not in valid_names
        ]
        if unknown_entities:
            raise ApiMappingError(
                summary="Unknown entity keys in population data",
                reason=(
                    f"Entity key(s) {', '.join(unknown_entities)} not found in "
                    f"{self._country_package} TaxBenefitSystem"
                ),
                fix=(
                    f"Population entity keys must be one of: "
                    f"{', '.join(sorted(tbs_entity_keys))}. "
                    "Check PopulationData.tables keys."
                ),
                invalid_names=tuple(unknown_entities),
                valid_names=tuple(sorted(tbs_entity_keys)),
            )

        # Validate policy parameters
        self._validate_policy_parameters(policy, tbs)

        # Build entity dict for SimulationBuilder.build_from_entities
        period_str = str(period)
        entities_dict = self._population_to_entity_dict(
            population, policy, period_str, tbs
        )

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        return simulation

    # ------------------------------------------------------------------
    # Story 9.4: 4-entity PopulationData format — membership columns
    # ------------------------------------------------------------------

    def _detect_membership_columns(
        self,
        person_table: pa.Table,
        tbs: Any,
    ) -> dict[str, tuple[str, str]]:
        """Detect membership columns on the person entity table.

        Story 9.4 AC-1, AC-3, AC-6: Checks for ``{entity.key}_id`` and
        ``{entity.key}_role`` columns for each group entity in the TBS.

        Args:
            person_table: The person entity PyArrow table.
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping group entity key to ``(id_column, role_column)`` tuple.
            Empty dict if no membership columns are detected (backward compat).

        Raises:
            ApiMappingError: If membership columns are incomplete (all-or-nothing)
                or unpaired (_id without _role or vice versa).
        """
        col_names = set(person_table.column_names)

        # Identify group entities from TBS
        group_entity_keys: list[str] = []
        for entity in tbs.entities:
            if not getattr(entity, "is_person", False):
                group_entity_keys.append(entity.key)

        # Check for membership column presence
        detected: dict[str, tuple[str, str]] = {}
        has_any_id = False
        has_any_role = False
        unpaired: list[str] = []
        present_pairs: list[str] = []
        missing_pairs: list[str] = []

        for entity_key in group_entity_keys:
            id_col = f"{entity_key}_id"
            role_col = f"{entity_key}_role"
            has_id = id_col in col_names
            has_role = role_col in col_names

            if has_id:
                has_any_id = True
            if has_role:
                has_any_role = True

            if has_id and has_role:
                detected[entity_key] = (id_col, role_col)
                present_pairs.append(entity_key)
            elif has_id and not has_role:
                unpaired.append(
                    f"'{id_col}' present but '{role_col}' missing"
                )
            elif has_role and not has_id:
                unpaired.append(
                    f"'{role_col}' present but '{id_col}' missing"
                )
            else:
                missing_pairs.append(entity_key)

        # No membership columns at all → backward compatible
        if not has_any_id and not has_any_role:
            return {}

        # Unpaired columns: _id without _role or vice versa
        if unpaired:
            raise ApiMappingError(
                summary="Unpaired membership column",
                reason=(
                    f"Membership columns must come in pairs "
                    f"({{entity_key}}_id + {{entity_key}}_role). "
                    f"Found: {'; '.join(unpaired)}"
                ),
                fix=(
                    "Add the missing paired column for each membership column. "
                    "Both _id and _role are required for each group entity."
                ),
                invalid_names=tuple(unpaired),
                valid_names=tuple(
                    f"{ek}_id, {ek}_role" for ek in group_entity_keys
                ),
            )

        # All-or-nothing: if any membership columns exist, all group entities
        # must have complete pairs
        if missing_pairs:
            raise ApiMappingError(
                summary="Incomplete entity membership columns",
                reason=(
                    f"Found membership columns for: "
                    f"{', '.join(present_pairs)}. "
                    f"Missing membership columns for: "
                    f"{', '.join(missing_pairs)}. "
                    f"All group entities must have _id and _role columns "
                    f"when any membership columns are present."
                ),
                fix=(
                    f"Add {{entity_key}}_id and {{entity_key}}_role columns "
                    f"for: {', '.join(missing_pairs)}"
                ),
                invalid_names=tuple(missing_pairs),
                valid_names=tuple(group_entity_keys),
            )

        return detected

    def _resolve_valid_role_keys(
        self,
        tbs: Any,
    ) -> dict[str, frozenset[str]]:
        """Build a mapping of entity key → valid role keys from the TBS.

        Story 9.4 AC-4: Uses ``role.plural or role.key`` to match the dict
        keys expected by ``SimulationBuilder.build_from_entities()``.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping group entity key to frozenset of valid role keys.
        """
        valid_roles: dict[str, frozenset[str]] = {}

        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                continue

            role_keys: set[str] = set()
            roles = getattr(entity, "roles", ())
            for role in roles:
                plural = getattr(role, "plural", None)
                key = getattr(role, "key", None)
                role_dict_key = plural or key
                if role_dict_key:
                    role_keys.add(role_dict_key)

            valid_roles[entity.key] = frozenset(role_keys)

        return valid_roles

    def _validate_entity_relationships(
        self,
        person_table: pa.Table,
        membership_cols: dict[str, tuple[str, str]],
        valid_roles: dict[str, frozenset[str]],
    ) -> None:
        """Validate membership column values for nulls and invalid roles.

        Story 9.4 AC-3, AC-4, AC-5: Checks every membership column for null
        values and validates role values against the TBS role definitions.

        Args:
            person_table: The person entity PyArrow table.
            membership_cols: Detected membership columns per group entity.
            valid_roles: Valid role keys per group entity.

        Raises:
            ApiMappingError: If null values or invalid role values are found.
        """
        for entity_key, (id_col, role_col) in membership_cols.items():
            # AC-5: Null check on _id column.
            # Use a vectorised filter to get the first null index rather than
            # iterating element-by-element with .as_py() per row — the Python
            # for-loop is only reached on the exceptional error path, but keeping
            # it vectorised keeps the code consistent and avoids any O(n) per-
            # element overhead even on validation failures.
            id_array = person_table.column(id_col)
            null_mask = pa.compute.is_null(id_array)
            if pa.compute.any(null_mask).as_py():
                # Vectorised first-index extraction — one .as_py() call total.
                null_positions = pa.compute.filter(
                    pa.array(range(len(id_array))), null_mask
                )
                first_null = null_positions[0].as_py()
                raise ApiMappingError(
                    summary="Null value in membership column",
                    reason=(
                        f"Column '{id_col}' has null value at "
                        f"row index {first_null}. All membership columns "
                        f"must have non-null values."
                    ),
                    fix=(
                        f"Ensure every person has a valid "
                        f"{entity_key} group assignment in "
                        f"'{id_col}'."
                    ),
                    invalid_names=(id_col,),
                    valid_names=(),
                )

            # AC-5: Null check on _role column.
            role_array = person_table.column(role_col)
            null_mask = pa.compute.is_null(role_array)
            if pa.compute.any(null_mask).as_py():
                null_positions = pa.compute.filter(
                    pa.array(range(len(role_array))), null_mask
                )
                first_null = null_positions[0].as_py()
                raise ApiMappingError(
                    summary="Null value in membership column",
                    reason=(
                        f"Column '{role_col}' has null value at "
                        f"row index {first_null}. All membership columns "
                        f"must have non-null values."
                    ),
                    fix=(
                        f"Ensure every person has a valid role "
                        f"in '{role_col}'."
                    ),
                    invalid_names=(role_col,),
                    valid_names=(),
                )

            # AC-4: Role value validation — check unique values only (typically ≤4
            # distinct roles per entity regardless of population size) to avoid
            # an O(n) scan over all person records.
            entity_valid_roles = valid_roles.get(entity_key, frozenset())
            if entity_valid_roles:
                for value in pa.compute.unique(role_array).to_pylist():
                    if value not in entity_valid_roles:
                        raise ApiMappingError(
                            summary="Invalid role value",
                            reason=(
                                f"Role value '{value}' in column "
                                f"'{role_col}' is not valid for entity "
                                f"'{entity_key}'. Valid roles: "
                                f"{sorted(entity_valid_roles)}"
                            ),
                            fix=(
                                f"Use one of the valid role values for "
                                f"'{entity_key}': "
                                f"{sorted(entity_valid_roles)}"
                            ),
                            invalid_names=(str(value),),
                            valid_names=tuple(sorted(entity_valid_roles)),
                        )

    def _population_to_entity_dict(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period_str: str,
        tbs: Any,
    ) -> dict[str, Any]:
        """Convert PopulationData tables to the dict format expected by OpenFisca.

        OpenFisca's ``build_from_entities`` expects **plural** entity keys::

            {
                "individus": {
                    "person_0": {"salaire_de_base": {"2024": 30000.0}},
                    ...
                },
                "menages": {
                    "menage_0": {"personne_de_reference": ["person_0"]},
                    ...
                }
            }

        PopulationData tables may use either singular (entity.key) or plural
        (entity.plural) keys.  This method normalises to plural.

        Story 9.4: When membership columns are detected on the person table
        (``{entity_key}_id`` and ``{entity_key}_role``), the method switches
        to 4-entity mode — building group entity instances with role
        assignments from the membership columns instead of treating every
        table as an independent entity with period-wrapped columns.
        """
        result: dict[str, Any] = {}

        # Step 1: Build key→plural mapping for normalisation
        key_to_plural = {entity.key: entity.plural for entity in tbs.entities}
        plural_set = set(key_to_plural.values())

        # Step 2: Identify the person entity
        person_entity: Any = None
        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                person_entity = entity
                break

        person_entity_plural = person_entity.plural if person_entity else None

        # Step 2b: Find person_table_key in population.tables
        person_table_key: str | None = None
        if person_entity is not None:
            if person_entity.key in population.tables:
                person_table_key = person_entity.key
            elif person_entity.plural in population.tables:
                person_table_key = person_entity.plural

        # Step 3: Detect membership columns
        membership_cols: dict[str, tuple[str, str]] = {}
        if person_table_key is not None:
            person_table = population.tables[person_table_key]
            membership_cols = self._detect_membership_columns(person_table, tbs)

        # Step 4: No membership columns → execute existing all-tables loop
        if not membership_cols:
            for entity_key, table in population.tables.items():
                # Normalise to plural key
                plural_key = key_to_plural.get(entity_key, entity_key)
                if entity_key in plural_set:
                    plural_key = entity_key

                entity_dict: dict[str, Any] = {}
                columns = table.column_names
                num_rows = table.num_rows

                for i in range(num_rows):
                    instance_id = f"{entity_key}_{i}"
                    instance_data: dict[str, Any] = {}

                    for col in columns:
                        value = table.column(col)[i].as_py()
                        instance_data[col] = {period_str: value}

                    entity_dict[instance_id] = instance_data

                result[plural_key] = entity_dict

            # Inject policy parameters
            if (
                policy.policy
                and person_entity_plural
                and person_entity_plural in result
            ):
                for instance_id in result[person_entity_plural]:
                    for param_key, param_value in policy.policy.items():
                        result[person_entity_plural][instance_id][param_key] = {
                            period_str: param_value
                        }

            return result

        # Step 5: 4-entity mode — membership columns detected
        # Defensive: person_table_key should always be non-None here (membership
        # columns require a person table), but assert would be stripped by -O and
        # produce a cryptic KeyError. Raise ApiMappingError explicitly instead.
        if person_table_key is None:
            raise ApiMappingError(
                summary="Person entity table not found in population",
                reason=(
                    "Membership columns were detected but no table keyed by the "
                    "person entity singular or plural name was found in "
                    "population.tables."
                ),
                fix=(
                    "Include the person entity table (e.g. 'individu' or "
                    "'individus') in PopulationData.tables when using membership "
                    "columns."
                ),
                invalid_names=(),
                valid_names=(),
            )
        person_table = population.tables[person_table_key]

        # Step 5a: Resolve valid role keys
        valid_roles = self._resolve_valid_role_keys(tbs)

        # Step 5b: Validate entity relationships
        self._validate_entity_relationships(person_table, membership_cols, valid_roles)

        # Step 5c: Build set of membership column names to exclude from period-wrapping
        membership_col_names: set[str] = set()
        for id_col, role_col in membership_cols.values():
            membership_col_names.add(id_col)
            membership_col_names.add(role_col)

        # Step 5d: Build person instances FROM PERSON TABLE ONLY.
        # Pre-materialise non-membership columns as Python lists once to avoid
        # O(n×c) scalar-boxing inside the row loop (c = variable column count).
        var_columns: dict[str, list[Any]] = {
            col: person_table.column(col).to_pylist()
            for col in person_table.column_names
            if col not in membership_col_names
        }
        person_dict: dict[str, Any] = {
            f"{person_table_key}_{i}": {
                col: {period_str: vals[i]}
                for col, vals in var_columns.items()
            }
            for i in range(person_table.num_rows)
        }

        # Defensive: person_entity_plural should always be non-None for valid TBS
        # instances, but `assert` is stripped by -O and `result[None] = ...` would
        # silently corrupt the entity dict. Raise ApiMappingError explicitly.
        if person_entity_plural is None:
            raise ApiMappingError(
                summary="Cannot determine person entity plural name",
                reason=(
                    "The person entity in the TaxBenefitSystem has no .plural "
                    "attribute. This indicates an incompatible OpenFisca version "
                    "or malformed TBS."
                ),
                fix="Check the OpenFisca compatibility matrix.",
                invalid_names=(),
                valid_names=(),
            )
        result[person_entity_plural] = person_dict

        # Step 5e: Build group entity instances from membership columns.
        # Single-pass O(n) approach: materialise each id/role array to a Python
        # list once, then group persons by (group_id, role_key) in one iteration.
        # The original O(n×g) nested loop (one inner scan per distinct group ID)
        # would take O(n×g) = O(250k × 100k) ≈ 25 billion ops for a realistic
        # French population — this replaces it with O(n) regardless of group count.
        for group_entity_key, (id_col, role_col) in membership_cols.items():
            id_array = person_table.column(id_col)
            role_array = person_table.column(role_col)

            # Materialise ONCE to Python lists — avoids repeated .as_py() per element.
            id_list = id_array.to_pylist()
            role_list = role_array.to_pylist()
            sorted_group_ids = sorted(set(id_list))

            # Single O(n) pass: group person IDs by (group_id, role_key)
            role_assignments_by_group: dict[Any, dict[str, list[str]]] = {}
            for i, (gid, rkey) in enumerate(zip(id_list, role_list)):
                person_id = f"{person_table_key}_{i}"
                role_assignments_by_group.setdefault(gid, {}).setdefault(
                    rkey, []
                ).append(person_id)

            group_dict: dict[str, Any] = {
                f"{group_entity_key}_{group_id}": role_assignments_by_group.get(
                    group_id, {}
                )
                for group_id in sorted_group_ids
            }

            group_plural = key_to_plural[group_entity_key]
            result[group_plural] = group_dict

        # Step 5f: Merge group entity table variables (if present)
        for group_entity_key, (id_col, _role_col) in membership_cols.items():
            # Check if a group entity table exists in population.tables
            group_table: pa.Table | None = None
            group_table_key: str | None = None
            group_plural = key_to_plural[group_entity_key]

            if group_entity_key in population.tables and group_entity_key != person_table_key:
                group_table = population.tables[group_entity_key]
                group_table_key = group_entity_key
            elif group_plural in population.tables and group_plural != person_table_key:
                group_table = population.tables[group_plural]
                group_table_key = group_plural

            if group_table is None:
                continue

            # Get sorted distinct group IDs from person table's _id column
            id_array = person_table.column(id_col)
            sorted_group_ids = sorted(pa.compute.unique(id_array).to_pylist())

            # Validate row count match
            if group_table.num_rows != len(sorted_group_ids):
                raise ApiMappingError(
                    summary="Group entity table row count mismatch",
                    reason=(
                        f"Group entity table '{group_table_key}' has "
                        f"{group_table.num_rows} rows but the person table "
                        f"has {len(sorted_group_ids)} distinct "
                        f"'{id_col}' values. Row counts must match."
                    ),
                    fix=(
                        f"Ensure the '{group_table_key}' table has exactly "
                        f"{len(sorted_group_ids)} rows, one per distinct "
                        f"group ID in the person table's '{id_col}' column."
                    ),
                    invalid_names=(str(group_table_key),),
                    valid_names=(),
                )

            # Positional match: row i → sorted_group_ids[i]
            # ⚠️ ORDERING ASSUMPTION: group table rows must be ordered by ascending
            # {entity_key}_id value from the person table. Mismatched order causes
            # silent per-row value swapping (no error raised). Log a warning so
            # this assumption is visible in structured logs during debugging.
            logger.warning(
                "event=group_entity_table_positional_merge "
                "entity=%s table_key=%s sorted_ids=%s "
                "assumption=rows_ordered_by_ascending_group_id",
                group_entity_key,
                group_table_key,
                sorted_group_ids,
            )
            for i, group_id in enumerate(sorted_group_ids):
                instance_id = f"{group_entity_key}_{group_id}"
                for col in group_table.column_names:
                    value = group_table.column(col)[i].as_py()
                    result[group_plural][instance_id][col] = {period_str: value}

        # Step 5g: Inject policy parameters into person entity instances
        if policy.policy and person_entity_plural in result:
            for instance_id in result[person_entity_plural]:
                for param_key, param_value in policy.policy.items():
                    result[person_entity_plural][instance_id][param_key] = {
                        period_str: param_value
                    }

        return result

    # ------------------------------------------------------------------
    # Story 9.2: Entity-aware result extraction
    # ------------------------------------------------------------------

    def _resolve_variable_entities(
        self, tbs: Any
    ) -> dict[str, list[str]]:
        """Group output variables by their entity's plural name.

        Queries ``tbs.variables[var_name].entity`` to determine which entity
        each output variable belongs to, then groups them.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping entity plural name to list of variable names.
            E.g. ``{"individus": ["salaire_net"], "foyers_fiscaux": ["irpp"]}``.

        Raises:
            ApiMappingError: If a variable's entity cannot be determined.
        """
        vars_by_entity: dict[str, list[str]] = {}

        for var_name in self._output_variables:
            variable = tbs.variables.get(var_name)
            if variable is None:
                # Should not happen — _validate_output_variables runs first.
                # Defensive guard for edge cases.
                raise ApiMappingError(
                    summary="Cannot resolve variable entity",
                    reason=(
                        f"Variable '{var_name}' not found in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "Ensure the variable exists in the country package. "
                        "This may indicate the TBS was modified after validation."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            entity = getattr(variable, "entity", None)
            if entity is None:
                raise ApiMappingError(
                    summary="Cannot determine entity for variable",
                    reason=(
                        f"Variable '{var_name}' has no .entity attribute in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "This variable may not be properly defined in the "
                        "country package. Check the variable definition."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            entity_plural = getattr(entity, "plural", None)
            if entity_plural is None:
                # entity.plural is required — silently falling back to entity.key
                # would produce wrong plural keys (e.g. "foyer_fiscal" instead of
                # "foyers_fiscaux") causing subtle downstream lookup failures.
                # This path only occurs with a malformed/incompatible TBS.
                entity_key = getattr(entity, "key", None)
                raise ApiMappingError(
                    summary="Cannot determine entity plural name for variable",
                    reason=(
                        f"Variable '{var_name}' entity has no .plural attribute"
                        + (
                            f" (entity.key={entity_key!r})"
                            if entity_key
                            else ", no .key attribute either"
                        )
                    ),
                    fix=(
                        "This may indicate an incompatible OpenFisca version. "
                        "Check the OpenFisca compatibility matrix."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            vars_by_entity.setdefault(entity_plural, []).append(var_name)

        logger.debug(
            "entity_variable_mapping=%s output_variables=%s",
            {k: v for k, v in vars_by_entity.items()},
            list(self._output_variables),
        )

        return vars_by_entity

    def _extract_results_by_entity(
        self,
        simulation: Any,
        period: int,
        vars_by_entity: dict[str, list[str]],
        variable_periodicities: dict[str, str],
    ) -> dict[str, pa.Table]:
        """Extract output variables grouped by entity into per-entity tables.

        For each entity group, calls the appropriate calculation method
        (``calculate()`` or ``calculate_add()``) for its variables and
        builds a ``pa.Table`` per entity. Arrays within an entity group
        share the same length (entity instance count).

        Story 9.3: Uses ``_calculate_variable()`` for periodicity-aware
        dispatch instead of calling ``simulation.calculate()`` directly.

        Args:
            simulation: The completed OpenFisca simulation.
            period: Computation period (integer year).
            vars_by_entity: Output variables grouped by entity plural name
                (from ``_resolve_variable_entities``).
            variable_periodicities: Periodicity per variable
                (from ``_resolve_variable_periodicities``).

        Returns:
            Dict mapping entity plural name to a PyArrow Table containing
            that entity's output variables.
        """
        period_str = str(period)
        entity_tables: dict[str, pa.Table] = {}

        for entity_plural, var_names in vars_by_entity.items():
            arrays: dict[str, pa.Array] = {}
            for var_name in var_names:
                periodicity = variable_periodicities[var_name]
                numpy_array = self._calculate_variable(
                    simulation, var_name, period_str, periodicity
                )
                arrays[var_name] = pa.array(numpy_array)
            entity_tables[entity_plural] = pa.table(arrays)

        return entity_tables

    def _select_primary_output(
        self,
        entity_tables: dict[str, pa.Table],
        tbs: Any,
    ) -> pa.Table:
        """Select the primary output_fields table for backward compatibility.

        When all variables belong to one entity, returns that entity's table.
        When variables span multiple entities, returns the person-entity table
        (or the first entity's table if no person entity is present).

        Args:
            entity_tables: Per-entity output tables.
            tbs: The loaded TaxBenefitSystem.

        Returns:
            A single PyArrow Table to use as ``output_fields``.
        """
        if len(entity_tables) == 1:
            return next(iter(entity_tables.values()))

        # Find the person entity plural name
        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                person_plural = entity.plural
                if person_plural in entity_tables:
                    return entity_tables[person_plural]

        # Fallback: return the first entity's table
        return next(iter(entity_tables.values()))
