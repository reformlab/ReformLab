# Story 18.5: Consolidate Configuration Flow and Split Dense Screens

Status: draft

## Story

As a policy analyst,
I want the 4-step configuration flow (population → template → parameters → assumptions) to feel like one cohesive panel rather than 4 separate screen transitions,
and as a developer, I want the 800-line ComparisonDashboardScreen split into maintainable sub-components,
so that the configuration UX is smoother and the codebase is easier to maintain.

## Acceptance Criteria

1. **AC-1: Tabbed configuration panel** — Given the configuration view mode, when displayed, then the 4 steps (Population, Policy, Parameters, Validation) are rendered as horizontal tabs within a single panel, rather than as separate screen renders with a stepper above. Clicking a tab instantly switches content without a full view mode transition. The ModelConfigStepper is replaced by a shadcn Tabs component.

2. **AC-2: Inline navigation** — Given the tabbed configuration panel, when the user completes a step (e.g., selects a population), then the tab shows a subtle completion indicator (checkmark badge) and the "Next" button advances to the next tab. The user can also click any tab directly to jump to that step.

3. **AC-3: ComparisonDashboard tab extraction** — Given `ComparisonDashboardScreen.tsx` (805 lines), when this story is complete, then the three inline tab components (DistributionalTab, FiscalTab, WelfareTab) are extracted into separate files:
   - `components/simulation/comparison/DistributionalTab.tsx`
   - `components/simulation/comparison/FiscalTab.tsx`
   - `components/simulation/comparison/WelfareTab.tsx`
   ComparisonDashboardScreen imports and renders them, reducing its size to ~300 lines.

4. **AC-4: PortfolioDesigner sub-component extraction** — Given `PortfolioDesignerScreen.tsx` (763 lines), when this story is complete, then the step content for each of the 3 steps is extracted into separate components:
   - Step 1 content → stays inline (uses PortfolioTemplateBrowser, already a component)
   - Step 2 content → stays inline (uses PortfolioCompositionPanel)
   - Step 3 "Review & Save" → extract `PortfolioReviewPanel.tsx` (~150 lines with save/clone dialogs)
   PortfolioDesignerScreen imports and renders them, reducing its size to ~500 lines.

5. **AC-5: No behavior changes** — Given all affected screens, when rendered, then interaction behavior is identical to before. All existing tests pass.

## Tasks / Subtasks

- [ ] Task 1: Refactor configuration flow to tabs
  - [ ] 1.1: Replace `ModelConfigStepper` + conditional rendering in App.tsx with a shadcn `Tabs` component
  - [ ] 1.2: Each tab renders the corresponding screen component inline (PopulationSelectionScreen, TemplateSelectionScreen, etc.)
  - [ ] 1.3: Add completion indicator badges to tab triggers
  - [ ] 1.4: Keep the "Next Step" / "Go to Simulation" button below the tabs panel

- [ ] Task 2: Extract ComparisonDashboard tab components
  - [ ] 2.1: Create `frontend/src/components/simulation/comparison/` directory
  - [ ] 2.2: Extract DistributionalTab into `DistributionalTab.tsx`
  - [ ] 2.3: Extract FiscalTab into `FiscalTab.tsx`
  - [ ] 2.4: Extract WelfareTab into `WelfareTab.tsx`
  - [ ] 2.5: Update ComparisonDashboardScreen to import extracted components

- [ ] Task 3: Extract PortfolioDesigner review panel
  - [ ] 3.1: Extract review/save step content into `PortfolioReviewPanel.tsx`
  - [ ] 3.2: Move save and clone dialog JSX into the new component
  - [ ] 3.3: Update PortfolioDesignerScreen imports

- [ ] Task 4: Tests
  - [ ] 4.1: Update configuration flow tests for tab-based navigation
  - [ ] 4.2: Verify ComparisonDashboard tests pass with extracted components
  - [ ] 4.3: Run full test suite — zero regressions

## Dev Notes

- The 4 config screen components (PopulationSelectionScreen etc.) are only 40-65 lines each — they're lightweight enough to render inline in tabs without performance concern
- When extracting ComparisonDashboard tabs, each receives the shared state (selectedRunIds, data, etc.) as props — keep prop interfaces minimal
- The `FiscalTab` and `WelfareTab` components share ~80% of their table rendering logic — consider a shared `IndicatorTable` helper during extraction, but don't over-abstract
