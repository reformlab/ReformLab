# Story 20.1: Implement canonical scenario model and stage-aware routing shell

Status: done

## Story

As a policy analyst,
I want the workspace organized as a four-stage shell (Policies & Portfolio, Population, Engine, Run / Results / Compare) with distinct scenario/portfolio/run objects,
so that I navigate a coherent, scenario-centered workspace instead of a flat list of disconnected screens.

## Acceptance Criteria

1. **AC-1: Four-stage navigation visible** — Given the application shell, when loaded, then a four-stage navigation is visible: Policies & Portfolio, Population, Engine, Run / Results / Compare.
2. **AC-2: Route-addressable stage views** — Given a stage, when its route is visited, then the corresponding stage view renders without full-page reload. Browser back/forward navigates between stages.
3. **AC-3: Canonical object model** — Given the frontend state model, when inspected, then `WorkspaceScenario`, `PortfolioListItem`, and `ResultListItem` are distinct TypeScript interfaces: `WorkspaceScenario` references portfolio by name and population by ID array, `PortfolioListItem` is unchanged, and `ResultListItem` is unchanged. No single interface owns fields from more than one object class.
4. **AC-4: Default and invalid hash handling** — Given the app loads with an empty hash (`#`) or an unrecognised stage, then the app defaults to the `policies` stage without throwing an error. Given a valid stage with an invalid subview, then the stage renders with `activeSubView = null`.
5. **AC-5: Existing stage-4 screens preserved** — Given the routing refactor is complete, when navigating to `#results`, `#results/runner`, `#results/comparison`, and `#results/decisions`, then `ResultsOverviewScreen`, `SimulationRunnerScreen`, `ComparisonDashboardScreen`, and `BehavioralDecisionViewerScreen` render correctly with all props satisfied and no TypeScript errors.

## Tasks / Subtasks

- [x] Task 1: Define canonical workspace types (AC: #3)
  - [x] 1.1: Create `frontend/src/types/workspace.ts` with `WorkspaceScenario`, `EngineConfig`, `StageKey`, `SubView`, and `ActiveView` types
  - [x] 1.2: `WorkspaceScenario` must reference `portfolioName` (from existing `PortfolioListItem`), `populationIds: string[]`, and `engineConfig` — not flatten them
  - [x] 1.3: Ensure `Run` remains the existing `ResultListItem` / `RunResponse` — no new run type needed
  - [x] 1.4: Ensure `Portfolio` remains the existing `PortfolioListItem` / `PortfolioDetailResponse` — no new portfolio type needed
- [x] Task 2: Implement hash-based stage routing (AC: #2)
  - [x] 2.1: Add routing state to `AppContext.tsx`: `activeStage: StageKey`, `activeSubView: SubView | null`, `navigateTo(stage, subView?)` action
  - [x] 2.2: Sync routing state with `window.location.hash` (e.g., `#policies`, `#population`, `#engine`, `#results`, `#results/comparison`). Listen for `hashchange` to enable browser back/forward. Empty hash or unrecognised stage defaults to `"policies"` with `activeSubView = null`. Invalid subview for a valid stage sets `activeSubView = null` (no error thrown).
  - [x] 2.3: Replace `ViewMode` union in `App.tsx` with stage-based view resolution. Map old `viewMode` consumers to the new `activeStage + activeSubView` model
  - [x] 2.4: Update all `setViewMode(...)` call sites in `App.tsx` to use `navigateTo(stage, subView?)`. Exhaustive list: `handleStartRun` (3 calls: `"progress"` → `navigateTo("results","runner")`, `"run"` → `navigateTo("results","runner")`, `"results"` → `navigateTo("results")`); header buttons `"configuration"` → `navigateTo("engine")`, `"Simulation"` → `navigateTo("results","runner")`, `"Configure Policy"` → `navigateTo("engine")`; `openComparison` → replace body with `navigateTo("results","comparison")` then delete the wrapper function; `backFromComparison` → delete (browser back handles this); `openDecisions` → replace body with `navigateTo("results","decisions")` then delete; `backFromDecisions` → delete. Also remove `previousViewMode` state and its setter — they are fully superseded by hash-based back/forward.
- [x] Task 3: Build TopBar component (AC: #1)
  - [x] 3.1: Create `frontend/src/components/layout/TopBar.tsx` — 48px height, `bg-white border-b border-slate-200`
  - [x] 3.2: Left: current stage label (`text-lg font-semibold text-slate-900`, Inter)
  - [x] 3.3: Right: BookOpen (docs link), Github icon, API status dot (emerald connected / amber disconnected with tooltip), Settings icon — all Lucide line-style, `text-slate-500`
  - [x] 3.4: API status dot: `w-2 h-2 rounded-full bg-emerald-500` or `bg-amber-500`. Use `apiConnected` from `useAppState()` — this boolean is already computed in `AppContext` from template/population mock-data flags. Do not add a new fetch or polling loop.
- [x] Task 4: Update WorkflowNavRail to 4 new stages (AC: #1)
  - [x] 4.1: Replace `STAGES` array in `WorkflowNavRail.tsx` with the canonical definitions from `workspace.ts` (import `STAGES` from `@/types/workspace`). Canonical labels: `policies` → "Policies & Portfolio", `population` → "Population", `engine` → "Engine", `results` → "Run / Results / Compare".
  - [x] 4.2: Update `activeFor` arrays: policies → `["policies"]`; population → `["population", "data-fusion", "population-explorer"]`; engine → `["engine"]`; results → `["results", "comparison", "decisions", "runner"]`
  - [x] 4.3: Update stage completion logic: Policies = `portfolios.length > 0`; Population = `selectedPopulationId` exists; Engine = scenario has valid engine config; Results = `results.length > 0`
  - [x] 4.4: Update summary lines: Policies → portfolio policy count; Population → record count; Engine → year range; Results → run count
  - [x] 4.5: Remove ScenarioCard rendering from sidebar (ScenarioCards are retired in Revision 2.0). Keep all AppContext scenario actions (`startRun`, `cloneScenario`, `deleteScenario`) in place — they will be consumed by stage screens in stories 20.3–20.4. Do not remove the `scenarios: Scenario[]` state or its setters from AppContext in this story.
  - [x] 4.6: Update `WorkflowNavRailProps` to replace `viewMode: WorkflowViewMode` + `setViewMode` with `activeStage: StageKey` + `navigateTo: (stage: StageKey) => void`. The component receives these via props (not via `useAppState()`) to preserve testability. Wire click handlers to call the injected `navigateTo(stage)` prop.
- [x] Task 5: Restructure App.tsx shell layout (AC: #1, #2)
  - [x] 5.1: Remove the gradient header box (`bg-gradient-to-r from-white to-indigo-50`, `shadow-sm`, `rounded-lg`) and all content inside it (logo, subtitle, nav buttons)
  - [x] 5.2: Add `<TopBar>` inside the main content column of `WorkspaceLayout`, above the stage content area
  - [x] 5.3: Move logo mark to sidebar (in `WorkflowNavRail` or `LeftPanel`). Use existing brand mark SVG or simple text "ReformLab" in `text-slate-700 font-semibold`
  - [x] 5.4: Replace the `viewMode`-based conditional rendering block with stage-based rendering: each `StageKey` maps to a screen component
  - [x] 5.5: For stages without full content yet, create stub placeholder screens (see Task 6)
- [x] Task 6: Create stub stage screens (AC: #2)
  - [x] 6.1: Create `frontend/src/components/screens/PoliciesStageScreen.tsx` — renders `PortfolioDesignerScreen` directly, passing existing props from `AppContext`. It is a thin wrapper, not a placeholder. Stage 1 is considered complete for this story's purposes.
  - [x] 6.2: Create `frontend/src/components/screens/PopulationStageScreen.tsx` — renders `DataFusionWorkbench` directly, passing existing props from `AppContext`. It is a thin wrapper, not a placeholder. Stage 2 is considered complete for this story's purposes.
  - [x] 6.3: Create `frontend/src/components/screens/EngineStageScreen.tsx` — stub with heading "Engine Configuration" and placeholder text
  - [x] 6.4: Ensure Stage 4 renders existing screens (`SimulationRunnerScreen`, `ResultsOverviewScreen`, `ComparisonDashboardScreen`, `BehavioralDecisionViewerScreen`) based on `activeSubView`
- [x] Task 7: Apply brand compliance fixes (AC: #1)
  - [x] 7.1: Remove all `indigo-*` color classes from shell components (`App.tsx`, `WorkspaceLayout.tsx`, `WorkflowNavRail.tsx`, `LeftPanel.tsx`)
  - [x] 7.2: Remove `shadow-sm` from static layout panels
  - [x] 7.3: Change panel containers from `rounded-lg` to `rounded-none`
  - [x] 7.4: Ensure sidebar is `bg-slate-50`, main content is `bg-white`
- [x] Task 8: Update AppContext with canonical scenario state (AC: #3)
  - [x] 8.1: Add `activeScenario: WorkspaceScenario | null` to `AppState`
  - [x] 8.2: Add scenario operations: `setActiveScenario`, `updateScenarioField` (immutable updates via spread)
  - [x] 8.3: Add `activeScenario: WorkspaceScenario | null` alongside (not replacing) existing fields. The existing `selectedTemplateId`, `selectedScenarioId`, `parameterValues`, and `scenarios: Scenario[]` state must remain in `AppContext` unchanged for stories 20.3–20.6 to consume. New code in this story reads/writes only `activeScenario`. No existing field reads may be replaced in this story — that migration is owned by 20.3–20.6.
  - [x] 8.4: Keep existing `portfolios`, `results`, `runResult` fields — they are already correct as separate objects
- [x] Task 9: Update tests (AC: #1, #2, #3)
  - [x] 9.1: Update `WorkflowNavRail.test.tsx` — new stage labels, new click handler targets, remove ScenarioCard references
  - [x] 9.2: Update `App.test.tsx` — verify 4-stage shell renders, gradient header removed
  - [x] 9.3: Update `analyst-journey.test.tsx` — replace all `setViewMode` / `viewMode` references with hash-based navigation assertions
    - [x] 9.3a: The "navigates to comparison and back" flow (which targets the gradient-header "Simulation" button) must be rewritten: navigate by setting `window.location.hash = "#results/comparison"` directly; verify `ComparisonDashboardScreen` renders; simulate a `hashchange` event back to `"#results"` and verify `ResultsOverviewScreen` renders. The old header button approach no longer exists after Task 5.1.
    - [x] 9.3b: Any assertion that calls `screen.getByRole("button", { name: /back to results/i })` targeting the old header buttons must be removed — back-navigation is now via browser hash history.
  - [x] 9.4: Add test for hash routing: changing `window.location.hash` triggers correct stage render
  - [x] 9.5: Add test for `WorkspaceScenario` type: verify distinct portfolio/scenario/run in context
  - [x] 9.6: Verify all existing screen tests still pass (no broken imports or missing props)
- [x] Task 10: Run quality gates
  - [x] 10.1: `npm run typecheck` — 0 errors
  - [x] 10.2: `npm run lint` — 0 errors (fast-refresh warnings pre-existing, OK)
  - [x] 10.3: `npm test` — all tests pass
  - [x] 10.4: `uv run ruff check src/ tests/` — 0 errors (backend unchanged but verify)
  - [x] 10.5: `uv run mypy src/` — passes (backend unchanged but verify)

## Dev Notes

### Architecture Constraints

- **No router library needed.** The project has no `react-router` or similar dependency. Use hash-based routing (`window.location.hash`) with a `hashchange` event listener. This is the simplest approach consistent with the existing SPA pattern and avoids adding a new dependency.
- **No backend changes in this story.** This is purely a frontend structural story. Backend routes (`/api/scenarios`, `/api/portfolios`, `/api/results`, etc.) already exist and are unchanged.
- **Existing screens must not break.** Stage 4 screens (`ResultsOverviewScreen`, `ComparisonDashboardScreen`, `BehavioralDecisionViewerScreen`, `SimulationRunnerScreen`) and `DataFusionWorkbench` must continue to render correctly — they are re-mounted under the new stage routing, not rewritten.
- **Frozen dataclass pattern applies to TS too.** `WorkspaceScenario` should be treated as immutable in practice — update via spread (`{ ...scenario, field: newValue }`), never mutate in place.

### Canonical Object Model (source of truth)

From UX spec Revision 2.0 (2026-03-24):

| Object | Definition | Owned by Stage |
|---|---|---|
| **Portfolio** | Reusable bundle of policy templates + parameter schedules | Stage 1 |
| **Population** | Reusable dataset (selected/generated/uploaded) | Stage 2 |
| **Scenario** | Versioned definition: portfolio ref + population selections + engine config + metadata | Stages 1–3 |
| **Run** | Immutable execution of one scenario version | Stage 4 |
| **Comparison** | Derived view over 2+ completed runs | Stage 4 |

Key relationships:
- Scenario references exactly one portfolio version (by name) and one or more population selections (by ID)
- Scenario owns engine settings (time horizon, seed, investment-decision toggle, calibration controls)
- Run is never edited — to change results, edit/clone the scenario
- Reform-as-delta: reform scenario stores sparse overrides vs. a baseline scenario version

### Current ViewMode → New Stage Mapping

| Old ViewMode | New StageKey | SubView |
|---|---|---|
| `"portfolio"` | `"policies"` | `null` |
| `"configuration"` | `"engine"` | `null` |
| `"data-fusion"` | `"population"` | `"data-fusion"` |
| `"runner"` | `"results"` | `"runner"` |
| `"run"` / `"progress"` | `"results"` | `"runner"` |
| `"results"` | `"results"` | `null` |
| `"comparison"` | `"results"` | `"comparison"` |
| `"decisions"` | `"results"` | `"decisions"` |

### Brand Compliance Fixes Required

Items to remove from current `App.tsx` and shell:
- `bg-gradient-to-r from-white to-indigo-50` — gradient header box
- `shadow-sm` on header/panel containers
- `rounded-lg` on panel containers → `rounded-none`
- All `indigo-*` color classes → use only slate/blue/emerald/amber/red/violet
- Logo/title in main content area → move logo to sidebar only
- Subtitle "Environmental policy analysis workspace" → remove entirely

### New Type Definitions

```typescript
// frontend/src/types/workspace.ts

export type StageKey = "policies" | "population" | "engine" | "results";

export type SubView =
  | "data-fusion"
  | "population-explorer"
  | "comparison"
  | "decisions"
  | "runner";

// String type (not closed union) to allow EPIC-21 evidence-related states.
// Known values at this revision: "draft" | "ready" | "running" | "completed" | "failed"
export type ScenarioStatus = string;

export interface EngineConfig {
  startYear: number;
  endYear: number;
  seed: number | null;
  investmentDecisionsEnabled: boolean;
}

export interface WorkspaceScenario {
  id: string;                        // matches ScenarioResponse.name
  name: string;
  version: string;
  status: ScenarioStatus;
  isBaseline: boolean;
  baselineRef: string | null;
  portfolioName: string | null;      // references PortfolioListItem.name
  populationIds: string[];           // references PopulationItem.id
  engineConfig: EngineConfig;
  policyType: string | null;
  lastRunId: string | null;
}

// Single source of truth for stage definitions — import this in WorkflowNavRail, TopBar, and tests
export const STAGES: { key: StageKey; label: string; activeFor: string[] }[] = [
  { key: "policies",   label: "Policies & Portfolio",   activeFor: ["policies"] },
  { key: "population", label: "Population",             activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "engine",     label: "Engine",                 activeFor: ["engine"] },
  { key: "results",    label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner"] },
];

const VALID_STAGES = new Set<string>(["policies", "population", "engine", "results"]);
export function isValidStage(s: string): s is StageKey {
  return VALID_STAGES.has(s);
}

const VALID_SUBVIEWS = new Set<string>(["data-fusion", "population-explorer", "comparison", "decisions", "runner"]);
export function isValidSubView(s: string): s is SubView {
  return VALID_SUBVIEWS.has(s);
}
```

### Hash Routing Implementation Sketch

```typescript
// In AppContext.tsx or a dedicated useHashRouter hook
// isValidStage and isValidSubView are exported from workspace.ts
function useHashRouter() {
  const [activeStage, setActiveStage] = useState<StageKey>("policies");
  const [activeSubView, setActiveSubView] = useState<SubView | null>(null);

  useEffect(() => {
    function onHashChange() {
      const hash = window.location.hash.slice(1); // remove leading #
      const [stage, sub] = hash.split("/");
      if (stage && isValidStage(stage)) {
        setActiveStage(stage);
        setActiveSubView(sub && isValidSubView(sub) ? sub : null);
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

  const navigateTo = useCallback((stage: StageKey, subView?: SubView) => {
    const hash = subView ? `${stage}/${subView}` : stage;
    window.location.hash = hash;
    // hashchange event fires automatically, updating state via the listener above
  }, []);

  return { activeStage, activeSubView, navigateTo };
}
```

### Files to Create

| File | Purpose |
|---|---|
| `frontend/src/types/workspace.ts` | Canonical workspace types: `StageKey`, `SubView`, `WorkspaceScenario`, `EngineConfig`, `STAGES` |
| `frontend/src/components/layout/TopBar.tsx` | 48px top bar with stage name + utility icons |
| `frontend/src/components/screens/PoliciesStageScreen.tsx` | Thin wrapper rendering `PortfolioDesignerScreen` with AppContext props — Stage 1 fully functional |
| `frontend/src/components/screens/PopulationStageScreen.tsx` | Thin wrapper rendering `DataFusionWorkbench` with AppContext props — Stage 2 fully functional |
| `frontend/src/components/screens/EngineStageScreen.tsx` | Stage 3 stub (placeholder) |

### Files to Modify

| File | Changes |
|---|---|
| `frontend/src/App.tsx` | Remove gradient header, remove ViewMode type, add TopBar, wire stage-based rendering |
| `frontend/src/contexts/AppContext.tsx` | Add `activeStage`, `activeSubView`, `navigateTo`, `activeScenario: WorkspaceScenario`, hash sync |
| `frontend/src/components/layout/WorkflowNavRail.tsx` | New STAGES array, new click handlers, remove ScenarioCard, add logo mark |
| `frontend/src/components/layout/WorkspaceLayout.tsx` | Add TopBar slot; update `h-[calc(100vh-Xrem)]` to account for the 48px (3rem) TopBar height |
| `frontend/src/components/layout/LeftPanel.tsx` | Remove ScenarioCard imports, brand fixes |
| `frontend/src/components/help/ContextualHelpPanel.tsx` | Update props from `viewMode: string` to `activeStage: StageKey, activeSubView: SubView \| null`; update the `getHelpEntry(...)` call accordingly |
| `frontend/src/components/help/help-content.ts` | Add help content keys for new stages: `"policies"`, `"population"`, `"engine"`, `"results"` (can map to existing entries or have simple default text) |
| `frontend/src/api/types.ts` | No changes — existing types are correct |
| `frontend/src/data/mock-data.ts` | **Keep** existing `Scenario` interface and `mockScenarios` unchanged. Add a `// @deprecated — use WorkspaceScenario (pending 20.3–20.6)` comment on the interface. Do not delete or modify the data — `AppContext` still initialises `scenarios` from `mockScenarios`. |

### Test Files to Update

| File | Changes |
|---|---|
| `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` | New stage labels, new navigation targets |
| `frontend/src/__tests__/App.test.tsx` | Verify 4-stage shell, no gradient header |
| `frontend/src/__tests__/workflows/analyst-journey.test.tsx` | Replace ViewMode references |

### EPIC-21 Extensibility Note

Story 20.1 does not implement EPIC-21 features, but the types must be extensible:
- `WorkspaceScenario.status` uses `ScenarioStatus = string` (not a closed union) — leave room for evidence-related states such as `"evidence-pending"` that EPIC-21 may introduce. Known values are documented as a comment in `workspace.ts`.
- Population references use `string[]` IDs — EPIC-21 Story 21.2 will attach evidence metadata to these IDs
- Engine validation (Story 20.5) will use a check registry — this story just establishes the routing shell

### Project Structure Notes

- New types go in `frontend/src/types/workspace.ts` — this creates a new `types/` directory, consistent with separating domain types from API DTOs in `api/types.ts`
- New layout components in `frontend/src/components/layout/` (existing convention)
- Stage screen stubs in `frontend/src/components/screens/` (existing convention)
- No backend files touched

### References

- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Revision 2.0 Workspace Model, lines ~1260-1360]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Stage Navigation Rail, lines ~1752-1777]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Brand Visual Identity, lines ~1350-1362]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 20.1, lines 2018-2032]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR32 stage-based GUI, FR28 run lineage, FR29 scenario versioning]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend component tree and state model]
- [Source: `frontend/src/App.tsx` — Current ViewMode type and gradient header]
- [Source: `frontend/src/contexts/AppContext.tsx` — Current state model]
- [Source: `frontend/src/components/layout/WorkflowNavRail.tsx` — Current STAGES array]
- [Source: `frontend/src/api/types.ts` — Existing PortfolioListItem, ScenarioResponse, RunResponse, ResultListItem]
- [Source: `frontend/src/data/mock-data.ts` — Current Scenario mock interface (to be replaced)]
- [Source: Story 18.1 implementation — Previous WorkflowNavRail story for pattern reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

- Implemented all 10 tasks; all quality gates pass (354/354 tests, 0 lint errors, 0 TS errors, 0 ruff errors, 0 mypy errors)
- No new dependencies added — hash-based routing implemented entirely in AppContext via `hashchange` event listener
- Frontend-only story — 0 backend changes
- Key pattern: stage labels appear in both TopBar and WorkflowNavRail simultaneously; tests use `getAllByText(...).length >= 1` to handle this
- WorkspaceLayout refactored from fixed `h-[calc(100vh-5.5rem)]` to flexbox model (`flex-1` inside `h-screen flex-col` App shell)
- All existing stage-4 screens (ResultsOverview, SimulationRunner, ComparisonDashboard, BehavioralDecisionViewer) preserved and wired via `activeSubView`
- `WorkspaceScenario` and `EngineConfig` added alongside (not replacing) legacy `Scenario` type — migration deferred to stories 20.3–20.6
- ContextualHelpPanel and help-content updated to use `StageKey`/`SubView` props instead of legacy `viewMode`/`activeStep`
- LeftPanel brand marks updated: collapsed "SCENARIOS" text → "RL"; expanded "Scenarios" → "ReformLab"
- [Code Review Synthesis] Fixed duplicate `refetchResults()` call in auth effect (AppContext.tsx)
- [Code Review Synthesis] Added empty-state for `#results/decisions` without prior run (App.tsx)
- [Code Review Synthesis] Tightened `STAGES.activeFor` type from `string[]` to `(StageKey | SubView)[]` (workspace.ts)
- [Code Review Synthesis] Removed no-op `navigateTo` in handleStartRun catch block (App.tsx)
- [Code Review Synthesis] Added AC-5 test for `#results/decisions` empty-state (analyst-journey.test.tsx)

### File List

#### New Files
- `frontend/src/types/workspace.ts`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/components/screens/PoliciesStageScreen.tsx`
- `frontend/src/components/screens/PopulationStageScreen.tsx`
- `frontend/src/components/screens/EngineStageScreen.tsx`

#### Modified Files
- `frontend/src/App.tsx`
- `frontend/src/contexts/AppContext.tsx`
- `frontend/src/components/layout/WorkflowNavRail.tsx`
- `frontend/src/components/layout/WorkspaceLayout.tsx`
- `frontend/src/components/layout/LeftPanel.tsx`
- `frontend/src/components/help/ContextualHelpPanel.tsx`
- `frontend/src/components/help/help-content.ts`
- `frontend/src/data/mock-data.ts`
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx`
- `frontend/src/__tests__/App.test.tsx`
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx`
- `frontend/src/components/help/__tests__/ContextualHelpPanel.test.tsx`
- `frontend/src/components/layout/__tests__/LeftPanel.test.tsx`

## Senior Developer Review (AI)

### Review: 2026-03-25
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 4.1 → Approved with Reservations
- **Issues Found:** 7
- **Issues Fixed:** 4
- **Action Items Created:** 3

#### Review Follow-ups (AI)
- [ ] [AI-Review] LOW: TopBar icons (BookOpen, Github, Settings) are non-interactive — wrap in `<button>` or `<a>` with `aria-label` for accessibility (`frontend/src/components/layout/TopBar.tsx`)
- [ ] [AI-Review] LOW: SubView validation is global, not stage-aware — `#engine/comparison` accepts `comparison` as subview; consider a stage→allowedSubViews map (`frontend/src/contexts/AppContext.tsx`)
- [ ] [AI-Review] LOW: Task 9.5 test is a tautology — does not verify AC-3 interface distinctness at runtime; consider testing context shape or `getHelpEntry` directly (`frontend/src/__tests__/workflows/analyst-journey.test.tsx`)
