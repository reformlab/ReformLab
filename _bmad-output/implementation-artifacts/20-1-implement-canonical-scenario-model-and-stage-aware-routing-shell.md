# Story 20.1: Implement canonical scenario model and stage-aware routing shell

Status: ready-for-dev

## Story

As a policy analyst,
I want the workspace organized as a four-stage shell (Policies & Portfolio, Population, Engine, Run / Results / Compare) with distinct scenario/portfolio/run objects,
so that I navigate a coherent, scenario-centered workspace instead of a flat list of disconnected screens.

## Acceptance Criteria

1. **AC-1: Four-stage navigation visible** — Given the application shell, when loaded, then a four-stage navigation is visible: Policies & Portfolio, Population, Engine, Run / Results / Compare.
2. **AC-2: Route-addressable stage views** — Given a stage, when its route is visited, then the corresponding stage view renders without full-page reload. Browser back/forward navigates between stages.
3. **AC-3: Canonical object model** — Given the frontend state model, when inspected, then portfolio, scenario, and run are represented as distinct TypeScript interfaces with clear ownership boundaries matching the canonical object model.

## Tasks / Subtasks

- [ ] Task 1: Define canonical workspace types (AC: #3)
  - [ ] 1.1: Create `frontend/src/types/workspace.ts` with `WorkspaceScenario`, `EngineConfig`, `StageKey`, `SubView`, and `ActiveView` types
  - [ ] 1.2: `WorkspaceScenario` must reference `portfolioName` (from existing `PortfolioListItem`), `populationIds: string[]`, and `engineConfig` — not flatten them
  - [ ] 1.3: Ensure `Run` remains the existing `ResultListItem` / `RunResponse` — no new run type needed
  - [ ] 1.4: Ensure `Portfolio` remains the existing `PortfolioListItem` / `PortfolioDetailResponse` — no new portfolio type needed
- [ ] Task 2: Implement hash-based stage routing (AC: #2)
  - [ ] 2.1: Add routing state to `AppContext.tsx`: `activeStage: StageKey`, `activeSubView: SubView | null`, `navigateTo(stage, subView?)` action
  - [ ] 2.2: Sync routing state with `window.location.hash` (e.g., `#policies`, `#population`, `#engine`, `#results`, `#results/comparison`). Listen for `hashchange` to enable browser back/forward
  - [ ] 2.3: Replace `ViewMode` union in `App.tsx` with stage-based view resolution. Map old `viewMode` consumers to the new `activeStage + activeSubView` model
  - [ ] 2.4: Update all `setViewMode(...)` call sites throughout the codebase to use `navigateTo(stage, subView?)`
- [ ] Task 3: Build TopBar component (AC: #1)
  - [ ] 3.1: Create `frontend/src/components/layout/TopBar.tsx` — 48px height, `bg-white border-b border-slate-200`
  - [ ] 3.2: Left: current stage label (`text-lg font-semibold text-slate-900`, Inter)
  - [ ] 3.3: Right: BookOpen (docs link), Github icon, API status dot (emerald connected / amber disconnected with tooltip), Settings icon — all Lucide line-style, `text-slate-500`
  - [ ] 3.4: API status dot: `w-2 h-2 rounded-full bg-emerald-500` or `bg-amber-500`, derive from existing API health check or a simple fetch to `/api/templates`
- [ ] Task 4: Update WorkflowNavRail to 4 new stages (AC: #1)
  - [ ] 4.1: Replace `STAGES` array in `WorkflowNavRail.tsx` with new definitions: `policies` ("Policies"), `population` ("Population"), `engine` ("Engine"), `results` ("Results")
  - [ ] 4.2: Update `activeFor` arrays: policies → `["policies"]`; population → `["population", "data-fusion", "population-explorer"]`; engine → `["engine"]`; results → `["results", "comparison", "decisions", "runner"]`
  - [ ] 4.3: Update stage completion logic: Policies = `portfolios.length > 0`; Population = `selectedPopulationId` exists; Engine = scenario has valid engine config; Results = `results.length > 0`
  - [ ] 4.4: Update summary lines: Policies → portfolio policy count; Population → record count; Engine → year range; Results → run count
  - [ ] 4.5: Remove ScenarioCard rendering from sidebar (ScenarioCards are retired in Revision 2.0)
  - [ ] 4.6: Wire click handlers to call `navigateTo(stage)` instead of `setViewMode(mode)`
- [ ] Task 5: Restructure App.tsx shell layout (AC: #1, #2)
  - [ ] 5.1: Remove the gradient header box (`bg-gradient-to-r from-white to-indigo-50`, `shadow-sm`, `rounded-lg`) and all content inside it (logo, subtitle, nav buttons)
  - [ ] 5.2: Add `<TopBar>` inside the main content column of `WorkspaceLayout`, above the stage content area
  - [ ] 5.3: Move logo mark to sidebar (in `WorkflowNavRail` or `LeftPanel`). Use existing brand mark SVG or simple text "ReformLab" in `text-slate-700 font-semibold`
  - [ ] 5.4: Replace the `viewMode`-based conditional rendering block with stage-based rendering: each `StageKey` maps to a screen component
  - [ ] 5.5: For stages without full content yet, create stub placeholder screens (see Task 6)
- [ ] Task 6: Create stub stage screens (AC: #2)
  - [ ] 6.1: Create `frontend/src/components/screens/PoliciesStageScreen.tsx` — stub with heading "Policies & Portfolio" and placeholder text; re-exports existing `PortfolioDesignerScreen` content or a simple placeholder
  - [ ] 6.2: Create `frontend/src/components/screens/PopulationStageScreen.tsx` — stub that wraps/re-routes to existing `DataFusionWorkbench` or placeholder
  - [ ] 6.3: Create `frontend/src/components/screens/EngineStageScreen.tsx` — stub with heading "Engine Configuration" and placeholder text
  - [ ] 6.4: Ensure Stage 4 renders existing screens (`SimulationRunnerScreen`, `ResultsOverviewScreen`, `ComparisonDashboardScreen`, `BehavioralDecisionViewerScreen`) based on `activeSubView`
- [ ] Task 7: Apply brand compliance fixes (AC: #1)
  - [ ] 7.1: Remove all `indigo-*` color classes from shell components (`App.tsx`, `WorkspaceLayout.tsx`, `WorkflowNavRail.tsx`, `LeftPanel.tsx`)
  - [ ] 7.2: Remove `shadow-sm` from static layout panels
  - [ ] 7.3: Change panel containers from `rounded-lg` to `rounded-none`
  - [ ] 7.4: Ensure sidebar is `bg-slate-50`, main content is `bg-white`
- [ ] Task 8: Update AppContext with canonical scenario state (AC: #3)
  - [ ] 8.1: Add `activeScenario: WorkspaceScenario | null` to `AppState`
  - [ ] 8.2: Add scenario operations: `setActiveScenario`, `updateScenarioField` (immutable updates via spread)
  - [ ] 8.3: Migrate existing `selectedTemplateId` / `selectedScenarioId` / `parameterValues` references to use `activeScenario` fields where possible — but keep backward-compatible getters for screens not yet refactored (20.3–20.6)
  - [ ] 8.4: Keep existing `portfolios`, `results`, `runResult` fields — they are already correct as separate objects
- [ ] Task 9: Update tests (AC: #1, #2, #3)
  - [ ] 9.1: Update `WorkflowNavRail.test.tsx` — new stage labels, new click handler targets, remove ScenarioCard references
  - [ ] 9.2: Update `App.test.tsx` — verify 4-stage shell renders, gradient header removed
  - [ ] 9.3: Update `analyst-journey.test.tsx` — replace old ViewMode references with stage-based navigation
  - [ ] 9.4: Add test for hash routing: changing `window.location.hash` triggers correct stage render
  - [ ] 9.5: Add test for `WorkspaceScenario` type: verify distinct portfolio/scenario/run in context
  - [ ] 9.6: Verify all existing screen tests still pass (no broken imports or missing props)
- [ ] Task 10: Run quality gates
  - [ ] 10.1: `npm run typecheck` — 0 errors
  - [ ] 10.2: `npm run lint` — 0 errors (fast-refresh warnings pre-existing, OK)
  - [ ] 10.3: `npm test` — all tests pass
  - [ ] 10.4: `uv run ruff check src/ tests/` — 0 errors (backend unchanged but verify)
  - [ ] 10.5: `uv run mypy src/` — passes (backend unchanged but verify)

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
  status: "draft" | "ready" | "running" | "completed" | "failed";
  isBaseline: boolean;
  baselineRef: string | null;
  portfolioName: string | null;      // references PortfolioListItem.name
  populationIds: string[];           // references PopulationItem.id
  engineConfig: EngineConfig;
  policyType: string | null;
  lastRunId: string | null;
}

export const STAGES: { key: StageKey; label: string; activeFor: string[] }[] = [
  { key: "policies",   label: "Policies & Portfolio", activeFor: ["policies"] },
  { key: "population", label: "Population",           activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "engine",     label: "Engine",               activeFor: ["engine"] },
  { key: "results",    label: "Run / Results",        activeFor: ["results", "comparison", "decisions", "runner"] },
];
```

### Hash Routing Implementation Sketch

```typescript
// In AppContext.tsx or a dedicated useHashRouter hook
function useHashRouter() {
  const [activeStage, setActiveStage] = useState<StageKey>("policies");
  const [activeSubView, setActiveSubView] = useState<SubView | null>(null);

  useEffect(() => {
    function onHashChange() {
      const hash = window.location.hash.slice(1); // remove #
      const [stage, sub] = hash.split("/");
      if (isValidStage(stage)) {
        setActiveStage(stage as StageKey);
        setActiveSubView((sub as SubView) ?? null);
      }
    }
    window.addEventListener("hashchange", onHashChange);
    onHashChange(); // read initial hash
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigateTo = useCallback((stage: StageKey, subView?: SubView) => {
    const hash = subView ? `${stage}/${subView}` : stage;
    window.location.hash = hash;
  }, []);

  return { activeStage, activeSubView, navigateTo };
}
```

### Files to Create

| File | Purpose |
|---|---|
| `frontend/src/types/workspace.ts` | Canonical workspace types: `StageKey`, `SubView`, `WorkspaceScenario`, `EngineConfig`, `STAGES` |
| `frontend/src/components/layout/TopBar.tsx` | 48px top bar with stage name + utility icons |
| `frontend/src/components/screens/PoliciesStageScreen.tsx` | Stage 1 stub (placeholder, wraps existing `PortfolioDesignerScreen` content) |
| `frontend/src/components/screens/PopulationStageScreen.tsx` | Stage 2 stub (placeholder, wraps existing `DataFusionWorkbench`) |
| `frontend/src/components/screens/EngineStageScreen.tsx` | Stage 3 stub (placeholder) |

### Files to Modify

| File | Changes |
|---|---|
| `frontend/src/App.tsx` | Remove gradient header, remove ViewMode type, add TopBar, wire stage-based rendering |
| `frontend/src/contexts/AppContext.tsx` | Add `activeStage`, `activeSubView`, `navigateTo`, `activeScenario: WorkspaceScenario`, hash sync |
| `frontend/src/components/layout/WorkflowNavRail.tsx` | New STAGES array, new click handlers, remove ScenarioCard, add logo mark |
| `frontend/src/components/layout/WorkspaceLayout.tsx` | Add TopBar slot, adjust layout if needed |
| `frontend/src/components/layout/LeftPanel.tsx` | Remove ScenarioCard imports, brand fixes |
| `frontend/src/api/types.ts` | No changes — existing types are correct |
| `frontend/src/data/mock-data.ts` | Deprecate/remove old `Scenario` interface (replaced by `WorkspaceScenario`) |

### Test Files to Update

| File | Changes |
|---|---|
| `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` | New stage labels, new navigation targets |
| `frontend/src/__tests__/App.test.tsx` | Verify 4-stage shell, no gradient header |
| `frontend/src/__tests__/workflows/analyst-journey.test.tsx` | Replace ViewMode references |

### EPIC-21 Extensibility Note

Story 20.1 does not implement EPIC-21 features, but the types must be extensible:
- `WorkspaceScenario` should not use a closed union for status — leave room for evidence-related states
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

- Ultimate context engine analysis completed — comprehensive developer guide created
- Analyzed architecture, UX spec (Revision 2.0), PRD, epics, and full frontend codebase
- No new dependencies required (hash-based routing, no react-router)
- This is a frontend-only structural story (0 backend changes)
- 5 new files, ~7 modified files, ~3 test files updated
- Downstream stories 20.2–20.7 all depend on the shell and types delivered here

### File List
