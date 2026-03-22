# Story 18.4: Restructure Results View with Tabs and Hierarchy

Status: draft

## Story

As a policy analyst who has just run a simulation,
I want the results view to be organized into clear sections with proper visual hierarchy,
so that I can quickly find key outcomes, explore detailed indicators, and access export/comparison actions without scanning a flat list of buttons.

## Acceptance Criteria

1. **AC-1: Results header with run metadata** — Given the results view (`App.tsx` viewMode="results"), when displayed, then a header section shows: run ID (truncated, monospace), timestamp, population used, template/portfolio used, and run duration. This replaces the current bare chart + buttons layout.

2. **AC-2: Tabbed results layout** — Given the results view, when displayed, then content is organized into tabs:
   - **Overview** (default): Distributional chart + summary stat cards (replace mock stats with real indicators when available)
   - **Indicators**: Link/button to open Comparison Dashboard for deeper analysis
   - **Export**: CSV and Parquet export buttons with format descriptions ("CSV — tabular data for spreadsheets", "Parquet — columnar format for programmatic analysis")

3. **AC-3: Primary vs. secondary actions** — Given the results view, when action buttons are displayed, then "Compare Runs" is a primary button (default variant), "Behavioral Decisions" is secondary (outline), and "Run Again" is tertiary (ghost). Export buttons appear only in the Export tab, not in the main action bar.

4. **AC-4: Real summary stats** — Given a completed simulation run with indicator data, when the Overview tab is displayed, then summary stat cards show real values from the run result (total revenue impact, Gini coefficient change, average household cost, etc.) instead of `mockSummaryStats`. If no indicator data is available, show placeholder cards with "—" values and a note "Run comparison to generate indicators."

5. **AC-5: Results screen as standalone component** — Given the current inline results rendering in `App.tsx:356-377`, when this story is complete, then results are rendered by a dedicated `ResultsOverviewScreen.tsx` component in `components/screens/`, consistent with other screens.

## Tasks / Subtasks

- [ ] Task 1: Create ResultsOverviewScreen
  - [ ] 1.1: Create `frontend/src/components/screens/ResultsOverviewScreen.tsx`
  - [ ] 1.2: Implement run metadata header (run_id, timestamp, population, template)
  - [ ] 1.3: Implement Tabs layout (Overview / Indicators / Export) using shadcn Tabs
  - [ ] 1.4: Move DistributionalChart + SummaryStatCard grid into Overview tab
  - [ ] 1.5: Create Export tab with CSV/Parquet buttons and format descriptions
  - [ ] 1.6: Create Indicators tab with "Open Comparison Dashboard" and "View Behavioral Decisions" buttons

- [ ] Task 2: Wire into App.tsx
  - [ ] 2.1: Replace inline results JSX in App.tsx with `<ResultsOverviewScreen>` component
  - [ ] 2.2: Pass necessary props (runResult, decileData, onCompare, onDecisions, onRunAgain, onExportCsv, onExportParquet)
  - [ ] 2.3: Clean up action button handlers that move to the new component

- [ ] Task 3: Real summary stats (partial)
  - [ ] 3.1: Check if `runResult` from AppContext contains indicator summary data
  - [ ] 3.2: If available, map real indicator values to SummaryStatCard format
  - [ ] 3.3: If not available, render placeholder cards with "—" values

- [ ] Task 4: Tests
  - [ ] 4.1: Unit test ResultsOverviewScreen renders tabs, metadata header
  - [ ] 4.2: Test tab switching between Overview/Indicators/Export
  - [ ] 4.3: Verify existing workflow tests still pass

## Dev Notes

- Current results view in App.tsx is only ~20 lines of JSX but packs 5 action buttons with no hierarchy — the restructure gives each action a logical home
- The `mockSummaryStats` import in App.tsx should be removed once real stats are wired; leave placeholder logic for when indicators haven't been fetched
- The Indicators tab is intentionally lightweight — it's a gateway to the full ComparisonDashboardScreen rather than duplicating its content
- Consider adding a "Run completed successfully" success banner at the top of the results view (using the emerald color palette)
