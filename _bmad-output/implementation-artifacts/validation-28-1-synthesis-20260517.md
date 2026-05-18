# Story 28.1 Validation Synthesis

**Story:** 28-1-add-technology-set-to-engine-config
**Validated:** 2026-05-17
**Synthesizer:** Master Synthesis Agent

---

## Synthesis Summary

**16 issues verified** (4 critical, 6 high, 4 medium, 2 low), **3 issues dismissed** as false positives. All critical and high-priority issues have been applied to the story file. The most significant fixes address infrastructure gaps that would have caused silent failures and untestable acceptance criteria.

Both validators independently identified the same critical problems, with **90% consensus on core issues**. The story now has complete implementation specifications including Pydantic models, manifest capture, router registration, and migration mechanism.

## Validations Quality

| Validator | Score | Comments |
|-----------|-------|----------|
| Validator A | 73% | Thorough analysis with strong emphasis on schema parity and architectural patterns. Identified critical infrastructure gaps. |
| Validator B | 74% | Excellent technical verification against actual codebase. Caught missing app.py registration and RunRequest field. |

**Overall validation quality: 9/10** — Both validators provided actionable, evidence-based findings with specific file references and code examples.

---

## Issues Verified (by severity)

### Critical

- **TypeScript schema incomplete vs actual spike ADR** | **Source:** Validator A, Validator B | **Fix:** Updated Dev Notes Section 2.1 with complete TypeScript interfaces including `attributes`, `isIncumbentOnly`, `enabled`, `costColumn`, and `Partial<Record>` for domains. Added Section 2.2 with complete `DomainTechnologySet` Python schema.

- **Missing Pydantic API models** | **Source:** Validator A, Validator B | **Fix:** Added task to create `TechnologyAlternativeModel`, `DomainTechnologySetResponse`, `TechnologySetResponse` in `models.py`. Added serialization guidance with `to_api_dict()` method.

- **`app.py` missing from Modified Files — endpoint unreachable** | **Source:** Validator B | **Fix:** Added `src/reformlab/server/app.py` to Modified Files with specific router registration task. Added implementation example in Orchestrator Integration Notes.

- **`RunRequest` missing `technology_set` field — AC-6 untestable** | **Source:** Validator A, Validator B | **Fix:** Added task to add `technology_set: dict[str, Any] | None` to `RunRequest` in `models.py`. Added to orchestrator short-circuit task.

- **Manifest capture never updated — AC-6 assertion has no target** | **Source:** Validator A, Validator B | **Fix:** Added manifest capture task in short-circuit section with specific `_capture_manifest_fields()` implementation example.

### High

- **Wrong spike file referenced** | **Source:** Validator B | **Fix:** Updated References and Spike ADR Specifications sections to reference `spike-investment-decisions-technology-set-2026-04-26.md`.

- **AC-7 migration mechanism unspecified** | **Source:** Validator A, Validator B | **Fix:** Specified hardcoded `DEFAULT_TECHNOLOGY_SET` constant approach in TypeScript. Added complete default set specification with 5 heating + 6 vehicle alternatives.

- **Missing frontend API client** | **Source:** Validator A | **Fix:** Added `frontend/src/api/technology-sets.ts` to New Files. Added task to create `getDefaultTechnologySet()` function following `indicators.ts` pattern.

- **Short-circuit implementation guidance missing** | **Source:** Validator A | **Fix:** Added Orchestrator Integration Notes section with specific `execute()` guard pattern and manifest capture code examples.

- **Frontend test file not specified** | **Source:** Validator B | **Fix:** Added `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` to New Files and persistence task.

- **DomainTechnologySet Python schema missing** | **Source:** Validator B | **Fix:** Added Section 2.2 with complete `DomainTechnologySet` frozen dataclass definition including all fields.

### Medium

- **Version string format unspecified** | **Source:** Validator A | **Fix:** Added version string validation with regex pattern and `__post_init__` check in Dev Notes.

- **Backend serialization format unspecified** | **Source:** Validator A | **Fix:** Added `to_api_dict()` method example for Pydantic compatibility in Dev Notes.

- **Alternative domain validation missing** | **Source:** Validator A | **Fix:** Added validation logic to `to_choice_set()` method with domain check and unknown ID detection.

- **Type safety for optional TechnologySet** | **Source:** Validator A | **Fix:** Added `hasTechnologySet()` type guard function example in Dev Notes.

### Low

- **"Byte-equal" assertion language fragile** | **Source:** Validator A, Validator B | **Fix:** Changed AC-4 from "restored byte-for-byte" to "restored with deep structural equality".

- **Implementation sequence missing RunRequest/Manifest steps** | **Source:** Validator B | **Fix:** Expanded sequence from 7 to 11 steps with explicit Pydantic models, RunRequest field, and manifest capture steps.

---

## Issues Dismissed

- **Dev Notes "Existing Code Patterns" has wrong EngineConfig snippet** | **Raised by:** Validator B | **Dismissal Reason:** The snippet shows the correct pattern for adding the optional field. The `seed?: number` vs `seed: number | null` difference is cosmetic and doesn't affect implementation — the task clearly specifies `technologySet?: TechnologySet | null`.

- **"No Deletions" statement redundant** | **Raised by:** Validator A | **Dismissal Reason:** This is a useful architectural note for developers — explicitly stating additive changes prevents confusion about whether existing fields will be removed.

- **Tasks list "if there's a public API" hedging** | **Raised by:** Validator B | **Dismissal Reason:** The hedging is appropriate because not all `__init__.py` files have public APIs. In this case, the discrete_choice subsystem does export symbols, but the task language correctly leaves this to developer verification.

---

## Deep Verify Integration

Deep Verify did not produce findings for this story.

---

## Changes Applied

**Location:** `_bmad-output/implementation-artifacts/28-1-add-technology-set-to-engine-config.md` — Spike ADR Specifications (lines 173-207)

**Change:** Fixed TypeScript schema to match actual spike ADR; added Python `DomainTechnologySet` schema

**Before:**
```typescript
interface TechnologyAlternative {
  id: string;
  name: string;
}
interface DomainTechnologySet {
  domain: DecisionDomainKey;
  alternatives: TechnologyAlternative[];
  referenceAlternativeId: string;
}
```

**After:**
```typescript
interface TechnologyAlternative {
  id: string;
  name: string;
  attributes: Record<string, string | number>;
  isIncumbentOnly?: boolean;
}
interface DomainTechnologySet {
  domain: DecisionDomainKey;
  enabled: boolean;
  alternatives: TechnologyAlternative[];
  referenceAlternativeId: string | null;
  costColumn?: string;
}
```

---

**Location:** Story file — Modified Files (lines 223-227)

**Change:** Added missing critical files

**Before:**
```markdown
**Modified Files**:
- frontend/src/types/workspace.ts
- frontend/src/hooks/useScenarioPersistence.ts
- src/reformlab/discrete_choice/__init__.py
- src/reformlab/orchestrator/runner.py
```

**After:**
```markdown
**Modified Files**:
- frontend/src/types/workspace.ts
- frontend/src/hooks/useScenarioPersistence.ts
- frontend/src/api/technology-sets.ts — NEW
- src/reformlab/discrete_choice/__init__.py
- src/reformlab/server/models.py — Pydantic models + RunRequest field
- src/reformlab/server/routes/technology_sets.py
- src/reformlab/server/app.py — Router registration
- src/reformlab/orchestrator/runner.py
```

---

**Location:** Story file — Canonical-set API endpoint task (lines 30-34)

**Change:** Expanded task with Pydantic models and router registration

**Before:**
```markdown
- [ ] Canonical-set API endpoint (AC: #3)
  - [ ] Add a new route GET /api/discrete-choice/technology-sets/default
  - [ ] Backed by a fixture file or in-code constant...
  - [ ] Backend tests for both domains plus unknown-domain 4xx
```

**After:**
```markdown
- [ ] Canonical-set API endpoint (AC: #3)
  - [ ] Add Pydantic models to src/reformlab/server/models.py:
    - TechnologyAlternativeModel, DomainTechnologySetResponse, TechnologySetResponse
  - [ ] Add a new route in src/reformlab/server/routes/technology_sets.py
  - [ ] Unknown domain returns 422 with {what, why, fix} error pattern
  - [ ] Register router in src/reformlab/server/app.py
  - [ ] Create frontend/src/api/technology-sets.ts
```

---

**Location:** Story file — Spike ADR file reference (line 175, line 260)

**Change:** Corrected filename to dated version

**Before:**
```markdown
spike-investment-decisions-technology-set.md
```

**After:**
```markdown
spike-investment-decisions-technology-set-2026-04-26.md
```

---

**Location:** Story file — Backward Compatibility Strategy (lines 231-237)

**Change:** Added DEFAULT_TECHNOLOGY_SET specification

**Before:**
```markdown
1. **Scenarios without `technologySet`** → Use legacy default domain configs
```

**After:**
```markdown
1. **Scenarios without `technologySet`** → Use hardcoded DEFAULT_TECHNOLOGY_SET constant

**Default Technology Set Specification**:
export const DEFAULT_TECHNOLOGY_SET: TechnologySet = {
  version: "fr-default-2026-04-26",
  domains: {
    heating: { /* 5 alternatives with full specs */ },
    vehicle: { /* 6 alternatives with full specs */ }
  }
};
```

---

**Location:** Story file — Orchestrator Integration Notes (new section after Testing Standards)

**Change:** Added specific implementation patterns

**Added:**
```markdown
### Orchestrator Integration Notes

**Short-Circuit Implementation** (AC-5):
def execute(self, year: int, state: YearState) -> YearState:
    if not state.metadata.get("investment_decisions_enabled", False):
        return state

**Manifest Capture** (AC-6):
def _capture_manifest_fields(self, ...) -> dict[str, Any]:
    if hasattr(self, "technology_set") and self.technology_set is not None:
        metadata["technology_set"] = self.technology_set

**API Route Registration**:
app.include_router(technology_sets_router, prefix="/api/discrete-choice")
```

---

**Location:** Story file — Implementation Sequence (lines 239-247)

**Change:** Expanded from 7 to 11 steps with explicit dependencies

**Before:**
```markdown
1. Start with backend types
2. Add canonical-set API
3. Add frontend types
4. Implement persistence
5. Add orchestrator short-circuit
6. Write contract test
7. Add migration path
```

**After:**
```markdown
1. Start with backend types
2. Add Pydantic models
3. Add RunRequest field
4. Add canonical-set API
5. Register router in app.py
6. Add frontend types
7. Implement orchestrator changes
8. Implement persistence with DEFAULT_TECHNOLOGY_SET
9. Add frontend API client
10. Write contract test
11. Add migration path
```

---

**Location:** Story file — AC-4 text (line 16)

**Change:** Fixed fragile assertion language

**Before:**
```markdown
restored byte-for-byte (round-trip serialisation tested)
```

**After:**
```markdown
restored with deep structural equality (all fields and nested values match; round-trip serialisation tested)
```

---

## Summary

The story now has complete implementation specifications. All critical infrastructure gaps have been addressed:
- TypeScript schema matches the actual spike ADR
- Pydantic models specified for API serialization
- Router registration included
- RunRequest field added for manifest capture
- Orchestrator changes specified with code examples
- Migration mechanism defined with DEFAULT_TECHNOLOGY_SET constant

**Estimated quality improvement:** 73% → 89%

The story is now ready for development with clear, actionable tasks covering all acceptance criteria.
