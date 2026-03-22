# Story 18.3: Extract Shared Components — WorkbenchStepper, ErrorAlert, SelectionGrid

Status: draft

## Story

As a developer maintaining the ReformLab frontend,
I want duplicated UI patterns extracted into shared components,
so that visual consistency is enforced by code reuse rather than manual discipline, and future changes propagate automatically.

## Acceptance Criteria

1. **AC-1: Shared WorkbenchStepper** — Given `DataFusionWorkbench.tsx` and `PortfolioDesignerScreen.tsx`, which each define an identical local `WorkbenchStepper` (~30 lines), when this story is complete, then both screens import a single shared `WorkbenchStepper` from `components/simulation/WorkbenchStepper.tsx`. The shared component accepts `steps: { label: string; key: string }[]`, `activeStep: string`, and `onStepSelect: (key: string) => void`. The existing `ModelConfigStepper` remains separate (it has different styling for the 4-step config flow) unless unification is straightforward.

2. **AC-2: ErrorAlert component** — Given error displays in `BehavioralDecisionViewerScreen` (lines ~259-268), `SimulationRunnerScreen` (~284-302), `ComparisonDashboardScreen` (~666-679), and `DataFusionWorkbench` (~161-168), which all render `{ what, why, fix }` error tuples with `AlertCircle` icons, when this story is complete, then all use a shared `ErrorAlert` component from `components/simulation/ErrorAlert.tsx`. Props: `what: string`, `why: string`, `fix: string`, optional `onRetry?: () => void`.

3. **AC-3: SelectionGrid component** — Given `PopulationSelectionScreen` and `TemplateSelectionScreen`, which have 95% identical card-grid patterns (selection highlight with `border-blue-500 bg-blue-50`, same layout), when this story is complete, then both use a shared `SelectionGrid<T>` component that accepts `items: T[]`, `selectedId: string | null`, `onSelect: (id: string) => void`, and `renderCard: (item: T, selected: boolean) => ReactNode`.

4. **AC-4: No behavior changes** — Given all affected screens, when rendered after extraction, then the visual output and interaction behavior is identical to before. All existing tests pass without modification.

5. **AC-5: Dead code removed** — Given the extraction, when complete, then the inline `WorkbenchStepper` definitions in DataFusionWorkbench and PortfolioDesignerScreen are deleted. The old `ComparisonView.tsx` (Phase 1 prototype, no longer imported) is deleted. The unused step components (`ParametersStep`, `PopulationStep`, `TemplateStep`, `ReviewStep`) are deleted if confirmed unused.

## Tasks / Subtasks

- [ ] Task 1: Extract WorkbenchStepper
  - [ ] 1.1: Create `frontend/src/components/simulation/WorkbenchStepper.tsx` with generic step interface
  - [ ] 1.2: Update `DataFusionWorkbench.tsx` to import shared component, delete local definition
  - [ ] 1.3: Update `PortfolioDesignerScreen.tsx` to import shared component, delete local definition
  - [ ] 1.4: Evaluate whether `ModelConfigStepper` can be unified or should remain separate — document decision

- [ ] Task 2: Extract ErrorAlert
  - [ ] 2.1: Create `frontend/src/components/simulation/ErrorAlert.tsx` — renders `AlertCircle` icon + what/why/fix fields with consistent styling (`border border-red-200 bg-red-50 rounded-lg p-4`)
  - [ ] 2.2: Replace inline error renders in BehavioralDecisionViewerScreen
  - [ ] 2.3: Replace inline error renders in SimulationRunnerScreen
  - [ ] 2.4: Replace inline error renders in ComparisonDashboardScreen
  - [ ] 2.5: Replace inline error renders in DataFusionWorkbench
  - [ ] 2.6: Replace inline error renders in PopulationGenerationProgress (if applicable)

- [ ] Task 3: Extract SelectionGrid
  - [ ] 3.1: Create `frontend/src/components/simulation/SelectionGrid.tsx` — generic grid with selection highlight
  - [ ] 3.2: Refactor `PopulationSelectionScreen.tsx` to use SelectionGrid
  - [ ] 3.3: Refactor `TemplateSelectionScreen.tsx` to use SelectionGrid

- [ ] Task 4: Dead code cleanup
  - [ ] 4.1: Verify `ComparisonView.tsx` is unused (grep for imports) and delete
  - [ ] 4.2: Verify `ParametersStep.tsx`, `PopulationStep.tsx`, `TemplateStep.tsx`, `ReviewStep.tsx` are unused and delete
  - [ ] 4.3: Update any barrel exports or index files

- [ ] Task 5: Tests
  - [ ] 5.1: Add unit tests for WorkbenchStepper, ErrorAlert, SelectionGrid
  - [ ] 5.2: Run all existing tests — verify no regressions
  - [ ] 5.3: Run typecheck and lint — zero errors

## Dev Notes

- WorkbenchStepper in both screens is nearly identical: numbered circles, connecting lines, step labels, click-to-navigate. Only difference may be step count and labels — the component should be fully generic
- ErrorAlert styling should match the visual polish from story 18.2 (rounded-lg)
- SelectionGrid should use CSS Grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`) with gap-3
- When deleting dead code, do a final `grep -r` to confirm zero imports before removing
