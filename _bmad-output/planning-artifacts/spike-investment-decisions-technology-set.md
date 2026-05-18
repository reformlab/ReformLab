# ADR: Technology-Set as a First-Class Concept for Investment Decisions

**Status:** Proposed (Architect Spike — Story 28.0)
**Date:** 2026-05-17
**Author:** Architect Agent (with bmad-architect)
**Epic:** EPIC-28
**Related Stories:** 28.1-28.5 (to be sized after this ADR is approved)

---

## Context

Investment decisions currently model household choices using the discrete choice subsystem (`DiscreteChoiceStep`, `VehicleInvestmentDomain`, `HeatingInvestmentDomain`). However, the analyst cannot explicitly declare which technologies are *in scope* for a given scenario — the domain's full alternative list is always available.

This ADR addresses the user need to:
1. Declare a scoped technology set per domain (e.g., "EV and hybrid only, no petrol")
2. Track incumbent technologies in the population for multi-period state transitions
3. Write chosen technologies back into the population for subsequent years
4. Record technology provenance in the manifest for reproducibility

---

## Decision Drivers

- **User Control:** Analysts need to constrain the technology choice space (e.g., policy analysis of "EV-only" scenarios)
- **Multi-Period Realism:** Households have incumbent technologies that affect replacement decisions (e.g., gas boiler → heat pump is different from new build → heat pump)
- **Reproducibility:** The technology set must be recorded in manifests for audit and comparison
- **Backward Compatibility:** Existing scenarios and populations without incumbent columns must continue to work
- **Adapter Isolation:** Changes should live above `ComputationAdapter` when possible
- **Determinism:** All runs must be reproducible; technology configuration is part of the scenario definition

---

## Decisions Made

### Decision 1: What does `EngineConfig.technology_set` look like?

**Chosen Option:** Per-domain technology selection with alternative ID lists.

**Rationale:**
- Simple, explicit, and easy to validate against known alternatives
- Avoids over-engineering taste parameter overrides in the initial implementation (deferred to Story 28.4)
- Aligns with existing `Alternative` and `ChoiceSet` patterns

**Rejected Alternatives:**
- *Per-domain alternative lists with taste overrides:* More complex; taste parameters already handled via `TasteParameters` in domains (Story 21.7). Defer taste override UI to Story 28.4.
- *Rich configuration object with weights:* Over-engineering for MVP; technology scoping is the primary user need

**Schema Definition:**

```python
# Backend (src/reformlab/discrete_choice/types.py)

@dataclass(frozen=True)
class TechnologySet:
    """Scoped technology set per domain for investment decisions.

    Defines which alternatives are available for choice in each enabled domain.
    When None or empty, defaults to the domain's full alternative list.

    Attributes:
        domains: Mapping from domain name to technology selection.
            Keys: "vehicle", "heating", etc.
            Values: DomainTechnologySelection

    Example:
        TechnologySet(
            domains={
                "vehicle": DomainTechnologySelection(
                    alternative_ids=("ev", "hybrid", "keep_current"),
                ),
                "heating": DomainTechnologySelection(
                    alternative_ids=("heat_pump", "gas_boiler", "keep_current"),
                ),
            }
        )
    """

    domains: dict[str, DomainTechnologySelection]

    def to_choice_set(self, domain: str, full_alternatives: tuple[Alternative, ...]) -> ChoiceSet:
        """Return a ChoiceSet filtered to this technology set's alternatives for the domain.

        Args:
            domain: Domain name (e.g., "vehicle").
            full_alternatives: Full alternative list from the domain.

        Returns:
            ChoiceSet with only the alternatives in this technology set.

        Raises:
            DiscreteChoiceError: If domain not in technology set or alternative IDs invalid.
        """
        if domain not in self.domains:
            # Return full choice set when domain not constrained
            return ChoiceSet(alternatives=full_alternatives)

        selection = self.domains[domain]
        valid_ids = {alt.id for alt in full_alternatives}
        unknown_ids = set(selection.alternative_ids) - valid_ids
        if unknown_ids:
            raise DiscreteChoiceError(
                f"Unknown alternative IDs in technology_set['{domain}']: "
                f"{sorted(unknown_ids)}. Valid: {sorted(valid_ids)}"
            )

        filtered = tuple(
            alt for alt in full_alternatives if alt.id in selection.alternative_ids
        )
        return ChoiceSet(alternatives=filtered)


@dataclass(frozen=True)
class DomainTechnologySelection:
    """Technology selection for a single domain.

    Attributes:
        alternative_ids: Ordered tuple of alternative IDs to include in the choice set.
            Must be subset of the domain's full alternative list.
    """

    alternative_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.alternative_ids:
            raise ValueError("alternative_ids must be non-empty")
```

**Frontend Schema (frontend/src/types/workspace.ts):**

```typescript
export interface DomainTechnologySelection {
  alternativeIds: string[];  // e.g., ["ev", "hybrid", "keep_current"]
}

export interface TechnologySet {
  domains: Record<string, DomainTechnologySelection>;  // key: domain name
}
```

**Empty Technology Set Semantics:**
- `technology_set: null` → All domain alternatives available (default)
- `technology_set: { domains: {} }` → Same as null (no constraints)
- `technology_set: { domains: { "vehicle": {...} } }` → Only vehicle constrained; heating uses full list

**Construction Example:**

```python
# French market default with EV-only scenario
ev_only_tech_set = TechnologySet(
    domains={
        "vehicle": DomainTechnologySelection(
            alternative_ids=("keep_current", "buy_ev", "buy_no_vehicle"),
        ),
        # Heating not constrained — uses full list from HeatingDomainConfig
    }
)
```

---

### Decision 2: What's the population schema delta?

**Chosen Option:** Per-domain optional columns with PyArrow dictionary encoding.

**Rationale:**
- Simple, queryable, aligns with existing domain pattern
- Dictionary encoding (`pa.dictionary(pa.int32(), pa.utf8())`) provides O(1) categorical filtering and efficient storage
- Optional columns enable backward compatibility

**Rejected Alternatives:**
- *Single structured map column:* PyArrow map type is less common, requires special handling; less queryable
- *JSON string column:* Loses type safety and filtering efficiency

**Schema Definition:**

```python
# Population schema for menage entity table
# New columns (optional, nullable):

incumbent_vehicle: pa.dictionary(pa.int32(), pa.utf8())  # or null
incumbent_heating: pa.dictionary(pa.int32(), pa.utf8())  # or null

# Validation rules:
# 1. Column is optional (may be absent from schema)
# 2. When present, values must be in domain's alternative_ids
# 3. Null values represent "unknown" or "not applicable"
# 4. Empty strings are invalid (use null instead)
```

**Column Naming Convention:**
- Pattern: `incumbent_{domain}` where `{domain}` matches `DecisionDomain.name`
- Examples: `incumbent_vehicle`, `incumbent_heating`
- Future domains: `incumbent_insulation`, `incumbent_solar`, etc.

**PyArrow Dictionary Encoding Benefits:**
- Efficient storage: categorical values stored as integer indices
- O(1) filtering: `table.filter(pa.compute.field("incumbent_vehicle") == "ev")`
- Null-safe: missing values represented cleanly
- Deterministic: dictionary indices are stable after sort

**Optional vs Required Semantics:**
- **Optional (MVP):** Column may be absent; scenarios without decisions or with legacy populations skip validation
- **Required (Future):** When investment decisions are enabled, column must exist (enforced in Story 28.2 validation)

**Default Value Strategy:**
- When column exists but has null values, default to the domain's reference alternative (e.g., "keep_current")
- Explicit user override available in Story 28.4 wizard UI

**Validation Behavior (Backward Compatibility):**

| Scenario | Investment Decisions Enabled | Incumbent Column Present | Validation Behavior |
|----------|------------------------------|-------------------------|---------------------|
| Legacy population | No | No | Silent pass — no validation needed |
| Legacy population | Yes | No | Warning in metadata; default incumbents applied |
| New population | Yes | Yes | Full validation — error on invalid values |
| New population | No | Yes | Silent — column ignored |

**Validation Code Sketch (Story 28.2):**

```python
def validate_incumbent_column(
    table: pa.Table,
    domain: DecisionDomain,
    column_name: str,
) -> None:
    """Validate incumbent technology column values.

    Args:
        table: Entity table (e.g., menage).
        domain: Decision domain with alternatives.
        column_name: Column name (e.g., "incumbent_vehicle").

    Raises:
        DiscreteChoiceError: If column values are not in domain's alternative_ids.
    """
    if column_name not in table.column_names:
        return  # Optional column

    column = table.column(column_name)
    valid_ids = domain.alternative_ids  # tuple[str, ...]

    # Extract unique non-null values
    import pyarrow.compute as pc
    unique_values = pc.unique(column).to_pylist()
    unique_values = [v for v in unique_values if v is not None]

    invalid_ids = set(unique_values) - set(valid_ids)
    if invalid_ids:
        raise DiscreteChoiceError(
            f"Invalid incumbent technology IDs in column '{column_name}': "
            f"{sorted(invalid_ids)}. Valid: {sorted(valid_ids)}"
        )
```

---

### Decision 3: How does `DiscreteChoiceStep` write back?

**Chosen Option:** Extend existing `*StateUpdateStep` pattern with incumbent column updates.

**Rationale:**
- Reuses proven pattern from `VehicleStateUpdateStep` and `HeatingStateUpdateStep`
- Consistent with existing `apply_choices_to_population` utility
- Clear separation of concerns: `DiscreteChoiceStep` computes choices, `*StateUpdateStep` writes back

**Rejected Alternatives:**
- *Generic writeback step:* Less flexible, may not fit all domain semantics
- *In-place mutation:* Violates immutability principle of `PopulationData`

**Writeback Contract:**

```python
# New step in discrete_choice/state_update.py

class IncumbentUpdateStep:
    """Orchestrator step that writes chosen technologies back to population as incumbents.

    Reads ChoiceResult from state, updates the incumbent_{domain} column in the
    population entity table, and returns updated YearState. Safe to run only
    when investment decisions are enabled and incumbent column exists.

    Story 28.3: Wire DiscreteChoiceStep outputs into population frame.
    """

    __slots__ = (
        "_domain",
        "_population_key",
        "_incumbent_column",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        domain: DecisionDomain,
        population_key: str = "population_data",
        incumbent_column: str | None = None,  # auto-derived from domain.name if None
        name: str | None = None,
        depends_on: tuple[str, ...] = ("logit_choice",),
        description: str | None = None,
    ) -> None:
        self._domain = domain
        self._population_key = population_key
        self._incumbent_column = incumbent_column or f"incumbent_{domain.name}"
        self._name = name or f"{domain.name}_incumbent_update"
        self._depends_on = depends_on
        self._description = description or (
            f"Update {self._incumbent_column} column from choice result"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        return self._depends_on

    @property
    def description(self) -> str:
        return self._description

    def execute(self, year: int, state: YearState) -> YearState:
        """Update incumbent column in population from choice result.

        Args:
            year: Current simulation year.
            state: Current year state with ChoiceResult.

        Returns:
            New YearState with updated population.

        Raises:
            DiscreteChoiceError: If required data missing or column invalid.
        """
        from reformlab.computation.types import PopulationData
        from reformlab.discrete_choice.types import ChoiceResult

        # Read ChoiceResult
        choice_result = state.data.get(DISCRETE_CHOICE_RESULT_KEY)
        if not isinstance(choice_result, ChoiceResult):
            raise DiscreteChoiceError(
                f"ChoiceResult not found in YearState.data['{DISCRETE_CHOICE_RESULT_KEY}']",
                year=year,
                step_name=self._name,
            )

        # Read PopulationData
        population = state.data.get(self._population_key)
        if not isinstance(population, PopulationData):
            raise DiscreteChoiceError(
                f"PopulationData not found in YearState.data['{self._population_key}']",
                year=year,
                step_name=self._name,
            )

        # Determine entity key from domain config
        entity_key = getattr(
            getattr(self._domain, "config", None),
            "entity_key",
            "menage",  # default for vehicle/heating
        )

        if entity_key not in population.tables:
            raise DiscreteChoiceError(
                f"Entity key '{entity_key}' not found in population tables",
                year=year,
                step_name=self._name,
            )

        table = population.tables[entity_key]
        n = table.num_rows

        # Check if incumbent column exists
        if self._incumbent_column not in table.column_names:
            # Column doesn't exist — add it with default values
            # Use domain's reference alternative (e.g., "keep_current")
            ref_alternative = self._reference_alternative()
            default_col = pa.array([ref_alternative] * n, type=pa.utf8())
            table = table.append_column(self._incumbent_column, default_col)

        # Extract chosen alternatives
        chosen_list = choice_result.chosen.to_pylist()

        if len(chosen_list) != n:
            raise DiscreteChoiceError(
                f"ChoiceResult length ({len(chosen_list)}) does not match "
                f"entity table row count ({n})"
            )

        # Update incumbent column with chosen values
        new_incumbent_col = pa.array(chosen_list, type=pa.utf8())
        col_idx = table.column_names.index(self._incumbent_column)
        updated_table = table.set_column(col_idx, self._incumbent_column, new_incumbent_col)

        # Build new population
        new_tables = dict(population.tables)
        new_tables[entity_key] = updated_table
        updated_population = PopulationData(
            tables=new_tables,
            metadata=dict(population.metadata),
        )

        # Update state
        new_data = dict(state.data)
        new_data[self._population_key] = updated_population

        logger.info(
            "year=%d step_name=%s n_households=%d column=%s event=incumbent_updated",
            year,
            self._name,
            n,
            self._incumbent_column,
        )

        return replace(state, data=new_data)

    def _reference_alternative(self) -> str:
        """Return reference alternative for default incumbent value.

        Defaults to "keep_current" for vehicle/heating domains.
        Future domains may override.
        """
        return "keep_current"
```

**Interaction with Existing `*StateUpdateStep` Classes:**

The pipeline for each domain becomes:
1. `DiscreteChoiceStep` → computes choices, stores `ChoiceResult` in state
2. `LogitChoiceStep` → draws choices from probabilities, overwrites `ChoiceResult`
3. `DecisionRecordStep` → snapshots `ChoiceResult` into decision log
4. `{Domain}StateUpdateStep` → updates population attributes (e.g., `vehicle_type`, `vehicle_age`)
5. **NEW:** `IncumbentUpdateStep` → updates `incumbent_{domain}` column

**Sequence Diagram (Multi-Period):**

```
Year 1:
  Population (no incumbent column)
    → DiscreteChoiceStep (full tech set)
    → LogitChoiceStep (draw choices)
    → VehicleStateUpdateStep (set vehicle_type="ev", vehicle_age=0)
    → IncumbentUpdateStep (set incumbent_vehicle="ev")
  Result: Population has incumbent_vehicle="ev" for all households

Year 2:
  Population (incumbent_vehicle="ev" from Year 1)
    → DiscreteChoiceStep (full tech set)
    → LogitChoiceStep (draw choices)
    → VehicleStateUpdateStep (set vehicle_type="hybrid", vehicle_age=0)
    → IncumbentUpdateStep (set incumbent_vehicle="hybrid")
  Result: Population has incumbent_vehicle="hybrid" (transition from "ev")
```

---

### Decision 4: Multi-period state threading

**Chosen Option:** State key naming convention with `{domain}_{key}` pattern and domain-ordered step execution.

**Rationale:**
- Prevents key collisions between domains
- Aligns with existing `DISCRETE_CHOICE_*_KEY` pattern
- Deterministic ordering prevents race conditions

**State Key Naming Convention:**

```python
# Existing shared keys (from discrete_choice/step.py):
DISCRETE_CHOICE_COST_MATRIX_KEY = "discrete_choice_cost_matrix"
DISCRETE_CHOICE_EXPANSION_KEY = "discrete_choice_expansion"
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"
DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"  # from logit.py
DECISION_LOG_KEY = "discrete_choice_decision_log"  # from decision_record.py

# Domain-specific keys (new pattern):
# {domain}_{key} where domain = DecisionDomain.name

VEHICLE_INCUMBENT_KEY = "vehicle_incumbent"
HEATING_INCUMBENT_KEY = "heating_incumbent"

VEHICLE_TRANSITION_LOG_KEY = "vehicle_transition_log"
HEATING_TRANSITION_LOG_KEY = "heating_transition_log"

TECHNOLOGY_SET_KEY = "technology_set"  # shared across domains
```

**2-Year State Diagram (Heating Domain Example):**

```
YearState (year=1).data:
  population_data: PopulationData(
    tables={"menage": Table with columns [..., incumbent_heating=null]}
  )
  technology_set: TechnologySet(domains={"heating": {...}})
  discrete_choice_cost_matrix: CostMatrix(...)
  discrete_choice_result: ChoiceResult(chosen=["gas_boiler", "heat_pump", ...])
  heating_incumbent: {"gas_boiler": 1200, "heat_pump": 800}  # distribution

YearState (year=2).data:
  population_data: PopulationData(
    tables={"menage": Table with columns [..., incumbent_heating="gas_boiler", ...]}
  )
  technology_set: TechnologySet(domains={"heating": {...}})  # unchanged
  discrete_choice_cost_matrix: CostMatrix(...)
  discrete_choice_result: ChoiceResult(chosen=["heat_pump", "heat_pump", ...])
  heating_incumbent: {"heat_pump": 2000}  # all converted
  heating_transition_log: TransitionLog(
    from_to={"gas_boiler": {"heat_pump": 800}, "heat_pump": {"heat_pump": 1200}}
  )
```

**Multi-Domain Step Ordering Rules:**

```python
# Correct ordering — all steps for one domain before next domain:
step_pipeline = (
    # Vehicle domain steps
    DiscreteChoiceStep(..., domain=vehicle_domain, name="vehicle_choice"),
    LogitChoiceStep(..., taste_params=vehicle_taste, name="vehicle_logit"),
    DecisionRecordStep(..., depends_on=("vehicle_state_update",)),
    VehicleStateUpdateStep(..., name="vehicle_state_update"),
    IncumbentUpdateStep(..., domain=vehicle_domain, name="vehicle_incumbent_update"),

    # Heating domain steps (complete before next domain)
    DiscreteChoiceStep(..., domain=heating_domain, name="heating_choice"),
    LogitChoiceStep(..., taste_params=heating_taste, name="heating_logit"),
    DecisionRecordStep(..., depends_on=("heating_state_update",)),
    HeatingStateUpdateStep(..., name="heating_state_update"),
    IncumbentUpdateStep(..., domain=heating_domain, name="heating_incumbent_update"),
)

# INCORRECT — interleaved domains risk state corruption:
step_pipeline = (
    DiscreteChoiceStep(..., domain=vehicle_domain, name="vehicle_choice"),
    DiscreteChoiceStep(..., domain=heating_domain, name="heating_choice"),  # WRONG
    LogitChoiceStep(..., taste_params=vehicle_taste, name="vehicle_logit"),
    # ...
)
```

**Transition Record Structure:**

```python
# New type in discrete_choice/types.py

@dataclass(frozen=True)
class TransitionRecord:
    """Record of technology transitions for a single household in one year.

    Attributes:
        household_id: Household identifier (from entity key column).
        period: Simulation year when transition occurred.
        domain: Domain name (e.g., "vehicle", "heating").
        from_tech: Incumbent technology before choice (null if first year).
        to_tech: Chosen technology after choice.
    """

    household_id: str | int
    period: int
    domain: str
    from_tech: str | None
    to_tech: str


@dataclass(frozen=True)
class TransitionLog:
    """Aggregate transition log for a domain in one year.

    Stores per-domain transition counts and from→to mappings.

    Attributes:
        domain: Domain name.
        period: Simulation year.
        from_to: Nested mapping from_tech → {to_tech: count}.
        totals: Per-alternative counts.
    """

    domain: str
    period: int
    from_to: dict[str | None, dict[str, int]]  # None for first-year households
    totals: dict[str, int]  # final incumbent distribution

    @classmethod
    def from_choice_result(
        cls,
        choice_result: ChoiceResult,
        incumbent_column: pa.ChunkedArray,
        domain: str,
        period: int,
    ) -> TransitionLog:
        """Build transition log from choice result and incumbent column.

        Args:
            choice_result: Logit choice result with chosen alternatives.
            incumbent_column: PyArrow column with incumbent technologies.
            domain: Domain name.
            period: Simulation year.

        Returns:
            TransitionLog with aggregate transition counts.
        """
        chosen = choice_result.chosen.to_pylist()
        incumbents = incumbent_column.to_pylist()

        from_to: dict[str | None, dict[str, int]] = {}
        totals: dict[str, int] = {}

        for from_tech, to_tech in zip(incumbents, chosen):
            # Update from→to mapping
            if from_tech not in from_to:
                from_to[from_tech] = {}
            from_to[from_tech][to_tech] = from_to[from_tech].get(to_tech, 0) + 1

            # Update totals
            totals[to_tech] = totals.get(to_tech, 0) + 1

        return cls(domain=domain, period=period, from_to=from_to, totals=totals)
```

**Error Recovery Strategy for State Corruption:**

```python
# Detection — in IncumbentUpdateStep.execute():

# 1. Validate column type
col_type = table.column(self._incumbent_column).type
if not pa.types.is_dictionary(col_type) and not pa.types.is_string(col_type):
    raise DiscreteChoiceError(
        f"Column '{self._incumbent_column}' has invalid type {col_type}. "
        f"Expected dictionary(utf8) or utf8."
    )

# 2. Validate values are in domain alternatives
valid_ids = self._domain.alternative_ids
invalid_mask = pc.is_in(column, value_set=valid_ids).invert()
if invalid_mask.true_count > 0:
    invalid_indices = pc.indices(nonnull=True, filters=invalid_mask).to_pylist()
    raise DiscreteChoiceError(
        f"Column '{self._incumbent_column}' has {len(invalid_indices)} invalid values "
        f"at indices {invalid_indices[:10]}..."
    )

# Recovery — fail-loud with guidance
# No silent recovery; state corruption indicates a bug in pipeline ordering
```

---

### Decision 5: Manifest provenance fields

**Chosen Option:** Add `technology_set` and `transition_summary` fields to `RunManifest`.

**Rationale:**
- Records technology configuration for reproducibility
- Enables comparison of scenarios with different technology scopes
- Supports audit trails for policy analysis

**New Manifest Fields:**

```python
# In governance/manifest.py

@dataclass(frozen=True)
class RunManifest:
    # ... existing fields ...

    # Story 28.0: Technology set and transition provenance
    technology_set: dict[str, Any] = field(default_factory=dict)
    """
    Technology set configuration per domain.

    Schema:
    {
        "domains": {
            "vehicle": {
                "alternative_ids": ["ev", "hybrid", "keep_current"],
                "n_alternatives": 3,
                "is_constrained": true
            },
            "heating": {
                "alternative_ids": ["heat_pump", "gas_boiler", "keep_current"],
                "n_alternatives": 3,
                "is_constrained": true
            }
        },
        "hash": "sha256:..."  # hash of sorted technology set for comparison
    }
    """

    transition_summary: dict[str, Any] = field(default_factory=dict)
    """
    Aggregate transition counts per domain per year.

    Schema:
    {
        "vehicle": {
            "2026": {
                "from_to": {
                    "keep_current": {"ev": 120, "hybrid": 80},
                    "ev": {"keep_current": 100, "hybrid": 50}
                },
                "totals": {"ev": 220, "hybrid": 130, "keep_current": 100}
            },
            "2027": { ... }
        },
        "heating": { ... }
    }
    """
```

**Manifest Version Bump Strategy:**

```python
# Current manifest format version (Story 21.x)
MANIFEST_FORMAT_VERSION = "1.0.0"

# Story 28.0 bumps minor version for new optional fields
MANIFEST_FORMAT_VERSION = "1.1.0"  # backward compatible

# Breaking changes (future) bump major version
# MANIFEST_FORMAT_VERSION = "2.0.0"
```

**Migration Path:**
- Old manifests (v1.0.0) without `technology_set` field are valid — default to empty dict
- New readers check for field presence; writers always include the field
- No manifest migration script needed — backward compatible

**JSON Example Manifest Snippet:**

```json
{
  "manifest_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-05-17T12:00:00Z",
  "engine_version": "0.28.0",
  "technology_set": {
    "domains": {
      "vehicle": {
        "alternative_ids": ["ev", "hybrid", "keep_current"],
        "n_alternatives": 3,
        "is_constrained": true
      }
    },
    "hash": "sha256:a1b2c3d4..."
  },
  "transition_summary": {
    "vehicle": {
      "2026": {
        "from_to": {
          null: {"ev": 500},
          "ev": {"keep_current": 300, "hybrid": 100}
        },
        "totals": {"ev": 500, "keep_current": 300, "hybrid": 100}
      },
      "2027": {
        "from_to": {
          "ev": {"ev": 450, "hybrid": 50},
          "hybrid": {"ev": 50, "keep_current": 50}
        },
        "totals": {"ev": 500, "keep_current": 50, "hybrid": 100}
      }
    }
  }
}
```

---

### Decision 6: Adapter contract

**Chosen Option:** No changes to `ComputationAdapter` interface.

**Rationale:**
- Technology scoping lives entirely above the adapter layer
- `DiscreteChoiceStep` filters alternatives before calling `adapter.compute()`
- Adapter remains domain-agnostic — no OpenFisca coupling

**Adapter Interface (Unchanged):**

```python
# computation/adapter.py

class ComputationAdapter(Protocol):
    """Protocol for tax-benefit computation adapters.

    The adapter computes output fields for a given population and policy.
    Implementations must not import OpenFisca directly outside this module.
    """

    @property
    def version(self) -> str:
        """Adapter version string for provenance."""
        ...

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Compute output fields for the given population and policy.

        Args:
            population: Population data with entity tables.
            policy: Policy parameters.
            period: Computation period (e.g., year).

        Returns:
            ComputationResult with output fields.
        """
        ...
```

**Where Technology Filtering Happens:**

```python
# In discrete_choice/step.py — DiscreteChoiceStep.execute()

# BEFORE adapter.compute():
technology_set = state.data.get(TECHNOLOGY_SET_KEY)
if technology_set is not None:
    choice_set = technology_set.to_choice_set(domain.name, domain.alternatives)
else:
    choice_set = ChoiceSet(alternatives=domain.alternatives)  # full list

# Population expansion uses filtered choice set
expansion = expand_population(population, choice_set, domain)

# Adapter receives expanded population (N×M filtered rows)
result = self._adapter.compute(
    population=expansion.population,  # already filtered
    policy=self._policy,
    period=year,
)
```

**Why This Matters:**
- Adapter isolation is preserved — no OpenFisca coupling outside adapter modules
- Multi-domain support works — each domain's `DiscreteChoiceStep` filters independently
- Mock adapter tests continue to work — technology scoping is a discrete choice concern

---

### Decision 7: Backward compatibility

**Chosen Option:** Graceful degradation with warnings for populations without incumbent columns.

**Rationale:**
- Existing scenarios must continue to work without modification
- Analysts receive clear guidance when upgrading to technology-aware populations
- No data migration required for bundled populations

**Validation Behavior Matrix:**

| Population Type | Incumbent Column | Decisions Enabled | Behavior |
|----------------|------------------|-------------------|----------|
| Legacy bundled | Absent | No | Silent pass — no validation |
| Legacy bundled | Absent | Yes | Warning logged; defaults to reference alternative |
| New bundled | Present | Yes | Full validation |
| New uploaded | Present | Yes | Full validation |
| New uploaded | Absent | Yes | Error — user must provide column |

**Default Incumbent Assignment Algorithm:**

```python
def assign_default_incumbents(
    table: pa.Table,
    domain: DecisionDomain,
    column_name: str,
) -> pa.Table:
    """Add incumbent column with default reference alternative.

    Args:
        table: Entity table (e.g., menage).
        domain: Decision domain with alternatives.
        column_name: Column name (e.g., "incumbent_vehicle").

    Returns:
        New table with incumbent column added.

    Raises:
        DiscreteChoiceError: If column already exists.
    """
    if column_name in table.column_names:
        raise DiscreteChoiceError(
            f"Column '{column_name}' already exists in table"
        )

    # Default to first alternative with "keep" in ID or first in list
    reference_alternative = _find_reference_alternative(domain)

    n = table.num_rows
    default_col = pa.array([reference_alternative] * n, type=pa.utf8())

    logger.warning(
        "column=%s domain=%s default=%s event=default_incumbent_assigned",
        column_name,
        domain.name,
        reference_alternative,
    )

    return table.append_column(column_name, default_col)


def _find_reference_alternative(domain: DecisionDomain) -> str:
    """Find reference alternative for default incumbent assignment.

    Priority:
    1. Alternative with "keep_current" ID
    2. Alternative with "keep" in ID
    3. First alternative in domain list

    Returns:
        Alternative ID string.
    """
    for alt in domain.alternatives:
        if alt.id == "keep_current":
            return alt.id

    for alt in domain.alternatives:
        if "keep" in alt.id:
            return alt.id

    return domain.alternatives[0].id
```

**Migration Strategy for Bundled Populations:**

```python
# Story 28.2: Population data migration script

# 1. Detect bundled populations without incumbent columns
# 2. Add incumbent columns based on domain defaults
# 3. Re-upload with new schema
# 4. Bump population version in metadata

# No automatic migration at runtime — explicit data upgrade step
```

**Error Messages:**

```python
# Population without incumbent column when decisions enabled:
raise DiscreteChoiceError(
    "Investment decisions are enabled but population does not have "
    f"the required 'incumbent_{domain}' column. Please upgrade your "
    f"population data or disable investment decisions.",
    what="Missing incumbent technology column",
    why="Population was created before technology tracking was implemented",
    fix="Upgrade population to include incumbent column or disable investment decisions",
)

# Invalid incumbent values:
raise DiscreteChoiceError(
    f"Population has invalid incumbent technology IDs: {invalid_ids}. "
    f"Valid IDs for {domain} domain: {valid_ids}",
    what="Invalid incumbent technology in population",
    why="Population data was created with different alternative set",
    fix="Validate population alternatives match technology set configuration",
)
```

---

### Decision 8: TasteParameters type reconciliation

**Chosen Option:** Defer per-domain taste parameter overrides to Story 28.4; use existing backend `TasteParameters` structure.

**Rationale:**
- Frontend `TasteParameters` (3-field vehicle-specific) is a UI concern
- Backend `TasteParameters` (7-field generalized) is the runtime type
- Taste parameter overrides are a power-user feature not required for MVP
- TechnologySet should focus on alternative scoping first

**Type Incompatibility:**

```typescript
// Frontend (workspace.ts) — vehicle-specific, 3 fields
export interface TasteParameters {
  priceSensitivity: number;  // [-5, 0], default -1.5
  rangeAnxiety: number;      // [-3, 0], default -0.8
  envPreference: number;     // [0, 3], default 0.5
}
```

```python
# Backend (types.py) — generalized, 7 fields
@dataclass(frozen=True)
class TasteParameters:
    beta_cost: float  # legacy field
    asc: dict[str, float]  # per-alternative constants
    betas: dict[str, float]  # named coefficients
    calibrate: frozenset[str]  # parameters to optimize
    fixed: frozenset[str]  # literature values
    reference_alternative: str | None
    literature_sources: dict[str, str]
```

**Resolution Strategy:**

1. **Story 28.0-28.3:** `TechnologySet` does NOT include taste parameter overrides
2. **Story 28.4:** Extend `TechnologySet` with optional `taste_parameter_overrides` field
3. **Story 28.4:** Generalize frontend `TasteParameters` to match backend schema
4. **Story 28.4:** Add wizard UI for taste parameter configuration (power-user feature)

**TechnologySet Schema (MVP — No Taste Overrides):**

```python
@dataclass(frozen=True)
class TechnologySet:
    """Technology set without taste parameter overrides (MVP).

    Story 28.4 will add optional taste_parameter_overrides field.
    """

    domains: dict[str, DomainTechnologySelection]
```

**TechnologySet Schema (Future — With Taste Overrides):**

```python
@dataclass(frozen=True)
class DomainTechnologySelection:
    """Technology selection with optional taste overrides.

    Story 28.4: Add taste_overrides field.
    """

    alternative_ids: tuple[str, ...]
    taste_overrides: TasteParameters | None = None  # Story 28.4


@dataclass(frozen=True)
class TechnologySet:
    """Technology set with optional taste parameter overrides.

    Story 28.4: Full taste override support.
    """

    domains: dict[str, DomainTechnologySelection]
```

**Frontend Migration Path (Story 28.4):**

```typescript
// Future generalized taste parameters (Story 28.4)
export interface GeneralizedTasteParameters {
  // Alternative-specific constants (ASCs)
  alternativeSpecificConstants: Record<string, number>;

  // Named coefficients
  coefficients: Record<string, number>;

  // Calibration flags
  calibrate: string[];
  fixed: string[];
  referenceAlternative: string;
}

// Backward compatible with existing vehicle-specific interface
export interface TasteParameters extends GeneralizedTasteParameters {
  // Vehicle-specific convenience getters
  get priceSensitivity(): number { return this.coefficients["cost"] ?? -1.5; }
  get rangeAnxiety(): number { return this.coefficients["range"] ?? -0.8; }
  get envPreference(): number { return this.coefficients["env"] ?? 0.5; }
}
```

---

## Story 28.1–28.5 Sizing

After completing the spike, the stories can be sized concretely:

| Story | Title | Complexity | Risk Factors | SP Estimate | Rationale |
|-------|-------|------------|--------------|-------------|-----------|
| 28.1 | Add `technology_set` to `EngineConfig`; expose API and persistence | Low | Type reconciliation frontend/backend; FastAPI validation | 5 | Straightforward type addition, simple API endpoint, persistence in existing EngineConfig |
| 28.2 | Extend `PopulationData` schema with incumbent columns; migration + manifest | Medium | PyArrow dictionary encoding; backward compatibility; bundled population upgrade | 5 | Requires careful schema design, validation logic, and migration tests |
| 28.3 | Wire `DiscreteChoiceStep` outputs into population frame; orchestrator multi-period | High | State threading; transition logging; step ordering; corruption detection | 5 | Touches orchestrator core, multi-period semantics are tricky |
| 28.4 | Investment Decisions wizard — Technology step; reactive defaults | Medium | UI complexity; default detection from population; error UX | 3 | Contained UI work, well-defined inputs from backend |
| 28.5 | Regression and analyst-journey coverage for multi-period decisions | Low | Test fixture updates; flakiness in multi-period tests | 3 | Straightforward test authoring, no production code |

**Total:** ~21 SP across 5 stories (after 3 SP architect spike).

---

## Error Handling Specification

Each failure mode specifies error type, message format, and recovery strategy following project pattern `{what, why, fix}`.

### Failure Modes

| Failure Mode | Error Type | Message Format | Recovery Strategy |
|--------------|------------|----------------|-------------------|
| Invalid incumbent technology IDs in population | `DiscreteChoiceError` | `Invalid incumbent IDs in column '{col}': {ids}. Valid: {valid}` | Fail-loud; user must fix population or disable decisions |
| Missing incumbent column when decisions enabled | `DiscreteChoiceError` | `Column 'incumbent_{domain}' required when decisions enabled` | Fail-loud; user must upgrade population or disable decisions |
| Unknown alternative IDs in technology set | `DiscreteChoiceError` | `Unknown alternatives in technology_set['{domain}']: {ids}` | Fail-loud; user must fix EngineConfig |
| Multi-domain state key collision | `DiscreteChoiceError` | `State key '{key}' already in use by {other_domain}` | Fail-loud; pipeline configuration error |
| Transition record merge failures | `DiscreteChoiceError` | `Cannot merge transition log: {reason}` | Fail-loud; indicates state corruption |
| Manifest serialization failures | `ManifestValidationError` | `Cannot serialize technology_set: {reason}` | Fail-loud; indicates schema mismatch |

### Error Type Hierarchy

```python
# discrete_choice/errors.py

class DiscreteChoiceError(ReformLabError):
    """Base error for discrete choice subsystem."""

    def __init__(
        self,
        message: str,
        *,
        what: str | None = None,
        why: str | None = None,
        fix: str | None = None,
        year: int | None = None,
        step_name: str | None = None,
        domain_name: str | None = None,
        **kwargs: Any,
    ):
        self.year = year
        self.step_name = step_name
        self.domain_name = domain_name
        super().__init__(message, what=what, why=why, fix=fix, **kwargs)


class StateCorruptionError(DiscreteChoiceError):
    """State corruption in multi-period execution."""


class TechnologySetValidationError(DiscreteChoiceError):
    """Invalid technology set configuration."""


class IncumbentColumnError(DiscreteChoiceError):
    """Invalid or missing incumbent column in population."""
```

### Logging Levels and Structured Format

```python
# Logging format follows project pattern: key=value pairs

logger.info(
    "year=%d step_name=%s domain=%s n_households=%d n_alternatives=%d "
    "event=step_start",
    year, step_name, domain, n, m
)

logger.warning(
    "column=%s domain=%s default=%s event=default_incumbent_assigned",
    column_name, domain, reference_alternative
)

logger.error(
    "year=%d step_name=%s domain=%s invalid_ids=%s event=validation_failed",
    year, step_name, domain, sorted(invalid_ids)
)
```

---

## Open Questions for PM Review

1. **FR Additions:** Does this ADR require new FR entries in the PRD, or are existing FR43/FR46 sufficient?
2. **Taste Parameter Overrides:** Should Story 28.4 include full generalized taste parameter UI, or is MVP (technology scoping only) acceptable?
3. **Population Migration:** Should bundled populations be auto-migrated, or is explicit upgrade acceptable?
4. **Comparison Semantics:** How should comparison views treat scenarios with different technology sets? (e.g., baseline uses full tech set, reform uses EV-only)

---

## References

- [Sprint Change Proposal](sprint-change-proposal-2026-04-26.md) Section 4.2 — EPIC-28 definition
- [`src/reformlab/discrete_choice/`](../../src/reformlab/discrete_choice/) — Existing discrete choice subsystem
- [`src/reformlab/orchestrator/types.py`](../../src/reformlab/orchestrator/types.py) — YearState, OrchestratorConfig
- [`src/reformlab/computation/types.py`](../../src/reformlab/computation/types.py) — PopulationData schema
- [`frontend/src/types/workspace.ts`](../../frontend/src/types/workspace.ts) — EngineConfig, frontend types
- [`src/reformlab/governance/manifest.py`](../../src/reformlab/governance/manifest.py) — RunManifest provenance

---

## Appendix: Pseudocode Examples

### Example 1: Full Pipeline with Technology Set

```python
# orchestrator/compiler.py

def build_step_pipeline(
    config: OrchestratorConfig,
    technology_set: TechnologySet | None,
) -> tuple[PipelineStep, ...]:
    """Build orchestrator step pipeline with technology set support.

    Returns ordered steps for vehicle and heating domains with incumbent updates.
    """
    steps: list[PipelineStep] = []

    # Computation step (unchanged)
    steps.append(ComputationStep(adapter, policy))

    # Vehicle domain (if enabled)
    if technology_set is None or "vehicle" in technology_set.domains:
        vehicle_domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        vehicle_taste = config.taste_parameters  # from EngineConfig

        steps.extend([
            DiscreteChoiceStep(
                adapter, vehicle_domain, policy,
                name="vehicle_choice",
            ),
            LogitChoiceStep(
                taste_parameters=vehicle_taste,
                name="vehicle_logit",
            ),
            VehicleStateUpdateStep(
                vehicle_domain,
                name="vehicle_state_update",
            ),
            IncumbentUpdateStep(
                vehicle_domain,
                name="vehicle_incumbent_update",
            ),
            DecisionRecordStep(
                depends_on=("vehicle_incumbent_update",),
            ),
        ])

    # Heating domain (if enabled)
    if technology_set is None or "heating" in technology_set.domains:
        heating_domain = HeatingInvestmentDomain(default_heating_domain_config())

        steps.extend([
            DiscreteChoiceStep(
                adapter, heating_domain, policy,
                name="heating_choice",
            ),
            # ... similar to vehicle
        ])

    return tuple(steps)
```

### Example 2: Multi-Period Execution

```python
# orchestrator/runner.py

def run_multi_period(
    config: OrchestratorConfig,
    technology_set: TechnologySet | None,
) -> OrchestratorResult:
    """Run multi-period simulation with technology transitions.

    Demonstrates state threading across years with incumbent updates.
    """
    state = YearState(year=config.start_year, data={
        "population_data": load_initial_population(),
        "technology_set": technology_set,
    })

    yearly_states: dict[int, YearState] = {}

    for year in range(config.start_year, config.end_year + 1):
        # Set year-specific seed
        year_seed = config.seed ^ year if config.seed else None
        state = replace(state, year=year, seed=year_seed)

        # Execute all steps for this year
        for step in config.step_pipeline:
            state = step.execute(year, state)

        yearly_states[year] = state

        # Log transition summary
        if technology_set:
            for domain in technology_set.domains.keys():
                log_key = f"{domain}_transition_log"
                if log_key in state.data:
                    transition_log = state.data[log_key]
                    logger.info(
                        "year=%d domain=%s transitions=%s event=year_complete",
                        year, domain, transition_log.from_to
                    )

    return OrchestratorResult(
        success=True,
        yearly_states=yearly_states,
        metadata={"technology_set": technology_set},
    )
```

### Example 3: Frontend Wizard Integration

```typescript
// frontend/src/components/engine/InvestmentDecisionsWizard.tsx

interface TechnologyStepProps {
  technologySet: TechnologySet;
  onTechnologySetChange: (set: TechnologySet) => void;
  population: PopulationData | null;
}

function TechnologyStep({ technologySet, onTechnologySetChange, population }: TechnologyStepProps) {
  // Detect incumbent column availability
  const hasIncumbentVehicle = population?.columns.includes("incumbent_vehicle") ?? false;
  const hasIncumbentHeating = population?.columns.includes("incumbent_heating") ?? false;

  // Reactive defaults from population
  useEffect(() => {
    if (hasIncumbentVehicle && !technologySet.domains["vehicle"]) {
      // Default to full technology set when population has incumbents
      const defaultSet: TechnologySet = {
        domains: {
          vehicle: { alternativeIds: DEFAULT_VEHICLE_ALTERNATIVES },
        },
      };
      onTechnologySetChange(defaultSet);
    }
  }, [hasIncumbentVehicle]);

  return (
    <StepPanel>
      <DomainSelector
        domain="vehicle"
        alternatives={VEHICLE_ALTERNATIVES}
        selected={technologySet.domains["vehicle"]?.alternativeIds ?? []}
        onChange={(ids) => updateDomain("vehicle", ids)}
        hasIncumbentData={hasIncumbentVehicle}
      />
      <DomainSelector
        domain="heating"
        alternatives={HEATING_ALTERNATIVES}
        selected={technologySet.domains["heating"]?.alternativeIds ?? []}
        onChange={(ids) => updateDomain("heating", ids)}
        hasIncumbentData={hasIncumbentHeating}
      />
    </StepPanel>
  );
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-05-17
**Next Review:** After PM sign-off and before Story 28.1 implementation
