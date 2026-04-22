# Story 26.6: Add Deterministic Scenario Name Suggestions from Policy Set and Population Context

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want scenario names to be suggested automatically based on my policy set and population selections,
so that I don't have to manually name every scenario but still have control when I want a custom name.

## Acceptance Criteria

1. Given a new scenario has policy set "Carbon Tax" and population "FR Synthetic 2024", when the name has not been manually edited, then the suggested name is "Carbon Tax — FR Synthetic 2024".
2. Given only a policy set is selected, then the suggested name uses the policy set with a sensible fallback suffix.
3. Given the analyst manually edits the scenario name, when policy set or population changes later, then the manual name is not overwritten.
4. Given a named scenario is cloned, when the clone opens, then it follows the clone naming rule rather than reverting to a generic "New Scenario".

## Tasks / Subtasks

- [ ] Update scenario naming format to use em dash separator (AC: #1, #2)
  - [ ] Modify `generateScenarioSuggestion()` in `frontend/src/utils/naming.ts` to use " — " (em dash) instead of " (" (parentheses)
  - [ ] Change format from `"{portfolioName} ({populationShortName})"` to `"{portfolioName} — {populationShortName}"`
  - [ ] Ensure population-only fallback uses em dash format: `"Untitled — {populationShortName}"`
  - [ ] Keep "Untitled Scenario" as final fallback when no context available

- [ ] Update existing tests for new naming format (AC: #1, #2)
  - [ ] Update `frontend/src/utils/__tests__/naming.test.ts` to expect em dash format
  - [ ] Update test assertions for `generateScenarioSuggestion()` with portfolio + population
  - [ ] Update test assertions for population-only fallback
  - [ ] Add new test case for "Policy Set — Population" format

- [ ] Verify auto-update effect works with new format (AC: #3)
  - [ ] Verify AppContext auto-update effect (lines 496-535) works correctly with new em dash format
  - [ ] Verify manual edit freeze (`manuallyEditedScenarioNames`) still prevents auto-updates
  - [ ] Verify demo scenario name is never auto-updated

- [ ] Verify clone naming works with new format (AC: #4)
  - [ ] Verify `generateScenarioCloneName()` preserves em dash in clone names
  - [ ] Verify clone names get " (copy)" suffix correctly appended
  - [ ] Verify collision handling works with em dash format

- [ ] Add regression tests for naming edge cases (AC: #1, #2, #3, #4)
  - [ ] Test full context: policy set + population → "Policy Set — Population"
  - [ ] Test policy set only → "Policy Set" (no suffix)
  - [ ] Test population only → "Untitled — Population"
  - [ ] Test no context → "Untitled Scenario"
  - [ ] Test manual edit freeze with auto-update
  - [ ] Test clone naming preserves em dash format

## Dev Notes

### Current State Analysis

**What's Already Implemented (Story 22.3):**
- `generateScenarioSuggestion()` in `frontend/src/utils/naming.ts` (lines 188-214)
- Manual edit tracking with `manuallyEditedScenarioNames` Set in AppContext
- Auto-update effect in `AppContext.tsx` (lines 496-535)
- Clone naming with `generateScenarioCloneName()` (lines 255-268)
- Comprehensive test coverage in `frontend/src/utils/__tests__/naming.test.ts`

**Current Naming Format (Story 22.3):**
```typescript
// Current implementation uses parentheses
const populationPart = population ? ` (${getPopulationShortName(population)})` : "";
return `${portfolioName}${populationPart}`;
// Examples:
// - "Carbon Tax" + "FR Synthetic 2024" → "Carbon Tax (FR Synthetic 2024)"
// - Population only → "Untitled (FR Synthetic 2024)"
```

**Required Naming Format (Story 26.6):**
```typescript
// New implementation uses em dash
const populationPart = population ? ` — ${getPopulationShortName(population)}` : "";
return `${portfolioName}${populationPart}`;
// Examples:
// - "Carbon Tax" + "FR Synthetic 2024" → "Carbon Tax — FR Synthetic 2024"
// - Population only → "Untitled — FR Synthetic 2024"
```

### Architecture Context

**Naming Function Signature:**
```typescript
// frontend/src/utils/naming.ts (lines 188-194)
export function generateScenarioSuggestion(
  portfolioName: string | null,           // Policy set name (from portfolioName field)
  selectedPopulationId: string,           // Primary population ID
  populations: readonly Population[],     // All available populations
  templates: readonly Template[],         // All available templates (for composition fallback)
  composition: readonly CompositionEntry[], // Policy composition (if no portfolioName)
): string
```

**Policy Set Terminology Note:**
- The codebase uses `portfolioName` (legacy terminology from EPIC-17)
- Epic 25 introduces "policy set" as the user-facing term
- The `portfolioName` field stores the policy set name
- Story 26.6 updates the display format to use em dash while keeping `portfolioName` as the field name

**Manual Edit Tracking:**
```typescript
// AppContext.tsx (lines 259-282)
const updateScenarioField = useCallback(<K extends keyof WorkspaceScenario>(
  field: K,
  value: WorkspaceScenario[K],
) => {
  if (field === "name" && current.id !== DEMO_SCENARIO_ID) {
    setManuallyEditedScenarioNames((prev) => {
      const updated = new Set(prev);
      updated.add(current.id);
      saveManuallyEditedNames(updated);
      return updated;
    });
  }
  return { ...current, [field]: value };
}, []);
```

**Auto-Update Effect:**
```typescript
// AppContext.tsx (lines 496-535)
useEffect(() => {
  if (!activeScenario) return;
  const isManuallyEdited = manuallyEditedScenarioNames.has(activeScenario.id);
  const isDemo = activeScenario.id === DEMO_SCENARIO_ID;

  if (isDemo) return;           // Demo name never changes
  if (isManuallyEdited) return;  // Manual edits freeze the name

  const suggestedName = generateScenarioSuggestion(
    selectedPortfolioName,
    selectedPopulationId,
    populations,
    templates,
    [],
  );

  if (suggestedName !== activeScenario.name) {
    setActiveScenario(prev => prev ? { ...prev, name: suggestedName } : null);
  }
}, [activeScenario?.portfolioName, activeScenario?.populationIds, /* ... */]);
```

**Dependencies:**
- selectedPortfolioName - Global state for currently selected policy set
- selectedPopulationId - Global state for currently selected population
- populations - Array of PopulationLibraryItem from usePopulations()
- templates - Array of Template from useTemplates()

### Implementation Strategy

**Phase 1: Update naming.ts**
1. Change line 196 from ` (${getPopulationShortName(population)})` to ` — ${getPopulationShortName(population)}`
2. Update line 200 from `return ${portfolioName}${populationPart}` to same (no change needed)
3. Update line 210 from `return Untitled${populationPart}` to same (no change needed)
4. Update docstring to reflect new em dash format

**Phase 2: Update tests**
1. Update `frontend/src/utils/__tests__/naming.test.ts` assertions
2. Change expected output from `"Portfolio (Population)"` to `"Portfolio — Population"`
3. Change expected output from `"Untitled (Population)"` to `"Untitled — Population"`

**Phase 3: Verify integrations**
1. AppContext auto-update effect works without changes (uses same function)
2. ScenarioStageScreen name input works without changes (displays activeScenario.name)
3. Clone naming works without changes (appends " (copy)" to whatever the name is)

**Phase 4: Add regression tests**
1. Test full context: "Carbon Tax — FR Synthetic 2024"
2. Test policy set only: "Carbon Tax"
3. Test population only: "Untitled — FR Synthetic 2024"
4. Test no context: "Untitled Scenario"
5. Test manual edit freeze with em dash format
6. Test clone preserves em dash: "Carbon Tax — FR Synthetic 2024 (copy)"

### Key Design Decisions

**Em Dash Character:**
- Use the em dash (—, U+2014) for separator
- Include spaces on both sides: ` — ` (space, em dash, space)
- This matches UX specification and provides clear visual separation

**Fallback Hierarchy:**
1. Policy set + population → "{Policy Set} — {Population}"
2. Policy set only → "{Policy Set}"
3. Population only → "Untitled — {Population}"
4. No context → "Untitled Scenario"

**Manual Edit Freeze:**
- Once a scenario name is manually edited, it's added to `manuallyEditedScenarioNames` Set
- Auto-update effect checks this Set and skips updates for manually edited names
- Demo scenario is never auto-updated (hardcoded ID check)

**Clone Naming:**
- Clones always get " (copy)" suffix appended to the original name
- Collision handling: " (copy 2)", " (copy 3)", etc.
- Em dash in original name is preserved in clone

### Project Structure Notes

**Files to Modify:**
- `frontend/src/utils/naming.ts` — Update `generateScenarioSuggestion()` format
- `frontend/src/utils/__tests__/naming.test.ts` — Update test assertions

**Files to Verify (no changes expected):**
- `frontend/src/contexts/AppContext.tsx` — Auto-update effect should work unchanged
- `frontend/src/components/screens/ScenarioStageScreen.tsx` — Name input should work unchanged
- `frontend/src/hooks/useScenarioPersistence.ts` — Persistence should work unchanged

**Type Definitions:**
- `WorkspaceScenario.name: string` — No change needed (still a string)
- `PortfolioListItem.name: string` — No change needed (policy set display name)
- `PopulationLibraryItem.name: string` — No change needed (population display name)

### Testing Strategy

**Unit Tests (naming.test.ts):**
```typescript
describe("generateScenarioSuggestion() with em dash format", () => {
  it("returns 'Policy Set — Population' for full context", () => {
    const result = generateScenarioSuggestion(
      "Carbon Tax",
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      [],
    );
    expect(result).toBe("Carbon Tax — FR Synthetic 2024");
  });

  it("returns 'Policy Set' for policy set only", () => {
    const result = generateScenarioSuggestion(
      "Carbon Tax",
      "",
      [],
      mockTemplates,
      [],
    );
    expect(result).toBe("Carbon Tax");
  });

  it("returns 'Untitled — Population' for population only", () => {
    const result = generateScenarioSuggestion(
      null,
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      [],
    );
    expect(result).toBe("Untitled — FR Synthetic 2024");
  });

  it("returns 'Untitled Scenario' for no context", () => {
    const result = generateScenarioSuggestion(
      null,
      "",
      [],
      mockTemplates,
      [],
    );
    expect(result).toBe("Untitled Scenario");
  });
});
```

**Integration Tests:**
- Verify AppContext auto-update works with em dash format
- Verify manual edit freeze prevents auto-update
- Verify clone naming preserves em dash

**Regression Tests:**
- Run all existing scenario-related tests
- Run all portfolio/policy set tests
- Run all population tests

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-26.6] — Story requirements and acceptance criteria
- [Source: frontend/src/utils/naming.ts#L188-L214] — Current `generateScenarioSuggestion()` implementation
- [Source: frontend/src/contexts/AppContext.tsx#L496-L535] — Auto-update effect implementation
- [Source: frontend/src/utils/__tests__/naming.test.ts] — Existing test coverage
- [Source: frontend/src/types/workspace.ts#L77-L90] — WorkspaceScenario type definition

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (story creation)

### Debug Log References

None — story created with comprehensive context from existing codebase analysis.

### Completion Notes List

Story 26.6 created with comprehensive developer context:

**Context Sources Analyzed:**
- Epic 26 Story 26.6 requirements and UX-DR15
- Existing `generateScenarioSuggestion()` implementation in `naming.ts`
- Auto-update effect and manual edit tracking in `AppContext.tsx`
- Test coverage in `naming.test.ts`
- Clone naming implementation

**Key Findings:**
- Story 22.3 already implemented scenario name suggestions with parentheses format
- Manual edit tracking and auto-update effect already exist and work correctly
- Only change needed: Replace " (" with " — " in the separator
- No type changes needed — `WorkspaceScenario.name` remains a string
- Clone naming automatically works with new format (just appends " (copy)")

**Implementation Strategy:**
1. Single-line change in `generateScenarioSuggestion()`: update separator from ` (${population})` to ` — ${population}`
2. Update test assertions to expect em dash format
3. Verify auto-update effect still works (no changes needed)
4. Add regression tests for edge cases

**Testing Strategy:**
- Update existing unit tests in `naming.test.ts`
- Verify AppContext auto-update integration works
- Add regression tests for all naming combinations

**Files to Modify:**
- `frontend/src/utils/naming.ts` — Update separator format
- `frontend/src/utils/__tests__/naming.test.ts` — Update test assertions

**Expected Changes:**
- 1 line changed in `naming.ts` (separator format)
- ~5-10 test assertions updated in `naming.test.ts`
- No type changes
- no AppContext changes

Status set to: ready-for-dev

### File List

- `_bmad-output/implementation-artifacts/26-6-add-deterministic-scenario-name-suggestions-from-policy-set-and-population-context.md`

## Change Log

### 2026-04-22: Story 26.6 Created

**Summary:** Create story for deterministic scenario name suggestions with em dash format

**Analysis:**
- Existing Story 22.3 implementation uses parentheses: `"Policy Set (Population)"`
- Story 26.6 requires em dash format: `"Policy Set — Population"`
- Manual edit tracking and auto-update effect already exist
- Single-line change in `generateScenarioSuggestion()` + test updates

**Implementation Scope:**
- Update `frontend/src/utils/naming.ts` separator format
- Update `frontend/src/utils/__tests__/naming.test.ts` assertions
- Verify auto-update effect works (no changes needed)
- Add regression tests for edge cases
