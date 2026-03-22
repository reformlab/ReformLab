# Story 18.6: Standardize Form Inputs and Add Loading Skeletons

Status: draft

## Story

As a policy analyst,
I want all form inputs to look and behave consistently, and content areas to show skeleton placeholders while loading,
so that the interface feels cohesive and responsive rather than jumpy or inconsistent.

## Acceptance Criteria

1. **AC-1: No raw `<input>` elements** — Given all screens, when inspected, then every form input uses the shadcn `<Input>` component from `@/components/ui/input`. No raw `<input>` HTML elements remain in screen or simulation components. Specifically, the raw `<input type="number">` elements in `SimulationRunnerScreen` (year/seed inputs) are replaced with `<Input>`.

2. **AC-2: Numeric input variant** — Given numeric form fields (year, seed, record count, parameter values), when rendered, then they use a consistent pattern: `<Input type="number" className="data-mono" />` with appropriate width constraints. A `NumericInput` wrapper component is optional but the pattern must be consistent.

3. **AC-3: Card grid skeletons** — Given the PopulationSelectionScreen and TemplateSelectionScreen, when data is loading (populations/templates arrays are empty and loading is true), then skeleton cards (gray rounded rectangles with `animate-pulse`) are shown in the same grid layout as the actual cards.

4. **AC-4: Chart area skeletons** — Given any screen with a Recharts chart (DistributionalChart, MultiRunChart, TransitionChart), when the chart data is loading or empty, then a skeleton placeholder (gray rectangle matching chart height `h-72` with `animate-pulse`) is shown instead of an empty space or nothing.

5. **AC-5: Table row skeletons** — Given the ComparisonDashboardScreen and ResultsListPanel, when data is loading, then skeleton table rows (3-5 animated gray bars per row, 5 rows) are shown in place of actual content.

6. **AC-6: Consistent form labels** — Given all labeled form fields, when rendered, then labels use the pattern `text-xs font-semibold uppercase text-slate-500` consistently. Fields without labels get appropriate `aria-label` attributes.

## Tasks / Subtasks

- [ ] Task 1: Standardize inputs
  - [ ] 1.1: Grep for raw `<input` across all `frontend/src/components/` files
  - [ ] 1.2: Replace each instance with shadcn `<Input>` component
  - [ ] 1.3: Ensure `data-mono` class is applied to all numeric inputs
  - [ ] 1.4: Verify consistent label patterns across all forms

- [ ] Task 2: Create Skeleton components
  - [ ] 2.1: Create `frontend/src/components/ui/skeleton.tsx` — base Skeleton component (`div` with `animate-pulse bg-slate-200 rounded-md`)
  - [ ] 2.2: Create `SkeletonCard` variant (card-shaped skeleton for selection grids)
  - [ ] 2.3: Create `SkeletonChart` variant (chart-height rectangle)
  - [ ] 2.4: Create `SkeletonTableRows` variant (multiple rows of varying-width bars)

- [ ] Task 3: Integrate skeletons
  - [ ] 3.1: Add skeleton states to PopulationSelectionScreen and TemplateSelectionScreen (or SelectionGrid from 18.3)
  - [ ] 3.2: Add skeleton states to chart containers in DistributionalChart, MultiRunChart, TransitionChart
  - [ ] 3.3: Add skeleton states to ResultsListPanel and ComparisonDashboard tables

- [ ] Task 4: Tests
  - [ ] 4.1: Test Skeleton component renders with correct classes
  - [ ] 4.2: Test that loading states in screens show skeletons
  - [ ] 4.3: Run full test suite — zero regressions

## Dev Notes

- shadcn/ui has an official Skeleton component — check if it's already installed (`components/ui/skeleton.tsx`). If not, install via `npx shadcn@latest add skeleton`
- The `animate-pulse` animation is built into Tailwind — no additional CSS needed
- Skeleton dimensions should match the actual content dimensions to prevent layout shift when data loads
- Loading states: check AppContext for existing `*Loading` boolean flags (e.g., `populationsLoading`, `templatesLoading`)
