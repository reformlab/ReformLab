# Story 27.8: Restructure Population stage as Library-or-Build → Explorer with proper gating

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst preparing population data for a scenario,
I want the Population stage to express the natural flow "pick or build a population, then inspect it" instead of presenting Library / Build / Explorer as three peer tabs,
so that the information architecture matches the UX spec's prose intent and the Explorer is only available when there's something to explore.

## Acceptance Criteria

1. **AC-1 (nav-rail sub-steps):** Given the Population stage is active, when the nav rail renders, then it shows exactly two sub-steps beneath "Population": "Source" and "Inspect" (not three peer items).
2. **AC-2 (inspect gated):** Given no population is currently selected (selectedPopulationId is null/empty), when the nav rail renders, then "Inspect" sub-step is visibly disabled with tooltip text "Select or build a population first" and clicking has no effect.
3. **AC-3 (library selection enables inspect):** Given the analyst is in Source → Library and clicks "Select" on a population card, when the selection completes, then selectedPopulationId is set and "Inspect" becomes enabled/clickable in the nav rail.
4. **AC-4 (build generates enables inspect):** Given the analyst is in Source → Build (DataFusionWorkbench) and completes a generation, when the flow finishes, then the generated population is automatically selected (via handleDataFusionGenerated) and "Inspect" becomes enabled.
5. **AC-5 (inspect sub-view renders explorer):** Given "Inspect" is enabled and the analyst clicks it in the nav rail, when navigation completes, then activeSubView === "inspect" and PopulationExplorer renders for the selected population.
6. **AC-6 (source sub-view renders library-or-build):** Given the analyst clicks "Source" in the nav rail, when navigation completes, then activeSubView === "source" and PopulationLibraryScreen renders by default (with "Build New" button to switch to DataFusionWorkbench).
7. **AC-7 (legacy state migration):** Given a returning user has legacy activeSubView values in localStorage (null, "data-fusion", "population-explorer"), when the app initializes, then values migrate correctly: null → "source", "data-fusion" → "source", "population-explorer" → "inspect".
8. **AC-8 (url hash consistency):** Given the URL hash reflects Population sub-views, when the analyst navigates, then valid hashes are #population (Source), #population?source, #population?inspect — legacy hashes like #population/population-explorer are migrated on app load.

## Tasks / Subtasks

- [ ] **Task 1: Update types and constants** (AC: #1, #7, #8)
  - [ ] Subtask 1.1: In `frontend/src/types/workspace.ts`, locate the `SubView` type union (around line 33-37) and the `POPULATION_SUB_STEPS` constant
  - [ ] Subtask 1.2: Replace the current three-item sub-step model with two items: `"source"` and `"inspect"`
  - [ ] Subtask 1.3: Add a migration constant `LEGACY_POPULATION_SUBVIEW_MAP` that maps: `null → "source"`, `"data-fusion" → "source"`, `"population-explorer" → "inspect"`
  - [ ] Subtask 1.4: Export this migration constant for use in AppContext and persistence hooks

- [ ] **Task 2: Implement PopulationStageScreen routing** (AC: #3, #4, #6)
  - [ ] Subtask 2.1: In `PopulationStageScreen.tsx:282-318`, modify the routing logic to handle `activeSubView === "source"` and `activeSubView === "inspect"`
  - [ ] Subtask 2.2: For `source` sub-view: render PopulationLibraryScreen as default; "Build New" button calls `navigateTo("population", "data-fusion")` to show DataFusionWorkbench (note: data-fusion is a legacy sub-view that still works within the source context)
  - [ ] Subtask 2.3: For `inspect` sub-view: render PopulationExplorer with `explorerPopulationId` set to `selectedPopulationId`
  - [ ] Subtask 2.4: Update `handleDataFusionGenerated` (around line 265) to: (a) set selectedPopulationId to the generated population's ID, (b) call `navigateTo("population", "inspect")` to switch to the inspect view
  - [ ] Subtask 2.5: Ensure that when no population is selected and user tries to navigate to "inspect", the screen shows an empty state with a "Back to Library" button

- [ ] **Task 3: Update WorkflowNavRail for Population sub-steps** (AC: #1, #2)
  - [ ] Subtask 3.1: In `frontend/src/components/layout/WorkflowNavRail.tsx` (around line 228-294), locate the Population stage rendering logic
  - [ ] Subtask 3.2: When `activeStage === "population"`, render two sub-step items: "Source" and "Inspect" (using the new sub-step constants)
  - [ ] Subtask 3.3: Disable the "Inspect" sub-step item when `selectedPopulationId` is null/empty; add `disabled` attribute and `title` tooltip: "Select or build a population first"
  - [ ] Subtask 3.4: Enable "Inspect" when `selectedPopulationId` has a value; clicking it calls `navigateTo("population", "inspect")`
  - [ ] Subtask 3.5: Ensure "Source" is active when `activeSubView === "source"` or `activeSubView === null` or `activeSubView === "data-fusion"` (legacy compatibility)
  - [ ] Subtask 3.6: Ensure "Inspect" is active when `activeSubView === "inspect"`

- [ ] **Task 4: Implement legacy state migration** (AC: #5, #7, #8)
  - [ ] Subtask 4.1: In `frontend/src/contexts/AppContext.tsx`, locate the `activeSubView` initialization from localStorage/hash (around line 215)
  - [ ] Subtask 4.2: Add migration logic that checks if `activeStage === "population"` and the loaded sub-view is a legacy value
  - [ ] Subtask 4.3: Apply the `LEGACY_POPULATION_SUBVIEW_MAP` to convert legacy values to new values
  - [ ] Subtask 4.4: For URL hash parsing, handle legacy patterns: `#population` → `#population?source`, `#population/population-explorer` → `#population?inspect`
  - [ ] Subtask 4.5: Ensure the migration runs once on app load and does not re-migrate on every render (use useRef or a one-time flag)

- [ ] **Task 5: Update useScenarioPersistence hook** (AC: #7)
  - [ ] Subtask 5.1: In `frontend/src/hooks/useScenarioPersistence.ts`, locate the `activeSubView` save/restore logic
  - [ ] Subtask 5.2: Apply migration when restoring: if restored value is legacy, map to new value before setting state
  - [ ] Subtask 5.3: Save new values directly (no reverse migration needed; forward compatibility only)

- [ ] **Task 6: Add tests** (AC: all)
  - [ ] Subtask 6.1: Add nav-rail render test in `WorkflowNavRail.test.tsx`: verify Population shows two sub-steps; Inspect disabled when no selection
  - [ ] Subtask 6.2: Add sub-step navigation test in `PopulationStageScreen.test.tsx`: click Source → Library renders; click Inspect (when enabled) → Explorer renders
  - [ ] Subtask 6.3: Add selection enables inspect test: select population → Inspect becomes enabled; clicking it opens Explorer
  - [ ] Subtask 6.4: Add build flow test: Build New → Generate and use → population selected → Inspect enabled
  - [ ] Subtask 6.5: Add migration test in `AppContext.test.tsx`: legacy `population-explorer` maps to `inspect`, `data-fusion` maps to `source`
  - [ ] Subtask 6.6: Add URL hash test: legacy `#population/population-explorer` parses as `inspect` sub-view

- [ ] **Task 7: Quality gates** (AC: all)
  - [ ] Subtask 7.1: Run `npm run typecheck` — must pass with new type definitions
  - [ ] Subtask 7.2: Run `npm run lint` — must pass
  - [ ] Subtask 7.3: Run `npm test` — all Population and nav-rail tests must pass

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

**Sub-step state model:**
```typescript
// New values for activeSubView when activeStage === "population"
type PopulationSubView = "source" | "inspect";

// Migration map
const LEGACY_POPULATION_SUBVIEW_MAP: Record<string, PopulationSubView | null> = {
  null: "source",           // Library default
  "data-fusion": "source",  // Build is within source
  "population-explorer": "inspect",
};
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
   - **Scenario:** User has URL `#population?inspect` but no population selected
   - **Handling:** Show empty state in PopulationExplorer with "Select a population first" message and "Back to Library" button

2. **Deep linking to explorer with specific population:**
   - **Scenario:** User wants to bookmark a specific explorer view
   - **Limitation:** URL hash only encodes sub-view, not population ID (population ID is in AppContext state)
   - **Workaround:** Not supported in this story; explorer remains a transient view

3. **Browser back button from inspect:**
   - **Current:** Back button navigates from `#population?inspect` to `#population?source`
   - **New:** Same behavior works correctly with new hash format

4. **Migration timing:**
   - **Scenario:** User has legacy state in localStorage on app upgrade
   - **Handling:** Migration runs once on app load in AppContext useEffect
   - **Idempotency:** Migration can run multiple times safely (maps old values to new values)

5. **Data Fusion completion flow:**
   - **Current:** `handleDataFusionGenerated` navigates back to library (`navigateTo("population")`)
   - **New:** Should navigate to inspect (`navigateTo("population", "inspect")`) AND set selectedPopulationId
   - **Rationale:** User likely wants to explore the population they just built

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
  - Lines 213-220: Add migration logic in activeSubView initialization
  - URL hash parsing: handle legacy patterns

- **`frontend/src/hooks/useScenarioPersistence.ts`:**
  - Apply migration when restoring activeSubView from localStorage

### Testing Strategy

1. **Unit tests for migration:** Verify legacy values map correctly
2. **Integration tests for flow:** Source → Inspect navigation works
3. **Regression tests:** Existing Library/Build/Explorer functionality preserved
4. **Visual tests:** Nav-rail sub-steps render correctly with disabled states

### Backward Compatibility

- **URL hashes:** Legacy `#population/population-explorer` is migrated on app load
- **localStorage:** Legacy sub-view values are migrated on app load
- **API contracts:** No changes to backend APIs or data structures
- **Component props:** No changes to PopulationLibraryScreen, DataFusionWorkbench, or PopulationExplorer props

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-27:-Workspace-UX-Stabilization]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Revision:-Stage-2-—-Population (lines 1601-1650)]
- [Source: _bmad-output/implementation-artifacts/27-6-add-not-started-nav-rail-state-and-stop-demo-presatisfying-stages.md (nav-rail status semantics)]
- [Source: frontend/src/types/workspace.ts (SubView type, POPULATION_SUB_STEPS)]
- [Source: frontend/src/components/screens/PopulationStageScreen.tsx:6-14, 265-269, 282-318]
- [Source: frontend/src/components/layout/WorkflowNavRail.tsx:228-294]
- [Source: frontend/src/contexts/AppContext.tsx:213-220 (activeSubView state)]

## Dev Agent Record

### Agent Model Used

<!-- Populated after implementation is complete -->

### Debug Log References

<!-- Populated after implementation is complete -->

### Completion Notes List

<!-- Populated after implementation is complete -->

### File List

<!-- Populated after implementation is complete -->
