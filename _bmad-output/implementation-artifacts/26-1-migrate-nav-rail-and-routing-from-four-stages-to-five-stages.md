# Story 26.1: Migrate nav rail and routing from four stages to five stages

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want the navigation to reflect the canonical five-stage workflow (Policies → Population → Investment Decisions → Scenario → Run / Results / Compare),
so that I can move through the workspace in the sequence specified by UX Revision 4.1, with the old "Engine" terminology replaced by "Scenario", and Investment Decisions elevated to its own stage.

## Acceptance Criteria

1. Given the workspace renders, when the nav rail displays, then it shows exactly five stages in order: "Policies", "Population", "Investment Decisions", "Scenario", and "Run / Results / Compare".
2. Given the URL hash is `#engine` (legacy bookmark), when the app loads, then it resolves to the Scenario stage (hash changes to `#scenario`) without errors.
3. Given saved workspace state has `activeStage: "engine"` (from previous session), when restored via localStorage, then the active stage becomes "scenario".
4. Given Population is active, then Library, Build, and Explorer remain as stage-local sub-steps under Population (not promoted to top-level stages).
5. Given any five-stage nav item is clicked, then the correct stage content renders, the hash updates, and WorkflowNavRail shows the correct active state.
6. Given the mobile stage switcher renders at narrow width, then it shows five stage buttons matching the nav rail stages.
7. Given type validation runs, then StageKey includes "policies", "population", "investment-decisions", "scenario", "results" and explicitly excludes "engine".
8. Given Scenario stage is active, then the main panel renders EngineStageScreen (to be renamed in Story 26.3) with correct content.

## Tasks / Subtasks

- [ ] Update StageKey type and STAGES constant in workspace.ts (AC: #1, #7)
  - [ ] Add "investment-decisions" to StageKey type union
  - [ ] Replace "engine" with "scenario" in StageKey type union
  - [ ] Update VALID_STAGES Set to include all five new stage keys
  - [ ] Add "investment-decisions" stage entry to STAGES array with label "Investment Decisions" and activeFor array
  - [ ] Update "engine" stage entry to "scenario" with label "Scenario"
  - [ ] Update STAGES order: policies, population, investment-decisions, scenario, results
  - [ ] Verify results stage activeFor includes all sub-views: results, comparison, decisions, runner

- [ ] Update WorkflowNavRail component for five stages (AC: #1, #5)
  - [ ] Update isComplete() function switch statement to handle "investment-decisions" and "scenario" cases
  - [ ] Update getSummary() function switch statement to handle "investment-decisions" and "scenario" cases
  - [ ] Verify connecting lines render correctly between all five stages
  - [ ] Verify population sub-steps (Library, Build, Explorer) still render when population stage is active
  - [ ] Update comments referencing "four stages" to "five stages"

- [ ] Update MobileStageSwitcher component for five stages (AC: #6)
  - [ ] Verify STAGES import from workspace.ts includes five stages
  - [ ] Confirm horizontal scroll shows all five stage buttons
  - [ ] Verify active state highlighting works for all five stages

- [ ] Add hash routing migration for legacy #engine → #scenario (AC: #2)
  - [ ] Add migration logic in AppContext onHashChange effect
  - [ ] When hash is "engine", auto-redirect to "scenario" and update hash
  - [ ] Test bookmark navigation with #engine resolves correctly
  - [ ] Verify direct navigation to #scenario works without migration

- [ ] Add localStorage migration for activeStage: "engine" → "scenario" (AC: #3)
  - [ ] Add migration in loadStage() function in useScenarioPersistence.ts
  - [ ] When loaded stage is "engine", return "scenario" instead
  - [ ] Test returning user with saved "engine" stage migrates to "scenario"
  - [ ] Verify subsequent saves use "scenario" not "engine"

- [ ] Update App.tsx main content routing (AC: #8)
  - [ ] Add case for "investment-decisions" stage (placeholder or skip to next story)
  - [ ] Replace "engine" case with "scenario" case
  - [ ] Verify both stage keys render EngineStageScreen (ScenarioStageScreen comes in Story 26.3)
  - [ ] Update comments referencing four stages to five stages

- [ ] Update type guards and validation (AC: #7)
  - [ ] Update isValidStage() to exclude "engine" explicitly
  - [ ] Add tests for invalid legacy "engine" stage key
  - [ ] Verify TypeScript compilation rejects "engine" as valid StageKey

- [ ] Update WorkflowNavRail tests for five stages (AC: #1, #5)
  - [ ] Update "renders all four stage labels" test to assert five stages
  - [ ] Add tests for investment-decisions stage rendering
  - [ ] Add tests for scenario stage (formerly engine) rendering
  - [ ] Update completion tests for investment-decisions and scenario stages
  - [ ] Update navigation tests for all five stages
  - [ ] Add hash migration test for #engine → #scenario

- [ ] Update MobileStageSwitcher tests for five stages (AC: #6)
  - [ ] Update test to assert five stage buttons render
  - [ ] Verify all five stages are clickable and navigate correctly

- [ ] Add localStorage migration tests (AC: #3)
  - [ ] Test loadStage() returns "scenario" when localStorage has "engine"
  - [ ] Test returning user flow with migrated stage

- [ ] Non-regression: verify existing Population sub-steps work (AC: #4)
  - [ ] Test Library, Build, Explorer sub-steps still render under Population
  - [ ] Test sub-step navigation still works after five-stage migration
  - [ ] Verify population sub-step disabled states still function

## Dev Notes

### Architecture Context

**UX Revision 4.1 (from UX-DR6):** "The workspace must use a five-stage nav rail (Policies → Population → Investment Decisions → Scenario → Run/Results/Compare) as specified in UX Revision 4.1."

**Key Design Decision:** This story updates the nav rail and routing structure only. The InvestmentDecisionsStageScreen component creation happens in Story 26.2, and the EngineStageScreen rename to ScenarioStageScreen happens in Story 26.3. For this story, the "investment-decisions" stage can show a placeholder or the wizard can be rendered directly.

**Migration Strategy:**
- Hash routing: `#engine` → `#scenario` via client-side redirect
- localStorage: Read-time migration in `loadStage()` returns "scenario" for stored "engine"
- Type safety: StageKey excludes "engine" so TypeScript prevents new "engine" references
- Runtime: isValidStage() rejects "engine" explicitly

### Current State (After Epic 25)

**Four-Stage Structure (legacy):**
```typescript
// frontend/src/types/workspace.ts
export type StageKey = "policies" | "population" | "engine" | "results";
export const STAGES = [
  { key: "policies", label: "Policy", activeFor: ["policies"] },
  { key: "population", label: "Population", activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "engine", label: "Scenario", activeFor: ["engine"] },
  { key: "results", label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner"] },
];
```

**Hash Routing (AppContext.tsx, lines 216-232):**
- Listens for hashchange events
- Parses hash as `[stage]/[subView]`
- Validates stage with `isValidStage()`
- Falls back to "policies" for empty or unknown stage

**Stage Persistence (useScenarioPersistence.ts, lines 74-90):**
- `saveStage(stage)` saves to localStorage key "reformlab-active-stage"
- `loadStage()` reads from localStorage and validates with `isValidStage()`

**Main Content Routing (App.tsx, lines 201-211):**
```typescript
const mainPanelContent = (
  <>
    {activeStage === "policies" ? <PoliciesStageScreen /> : null}
    {activeStage === "population" ? <PopulationStageScreen /> : null}
    {activeStage === "engine" ? <EngineStageScreen /> : null}
    {activeStage === "results" ? resultsContent : null}
  </>
);
```

### File: `frontend/src/types/workspace.ts`

**Current StageKey type (line 16):**
```typescript
export type StageKey = "policies" | "population" | "engine" | "results";
```

**Target StageKey type:**
```typescript
export type StageKey = "policies" | "population" | "investment-decisions" | "scenario" | "results";
```

**Current VALID_STAGES Set (line 105):**
```typescript
const VALID_STAGES = new Set<string>(["policies", "population", "engine", "results"]);
```

**Target VALID_STAGES Set:**
```typescript
const VALID_STAGES = new Set<string>(["policies", "population", "investment-decisions", "scenario", "results"]);
```

**Current STAGES constant (lines 94-99):**
```typescript
export const STAGES: { key: StageKey; label: string; activeFor: (StageKey | SubView)[] }[] = [
  { key: "policies",   label: "Policy",    activeFor: ["policies"] },
  { key: "population", label: "Population", activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "engine",     label: "Scenario", activeFor: ["engine"] },
  { key: "results",    label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner"] },
];
```

**Target STAGES constant:**
```typescript
export const STAGES: { key: StageKey; label: string; activeFor: (StageKey | SubView)[] }[] = [
  { key: "policies",           label: "Policies",           activeFor: ["policies"] },
  { key: "population",         label: "Population",         activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "investment-decisions", label: "Investment Decisions", activeFor: ["investment-decisions"] },
  { key: "scenario",           label: "Scenario",           activeFor: ["scenario"] },
  { key: "results",            label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner"] },
];
```

**Label Updates:**
- "Policy" → "Policies" (plural to match multi-policy nature)
- "Scenario" kept same (was already correct label for engine stage)
- Added "Investment Decisions" label

### File: `frontend/src/components/layout/WorkflowNavRail.tsx`

**Current isComplete() function (lines 42-67):**
```typescript
function isComplete(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
): boolean {
  switch (key) {
    case "policies":
      return typeof activeScenario?.portfolioName === "string" && activeScenario.portfolioName.length > 0;
    case "population":
      return (
        (activeScenario?.populationIds?.length ?? 0) > 0 ||
        !!selectedPopulationId ||
        dataFusionResult !== null
      );
    case "engine":
      return activeScenario !== null;
    case "results":
      return results.length > 0;
  }
}
```

**Target isComplete() function:**
```typescript
function isComplete(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
): boolean {
  switch (key) {
    case "policies":
      return typeof activeScenario?.portfolioName === "string" && activeScenario.portfolioName.length > 0;
    case "population":
      return (
        (activeScenario?.populationIds?.length ?? 0) > 0 ||
        !!selectedPopulationId ||
        dataFusionResult !== null
      );
    case "investment-decisions":
      // Story 26.2 will implement proper completion logic
      // For now, stage is complete when decisions are disabled or configured
      return !activeScenario?.engineConfig.investmentDecisionsEnabled ||
             activeScenario?.engineConfig.logitModel !== null;
    case "scenario":
      return activeScenario !== null;
    case "results":
      return results.length > 0;
  }
}
```

**Current getSummary() function (lines 73-110):**
```typescript
function getSummary(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
  populations: PopulationItem[],
): string | null {
  switch (key) {
    case "policies":
      return activeScenario?.portfolioName ?? null;
    case "population": {
      const popId = activeScenario?.populationIds?.[0] ?? selectedPopulationId;
      if (popId) {
        return populations.find((p) => p.id === popId)?.name ?? popId;
      }
      if (dataFusionResult) {
        const count = dataFusionResult.summary.record_count.toLocaleString();
        return `${count} records`;
      }
      return null;
    }
    case "engine": {
      if (!activeScenario) return null;
      const { startYear, endYear } = activeScenario.engineConfig;
      return `${startYear}–${endYear}`;
    }
    case "results": {
      if (results.length === 0) return null;
      const n = results.length;
      return `${n} run${n !== 1 ? "s" : ""}`;
    }
  }
}
```

**Target getSummary() function:**
```typescript
function getSummary(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
  populations: PopulationItem[],
): string | null {
  switch (key) {
    case "policies":
      return activeScenario?.portfolioName ?? null;
    case "population": {
      const popId = activeScenario?.populationIds?.[0] ?? selectedPopulationId;
      if (popId) {
        return populations.find((p) => p.id === popId)?.name ?? popId;
      }
      if (dataFusionResult) {
        const count = dataFusionResult.summary.record_count.toLocaleString();
        return `${count} records`;
      }
      return null;
    }
    case "investment-decisions": {
      // Story 26.2 will implement proper summary
      if (!activeScenario?.engineConfig.investmentDecisionsEnabled) {
        return "Disabled";
      }
      return activeScenario.engineConfig.logitModel ?? null;
    }
    case "scenario": {
      if (!activeScenario) return null;
      const { startYear, endYear } = activeScenario.engineConfig;
      return `${startYear}–${endYear}`;
    }
    case "results": {
      if (results.length === 0) return null;
      const n = results.length;
      return `${n} run${n !== 1 ? "s" : ""}`;
    }
  }
}
```

**Component Test Updates Required:**
- Update stage count assertions from 4 to 5
- Add tests for investment-decisions stage
- Update "engine" references to "scenario"
- Add hash migration test

### File: `frontend/src/components/layout/MobileStageSwitcher.tsx`

**Current component:**
- Renders STAGES.map() for horizontal navigation
- Already uses workspace.ts STAGES constant
- No hardcoded stage count

**Changes Required:**
- Update docstring from "Shows all 4 canonical workflow stages" to "Shows all 5 canonical workflow stages"
- Tests will automatically pass due to STAGES import
- Verify all five stages are visible in horizontal scroll

### File: `frontend/src/contexts/AppContext.tsx`

**Hash Routing Migration (lines 216-232):**

Add migration logic in onHashChange():
```typescript
useEffect(() => {
  function onHashChange() {
    let hash = window.location.hash.slice(1); // remove leading #
    const [stage, sub] = hash.split("/");

    // Story 26.1: Migrate legacy #engine hash to #scenario
    const migratedStage = stage === "engine" ? "scenario" : stage;

    if (migratedStage && isValidStage(migratedStage)) {
      setActiveStage(migratedStage);
      setActiveSubView(sub && isValidSubView(sub) ? sub : null);
      // Update hash if migration occurred
      if (stage === "engine") {
        window.location.hash = sub ? `scenario/${sub}` : "scenario";
      }
    } else {
      // Empty hash or unknown stage → default to policies
      setActiveStage("policies");
      setActiveSubView(null);
    }
  }
  window.addEventListener("hashchange", onHashChange);
  onHashChange(); // read initial hash on mount
  return () => window.removeEventListener("hashchange", onHashChange);
}, []);
```

**Alternative approach (without immediate hash update):**
If immediate hash update causes issues, use a one-time migration flag:
```typescript
const engineMigratedRef = useRef(false);

useEffect(() => {
  function onHashChange() {
    const hash = window.location.hash.slice(1);
    const [stage, sub] = hash.split("/");

    // One-time migration for legacy #engine hash
    if (stage === "engine" && !engineMigratedRef.current) {
      engineMigratedRef.current = true;
      window.location.hash = sub ? `scenario/${sub}` : "scenario";
      return; // Wait for next hashchange event
    }

    if (stage && isValidStage(stage)) {
      setActiveStage(stage);
      setActiveSubView(sub && isValidSubView(sub) ? sub : null);
    } else {
      setActiveStage("policies");
      setActiveSubView(null);
    }
  }
  // ... rest of effect
}, []);
```

### File: `frontend/src/hooks/useScenarioPersistence.ts`

**Current loadStage() function (lines 82-90):**
```typescript
export function loadStage(): StageKey | null {
  try {
    const raw = localStorage.getItem(STAGE_STORAGE_KEY);
    if (!raw) return null;
    return isValidStage(raw) ? raw : null;
  } catch {
    return null;
  }
}
```

**Target loadStage() with migration:**
```typescript
export function loadStage(): StageKey | null {
  try {
    const raw = localStorage.getItem(STAGE_STORAGE_KEY);
    if (!raw) return null;
    // Story 26.1: Migrate legacy "engine" stage to "scenario"
    const migrated = raw === "engine" ? "scenario" : raw;
    return isValidStage(migrated) ? migrated : null;
  } catch {
    return null;
  }
}
```

**Note:** The migration happens at read-time. Subsequent saves will use "scenario". Over time, all localStorage entries will be updated organically.

### File: `frontend/src/App.tsx`

**Current mainPanelContent (lines 201-211):**
```typescript
const mainPanelContent = (
  <>
    {activeStage === "policies" ? <PoliciesStageScreen /> : null}
    {activeStage === "population" ? (
      <PopulationStageScreen
        onExplorerPopulationChange={setExplorerPopulationId}
      />
    ) : null}
    {activeStage === "engine" ? <EngineStageScreen /> : null}
    {activeStage === "results" ? resultsContent : null}
  </>
);
```

**Target mainPanelContent:**
```typescript
const mainPanelContent = (
  <>
    {activeStage === "policies" ? <PoliciesStageScreen /> : null}
    {activeStage === "population" ? (
      <PopulationStageScreen
        onExplorerPopulationChange={setExplorerPopulationId}
      />
    ) : null}
    {activeStage === "investment-decisions" ? (
      // Story 26.2 will create InvestmentDecisionsStageScreen
      // For now, show placeholder or skip to scenario
      <div className="flex items-center justify-center p-12 text-slate-500">
        <p>Investment Decisions stage — coming in Story 26.2</p>
      </div>
    ) : null}
    {activeStage === "scenario" ? <EngineStageScreen /> : null}
    {activeStage === "results" ? resultsContent : null}
  </>
);
```

**Note:** Story 26.3 will rename EngineStageScreen to ScenarioStageScreen. For this story, both `activeStage === "scenario"` and the old `activeStage === "engine"` (if any references remain) should render EngineStageScreen.

### File: `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx`

**Current test structure:**
- Line 47: `it("renders all four stage labels when expanded"`
- Line 64: `it("shows stage numbers for all incomplete stages"` asserts 1-4
- Line 178: `it("calls navigateTo with engine when Scenario stage is clicked"`
- Line 182: `expect(navigateTo).toHaveBeenCalledWith("engine")`

**Required test updates:**
1. Update "renders all four stage labels" to "renders all five stage labels"
2. Add assertion for "Investment Decisions" label
3. Add assertion for "Scenario" label (already tested as "Scenario")
4. Update stage numbers test to assert 1-5
5. Update "calls navigateTo with engine" to "calls navigateTo with scenario"
6. Update expectation from `"engine"` to `"scenario"`
7. Add test for investment-decisions stage navigation
8. Add test for hash migration: `#engine` → `#scenario`

**New hash migration test:**
```typescript
describe("Story 26.1: Hash migration", () => {
  it("migrates legacy #engine hash to #scenario on load", () => {
    // Set hash to #engine
    window.location.hash = "engine";
    // Re-initialize routing (simulate app load)
    // Assert hash was updated to #scenario
    expect(window.location.hash).toBe("#scenario");
  });

  it("navigates to scenario stage when #engine is in URL", () => {
    window.location.hash = "engine";
    // Trigger hashchange
    // Assert activeStage is "scenario"
  });
});
```

### File: `frontend/src/components/layout/__tests__/MobileStageSwitcher.test.tsx`

**Check if test file exists:** If not, create it following WorkflowNavRail.test.tsx pattern.

**Required test updates:**
- Update stage count from 4 to 5
- Add tests for investment-decisions button
- Verify all five stages are clickable

### File: `frontend/src/hooks/__tests__/useScenarioPersistence.test.tsx`

**New localStorage migration tests:**
```typescript
describe("Story 26.1: localStorage migration", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("migrates stored 'engine' stage to 'scenario' on load", () => {
    localStorage.setItem("reformlab-active-stage", "engine");
    const loaded = loadStage();
    expect(loaded).toBe("scenario");
  });

  it("returns 'scenario' for stored 'engine' even after migration", () => {
    localStorage.setItem("reformlab-active-stage", "engine");
    const firstLoad = loadStage();
    expect(firstLoad).toBe("scenario");
    // Simulate app re-load
    const secondLoad = loadStage();
    expect(secondLoad).toBe("scenario"); // Still reads as engine from storage, migrates to scenario
  });

  it("preserves other stored stages", () => {
    localStorage.setItem("reformlab-active-stage", "policies");
    expect(loadStage()).toBe("policies");
    localStorage.setItem("reformlab-active-stage", "population");
    expect(loadStage()).toBe("population");
  });
});
```

### Testing Standards

**Frontend Component Tests:** `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx`

Required test coverage for Story 26.1:
- Test five stage labels render correctly
- Test stage indicators show numbers 1-5 for incomplete stages
- Test investment-decisions stage renders with correct label
- Test scenario stage (formerly engine) renders with correct label
- Test completion states for all five stages
- Test summary lines for all five stages
- Test navigation calls for all five stages
- Test hash migration from #engine to #scenario
- Test localStorage migration from "engine" to "scenario"

**Frontend Integration Tests:** `frontend/src/hooks/__tests__/useScenarioPersistence.test.tsx`

Required test coverage:
- Test loadStage() migrates "engine" to "scenario"
- Test other stages are preserved correctly
- Test migration is idempotent (always returns "scenario" for stored "engine")

### Project Structure Notes

**Frontend Files to Modify:**
- `frontend/src/types/workspace.ts` — Update StageKey, STAGES, VALID_STAGES
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Update isComplete(), getSummary()
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — Update tests for 5 stages
- `frontend/src/components/layout/MobileStageSwitcher.tsx` — Update docstring
- `frontend/src/components/layout/__tests__/MobileStageSwitcher.test.tsx` — Update tests for 5 stages (or create file)
- `frontend/src/contexts/AppContext.tsx` — Add hash routing migration
- `frontend/src/hooks/useScenarioPersistence.ts` — Add localStorage migration
- `frontend/src/hooks/__tests__/useScenarioPersistence.test.tsx` — Add migration tests
- `frontend/src/App.tsx` — Update mainPanelContent routing

**Files to Verify (no changes expected, but verify compatibility):**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Verify no hardcoded "engine" references
- `frontend/src/components/screens/PopulationStageScreen.tsx` — Verify sub-step routing still works
- `frontend/src/components/screens/EngineStageScreen.tsx` — Will be renamed in Story 26.3
- `frontend/src/components/screens/ResultsOverviewScreen.tsx` — Verify stage navigation works

### Implementation Order Recommendation

1. **Phase 1: Type and Constant Updates** (Foundation)
   - Update StageKey type in workspace.ts
   - Update STAGES constant in workspace.ts
   - Update VALID_STAGES Set in workspace.ts
   - Verify TypeScript compilation passes

2. **Phase 2: Component Updates** (UI changes)
   - Update WorkflowNavRail isComplete() and getSummary()
   - Update WorkflowNavRail tests for 5 stages
   - Update MobileStageSwitcher docstring
   - Update or create MobileStageSwitcher tests

3. **Phase 3: Routing and Migration** (Navigation changes)
   - Add hash routing migration in AppContext
   - Add localStorage migration in useScenarioPersistence
   - Add migration tests
   - Update App.tsx mainPanelContent routing

4. **Phase 4: Integration and Regression** (Validation)
   - Test full navigation flow across all five stages
   - Test hash migration with #engine bookmarks
   - Test localStorage migration with returning user
   - Verify Population sub-steps still work
   - Non-regression testing for existing stages

### Key Implementation Decisions

**Hash Migration Strategy:**
- Immediate redirect: When #engine is detected, immediately update hash to #scenario
- Alternative: Use ref flag to prevent infinite loops if hashchange event fires recursively
- Recommendation: Use one-time migration flag to prevent edge cases

**localStorage Migration Strategy:**
- Read-time migration: loadStage() returns "scenario" when stored value is "engine"
- No immediate write: Don't update localStorage on read to avoid write amplification
- Organic migration: Subsequent saves will use "scenario", gradually updating all entries

**Stage Content Placeholder:**
- Story 26.1 adds routing structure only
- Story 26.2 creates InvestmentDecisionsStageScreen
- Story 26.3 renames EngineStageScreen to ScenarioStageScreen
- For this story, use simple placeholder div for investment-decisions stage

**Terminology Migration:**
- User-facing: "Engine" → "Scenario" (completed in UX spec updates)
- Internal: `engine` → `scenario` (this story)
- Labels: "Policy" → "Policies" (plural form)

**Why Not Combine Stories:**
- Story 26.1 is structural (types, routing, nav rail)
- Story 26.2 is content (InvestmentDecisionsStageScreen creation)
- Story 26.3 is rename (EngineStageScreen → ScenarioStageScreen)
- Separation allows independent completion and testing

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-26] - Epic 26 requirements
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] - UX design specification (Revision 4.1, UX-DR6)
- [Source: frontend/src/types/workspace.ts] - StageKey, STAGES, type guards
- [Source: frontend/src/components/layout/WorkflowNavRail.tsx] - Nav rail component (Story 20.1)
- [Source: frontend/src/components/layout/MobileStageSwitcher.tsx] - Mobile stage switcher (Story 22.7)
- [Source: frontend/src/contexts/AppContext.tsx] - Hash-based routing (Story 20.1)
- [Source: frontend/src/hooks/useScenarioPersistence.ts] - Stage persistence (Story 20.2)
- [Source: frontend/src/App.tsx] - Main content routing

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

Story created with comprehensive developer context:
- Five-stage structure: Policies, Population, Investment Decisions, Scenario, Run / Results / Compare
- Type updates: StageKey, STAGES constant, VALID_STAGES Set
- Component updates: WorkflowNavRail isComplete(), getSummary(), test updates
- Routing migration: Hash #engine → #scenario, localStorage "engine" → "scenario"
- Mobile switcher updates and test coverage
- Integration tests for migration paths
- Implementation order recommendations
- Non-regression checklist for existing functionality

Ultimate context engine analysis completed - comprehensive developer guide created.
Status set to: ready-for-dev
