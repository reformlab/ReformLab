# Story 18.1: Implement Workflow Navigation Rail

Status: draft

## Story

As a policy analyst,
I want a persistent vertical navigation rail in the left panel that shows my progress through the workflow stages (Population → Portfolio → Simulation → Results),
so that I always know where I am in the process, what's completed, and what's next.

## Acceptance Criteria

1. **AC-1: Navigation rail replaces flat buttons** — Given the left panel, when the workspace loads, then the four navigation buttons (Population, Portfolio, Simulation, Configure Policy) are replaced by a vertical stepper showing workflow stages with numbered step indicators and connecting lines between them.

2. **AC-2: Completion indicators** — Given a workflow stage, when the user has completed meaningful work in that stage (e.g., selected a population, created a portfolio, run a simulation), then the step indicator shows a checkmark icon with emerald color instead of the stage number. Incomplete stages show a circle with the stage number. The active stage shows a filled blue circle.

3. **AC-3: Stage summary lines** — Given each workflow stage in the nav rail, when there is relevant state (e.g., population selected, portfolio name, last run timestamp), then a one-line summary is displayed below the stage label in muted text (e.g., "INSEE households · 12,400 records", "carbon-transition · 3 templates", "Last run: 2 min ago").

4. **AC-4: Clickable navigation** — Given the nav rail, when the analyst clicks any stage, then the main panel switches to that stage's view mode. Stages are always clickable (no locking) to support non-linear workflows.

5. **AC-5: Scenarios section preserved** — Given the left panel, when scenarios exist, then ScenarioCards still appear below the navigation rail, separated by a visual divider.

6. **AC-6: Collapsed state** — Given the left panel in collapsed state, when viewed, then the nav rail shows only the step indicator icons (no labels or summaries) in a vertical column.

## Tasks / Subtasks

- [ ] Task 1: Create `WorkflowNavRail` component
  - [ ] 1.1: Create `frontend/src/components/layout/WorkflowNavRail.tsx` — vertical stepper with stage indicators (number/check), labels, summary lines, and connecting lines
  - [ ] 1.2: Define stage completion logic: Population = `selectedPopulationId || dataFusionResult` exists; Portfolio = `portfolios.length > 0`; Simulation = `results.length > 0`; Results = most recent run has result data
  - [ ] 1.3: Implement collapsed variant showing only icons
  - [ ] 1.4: Style with consistent design tokens: `border-l-2` connecting line, `h-8 w-8 rounded-full` step circles, emerald for completed, blue-500 for active, slate-300 for pending

- [ ] Task 2: Integrate into LeftPanel and App.tsx
  - [ ] 2.1: Replace the 4 `<Button>` elements in `App.tsx:436-466` with `<WorkflowNavRail>` component
  - [ ] 2.2: Pass `viewMode`, `setViewMode`, and completion state as props
  - [ ] 2.3: Add `<Separator>` between nav rail and ScenarioCard list
  - [ ] 2.4: Update LeftPanel collapsed view to render collapsed nav rail variant

- [ ] Task 3: Tests
  - [ ] 3.1: Unit test WorkflowNavRail renders all stages with correct completion states
  - [ ] 3.2: Test click handlers trigger correct viewMode changes
  - [ ] 3.3: Test collapsed state renders icon-only variant
  - [ ] 3.4: Verify existing workflow tests still pass

## Dev Notes

- The `viewMode` type in App.tsx maps to stages: `data-fusion` → Population, `portfolio` → Portfolio, `runner` → Simulation, `results|comparison|decisions` → Results, `configuration` → Configure Policy (keep as sub-navigation within the Simulation stage or as a separate entry)
- Consider whether "Configure Policy" (the 4-step config stepper) should be a separate nav rail stage or folded into the Simulation stage. Recommendation: fold it into Simulation as a sub-step, since it's preparation for running.
- Connecting lines between steps: use absolute-positioned `border-l-2` divs or flex with gap
