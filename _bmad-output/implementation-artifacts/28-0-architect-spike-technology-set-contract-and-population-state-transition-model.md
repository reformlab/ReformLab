# Story 28.0: Architect spike — technology-set contract and population state-transition model

Status: pending-pm-review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an architect,
I want to define the data contracts and architecture for technology-set configuration and population state transitions,
so that implementation stories 28.1–28.5 can proceed against one approved model with clear backward compatibility guarantees.

## Acceptance Criteria

1. **ADR document with complete decisions** — Deliver `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md` with one section per spike question (8 sections minimum). Each section states: chosen option with rationale, rejected alternatives with reasoning, and concrete type/schema definition or pseudocode example.
2. **TechnologySet schema defined** — Frozen dataclass definition with field names and types, validation rules, `to_choice_set(domain: str) -> ChoiceSet` method, and construction example.
3. **Population schema delta specified** — Column naming convention (e.g., `incumbent_heating`, `incumbent_vehicle`), PyArrow dictionary encoding type `pa.dictionary(pa.int32(), pa.utf8())`, optional/required semantics, default value strategy, and validation that values are in domain's alternative_ids set.
4. **Writeback contract specified** — Method signature, return type, sequence diagram showing orchestrator step chain, and interaction with existing `*StateUpdateStep` classes.
5. **Multi-period state threading specified** — State key naming convention to prevent collisions (`{domain}_{key}` pattern), 2-year state diagram showing `YearState.data` keys before/after each period, multi-domain step ordering rules, and error recovery strategy for state corruption.
6. **Manifest provenance fields specified** — List of new fields with name/type, JSON example manifest snippet, and version bump strategy.
7. **Backward compatibility path defined** — Validation behavior (error/warning/silent) for populations without incumbent columns, default assignment algorithm, and migration strategy for bundled populations.
8. **Stories 28.1–28.5 sized concretely** — Each story includes task breakdown (5-15 subtasks), complexity assessment (Low/Med/High), risk factors, and SP estimate with rationale.
9. **PM sign-off obtained** — ADR reviewed by PM and either new FR entries created in PRD or explicit approval recorded before story is marked done (per epics.md governance requirement).
10. **Error handling specified** — Each failure mode (invalid incumbents, missing columns, unknown alternatives, state collisions, transition failures) specifies error type, message format, and recovery strategy following project error response pattern `{what, why, fix}`.

## Spike Questions (from sprint-change-proposal)

The ADR must answer all 8 questions:

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

7. **Error handling — what are the failure modes?**
   - Invalid incumbent technology IDs in population
   - Missing incumbent columns when decisions enabled
   - Unknown alternative IDs in technology set
   - Multi-domain state key collisions
   - Transition record merge failures
   - Manifest serialization failures

8. **TasteParameters type reconciliation** — How do per-domain taste parameter overrides in `TechnologySet` relate to existing `TasteParameters` types? The frontend has a 3-field vehicle-specific `TasteParameters`; the backend has a generalized 7-field structure. Should the frontend type be generalized? Should `TechnologySet` define its own schema? Or should overrides be deferred to story 28.4?

## Tasks / Subtasks

- [x] Task 1: Analyze existing discrete choice domain contracts (AC: 1, 3, 6)
  - [x] 1.1 Review `DecisionDomain` protocol in `src/reformlab/discrete_choice/domain.py`
  - [x] 1.2 Review existing domain implementations (`heating.py`, `vehicle.py`)
  - [x] 1.3 Review `*StateUpdateStep` patterns and `apply_choices_to_population` utility
  - [x] 1.4 Review `Alternative` and `ChoiceSet` types in `types.py`
  - [x] 1.5 Review `decision_record.py` — `DecisionRecord`, `DecisionRecordStep`, `DECISION_LOG_KEY` and assess whether incumbent→chosen transition tracking extends this type or requires a new parallel type
- [x] Task 2: Analyze orchestrator state threading (AC: 3, 4)
  - [x] 2.1 Review `YearState` in `src/reformlab/orchestrator/types.py`
  - [x] 2.2 Review `OrchestratorConfig` and step pipeline execution
  - [x] 2.3 Review `PopulationData` schema in `src/reformlab/computation/types.py`
  - [x] 2.4 Review multi-period result handling in `panel.py`
- [x] Task 3: Analyze frontend workspace types (AC: 1)
  - [x] 3.1 Review `EngineConfig` in `frontend/src/types/workspace.ts`
  - [x] 3.2 Review investment decisions wizard structure
  - [x] 3.3 Review Pydantic models in `src/reformlab/server/models.py`
  - [x] 3.4 Compare frontend vs backend `TasteParameters` types and document incompatibility
- [x] Task 4: Design `TechnologySet` schema (AC: 1)
  - [x] 4.1 Define backend `TechnologySet` dataclass/frozen type
  - [x] 4.2 Define per-domain `TechnologySelection` type
  - [x] 4.3 Define taste parameter override structure — decide whether to use frontend type (3-field vehicle-specific), backend type (7-field generalized), or new domain-specific schema
  - [x] 4.4 Define default/empty technology-set semantics
- [x] Task 5: Design population schema delta (AC: 2, 5)
  - [x] 5.1 Choose column naming convention for incumbents
  - [x] 5.2 Define PyArrow schema for optional incumbent columns (use `pa.dictionary(pa.int32(), pa.utf8())` for efficient categorical filtering)
  - [x] 5.3 Define validation rules for missing/invalid incumbents
  - [x] 5.4 Define backward compatibility path
- [x] Task 6: Design writeback contract (AC: 3, 4, 5)
  - [x] 6.1 Specify choice-result → population update pattern
  - [x] 6.2 Define transition record structure (household_id, period, from_tech, to_tech)
  - [x] 6.3 Specify orchestrator state threading for multi-period
  - [x] 6.4 Define interaction with existing `*StateUpdateStep` classes
  - [x] 6.5 Specify state key naming convention to prevent multi-domain collisions
  - [x] 6.6 Specify multi-domain step ordering rules (all steps for one domain before next domain)
- [x] Task 7: Design manifest provenance (AC: 4)
  - [x] 7.1 Define technology-set version/hash field
  - [x] 7.2 Define incumbent distribution metadata
  - [x] 7.3 Define transition count metadata structure
  - [x] 7.4 Define manifest version bump strategy
- [x] Task 8: Design API and persistence (AC: 1)
  - [x] 8.1 Define `GET /api/technology-alternatives?domain={domain}` endpoint
  - [x] 8.2 Define technology-set persistence in `EngineConfig`
  - [x] 8.3 Define migration path for existing scenarios
- [x] Task 9: Size stories 28.1–28.5 (AC: 8)
  - [x] 9.1 Break down story 28.1 with concrete tasks and SP estimate
  - [x] 9.2 Break down story 28.2 with concrete tasks and SP estimate
  - [x] 9.3 Break down story 28.3 with concrete tasks and SP estimate
  - [x] 9.4 Break down story 28.4 with concrete tasks and SP estimate
  - [x] 9.5 Break down story 28.5 with concrete tasks and SP estimate
- [x] Task 10: Write ADR document (AC: 1-7)
  - [x] 10.1 Create `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md` (filename matches sprint-change-proposal Section 4.2)
  - [x] 10.2 Document all design decisions with rationale
  - [x] 10.3 Include schema definitions and code examples
  - [x] 10.4 Include backward compatibility strategy
  - [x] 10.5 Include manifest provenance specification
  - [x] 10.6 Follow ADR structure: Context, Decision Drivers, Decisions Made (one per spike question), Schema Definitions, Sequence Diagrams, Backward Compatibility, Error Handling, Story 28.1–28.5 Sizing
- [x] Task 11: Design error handling (AC: 10)
  - [x] 11.1 Specify error types for each failure mode (DiscreteChoiceError, ValidationError, StateCorruptionError, etc.)
  - [x] 11.2 Define error message format following project pattern `{what, why, fix}`
  - [x] 11.3 Define recovery strategies (fail-loud vs graceful degradation)
  - [x] 11.4 Document logging levels and structured log format
- [x] Task 12: Obtain PM sign-off (AC: 9)
  - [x] 12.1 Hand off ADR to PM for review
  - [x] 12.2 Update sprint-status.yaml to 'pending-pm-review'
  - [ ] 12.3 Wait for PM sign-off before marking story 28.0 done
  - [ ] 12.4 Ensure new FR entries are created in PRD if required by PM

## Dev Notes

### Relevant Architecture Patterns and Constraints

**Source Tree Components to Analyze (Read-Only):**
- `src/reformlab/discrete_choice/types.py` — `Alternative`, `ChoiceSet`, domain types
- `src/reformlab/discrete_choice/step.py` — `DiscreteChoiceStep` orchestrator integration
- `src/reformlab/discrete_choice/heating.py` — `HeatingInvestmentDomain`, `HeatingStateUpdateStep`
- `src/reformlab/discrete_choice/vehicle.py` — `VehicleInvestmentDomain`, `VehicleStateUpdateStep`
- `src/reformlab/discrete_choice/domain_utils.py` — `apply_choices_to_population`, `create_vintage_entries`
- `src/reformlab/discrete_choice/decision_record.py` — `DecisionRecord`, `DecisionRecordStep`, `DECISION_LOG_KEY`
- `src/reformlab/orchestrator/types.py` — `YearState`, `OrchestratorConfig`
- `src/reformlab/computation/types.py` — `PopulationData` schema
- `src/reformlab/server/models.py` — Pydantic request/response models
- `frontend/src/types/workspace.ts` — `EngineConfig`, workspace types
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — wizard UI

> **Note:** This spike produces ONE output file: the ADR at `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md`. No source code is modified.

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

### Testing Standards

No tests are produced by this spike. The deliverable is an ADR document, not code. Testing guidance for implementation stories 28.1–28.5 is in CLAUDE.md and project-context.md.

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
   - Implementation: Use `pa.dictionary(pa.int32(), pa.utf8())` for O(1) categorical filtering and efficient storage
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

**TasteParameters Type Consideration:**
- Frontend `TasteParameters` (workspace.ts) is vehicle-specific with 3 fields: `priceSensitivity`, `rangeAnxiety`, `envPreference`
- Backend `TasteParameters` (types.py) is generalized with 7 fields: `beta_cost`, `asc`, `betas`, `calibrate`, `fixed`, `reference_alternative`
- Spike must decide whether `TechnologySet.taste_parameter_overrides` uses frontend type, backend type, or a new domain-specific schema
- Decision affects story 28.4 (wizard UI) implementation

**State Key Management Consideration:**
- Domain-specific keys should use `{domain}_{key}` pattern (e.g., `heating_incumbent`, `vehicle_incumbent`) to prevent collisions
- Existing shared keys: `DISCRETE_CHOICE_RESULT_KEY`, `DISCRETE_CHOICE_METADATA_KEY`, `DECISION_LOG_KEY`
- New keys to consider: `TRANSITION_LOG_KEY`, `TECHNOLOGY_SET_KEY`
- Step ordering must prevent interleaving domain steps (e.g., all heating steps before vehicle steps)

**Multi-Domain Considerations:**
- When multiple domains are enabled (e.g., heating + vehicle), state updates must not overwrite each other
- DecisionRecordStep must capture per-domain results to prevent data loss
- EngineConfigCompiler should order steps by domain to respect dependencies

## References

- [Source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md`](../planning-artifacts/sprint-change-proposal-2026-04-26.md) Section 4.2 — EPIC-28 story list and spike questions
- [Source: `_bmad-output/planning-artifacts/epics.md`](../planning-artifacts/epics.md) — Epic 28 definition and story 28.0 description
- [Source: `src/reformlab/discrete_choice/types.py`](../../src/reformlab/discrete_choice/types.py) — Core discrete choice types
- [Source: `src/reformlab/discrete_choice/domain.py`](../../src/reformlab/discrete_choice/domain.py) — DecisionDomain protocol
- [Source: `src/reformlab/discrete_choice/step.py`](../../src/reformlab/discrete_choice/step.py) — DiscreteChoiceStep orchestrator integration
- [Source: `src/reformlab/discrete_choice/heating.py`](../../src/reformlab/discrete_choice/heating.py) — Heating domain and state update pattern
- [Source: `src/reformlab/discrete_choice/vehicle.py`](../../src/reformlab/discrete_choice/vehicle.py) — Vehicle domain and state update pattern
- [Source: `src/reformlab/discrete_choice/decision_record.py`](../../src/reformlab/discrete_choice/decision_record.py) — DecisionRecord and DecisionRecordStep
- [Source: `src/reformlab/orchestrator/types.py`](../../src/reformlab/orchestrator/types.py) — YearState and OrchestratorConfig
- [Source: `src/reformlab/computation/types.py`](../../src/reformlab/computation/types.py) — PopulationData schema
- [Source: `src/reformlab/server/models.py`](../../src/reformlab/server/models.py) — Pydantic API models
- [Source: `frontend/src/types/workspace.ts`](../../frontend/src/types/workspace.ts) — Frontend workspace types
- [Source: `_bmad-output/planning-artifacts/architecture-diagrams.md`](../planning-artifacts/architecture-diagrams.md) — System architecture diagrams

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References
No debugging required — this is an architect spike, not implementation.

### Completion Notes List
- Story 28.0 is an architect spike, not implementation
- Deliverable is ADR document at `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md`
- All 8 spike questions answered with chosen options, rejected alternatives, and concrete schema definitions
- Stories 28.1–28.5 sized concretely with SP estimates (5+5+5+3+3 = 21 SP)
- Error handling specified for all failure modes with `{what, why, fix}` pattern
- Backward compatibility path defined for populations without incumbent columns
- Taste parameter override decision deferred to Story 28.4 per sprint-change-proposal guidance
- ADR pending PM sign-off before implementation stories proceed
- sprint-status.yaml updated to `pending-pm-review`

### File List
_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md (created)
_bmad-output/implementation-artifacts/sprint-status.yaml (modified)
_bmad-output/implementation-artifacts/28-0-architect-spike-technology-set-contract-and-population-state-transition-model.md (modified)
