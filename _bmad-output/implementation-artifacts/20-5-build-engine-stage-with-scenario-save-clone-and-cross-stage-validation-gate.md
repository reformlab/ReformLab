# Story 20.5: Build Engine Stage with Scenario Save/Clone and Cross-Stage Validation Gate

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to configure the simulation engine (time horizon, seed, population selection, investment-decision model) and see a cross-stage validation checklist before running,
so that I can assemble a fully-specified, executable scenario and be blocked with actionable guidance when my setup is incomplete or incompatible.

## Acceptance Criteria

1. **AC-1: Engine configuration form** — Given Stage 3 (Engine) is open, when the user views the screen, then the stage shows a configuration form with: (a) **Time horizon** — start year and end year numeric inputs, a computed "N-year projection" label, and inline validation (endYear ≤ startYear produces a field-level error); (b) **Population selection** — a dropdown pre-populated from `activeScenario.populationIds[0]`, listing all available populations (built-in + Data Fusion result), updating `activeScenario.populationIds` and legacy `selectedPopulationId` on change, plus a text-link "+ Add population for sensitivity" that adds a second dropdown (max 2 populations in Story 20.5); (c) **Random seed** — a "Use deterministic seed" checkbox and a number input shown when checked (null when unchecked = let backend choose); (d) **Investment decisions** — a Switch toggle that expands an inline accordion when enabled, revealing: logit model dropdown (multinomial_logit / nested_logit / mixed_logit), taste parameter sliders (2–3 representative sliders with realistic defaults), and a `CalibrationPanel` stub (shows calibration status badge + method dropdown + disabled "Run Calibration" button); (e) **Discount rate** — a slider (0–10%, step 0.5%) with a numeric input, default 3%.

2. **AC-2: Scenario save and clone** — Given the Engine stage toolbar, when the user clicks "Save Scenario", then `saveCurrentScenario()` is called, the scenario is added to the saved list, and a success toast appears. When the user clicks "Clone Scenario", then `cloneCurrentScenario()` is called, the copy becomes `activeScenario`, and a success toast appears. The scenario name is editable inline in the toolbar (calls `updateScenarioField("name", newName)`). All field changes (time horizon, seed, populations, investment decisions, discount rate) are persisted automatically via `updateScenarioField("engineConfig", {...})` as the user types/changes controls.

3. **AC-3: Cross-stage validation gate with extensible check registry** — Given the Engine stage right panel, when the user views the validation gate, then a checklist displays the result of each registered `ValidationCheck`. The registry is an exported array `VALIDATION_CHECKS: ValidationCheck[]` defined in `frontend/src/components/engine/validationChecks.ts`. Built-in checks for Story 20.5: `portfolio-selected` (error if `activeScenario.portfolioName === null`), `population-selected` (error if `activeScenario.populationIds.length === 0`), `time-horizon-valid` (error if `startYear >= endYear` or `endYear - startYear > 50`), `investment-decisions-calibrated` (warning if investment decisions are enabled but calibration status is "not_configured"), and `memory-preflight` (async error/warning via `checkMemory()` API). Each check result shows: a status icon (✓ / ✗ / ⚠), a human-readable label, and an actionable error message when failing.

4. **AC-4: Execution blocked on validation failure** — Given one or more `"error"`-severity validation checks are failing, when the "Run Simulation" button is visible, then it is `disabled` and shows a tooltip listing the failing checks. Passing validation navigates to `results/runner` (no execution happens in Stage 3 — Stage 4 / `SimulationRunnerScreen` handles the run). Async memory-preflight is triggered by clicking "Run Simulation"; it shows a loading spinner on the button while pending.

5. **AC-5: Extensible check registry design** — Given the `VALIDATION_CHECKS` array in `validationChecks.ts`, when a new check is appended to it, then the `ValidationGate` component automatically renders the new check without code changes. Each `ValidationCheck` has: `id: string`, `label: string`, `severity: "error" | "warning"`, and `fn: (ctx: ValidationContext) => ValidationCheckResult | Promise<ValidationCheckResult>`. `ValidationContext` includes: `scenario: WorkspaceScenario | null`, `populations: Population[]`, `dataFusionResult: GenerationResult | null`, `portfolios: PortfolioListItem[]`. This design allows EPIC-21 Story 21.5 to append trust-status checks to the registry without modifying existing components.

## Tasks / Subtasks

- [x] Task 1: Extend `EngineConfig` in workspace types and update dependent code (AC: #1, #2)
  - [x] 1.1: In `frontend/src/types/workspace.ts`, add two new fields to `EngineConfig`:
    - `logitModel: "multinomial_logit" | "nested_logit" | "mixed_logit" | null` — null when investment decisions disabled
    - `discountRate: number` — default 0.03
  - [x] 1.2: Update the `createNewScenario()` in `AppContext.tsx` (line 335) to include the new defaults:
    ```typescript
    engineConfig: {
      startYear: 2025, endYear: 2030, seed: null,
      investmentDecisionsEnabled: false,
      logitModel: null, discountRate: 0.03,
    }
    ```
  - [x] 1.3: Update `createDemoScenario()` in `frontend/src/data/demo-scenario.ts` to include the new fields: `logitModel: null, discountRate: 0.03`.
  - [x] 1.4: Check all places that construct a `WorkspaceScenario` literal (grep `engineConfig:`) and add the new fields with defaults. Expected locations: `AppContext.tsx` (createNewScenario, cloneCurrentScenario is OK — spread already copies all fields), `demo-scenario.ts`, any test fixtures that construct `EngineConfig` directly.
  - [x] 1.5: Run `npm run typecheck` to verify no TypeScript errors from the new fields before proceeding.

- [x] Task 2: Create validation check registry (AC: #3, #5)
  - [x] 2.1: Create `frontend/src/components/engine/validationChecks.ts`. This file defines the extensible check registry. Do NOT import from AppContext — take all inputs as a `ValidationContext` parameter.
    ```typescript
    // frontend/src/components/engine/validationChecks.ts
    // SPDX-License-Identifier: AGPL-3.0-or-later
    // Copyright 2026 Lucas Vivier
    /** Cross-stage validation check registry for the Engine preflight gate.
     *
     * Each ValidationCheck has an id, label, severity, and fn.
     * EPIC-21 Story 21.5 appends trust-status checks to VALIDATION_CHECKS
     * without modifying this file or ValidationGate.
     *
     * Story 20.5 — AC-3, AC-5.
     */
    export interface ValidationCheckResult {
      passed: boolean;
      message: string;  // shown when not passed; empty string when passed
      severity: "error" | "warning";
    }
    export interface ValidationContext { ... }
    export interface ValidationCheck {
      id: string;
      label: string;
      severity: "error" | "warning";
      fn: (ctx: ValidationContext) => ValidationCheckResult | Promise<ValidationCheckResult>;
    }
    export const VALIDATION_CHECKS: ValidationCheck[] = [
      portfolioSelectedCheck,
      populationSelectedCheck,
      timeHorizonValidCheck,
      investmentDecisionsCalibratedCheck,
      memoryPreflightCheck,  // async — calls checkMemory() API
    ];
    ```
  - [x] 2.2: Implement all 5 built-in checks as pure functions:
    - `portfolioSelectedCheck` — severity "error"; passes when `scenario?.portfolioName` is non-null/non-empty; message: "No portfolio selected. Go to Stage 1 to compose a portfolio."
    - `populationSelectedCheck` — severity "error"; passes when `scenario?.populationIds.length > 0`; message: "No population selected. Go to Stage 2 to select a population."
    - `timeHorizonValidCheck` — severity "error"; passes when `startYear < endYear` AND `endYear - startYear <= 50`; messages: "End year must be greater than start year." / "Time horizon exceeds 50 years — reduce the range."
    - `investmentDecisionsCalibratedCheck` — severity "warning"; only applies when `scenario?.engineConfig.investmentDecisionsEnabled === true`; passes (with a note) if disabled; message when enabled: "Investment decisions are enabled but calibration is not configured. Results will use uncalibrated taste parameters."
    - `memoryPreflightCheck` — severity "error"; async; calls `checkMemory({ template_name: scenario.policyType ?? "", start_year: engineConfig.startYear, end_year: engineConfig.endYear, population_id: populationIds[0] ?? null })`; passes when `!response.should_warn`; message: `response.message`; on API failure (network error or 404) → returns `{ passed: true, message: "", severity: "error" }` (API unavailable is not blocking). See Task 5.
  - [x] 2.3: Export `VALIDATION_CHECKS`, `ValidationCheck`, `ValidationCheckResult`, `ValidationContext` from this file. No default export.

- [x] Task 3: Build `ValidationGate` and `RunSummaryPanel` components (AC: #3, #4, #5)
  - [x] 3.1: Create `frontend/src/components/engine/RunSummaryPanel.tsx`. A compact summary card showing everything that will be computed:
    - Scenario name + status badge (draft / ready / running / completed)
    - Baseline indicator: `[Baseline]` or `[Reform vs {baselineRef}]`
    - Portfolio: name (if set) + policy count (from portfolios list), or "— no portfolio" in red
    - Population(s): name(s) with row count, or "— no population" in red
    - Time horizon: `"YYYY – YYYY (N years)"`, or shows validation error in red
    - Investment decisions: "Enabled (multinomial logit)" or "Disabled"
    - Seed: "Fixed (seed: N)" or "Random"
    - Total estimated runs: `populationIds.length × 1 scenario` (e.g., "1 run" or "2 runs")
    - Applies Tailwind utility classes; no external state — receives all data as props.
  - [x] 3.2: Create `frontend/src/components/engine/ValidationGate.tsx`. Uses `VALIDATION_CHECKS` array directly (static import — does NOT accept a checks prop, to keep EPIC-21 injection at import-time). Props:
    ```typescript
    interface ValidationGateProps {
      context: ValidationContext;
      onRun: () => void;
      runLoading: boolean;
    }
    ```
    - Runs all sync checks immediately (no debounce needed — they're fast).
    - Async `memoryPreflightCheck` runs only when user clicks "Run Simulation" (not on every state change). Show loading spinner on the button while pending.
    - Check list: each row shows `CheckCircle2` (passed), `XCircle` (error), or `AlertTriangle` (warning) icon + label + error message when failing.
    - "Run Simulation" button: `disabled` when any "error" check is failing OR when `runLoading` is true. Tooltip (Shadcn Tooltip) on the disabled button lists failing check labels.
    - When button is clicked: run async check first → if all pass → call `onRun()`.
  - [x] 3.3: The `onRun` callback in `EngineStageScreen` calls `navigateTo("results", "runner")` — navigation to Stage 4 is the trigger for the runner screen to appear. Execution happens in `SimulationRunnerScreen`, not here.

- [x] Task 4: Build `InvestmentDecisionsAccordion` and `CalibrationPanel` (AC: #1)
  - [x] 4.1: Create `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx`. Uses the Shadcn `Switch` component for the toggle. When enabled, the accordion content expands in place (no routing, no sub-screen):
    - Logit model select: three options (`multinomial_logit` / `nested_logit` / `mixed_logit`). On change: calls `onEngineConfigChange({ ...config, logitModel: value })`.
    - Taste parameters: 3 representative sliders with Shadcn `Slider` component:
      - Price sensitivity (β_price): range [-5, 0], default -1.5, step 0.1
      - Range anxiety (β_range): range [-3, 0], default -0.8, step 0.1
      - Environmental preference (β_green): range [0, 3], default 0.5, step 0.1
    - These taste parameter values are display-only in Story 20.5 (NOT saved to `EngineConfig`). Add a `// TODO(Story 20.6+): persist taste params to EngineConfig` comment. Show values from local component state initialized to defaults.
    - `CalibrationPanel` (from Task 4.2) renders below taste parameters.
  - [x] 4.2: Create `frontend/src/components/engine/CalibrationPanel.tsx`. This is a **UI stub** — calibration backend is not available in Story 20.5. Shows:
    - Status badge: "Not configured" (amber) / "Calibrated ✓" (green — future state)
    - Calibration method select: "Maximum Likelihood (MLE)" / "Simulated Method of Moments (SMM)" — display only, no-op
    - Calibration targets table: empty table with columns [Target, Observed, Weight] and an "Add target" button that shows a `toast.info("Calibration targets coming soon")` toast (placeholder)
    - "Run Calibration" button: always `disabled`, tooltip "Full calibration available in a future release"
    - A `// Story 20.5 stub: full calibration implementation deferred` comment at file top
  - [x] 4.3: `InvestmentDecisionsAccordion` receives props:
    ```typescript
    interface InvestmentDecisionsAccordionProps {
      config: EngineConfig;
      onEngineConfigChange: (config: EngineConfig) => void;
    }
    ```
    Toggle calls `onEngineConfigChange({ ...config, investmentDecisionsEnabled: !config.investmentDecisionsEnabled, logitModel: !config.investmentDecisionsEnabled ? "multinomial_logit" : null })`.

- [x] Task 5: Build `EngineStageScreen` (AC: #1, #2, #3, #4)
  - [x] 5.1: Replace the stub at `frontend/src/components/screens/EngineStageScreen.tsx` with a stateful coordinator. It reads all state from `useAppState()` and has no props.
  - [x] 5.2: Layout: two-column split — left config form (flex-1) + right summary+validation panel (w-80 fixed). At narrow widths (<1200px) the right panel stacks below the form.
    ```
    ┌──────────────────────────────────────────────────────────────────────┐
    │ Toolbar: [scenario name input] [Save Scenario] [Clone Scenario]      │
    ├─────────────────────────────────────┬────────────────────────────────┤
    │ Configuration form (left)           │ Run Summary + Validation (right)│
    │                                     │                                 │
    │ Time Horizon                        │ RunSummaryPanel                 │
    │  Start year: [____] End: [____]     │ ─────────────────────────────   │
    │  "11-year projection"               │ ValidationGate                  │
    │                                     │  ✓ Portfolio selected           │
    │ Population                          │  ✗ No population selected       │
    │  Primary: [FR-2024 ▾]              │  ✓ Time horizon valid           │
    │  + Add population for sensitivity   │  ⚠ Calibration not configured   │
    │                                     │  … Memory check (async)         │
    │ Random Seed                         │                                 │
    │  ☐ Use deterministic seed           │  [Run Simulation ▶] (disabled)  │
    │                                     │                                 │
    │ Investment Decisions  ●──○          │                                 │
    │  (accordion collapsed)              │                                 │
    │                                     │                                 │
    │ Discount Rate                       │                                 │
    │  [───●──────] 3.0%                  │                                 │
    └─────────────────────────────────────┴────────────────────────────────┘
    ```
  - [x] 5.3: **Toolbar** — scenario name is an `<Input>` that:
    - Shows `activeScenario?.name ?? "New Scenario"`
    - On blur/Enter: calls `updateScenarioField("name", value)`
    - Max length: 80 characters
    - "Save Scenario" button: calls `saveCurrentScenario()` from `useAppState()`
    - "Clone Scenario" button: calls `cloneCurrentScenario()` from `useAppState()`
  - [x] 5.4: **Time horizon** — two number inputs (`type="number"`, min=1990, max=2100). On change: `updateScenarioField("engineConfig", { ...engineConfig, startYear/endYear: newVal })`. Show inline error `"End year must be after start year"` below inputs when `startYear >= endYear`. Show `"${endYear - startYear}-year projection"` label when valid.
  - [x] 5.5: **Population selector** — a `<select>` element (not Shadcn Select, for simpler multi-population support) showing all populations. Population list is computed:
    ```typescript
    const allPopulations = useMemo(() => [
      ...populations.map(p => ({ id: p.id, name: p.name, households: p.households })),
      ...(dataFusionResult ? [{ id: "data-fusion-result", name: "Fused Population", households: dataFusionResult.summary.record_count }] : []),
    ], [populations, dataFusionResult]);
    ```
    Primary selection: `activeScenario?.populationIds[0] ?? ""`. On change: `updateScenarioField("populationIds", [id])` AND `setSelectedPopulationId(id)` (legacy sync).
    Secondary population: shown when `hasSecondary` local state is true. On change: `updateScenarioField("populationIds", [primaryId, secondaryId])`. "× Remove" link removes secondary and resets `populationIds` to `[primaryId]`.
    "+ Add population for sensitivity" is a text `<button type="button">` styled with `text-blue-600 text-sm underline` — sets `hasSecondary = true`.
  - [x] 5.6: **Seed** — a controlled checkbox (`useLocalSeedEnabled` local state). When checked: show number input. On change: `updateScenarioField("engineConfig", { ...engineConfig, seed: enabled ? (value ?? 42) : null })`.
  - [x] 5.7: **Investment decisions** — render `InvestmentDecisionsAccordion` with `config={engineConfig}` and `onEngineConfigChange={(cfg) => updateScenarioField("engineConfig", cfg)}`.
  - [x] 5.8: **Discount rate** — Shadcn `Slider` (min=0, max=10, step=0.5) with a numeric input. On change: `updateScenarioField("engineConfig", { ...engineConfig, discountRate: value / 100 })`. Display as percentage: `Math.round(engineConfig.discountRate * 100 * 10) / 10 + "%"`.
  - [x] 5.9: **Right panel** — renders `<RunSummaryPanel>` and `<ValidationGate>`. `ValidationGate` receives:
    - `context: { scenario: activeScenario, populations, dataFusionResult, portfolios }`
    - `onRun: () => navigateTo("results", "runner")`
    - `runLoading: false` (run execution is in Stage 4)
  - [x] 5.10: Handle `activeScenario === null` gracefully: render a centered `"No active scenario"` message with a `"Start a new scenario"` button calling `createNewScenario()`.

- [x] Task 6: Update help content (AC: all)
  - [x] 6.1: In `frontend/src/components/help/help-content.ts`, update the `"engine"` entry to reflect the full Stage 3 content:
    - title: "Engine Configuration"
    - summary: "Assemble your scenario: bind portfolio and population, configure time horizon, seed, and investment-decision model. Cross-stage validation must pass before running."
    - tips:
      - "Set Start and End year — the 'N-year projection' label updates automatically. Max 50 years."
      - "Investment decisions expand inline when enabled — logit model and taste parameters appear without leaving the stage."
      - "The right panel shows a live validation checklist — all red checks must be resolved before Run is enabled."
      - "Save Scenario persists the full configuration (portfolio + population + engine settings) to your saved list."
      - "Clone Scenario creates a copy with '(copy)' appended — useful for sensitivity analysis variants."
      - "The memory preflight check runs when you click Run — it estimates if your population fits in RAM."
    - concepts: Random Seed / Logit Model / Cross-stage validation
  - [x] 6.2: No new sub-view keys needed (Engine has no sub-views in Story 20.5).

- [x] Task 7: Add tests (AC: all)
  - [x] 7.1: Create `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx`. Mock patterns:
    ```typescript
    vi.mock("@/contexts/AppContext", () => ({ useAppState: vi.fn() }));
    vi.mock("@/api/runs", () => ({ checkMemory: vi.fn() }));
    ```
    Tests (group by class `TestEngineStageScreen`):
    - Renders time horizon inputs with values from `activeScenario.engineConfig`
    - Start year input change calls `updateScenarioField("engineConfig", {..., startYear: N})`
    - End year input change calls `updateScenarioField("engineConfig", {..., endYear: N})`
    - Shows "N-year projection" label when `endYear > startYear`
    - Shows "End year must be after start year" error when `startYear >= endYear`
    - Population dropdown lists all populations from AppContext
    - Selecting population calls `updateScenarioField("populationIds", [id])` AND `setSelectedPopulationId(id)`
    - "+ Add population for sensitivity" link appears and shows second dropdown on click
    - Investment decisions toggle shows/hides accordion
    - When accordion visible: logit model dropdown renders with 3 options
    - Save Scenario button calls `saveCurrentScenario()`
    - Clone Scenario button calls `cloneCurrentScenario()`
    - Scenario name input update calls `updateScenarioField("name", newName)`
    - Renders "No active scenario" state when `activeScenario` is null
  - [x] 7.2: Create `frontend/src/components/engine/__tests__/ValidationGate.test.tsx`. Tests:
    - All checks passing → Run button is enabled
    - Portfolio check failing → Run button is disabled, shows error message
    - Population check failing → Run button is disabled
    - Time horizon check failing (startYear >= endYear) → shows error
    - Warning check failing (calibration) → Run button is still enabled (warnings don't block)
    - Clicking Run when all errors pass → calls `onRun()`
    - Clicking Run triggers async `memoryPreflightCheck`; shows loading state while pending
  - [x] 7.3: Create `frontend/src/components/engine/__tests__/validationChecks.test.ts`. Unit-tests for each built-in check:
    - `portfolioSelectedCheck`: passes/fails with/without `portfolioName`
    - `populationSelectedCheck`: passes/fails with/without `populationIds`
    - `timeHorizonValidCheck`: passes for valid ranges, fails for inverted or >50yr range
    - `investmentDecisionsCalibratedCheck`: warning when enabled, passes when disabled
    - `memoryPreflightCheck`: calls `checkMemory()`, passes when `!should_warn`, fails when `should_warn: true`, returns passed on API error (graceful degradation)
  - [x] 7.4: Add a Story 20.5 section to `frontend/src/__tests__/workflows/analyst-journey.test.tsx`:
    - Navigate to `#engine`, verify Engine Configuration heading is visible
    - Verify validation checklist is visible
    - Verify Run button is disabled when portfolio and population not selected (all fresh scenario)
    - Set `activeScenario` with populated portfolio + population → verify Run button becomes enabled (or at least not blocked by those checks)
  - [x] 7.5: Verify no regressions in existing tests:
    - `PoliciesStageScreen` tests (Stage 1 unchanged)
    - `PopulationStageScreen` tests (Stage 2 unchanged)
    - `WorkflowNavRail` tests — ensure `populations` prop still works after `EngineConfig` changes
    - All `App.test.tsx` assertions still pass
    - `demo-scenario.ts` snapshot tests (if any) — update for new `EngineConfig` fields

- [x] Task 8: Run quality gates (AC: all)
  - [x] 8.1: `npm run typecheck` — 0 errors (critical: `EngineConfig` extension must not break existing callers)
  - [x] 8.2: `npm run lint` — 0 errors
  - [x] 8.3: `npm test` — all tests pass, 0 failures, 0 regressions
  - [x] 8.4: `uv run ruff check src/ tests/` — 0 errors
  - [x] 8.5: `uv run mypy src/` — passes (no backend changes in this story)

## Dev Notes

### Architecture Constraints

- **No backend changes in this story.** The memory-preflight check calls the existing `POST /api/runs/memory-check` endpoint. All other validation is client-side. Population explorer endpoints (`/api/populations/{id}/profile` etc.) are in Story 20.7.
- **No router library.** Engine stage is `#engine`. No sub-views added in Story 20.5 (`SubView` type in `workspace.ts` is NOT modified).
- **No new AppContext state or actions needed.** All required actions are already in `AppState`: `updateScenarioField`, `saveCurrentScenario`, `cloneCurrentScenario`, `navigateTo`, `setSelectedPopulationId`.
- **EngineConfig extension requires touching 3 files**: `workspace.ts` (type), `AppContext.tsx` (createNewScenario default), `demo-scenario.ts` (demo defaults). The `cloneCurrentScenario` spread pattern already copies new fields.
- **Run execution stays in Stage 4.** The "Run Simulation" button in Engine stage only validates and navigates to `results/runner`. `SimulationRunnerScreen` calls `startRun()`. Story 20.6 refactors the runner to be scenario-aware.
- **Taste parameters are display-only in Story 20.5.** They live in local component state of `InvestmentDecisionsAccordion`. Adding them to `EngineConfig` is deferred to a future story when the backend calibration API is defined.
- **CalibrationPanel is a stub.** No calibration API exists yet. The panel shows the intended UI structure with disabled interactions. Full calibration in a future story post-20.6.
- **EPIC-21 extensibility** is achieved by the exported `VALIDATION_CHECKS: ValidationCheck[]` array. EPIC-21 Story 21.5 does `import { VALIDATION_CHECKS } from "@/components/engine/validationChecks"; VALIDATION_CHECKS.push(trustStatusCheck)` — no changes to `ValidationGate` or `EngineStageScreen`.

### EngineConfig Type Extension

`frontend/src/types/workspace.ts` after this story:
```typescript
export interface EngineConfig {
  startYear: number;
  endYear: number;
  seed: number | null;
  investmentDecisionsEnabled: boolean;
  logitModel: "multinomial_logit" | "nested_logit" | "mixed_logit" | null;
  discountRate: number;  // fractional: 0.03 = 3%
}
```

All consumers that construct `EngineConfig` literals must be updated. Run `grep -r "engineConfig:" frontend/src` to find all of them. Expected hits:
- `AppContext.tsx:335` — `createNewScenario()`
- `frontend/src/data/demo-scenario.ts` — `createDemoScenario()`
- Any test fixtures that construct `WorkspaceScenario` or `EngineConfig` literals

The `cloneCurrentScenario()` uses `{ ...activeScenario }` which copies all fields — no change needed there.

### Validation Check Registry Pattern

```typescript
// frontend/src/components/engine/validationChecks.ts

export interface ValidationContext {
  scenario: WorkspaceScenario | null;
  populations: Population[];
  dataFusionResult: GenerationResult | null;
  portfolios: PortfolioListItem[];
}

export interface ValidationCheckResult {
  passed: boolean;
  message: string;
  severity: "error" | "warning";
}

export interface ValidationCheck {
  id: string;
  label: string;
  severity: "error" | "warning";  // default severity (can be overridden by fn result)
  fn: (ctx: ValidationContext) => ValidationCheckResult | Promise<ValidationCheckResult>;
}

export const VALIDATION_CHECKS: ValidationCheck[] = [ /* 5 built-in checks */ ];
```

`ValidationGate` imports `VALIDATION_CHECKS` directly (not via props) so that EPIC-21 can mutate the array at import-time:
```typescript
// EPIC-21 Story 21.5 will do this in a separate module:
import { VALIDATION_CHECKS } from "@/components/engine/validationChecks";
import { trustStatusCheck } from "@/components/evidence/trustStatusCheck";
VALIDATION_CHECKS.push(trustStatusCheck); // array mutation at module initialization
```

This is the simplest extensibility mechanism that requires no changes to `ValidationGate`. Alternative plugin patterns (registry service, React context injection) would be over-engineering for Story 20.5.

### Memory Preflight Integration

`checkMemory()` from `frontend/src/api/runs.ts` takes:
```typescript
{
  template_name: scenario.policyType ?? "",
  start_year: engineConfig.startYear,
  end_year: engineConfig.endYear,
  population_id: populationIds[0] ?? null,
}
```

Returns `{ should_warn: boolean, estimated_gb: number, available_gb: number, message: string }`.

The `memoryPreflightCheck` implementation:
```typescript
async function memoryPreflightFn(ctx: ValidationContext): Promise<ValidationCheckResult> {
  if (!ctx.scenario) return { passed: true, message: "", severity: "error" };
  const { engineConfig, populationIds, policyType } = ctx.scenario;
  try {
    const resp = await checkMemory({
      template_name: policyType ?? "",
      start_year: engineConfig.startYear,
      end_year: engineConfig.endYear,
      population_id: populationIds[0] ?? null,
    });
    return {
      passed: !resp.should_warn,
      message: resp.should_warn ? resp.message : "",
      severity: "error",
    };
  } catch {
    // API unavailable → do not block execution
    return { passed: true, message: "", severity: "error" };
  }
}
```

Note: async check only runs on "Run Simulation" click, not on every state change. Other 4 checks run synchronously on every render.

### ValidationGate Behavior

**Sync checks** (portfolio, population, time horizon, calibration-warning): evaluated on every render using a `useMemo` over `context` — no debounce needed (pure functions, no I/O).

**Async check** (memory preflight): triggered only when the user clicks "Run Simulation":
```typescript
async function handleRun() {
  // 1. Run async check
  setRunLoading(true);
  const memResult = await memoryPreflightCheck.fn(context);
  setMemoryCheckResult(memResult);
  setRunLoading(false);
  // 2. Combine with sync results
  const allResults = [...syncResults, memResult];
  const hasErrors = allResults.some(r => r.severity === "error" && !r.passed);
  if (!hasErrors) onRun();
}
```

Local state in `ValidationGate`: `memoryCheckResult: ValidationCheckResult | null` (null = not yet run), `runLoading: boolean`.

### Component Architecture

```
EngineStageScreen (stateful coordinator, reads from useAppState())
├── Toolbar
│   ├── Scenario name <Input> (inline edit)
│   ├── [Save Scenario] → saveCurrentScenario()
│   └── [Clone Scenario] → cloneCurrentScenario()
├── Left column: Configuration
│   ├── Time Horizon section (start/end year inputs)
│   ├── Population section (<select> + secondary <select>)
│   ├── Random Seed section (checkbox + number input)
│   ├── InvestmentDecisionsAccordion (Switch + accordion)
│   │   ├── Logit model <select>
│   │   ├── Taste parameter sliders (local state only)
│   │   └── CalibrationPanel (UI stub)
│   └── Discount Rate section (Slider + number input)
└── Right column: Summary + Gate
    ├── RunSummaryPanel (pure display, all data via props)
    └── ValidationGate
        ├── Sync checks (useMemo, instant)
        ├── Async check (triggered on Run click)
        ├── Check list (icons + messages)
        └── [Run Simulation ▶] button
```

New files directory: `frontend/src/components/engine/` — a new directory for engine-specific components, parallel to `components/population/` created in Story 20.4.

### State Management in EngineStageScreen

All engine state flows through AppContext:

| What | Source | Writer |
|---|---|---|
| `engineConfig` (all fields) | `activeScenario.engineConfig` | `updateScenarioField("engineConfig", newCfg)` |
| Scenario name | `activeScenario.name` | `updateScenarioField("name", newName)` |
| Population IDs | `activeScenario.populationIds` | `updateScenarioField("populationIds", [id])` |
| Legacy selectedPopulationId | `selectedPopulationId` | `setSelectedPopulationId(id)` |
| Save to list | `savedScenarios` | `saveCurrentScenario()` |
| Clone | (creates new activeScenario) | `cloneCurrentScenario()` |

Local state in `EngineStageScreen` only:
- `hasSecondary: boolean` — whether the second population dropdown is shown

Local state in `InvestmentDecisionsAccordion`:
- `tasteParams: { priceSensitivity, rangeAnxiety, envPreference }` — NOT persisted to `EngineConfig`

Local state in `ValidationGate`:
- `memoryCheckResult: ValidationCheckResult | null`
- `runLoading: boolean`

### Key Interaction: Population Selection Sync

When user selects a population in Engine stage, two things must happen:
1. `updateScenarioField("populationIds", [id])` — canonical scenario field
2. `setSelectedPopulationId(id)` — legacy sync so `SimulationRunnerScreen`'s header shows correct population

This mirrors the pattern established in `PopulationStageScreen.tsx`'s `handleSelect()`.

### Nav Rail Completion (No Changes Needed)

`WorkflowNavRail.tsx` already handles engine stage completion correctly:
```typescript
case "engine":
  return activeScenario !== null;  // isComplete
```
```typescript
case "engine":
  const { startYear, endYear } = activeScenario.engineConfig;
  return `${startYear}–${endYear}`;  // getSummary
```

No changes needed to `WorkflowNavRail.tsx`.

### Scenario Persistence (Already Works)

`AppContext.tsx` (line 282–286) automatically persists `activeScenario` to localStorage on every change:
```typescript
useEffect(() => {
  if (!isAuthenticated || !initializedRef.current) return;
  persistScenario(activeScenario);
}, [activeScenario, isAuthenticated]);
```

So every `updateScenarioField("engineConfig", ...)` automatically saves to localStorage. The explicit "Save Scenario" button (`saveCurrentScenario()`) adds the scenario to the named `savedScenarios` list (`getSavedScenarios()`). These are two different operations:
- Auto-persist: every change (single active scenario)
- Explicit save: user-triggered (adds to list, appears in "Open saved scenario" flow)

### Shadcn Components Used

- `Button` — Save/Clone toolbar buttons, Run Simulation button
- `Input` — Scenario name, year inputs, numeric seed input
- `Slider` — Taste parameters, discount rate
- `Switch` — Investment decisions toggle
- `Badge` — Calibration status, scenario status
- `Tooltip` — Disabled Run button explanation
- `Separator` — Section dividers
- `ScrollArea` — Calibration targets table area

Lucide icons: `Play`, `Save`, `Copy`, `CalendarRange`, `Users`, `Dice1` (or `Hash`), `Brain`, `Wrench`, `CheckCircle2`, `XCircle`, `AlertTriangle`, `Loader2` (spin)

### Files to Create

| File | Purpose |
|---|---|
| `frontend/src/components/engine/validationChecks.ts` | Check registry: types + 5 built-in checks + `VALIDATION_CHECKS` array |
| `frontend/src/components/engine/ValidationGate.tsx` | Check list display + async run trigger + Run button |
| `frontend/src/components/engine/RunSummaryPanel.tsx` | Pre-flight scenario summary card |
| `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx` | Inline toggle + logit model + taste params + CalibrationPanel |
| `frontend/src/components/engine/CalibrationPanel.tsx` | UI stub (status, method, targets, disabled run) |
| `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx` | Unit tests for EngineStageScreen |
| `frontend/src/components/engine/__tests__/ValidationGate.test.tsx` | Unit tests for validation gate |
| `frontend/src/components/engine/__tests__/validationChecks.test.ts` | Unit tests for individual checks |

### Files to Modify

| File | Changes |
|---|---|
| `frontend/src/types/workspace.ts` | Add `logitModel` and `discountRate` to `EngineConfig` |
| `frontend/src/contexts/AppContext.tsx` | Update `createNewScenario()` default `engineConfig` with new fields |
| `frontend/src/data/demo-scenario.ts` | Add new `EngineConfig` fields to `createDemoScenario()` |
| `frontend/src/components/screens/EngineStageScreen.tsx` | Full rewrite — replace stub with complete implementation |
| `frontend/src/components/help/help-content.ts` | Update `"engine"` entry with full Stage 3 content |
| `frontend/src/__tests__/workflows/analyst-journey.test.tsx` | Add Story 20.5 section |
| Any test files that construct `EngineConfig` or `WorkspaceScenario` literals | Add new required fields `logitModel: null, discountRate: 0.03` |

### Files NOT Modified

| File | Why |
|---|---|
| `frontend/src/contexts/AppContext.tsx` (beyond `createNewScenario`) | `cloneCurrentScenario` uses spread — copies new fields automatically. No new actions needed. |
| `frontend/src/components/layout/WorkflowNavRail.tsx` | Engine completion/summary logic already correct |
| `frontend/src/App.tsx` | `EngineStageScreen` has no props; `handleStartRun` in App.tsx remains the execution path |
| `frontend/src/types/workspace.ts` (SubView) | No new sub-views for Engine stage |
| Any backend files (`src/reformlab/`) | Story 20.7 covers backend changes |

### Test Mock Patterns

```typescript
// EngineStageScreen test setup
const mockUpdateScenarioField = vi.fn();
const mockNavigateTo = vi.fn();
const mockSaveCurrentScenario = vi.fn();
const mockCloneCurrentScenario = vi.fn();
const mockSetSelectedPopulationId = vi.fn();

const defaultMockState = {
  activeScenario: {
    id: "test-id",
    name: "Test Scenario",
    portfolioName: "Test Portfolio",
    populationIds: ["fr-synthetic-2024"],
    engineConfig: {
      startYear: 2025, endYear: 2030,
      seed: null, investmentDecisionsEnabled: false,
      logitModel: null, discountRate: 0.03,
    },
    // ... other fields
  },
  populations: [{ id: "fr-synthetic-2024", name: "FR 2024", households: 100000, source: "INSEE", year: 2024 }],
  dataFusionResult: null,
  portfolios: [{ name: "Test Portfolio", description: "", version_id: "v1", policy_count: 1 }],
  updateScenarioField: mockUpdateScenarioField,
  navigateTo: mockNavigateTo,
  saveCurrentScenario: mockSaveCurrentScenario,
  cloneCurrentScenario: mockCloneCurrentScenario,
  setSelectedPopulationId: mockSetSelectedPopulationId,
  // ... other required AppState fields
};

vi.mocked(useAppState).mockReturnValue(defaultMockState as AppState);
```

For `validationChecks.test.ts`, test pure functions directly without mocking AppContext:
```typescript
import { portfolioSelectedCheck, populationSelectedCheck, timeHorizonValidCheck } from "../validationChecks";

const baseCtx: ValidationContext = {
  scenario: null, populations: [], dataFusionResult: null, portfolios: [],
};
```

### EPIC-21 Extensibility Note

The `VALIDATION_CHECKS` array export is the EPIC-21 extension point. Design constraints to maintain:
1. **No closure over React state** — all checks receive `ValidationContext` as an explicit parameter. This enables pure-function testing and external injection.
2. **Array mutation at module-init time** — EPIC-21's trust-status check module pushes to the array when imported. `ValidationGate` imports the array once; since arrays are reference types, mutations are visible.
3. **Severity contract** — `"error"` blocks run; `"warning"` shows but allows run. EPIC-21 trust-status checks use `"error"` severity for `validation-pending` synthetic data used as `production-safe`.
4. **Async checks** — the `fn` signature returns `ValidationCheckResult | Promise<ValidationCheckResult>`. All sync checks return synchronously; only `memoryPreflightCheck` is async. EPIC-21 trust-status checks can be sync (no API call needed — read from population metadata in context).

### Known Limitations / Future Stories

- **Taste parameters** are not persisted to `EngineConfig` in Story 20.5. The sliders are for UX completeness; values reset on component unmount. Story 20.6+ extends `EngineConfig`.
- **CalibrationPanel is a stub.** No backend calibration API in Story 20.5. Full calibration in a dedicated future story.
- **Maximum 2 populations** in the UI. More populations require Story 20.6's multi-run infrastructure.
- **Logit model saved to EngineConfig** but not yet used by the backend. The field is stored and round-tripped, ready for when the backend supports it.
- **Data fusion result population** ("data-fusion-result" ID) is in-memory and survives stage switches but not page reload (same limitation as Story 20.4).

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 20.5 definition, BKL-2005]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Stage 3: ENGINE section]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR25–FR29 governance, FR47–FR53 investment decisions]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Stage 3 engine + scenario semantics]
- [Source: `frontend/src/types/workspace.ts` — `EngineConfig`, `WorkspaceScenario`, `StageKey`]
- [Source: `frontend/src/contexts/AppContext.tsx` — `createNewScenario` (line 325), `cloneCurrentScenario` (line 346), `saveCurrentScenario` (line 298), `updateScenarioField` (line 223)]
- [Source: `frontend/src/api/runs.ts` — `checkMemory()` function]
- [Source: `frontend/src/api/types.ts` — `MemoryCheckRequest`, `MemoryCheckResponse`]
- [Source: `frontend/src/components/screens/PoliciesStageScreen.tsx` — save/load/clone dialog patterns, scenario integration]
- [Source: `frontend/src/components/screens/PopulationStageScreen.tsx` — population merge logic, `handleSelect()` dual-sync pattern]
- [Source: `frontend/src/components/layout/WorkflowNavRail.tsx` — engine completion/summary logic (lines 96–101)]
- [Source: `frontend/src/data/demo-scenario.ts` — `createDemoScenario()`, `EngineConfig` defaults]
- [Source: `_bmad-output/implementation-artifacts/20-4-build-population-library-and-data-explorer-stage.md` — Story 20.4 patterns, dual-sync pattern for population selection]
- [Source: `_bmad-output/implementation-artifacts/20-3-build-policies-and-portfolio-stage-with-inline-composition.md` — save/clone dialog patterns, scenario field update]
- [Source: `_bmad-output/planning-artifacts/epics.md` — EPIC-21 Story 21.5 trust-status validation extension point]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_None — all issues resolved inline._

### Completion Notes List

- **Tooltip stub**: `frontend/src/components/ui/tooltip.tsx` only exports a plain `<span>` wrapper (no `TooltipProvider`/`TooltipTrigger`/`TooltipContent`). Replaced tooltip usage in `ValidationGate.tsx` and `CalibrationPanel.tsx` with `title` attributes and inline text.
- **Switch stub**: `Switch` renders as `<input type="checkbox">` (not Radix). Used `onChange={(e) => handler(e.target.checked)}` instead of `onCheckedChange`.
- **React hooks before early return**: `useMemo` for `allPopulations` and `validationContext` must precede the `if (!activeScenario)` early return in `EngineStageScreen`. Removed a duplicate `validationContext` useMemo that was accidentally placed after the return.
- **Controlled number inputs in tests**: `userEvent.type` fires onChange for each character, producing intermediate values. Replaced with `fireEvent.change(input, { target: { value: "2026" } })` for number inputs.
- **Switch role in tests**: `getByRole("switch")` fails because the element renders as `<input type="checkbox">` (role = "checkbox"). Fixed test to use `getByRole("checkbox", { name: /toggle investment decisions/i })`.
- **ResizeObserver in tests**: The Shadcn `Slider` uses Radix UI which requires `ResizeObserver`. Added `beforeAll(() => { setupResizeObserver(); })` in `EngineStageScreen.test.tsx`.
- **Pre-existing pytest failure**: `tests/server/test_api.py::TestTemplateDetail::test_get_template_detail_for_first_available_template` fails before and after Story 20.5 changes. Not caused by this story.
- **Taste parameters**: Local state only in `InvestmentDecisionsAccordion` — not persisted to `EngineConfig` in this story per spec. `TODO(Story 20.6+)` comment added.

### File List

**Created:**
- `frontend/src/components/engine/validationChecks.ts`
- `frontend/src/components/engine/ValidationGate.tsx`
- `frontend/src/components/engine/RunSummaryPanel.tsx`
- `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx`
- `frontend/src/components/engine/CalibrationPanel.tsx`
- `frontend/src/components/engine/__tests__/validationChecks.test.ts`
- `frontend/src/components/engine/__tests__/ValidationGate.test.tsx`
- `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx`

**Modified:**
- `frontend/src/types/workspace.ts` — added `logitModel` and `discountRate` to `EngineConfig`
- `frontend/src/contexts/AppContext.tsx` — updated `createNewScenario()` default `engineConfig`
- `frontend/src/data/demo-scenario.ts` — added new `EngineConfig` fields to `createDemoScenario()`
- `frontend/src/components/screens/EngineStageScreen.tsx` — full rewrite (stub → complete implementation)
- `frontend/src/components/help/help-content.ts` — updated `"engine"` entry
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — added Story 20.5 section
- `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` — added `logitModel`/`discountRate` to fixtures
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — added new `EngineConfig` fields to fixtures
- `frontend/src/components/scenario/__tests__/ScenarioEntryDialog.test.tsx` — added new `EngineConfig` fields to fixtures
- `frontend/src/components/screens/__tests__/PopulationStageScreen.test.tsx` — added new `EngineConfig` fields to fixtures
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — added new `EngineConfig` fields to fixtures
