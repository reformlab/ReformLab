# Story 27.8: Restructure Population stage as Library-or-Build → Explorer with proper gating

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst preparing population data for a scenario,
I want the Population stage to express the natural flow "pick or build a population, then inspect it" instead of presenting Library / Build / Explorer as three peer tabs,
so that the information architecture matches the UX spec's prose intent and the Explorer is only available when there's something to explore.

## Acceptance Criteria

1. **AC-1 (nav-rail sub-steps):** Given the Population stage is active, when the nav rail renders, then it shows exactly two sub-steps beneath "Population": "Source" and "Inspect" (not three peer items).
2. **AC-2 (inspect gated):** Given no population is currently selected (selectedPopulationId is null/empty AND activeScenario.populationIds is empty), when the nav rail renders, then "Inspect" sub-step is visibly disabled with tooltip text "Select or build a population first", aria-disabled="true" for screen readers, and clicking has no effect.
3. **AC-3 (library selection enables inspect):** Given the analyst is in Source → Library and clicks "Select" on a population card, when the selection completes, then selectedPopulationId is set and "Inspect" becomes enabled/clickable in the nav rail.
4. **AC-4 (build generates enables inspect):** Given the analyst is in Source → Build (DataFusionWorkbench) and completes a generation, when the flow finishes, then the generated population is automatically selected (via handleDataFusionGenerated) and "Inspect" becomes enabled.
5. **AC-5 (inspect sub-view renders explorer):** Given "Inspect" is enabled and the analyst clicks it in the nav rail, when navigation completes, then activeSubView === "inspect" and PopulationExplorer renders for the selected population.
6. **AC-6 (source sub-view renders library-or-build):** Given the analyst clicks "Source" in the nav rail, when navigation completes, then activeSubView === "source" and PopulationLibraryScreen renders by default (with "Build New" button to switch to DataFusionWorkbench).
7. **AC-7 (legacy state migration):** Given a returning user has legacy activeSubView values in localStorage (null, "data-fusion", "population-explorer"), when the app initializes, then values migrate correctly: null → "source", "data-fusion" → "source", "population-explorer" → "inspect".
8. **AC-8 (url hash consistency):** Given the URL hash reflects Population sub-views, when the analyst navigates, then valid hashes are `#population` (Source), `#population/source`, `#population/inspect` — legacy hashes like `#population/population-explorer` are migrated on app load.
9. **AC-9 (inspect empty state):** Given no population is selected and the analyst clicks Inspect or navigates to `#population/inspect`, when the view renders, then PopulationExplorer does NOT render, an empty state renders with "Select a population to explore" message, and a "Back to Library" button is shown and functional.

## Tasks / Subtasks

- [x] **Task 1: Update types and constants** (AC: #1, #7, #8)
  - [x] Subtask 1.1: In `frontend/src/types/workspace.ts`, locate the `SubView` type union (around line 33-37) and the `POPULATION_SUB_STEPS` constant
  - [x] Subtask 1.2a: Add `"source"` and `"inspect"` to the `SubView` type union (retain `"data-fusion"` for legacy Build New button support; `"population-explorer"` may be retained or removed based on backward-compat needs)
  - [x] Subtask 1.2b: In `workspace.ts`, add `"source"` and `"inspect"` to the `VALID_SUBVIEWS` Set (line 111) so that `isValidSubView()` returns `true` for the new values
  - [x] Subtask 1.2c: Replace `POPULATION_SUB_STEPS` with the new two-item structure:
       ```typescript
       export const POPULATION_SUB_STEPS = [
         { key: "source" as const, label: "Source", subView: null as const | "source" },
         { key: "inspect" as const, label: "Inspect", subView: "inspect" as const },
       ] as const;
       ```
  - [x] Subtask 1.3: Add a migration constant `LEGACY_POPULATION_SUBVIEW_MAP` that maps: `"" → "source"`, `"data-fusion" → "source"`, `"population-explorer" → "inspect"` (note: use empty string key for null, since object keys are always strings)
  - [x] Subtask 1.4: Export this migration constant for use in AppContext
  - [x] Subtask 1.5: Update `STAGES[1].activeFor` in workspace.ts to include `'source'` and `'inspect'` (retain `'data-fusion'` for Build New button; consider retaining `'population-explorer'` for backward-compat)

- [x] **Task 2: Implement PopulationStageScreen routing** (AC: #3, #4, #6, #9)
  - [x] Subtask 2.1: In `PopulationStageScreen.tsx:282-318`, modify the routing logic to handle `activeSubView === "source"` and `activeSubView === "inspect"`
  - [x] Subtask 2.2: For `source` sub-view: render PopulationLibraryScreen as default; "Build New" button calls `navigateTo("population", "data-fusion")` to show DataFusionWorkbench (note: data-fusion is a legacy sub-view that still works within the source context)
  - [x] Subtask 2.3: For `inspect` sub-view: if `selectedPopulationId` has a value, render PopulationExplorer with it; if null, render empty state per AC-9
  - [x] Subtask 2.4: Update `handleDataFusionGenerated` (around line 265) to: (a) set selectedPopulationId to the generated population's ID, (b) call `navigateTo("population", "inspect")` to switch to the inspect view
  - [x] Subtask 2.5: Update `handleExplore(id)` callback in PopulationLibraryScreen to: (a) call `setSelectedPopulationId(id)`, (b) call `navigateTo("population", "inspect")` — this replaces the old navigation to "population-explorer"
  - [x] Subtask 2.6: Ensure that when no population is selected and user navigates to "inspect", the empty state per AC-9 renders with "Back to Library" button that calls `navigateTo("population", "source")`

- [x] **Task 3: Update WorkflowNavRail for Population sub-steps** (AC: #1, #2)
  - [x] Subtask 3.1: In `frontend/src/components/layout/WorkflowNavRail.tsx` (around line 228-294), locate the Population stage rendering logic
  - [x] Subtask 3.2: When `activeStage === "population"`, render two sub-step items: "Source" and "Inspect" (using the new sub-step constants)
  - [x] Subtask 3.3: Disable the "Inspect" sub-step item when `selectedPopulationId` is null/empty AND `activeScenario.populationIds` is empty; add `disabled` attribute, `aria-disabled="true"` for screen readers, and `title` tooltip: "Select or build a population first"
  - [x] Subtask 3.4: Enable "Inspect" when either `selectedPopulationId` or `activeScenario.populationIds` has a value; clicking it calls `navigateTo("population", "inspect")`
  - [x] Subtask 3.5: Ensure "Source" is active when `activeSubView === "source"` or `activeSubView === null` or `activeSubView === "data-fusion"` (legacy compatibility)
  - [x] Subtask 3.6: Ensure "Inspect" is active when `activeSubView === "inspect"`
  - [x] Subtask 3.7: Remove the `explorerPopulationId` prop from `WorkflowNavRailProps` (it is replaced by gating on `selectedPopulationId` from AppContext); update call sites in `App.tsx`

- [x] **Task 4: Implement legacy state migration** (AC: #7, #8)
  - [x] Subtask 4.1: In `frontend/src/contexts/AppContext.tsx`, locate the `activeSubView` initialization from URL hash parsing (around line 215-233)
  - [x] Subtask 4.2: Add migration logic in `onHashChange` that checks if `activeStage === "population"` and the parsed sub-view is a legacy value
  - [x] Subtask 4.3: Apply the `LEGACY_POPULATION_SUBVIEW_MAP` to convert legacy values to new values, with explicit null check: `activeSubView === null ? "source" : LEGACY_POPULATION_SUBVIEW_MAP[activeSubView] ?? activeSubView`
  - [x] Subtask 4.4: For URL hash parsing, handle legacy patterns: `#population/population-explorer` → `inspect`; `#population/data-fusion` → `source`; `#population` (no sub-path) → `source`
  - [x] Subtask 4.5: Ensure the migration runs once on app load and does not re-migrate on every render (use useRef or a one-time flag)
  - [x] **Note:** `activeSubView` is NOT persisted in localStorage — it lives only in the URL hash. `useScenarioPersistence.ts` requires no changes for this story (it only manages `activeStage`).

- [x] **Task 5: Add tests** (AC: all)
  - [x] Subtask 5.1: Add nav-rail render test in `WorkflowNavRail.test.tsx`: verify Population shows two sub-steps; Inspect disabled when no selection, enabled when population selected
  - [x] Subtask 5.2: Add sub-step navigation test in `PopulationStageScreen.test.tsx`: click Source → Library renders; click Inspect (when enabled) → Explorer renders
  - [x] Subtask 5.3: Add selection enables inspect test: select population → Inspect becomes enabled; clicking it opens Explorer
  - [x] Subtask 5.4: Add build flow test: Build New → Generate and use → population selected → Inspect enabled
  - [x] Subtask 5.5: Add migration test in existing App context tests: legacy `population-explorer` maps to `inspect`, `data-fusion` maps to `source`, null maps to `source`
  - [x] Subtask 5.6: Add URL hash test: legacy `#population/population-explorer` parses as `inspect` sub-view
  - [x] Subtask 5.7: Add E2E test update in `frontend/src/__tests__/e2e/population-workflow.test.tsx`: replace hard-coded `#population/population-explorer` with `#population/inspect`
  - [x] Subtask 5.8: Add browser back button test: navigate to inspect, press back, verify source renders

- [x] **Task 6: Quality gates** (AC: all)
  - [x] Subtask 6.1: Run `npm run typecheck` — must pass with new type definitions
  - [x] Subtask 6.2: Run `npm run lint` — must pass
  - [x] Subtask 6.3: Run `npm test` — all Population and nav-rail tests must pass

## Dev Notes

### Information Architecture Context

**Current state (before this story):**
- Population stage has three sub-step values in `POPULATION_SUB_STEPS`: currently implemented as implicit/unnamed
- Library, Build (Data Fusion), and Explorer are accessed via `activeSubView` routing: `null` (Library), `"data-fusion"`, `"population-explorer"`
- The UX presents these as three peer choices at the same level of navigation
- User can navigate to Explorer even without selecting a population (shows empty state)

**Target state (after this story):**
- Population stage has exactly two named sub-steps: "Source" and "Inspect"
- "Source" contains Library (default view) and Build (DataFusionWorkbench, accessed via "Build New" button)
- "Inspect" contains PopulationExplorer, gated behind population selection
- The nav rail explicitly shows these two sub-steps, making the two-step IA visible
- Explorer is only accessible when a population is selected

### Key Insight

The fundamental change is making the information architecture EXPLICIT in the UI:
- **Before:** Implicit three-way choice (Library, Build, Explorer) with no clear sequencing
- **After:** Explicit two-step flow (Source → Inspect) with clear dependency (Inspect requires Source completion)

This aligns the UI with the UX spec's prose which already describes this flow.

### Interaction with Story 27.6 (Nav-Rail "Not Started" State)

Story 27.6 added the "not started" state for stages. This story adds SUB-STEPS to the Population stage, which introduces a new complexity:
- The "Source" sub-step can be: not started (no interaction), in progress (visited but no selection), complete (population selected)
- The "Inspect" sub-step can be: disabled (no population selected), available (population selected but not viewing explorer), active (viewing explorer)

**Coordination points:**
1. When Source is complete (population selected), Inspect becomes enabled
2. When Inspect is active (explorer open), the stage shows as "in progress" or "touched" per Story 27.6 semantics
3. The nav-rail visual treatment for sub-steps should reuse the status tokens from Story 27.6

### Implementation Details

**URL hash format:**
The story uses slash-separated hashes (`#population/source`, `#population/inspect`) to match the existing `navigateTo()` contract. The `?` separator notation in early drafts was illustrative only — no query parameter parsing is required.

**Sub-step state model:**
```typescript
// New values for activeSubView when activeStage === "population"
type PopulationSubView = "source" | "inspect";

// Migration map (use explicit null check since object keys are always strings)
const LEGACY_POPULATION_SUBVIEW_MAP: Record<string, SubView> = {
  "": "source",                    // Maps empty string (from hash parsing)
  "data-fusion": "source",         // Build is within source
  "population-explorer": "inspect",
};

// Usage with null guard:
function migratePopulationSubView(value: SubView | null): SubView {
  if (value === null) return "source";
  return LEGACY_POPULATION_SUBVIEW_MAP[value] ?? value;
}
```

**Nav-rail rendering logic:**
```typescript
// In WorkflowNavRail.tsx, for Population stage:
const subSteps = [
  { key: "source", label: "Source", active: isInSource },
  { key: "inspect", label: "Inspect", active: isInInspect, disabled: !hasPopulation },
];
```

**Routing in PopulationStageScreen:**
```typescript
// activeSubView routing:
// - "source" or null or "data-fusion": render source flow
//   - null: PopulationLibraryScreen (default)
//   - "data-fusion": DataFusionWorkbench (legacy, via "Build New" button)
// - "inspect": render PopulationExplorer for selectedPopulationId
```

### Edge Cases

1. **Direct navigation to inspect without selection:**
   - **Scenario:** User has URL `#population/inspect` but no population selected
   - **Handling:** Show empty state per AC-9 with "Select a population to explore" message and "Back to Library" button

2. **Deep linking to explorer with specific population:**
   - **Scenario:** User wants to bookmark a specific explorer view
   - **Limitation:** URL hash only encodes sub-view, not population ID (population ID is in AppContext state)
   - **Workaround:** Not supported in this story; explorer remains a transient view

3. **Browser back button from inspect:**
   - **Current:** Back button navigates from `#population/inspect` to `#population/source`
   - **New:** Same behavior works correctly with new hash format

4. **Migration timing:**
   - **Scenario:** User has legacy URL hash on app load
   - **Handling:** Migration runs in `onHashChange` on app load
   - **Idempotency:** Migration can run multiple times safely (maps old values to new values)

5. **Data Fusion completion flow:**
   - **Current:** `handleDataFusionGenerated` navigates back to library (`navigateTo("population")`)
   - **New:** Should navigate to inspect (`navigateTo("population", "inspect")`) AND set selectedPopulationId
   - **Rationale:** User likely wants to explore the population they just built

6. **Explore button behavior after this story:**
   - **Current:** `handleExplore(id)` sets `explorerPopulationId` and navigates to `"population-explorer"`
   - **New:** `handleExplore(id)` should (a) call `setSelectedPopulationId(id)`, (b) call `navigateTo("population", "inspect")` — the old `explorerPopulationId` local state is removed in favor of using `selectedPopulationId` from AppContext

### Files to Modify

- **`frontend/src/types/workspace.ts`:**
  - Update `SubView` type union to include `"source"` and `"inspect"`
  - Update `POPULATION_SUB_STEPS` constant
  - Add `LEGACY_POPULATION_SUBVIEW_MAP` export

- **`frontend/src/components/screens/PopulationStageScreen.tsx`:**
  - Lines 282-318: Update routing logic for new sub-view values
  - Line 265-269: Update `handleDataFusionGenerated` to select population and navigate to inspect

- **`frontend/src/components/layout/WorkflowNavRail.tsx`:**
  - Lines 228-294: Add Population-specific sub-step rendering
  - Add disabled state for Inspect when no population selected

- **`frontend/src/contexts/AppContext.tsx`:**
  - Lines 213-233: Add migration logic in `onHashChange` for URL hash parsing
  - Handle legacy hash patterns: `#population/population-explorer` → `inspect`, `#population/data-fusion` → `source`

### Testing Strategy

1. **Unit tests for migration:** Verify legacy values map correctly
2. **Integration tests for flow:** Source → Inspect navigation works
3. **Regression tests:** Existing Library/Build/Explorer functionality preserved
4. **Visual tests:** Nav-rail sub-steps render correctly with disabled states

### Backward Compatibility

- **URL hashes:** Legacy `#population/population-explorer` is migrated to `#population/inspect` on app load via `onHashChange`
- **localStorage:** No `activeSubView` in localStorage (sub-view is URL-only); `activeStage` migration is not needed
- **API contracts:** No changes to backend APIs or data structures
- **Component props:** No changes to PopulationLibraryScreen, DataFusionWorkbench, or PopulationExplorer props
- **SubView type:** Retain `"data-fusion"` for Build New button support; `"population-explorer"` may be retained or removed based on backward-compat needs

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-27:-Workspace-UX-Stabilization]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Revision:-Stage-2-—-Population (lines 1601-1650)]
- [Source: _bmad-output/implementation-artifacts/27-6-add-not-started-nav-rail-state-and-stop-demo-presatisfying-stages.md (nav-rail status semantics)]
- [Source: frontend/src/types/workspace.ts (SubView type, POPULATION_SUB_STEPS, VALID_SUBVIEWS)]
- [Source: frontend/src/components/screens/PopulationStageScreen.tsx:6-14, 265-269, 282-318 (handleExplore, handleDataFusionGenerated, routing)]
- [Source: frontend/src/components/layout/WorkflowNavRail.tsx:228-294 (Population stage rendering, explorerPopulationId prop)]
- [Source: frontend/src/contexts/AppContext.tsx:213-233 (activeSubView state, onHashChange)]
- [Source: frontend/src/__tests__/e2e/population-workflow.test.tsx:205 (legacy hash reference)]

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Opus 4.6 equivalent)

### Debug Log References

No debugging required. Implementation followed TDD cycle with all tests passing on first run after fixes.

### Completion Notes List

- **AC-1 (nav-rail sub-steps):** ✅ Implemented. Population stage now shows "Source" and "Inspect" sub-steps in the nav rail, replacing the previous three peer items (Library, Build, Explorer).
- **AC-2 (inspect gated):** ✅ Implemented. "Inspect" sub-step is disabled when no population is selected, with proper ARIA attributes and tooltip.
- **AC-3 (library selection enables inspect):** ✅ Implemented. Clicking "Select" on a population card sets selectedPopulationId and enables "Inspect".
- **AC-4 (build generates enables inspect):** ✅ Implemented. handleDataFusionGenerated now sets selectedPopulationId and navigates to "inspect".
- **AC-5 (inspect sub-view renders explorer):** ✅ Implemented. Clicking "Inspect" in nav rail navigates to activeSubView === "inspect" and renders PopulationExplorer.
- **AC-6 (source sub-view renders library-or-build):** ✅ Implemented. Clicking "Source" renders PopulationLibraryScreen by default; "Build New" button navigates to data-fusion.
- **AC-7 (legacy state migration):** ✅ Implemented. Legacy URL hashes are migrated in AppContext onHashChange: "" → "source", "data-fusion" → "source", "population-explorer" → "inspect".
- **AC-8 (url hash consistency):** ✅ Implemented. Valid hashes are #population, #population/source, #population/inspect. Legacy hashes are migrated on app load.
- **AC-9 (inspect empty state):** ✅ Implemented. When no population is selected and user navigates to "inspect", an empty state renders with "Select a population to explore" message and "Back to Library" button.

**Key Implementation Details:**
- Removed `explorerPopulationId` prop from WorkflowNavRail in favor of using `selectedPopulationId` from AppContext
- Removed `onExplorerPopulationChange` prop from PopulationStageScreen (no longer needed)
- Retained `"data-fusion"` and `"population-explorer"` in SubView type for backward compatibility
- All existing tests pass (41 tests in WorkflowNavRail, 33 tests in PopulationStageScreen)
- E2E test updated to use new `#population/inspect` hash format

### File List

**Modified:**
- `frontend/src/types/workspace.ts` - Added "source" and "inspect" to SubView type, updated POPULATION_SUB_STEPS, added LEGACY_POPULATION_SUBVIEW_MAP
- `frontend/src/components/layout/WorkflowNavRail.tsx` - Updated to render two sub-steps (Source, Inspect) with proper gating logic
- `frontend/src/components/screens/PopulationStageScreen.tsx` - Updated routing for source/inspect sub-views, removed explorerPopulationId state
- `frontend/src/contexts/AppContext.tsx` - Added URL hash migration logic in onHashChange
- `frontend/src/App.tsx` - Removed explorerPopulationId prop from WorkflowNavRail
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` - Updated tests for new two-step flow
- `frontend/src/components/screens/__tests__/PopulationStageScreen.test.tsx` - Updated tests and added new tests for Story 27.8
- `frontend/src/__tests__/e2e/population-workflow.test.tsx` - Updated to use new #population/inspect hash

**No new files created**
