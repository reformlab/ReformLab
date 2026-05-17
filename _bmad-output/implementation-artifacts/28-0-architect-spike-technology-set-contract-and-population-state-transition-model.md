# Story 28.0: Architect spike — technology-set contract and population state-transition model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an architect,
I want to define the data contracts and architecture for technology-set configuration and population state transitions,
so that implementation stories 28.1–28.5 can proceed against one approved model with clear backward compatibility guarantees.

## Acceptance Criteria

1. Deliver an ADR document answering all technology-set contract questions (see spike questions below)
2. Define `TechnologySet` schema with per-domain alternative selection
3. Define population schema delta for incumbent-technology columns
4. Specify the writeback contract for `DiscreteChoiceStep` → population updates
5. Specify orchestrator multi-period state threading
6. Specify manifest provenance fields for technology-set versioning
7. Define backward compatibility path for populations without incumbent columns
8. Size stories 28.1–28.5 concretely (within ±2 SP accuracy)

## Spike Questions (from sprint-change-proposal)

The ADR must answer:

1. **What does `EngineConfig.technology_set` look like?**
   - Per-domain list of alternative IDs?
   - Taste parameter overrides per domain?
   - Default technology-set semantics?

2. **What's the population schema delta?**
   - One column per domain (`incumbent_heating`, `incumbent_vehicle`)?
   - Single keyed map column?
   - Optional vs required semantics?

3. **How does `DiscreteChoiceStep` write back?**
   - In-place mutation of `PopulationData`?
   - Returns new `PopulationData` instance?
   - How does the orchestrator chain it across periods?

4. **Manifest impact — what new provenance fields?**
   - Technology-set version/hash
   - Incumbent technology distribution
   - Transition counts per domain per year

5. **Backward compatibility — populations without incumbent columns?**
   - Validation behavior (error vs warning vs silent default)
   - Default incumbent assignment strategy

6. **Adapter contract — does `ComputationAdapter` change?**
   - Or does the change live entirely above it?

## Tasks / Subtasks

- [ ] Task 1: Analyze existing discrete choice domain contracts (AC: 1, 3, 6)
  - [ ] 1.1 Review `DecisionDomain` protocol in `src/reformlab/discrete_choice/domain.py`
  - [ ] 1.2 Review existing domain implementations (`heating.py`, `vehicle.py`)
  - [ ] 1.3 Review `*StateUpdateStep` patterns and `apply_choices_to_population` utility
  - [ ] 1.4 Review `Alternative` and `ChoiceSet` types in `types.py`
- [ ] Task 2: Analyze orchestrator state threading (AC: 3, 4)
  - [ ] 2.1 Review `YearState` in `src/reformlab/orchestrator/types.py`
  - [ ] 2.2 Review `OrchestratorConfig` and step pipeline execution
  - [ ] 2.3 Review `PopulationData` schema in `src/reformlab/computation/types.py`
  - [ ] 2.4 Review multi-period result handling in `panel.py`
- [ ] Task 3: Analyze frontend workspace types (AC: 1)
  - [ ] 3.1 Review `EngineConfig` in `frontend/src/types/workspace.ts`
  - [ ] 3.2 Review investment decisions wizard structure
  - [ ] 3.3 Review Pydantic models in `src/reformlab/server/models.py`
- [ ] Task 4: Design `TechnologySet` schema (AC: 1)
  - [ ] 4.1 Define backend `TechnologySet` dataclass/frozen type
  - [ ] 4.2 Define per-domain `TechnologySelection` type
  - [ ] 4.3 Define taste parameter override structure
  - [ ] 4.4 Define default/empty technology-set semantics
- [ ] Task 5: Design population schema delta (AC: 2, 5)
  - [ ] 5.1 Choose column naming convention for incumbents
  - [ ] 5.2 Define PyArrow schema for optional incumbent columns
  - [ ] 5.3 Define validation rules for missing/invalid incumbents
  - [ ] 5.4 Define backward compatibility path
- [ ] Task 6: Design writeback contract (AC: 3, 4)
  - [ ] 6.1 Specify choice-result → population update pattern
  - [ ] 6.2 Define transition record structure (household_id, period, from_tech, to_tech)
  - [ ] 6.3 Specify orchestrator state threading for multi-period
  - [ ] 6.4 Define interaction with existing `*StateUpdateStep` classes
- [ ] Task 7: Design manifest provenance (AC: 4)
  - [ ] 7.1 Define technology-set version/hash field
  - [ ] 7.2 Define incumbent distribution metadata
  - [ ] 7.3 Define transition count metadata structure
  - [ ] 7.4 Define manifest version bump strategy
- [ ] Task 8: Design API and persistence (AC: 1)
  - [ ] 8.1 Define `GET /api/technology-alternatives?domain={domain}` endpoint
  - [ ] 8.2 Define technology-set persistence in `EngineConfig`
  - [ ] 8.3 Define migration path for existing scenarios
- [ ] Task 9: Size stories 28.1–28.5 (AC: 8)
  - [ ] 9.1 Break down story 28.1 with concrete tasks and SP estimate
  - [ ] 9.2 Break down story 28.2 with concrete tasks and SP estimate
  - [ ] 9.3 Break down story 28.3 with concrete tasks and SP estimate
  - [ ] 9.4 Break down story 28.4 with concrete tasks and SP estimate
  - [ ] 9.5 Break down story 28.5 with concrete tasks and SP estimate
- [ ] Task 10: Write ADR document (AC: 1-7)
  - [ ] 10.1 Create `_bmad-output/planning-artifacts/adr-technology-set-and-population-state-transitions.md`
  - [ ] 10.2 Document all design decisions with rationale
  - [ ] 10.3 Include schema definitions and code examples
  - [ ] 10.4 Include backward compatibility strategy
  - [ ] 10.5 Include manifest provenance specification

## Dev Notes

### Relevant Architecture Patterns and Constraints

**Source Tree Components to Touch:**
- `src/reformlab/discrete_choice/types.py` — `Alternative`, `ChoiceSet`, domain types
- `src/reformlab/discrete_choice/step.py` — `DiscreteChoiceStep` orchestrator integration
- `src/reformlab/discrete_choice/heating.py` — `HeatingInvestmentDomain`, `HeatingStateUpdateStep`
- `src/reformlab/discrete_choice/vehicle.py` — `VehicleInvestmentDomain`, `VehicleStateUpdateStep`
- `src/reformlab/discrete_choice/domain_utils.py` — `apply_choices_to_population`, `create_vintage_entries`
- `src/reformlab/orchestrator/types.py` — `YearState`, `OrchestratorConfig`
- `src/reformlab/computation/types.py` — `PopulationData` schema
- `src/reformlab/server/models.py` — Pydantic request/response models
- `frontend/src/types/workspace.ts` — `EngineConfig`, workspace types
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — wizard UI

**Key Patterns to Follow:**
1. **Frozen dataclasses for domain types** — All types must use `@dataclass(frozen=True)` and be mutated via `dataclasses.replace()`
2. **PyArrow for data contracts** — Population data uses `pa.Table` with entity-keyed dictionaries
3. **Protocol-based interfaces** — `DecisionDomain` uses `@runtime_checkable` Protocol, not ABC
4. **Immutable state updates** — Orchestrator steps return new `YearState` via `replace(state, data=new_data)`
5. **Stable string-constant keys** — Use module-level constants for `YearState.data` keys (e.g., `DISCRETE_CHOICE_COST_MATRIX_KEY`)
6. **Deterministic execution** — All runs must be reproducible; seeds are explicit and logged
7. **Backward compatibility** — New features must not break existing scenarios; use optional fields and migration paths

### Existing Patterns to Leverage

**State Update Pattern** (from `heating.py` and `vehicle.py`):
```python
# Existing pattern for writing choices back to population:
updated_population = apply_choices_to_population(
    population, choice_result, config.alternatives, config.entity_key
)
# Returns new PopulationData with updated attributes per household
```

**Vintage Tracking Pattern** (already implemented):
- `create_vintage_entries()` creates cohort records for new purchases
- `VintageState` tracks asset cohorts by `asset_class` and `vintage_year`
- Each domain has a `non_purchase_ids` set for alternatives that don't create vintages

**Domain Config Pattern** (from `heating.py` and `vehicle.py`):
```python
@dataclass(frozen=True)
class VehicleDomainConfig:
    alternatives: tuple[Alternative, ...]
    cost_column: str = "total_vehicle_cost"
    entity_key: str = "menage"
    non_purchase_ids: frozenset[str] = frozenset({"keep_current", "buy_no_vehicle"})
    fuel_price_series: str | None = None
    fuel_price_default: float = 1.55
    taste_parameters: TasteParameters | None = None  # Story 21.7 / AC-7
```

**Frontend Workspace Types** (from `workspace.ts`):
```typescript
export interface EngineConfig {
  startYear: number;
  endYear: number;
  seed: number | null;
  investmentDecisionsEnabled: boolean | null;
  logitModel: "multinomial_logit" | "nested_logit" | "mixed_logit" | null;
  discountRate: number;
  tasteParameters?: TasteParameters | null;
  calibrationState?: CalibrationState;
}
```

### Testing Standards Summary

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`
- **Class-based test grouping** — Group tests by feature or acceptance criterion
- **Fixtures in conftest.py** — Subsystem-specific fixtures per `conftest.py`
- **Direct assertions** — Use plain `assert`; no custom assertion helpers
- **Test helpers are explicit** — Import shared callables from conftest directly
- **Golden file tests** — Use YAML fixtures in `tests/fixtures/`
- **MockAdapter for unit tests** — Never use real OpenFisca in orchestrator/template/indicator unit tests

### Project Structure Notes

**Alignment with unified project structure:**
- Python: `src/reformlab/` package with subsystem modules
- Tests: `tests/` mirror structure
- Frontend: `frontend/src/` with component, API, and type directories

**Naming conventions:**
- Files: `snake_case.py` throughout
- Classes: `PascalCase` (no suffixes like `Impl` or `Base`)
- Module-level docstrings: Every module has a docstring explaining its role
- Section separators: Use `# ====...====` comment blocks in longer modules

**Critical architectural boundaries:**
- **Adapter isolation is absolute** — Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca
- **Orchestrator is the core product** — Never build custom policy engines, formula compilers, or entity graph engines
- **Determinism is non-negotiable** — Every run must be reproducible; seeds are explicit, logged in manifests

### Design Considerations for Spike

**Incumbent Technology Storage Options:**
1. **Per-domain columns** — `incumbent_heating: string`, `incumbent_vehicle: string`
   - Pros: Simple, queryable, aligns with existing domain pattern
   - Cons: N columns for N domains, sparse if not all domains used
2. **Single structured column** — `incumbent_technologies: map<domain, alternative_id>`
   - Pros: One column, extensible
   - Cons: PyArrow map type is less common, requires special handling

**TechnologySet Configuration Options:**
1. **Per-domain alternative lists** — `{"vehicle": ["ev", "hybrid"], "heating": ["heat_pump"]}`
   - Pros: Simple, explicit, validates against known alternatives
   - Cons: Doesn't capture taste overrides
2. **Rich configuration with overrides** — Includes taste parameters, weights, defaults
   - Pros: Full expressiveness
   - Cons: More complex, potentially over-engineering for MVP

**Writeback Contract Options:**
1. **Extend existing `*StateUpdateStep` pattern** — Each domain's step writes back its own state
   - Pros: Reuses proven pattern, consistent with existing code
   - Cons: Requires per-step implementation
2. **Generic writeback step** — Single step handles all domains
   - Pros: Centralized, DRY
   - Cons: Less flexible, may not fit all domain semantics

**Manifest Provenance Considerations:**
- Must capture technology-set version/hash for reproducibility
- Should capture incumbent distribution at start of run
- Should capture transition counts per domain per year
- Must be backward compatible with existing manifests

## References

- [Source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md`](../planning-artifacts/sprint-change-proposal-2026-04-26.md) Section 4.2 — EPIC-28 story list and spike questions
- [Source: `_bmad-output/planning-artifacts/epics.md`](../planning-artifacts/epics.md) — Epic 28 definition and story 28.0 description
- [Source: `src/reformlab/discrete_choice/types.py`](../../src/reformlab/discrete_choice/types.py) — Core discrete choice types
- [Source: `src/reformlab/discrete_choice/domain.py`](../../src/reformlab/discrete_choice/domain.py) — DecisionDomain protocol
- [Source: `src/reformlab/discrete_choice/step.py`](../../src/reformlab/discrete_choice/step.py) — DiscreteChoiceStep orchestrator integration
- [Source: `src/reformlab/discrete_choice/heating.py`](../../src/reformlab/discrete_choice/heating.py) — Heating domain and state update pattern
- [Source: `src/reformlab/discrete_choice/vehicle.py`](../../src/reformlab/discrete_choice/vehicle.py) — Vehicle domain and state update pattern
- [Source: `src/reformlab/orchestrator/types.py`](../../src/reformlab/orchestrator/types.py) — YearState and OrchestratorConfig
- [Source: `src/reformlab/computation/types.py`](../../src/reformlab/computation/types.py) — PopulationData schema
- [Source: `src/reformlab/server/models.py`](../../src/reformlab/server/models.py) — Pydantic API models
- [Source: `frontend/src/types/workspace.ts`](../../frontend/src/types/workspace.ts) — Frontend workspace types
- [Source: `_bmad-output/planning-artifacts/architecture-diagrams.md`](../planning-artifacts/architecture-diagrams.md) — System architecture diagrams

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Opus 4.6 equivalent)

### Debug Log References

### Completion Notes List

- Story 28.0 is an architect spike, not implementation
- Deliverable is ADR document, not code
- Stories 28.1–28.5 will be sized concretely after this spike completes
- This spike must produce actionable guidance for implementation agents

### File List

Analysis complete. Ready for architect agent to execute spike.
