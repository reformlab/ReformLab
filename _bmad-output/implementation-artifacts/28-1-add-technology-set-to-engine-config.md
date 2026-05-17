# Story 28.1: Add `technology_set` to `EngineConfig`; expose API and persistence

Status: ready-for-dev

## Story

As an analyst configuring an investment-decisions scenario,
I want a typed `technology_set` on the engine configuration that names which technologies are in scope per domain, with a stable version and a fully-embedded snapshot for reproducibility,
so that future stories (population schema, choice writeback, wizard UI, multi-period regression) have a canonical contract to consume.

## Acceptance Criteria

1. Given the new types in `frontend/src/types/workspace.ts`, when imported, then the module exports `DecisionDomainKey`, `TechnologyAlternative`, `DomainTechnologySet`, and `TechnologySet` matching the spike's Section 2.1 shapes; `EngineConfig.technologySet?: TechnologySet | null` is added without breaking any existing consumer.
2. Given the new Python value object at `src/reformlab/discrete_choice/technology_set.py`, when imported, then it exports `DomainTechnologySet` and `TechnologySet` as frozen dataclasses, with a `to_choice_set(domain: str) -> ChoiceSet` method that materialises the existing `ChoiceSet` from existing `Alternative` instances. No mutation of `ChoiceSet` is introduced.
3. Given the new API endpoint `GET /api/discrete-choice/technology-sets/default?domain=heating`, when called with `domain=heating`, then the response is a `DomainTechnologySet` JSON shape representing the canonical French set (5 heating alternatives, including `keep_current` as `referenceAlternativeId`); `domain=vehicle` returns the canonical vehicle set (6 alternatives). Unknown domain → 4xx.
4. Given a scenario edit where the user populates `engineConfig.technologySet`, when the scenario is persisted to localStorage and reloaded, then the technology set is restored byte-for-byte (round-trip serialisation tested).
5. Given a scenario with `investmentDecisionsEnabled === false`, when persisted, then `technologySet` may be `null` or absent; the orchestrator must short-circuit (no validation, no writeback, no manifest snapshot of the set).
6. Given a contract test posting a `TechnologySet` JSON shape to `POST /api/runs`, when the run completes, then the manifest's `technology_set` field round-trips the same shape (this asserts TS-Python schema parity per the spike's risk 10.2).
7. Given an old scenario loaded from localStorage without a `technologySet` field, when restored with `investmentDecisionsEnabled === true`, then the migration in `useScenarioPersistence` falls back to the legacy `default_heating_domain_config` + `default_vehicle_domain_config` and emits a manifest warning when the run executes.

## Tasks / Subtasks

- [ ] Frontend types (AC: #1)
  - [ ] Add `DecisionDomainKey`, `TechnologyAlternative`, `DomainTechnologySet`, `TechnologySet` to `frontend/src/types/workspace.ts`
  - [ ] Extend `EngineConfig` with `technologySet?: TechnologySet | null`
  - [ ] Update any TypeScript consumer that constructs `EngineConfig` (search for `EngineConfig` instantiation; many will not need to change because the field is optional)
- [ ] Backend value object (AC: #2)
  - [ ] New file `src/reformlab/discrete_choice/technology_set.py` with the two frozen dataclasses and the `to_choice_set` method
  - [ ] Re-export from `src/reformlab/discrete_choice/__init__.py` if there's a public API there
- [ ] Canonical-set API endpoint (AC: #3)
  - [ ] Add a new route `GET /api/discrete-choice/technology-sets/default` in `src/reformlab/server/routes/`
  - [ ] Backed by a fixture file or in-code constant exposing the canonical `fr-default-2026-04-26` set: 5 heating alternatives (including `keep_current`) and 6 vehicle alternatives
  - [ ] Reference alternative ids: `keep_current` for heating, `keep_current` for vehicle (or domain-specific equivalents)
  - [ ] Backend tests for both domains plus unknown-domain 4xx
- [ ] Persistence (AC: #4, #7)
  - [ ] Update `useScenarioPersistence` (`frontend/src/hooks/useScenarioPersistence.ts`) to serialise/deserialise `technologySet`
  - [ ] Add a migration path: scenarios with `investmentDecisionsEnabled === true` but no `technologySet` keep working (legacy default-config fallback)
  - [ ] Round-trip test: serialise → reload → assert byte-equal
- [ ] Short-circuit when disabled (AC: #5)
  - [ ] Verify the orchestrator (`src/reformlab/orchestrator/runner.py`) does not invoke any technology-set validation when `investmentDecisionsEnabled === false`
  - [ ] Add a backend test asserting a run with `investmentDecisionsEnabled === false` succeeds even when `technology_set` is omitted
- [ ] Contract roundtrip test (AC: #6)
  - [ ] New test `tests/server/test_technology_set_roundtrip.py`: post a TechnologySet JSON, run an orchestrator, read the manifest, assert schema equivalence
  - [ ] This test enforces the TS↔Python parity called out in spike risk 10.2
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/`
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

### Critical Architecture Constraints (Source: project-context.md)

**Python Language Rules** (MUST follow — no exceptions):
- **Every file starts with** `from __future__ import annotations` — this is non-negotiable
- **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations or would create circular dependencies
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; structural (duck) typing only
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]`
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception`

**API Error Pattern** (MUST follow):
```python
raise HTTPException(
    status_code=422,
    detail={
        "what": "Invalid technology_set configuration",
        "why": f"Unknown domain: {domain}",
        "fix": f"Use one of: {', '.join(VALID_DOMAINS)}",
    },
)
```

**Critical Don't-Miss Rules**:
- **Never import OpenFisca outside adapter modules** — absolute architectural boundary
- **Determinism is non-negotiable** — every run must be reproducible; seeds explicit and logged
- **Data contracts fail loudly** — validation at ingestion boundaries is blocking
- **Assumption transparency** — every run produces a manifest (JSON) with assumptions, versions, seeds

### Existing Code Patterns (Reference for Implementation)

**Backend Frozen Dataclass Pattern** (from `src/reformlab/discrete_choice/types.py:24-38`):
```python
@dataclass(frozen=True)
class Alternative:
    """A single alternative in a decision domain."""
    id: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
```

**ChoiceSet Pattern** (from `src/reformlab/discrete_choice/types.py:40-76`):
```python
@dataclass(frozen=True)
class ChoiceSet:
    """An ordered set of alternatives for a decision domain."""
    alternatives: tuple[Alternative, ...]

    def __post_init__(self) -> None:
        # Validates uniqueness and non-empty
        # MUST follow similar pattern for DomainTechnologySet
```

**Domain Config Pattern** (from `src/reformlab/discrete_choice/vehicle.py:52-91`):
```python
@dataclass(frozen=True)
class VehicleDomainConfig:
    alternatives: tuple[Alternative, ...]
    cost_column: str = "total_vehicle_cost"
    entity_key: str = "menage"
    taste_parameters: TasteParameters | None = None
```

**Frontend EngineConfig Pattern** (from `frontend/src/types/workspace.ts`):
```typescript
export interface EngineConfig {
  startYear: number;
  endYear: number;
  seed?: number;
  investmentDecisionsEnabled: boolean | null;
  logitModel: "multinomial_logit" | "nested_logit" | "mixed_logit" | null;
  discountRate: number;
  // ADD: technologySet?: TechnologySet | null;
}
```

**API Route Pattern** (from `src/reformlab/server/routes/categories.py`):
```python
router = APIRouter()

@router.get("", response_model=list[CategoryItem])
async def list_categories() -> list[CategoryItem]:
    """Return all policy categories with metadata."""
    # Returns canonical data as Pydantic models
```

**Pydantic Model Pattern** (from `src/reformlab/server/models.py:196-209`):
```python
class CategoryItem(BaseModel):
    """Policy category metadata — Story 25.1, AC-1."""
    id: str
    label: str
    columns: list[str]
    compatible_types: list[str]
    formula_explanation: str
    description: str
```

### Testing Standards Summary

**Backend Testing** (from project-context.md):
- Mirror source structure: `tests/discrete_choice/test_technology_set.py`
- Class-based test grouping: `TestTechnologySetValidation`, `TestTechnologySetAPI`
- Fixtures in `conftest.py` — build PyArrow tables inline
- Direct assertions: `assert result == expected`
- Use `pytest.raises(DiscreteChoiceError, match="...")` for errors
- Reference story/AC in docstrings: `# Story 28.1 / AC-7`

**Frontend Testing** (from MEMORY.md):
- Vitest with `vi.mock("@/api/technology-sets")` for API mocks
- `ResizeObserver` polyfill needed for Recharts tests
- Test localStorage round-trip with `beforeEach` cleanup

**Quality Gates** (must all pass before marking done):
```bash
uv run ruff check src/ tests/
uv run mypy src/
npm run typecheck  # in frontend/
npm run lint       # in frontend/
uv run pytest tests/
npm test           # in frontend/
```

### Spike ADR Specifications (Source: Story 28.0 output)

The architect spike produced an ADR at `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md` with:

**Section 2: Backend TechnologySet Schema**:
```python
@dataclass(frozen=True)
class TechnologySet:
    version: str  # e.g., "fr-default-2026-04-26"
    domains: dict[str, DomainTechnologySet]

    def to_choice_set(self, domain: str) -> ChoiceSet:
        """Materialize ChoiceSet for domain from stored alternatives."""
```

**Section 2.1: Frontend TypeScript Types**:
```typescript
type DecisionDomainKey = "heating" | "vehicle";

interface TechnologyAlternative {
  id: string;
  name: string;
}

interface DomainTechnologySet {
  domain: DecisionDomainKey;
  alternatives: TechnologyAlternative[];
  referenceAlternativeId: string;
}

interface TechnologySet {
  version: string;
  domains: Record<DecisionDomainKey, DomainTechnologySet>;
}
```

**Section 5: Adapter Invariance** — No `ComputationAdapter` change in this story

**Section 6: Error Handling** — Use `{what, why, fix}` pattern for all errors

**Section 7: Backward Compatibility** — Scenarios without `technologySet` use legacy defaults

### Project Structure Notes

**New Files** (to create):
- `src/reformlab/discrete_choice/technology_set.py` — Backend frozen dataclasses
- `src/reformlab/server/routes/technology_sets.py` — Canonical-set API endpoint
- `tests/server/test_technology_set_roundtrip.py` — Contract round-trip tests
- `tests/discrete_choice/test_technology_set.py` — Unit tests for value objects

**Modified Files**:
- `frontend/src/types/workspace.ts` — Add `TechnologySet` types and extend `EngineConfig`
- `frontend/src/hooks/useScenarioPersistence.ts` — Serialize/deserialize `technologySet`
- `src/reformlab/discrete_choice/__init__.py` — Re-export new types (if public API)
- `src/reformlab/orchestrator/runner.py` — Short-circuit when disabled (AC-5)

**No Deletions** — All changes are additive

### Backward Compatibility Strategy

Per spike ADR Section 7:
1. **Scenarios without `technologySet`** → Use legacy default domain configs
2. **Populations without incumbent columns** → Graceful degradation (Story 28.2)
3. **Empty `technologySet`** → Treated as "use all alternatives"
4. **Disabled decisions** → No validation, no writeback, short-circuit in orchestrator

### Implementation Sequence Recommendation

1. **Start with backend types** — `technology_set.py` with frozen dataclasses
2. **Add canonical-set API** — Simple GET endpoint returning default sets
3. **Add frontend types** — TypeScript interfaces matching backend schema
4. **Implement persistence** — localStorage round-trip in useScenarioPersistence
5. **Add orchestrator short-circuit** — Skip when decisions disabled
6. **Write contract test** — TS↔Python parity validation
7. **Add migration path** — Legacy default fallback for old scenarios

### Dependencies Between Stories

- **Story 28.0** (architect spike) — DONE — provides ADR with schema definitions
- **Story 28.1** (this story) — IN PROGRESS — EngineConfig + API + persistence
- **Story 28.2** (population schema) — BACKLOG — extends PopulationData with incumbents
- **Story 28.3** (writeback) — BACKLOG — wires DiscreteChoiceStep outputs to population
- **Story 28.4** (wizard) — BACKLOG — consumes canonical-set API from this story
- **Story 28.5** (regression) — BACKLOG — multi-period decision runs

### References

- [Source: `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md`](../planning-artifacts/spike-investment-decisions-technology-set.md) — ADR with complete schema definitions
- [Source: `src/reformlab/discrete_choice/types.py`](../../src/reformlab/discrete_choice/types.py) — Alternative, ChoiceSet patterns
- [Source: `src/reformlab/discrete_choice/vehicle.py`](../../src/reformlab/discrete_choice/vehicle.py) — VehicleDomainConfig pattern
- [Source: `src/reformlab/server/models.py`](../../src/reformlab/server/models.py) — Pydantic v2 patterns
- [Source: `frontend/src/types/workspace.ts`](../../frontend/src/types/workspace.ts) — EngineConfig structure
- [Source: `_bmad-output/project-context.md`](../project-context.md) — Project architecture rules
- [Source: `.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md`](../../../../.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md) — Development conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — story creation phase only.

### Completion Notes List

- Story 28.1 has been enhanced with comprehensive developer context from project-context.md, MEMORY.md, and existing code analysis
- All architecture patterns, existing code references, and implementation standards have been documented
- The story includes detailed ACs with specific file locations and code patterns
- Backend and frontend testing standards are specified with quality gate commands
- Spike ADR references provide complete schema definitions for implementation
- Backward compatibility strategy is clearly defined
- Implementation sequence recommendation provides logical development order
- Story status is `ready-for-dev` — awaiting developer agent to begin implementation

### File List

**Story File**:
- `_bmad-output/implementation-artifacts/28-1-add-technology-set-to-engine-config.md` (enhanced with comprehensive context)

**New Files to Create** (per implementation):
- `src/reformlab/discrete_choice/technology_set.py` — Backend frozen dataclasses
- `src/reformlab/server/routes/technology_sets.py` — Canonical-set API endpoint
- `tests/server/test_technology_set_roundtrip.py` — Contract round-trip tests
- `tests/discrete_choice/test_technology_set.py` — Unit tests for value objects

**Files to Modify** (per implementation):
- `frontend/src/types/workspace.ts` — Add `TechnologySet` types and extend `EngineConfig`
- `frontend/src/hooks/useScenarioPersistence.ts` — Serialize/deserialize `technologySet`
- `src/reformlab/discrete_choice/__init__.py` — Re-export new types
- `src/reformlab/orchestrator/runner.py` — Short-circuit when decisions disabled

**Reference Files Analyzed**:
- `src/reformlab/discrete_choice/types.py` — Alternative, ChoiceSet patterns
- `src/reformlab/discrete_choice/vehicle.py` — VehicleDomainConfig pattern
- `src/reformlab/discrete_choice/heating.py` — Heating domain patterns
- `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep orchestrator integration
- `src/reformlab/server/models.py` — Pydantic v2 API patterns
- `src/reformlab/server/routes/categories.py` — Simple GET endpoint pattern
- `frontend/src/types/workspace.ts` — Frontend workspace types
- `_bmad-output/project-context.md` — Project architecture rules
- `.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md` — Development conventions
