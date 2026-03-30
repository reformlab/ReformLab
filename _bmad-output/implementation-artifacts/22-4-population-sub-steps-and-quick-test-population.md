# Story 22.4: Population sub steps and quick test population

Status: ready-for-dev

## Story

As a policy analyst working in the ReformLab workspace,
I want the Population stage to expose its internal work modes (Library, Build, Explorer) in the navigation rail and have access to a quick test population optimized for demos and smoke runs,
so that I can navigate Stage 2 more intuitively and run fast walkthroughs without waiting for large population loads or worrying about using demo data as if it were analysis-grade evidence.

## Acceptance Criteria

1. **[AC-1]** Given Population is the active stage (`activeStage === "population"`), when the WorkflowNavRail is rendered, then it displays three stage-local sub-steps labeled "Library", "Build", and "Explorer" below the main "Population" stage indicator.
2. **[AC-2]** Given the Population sub-steps are visible, when "Library" is clicked, then `activeSubView` becomes `null` and the PopulationLibraryScreen renders.
3. **[AC-3]** Given the Population sub-steps are visible, when "Build" is clicked, then `activeSubView` becomes `"data-fusion"` and DataFusionWorkbench renders.
4. **[AC-4]** Given the Population sub-steps are visible, when "Explorer" is clicked AND `explorerPopulationId` is null (no population being explored), then the user is routed to Library view with no confusing empty state (Explorer is disabled or redirects).
5. **[AC-5]** Given the Population sub-steps are visible, when "Explorer" is clicked AND `explorerPopulationId` is set (population is being explored), then `activeSubView` becomes `"population-explorer"` and PopulationExplorer renders with that population.
6. **[AC-6]** Given the Population Library is rendered, when the population list is displayed, then a "Quick Test Population" card appears at the top of the list (before other populations) with visible labeling that indicates it is for fast demos/smoke tests only.
7. **[AC-7]** Given the Quick Test Population, when selected for a scenario, then it works through the existing scenario and run flow (no backend errors, results render correctly).
8. **[AC-8]** Given the Quick Test Population, when displayed in the Population Library, then it has a distinct badge or visual treatment that differentiates it from analysis-grade populations (e.g., "Fast demo / smoke test" badge, smaller row count emphasized).

## Tasks / Subtasks

- [ ] **Task 1: Add Population sub-step data structures to workspace types** (AC: 1, 2, 3, 4, 5)
  - [ ] Add `PopulationSubStep` type to `workspace.ts`: `"library" | "build" | "explorer"`
  - [ ] Add `POPULATION_SUB_STEPS` constant array mapping sub-steps to labels and SubView values
  - [ ] Export both for use in WorkflowNavRail
  - [ ] Update type guards if needed for validation

- [ ] **Task 2: Modify WorkflowNavRail to display Population sub-steps** (AC: 1, 2, 3, 4, 5)
  - [ ] Add prop `explorerPopulationId: string | null` to WorkflowNavRailProps
  - [ ] When `activeStage === "population"`, render sub-step indicators below main Population stage
  - [ ] Each sub-step should be clickable (except Explorer when no population is being explored)
  - [ ] Sub-step click handlers call `navigateTo("population", subViewValue)` where subViewValue is: null for Library, "data-fusion" for Build, "population-explorer" for Explorer
  - [ ] Explorer sub-step should be visually disabled when `explorerPopulationId` is null
  - [ ] Active sub-step should have visual indicator (different from main stage indicator)
  - [ ] Maintain spacing and visual hierarchy — sub-steps should read as nested under Population, not as separate top-level stages

- [ ] **Task 3: Create Quick Test Population data definition** (AC: 6, 7, 8)
  - [ ] Create `frontend/src/data/quick-test-population.ts` with Quick Test Population definition
  - [ ] Use intentionally small row count (e.g., 100-500 households) for fast demo runs
  - [ ] Set `origin: "built-in"`, `canonical_origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "demo"` (new trust status value)
  - [ ] Include metadata: `is_synthetic: true`, `year: current year`, `column_count: minimal (5-10 columns)`
  - [ ] Export `QUICK_TEST_POPULATION_ID` and `getQuickTestPopulation()` function
  - [ ] Add JSDoc explaining this is NOT for substantive analysis, only demos/smoke tests

- [ ] **Task 4: Add "demo" trust status to badge system** (AC: 8)
  - [ ] Add "demo" case to TrustStatusBadge component
  - [ ] Use distinct visual treatment: yellow/amber badge with "Fast demo" or similar label
  - [ ] Ensure badge is clearly different from production-safe, exploratory, and validation statuses

- [ ] **Task 5: Integrate Quick Test Population into mock data and API layer** (AC: 6, 7, 8)
  - [ ] Add Quick Test Population to `mockPopulations` array in `frontend/src/data/mock-data.ts`
  - [ ] Ensure it appears first in the array (so it renders at top of library)
  - [ ] If using real API backend: add entry to backend population fixtures
  - [ ] Verify PopulationStageScreen merges it correctly into `mergedPopulations`

- [ ] **Task 6: Add Quick Test Population special treatment in PopulationLibraryScreen** (AC: 6, 8)
  - [ ] Quick Test Population should render at top of list (already first in array, verify no sorting disrupts this)
  - [ ] Add visible "Fast demo / smoke test" badge or callout
  - [ ] Consider subtle visual distinction: lighter border, different background tint, or prominent badge
  - [ ] Tooltip on badge explains purpose: "For fast demos and smoke testing only — not for substantive analysis"

- [ ] **Task 7: Update AppContext to pass explorerPopulationId to WorkflowNavRail** (AC: 4, 5)
  - [ ] Add `explorerPopulationId` to AppContext state (or derive from activeSubView + local state)
  - [ ] Pass `explorerPopulationId` prop to WorkflowNavRail in Workspace.tsx or shell component
  - [ ] Ensure value updates when PopulationExplorer is entered/exited

- [ ] **Task 8: Add tests for Population sub-steps navigation** (AC: 1, 2, 3, 4, 5)
  - [ ] Test: When Population is active stage, sub-steps are visible in WorkflowNavRail
  - [ ] Test: Clicking "Library" sets activeSubView to null
  - [ ] Test: Clicking "Build" sets activeSubView to "data-fusion"
  - [ ] Test: Clicking "Explorer" with no explorerPopulationId routes to Library (Explorer disabled)
  - [ ] Test: Clicking "Explorer" with explorerPopulationId set navigates to "population-explorer"
  - [ ] Test: Sub-steps are NOT visible when other stages are active

- [ ] **Task 9: Add tests for Quick Test Population** (AC: 6, 7, 8)
  - [ ] Test: Quick Test Population appears in mockPopulations array
  - [ ] Test: Quick Test Population renders first in PopulationLibraryScreen
  - [ ] Test: Quick Test Population has "demo" trust status badge
  - [ ] Test: Quick Test Population is selectable and works with scenario flow
  - [ ] Test: Quick Test Population has small row count (verify household count)
  - [ ] Test: Selecting Quick Test Population updates activeScenario.populationIds

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
- `origin`: "built-in"
- `canonical_origin`: "synthetic-public"
- `access_mode`: "bundled"
- `trust_status`: "demo" (NEW value for this story)
- `is_synthetic`: true
- `column_count`: ~8 (minimal demographic columns for demo purposes)

**Badge design:**
- Label: "Fast demo" or "Demo only"
- Color: Yellow/amber (`bg-yellow-100 text-yellow-700` or similar)
- Tooltip: "For fast demos and smoke testing only — not for substantive analysis"

### Visual Hierarchy Requirements

**Sub-steps in WorkflowNavRail:**
- Should appear NESTED under the main Population stage, not as separate top-level items
- Use smaller text size (e.g., `text-xs` vs `text-sm` for main stages)
- Use lighter font weight (e.g., `font-normal` vs `font-medium` for main stages)
- Add visual indentation (padding-left or margin-left) to show hierarchy
- Sub-step active state should be distinct from main stage active state

**Explorer Disabled State:**
- When `explorerPopulationId` is null, Explorer sub-step should be:
  - Visually disabled (opacity reduced, `cursor-not-allowed`)
  - Non-clickable OR click routes to Library (better UX)
  - Has tooltip explaining "Select a population to explore" or similar

### Scope Boundaries

**IN SCOPE for Story 22.4:**
- Adding Population sub-step display in WorkflowNavRail
- Creating Quick Test Population data definition
- Adding "demo" trust status badge
- Integrating Quick Test Population into library display
- Navigator behavior for Explorer with/without active population

**OUT OF SCOPE for Story 22.4:**
- Full mobile redesign (that's Story 22.7)
- Changing PopulationStageScreen routing logic (already works via hash)
- Backend API changes for Quick Test Population (can be mock-only initially)
- Changes to other stages' navigation patterns
- Data Fusion or Explorer functionality changes

### Component Architecture

**Files to modify:**
- `frontend/src/types/workspace.ts` — add PopulationSubStep type and POPULATION_SUB_STEPS constant
- `frontend/src/components/layout/WorkflowNavRail.tsx` — add sub-step rendering logic
- `frontend/src/data/quick-test-population.ts` — NEW: Quick Test Population definition
- `frontend/src/data/mock-data.ts` — add Quick Test Population to mockPopulations
- `frontend/src/components/population/TrustStatusBadge.tsx` — add "demo" case
- `frontend/src/contexts/AppContext.tsx` — pass explorerPopulationId to WorkflowNavRail
- `frontend/src/components/workspace/Workspace.tsx` (or shell) — update prop passing
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

1. **explorerPopulationId is local state** — Currently stored in PopulationStageScreen, not AppContext. Need to either lift it to AppContext OR derive it from activeSubView === "population-explorer". Lifting to AppContext is cleaner for WorkflowNavRail access.

2. **Sub-step vs SubView terminology** — Sub-step is the UX label in nav rail. SubView is the hash fragment value. They map: Library→null, Build→"data-fusion", Explorer→"population-explorer". Keep this mapping single-source-of-truth in POPULATION_SUB_STEPS constant.

3. **"demo" trust_status is a new value** — EPIC-21 defined trust_status values but "demo" may not have been specified. Add it to TrustStatusBadge without breaking existing values (production-safe, exploratory, validation).

4. **Quick Test Population placement** — Must appear first in list for visibility. Ensure no sorting or filtering logic moves it. PopulationStageScreen merges arrays in order: built-in, generated, uploaded. Put Quick Test Population first in built-in array.

5. **Sub-step visual hierarchy** — Sub-steps must NOT look like top-level stages. Use indentation, smaller text, and lighter styling to show they belong under Population.

6. **Explorer disabled behavior** — Worst UX is clickable Explorer that shows empty state. Better: disabled button with tooltip, OR click routes to Library. Choose routing approach for smoother UX.

7. **Hash navigation updates** — Clicking sub-steps should update `window.location.hash` via existing `navigateTo` function. No new routing logic needed.

8. **Mobile behavior** — Sub-steps may need different rendering on mobile (Story 22.7). For this story, ensure desktop behavior is solid. Mobile can be horizontal tabs or compact selector.

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
- Create quick-test-population.ts with small demo population
- Add "demo" case to TrustStatusBadge
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
- "demo" trust status is a new value added to EPIC-21 evidence system
- Sub-steps are UX layer only — no new SubView values introduced
- Mobile behavior deferred to Story 22.7 (Mobile demo viability)
- All changes are additive — no breaking changes to existing functionality

### File List

**New files to create:**
- `frontend/src/data/quick-test-population.ts` — Quick Test Population definition

**Files to modify:**
- `frontend/src/types/workspace.ts` — add PopulationSubStep type and POPULATION_SUB_STEPS
- `frontend/src/components/layout/WorkflowNavRail.tsx` — add sub-step rendering
- `frontend/src/components/population/TrustStatusBadge.tsx` — add "demo" case
- `frontend/src/data/mock-data.ts` — add Quick Test Population to mockPopulations
- `frontend/src/contexts/AppContext.tsx` — pass explorerPopulationId
- `frontend/src/components/workspace/Workspace.tsx` — update prop passing
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — add tests
- `frontend/src/components/screens/__tests__/PopulationLibraryScreen.test.tsx` — add tests

**Reference files (not modified):**
- `frontend/src/components/screens/PopulationStageScreen.tsx` — routing logic (reference)
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — library display (reference)
- `frontend/src/components/population/PopulationExplorer.tsx` — explorer (reference)

---
**Story Status:** ready-for-dev
**Created:** 2026-03-30
**Epic:** 22 (UX Revision 3 Workspace Fit and Mobile Demo Viability)
