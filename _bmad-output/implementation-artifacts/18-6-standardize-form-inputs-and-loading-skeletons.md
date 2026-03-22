
# Story 18.6: Standardize Form Inputs and Add Loading Skeletons

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst using the ReformLab workspace,
I want all form inputs to use consistent styled components and loading states to show skeleton placeholders instead of plain text,
so that the interface feels polished and cohesive, and I always know when content is loading.

## Acceptance Criteria

1. **AC-1: Number inputs standardized** — Given the 3 raw `<input type="number">` elements in `SimulationRunnerScreen.tsx` (lines 209, 220, 231 — start year, end year, seed), when rendered, then they use the `<Input>` component from `@/components/ui/input` with `type="number"` and consistent styling (inheriting the component's `rounded-md border-slate-300 focus:border-blue-500` classes). The compact sizing (`w-24 text-xs font-mono`) is applied via the `className` prop override.

2. **AC-2: Select elements standardized** — Given the 2 raw `<select>` elements in `PortfolioDesignerScreen.tsx` (line 434, conflict resolution strategy) and `TemplateSelectionScreen.tsx` (line 150, parameter type picker), when rendered, then they use the `<Select>` component from `@/components/ui/select`. Children `<option>` elements remain native HTML. The `Select` component receives `rounded-md` in its base classes (currently missing, unlike `Input`).

3. **AC-3: Checkbox component created** — Given that no `Checkbox` ui component exists, when this story is complete, then a `Checkbox` component exists at `frontend/src/components/ui/checkbox.tsx` as a thin wrapper around `<input type="checkbox">` (following the same pattern as `Input` and `Select` — no Radix dependency). The functional checkbox in `RunSelector.tsx` (line 53) is replaced with `<Checkbox>`.

4. **AC-4: Skeleton component created** — Given that no `Skeleton` ui component exists, when this story is complete, then a `Skeleton` component exists at `frontend/src/components/ui/skeleton.tsx` using the standard `animate-pulse rounded-md bg-slate-200` pattern (no additional dependencies). The component accepts `className` for sizing.

5. **AC-5: Loading text replaced with skeletons** — Given the 3 locations that show plain "Loading..." text during async operations, when data is being fetched, then skeleton placeholders are shown instead:
   - `ComparisonDashboardScreen.tsx` (line 188): "Loading comparison data…" → 3 skeleton bars inside a card
   - `ResultsOverviewScreen.tsx` (line 280): "Loading detail..." → 4 skeleton rows matching the detail table layout
   - `VariableOverlapView.tsx` (line 90): "Loading column details..." → 2 skeleton rows matching column list layout

6. **AC-6: No regressions** — Given all changes, when tests run, then:
   - All pre-existing 320 tests pass (0 failures)
   - `npm run typecheck` reports 0 errors
   - `npm run lint` reports 0 errors (pre-existing fast-refresh warnings OK)

7. **AC-7: Skeleton component tests** — Given the new `Skeleton` component, when tested, then a test file at `frontend/src/components/ui/__tests__/skeleton.test.tsx` verifies: renders with default classes (`animate-pulse`, `bg-slate-200`), accepts custom `className`, renders as a `div` element.

## Tasks / Subtasks

- [ ] Task 1: Fix `Select` component and create `Checkbox` and `Skeleton` components (AC: 2, 3, 4)
  - [ ] 1.1: Update `frontend/src/components/ui/select.tsx` — add `rounded-md` to base classes to match `Input` component
  - [ ] 1.2: Create `frontend/src/components/ui/checkbox.tsx` — thin wrapper around `<input type="checkbox">` with consistent styling (`h-4 w-4 cursor-pointer rounded border border-slate-300 accent-blue-500 disabled:cursor-not-allowed disabled:opacity-50`)
  - [ ] 1.3: Create `frontend/src/components/ui/skeleton.tsx` — `div` with `animate-pulse rounded-md bg-slate-200`, accepts `className` for sizing

- [ ] Task 2: Standardize number inputs in SimulationRunnerScreen (AC: 1)
  - [ ] 2.1: Import `Input` from `@/components/ui/input` in `SimulationRunnerScreen.tsx`
  - [ ] 2.2: Replace raw `<input type="number">` at line 209 (start year) with `<Input type="number" className="w-24 text-xs font-mono" ... />`
  - [ ] 2.3: Replace raw `<input type="number">` at line 220 (end year) with `<Input type="number" className="w-24 text-xs font-mono" ... />`
  - [ ] 2.4: Replace raw `<input type="number">` at line 231 (seed) with `<Input type="number" className="w-24 text-xs font-mono" ... />`

- [ ] Task 3: Standardize select elements (AC: 2)
  - [ ] 3.1: Import `Select` from `@/components/ui/select` in `PortfolioDesignerScreen.tsx`; replace raw `<select>` at line 434 with `<Select>` keeping the same props and children `<option>` elements; remove bespoke classes (`border-slate-200 px-2 py-1.5 text-xs bg-white`)
  - [ ] 3.2: Import `Select` from `@/components/ui/select` in `TemplateSelectionScreen.tsx`; replace raw `<select>` at line 150 with `<Select>` keeping the same props and children `<option>` elements; remove bespoke classes (`h-9 rounded-md border border-input bg-transparent px-2 text-sm`); use `className="flex-shrink-0 w-auto"` for inline sizing

- [ ] Task 4: Standardize checkbox in RunSelector (AC: 3)
  - [ ] 4.1: Import `Checkbox` from `@/components/ui/checkbox` in `RunSelector.tsx`; replace raw `<input type="checkbox">` at line 53 with `<Checkbox>` keeping the same `checked`, `disabled`, `onChange`, `aria-label` props; remove bespoke classes (`h-3.5 w-3.5 cursor-pointer`)

- [ ] Task 5: Add loading skeletons (AC: 5)
  - [ ] 5.1: In `ComparisonDashboardScreen.tsx` (line 186-190), replace the "Loading comparison data…" text block with a skeleton card containing 3 horizontal bars (`<Skeleton className="h-4 w-full" />` etc.) inside the existing `rounded-lg border` container
  - [ ] 5.2: In `ResultsOverviewScreen.tsx` (line 280-281), replace "Loading detail..." text with 4 skeleton rows (`<Skeleton className="h-3 w-full" />` spaced with `space-y-2`) to approximate the detail table layout
  - [ ] 5.3: In `VariableOverlapView.tsx` (line 89-90), replace "Loading column details..." text with 2 skeleton rows to approximate the column list

- [ ] Task 6: Write Skeleton tests (AC: 7)
  - [ ] 6.1: Create `frontend/src/components/ui/__tests__/skeleton.test.tsx` with tests: renders with `animate-pulse` class, renders with `bg-slate-200` class, accepts and merges custom `className`, renders as a `div` element

- [ ] Task 7: Verify no regressions (AC: 6)
  - [ ] 7.1: Run `npm test` — all pre-existing tests pass; new tests pass
  - [ ] 7.2: Run `npm run typecheck` — 0 errors
  - [ ] 7.3: Run `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)

## Dev Notes

### New UI Components

**`Checkbox` component (`frontend/src/components/ui/checkbox.tsx`):**

```tsx
import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Checkbox({
  className,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type">) {
  return (
    <input
      type="checkbox"
      className={cn(
        "h-4 w-4 cursor-pointer rounded border border-slate-300 accent-blue-500 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
```

This follows the project's existing thin-wrapper pattern (same as `Input` and `Select`). No Radix dependency — consistent with the project's lightweight ui component approach.

**`Skeleton` component (`frontend/src/components/ui/skeleton.tsx`):**

```tsx
import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-slate-200", className)}
      {...props}
    />
  );
}
```

Standard shadcn/ui skeleton adapted for the project (uses `bg-slate-200` instead of `bg-accent` since the project uses direct Tailwind colors, not CSS variable theming).

### Select Component Fix

Add `rounded-md` to `Select` base classes to match `Input`:

```tsx
// Before:
"h-8 w-full border border-slate-300 bg-white px-2 text-sm text-slate-900 outline-none focus:border-blue-500"

// After:
"h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-sm text-slate-900 outline-none focus:border-blue-500"
```

### SimulationRunnerScreen — Input Replacement Pattern

Each raw input becomes:

```tsx
// Before:
<input
  type="number"
  value={startYear}
  min={2020}
  max={endYear - 1}
  onChange={(e) => setStartYear(Number(e.target.value))}
  className="w-24 border border-slate-200 px-1.5 py-0.5 text-xs font-mono"
  aria-label="Start year"
/>

// After:
<Input
  type="number"
  value={startYear}
  min={2020}
  max={endYear - 1}
  onChange={(e) => setStartYear(Number(e.target.value))}
  className="w-24 text-xs font-mono"
  aria-label="Start year"
/>
```

The `Input` component provides `border`, `rounded-md`, `border-slate-300`, `bg-white`, `px-2`, `focus:border-blue-500` from its base classes. The `className` override provides only the compact sizing (`w-24 text-xs font-mono`). Note: the `Input` base height is `h-8`; the raw inputs used `py-0.5` for a shorter height. Override with `h-auto py-0.5` if needed to preserve the compact grid layout.

### PortfolioDesignerScreen — Select Replacement

```tsx
// Before (line 434):
<select
  value={resolutionStrategy}
  onChange={(e) => setResolutionStrategy(e.target.value as ResolutionStrategy)}
  className="w-full border border-slate-200 px-2 py-1.5 text-xs bg-white"
  aria-label="Resolution strategy"
>
  {VALID_STRATEGIES.map((s) => (
    <option key={s} value={s}>{s}</option>
  ))}
</select>

// After:
<Select
  value={resolutionStrategy}
  onChange={(e) => setResolutionStrategy(e.target.value as ResolutionStrategy)}
  className="text-xs"
  aria-label="Resolution strategy"
>
  {VALID_STRATEGIES.map((s) => (
    <option key={s} value={s}>{s}</option>
  ))}
</Select>
```

The `Select` component provides `w-full`, `border`, `border-slate-300`, `bg-white`, `px-2`, `h-8`. Only pass `text-xs` for the smaller text size.

### TemplateSelectionScreen — Select Replacement

```tsx
// Before (line 150):
<select
  value={param.type}
  onChange={(e) => updateParam(i, "type", e.target.value)}
  className="h-9 rounded-md border border-input bg-transparent px-2 text-sm"
>
  <option value="float">float</option>
  <option value="int">int</option>
  <option value="str">str</option>
</select>

// After:
<Select
  value={param.type}
  onChange={(e) => updateParam(i, "type", e.target.value)}
  className="w-auto flex-shrink-0"
>
  <option value="float">float</option>
  <option value="int">int</option>
  <option value="str">str</option>
</Select>
```

Note the original uses `border-input` (a CSS var that may or may not exist in this project's Tailwind config). The `Select` component uses `border-slate-300` which is the project standard. Override `w-full` with `w-auto flex-shrink-0` since this is an inline element in a row.

### RunSelector — Checkbox Replacement

```tsx
// Before (line 53):
<input
  type="checkbox"
  checked={isSelected}
  disabled={isDisabled}
  onChange={() => !isDisabled && onToggle(item.run_id)}
  aria-label={`Select run ${item.run_id.slice(0, 8)}`}
  className="h-3.5 w-3.5 cursor-pointer"
/>

// After:
<Checkbox
  checked={isSelected}
  disabled={isDisabled}
  onChange={() => !isDisabled && onToggle(item.run_id)}
  aria-label={`Select run ${item.run_id.slice(0, 8)}`}
  className="h-3.5 w-3.5"
/>
```

The `Checkbox` provides `cursor-pointer` and `disabled:cursor-not-allowed` from its base classes.

### Skeleton Loading Patterns

**ComparisonDashboardScreen (line 186-190):**

```tsx
// Before:
{loading ? (
  <div className="rounded-lg border border-slate-200 bg-white p-6 text-center">
    <p className="text-sm text-slate-500">Loading comparison data…</p>
  </div>
) : null}

// After:
{loading ? (
  <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-6">
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-1/2" />
  </div>
) : null}
```

**ResultsOverviewScreen (line 280-281):**

```tsx
// Before:
{detailLoading ? (
  <p className="text-xs text-slate-400">Loading detail...</p>
) : ...}

// After:
{detailLoading ? (
  <div className="space-y-2">
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-5/6" />
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-2/3" />
  </div>
) : ...}
```

**VariableOverlapView (line 89-90):**

```tsx
// Before:
{loading ? (
  <p className="text-xs text-slate-500">Loading column details...</p>
) : ...}

// After:
{loading ? (
  <div className="space-y-2">
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-3/4" />
  </div>
) : ...}
```

### What NOT to Change

- **Decorative readOnly checkboxes** — `PortfolioTemplateBrowser.tsx` (line 134), `DataSourceBrowser.tsx` (line 101): these are `readOnly` visual indicators, not interactive form inputs. Leave as-is.
- **Decorative readOnly radio** — `MergeMethodSelector.tsx` (line 72): `aria-hidden="true"`, purely decorative inside a `<button>`. Leave as-is.
- **Button-based loading states** — Button label swaps ("Loading...", "Running...", "Saving...", "Checking...") in `RunSelector`, `PortfolioDesignerScreen`, `PasswordPrompt`, `App.tsx` are appropriate UX — not plain text in content areas. Leave as-is.
- **`PopulationGenerationProgress.tsx`** — Already has a proper `Loader2` spinner animation. Leave as-is.
- **`BehavioralDecisionViewerScreen.tsx`** — Uses `animate-pulse` inline text in the header bar, which is a reasonable pattern for non-blocking background loads. Leave as-is.
- **`RunProgressBar` component** — Dedicated progress component for slow operations. Not a skeleton use case.
- **Backend files** — Frontend-only story.
- **`frontend/src/contexts/AppContext.tsx`** — No changes; loading booleans already exposed but are consumed for button disabling, not for skeleton display.
- **Initial data load skeletons** — The `useApi.ts` hooks initialize with mock data, so populations/templates/parameters screens show data immediately without a loading state. No skeleton needed for initial page renders.

### Existing Tests That Cover Modified Files

| File | Test File | Tests |
|------|-----------|-------|
| `RunSelector.tsx` | `ComparisonDashboardScreen.test.tsx` | 16 tests — renders run list, checkbox interactions |
| `SimulationRunnerScreen.tsx` | `SimulationRunnerScreen.test.tsx` | Tests cover year inputs, seed field |
| `PortfolioDesignerScreen.tsx` | `PortfolioDesignerScreen.test.tsx` | Tests cover strategy select |
| `TemplateSelectionScreen.tsx` | `TemplateSelectionScreen.test.tsx` | Tests cover custom template form |
| `ResultsOverviewScreen.tsx` | `ResultsOverviewScreen.test.tsx` | Tests cover detail loading state |
| `ComparisonDashboardScreen.tsx` | `ComparisonDashboardScreen.test.tsx` | Tests cover loading state |

These tests query by `aria-label`, `role`, and text content — not by element type. Replacing `<input>` with `<Input>` (which renders as `<input>`) and `<select>` with `<Select>` (which renders as `<select>`) should not break any existing test assertions.

**Potential test breakage:** If any test asserts the exact text "Loading comparison data…", "Loading detail...", or "Loading column details...", it will break because those strings are replaced by `<Skeleton>` elements. Check these specific assertions before implementing skeleton replacements — if found, update the test to query for the skeleton's container or `aria-busy` attribute instead.

### Skeleton Test Pattern

```tsx
import { render, screen } from "@testing-library/react";

import { Skeleton } from "@/components/ui/skeleton";

describe("Skeleton", () => {
  it("renders with animate-pulse class", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel")).toHaveClass("animate-pulse");
  });

  it("renders with bg-slate-200 class", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel")).toHaveClass("bg-slate-200");
  });

  it("merges custom className", () => {
    render(<Skeleton data-testid="skel" className="h-4 w-full" />);
    const el = screen.getByTestId("skel");
    expect(el).toHaveClass("animate-pulse");
    expect(el).toHaveClass("h-4");
    expect(el).toHaveClass("w-full");
  });

  it("renders as a div element", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel").tagName).toBe("DIV");
  });
});
```

### Project Structure Notes

**New files (3):**
- `frontend/src/components/ui/checkbox.tsx`
- `frontend/src/components/ui/skeleton.tsx`
- `frontend/src/components/ui/__tests__/skeleton.test.tsx`

**Modified files (8):**
- `frontend/src/components/ui/select.tsx` — add `rounded-md` to base classes
- `frontend/src/components/screens/SimulationRunnerScreen.tsx` — replace 3 raw `<input>` with `<Input>`
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` — replace 1 raw `<select>` with `<Select>`
- `frontend/src/components/screens/TemplateSelectionScreen.tsx` — replace 1 raw `<select>` with `<Select>`
- `frontend/src/components/comparison/RunSelector.tsx` — replace 1 raw `<input type="checkbox">` with `<Checkbox>`
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — replace loading text with `<Skeleton>` bars
- `frontend/src/components/screens/ResultsOverviewScreen.tsx` — replace loading text with `<Skeleton>` rows
- `frontend/src/components/simulation/VariableOverlapView.tsx` — replace loading text with `<Skeleton>` rows

### Complete Inventory of Raw Form Elements (Post-Story)

After this story, the only remaining raw form elements outside `components/ui/` will be:
- **`PortfolioTemplateBrowser.tsx:134`** — `<input type="checkbox" readOnly>` (decorative)
- **`DataSourceBrowser.tsx:101`** — `<input type="checkbox" readOnly>` (decorative)
- **`MergeMethodSelector.tsx:72`** — `<input type="radio" readOnly aria-hidden>` (decorative)
- **`PasswordPrompt.tsx`** — Already uses `<Input>` component

These are all non-interactive decorative indicators — not form inputs.

### References

- [Source: `_bmad-output/implementation-artifacts/epic-18-ux-polish-and-aesthetic-overhaul.md` — Story 18.6: "Standardize form inputs and add loading skeletons", 3SP, P1]
- [Source: `_bmad-output/planning-artifacts/epics.md` — BDD: "Given all form inputs, when rendered, then they use the shadcn Input component (no raw `<input>` elements)"]
- [Source: `_bmad-output/planning-artifacts/epics.md` — BDD: "Given loading states, when data is being fetched, then skeleton placeholders are shown instead of blank areas"]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic-level AC: "All form inputs use shadcn Input component (no raw `<input>` elements)"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Lines 1289-1301: Loading & Progress Patterns — "Fast operations (200ms-2s): Skeleton loader in the affected area only"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Lines 903-927: Design System Components — Input, Select, Slider, Switch]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Lines 1237-1258: Data Editing Patterns — inline editing, validation]
- [Source: `frontend/src/components/ui/input.tsx` — Input component pattern to follow]
- [Source: `frontend/src/components/ui/select.tsx` — Select component pattern to follow (missing rounded-md)]
- [Source: `frontend/src/components/screens/SimulationRunnerScreen.tsx:209-238` — 3 raw `<input type="number">` elements to replace]
- [Source: `frontend/src/components/screens/PortfolioDesignerScreen.tsx:434-443` — 1 raw `<select>` element to replace]
- [Source: `frontend/src/components/screens/TemplateSelectionScreen.tsx:150-158` — 1 raw `<select>` element to replace]
- [Source: `frontend/src/components/comparison/RunSelector.tsx:53-59` — 1 raw `<input type="checkbox">` to replace]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:186-190` — "Loading comparison data…" text to replace with skeleton]
- [Source: `frontend/src/components/screens/ResultsOverviewScreen.tsx:280-281` — "Loading detail..." text to replace with skeleton]
- [Source: `frontend/src/components/simulation/VariableOverlapView.tsx:89-90` — "Loading column details..." text to replace with skeleton]
- [Source: `_bmad-output/implementation-artifacts/18-5-consolidate-config-flow-split-dense-screens.md` — Predecessor story (dependency 18.3 already done)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes

### File List
