
# Story 18.3: Extract Shared Components (WorkbenchStepper, ErrorAlert, SelectionGrid)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer maintaining the ReformLab frontend,
I want duplicated UI patterns extracted into shared components,
so that visual consistency is enforced by code reuse rather than manual discipline, and future changes (stories 18.5-18.8) propagate automatically.

## Acceptance Criteria

1. **AC-1: Shared WorkbenchStepper** — Given `DataFusionWorkbench.tsx` (lines 48-80) and `PortfolioDesignerScreen.tsx` (lines 49-81), which each define an identical local `WorkbenchStepper` (~30 lines), when this story is complete, then both screens import a single shared `WorkbenchStepper` from `components/simulation/WorkbenchStepper.tsx`. The shared component accepts `steps: { label: string; key: string }[]`, `activeStep: string`, `onStepSelect: (key: string) => void`, and optional `ariaLabel?: string`. The existing `ModelConfigStepper` remains separate — it uses a 4-column grid layout with status icons (`CheckCircle2`/`CircleAlert`/`Circle`), which is a different visual pattern.

2. **AC-2: ErrorAlert component** — Given error displays in `BehavioralDecisionViewerScreen` (lines 259-268), `SimulationRunnerScreen` (lines 284-302), `ComparisonDashboardScreen` (lines 666-679), and `PopulationGenerationProgress` (lines 60-89), which all render `{ what, why, fix }` error tuples with `AlertCircle`/`XCircle` icons and red-50 backgrounds, when this story is complete, then all use a shared `ErrorAlert` component from `components/simulation/ErrorAlert.tsx`. Props: `what: string`, `why: string`, `fix: string`, optional `className?: string`. The `DataFusionWorkbench` itself does NOT render errors inline (it uses toast + delegates to `PopulationGenerationProgress`), so only 4 files need replacement.

3. **AC-3: SelectionGrid component** — Given `PopulationSelectionScreen` (lines 16-41) and `TemplateSelectionScreen` (lines 189-220), which have 95% identical card-grid patterns (selection highlight with `border-blue-500 bg-blue-50`, same `grid gap-2 xl:grid-cols-2` layout, same `<button type="button" className="text-left">` wrapper), when this story is complete, then both use a shared `SelectionGrid<T>` component from `components/simulation/SelectionGrid.tsx` that accepts `items: T[]`, `selectedId: string | null`, `onSelect: (id: string) => void`, `getId: (item: T) => string`, and `renderCard: (item: T, selected: boolean) => ReactNode`.

4. **AC-4: No behavior changes** — Given all affected screens, when rendered after extraction, then the visual output and interaction behavior is identical to before. All existing tests (259/259) pass without modification. `npm run typecheck` and `npm run lint` report zero errors.

5. **AC-5: Dead code removed** — Given the extraction, when complete, then the inline `WorkbenchStepper` definitions in `DataFusionWorkbench.tsx` and `PortfolioDesignerScreen.tsx` are deleted. The old `ComparisonView.tsx` (Phase 1 prototype, confirmed unused — `App.tsx` comment: "kept but no longer imported") is deleted. The unused step components (`ParametersStep.tsx`, `PopulationStep.tsx`, `TemplateStep.tsx`) are deleted if confirmed unused via grep. `ReviewStep.tsx` is kept — it is imported and used per embedded source code.

## Tasks / Subtasks

- [ ] Task 1: Extract WorkbenchStepper (AC: 1)
  - [ ] 1.1: Create `frontend/src/components/simulation/WorkbenchStepper.tsx` with generic step interface (see Dev Notes for exact props and implementation)
  - [ ] 1.2: Update `DataFusionWorkbench.tsx` — delete local `WorkbenchStepper` function (lines 48-80) and local `STEPS` type, import shared component, pass steps array and `ariaLabel="Workbench steps"`
  - [ ] 1.3: Update `PortfolioDesignerScreen.tsx` — delete local `WorkbenchStepper` function (lines 49-81) and local `STEPS` type, import shared component, pass steps array and `ariaLabel="Designer steps"`
  - [ ] 1.4: Document decision: `ModelConfigStepper` remains separate (grid layout + status icons vs flex scroll + plain text)

- [ ] Task 2: Extract ErrorAlert (AC: 2)
  - [ ] 2.1: Create `frontend/src/components/simulation/ErrorAlert.tsx` — renders `AlertCircle` icon + what/why/fix fields with consistent styling (see Dev Notes for canonical pattern)
  - [ ] 2.2: Replace inline error render in `BehavioralDecisionViewerScreen.tsx` (lines 259-268)
  - [ ] 2.3: Replace inline error render in `SimulationRunnerScreen.tsx` (lines 284-302 — the progress sub-view error state)
  - [ ] 2.4: Replace inline error render in `ComparisonDashboardScreen.tsx` (lines 666-679)
  - [ ] 2.5: Replace inline error render in `PopulationGenerationProgress.tsx` (lines 60-89 — the error branch)

- [ ] Task 3: Extract SelectionGrid (AC: 3)
  - [ ] 3.1: Create `frontend/src/components/simulation/SelectionGrid.tsx` — generic grid with selection highlight (see Dev Notes for exact interface)
  - [ ] 3.2: Refactor `PopulationSelectionScreen.tsx` (lines 16-41) to use SelectionGrid, passing `renderCard` with Card/CardHeader/CardContent
  - [ ] 3.3: Refactor `TemplateSelectionScreen.tsx` (lines 189-220) to use SelectionGrid, preserving the custom badge and existing Card structure

- [ ] Task 4: Dead code cleanup (AC: 5)
  - [ ] 4.1: Grep for imports of `ComparisonView` across codebase, confirm zero, delete `frontend/src/components/simulation/ComparisonView.tsx`
  - [ ] 4.2: Grep for imports of `ParametersStep`, `PopulationStep`, `TemplateStep` — confirm zero imports, delete files
  - [ ] 4.3: Verify `ReviewStep.tsx` is actually used — `ReviewStep` appears in the embedded source code context, so it is likely still imported; do NOT delete without confirming it has zero imports

- [ ] Task 5: Tests and verification (AC: 4)
  - [ ] 5.1: Add unit tests for `WorkbenchStepper` — renders steps, highlights active, calls onStepSelect on click
  - [ ] 5.2: Add unit tests for `ErrorAlert` — renders what/why/fix text, has role="alert", renders AlertCircle icon
  - [ ] 5.3: Add unit tests for `SelectionGrid` — renders items, highlights selected, calls onSelect on click
  - [ ] 5.4: Run `npm test` — all tests pass (expect 259+ total, 0 failures)
  - [ ] 5.5: Run `npm run typecheck` — 0 errors
  - [ ] 5.6: Run `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)

## Dev Notes

### WorkbenchStepper — Canonical Implementation

Both existing implementations are **byte-for-byte identical** in structure (only `aria-label` differs). The shared component should match this exact pattern:

```tsx
// frontend/src/components/simulation/WorkbenchStepper.tsx
import { cn } from "@/lib/utils";

export interface StepDef {
  key: string;
  label: string;
}

interface WorkbenchStepperProps {
  steps: StepDef[];
  activeStep: string;
  onStepSelect: (key: string) => void;
  ariaLabel?: string;
}

export function WorkbenchStepper({
  steps,
  activeStep,
  onStepSelect,
  ariaLabel = "Steps",
}: WorkbenchStepperProps) {
  return (
    <nav aria-label={ariaLabel} className="border-b border-slate-200 bg-white p-3">
      <ol className="flex gap-1 overflow-x-auto">
        {steps.map((step) => {
          const isActive = step.key === activeStep;
          return (
            <li key={step.key} className="shrink-0">
              <button
                type="button"
                onClick={() => onStepSelect(step.key)}
                className={cn(
                  "border px-3 py-1.5 text-xs",
                  isActive
                    ? "border-blue-500 bg-blue-50 text-blue-700 font-medium"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                )}
              >
                {step.label}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
```

**Caller change pattern (DataFusionWorkbench):**
```tsx
// Before: local STEPS array with typed key
type WorkbenchStep = "sources" | "overlap" | "method" | "generate" | "preview";
const STEPS: Array<{ key: WorkbenchStep; label: string }> = [...];

// After: keep the local STEPS const (for type safety in the screen), import WorkbenchStepper
import { WorkbenchStepper } from "@/components/simulation/WorkbenchStepper";
// Delete the local WorkbenchStepper function definition
// Usage stays the same: <WorkbenchStepper activeStep={activeStep} steps={STEPS} onStepSelect={setActiveStep} ariaLabel="Workbench steps" />
```

### ErrorAlert — Canonical Implementation

Four distinct inline error patterns exist. They differ slightly in icon size, text size, and field labeling. **Normalize to the most common pattern** (ComparisonDashboardScreen style with labeled fields):

```tsx
// frontend/src/components/simulation/ErrorAlert.tsx
import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorAlertProps {
  what: string;
  why: string;
  fix: string;
  className?: string;
}

export function ErrorAlert({ what, why, fix, className }: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3",
        className,
      )}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
      <div className="space-y-0.5 text-xs">
        <p className="font-semibold text-red-800">{what}</p>
        <p className="text-red-700">{why}</p>
        <p className="text-red-600">{fix}</p>
      </div>
    </div>
  );
}
```

**Current error patterns (4 screens) — what changes:**

| File | Lines | Current pattern | Change |
|------|-------|-----------------|--------|
| `BehavioralDecisionViewerScreen.tsx` | 259-268 | `AlertCircle size={16}`, `gap-3 p-4`, `text-sm`/`text-xs` | Replace with `<ErrorAlert what={error.what} why={error.why} fix={error.fix} className="mb-5" />` |
| `SimulationRunnerScreen.tsx` | ~286-300 | `AlertCircle h-5 w-5`, wraps entire section, includes back button | Replace error `<section>` with `<ErrorAlert />` + keep the back button below it |
| `ComparisonDashboardScreen.tsx` | ~666-679 | `AlertCircle h-4 w-4`, closest to canonical | Replace with `<ErrorAlert />` |
| `PopulationGenerationProgress.tsx` | 60-89 | `XCircle h-5 w-5`, "What:/Why:/Fix:" labeled format, `<section>` | Replace error branch with `<ErrorAlert />` wrapped in a section |

**Important:** The `SimulationRunnerScreen` error display includes a "Back to Configuration" button *after* the error. Keep that button outside the `<ErrorAlert />` — don't add button/action support to the component (YAGNI).

**Important:** `PopulationGenerationProgress` also has a plain `error: string | null` prop for non-structured errors. Keep that as a simple `<p>` fallback — `ErrorAlert` is only for the structured `{what, why, fix}` tuple.

### SelectionGrid — Canonical Implementation

```tsx
// frontend/src/components/simulation/SelectionGrid.tsx
import type { ReactNode } from "react";

interface SelectionGridProps<T> {
  items: T[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  getId: (item: T) => string;
  renderCard: (item: T, selected: boolean) => ReactNode;
  className?: string;
}

export function SelectionGrid<T>({
  items,
  selectedId,
  onSelect,
  getId,
  renderCard,
  className,
}: SelectionGridProps<T>) {
  return (
    <section className={className ?? "grid gap-2 xl:grid-cols-2"}>
      {items.map((item) => {
        const id = getId(item);
        const selected = id === selectedId;
        return (
          <button
            type="button"
            key={id}
            onClick={() => onSelect(id)}
            className="text-left"
          >
            {renderCard(item, selected)}
          </button>
        );
      })}
    </section>
  );
}
```

**Caller change pattern (PopulationSelectionScreen):**
```tsx
// Before: inline map with button + Card
<section className="grid gap-2 xl:grid-cols-2">
  {populations.map((population) => {
    const selected = population.id === selectedPopulationId;
    return (
      <button type="button" key={population.id} onClick={...} className="text-left">
        <Card className={selected ? "border-blue-500 bg-blue-50" : ...}>...</Card>
      </button>
    );
  })}
</section>

// After:
<SelectionGrid
  items={populations}
  selectedId={selectedPopulationId}
  onSelect={onSelectPopulation}
  getId={(p) => p.id}
  renderCard={(population, selected) => (
    <Card className={selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white"}>
      <CardHeader><CardTitle>{population.name}</CardTitle></CardHeader>
      <CardContent>...</CardContent>
    </Card>
  )}
/>
```

### What NOT to Extract

- **`DataSourceBrowser.tsx` / `PortfolioTemplateBrowser.tsx`** — These have multi-select (checkbox) grids with search/filter inputs and grouped-by-provider/type sections. They are NOT simple single-select card grids. Do NOT try to make `SelectionGrid` handle multi-select — that would over-engineer the component. Leave these as-is.
- **`ModelConfigStepper`** — Grid layout with status icons, fundamentally different from the flex scroll WorkbenchStepper. Leave as-is.
- **`MergeMethodSelector`** — Single-column radio-select layout, different visual pattern. Leave as-is.
- **`ConflictList`** in `PortfolioDesignerScreen.tsx` — Only used once, no duplication. Leave as-is.
- **Dialog/Modal patterns** — `PortfolioDesignerScreen` and `TemplateSelectionScreen` both have inline modal dialogs. These could use the shadcn `Dialog` component but that's a separate refactor, not in scope for this story.

### Dead Code Verification Checklist

| File | Expected result | Action |
|------|----------------|--------|
| `ComparisonView.tsx` | 0 imports — App.tsx comment confirms unused | Delete |
| `ParametersStep.tsx` | 0 imports — default export, not used in any screen | Delete if confirmed |
| `PopulationStep.tsx` | 0 imports — default export, not used in any screen | Delete if confirmed |
| `TemplateStep.tsx` | 0 imports — default export, not used in any screen | Delete if confirmed |
| `ReviewStep.tsx` | **Check carefully** — may still be imported somewhere | Do NOT delete unless grep confirms zero imports |

**Verification command:**
```bash
grep -r "ComparisonView\|ParametersStep\|PopulationStep\|TemplateStep\|ReviewStep" frontend/src/ --include="*.tsx" --include="*.ts" -l
```

### ErrorState Type Consolidation

The `ErrorState` interface `{ what: string; why: string; fix: string }` is defined identically in 3+ files:
- `ComparisonDashboardScreen.tsx` (line ~23)
- `SimulationRunnerScreen.tsx` (line ~27)
- `BehavioralDecisionViewerScreen.tsx` (line ~31)

Export it from `ErrorAlert.tsx`:
```tsx
export interface ErrorState {
  what: string;
  why: string;
  fix: string;
}
```

Then import it in screens that maintain error state. This is a low-risk consolidation that reduces duplication further.

Also, `extractErrorDetail()` in `BehavioralDecisionViewerScreen.tsx` (lines 68-80) is a useful helper for converting caught errors to `ErrorState`. Consider exporting it from `ErrorAlert.tsx` as well — or leave it in `BehavioralDecisionViewerScreen` if it's the only consumer. Check before deciding.

### Test File Locations

New test files to create:
- `frontend/src/components/simulation/__tests__/WorkbenchStepper.test.tsx`
- `frontend/src/components/simulation/__tests__/ErrorAlert.test.tsx`
- `frontend/src/components/simulation/__tests__/SelectionGrid.test.tsx`

Existing test files that must pass unchanged:
- `frontend/src/components/screens/__tests__/DataFusionWorkbench.test.tsx` — tests stepper navigation
- `frontend/src/components/screens/__tests__/PortfolioDesignerScreen.test.tsx` — tests stepper tabs
- `frontend/src/components/screens/__tests__/ComparisonDashboardScreen.test.tsx` — tests error rendering
- `frontend/src/components/screens/__tests__/SimulationRunnerScreen.test.tsx` — tests error state
- `frontend/src/components/screens/__tests__/BehavioralDecisionViewerScreen.test.tsx` — tests error state

### Project Structure Notes

- New shared components go in `frontend/src/components/simulation/` (same level as `ModelConfigStepper.tsx`, `RunProgressBar.tsx`, etc.)
- Tests go in `frontend/src/components/simulation/__tests__/` (same pattern as `ModelConfigStepper.test.tsx`)
- Alignment with unified project structure: all simulation-domain shared components live in `components/simulation/`; UI primitives in `components/ui/`
- No new `components/ui/` files — `ErrorAlert`, `WorkbenchStepper`, `SelectionGrid` are domain-level, not UI primitives
- Tailwind v4 via `@tailwindcss/vite` plugin; no config file changes needed
- React 19: ref as regular prop (no forwardRef needed)

### Files to Modify (Complete List)

**New files (3):**
- `frontend/src/components/simulation/WorkbenchStepper.tsx`
- `frontend/src/components/simulation/ErrorAlert.tsx`
- `frontend/src/components/simulation/SelectionGrid.tsx`

**New test files (3):**
- `frontend/src/components/simulation/__tests__/WorkbenchStepper.test.tsx`
- `frontend/src/components/simulation/__tests__/ErrorAlert.test.tsx`
- `frontend/src/components/simulation/__tests__/SelectionGrid.test.tsx`

**Files to modify (6):**
- `frontend/src/components/screens/DataFusionWorkbench.tsx` — delete local WorkbenchStepper, import shared
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` — delete local WorkbenchStepper, import shared
- `frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx` — replace inline error with ErrorAlert
- `frontend/src/components/screens/SimulationRunnerScreen.tsx` — replace inline error with ErrorAlert
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — replace inline error with ErrorAlert
- `frontend/src/components/simulation/PopulationGenerationProgress.tsx` — replace error branch with ErrorAlert

**Files to modify (2 — SelectionGrid consumers):**
- `frontend/src/components/screens/PopulationSelectionScreen.tsx` — refactor to use SelectionGrid
- `frontend/src/components/screens/TemplateSelectionScreen.tsx` — refactor grid section to use SelectionGrid

**Files to delete (3-5):**
- `frontend/src/components/simulation/ComparisonView.tsx` — confirmed unused
- `frontend/src/components/simulation/ParametersStep.tsx` — likely unused (verify first)
- `frontend/src/components/simulation/PopulationStep.tsx` — likely unused (verify first)
- `frontend/src/components/simulation/TemplateStep.tsx` — likely unused (verify first)
- `frontend/src/components/simulation/ReviewStep.tsx` — **only if confirmed unused** (it appears in embedded context, so likely NOT dead)

### Files NOT to Modify

- `ModelConfigStepper.tsx` — different visual pattern, leave as-is
- `DataSourceBrowser.tsx` — multi-select with search, different pattern
- `PortfolioTemplateBrowser.tsx` — multi-select with search, different pattern
- `MergeMethodSelector.tsx` — radio single-select block layout, different pattern
- `App.tsx` — no changes needed (imports screens, doesn't import extracted components directly)
- Any `components/ui/` files — no changes to shadcn primitives
- Backend files — this is a frontend-only story
- Test files — existing tests should pass without modification (only new test files added)

### References

- [Source: `_bmad-output/implementation-artifacts/epic-18-ux-polish-and-aesthetic-overhaul.md` — Epic exit criteria: "All 9 screens use shared components (no duplicated WorkbenchStepper, no inline error displays)"]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 18.3 BDD: "Given WorkbenchStepper variants across screens, when refactored, then a single shared component is used everywhere"]
- [Source: `frontend/src/components/screens/DataFusionWorkbench.tsx:48-80` — First WorkbenchStepper definition]
- [Source: `frontend/src/components/screens/PortfolioDesignerScreen.tsx:49-81` — Second WorkbenchStepper definition (identical)]
- [Source: `frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx:259-268` — Error display pattern A]
- [Source: `frontend/src/components/screens/SimulationRunnerScreen.tsx:284-302` — Error display pattern B]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:666-679` — Error display pattern C]
- [Source: `frontend/src/components/simulation/PopulationGenerationProgress.tsx:60-89` — Error display pattern D]
- [Source: `frontend/src/components/screens/PopulationSelectionScreen.tsx:16-41` — SelectionGrid pattern A]
- [Source: `frontend/src/components/screens/TemplateSelectionScreen.tsx:189-220` — SelectionGrid pattern B]
- [Source: `frontend/src/components/simulation/ModelConfigStepper.tsx` — Existing stepper (different pattern, keep separate)]
- [Source: `_bmad-output/implementation-artifacts/18-2-visual-polish-pass.md` — Story 18.2 done: rounded-lg + shadow-sm on containers, 259 tests passing]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes

### File List

