
# Story 18.5: Consolidate Configuration Flow and Split Dense Screens

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst navigating the ReformLab workspace,
I want the configuration flow consolidated into its own screen component and the densest screen files broken into focused sub-component files,
so that the codebase is easier to maintain, App.tsx is readable at a glance, and future modifications to comparison or configuration UI can be made without wading through 789-line monoliths.

## Acceptance Criteria

1. **AC-1: ConfigurationScreen extraction** — Given the current inline configuration JSX in `App.tsx:281-335` (ModelConfigStepper + 4 conditional step screens + Next/Go-to-Simulation button), when this story is complete, then:
   - A dedicated `ConfigurationScreen` component exists at `frontend/src/components/screens/ConfigurationScreen.tsx`
   - `App.tsx` renders `<ConfigurationScreen ... />` in the `viewMode === "configuration"` block instead of the inline JSX
   - The `STEP_ORDER` constant and `getConfigSteps()` function move from `App.tsx` into `ConfigurationScreen.tsx`
   - ConfigurationScreen internally computes `configSteps` (from `activeStep`), `filteredParameters` (from `parameters` + `selectedTemplate`), and `isLastStep`; handles the "Next Step" / "Go to Simulation" button logic via step advancement + `onGoToSimulation` callback
   - `activeStep` state remains in `App.tsx` (the right panel references it for the workspace state badge at line ~506)

2. **AC-2: ComparisonDashboardScreen sub-component extraction** — Given the current 789-line `ComparisonDashboardScreen.tsx` with 4 inline sub-components and 5 helper functions, when this story is complete, then:
   - `RunSelector` (lines 135-239) is extracted to `frontend/src/components/comparison/RunSelector.tsx`
   - `FiscalTab` (lines 244-332) is extracted to `frontend/src/components/comparison/FiscalTab.tsx`
   - `WelfareTab` (lines 337-459) is extracted to `frontend/src/components/comparison/WelfareTab.tsx`
   - `DetailPanel` (lines 465-524) is extracted to `frontend/src/components/comparison/DetailPanel.tsx`
   - Helper functions (`runLabel`, `statusVariant`, `buildSeries`, `escapeCsvField`, `exportComparisonCsv`) and shared types (`ViewMode`, `ActiveTab`, `DetailTarget`) are extracted to `frontend/src/components/comparison/comparison-helpers.ts`
   - `ComparisonDashboardScreen.tsx` imports from the new files and contains only orchestration state + layout (~265 lines)
   - The new `components/comparison/` folder has an `index.ts` barrel export

3. **AC-3: App.tsx simplification** — Given the extractions in AC-1 and AC-2, when complete, then:
   - `App.tsx` no longer contains the `STEP_ORDER` constant or the `getConfigSteps()` function
   - The `configSteps` memo, `filteredParameters` memo, and `isLastStep` derivation are removed from `App.tsx` (moved into ConfigurationScreen)
   - The `nextStep` function is removed from `App.tsx`
   - The inline `viewMode === "configuration"` JSX block (~50 lines) is replaced by a single `<ConfigurationScreen ... />` element
   - All imports that were only used by the configuration block (`ModelConfigStepper`, `PopulationSelectionScreen`, `TemplateSelectionScreen`, `ParameterEditingScreen`, `AssumptionsReviewScreen`, `ConfigStep` type) are removed from `App.tsx` and added to `ConfigurationScreen.tsx`

4. **AC-4: State preservation and no regressions** — Given both extractions, when the user navigates between configuration steps, view modes, and comparison tabs, then:
   - All navigational state is preserved identically to before (stepping forward/backward in config, switching viewMode, tab switching in comparison)
   - All pre-existing 311 tests pass (0 failures)
   - `npm run typecheck` reports 0 errors
   - `npm run lint` reports 0 errors (pre-existing fast-refresh warnings OK)

5. **AC-5: ConfigurationScreen tests** — Given the new `ConfigurationScreen` component, when tested, then:
   - A test file exists at `frontend/src/components/screens/__tests__/ConfigurationScreen.test.tsx`
   - Tests cover: default step rendering (population), step advancement via "Next Step", "Go to Simulation" text on last step, `onGoToSimulation` callback on last-step click, non-blocking step selection via stepper, correct screen rendered for each step (PopulationSelectionScreen, TemplateSelectionScreen, ParameterEditingScreen, AssumptionsReviewScreen), and parameter filtering by selected template

## Tasks / Subtasks

- [x] Task 1: Create ConfigurationScreen component (AC: 1, 3)
  - [x] 1.1: Create `frontend/src/components/screens/ConfigurationScreen.tsx` with props interface; move `STEP_ORDER`, `getConfigSteps`, step navigation logic
  - [x] 1.2: Implement internal `filteredParameters` memo (filter `parameters` by `selectedTemplate.parameterGroups`)
  - [x] 1.3: Implement `nextStep` handler internally (advance step or call `onGoToSimulation`)
  - [x] 1.4: Render ModelConfigStepper + conditional step screens + Next/GoToSimulation button

- [x] Task 2: Wire ConfigurationScreen into App.tsx (AC: 1, 3)
  - [x] 2.1: Import `ConfigurationScreen`, replace inline configuration JSX block with `<ConfigurationScreen ... />`
  - [x] 2.2: Remove `STEP_ORDER`, `getConfigSteps`, `configSteps` memo, `filteredParameters` memo, `isLastStep`, `nextStep` from App.tsx
  - [x] 2.3: Remove imports only used by configuration block (`ModelConfigStepper` component, `PopulationSelectionScreen`, `TemplateSelectionScreen`, `ParameterEditingScreen`, `AssumptionsReviewScreen`, `ConfigStep` type); add `import type { ConfigStepKey } from "@/components/simulation/ModelConfigStepper"` to App.tsx; update `activeStep` state type from `ConfigStep["key"]` to `ConfigStepKey`
  - [x] 2.4: Keep `activeStep`/`setActiveStep` state in App.tsx (right panel uses it)

- [x] Task 3: Extract ComparisonDashboardScreen sub-components (AC: 2)
  - [x] 3.1: Create `frontend/src/components/comparison/comparison-helpers.ts` — move `ViewMode`, `ActiveTab`, `DetailTarget`, `MAX_RUNS`, `METHODOLOGY_DESCRIPTIONS`, `runLabel`, `statusVariant`, `buildSeries`, `escapeCsvField`, `exportComparisonCsv`; add imports: `ResultListItem`, `PortfolioComparisonResponse` from `@/api/types`; `CHART_COLORS` and `SeriesSpec` from `@/components/simulation/MultiRunChart`
  - [x] 3.2: Create `frontend/src/components/comparison/RunSelector.tsx` — move `RunSelectorProps` + `RunSelector` function; import `runLabel`, `statusVariant`, `MAX_RUNS` from helpers
  - [x] 3.3: Create `frontend/src/components/comparison/FiscalTab.tsx` — move `FiscalTab` function; import `ViewMode` + `columnarToRows` from respective sources
  - [x] 3.4: Create `frontend/src/components/comparison/WelfareTab.tsx` — move `WelfareTab` function; import `ViewMode` + `columnarToRows`
  - [x] 3.5: Create `frontend/src/components/comparison/DetailPanel.tsx` — move `DetailPanel` function only; `DetailTarget` type stays in `comparison-helpers.ts` and is imported via `import type { DetailTarget } from "./comparison-helpers"`
  - [x] 3.6: Create `frontend/src/components/comparison/index.ts` barrel export
  - [x] 3.7: Update `ComparisonDashboardScreen.tsx` — replace inline sub-components with imports from `@/components/comparison`; remove moved code

- [x] Task 4: ConfigurationScreen tests (AC: 5)
  - [x] 4.1: Create `frontend/src/components/screens/__tests__/ConfigurationScreen.test.tsx`
  - [x] 4.2: Test: renders PopulationSelectionScreen by default (activeStep="population")
  - [x] 4.3: Test: renders TemplateSelectionScreen when activeStep="template"
  - [x] 4.4: Test: renders ParameterEditingScreen when activeStep="parameters"
  - [x] 4.5: Test: renders AssumptionsReviewScreen when activeStep="assumptions"
  - [x] 4.6: Test: "Next Step" button advances step via onStepSelect callback
  - [x] 4.7: Test: shows "Go to Simulation" on last step (assumptions)
  - [x] 4.8: Test: clicking "Go to Simulation" calls onGoToSimulation
  - [x] 4.9: Test: clicking stepper step calls onStepSelect (non-blocking navigation)
  - [x] 4.10: Test: filters parameters by selected template's parameterGroups

- [x] Task 5: Verify no regressions (AC: 4)
  - [x] 5.1: Run `npm test` — all pre-existing tests pass; new tests pass
  - [x] 5.2: Run `npm run typecheck` — 0 errors
  - [x] 5.3: Run `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)

## Dev Notes

### ConfigurationScreen — Props Interface

```tsx
// frontend/src/components/screens/ConfigurationScreen.tsx

import type { ConfigStepKey } from "@/components/simulation/ModelConfigStepper";
import type { Parameter, Population, Template } from "@/data/mock-data";

export interface ConfigurationScreenProps {
  activeStep: ConfigStepKey;
  onStepSelect: (step: ConfigStepKey) => void;
  populations: Population[];
  selectedPopulationId: string;
  onSelectPopulation: (id: string) => void;
  templates: Template[];
  selectedTemplateId: string;
  onSelectTemplate: (id: string) => void;
  onTemplatesChanged: () => void;
  parameters: Parameter[];              // Unfiltered — ConfigurationScreen filters internally
  parameterValues: Record<string, number>;
  onParameterChange: (id: string, value: number) => void;
  onGoToSimulation: () => void;         // Called when user clicks "Go to Simulation" on last step
}
```

**Key design decisions:**
- `activeStep` state remains in App.tsx because the right panel displays it (`<Badge variant="violet">{activeStep}</Badge>` at App.tsx line ~506)
- `parameters` are passed unfiltered; ConfigurationScreen computes `filteredParameters` and derives `selectedPopulation`/`selectedTemplate` internally from the lists + IDs
- `onGoToSimulation` replaces the `setViewMode("run")` call that was previously inside `nextStep()`
- No `configSteps` prop — ConfigurationScreen computes it internally from `activeStep`

### Code to Move from App.tsx into ConfigurationScreen

**Constants and functions to move:**
```tsx
// These move from App.tsx top-level into ConfigurationScreen.tsx

const STEP_ORDER: ConfigStepKey[] = [
  "population",
  "template",
  "parameters",
  "assumptions",
];

function getConfigSteps(activeStep: ConfigStepKey): ConfigStep[] {
  return [
    { key: "population", label: "Population", status: activeStep === "population" ? "incomplete" : "complete" },
    { key: "template", label: "Policy", status: activeStep === "template" ? "incomplete" : "complete" },
    { key: "parameters", label: "Parameters", status: activeStep === "parameters" ? "incomplete" : "complete" },
    { key: "assumptions", label: "Validation", status: activeStep === "assumptions" ? "incomplete" : "complete" },
  ];
}
```

**Memos to compute internally:**
```tsx
// Inside ConfigurationScreen component body:

const configSteps = useMemo(() => getConfigSteps(activeStep), [activeStep]);

const selectedPopulation = useMemo(
  () => populations.find((p) => p.id === selectedPopulationId),
  [populations, selectedPopulationId],
);

const selectedTemplate = useMemo(
  () => templates.find((t) => t.id === selectedTemplateId),
  [templates, selectedTemplateId],
);

const filteredParameters = useMemo(() => {
  if (!selectedTemplate) return parameters;
  return parameters.filter((p) => selectedTemplate.parameterGroups.includes(p.group));
}, [selectedTemplate, parameters]);

const isLastStep = activeStep === STEP_ORDER[STEP_ORDER.length - 1];
```

**Step navigation handler:**
```tsx
const nextStep = () => {
  const currentIndex = STEP_ORDER.indexOf(activeStep);
  if (currentIndex >= STEP_ORDER.length - 1) {
    onGoToSimulation();
    return;
  }
  const next = STEP_ORDER[currentIndex + 1] ?? activeStep;
  onStepSelect(next);
};
```

### App.tsx After Extraction

The `viewMode === "configuration"` block shrinks to:
```tsx
{viewMode === "configuration" ? (
  <ConfigurationScreen
    activeStep={activeStep}
    onStepSelect={setActiveStep}
    populations={populations}
    selectedPopulationId={selectedPopulationId}
    onSelectPopulation={setSelectedPopulationId}
    templates={templates}
    selectedTemplateId={selectedTemplateId}
    onSelectTemplate={selectTemplate}
    onTemplatesChanged={refetchTemplates}
    parameters={parameters}
    parameterValues={parameterValues}
    onParameterChange={setParameterValue}
    onGoToSimulation={() => setViewMode("run")}
  />
) : null}
```

**Removals from App.tsx:**
- `STEP_ORDER` constant (line 39-44) — REMOVE
- `getConfigSteps` function (line 63-70) — REMOVE
- `configSteps` memo (line 95) — REMOVE
- `filteredParameters` memo (lines 106-109) — REMOVE (only used by config steps, now internal to ConfigurationScreen)
- `isLastStep` derivation — REMOVE
- `nextStep` function (lines 161-168) — REMOVE
- Imports: `ModelConfigStepper` component, `ConfigStep` type, `PopulationSelectionScreen`, `TemplateSelectionScreen`, `ParameterEditingScreen`, `AssumptionsReviewScreen` — REMOVE from App.tsx; ADD `import type { ConfigStepKey }` from `ModelConfigStepper`; update `activeStep` state type from `ConfigStep["key"]` to `ConfigStepKey`

**Keep in App.tsx:**
- `activeStep`/`setActiveStep` state — right panel needs it
- `selectedPopulation` memo — right panel uses `selectedPopulation?.name`
- `selectedTemplate` memo — right panel uses `selectedTemplate?.name`; run view uses `selectedTemplate?.name ?? "selected policy"`

### ComparisonDashboardScreen Extraction Map

| Source (lines in ComparisonDashboardScreen.tsx) | Target File |
|------------------------------------------------|-------------|
| Types: `ViewMode`, `ActiveTab`, `DetailTarget` (38-46) | `comparison-helpers.ts` |
| Constants: `MAX_RUNS`, `METHODOLOGY_DESCRIPTIONS` (52-61) | `comparison-helpers.ts` |
| Helpers: `runLabel`, `statusVariant`, `buildSeries`, `escapeCsvField`, `exportComparisonCsv` (67-129) | `comparison-helpers.ts` |
| `RunSelectorProps` + `RunSelector` (135-239) | `RunSelector.tsx` |
| `FiscalTab` (244-332) | `FiscalTab.tsx` |
| `WelfareTab` (337-459) | `WelfareTab.tsx` |
| `DetailPanel` (465-524) | `DetailPanel.tsx` |
| `ComparisonDashboardScreen` (528-789) | Stays — imports from above |

**comparison-helpers.ts imports:**
```ts
import type { ResultListItem, PortfolioComparisonResponse } from "@/api/types";
import { CHART_COLORS } from "@/components/simulation/MultiRunChart";
import type { SeriesSpec } from "@/components/simulation/MultiRunChart";
```

**RunSelector.tsx imports:**
```tsx
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CHART_COLORS } from "@/components/simulation/MultiRunChart";
import type { ResultListItem } from "@/api/types";
import { MAX_RUNS, runLabel, statusVariant } from "./comparison-helpers";
```

**FiscalTab.tsx imports:**
```tsx
import { columnarToRows } from "@/components/simulation/MultiRunChart";
import type { ComparisonData } from "@/api/types";
import type { ViewMode } from "./comparison-helpers";
```

**WelfareTab.tsx imports:**
```tsx
import { columnarToRows } from "@/components/simulation/MultiRunChart";
import type { ComparisonData } from "@/api/types";
import type { ViewMode } from "./comparison-helpers";
```

**DetailPanel.tsx imports:**
```tsx
import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { DetailTarget } from "./comparison-helpers";
```

**Barrel export (`index.ts`):**
```tsx
export { RunSelector } from "./RunSelector";
export type { RunSelectorProps } from "./RunSelector";
export { FiscalTab } from "./FiscalTab";
export { WelfareTab } from "./WelfareTab";
export { DetailPanel } from "./DetailPanel";
export {
  type ViewMode,
  type ActiveTab,
  type DetailTarget,
  MAX_RUNS,
  METHODOLOGY_DESCRIPTIONS,
  runLabel,
  statusVariant,
  buildSeries,
  escapeCsvField,
  exportComparisonCsv,
} from "./comparison-helpers";
```

**Updated ComparisonDashboardScreen imports:**
```tsx
import { RunSelector } from "@/components/comparison/RunSelector";
import { FiscalTab } from "@/components/comparison/FiscalTab";
import { WelfareTab } from "@/components/comparison/WelfareTab";
import { DetailPanel } from "@/components/comparison/DetailPanel";
import {
  type ViewMode,
  type ActiveTab,
  type DetailTarget,
  buildSeries,
  exportComparisonCsv,
} from "@/components/comparison/comparison-helpers";
```

### ConfigurationScreen Tests — Patterns

Follow existing screen test patterns (see `ResultsOverviewScreen.test.tsx`, `ComparisonDashboardScreen.test.tsx`):

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

// Mock the template API (TemplateSelectionScreen calls createCustomTemplate)
vi.mock("@/api/templates", () => ({
  createCustomTemplate: vi.fn(),
}));

import { ConfigurationScreen } from "@/components/screens/ConfigurationScreen";
import type { Parameter, Population, Template } from "@/data/mock-data";

function mockPopulations(): Population[] {
  return [
    { id: "pop-1", name: "France 2024", households: 30000000, source: "INSEE", year: 2024 },
  ];
}

function mockTemplates(): Template[] {
  return [
    {
      id: "tpl-1", name: "Carbon Tax", type: "carbon_tax",
      parameterCount: 3, description: "Standard carbon tax",
      parameterGroups: ["carbon"], is_custom: false,
    },
  ];
}

function mockParameters(): Parameter[] {
  return [
    { id: "p1", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tCO2", group: "carbon", type: "slider", min: 0, max: 200 },
    { id: "p2", label: "Other Param", value: 10, baseline: 10, unit: "%", group: "other", type: "number" },
  ];
}

const defaultProps = {
  activeStep: "population" as const,
  onStepSelect: vi.fn(),
  populations: mockPopulations(),
  selectedPopulationId: "pop-1",
  onSelectPopulation: vi.fn(),
  templates: mockTemplates(),
  selectedTemplateId: "tpl-1",
  onSelectTemplate: vi.fn(),
  onTemplatesChanged: vi.fn(),
  parameters: mockParameters(),
  parameterValues: { p1: 44, p2: 10 },
  onParameterChange: vi.fn(),
  onGoToSimulation: vi.fn(),
};
```

**Key test: parameter filtering by template** — When `selectedTemplateId` matches a template with `parameterGroups: ["carbon"]`, only parameters with `group: "carbon"` should be rendered in the Parameters step. The "Other Param" (`group: "other"`) should NOT appear. This verifies the internal `filteredParameters` memo works correctly.

**Key test: step advancement** — Clicking "Next Step" when `activeStep="population"` should call `onStepSelect("template")`. When `activeStep="assumptions"` (last step), the button should read "Go to Simulation" and call `onGoToSimulation` instead.

### What NOT to Change

- **`frontend/src/components/simulation/ModelConfigStepper.tsx`** — Stays at its current location; ConfigurationScreen imports it
- **`PopulationSelectionScreen.tsx`, `TemplateSelectionScreen.tsx`, `ParameterEditingScreen.tsx`, `AssumptionsReviewScreen.tsx`** — Stay at current locations; ConfigurationScreen imports them
- **`frontend/src/components/simulation/MultiRunChart.tsx`** — Stays; comparison sub-components import `columnarToRows` and `CHART_COLORS` from it
- **`frontend/src/components/simulation/CrossMetricPanel.tsx`** — Stays; ComparisonDashboardScreen still imports it directly
- **`frontend/src/components/simulation/ErrorAlert.tsx`** — Stays; ComparisonDashboardScreen still imports it directly
- **Backend files** — Frontend-only story
- **`frontend/src/contexts/AppContext.tsx`** — No state changes needed
- **`frontend/src/data/mock-data.ts`** — No changes
- **Test files for ComparisonDashboardScreen** — Existing tests (`ComparisonDashboardScreen.test.tsx`, 297 lines, 16 tests) should pass without modification since ComparisonDashboardScreen's public API (props, rendered output) does not change
- **`analyst-journey.test.tsx`** — Should pass without modification since the UI output is unchanged
- **`SimulationRunnerScreen.tsx`** — Not in scope for this story (337 lines; less dense, sub-views share extensive local state making extraction complex for the benefit)
- **`PortfolioDesignerScreen.tsx`** — Not in scope (724 lines but complexity is nested form state, not clearly separable sub-components)

### Right Panel activeStep Dependency

The right panel in App.tsx (~line 506) displays the active config step:
```tsx
{viewMode === "configuration" ? (
  <Badge variant="violet">{activeStep}</Badge>
) : null}
```
This is why `activeStep` state must remain in App.tsx. ConfigurationScreen receives it as a prop and calls `onStepSelect` to update it. This is the same pattern as ResultsOverviewScreen receiving `runResult` as a prop.

### Imports to Verify After Extraction

After removing configuration-related imports from App.tsx, verify these are still needed:
- `useMemo` — YES (still used for `selectedPopulation`, `selectedTemplate`, `selectedScenario`)
- `useState` — YES (still used for `activeStep`, `viewMode`, `leftCollapsed`, etc.)
- `Button` — YES (still used in header nav buttons, run view)
- `SummaryStatCard` — YES (still used in run view, line ~338)
- `mockSummaryStats` — YES (still used in run view, line ~338)
- `Badge` — YES (still used in right panel)
- `Separator` — YES (still used in left panel)

### Project Structure Notes

**New folder:**
- `frontend/src/components/comparison/` — domain-specific folder for comparison sub-components (RunSelector, FiscalTab, WelfareTab, DetailPanel, helpers)

This follows the established pattern of domain folders (`simulation/`, `layout/`, `auth/`). The `comparison/` folder groups all sub-components that were previously inlined in ComparisonDashboardScreen. `MultiRunChart` and `CrossMetricPanel` stay in `simulation/` because they are reusable visualization components, not comparison-specific orchestration components.

**New files (8):**
- `frontend/src/components/screens/ConfigurationScreen.tsx`
- `frontend/src/components/screens/__tests__/ConfigurationScreen.test.tsx`
- `frontend/src/components/comparison/RunSelector.tsx`
- `frontend/src/components/comparison/FiscalTab.tsx`
- `frontend/src/components/comparison/WelfareTab.tsx`
- `frontend/src/components/comparison/DetailPanel.tsx`
- `frontend/src/components/comparison/comparison-helpers.ts`
- `frontend/src/components/comparison/index.ts`

**Files to modify (2):**
- `frontend/src/App.tsx` — replace inline config JSX with `<ConfigurationScreen>`, remove moved code/imports
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — replace inline sub-components with imports from `@/components/comparison`

### References

- [Source: `_bmad-output/implementation-artifacts/epic-18-ux-polish-and-aesthetic-overhaul.md` — Story 18.5: "Consolidate configuration flow and split dense screens", 5SP, P1]
- [Source: `_bmad-output/planning-artifacts/epics.md` — BDD: "Given dense configuration screens, when viewed, then content is split into logical sections or steps"]
- [Source: `_bmad-output/planning-artifacts/epics.md` — BDD: "Given the configuration flow, when navigating between sections, then state is preserved"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Lines 684-688: "Progressive steps, not a wizard — steps can be jumped between freely"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Lines 63-75: "Configuration is complex but navigable — Model setup involves real analytical decisions"]
- [Source: `frontend/src/App.tsx:39-44` — STEP_ORDER constant to move]
- [Source: `frontend/src/App.tsx:63-70` — getConfigSteps function to move]
- [Source: `frontend/src/App.tsx:95-109` — configSteps, selectedPopulation, selectedTemplate, filteredParameters memos]
- [Source: `frontend/src/App.tsx:161-168` — nextStep function to move]
- [Source: `frontend/src/App.tsx:281-335` — Inline configuration JSX to replace with ConfigurationScreen]
- [Source: `frontend/src/App.tsx:502-510` — Right panel activeStep badge (reason for keeping state in App.tsx)]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:135-239` — RunSelector sub-component to extract]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:244-332` — FiscalTab sub-component to extract]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:337-459` — WelfareTab sub-component to extract]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:465-524` — DetailPanel sub-component to extract]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:67-129` — Helper functions to extract]
- [Source: `frontend/src/components/screens/__tests__/ComparisonDashboardScreen.test.tsx` — 297 lines, 16 tests; must pass unchanged after extraction]
- [Source: `frontend/src/components/screens/ResultsOverviewScreen.tsx` — Screen component extraction pattern to follow (Story 18.4)]
- [Source: `_bmad-output/implementation-artifacts/18-4-restructure-results-view.md` — Predecessor story pattern: screen extraction from App.tsx]
- [Source: `_bmad-output/implementation-artifacts/18-3-extract-shared-components.md` — Story 18.3 done: shared components available (dependency satisfied)]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes

All 5 tasks completed. 320 tests pass (311 pre-existing + 9 new ConfigurationScreen tests). TypeScript: 0 errors. ESLint: 0 errors (4 pre-existing fast-refresh warnings unchanged).

- ConfigurationScreen extracted from App.tsx inline JSX (lines 281-335); STEP_ORDER, getConfigSteps, configSteps memo, filteredParameters memo, isLastStep, nextStep all moved; App.tsx simplified.
- ComparisonDashboardScreen split from 789 lines into 5 new files under `components/comparison/` plus barrel `index.ts`; orchestration-only remainder is ~265 lines.
- 9 ConfigurationScreen tests written covering all AC-5 scenarios.

### File List

**New files (8):**
- `frontend/src/components/screens/ConfigurationScreen.tsx`
- `frontend/src/components/screens/__tests__/ConfigurationScreen.test.tsx`
- `frontend/src/components/comparison/RunSelector.tsx`
- `frontend/src/components/comparison/FiscalTab.tsx`
- `frontend/src/components/comparison/WelfareTab.tsx`
- `frontend/src/components/comparison/DetailPanel.tsx`
- `frontend/src/components/comparison/comparison-helpers.ts`
- `frontend/src/components/comparison/index.ts`

**Modified files (2):**
- `frontend/src/App.tsx` — replace inline config JSX with `<ConfigurationScreen>`, remove moved code/imports
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — replace inline sub-components with imports from `@/components/comparison`
