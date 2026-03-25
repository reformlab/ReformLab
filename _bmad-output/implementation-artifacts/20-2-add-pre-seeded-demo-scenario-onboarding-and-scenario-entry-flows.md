# Story 20.2: Add pre-seeded demo-scenario onboarding and scenario entry flows

Status: ready-for-dev

## Story

As a policy analyst,
I want the application to open a real pre-seeded demo scenario on first launch (with Run immediately enabled) and to resume my last scenario on subsequent visits, with clear entry flows for creating, cloning, or switching scenarios,
so that I can produce my first distributional chart in under a minute and easily manage multiple analysis scenarios.

## Acceptance Criteria

1. **AC-1: First-launch demo scenario** — Given a first-time user (no prior session in localStorage), when the application loads after authentication, then a pre-seeded demo scenario is set as `activeScenario` with Stages 1-3 prefilled (valid portfolio reference, population ID, engine config), and the app navigates to `#results/runner` so the Run button is immediately clickable.
2. **AC-2: Returning-user scenario resume** — Given a returning user with a previously saved scenario in localStorage, when the application loads after authentication, then their most recent `activeScenario` is restored from localStorage and the app navigates to the last active stage (also persisted).
3. **AC-3: Scenario entry flows** — Given the scenario entry UI (triggered from TopBar), when accessed, then it supports four actions: (a) create new scenario from template, (b) open a previously saved scenario, (c) clone the current scenario, and (d) reset to the demo scenario.
4. **AC-4: Demo scenario validity** — Given the demo scenario is loaded, when the user clicks Run Simulation on Stage 4, then the simulation executes successfully using the demo's `selectedTemplateId`, `parameterValues`, and `selectedPopulationId` — no additional configuration required.
5. **AC-5: Scenario persistence** — Given the user modifies `activeScenario` (via entry flows or in-app actions), when the change occurs, then `activeScenario` and `activeStage` are persisted to localStorage. On page reload (after re-auth), the persisted state is restored.

## Tasks / Subtasks

- [ ] Task 1: Define demo scenario constant and factory (AC: #1, #4)
  - [ ] 1.1: Create `frontend/src/data/demo-scenario.ts` exporting `DEMO_SCENARIO_ID = "demo-carbon-tax-dividend"` and `createDemoScenario(): WorkspaceScenario`
  - [ ] 1.2: Demo scenario values: `id: DEMO_SCENARIO_ID`, `name: "Demo — Carbon Tax + Dividend"`, `version: "1.0"`, `status: "ready"`, `isBaseline: false`, `baselineRef: null`, `portfolioName: null` (no portfolio required for run — template-based), `populationIds: ["fr-synthetic-2024"]`, `engineConfig: { startYear: 2025, endYear: 2030, seed: 42, investmentDecisionsEnabled: false }`, `policyType: "carbon_tax"`, `lastRunId: null`
  - [ ] 1.3: Export `DEMO_TEMPLATE_ID = "carbon-tax-dividend"` and `DEMO_POPULATION_ID = "fr-synthetic-2024"` — these are used by AppContext to also set the legacy `selectedTemplateId` and `selectedPopulationId` state alongside `activeScenario`
  - [ ] 1.4: Add unit test `frontend/src/data/__tests__/demo-scenario.test.ts` verifying `createDemoScenario()` returns a valid `WorkspaceScenario` with all required fields non-undefined and `engineConfig.startYear < engineConfig.endYear`
- [ ] Task 2: Implement scenario persistence hook (AC: #2, #5)
  - [ ] 2.1: Create `frontend/src/hooks/useScenarioPersistence.ts` exporting `useScenarioPersistence()` hook
  - [ ] 2.2: Define localStorage keys: `SCENARIO_STORAGE_KEY = "reformlab-active-scenario"`, `STAGE_STORAGE_KEY = "reformlab-active-stage"`, `SAVED_SCENARIOS_KEY = "reformlab-saved-scenarios"`, `HAS_LAUNCHED_KEY = "reformlab-has-launched"`
  - [ ] 2.3: Implement `saveScenario(scenario: WorkspaceScenario | null): void` — JSON.stringify to localStorage under `SCENARIO_STORAGE_KEY`
  - [ ] 2.4: Implement `loadScenario(): WorkspaceScenario | null` — JSON.parse from localStorage, return `null` on parse error or missing key (never throw)
  - [ ] 2.5: Implement `saveStage(stage: StageKey): void` and `loadStage(): StageKey | null` — persist/restore last active stage
  - [ ] 2.6: Implement `isFirstLaunch(): boolean` — returns `true` if `HAS_LAUNCHED_KEY` is not `"true"` in localStorage
  - [ ] 2.7: Implement `markLaunched(): void` — sets `HAS_LAUNCHED_KEY = "true"` in localStorage
  - [ ] 2.8: Implement `getSavedScenarios(): WorkspaceScenario[]` and `saveScenarioToList(scenario: WorkspaceScenario): void` — manages an array of saved scenarios in localStorage under `SAVED_SCENARIOS_KEY`. `saveScenarioToList` upserts by `id` (replaces if same id exists, appends otherwise). Max 20 entries (drop oldest on overflow).
  - [ ] 2.9: Export all keys as named constants so tests can reference them directly
- [ ] Task 3: Wire first-launch and returning-user logic into AppContext (AC: #1, #2, #4)
  - [ ] 3.1: Import `useScenarioPersistence` hook and `createDemoScenario`, `DEMO_TEMPLATE_ID`, `DEMO_POPULATION_ID` into `AppContext.tsx`
  - [ ] 3.2: Add a new `useEffect` that fires when `isAuthenticated` transitions to `true`. This effect implements the scenario initialization flow:
    ```
    if (isFirstLaunch()) {
      // First launch: load demo scenario
      const demo = createDemoScenario();
      setActiveScenario(demo);
      setSelectedTemplateId(DEMO_TEMPLATE_ID);
      setSelectedPopulationId(DEMO_POPULATION_ID);
      markLaunched();
      navigateTo("results", "runner");
    } else {
      // Returning user: restore saved scenario
      const saved = loadScenario();
      if (saved) setActiveScenario(saved);
      const savedStage = loadStage();
      if (savedStage) navigateTo(savedStage);
    }
    ```
  - [ ] 3.3: Add a `useEffect` that persists `activeScenario` to localStorage whenever it changes: `saveScenario(activeScenario)`. Only persist when `isAuthenticated` is true (avoid writing null during logout).
  - [ ] 3.4: Add a `useEffect` that persists `activeStage` to localStorage whenever it changes: `saveStage(activeStage)`. Only persist when `isAuthenticated` is true.
  - [ ] 3.5: **Critical ordering:** The initialization effect (3.2) must run *after* the hash-routing effect is set up but *before* the mock-data warning effect. Use a `useRef` flag (`initializedRef`) to ensure it runs exactly once per auth session. The initialization `navigateTo(...)` call will trigger hash updates which the existing hash listener will process.
  - [ ] 3.6: Add `savedScenarios: WorkspaceScenario[]` and `saveCurrentScenario: () => void` to `AppState` interface. `saveCurrentScenario` calls `saveScenarioToList(activeScenario!)` when activeScenario is non-null, then shows `toast.success("Scenario saved")`.
  - [ ] 3.7: Add `loadSavedScenario: (id: string) => void` to `AppState` — finds scenario in `getSavedScenarios()`, sets it as `activeScenario`, navigates to `"policies"`.
  - [ ] 3.8: Add `resetToDemo: () => void` to `AppState` — calls `setActiveScenario(createDemoScenario())`, sets `selectedTemplateId(DEMO_TEMPLATE_ID)`, `setSelectedPopulationId(DEMO_POPULATION_ID)`, navigates to `"results"`, shows `toast.info("Demo scenario loaded")`.
  - [ ] 3.9: Add `createNewScenario: (templateId?: string) => void` to `AppState` — creates a new `WorkspaceScenario` with a generated UUID (use `crypto.randomUUID()`), sets it as activeScenario, optionally sets `selectedTemplateId` if provided, navigates to `"policies"`.
  - [ ] 3.10: Add `cloneCurrentScenario: () => void` to `AppState` — deep-copies `activeScenario` with a new UUID and `name + " (copy)"`, sets as activeScenario, shows `toast.success("Scenario cloned")`.
  - [ ] 3.11: Add all new state/actions to the `useMemo` value object and its dependency array.
  - [ ] 3.12: **Do NOT remove or replace any existing legacy state** (`scenarios`, `selectedScenarioId`, `selectedTemplateId`, `parameterValues`, `startRun`, `cloneScenario`, `deleteScenario`). These remain for stories 20.3–20.6. The new scenario actions operate on `activeScenario` only. The legacy `startRun` still uses `selectedTemplateId` and `parameterValues` for actual execution.
- [ ] Task 4: Build ScenarioEntryDialog component (AC: #3)
  - [ ] 4.1: Create `frontend/src/components/scenario/ScenarioEntryDialog.tsx`
  - [ ] 4.2: Use Shadcn `Dialog` + `DialogContent` + `DialogHeader` + `DialogTitle`. Import from `@/components/ui/dialog`.
  - [ ] 4.3: Props interface:
    ```typescript
    interface ScenarioEntryDialogProps {
      open: boolean;
      onOpenChange: (open: boolean) => void;
    }
    ```
  - [ ] 4.4: Dialog content layout — four action cards in a 2×2 CSS grid (`grid grid-cols-2 gap-3 p-4`):
    - **"New Scenario"** — `FilePlus` icon (Lucide), subtitle "Start fresh from a template", click → `createNewScenario()` → close dialog
    - **"Open Saved"** — `FolderOpen` icon, subtitle "Resume a previous scenario", click → expand to show saved scenario list (inline, below the grid). If no saved scenarios, show "No saved scenarios yet" in `text-sm text-slate-400`.
    - **"Clone Current"** — `Copy` icon, subtitle "Duplicate the active scenario", click → `cloneCurrentScenario()` → close dialog. Disabled (opacity-50, pointer-events-none) when `activeScenario === null`.
    - **"Demo Scenario"** — `Play` icon, subtitle "Carbon Tax + Dividend example", click → `resetToDemo()` → close dialog
  - [ ] 4.5: Each action card: `border border-slate-200 rounded-md p-3 hover:bg-slate-50 cursor-pointer transition-colors`. Icon `h-5 w-5 text-slate-600 mb-1`. Title `text-sm font-medium text-slate-800`. Subtitle `text-xs text-slate-500`.
  - [ ] 4.6: Saved scenario list (shown when "Open Saved" is clicked): renders `savedScenarios` as a vertical list of clickable rows. Each row shows: scenario name (`text-sm font-medium`), policy type badge (`Badge` from Shadcn), engine year range (`text-xs text-slate-400`). Click → `loadSavedScenario(id)` → close dialog.
  - [ ] 4.7: Dialog header: "Switch Scenario" as title, scenario name below as subtitle in `text-sm text-slate-500` (e.g., "Current: Demo — Carbon Tax + Dividend").
- [ ] Task 5: Wire ScenarioEntryDialog to TopBar (AC: #3)
  - [ ] 5.1: In `TopBar.tsx`, add scenario name display between the logo and the stage label: `activeScenario?.name ?? "No scenario"` in `text-sm text-slate-500 truncate max-w-48`. Separate from stage label with a `Separator` (vertical, `h-5`).
  - [ ] 5.2: Make the scenario name clickable — wrap in a `<button>` with `hover:text-slate-700 transition-colors` and `aria-label="Switch scenario"`. On click, set `scenarioDialogOpen = true`.
  - [ ] 5.3: Add `const [scenarioDialogOpen, setScenarioDialogOpen] = useState(false)` state to `TopBar`. Render `<ScenarioEntryDialog open={scenarioDialogOpen} onOpenChange={setScenarioDialogOpen} />` at the bottom of the component.
  - [ ] 5.4: Add a "Save" button (Lucide `Save` icon, `h-4 w-4 text-slate-500`) next to the scenario name. On click → `saveCurrentScenario()`. Disabled when `activeScenario === null`. Wrap in `<button>` with `aria-label="Save scenario"`.
- [ ] Task 6: Update help content for onboarding context (AC: #1)
  - [ ] 6.1: In `help-content.ts`, update the `"results/runner"` entry to include a tip about the demo scenario: "First launch? The demo scenario is pre-configured — click Run Simulation to see your first distributional chart."
  - [ ] 6.2: Add a new entry `"onboarding"` (not routed, used as fallback content) with tips about the scenario entry dialog: "Click the scenario name in the top bar to switch scenarios, create new, or reset to the demo."
- [ ] Task 7: Add tests (AC: #1, #2, #3, #4, #5)
  - [ ] 7.1: Create `frontend/src/data/__tests__/demo-scenario.test.ts` — unit test for `createDemoScenario()`:
    - Returns WorkspaceScenario with `id === DEMO_SCENARIO_ID`
    - `engineConfig.startYear === 2025` and `endYear === 2030`
    - `populationIds` includes `DEMO_POPULATION_ID`
    - `policyType === "carbon_tax"`
    - `status === "ready"`
  - [ ] 7.2: Create `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` — unit tests for persistence functions:
    - `saveScenario` → `loadScenario` round-trip preserves all fields
    - `loadScenario` returns `null` on empty localStorage
    - `loadScenario` returns `null` on corrupted JSON (no throw)
    - `isFirstLaunch` returns `true` when key absent, `false` after `markLaunched()`
    - `saveScenarioToList` upserts by ID; `getSavedScenarios` returns the list
    - `saveScenarioToList` caps at 20 entries (oldest dropped)
  - [ ] 7.3: Update `frontend/src/__tests__/App.test.tsx` — add test:
    - "first launch navigates to results/runner with demo scenario (AC-1)": Clear all localStorage, authenticate, verify `window.location.hash` is `#results/runner` and SimulationRunnerScreen renders with "Run Simulation" button.
  - [ ] 7.4: Update `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — add tests:
    - "first-launch loads demo scenario and opens runner (AC-1)": Authenticate with empty localStorage → verify `#results/runner` hash → verify "Run Simulation" button visible
    - "returning user restores saved scenario and stage (AC-2)": Pre-set localStorage with a saved scenario and `activeStage = "engine"` → authenticate → verify EngineStageScreen renders (hash is `#engine`)
    - "scenario entry dialog opens from TopBar and shows 4 options (AC-3)": Authenticate → click scenario name in TopBar → verify Dialog opens with "New Scenario", "Open Saved", "Clone Current", "Demo Scenario" labels
    - "reset to demo from entry dialog (AC-3)": Open dialog → click "Demo Scenario" → verify `activeScenario` name is demo name, verify navigation
  - [ ] 7.5: Create `frontend/src/components/scenario/__tests__/ScenarioEntryDialog.test.tsx`:
    - Renders 4 action cards when open
    - "Clone Current" is disabled when activeScenario is null
    - Clicking "New Scenario" calls createNewScenario and closes dialog
    - Clicking "Demo Scenario" calls resetToDemo and closes dialog
    - "Open Saved" expands saved list; clicking a saved scenario calls loadSavedScenario
  - [ ] 7.6: **Test setup convention**: All tests that exercise first-launch logic must clear localStorage before each test (`localStorage.clear()` in `beforeEach`). Tests for returning-user flow must pre-populate localStorage using the exported key constants from `useScenarioPersistence.ts`.
- [ ] Task 8: Run quality gates (AC: all)
  - [ ] 8.1: `npm run typecheck` — 0 errors
  - [ ] 8.2: `npm run lint` — 0 errors (fast-refresh warnings pre-existing, OK)
  - [ ] 8.3: `npm test` — all tests pass (including all new and existing tests)
  - [ ] 8.4: `uv run ruff check src/ tests/` — 0 errors (backend unchanged but verify)
  - [ ] 8.5: `uv run mypy src/` — passes (backend unchanged but verify)

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
      1. loadScenario() from localStorage → setActiveScenario
      2. loadStage() from localStorage → navigateTo(savedStage)
      3. If loadScenario() returns null → fall through to demo
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
| `activeScenario.policyType = "carbon_tax"` | `selectedTemplateId = "carbon-tax-dividend"` | `startRun()` uses `selectedTemplateId` to find template params |
| `activeScenario.populationIds[0]` | `selectedPopulationId = "fr-synthetic-2024"` | `startRun()` passes `population_id` to API |
| `activeScenario.engineConfig` | (no legacy equivalent) | Engine config only used by `activeScenario` |

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

### Debug Log References

### Completion Notes List

### File List
