# Story 18.7: Repurpose Right Panel as Contextual Help

Status: draft

## Story

As a policy analyst,
I want the right sidebar to show contextually relevant information about what I'm currently working on (data source documentation, parameter descriptions, metric methodology, run manifests),
so that I don't have to leave my current workflow to find reference information.

## Acceptance Criteria

1. **AC-1: Context-aware content** — Given the right panel, when the user is in different view modes, then the panel displays content relevant to that mode:
   - **Data Fusion**: Data source metadata, variable descriptions, merge method documentation
   - **Portfolio**: Selected template details, parameter descriptions, conflict explanations
   - **Simulation/Config**: Population summary, selected policy details, parameter baseline values
   - **Results**: Run manifest summary (inputs, seed, timestamp, duration, assumptions count)
   - **Comparison**: Metric methodology descriptions, indicator definitions
   - **Behavioral Decisions**: Decision model documentation, domain parameter descriptions

2. **AC-2: Remove "Workspace State" card** — Given the right panel, when rendered, then the "Workspace State" debug card (which shows viewMode as a badge) is removed. This is developer information, not analyst information.

3. **AC-3: Collapsible detail sections** — Given the right panel content, when there are multiple sections, then each section is collapsible (using the shadcn Collapsible component) so the user can manage information density. Sections default to expanded.

4. **AC-4: Help panel header** — Given the right panel, when expanded, then the header reads "Context" (not "Run Context" as currently) with a book/info icon.

5. **AC-5: Preserved scenario summary** — Given the right panel, when a scenario is selected, then the scenario summary card (name, status, last run, template, parameter count) remains at the top of the panel in all modes, followed by the context-specific content below.

6. **AC-6: Graceful empty states** — Given a view mode where no contextual information is available (e.g., no population selected in Data Fusion yet), then the panel shows a helpful empty state message: "Select a data source to see its documentation here."

## Tasks / Subtasks

- [ ] Task 1: Design context content per mode
  - [ ] 1.1: Define what data is available per viewMode from AppContext and API responses
  - [ ] 1.2: Create `ContextPanel` component in `frontend/src/components/layout/ContextPanel.tsx` that switches content based on `viewMode` prop
  - [ ] 1.3: Implement Data Fusion context: selected source names, column count, merge method description
  - [ ] 1.4: Implement Portfolio context: template descriptions, parameter groups
  - [ ] 1.5: Implement Results context: run manifest fields (run_id, started_at, duration, seed, assumption_count)
  - [ ] 1.6: Implement Comparison context: indicator type definitions from API

- [ ] Task 2: Update RightPanel
  - [ ] 2.1: Replace static cards in `App.tsx:501-545` with `<ContextPanel viewMode={viewMode} ... />`
  - [ ] 2.2: Remove "Workspace State" card
  - [ ] 2.3: Update RightPanel header from "Run Context" to "Context" with info icon
  - [ ] 2.4: Keep scenario summary card at top, add Separator, then context content
  - [ ] 2.5: Wrap context sections in Collapsible components

- [ ] Task 3: Tests
  - [ ] 3.1: Unit test ContextPanel renders appropriate content for each viewMode
  - [ ] 3.2: Test collapsible behavior
  - [ ] 3.3: Test empty states render correctly
  - [ ] 3.4: Verify existing tests pass

## Dev Notes

- The current right panel data (Selected Scenario, Population, Template) is mostly redundant with what's already visible in the active screen. The context panel should add *new* value, not repeat what the main content shows
- For Results mode, the run manifest is available from `ResultDetailView` — the context panel should show a summary, with "View full manifest" linking to the detail view
- Don't over-populate the panel — 2-3 collapsible sections per mode is enough. The goal is reference information, not a second dashboard
- The panel content can be purely derived from existing AppContext state — no new API calls needed for MVP
