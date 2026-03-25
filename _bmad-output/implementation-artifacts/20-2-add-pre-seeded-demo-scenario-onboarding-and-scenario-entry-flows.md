# Story 20.2: Add pre-seeded demo-scenario onboarding and scenario entry flows

Status: done

## Story

As a policy analyst,
I want the application to open a real pre-seeded demo scenario on first launch (with Run immediately enabled) and to resume my last scenario on subsequent visits, with clear entry flows for creating, cloning, or switching scenarios,
so that I can produce my first distributional chart in under a minute and easily manage multiple analysis scenarios.

## Acceptance Criteria

1. **AC-1: First-launch demo scenario** — Given a first-time user (no prior session in localStorage), when the application loads after authentication, then a pre-seeded demo scenario is set as `activeScenario` with population ID and engine config prefilled (the demo is template-based; `portfolioName` is intentionally `null` — no portfolio required for run), and the app navigates to `#results/runner` so the Run button is immediately clickable.
2. **AC-2: Returning-user scenario resume** — Given a returning user with a previously saved scenario in localStorage, when the application loads after authentication, then their most recent `activeScenario` is restored from localStorage and the app navigates to the last active stage (also persisted).
3. **AC-3: Scenario entry flows** — Given the scenario entry UI (triggered from TopBar), when accessed, then it supports four actions: (a) create new scenario from template, (b) open a previously saved scenario, (c) clone the current scenario, and (d) reset to the demo scenario.
4. **AC-4: Demo scenario validity** — Given the demo scenario is loaded, when the user clicks Run Simulation on Stage 4, then the simulation executes successfully via the existing `startRun()` flow, using legacy state seeded by demo initialization: `selectedTemplateId = "carbon-tax-dividend"`, default `parameterValues` (from mockParameters), and `selectedPopulationId = "fr-synthetic-2024"`. Note: `activeScenario.engineConfig` is NOT wired to `startRun()` in this story — that migration is deferred to stories 20.3–20.6.
5. **AC-5: Scenario persistence** — Given the user modifies `activeScenario` (via entry flows or in-app actions), when the change occurs, then `activeScenario` and `activeStage` are persisted to localStorage. On page reload (after re-auth), the persisted state is restored.

## Tasks / Subtasks

- [x] Task 1: Define demo scenario constant and factory (AC: #1, #4)
  - [x] 1.1: Create `frontend/src/data/demo-scenario.ts` exporting `DEMO_SCENARIO_ID = "demo-carbon-tax-dividend"` and `createDemoScenario(): WorkspaceScenario`
  - [x] 1.2: Demo scenario values: `id: DEMO_SCENARIO_ID`, `name: "Demo — Carbon Tax + Dividend"`, `version: "1.0"`, `status: "ready"`, `isBaseline: false`, `baselineRef: null`, `portfolioName: null` (no portfolio required for run — template-based), `populationIds: ["fr-synthetic-2024"]`, `engineConfig: { startYear: 2025, endYear: 2030, seed: 42, investmentDecisionsEnabled: false }`, `policyType: "carbon-tax"`, `lastRunId: null`
  - [x] 1.3: Export `DEMO_TEMPLATE_ID = "carbon-tax-dividend"` and `DEMO_POPULATION_ID = "fr-synthetic-2024"` — these are used by AppContext to also set the legacy `selectedTemplateId` and `selectedPopulationId` state alongside `activeScenario`
  - [x] 1.4: Add unit test `frontend/src/data/__tests__/demo-scenario.test.ts` verifying `createDemoScenario()` returns a valid `WorkspaceScenario` with all required fields non-undefined and `engineConfig.startYear < engineConfig.endYear`
- [x] Task 2: Implement scenario persistence hook (AC: #2, #5)
  - [x] 2.1: Create `frontend/src/hooks/useScenarioPersistence.ts` exporting `useScenarioPersistence()` hook
  - [x] 2.2: Define localStorage keys: `SCENARIO_STORAGE_KEY = "reformlab-active-scenario"`, `STAGE_STORAGE_KEY = "reformlab-active-stage"`, `SAVED_SCENARIOS_KEY = "reformlab-saved-scenarios"`, `HAS_LAUNCHED_KEY = "reformlab-has-launched"`
  - [x] 2.3: Implement `saveScenario(scenario: WorkspaceScenario | null): void` — JSON.stringify to localStorage under `SCENARIO_STORAGE_KEY`
  - [x] 2.4: Implement `loadScenario(): WorkspaceScenario | null` — JSON.parse from localStorage, return `null` on parse error or missing key (never throw)
  - [x] 2.5: Implement `saveStage(stage: StageKey): void` and `loadStage(): StageKey | null` — persist/restore last active stage
  - [x] 2.6: Implement `isFirstLaunch(): boolean` — returns `true` if `HAS_LAUNCHED_KEY` is not `"true"` in localStorage
  - [x] 2.7: Implement `markLaunched(): void` — sets `HAS_LAUNCHED_KEY = "true"` in localStorage
  - [x] 2.8: Implement `getSavedScenarios(): WorkspaceScenario[]` and `saveScenarioToList(scenario: WorkspaceScenario): void` — manages an array of saved scenarios in localStorage under `SAVED_SCENARIOS_KEY`. `saveScenarioToList` upserts by `id` (replaces if same id exists, appends otherwise). Max 20 entries (drop oldest on overflow).
  - [x] 2.9: Export all keys as named constants so tests can reference them directly
- [x] Task 3: Wire first-launch and returning-user logic into AppContext (AC: #1, #2, #4)
  - **Hook usage pattern (read before implementing):** Call `const { isFirstLaunch, markLaunched, saveScenario, loadScenario, saveStage, loadStage, getSavedScenarios, saveScenarioToList } = useScenarioPersistence()` once at the top of `AppProvider` alongside other hooks. Reference the returned functions inside `useCallback` and `useEffect` bodies — do NOT call `useScenarioPersistence()` inside a callback or effect (violates rules of hooks).
  - [x] 3.1: Import `useScenarioPersistence` hook and `createDemoScenario`, `DEMO_TEMPLATE_ID`, `DEMO_POPULATION_ID` into `AppContext.tsx`
  - [x] 3.2: Add a new `useEffect` that fires when `isAuthenticated` transitions to `true`. Guard at the top with `initializedRef` to ensure it runs exactly once per auth session (see Task 3.5).
  - [x] 3.3: Add a `useEffect` that persists `activeScenario` to localStorage whenever it changes. Guard: only persist when `isAuthenticated && initializedRef.current`.
  - [x] 3.4: Add a `useEffect` that persists `activeStage` to localStorage whenever it changes. Guard: only persist when `isAuthenticated && initializedRef.current`.
  - [x] 3.5: Add `useRef` to React imports; declare `const initializedRef = useRef(false)` at the top of `AppProvider`.
  - [x] 3.6: Add `savedScenarios: WorkspaceScenario[]` and `saveCurrentScenario: () => void` to `AppState` interface.
  - [x] 3.7: Add `loadSavedScenario: (id: string) => void` to `AppState`.
  - [x] 3.8: Add `resetToDemo: () => void` to `AppState`.
  - [x] 3.9: Add `createNewScenario: (templateId?: string) => void` to `AppState`.
  - [x] 3.10: Add `cloneCurrentScenario: () => void` to `AppState`.
  - [x] 3.11: Add all new state/actions to the `useMemo` value object and its dependency array.
  - [x] 3.12: All existing legacy state preserved (`scenarios`, `selectedScenarioId`, `selectedTemplateId`, `parameterValues`, `startRun`, `cloneScenario`, `deleteScenario`).
- [x] Task 4: Build ScenarioEntryDialog component (AC: #3)
  - [x] 4.1: Create `frontend/src/components/scenario/ScenarioEntryDialog.tsx`
  - [x] 4.2: Built using fixed overlay pattern (shadcn Dialog stubs lack DialogContent/Header/Title — used inline modal instead)
  - [x] 4.3: Props interface: `{ open: boolean; onOpenChange: (open: boolean) => void }`
  - [x] 4.4: Dialog content layout — four action cards in a 2×2 CSS grid
  - [x] 4.5: Each action card is a `<button>` element for keyboard accessibility
  - [x] 4.6: Saved scenario list with name, policy type badge, engine year range
  - [x] 4.7: Dialog header: "Switch Scenario" as title, current scenario name as subtitle
- [x] Task 5: Wire ScenarioEntryDialog to TopBar (AC: #3)
  - [x] 5.1: Added scenario name display with `<Separator orientation="vertical" />`
  - [x] 5.2: Scenario name clickable with `aria-label="Switch scenario"`
  - [x] 5.3: `scenarioDialogOpen` state + `<ScenarioEntryDialog>` rendered
  - [x] 5.4: Save button (Lucide `Save` icon) added next to scenario name
- [x] Task 6: Update help content for onboarding context (AC: #1)
  - [x] 6.1: Updated `"results/runner"` entry tips to include demo scenario onboarding tip
  - [x] 6.2: Added `"onboarding"` entry with scenario entry dialog tips
- [x] Task 7: Add tests (AC: #1, #2, #3, #4, #5)
  - [x] 7.1: Created `frontend/src/data/__tests__/demo-scenario.test.ts` (14 tests)
  - [x] 7.2: Created `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` (22 tests)
  - [x] 7.3: Updated `frontend/src/__tests__/App.test.tsx` — added first-launch test
  - [x] 7.4: Updated `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — added 4 new Story 20.2 tests; updated 2 existing tests to reflect new first-launch behavior
  - [x] 7.5: Created `frontend/src/components/scenario/__tests__/ScenarioEntryDialog.test.tsx` (11 tests)
  - [x] 7.6: All first-launch tests clear localStorage in `beforeEach`; returning-user tests use exported key constants
- [x] Task 8: Run quality gates (AC: all)
  - [x] 8.1: `npm run typecheck` — 0 errors
  - [x] 8.2: `npm run lint` — 0 errors (2 pre-existing fast-refresh warnings)
  - [x] 8.3: `npm test` — 407 tests pass across 48 test files (0 failures, 0 regressions)
  - [x] 8.4: `uv run ruff check src/ tests/` — 0 errors
  - [x] 8.5: `uv run mypy src/` — passes (149 source files)

## Dev Notes

### Architecture Constraints

- **No backend changes in this story.** This is purely a frontend story. The backend API endpoints (`/api/scenarios`, `/api/templates`, `/api/populations`, `/api/runs`) are unchanged. The demo scenario leverages existing mock data and existing API hooks.
- **No router library.** Continue using hash-based routing via `window.location.hash` established in Story 20.1.
- **Dual state model persists.** `activeScenario` (new canonical) coexists with legacy `scenarios[]`, `selectedTemplateId`, `parameterValues`. This story bridges them by setting legacy state from demo scenario values. Full migration to `activeScenario`-only is deferred to stories 20.3–20.6.
- **Immutable scenario updates.** `WorkspaceScenario` is treated as immutable — update via spread (`{ ...scenario, field: newValue }`), never mutate in place.
- **localStorage, not sessionStorage.** Scenario persistence uses `localStorage` (survives browser close) because the UX spec requires "returning users resume saved scenarios." Auth uses `sessionStorage` (session-scoped), so the user must re-authenticate but their scenario is restored.

### Demo Scenario Design Rationale

The demo scenario uses the "Carbon Tax — With Dividend" template because:
1. It is the flagship example referenced throughout the PRD (FR34 quickstart) and UX spec (Journey 2)
2. It ships with the most parameter variety (10 params across 3 groups: Tax Rates, Thresholds, Redistribution)
3. It produces a visually compelling distributional chart with clear progressive impact (D1 gains, D10 loses)
4. The template exists in `mockTemplates` as `id: "carbon-tax-dividend"`, so it works even without API

The demo scenario references `populationIds: ["fr-synthetic-2024"]` which always exists in `mockPopulations`. The `engineConfig` uses `seed: 42` for deterministic results matching existing test expectations.

### First-Launch vs Returning-User Decision Tree

```
App loads → Authenticate →
  ├── localStorage["reformlab-has-launched"] absent?
  │   └── YES (first launch):
  │       1. createDemoScenario() → setActiveScenario
  │       2. Set legacy: selectedTemplateId, selectedPopulationId
  │       3. markLaunched()
  │       4. navigateTo("results", "runner")
  │
  └── NO (returning user):
      1. loadScenario() from localStorage:
         - If present → setActiveScenario(saved)
         - If null (localStorage externally cleared) → fall back to demo:
           createDemoScenario() → setActiveScenario, set legacy IDs
           (do NOT call markLaunched() — has-launched flag stays true)
      2. loadStage() from localStorage → navigateTo(savedStage)
         - If stage missing → navigateTo("results", "runner")
```

### Scenario Entry Dialog Component Tree

```
TopBar
├── Logo + Stage Label
├── Scenario Name (clickable) + Save button
│   └── onClick → ScenarioEntryDialog opens
└── Utility icons (docs, github, API status, settings)

ScenarioEntryDialog (Shadcn Dialog)
├── DialogHeader: "Switch Scenario" + current name
├── 2×2 Grid of Action Cards:
│   ├── [FilePlus] New Scenario → createNewScenario()
│   ├── [FolderOpen] Open Saved → expand saved list
│   ├── [Copy] Clone Current → cloneCurrentScenario()
│   └── [Play] Demo Scenario → resetToDemo()
└── Saved Scenario List (conditional, below grid)
    └── Clickable rows: name + policyType badge + year range
```

### localStorage Key Schema

| Key | Type | Purpose |
|---|---|---|
| `reformlab-active-scenario` | `JSON<WorkspaceScenario \| null>` | Current workspace scenario |
| `reformlab-active-stage` | `StageKey` | Last active stage for resume |
| `reformlab-saved-scenarios` | `JSON<WorkspaceScenario[]>` | User's saved scenario library (max 20) |
| `reformlab-has-launched` | `"true" \| absent` | First-launch detection flag |
| `reformlab-left-panel-collapsed` | `"true" \| "false"` | (Existing) Left panel state |
| `reformlab-right-panel-collapsed` | `"true" \| "false"` | (Existing) Right panel state |

### Interaction with Legacy State

The demo scenario initialization sets both new and legacy state to keep the existing `startRun` flow working:

| New State (activeScenario) | Legacy State (set alongside) | Why |
|---|---|---|
| `activeScenario.policyType = "carbon-tax"` | `selectedTemplateId = "carbon-tax-dividend"` | `startRun()` uses `selectedTemplateId` to find template params. `policyType` uses hyphen format matching the template's `type` field in `mock-data.ts`. |
| `activeScenario.populationIds[0]` | `selectedPopulationId = "fr-synthetic-2024"` | `startRun()` passes `population_id` to API |
| `activeScenario.engineConfig` | ⚠️ **No legacy equivalent — do NOT wire `engineConfig` to `startRun()` in this story.** | `startRun()` still hardcodes `start_year: 2025, end_year: 2030`. Migration to scenario-driven execution is deferred to stories 20.3–20.6. |

The legacy `parameterValues` are NOT overridden by the demo scenario — they are already initialized from `mockParameters` (which match the carbon tax template defaults). This is correct behavior: the demo scenario uses default parameter values.

### Nav Rail Completion After Demo Load

After demo scenario loads:
- **Policies** (portfolios.length > 0): Depends on API/mock — may show incomplete. This is acceptable because the user lands on Stage 4, not Stage 1.
- **Population** (selectedPopulationId exists): **Complete** — set to "fr-synthetic-2024"
- **Engine** (activeScenario !== null): **Complete** — demo scenario is set
- **Results** (results.length > 0): Incomplete until first run. This is expected — the user needs to click Run.

### Files to Create

| File | Purpose |
|---|---|
| `frontend/src/data/demo-scenario.ts` | Demo scenario constant, factory, and template/population ID constants |
| `frontend/src/data/__tests__/demo-scenario.test.ts` | Unit tests for demo scenario factory |
| `frontend/src/hooks/useScenarioPersistence.ts` | localStorage read/write hook for scenario + stage persistence |
| `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` | Unit tests for persistence hook |
| `frontend/src/components/scenario/ScenarioEntryDialog.tsx` | Scenario entry flow dialog (4 actions + saved list) |
| `frontend/src/components/scenario/__tests__/ScenarioEntryDialog.test.tsx` | Unit tests for entry dialog |

### Files to Modify

| File | Changes |
|---|---|
| `frontend/src/contexts/AppContext.tsx` | Add initialization effect (first-launch / returning-user), add persistence effects for activeScenario and activeStage, add new actions to AppState (saveCurrentScenario, loadSavedScenario, resetToDemo, createNewScenario, cloneCurrentScenario, savedScenarios). Import persistence hook and demo scenario factory. |
| `frontend/src/components/layout/TopBar.tsx` | Add scenario name display (clickable), Save button, ScenarioEntryDialog rendering with open/close state. Import activeScenario and new actions from useAppState(). |
| `frontend/src/components/help/help-content.ts` | Update "results/runner" tips array to include demo scenario tip. |
| `frontend/src/__tests__/App.test.tsx` | Add first-launch → demo → runner test |
| `frontend/src/__tests__/workflows/analyst-journey.test.tsx` | Add first-launch, returning-user, and entry dialog navigation tests |

### Test Files to Create

| File | Tests |
|---|---|
| `frontend/src/data/__tests__/demo-scenario.test.ts` | Demo scenario validity (fields, types, ranges) |
| `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` | Persistence round-trips, error handling, first-launch detection, max-entries cap |
| `frontend/src/components/scenario/__tests__/ScenarioEntryDialog.test.tsx` | Dialog rendering, action card clicks, disabled states, saved scenario list |

### EPIC-21 Extensibility Note

Story 20.2 does not implement EPIC-21 features, but the demo scenario design accommodates future extensions:
- `WorkspaceScenario.status` uses `ScenarioStatus = string` (not closed union) — demo uses `"ready"` but EPIC-21 may add evidence-related states
- `populationIds` are string arrays — EPIC-21 Story 21.2 will attach evidence metadata to these IDs
- The saved scenarios list (`reformlab-saved-scenarios`) stores full `WorkspaceScenario` objects — when EPIC-21 adds new fields to `WorkspaceScenario`, `loadScenario()` must tolerate missing fields gracefully (use optional chaining / defaults in consuming code)

### Shadcn Components Used

From the available component library:
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle` — ScenarioEntryDialog
- `Badge` — Policy type badge in saved scenario list
- `Separator` — Visual separator in TopBar between scenario name and stage label
- `Button` — Save button (already available)

Lucide icons used: `FilePlus`, `FolderOpen`, `Copy`, `Play`, `Save`

### Project Structure Notes

- New `frontend/src/components/scenario/` directory — consistent with existing `frontend/src/components/screens/`, `frontend/src/components/layout/`, `frontend/src/components/help/` pattern
- New `frontend/src/data/__tests__/` directory — mirrors source structure per testing convention
- New `frontend/src/hooks/__tests__/` directory — mirrors source structure per testing convention
- Hook in `frontend/src/hooks/` — consistent with existing `useApi.ts` location

### References

- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Journey 2: First-Run Onboarding, lines ~514-550]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Journey 3: Scenario Workspace, lines ~552-600]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Updated User Journey (Revision 2.0), lines ~1786-1803]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Zero-Config Onboarding, line ~1277]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Scenario Summary Card, lines ~780-790]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Flow Optimization: 1 click to first chart, line ~717]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 20.2 BKL-2002, PRD refs FR32, FR34]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR7 (templates), FR8 (reforms), FR9 (versioned registry), FR32 (no-code GUI), FR34 (quickstart)]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend Scenario Entry Points, Section 5.10]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — ScenarioRegistry.clone, Section 5.2]
- [Source: `_bmad-output/implementation-artifacts/20-1-implement-canonical-scenario-model-and-stage-aware-routing-shell.md` — Story 20.1 complete implementation]
- [Source: `frontend/src/types/workspace.ts` — WorkspaceScenario, EngineConfig, StageKey, SubView]
- [Source: `frontend/src/contexts/AppContext.tsx` — Current state model, hash routing, activeScenario]
- [Source: `frontend/src/data/mock-data.ts` — mockTemplates (carbon-tax-dividend), mockPopulations (fr-synthetic-2024), mockParameters]
- [Source: `frontend/src/api/scenarios.ts` — createScenario, cloneScenario API functions]
- [Source: `frontend/src/App.tsx` — Current workspace rendering, stage-based content routing]
- [Source: `frontend/src/components/layout/TopBar.tsx` — Current TopBar layout]
- [Source: `frontend/src/__tests__/workflows/helpers.ts` — Test mock factories pattern]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — clean implementation, no blocking issues.

### Completion Notes List

- Task 4: shadcn `Dialog` component in this project is a stub (only exports `Dialog`, no `DialogContent`/`DialogHeader`/`DialogTitle`). Used inline fixed-overlay pattern consistent with `TemplateSelectionScreen.tsx` instead.
- Task 7.4: Updated two pre-existing Story 20.1 tests that became incorrect after Story 20.2 changed first-launch behavior:
  - "shows Policies & Portfolio as the default view on load" → updated to use returning-user localStorage pre-population
  - "activeScenario is null initially" → updated to reflect demo scenario set on first launch
- All 407 tests pass; 0 regressions.

### File List

**Created:**
- `frontend/src/data/demo-scenario.ts`
- `frontend/src/data/__tests__/demo-scenario.test.ts`
- `frontend/src/hooks/useScenarioPersistence.ts`
- `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts`
- `frontend/src/components/scenario/ScenarioEntryDialog.tsx`
- `frontend/src/components/scenario/__tests__/ScenarioEntryDialog.test.tsx`

**Modified:**
- `frontend/src/contexts/AppContext.tsx`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/components/help/help-content.ts`
- `frontend/src/__tests__/App.test.tsx`
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx`
