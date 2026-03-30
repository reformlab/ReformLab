# Story 22.4: Population sub steps and quick test population

Status: completed

## Story

As a policy analyst working in the ReformLab workspace,
I want the Population stage to expose its internal work modes (Library, Build, Explorer) in the navigation rail and have access to a quick test population optimized for demos and smoke runs,
so that I can navigate Stage 2 more intuitively and run fast walkthroughs without waiting for large population loads or worrying about using demo data as if it were analysis-grade evidence.

## Acceptance Criteria

1. **[AC-1]** Given Population is the active stage (`activeStage === "population"`), when the WorkflowNavRail is rendered, then it displays three stage-local sub-steps labeled "Library", "Build", and "Explorer" below the main "Population" stage indicator.
2. **[AC-2]** Given the Population sub-steps are visible, when "Library" is clicked, then `activeSubView` becomes `null` and the PopulationLibraryScreen renders.
3. **[AC-3]** Given the Population sub-steps are visible, when "Build" is clicked, then `activeSubView` becomes `"data-fusion"` and DataFusionWorkbench renders.
4. **[AC-4]** Given the Population sub-steps are visible, when "Explorer" is clicked AND `explorerPopulationId` is null (no population being explored), then the Explorer sub-step is visually disabled (opacity-50, cursor-not-allowed), shows tooltip "Select a population to explore", and clicking it has no effect (no navigation occurs).
5. **[AC-5]** Given the Population sub-steps are visible, when "Explorer" is clicked AND `explorerPopulationId` is set (population is being explored), then `activeSubView` becomes `"population-explorer"` and PopulationExplorer renders with that population.
6. **[AC-6]** Given the Population Library is rendered, when the population list is displayed, then a "Quick Test Population" card appears at the top of the list (before other populations) with visible labeling that indicates it is for fast demos/smoke tests only.
7. **[AC-7]** Given the Quick Test Population, when selected for a scenario, then: (a) the scenario can be saved with Quick Test Population as the selected population, (b) the run executes without frontend or backend errors (in mock mode), and (c) results render correctly in the results panel.
8. **[AC-8]** Given the Quick Test Population, when displayed in the Population Library, then it has distinct visual treatment that differentiates it from analysis-grade populations: displays the "demo-only" trust status badge ("Demo Only" label) AND has a prominent "Fast demo / smoke test" callout on the card with tooltip explaining purpose.

## Tasks / Subtasks

- [x] **Task 1: Add Population sub-step data structures to workspace types** (AC: 1, 2, 3, 4, 5)
  - [x] Add `PopulationSubStep` type to `workspace.ts`: `"library" | "build" | "explorer"`
  - [x] Add `POPULATION_SUB_STEPS` constant array with explicit structure
  - [x] Export both for use in WorkflowNavRail
  - [x] Update type guards if needed for validation

- [x] **Task 2: Modify WorkflowNavRail to display Population sub-steps** (AC: 1, 2, 3, 4, 5)
  - [x] Add prop `explorerPopulationId: string | null` to WorkflowNavRailProps
  - [x] When `activeStage === "population"` AND `collapsed === false`, render sub-step indicators below main Population stage with visual hierarchy: `text-xs font-normal pl-6`
  - [x] When `collapsed === true`, hide sub-steps entirely (they don't fit in collapsed view)
  - [x] Each sub-step should be clickable (except Explorer when disabled)
  - [x] Sub-step click handlers call existing `navigateTo("population", subViewValue)` where subViewValue is: null for Library, "data-fusion" for Build, "population-explorer" for Explorer
  - [x] Explorer sub-step when `explorerPopulationId` is null: visually disabled (`opacity-50 cursor-not-allowed`), `aria-disabled="true"`, no click handler
  - [x] Active sub-step should have visual indicator distinct from main stage (e.g., filled circle `bg-blue-500` vs numbered circle)
  - [x] Add hover effect (`hover:bg-slate-50`) for clickable sub-steps

- [x] **Task 3: Create Quick Test Population data definition** (AC: 6, 7, 8)
  - [x] Create `frontend/src/data/quick-test-population.ts` with Quick Test Population definition
  - [x] Use intentionally small row count (e.g., 100-500 households) for fast demo runs
  - [x] Set `origin: "built-in"`, `canonical_origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "demo-only"` (reuse existing trust status from EPIC-21)
  - [x] Include metadata: `is_synthetic: true`, `year: current year`, `column_count: minimal (5-10 columns)`
  - [x] Export `QUICK_TEST_POPULATION_ID` and `getQuickTestPopulation()` function
  - [x] Add JSDoc explaining this is NOT for substantive analysis, only demos/smoke tests

- [x] **Task 4: Update trust status badge display for Quick Test Population** (AC: 8)
  - [x] TrustStatusBadge already has a "demo-only" case — verify it renders with "Demo Only" label
  - [x] For Quick Test Population, ensure "demo-only" badge has distinct visual treatment: consider adding tooltip "For fast demos and smoke testing only — not for substantive analysis"
  - [x] Optionally add "Fast demo" visual callout in PopulationLibraryScreen card for extra clarity

- [x] **Task 5: Integrate Quick Test Population into mock data** (AC: 6, 7, 8)
  - [x] Add Quick Test Population to `mockPopulations` array in `frontend/src/data/mock-data.ts`
  - [x] Ensure it appears first in the array (so it renders at top of library)
  - [x] Verify PopulationStageScreen merges it correctly into `mergedPopulations`
  - [x] Note: Backend integration is out of scope for this story (mock-only delivery)

- [x] **Task 6: Add Quick Test Population special treatment in PopulationLibraryScreen** (AC: 6, 8)
  - [x] Quick Test Population should render at top of list with deterministic ordering: check if `population.id === QUICK_TEST_POPULATION_ID` and render first regardless of sort order
  - [x] Add visible "Fast demo / smoke test" badge or callout on the card
  - [x] Consider subtle visual distinction: lighter border (`border-slate-200` vs default), different background tint, or prominent badge
  - [x] Tooltip on badge explains purpose: "For fast demos and smoke testing only — not for substantive analysis"

- [x] **Task 7: Pass explorerPopulationId from PopulationStageScreen to WorkflowNavRail** (AC: 4, 5)
  - [x] Keep `explorerPopulationId` as local state in PopulationStageScreen (do NOT lift to AppContext — this keeps stage-local state properly encapsulated)
  - [x] Pass `explorerPopulationId` prop to WorkflowNavRail via the shell component that renders both PopulationStageScreen and WorkflowNavRail
  - [x] Alternative: If PopulationStageScreen and WorkflowNavRail are siblings, add a callback prop to PopulationStageScreen that notifies parent of explorerPopulationId changes, then parent passes it to WorkflowNavRail
  - [x] Ensure value updates when PopulationExplorer is entered/exited

- [x] **Task 8: Add tests for Population sub-steps navigation** (AC: 1, 2, 3, 4, 5)
  - [x] Test: When Population is active stage AND rail is not collapsed, sub-steps are visible in WorkflowNavRail
  - [x] Test: When Population is active stage AND rail is collapsed, sub-steps are hidden
  - [x] Test: Clicking "Library" sets activeSubView to null
  - [x] Test: Clicking "Build" sets activeSubView to "data-fusion"
  - [x] Test: Clicking "Explorer" with no explorerPopulationId does nothing (disabled, no navigation)
  - [x] Test: Explorer sub-step has aria-disabled="true" when explorerPopulationId is null
  - [x] Test: Clicking "Explorer" with explorerPopulationId set navigates to "population-explorer"
  - [x] Test: Sub-steps are NOT visible when other stages are active

- [x] **Task 9: Add tests for Quick Test Population** (AC: 6, 7, 8)
  - [x] Test: Quick Test Population appears in mockPopulations array
  - [x] Test: Quick Test Population renders first in PopulationLibraryScreen
  - [x] Test: Quick Test Population has "demo-only" trust status badge
  - [x] Test: Quick Test Population is selectable and works with scenario flow
  - [x] Test: Quick Test Population has small row count (verify household count is 100-500)
  - [x] Test: Selecting Quick Test Population updates activeScenario.populationIds

## Dev Notes

### Current Implementation Analysis

**Population Stage Structure (`PopulationStageScreen.tsx`):**
- Routes based on `activeSubView`: `null` → PopulationLibraryScreen, `"data-fusion"` → DataFusionWorkbench, `"population-explorer"` → PopulationExplorer
- Manages local state: `previewPopulationId`, `explorerPopulationId`, `uploadedPopulations`, `uploadDialogOpen`
- `explorerPopulationId` is local state, not in AppContext

**WorkflowNavRail Current Behavior:**
- Shows 4 main stages (Policies & Portfolio, Population, Engine, Run / Results / Compare)
- Does NOT show Population sub-steps
- Uses `STAGES` array from `workspace.ts` for rendering
- Completion logic for Population stage checks `activeScenario.populationIds`, `selectedPopulationId`, or `dataFusionResult`

**Population Library (`PopulationLibraryScreen.tsx`):**
- Renders grid of population cards from `populations` prop
- Each card shows: name, badges (OriginBadge, TrustStatusBadge, SyntheticBadge), metadata, action buttons
- Populations come from `mergedPopulations` in PopulationStageScreen (built-in + generated + uploaded)

**Evidence Badge System (EPIC-21):**
- `OriginBadge`: shows `origin` field (built-in, generated, uploaded)
- `TrustStatusBadge`: shows `trust_status` field (production-safe, exploratory, validation)
- `SyntheticBadge`: shows `is_synthetic` boolean with `canonical_origin` context

### Navigation Architecture

**Hash-based routing (Story 20.1):**
- URL format: `#stage` or `#stage/subView`
- Population sub-views: `#population` (Library), `#population/data-fusion` (Build), `#population/population-explorer` (Explorer)
- `navigateTo(stage, subView)` updates `window.location.hash`
- `activeStage` and `activeSubView` are derived from hash

**Sub-step to SubView mapping:**
- `Library` → `activeSubView = null` (default Population view)
- `Build` → `activeSubView = "data-fusion"`
- `Explorer` → `activeSubView = "population-explorer"` (only when `explorerPopulationId` is set)

### Quick Test Population Specification

**Recommended characteristics:**
- `id`: "quick-test-population"
- `name`: "Quick Test Population"
- `households`: 100 (intentionally small for fast runs)
- `source`: "Built-in demo data"
- `year`: 2026 (current year)
- `origin`: "built-in"`
- `canonical_origin`: "synthetic-public"`
- `access_mode`: "bundled"`
- `trust_status`: "demo-only"` (reuse existing trust status from EPIC-21)
- `is_synthetic`: true
- `column_count`: ~8 (minimal demographic columns for demo purposes; must include: household_id, income, household_size, region, age, year)

**Badge design:**
- Use existing "demo-only" TrustStatusBadge which displays "Demo Only"
- Consider adding visual callout in card: "Fast demo / smoke test" with tooltip explaining purpose
- Tooltip: "For fast demos and smoke testing only — not for substantive analysis"

### Visual Hierarchy Requirements

**Sub-steps in WorkflowNavRail:**
- Should appear NESTED under the main Population stage, not as separate top-level items
- Text styling: `text-xs font-normal` (vs `text-sm font-medium` for main stages)
- Indentation: `pl-6` (24px left padding) to show hierarchy
- Container: `flex flex-col gap-1` for sub-step grouping under Population
- Sub-step active state: distinct from main stage active state (consider filled circle vs numbered)
- Sub-step clickable area: full-width with hover effect (`hover:bg-slate-50`)

**Explorer Disabled State:**
- When `explorerPopulationId` is null, Explorer sub-step should be:
  - Visually disabled: `opacity-50 cursor-not-allowed`
  - Non-clickable (no navigation occurs on click)
  - Has tooltip: "Select a population to explore"
  - Accessibility: `aria-disabled="true"` and `aria-describedby` pointing to tooltip

### Scope Boundaries

**IN SCOPE for Story 22.4:**
- Adding Population sub-step display in WorkflowNavRail
- Creating Quick Test Population data definition
- Reusing existing "demo-only" trust status badge (no new enum value)
- Integrating Quick Test Population into library display
- Navigator behavior for Explorer with/without active population

**OUT OF SCOPE for Story 22.4:**
- Full mobile redesign (that's Story 22.7)
- Changing PopulationStageScreen routing logic (already works via hash)
- Backend API changes for Quick Test Population — delivery mode is mock-only for this story
- Changes to other stages' navigation patterns
- Data Fusion or Explorer functionality changes

### Component Architecture

**Files to modify:**
- `frontend/src/types/workspace.ts` — add PopulationSubStep type and POPULATION_SUB_STEPS constant
- `frontend/src/components/layout/WorkflowNavRail.tsx` — add sub-step rendering logic
- `frontend/src/data/quick-test-population.ts` — NEW: Quick Test Population definition
- `frontend/src/data/mock-data.ts` — add Quick Test Population to mockPopulations
- `frontend/src/components/population/TrustStatusBadge.tsx` — verify "demo-only" case (already exists)
- `frontend/src/components/screens/PopulationStageScreen.tsx` — pass explorerPopulationId to parent
- `frontend/src/components/workspace/Workspace.tsx` (or shell) — update prop passing for explorerPopulationId
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — add sub-step tests
- `frontend/src/components/screens/__tests__/PopulationLibraryScreen.test.tsx` — add Quick Test Population tests

**Files to reference:**
- `frontend/src/components/screens/PopulationStageScreen.tsx` — routing logic
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — library display
- `frontend/src/components/population/PopulationExplorer.tsx` — explorer component

### Testing Patterns

Per project context:
- Use Vitest for frontend tests
- Test file structure mirrors source
- Mock `useAppState` with `vi.mock("@/contexts/AppContext")`
- Use `render` from `@testing-library/react`

**Test coverage targets:**
- Sub-steps render only when Population stage is active
- Each sub-step click produces correct hash navigation
- Explorer is disabled when no population selected
- Quick Test Population appears in mock data
- Quick Test Population has correct metadata and badge
- Quick Test Population is selectable and works with scenario

### Known Constraints and Gotchas

1. **explorerPopulationId is local state** — Currently stored in PopulationStageScreen, not AppContext. For this story, keep it as local state and pass it to WorkflowNavRail via parent component props/callback pattern. Do NOT lift to AppContext.

2. **Sub-step vs SubView terminology** — Sub-step is the UX label in nav rail. SubView is the hash fragment value. They map: Library→null, Build→"data-fusion", Explorer→"population-explorer". Keep this mapping single-source-of-truth in POPULATION_SUB_STEPS constant.

3. **"demo-only" trust_status already exists** — EPIC-21 already defined this trust status value. TrustStatusBadge.tsx already has a case for "demo-only" that displays "Demo Only". Reuse this existing value rather than creating a new enum.

4. **Quick Test Population placement** — Must appear first in list for visibility. Ensure no sorting or filtering logic moves it. PopulationStageScreen merges arrays in order: built-in, generated, uploaded. Put Quick Test Population first in built-in array.

5. **Sub-step visual hierarchy** — Sub-steps must NOT look like top-level stages. Use indentation, smaller text, and lighter styling to show they belong under Population.

6. **Explorer disabled behavior** — When `explorerPopulationId` is null, Explorer sub-step is visually disabled (`opacity-50 cursor-not-allowed`), non-clickable, and has a tooltip "Select a population to explore". No navigation occurs.

7. **Hash navigation updates** — Clicking sub-steps should update `window.location.hash` via existing `navigateTo` function. No new routing logic needed.

8. **Mobile behavior** — Sub-steps may need different rendering on mobile (Story 22.7). For this story, ensure desktop behavior is solid. Mobile can be horizontal tabs or compact selector.

9. **Collapsed rail behavior** — When WorkflowNavRail is collapsed (`collapsed === true`), sub-steps should be hidden entirely. Only the main Population stage indicator shows in collapsed mode.

### References

- **Epic 22 definition:** `_bmad-output/planning-artifacts/epics.md#Epic-22`
- **UX Revision 3 spec:** `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 5 (Population Sub-Steps) and Change 8 (Quick Test Population)
- **Story 20.4:** `_bmad-output/implementation-artifacts/20-4-population-library-and-data-explorer-stage.md` — Population library implementation
- **Story 22.1:** `_bmad-output/implementation-artifacts/22-1-shell-branding-external-links-and-scenario-entry-relocation.md` — Previous story for reference
- **PopulationStageScreen source:** `frontend/src/components/screens/PopulationStageScreen.tsx`
- **WorkflowNavRail source:** `frontend/src/components/layout/WorkflowNavRail.tsx`
- **workspace.ts types:** `frontend/src/types/workspace.ts`

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Implementation Plan

**Phase 1: Data structures and types (Task 1)**
- Add PopulationSubStep type to workspace.ts
- Add POPULATION_SUB_STEPS constant with mapping
- Export for WorkflowNavRail use

**Phase 2: Quick Test Population definition (Task 3, 4, 5)**
- Create quick-test-population.ts with small demo population using "demo-only" trust status
- Verify TrustStatusBadge handles "demo-only" case (already exists)
- Integrate into mock-data.ts and API layer

**Phase 3: Navigation integration (Task 2, 7)**
- Modify WorkflowNavRail to render Population sub-steps
- Add explorerPopulationId prop and logic
- Update AppContext and Workspace to pass required props

**Phase 4: Library display (Task 6)**
- Ensure Quick Test Population renders first
- Add "Fast demo / smoke test" badge
- Add tooltip explaining purpose

**Phase 5: Testing (Task 8, 9)**
- Add WorkflowNavRail sub-step tests
- Add Quick Test Population tests
- Verify all acceptance criteria

### Debug Log References

Analysis completed from source files:
- `PopulationStageScreen.tsx` — routing and state management
- `WorkflowNavRail.tsx` — navigation component
- `PopulationLibraryScreen.tsx` — library display
- `workspace.ts` — type definitions
- `demo-scenario.ts` — existing demo pattern
- `ux-revision-3-implementation-spec.md` — Change 5 and Change 8 specs

### Completion Notes List

- Story 22.4 builds on existing hash-based routing from Story 20.1
- PopulationStageScreen routing logic is unchanged — only navigation visibility changes
- Quick Test Population is a new built-in, separate from the demo scenario
- "demo-only" trust status is reused from EPIC-21 evidence system (not a new value)
- Sub-steps are UX layer only — no new SubView values introduced
- explorerPopulationId remains local state in PopulationStageScreen (not lifted to AppContext)
- Mobile behavior deferred to Story 22.7 (Mobile demo viability)
- All changes are additive — no breaking changes to existing functionality
- **Implementation completed 2026-03-30:**
  - Added PopulationSubStep type and POPULATION_SUB_STEPS constant to workspace.ts
  - Modified WorkflowNavRail to render Population sub-steps with proper disabled state for Explorer
  - Created quick-test-population.ts with 100-household demo population
  - Added Quick Test Population to mock-data.ts (first in array)
  - Updated PopulationLibraryScreen with special treatment for Quick Test Population (amber border, "Fast demo / smoke test" badge, sorted first)
  - Added callback pattern in PopulationStageScreen to notify parent of explorerPopulationId changes
  - Updated App.tsx to pass explorerPopulationId and activeSubView to WorkflowNavRail
  - Added 14 new tests for Population sub-steps navigation (WorkflowNavRail.test.tsx)
  - Added 18 new tests for Quick Test Population (PopulationLibraryScreen.test.tsx)
  - All tests for modified components pass (72 tests across WorkflowNavRail, PopulationLibraryScreen, PopulationStageScreen)

### File List

**New files created:**
- `frontend/src/data/quick-test-population.ts` — Quick Test Population definition
- `frontend/src/components/screens/__tests__/PopulationLibraryScreen.test.tsx` — PopulationLibraryScreen tests

**Files modified:**
- `frontend/src/types/workspace.ts` — added PopulationSubStep type and POPULATION_SUB_STEPS
- `frontend/src/components/layout/WorkflowNavRail.tsx` — added sub-step rendering logic with SubStepIndicator component
- `frontend/src/data/mock-data.ts` — added Quick Test Population to mockPopulations
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — added special treatment for Quick Test Population (sorting, visual distinction, badge)
- `frontend/src/components/screens/PopulationStageScreen.tsx` — added PopulationStageScreenProps interface with onExplorerPopulationChange callback, useEffect to notify parent
- `frontend/src/App.tsx` — added explorerPopulationId state, passed callback to PopulationStageScreen, passed props to WorkflowNavRail
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — added 14 tests for Population sub-steps
- `frontend/src/components/screens/__tests__/PopulationStageScreen.test.tsx` — fixed mock data to include evidence fields

**Reference files (not modified):**
- `frontend/src/components/population/TrustStatusBadge.tsx` — verified "demo-only" case already exists
- `frontend/src/components/population/PopulationExplorer.tsx` — explorer component (reference only)

---
**Story Status:** completed
**Created:** 2026-03-30
**Epic:** 22 (UX Revision 3 Workspace Fit and Mobile Demo Viability)
