
# Story 18.7: Repurpose Right Panel as Contextual Help

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst using the ReformLab workspace,
I want the right panel to display contextual help relevant to my current workflow stage,
so that I can understand what to do at each step without leaving the workspace or consulting external documentation.

## Acceptance Criteria

1. **AC-1: Stage-specific help content** — Given the right panel in expanded state, when any workflow stage is active (viewMode is one of: `data-fusion`, `portfolio`, `runner`, `configuration`, `run`, `progress`, `results`, `comparison`, `decisions`), then the help panel displays a stage-specific title (`text-sm font-semibold text-slate-900`), summary description (`text-xs text-slate-600 leading-normal`), and a bulleted list of practical tips (`text-xs text-slate-500`, `<ul>` with `<li>` elements using `list-disc` marker). The content updates automatically when the user navigates to a different stage.

2. **AC-2: Configuration sub-step differentiation** — Given the configuration view mode (`viewMode === "configuration"`), when the user navigates between sub-steps (`activeStep` cycles through `population`, `template`, `parameters`, `assumptions`), then the help panel displays sub-step-specific content distinct from the general stage help. Each sub-step has its own title, summary, and tips. The lookup key is `configuration:${activeStep}`. When `viewMode !== "configuration"`, the `activeStep` prop is ignored.

3. **AC-3: Key concepts expandable** — Given help entries that include key concepts (term-definition pairs), when rendered, then a "Key Concepts" section appears below the tips using the `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent` components from `@/components/ui/collapsible`. The section is collapsed by default. A `ChevronRight` icon (lucide-react) on the trigger rotates 90 degrees when expanded. Entries without concepts omit this section entirely.

4. **AC-4: Panel header and label updated** — Given the `RightPanel` component:
   - When expanded, the header text reads **"Help"** (replacing "Run Context"). A `HelpCircle` icon (`h-3.5 w-3.5 text-slate-400`, lucide-react) is displayed to the left of the header text.
   - When collapsed, the rotated vertical label reads **"Help"** (replacing "Context").

5. **AC-5: Old static content replaced** — Given the repurposed right panel, when any view mode is active, then the previous static sections (Selected Scenario card, Population name, Template name, Workspace State badges — App.tsx lines 407-448) are no longer rendered. Unused code is removed: the `selectedPopulation` useMemo and the `Badge` import become dead code in App.tsx and must be removed. The `selectedTemplate` and `selectedScenario` useMemos are still used in `mainPanelContent` and must NOT be removed.

6. **AC-6: No regressions** — Given all changes, when tests run, then:
   - The full test suite passes (0 failures)
   - `npm run typecheck` reports 0 errors
   - `npm run lint` reports 0 errors (pre-existing fast-refresh warnings OK)

7. **AC-7: New component tests** — Given the new `ContextualHelpPanel` component, when tested in `frontend/src/components/help/__tests__/ContextualHelpPanel.test.tsx`, then:
   - Renders the correct help title for at least 4 distinct viewModes (`data-fusion`, `portfolio`, `results`, `comparison`)
   - Renders sub-step-specific title when `viewMode="configuration"` and `activeStep="population"` (should show "Select Population", not generic configuration help)
   - Renders tips as `<li>` elements inside a `<ul>`
   - Renders a "Key Concepts" trigger (text "Key Concepts") for entries that define concepts
   - Does NOT render "Key Concepts" for entries without concepts

## Tasks / Subtasks

- [ ] Task 1: Create help content data module (AC: 1, 2)
  - [ ] 1.1: Create `frontend/src/components/help/help-content.ts` with `HelpEntry` interface and `HELP_CONTENT` record containing all 12 help entries (see Dev Notes for exact content)
  - [ ] 1.2: Export `getHelpEntry(viewMode: string, activeStep?: string): HelpEntry` lookup function — when `viewMode === "configuration"` and `activeStep` is defined, looks up `configuration:${activeStep}`; otherwise looks up by `viewMode`; falls back to `configuration:population` if key not found

- [ ] Task 2: Create ContextualHelpPanel component (AC: 1, 2, 3)
  - [ ] 2.1: Create `frontend/src/components/help/ContextualHelpPanel.tsx` accepting `viewMode: string` and optional `activeStep?: string`
  - [ ] 2.2: Render help title, summary, and tips list using styles from AC-1
  - [ ] 2.3: When `help.concepts` is defined and non-empty, render a collapsible "Key Concepts" section using `Collapsible`/`CollapsibleTrigger`/`CollapsibleContent`. Use local `useState(false)` to track open state; apply `rotate-90` to `ChevronRight` icon when open.
  - [ ] 2.4: Each concept renders as a `<dt>` (term, `text-xs font-medium text-slate-700`) and `<dd>` (definition, `text-xs text-slate-500 leading-normal`) inside a `<dl>`

- [ ] Task 3: Update RightPanel header (AC: 4)
  - [ ] 3.1: In `RightPanel.tsx` line 29, change `"Run Context"` to `"Help"`
  - [ ] 3.2: In `RightPanel.tsx` line 20, change `"Context"` to `"Help"`
  - [ ] 3.3: Import `HelpCircle` from `lucide-react`; add `<HelpCircle className="h-3.5 w-3.5 text-slate-400" />` before the header `<p>` tag inside a `<div className="flex items-center gap-1.5">` wrapper

- [ ] Task 4: Update App.tsx right panel content (AC: 5)
  - [ ] 4.1: Import `ContextualHelpPanel` from `@/components/help/ContextualHelpPanel`
  - [ ] 4.2: Replace lines 407-448 (old right panel children `<div className="space-y-3">...`) with `<ContextualHelpPanel viewMode={viewMode} activeStep={activeStep} />`
  - [ ] 4.3: Remove the `Badge` import (line 23) — no longer used in App.tsx after removing the right panel content. Verify no other usage exists in the file.
  - [ ] 4.4: Remove the `selectedPopulation` useMemo (lines 81-84) — no longer referenced after removing the right panel content. Do NOT remove `selectedTemplate` or `selectedScenario` — they are used in `mainPanelContent`.

- [ ] Task 5: Write tests (AC: 7)
  - [ ] 5.1: Create `frontend/src/components/help/__tests__/ContextualHelpPanel.test.tsx`
  - [ ] 5.2: Test: renders "Population Builder" title when `viewMode="data-fusion"`
  - [ ] 5.3: Test: renders "Portfolio Designer" title when `viewMode="portfolio"`
  - [ ] 5.4: Test: renders "Results Overview" title when `viewMode="results"`
  - [ ] 5.5: Test: renders "Comparison Dashboard" title when `viewMode="comparison"`
  - [ ] 5.6: Test: renders "Select Population" title when `viewMode="configuration"` and `activeStep="population"` (not generic configuration help)
  - [ ] 5.7: Test: renders tips as `<li>` elements inside a `<ul>`
  - [ ] 5.8: Test: renders "Key Concepts" trigger text for `viewMode="data-fusion"` (which has concepts defined)
  - [ ] 5.9: Test: does NOT render "Key Concepts" for `viewMode="progress"` (which has no concepts)

- [ ] Task 6: Verify no regressions (AC: 6)
  - [ ] 6.1: Run `npm test` — full test suite passes (0 failures)
  - [ ] 6.2: Run `npm run typecheck` — 0 errors
  - [ ] 6.3: Run `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)

## Dev Notes

### Help Content Data (`help-content.ts`)

Define the following interface and record. All text content is provided below — copy verbatim:

```typescript
export interface HelpEntry {
  title: string;
  summary: string;
  tips: string[];
  concepts?: Array<{ term: string; definition: string }>;
}

export function getHelpEntry(viewMode: string, activeStep?: string): HelpEntry {
  const key = viewMode === "configuration" && activeStep
    ? `configuration:${activeStep}`
    : viewMode;
  return HELP_CONTENT[key] ?? HELP_CONTENT["configuration:population"]!;
}
```

**Complete help content (12 entries):**

| Key | Title | Summary | Tips | Concepts |
|-----|-------|---------|------|----------|
| `data-fusion` | Population Builder | Create a synthetic population by selecting and merging data from multiple statistical sources. | 4 | 3 |
| `portfolio` | Portfolio Designer | Compose multiple policy templates into a single reform package with conflict resolution. | 4 | 3 |
| `configuration:population` | Select Population | Choose the population dataset for your simulation. | 3 | — |
| `configuration:template` | Choose Policy Template | Select a policy template that defines the reform to simulate. | 3 | — |
| `configuration:parameters` | Configure Parameters | Adjust policy parameters to define your specific reform scenario. | 3 | 1 |
| `configuration:assumptions` | Review Assumptions | Verify all assumptions and data sources before running the simulation. | 3 | — |
| `run` | Run Simulation | Execute the configured simulation across the specified year range. | 3 | — |
| `progress` | Simulation in Progress | The simulation is computing results for each year in the range. | 2 | — |
| `runner` | Simulation Runner | Configure and execute a full multi-year simulation run with explicit controls. | 3 | — |
| `results` | Results Overview | Explore the distributional impact of your reform across income deciles. | 4 | — |
| `comparison` | Comparison Dashboard | Compare up to 5 simulation runs side-by-side with distributional and fiscal indicators. | 4 | 3 |
| `decisions` | Behavioral Decisions | Explore how households respond to policy changes through discrete choice modeling. | 3 | 2 |

**Full tips and concepts per entry:**

**`data-fusion`:**
- Tips:
  - "Select at least two data sources from the available providers to begin"
  - "Overlapping variables (shared across sources) enable statistical matching for higher-quality fusion"
  - "The merge method determines how records are combined — conditional sampling preserves correlations best"
  - "Preview the generated population to verify demographic distributions before proceeding"
- Concepts:
  - Data Fusion: "Combining records from multiple data sources into a unified population dataset using statistical matching."
  - Overlapping Variables: "Variables present in multiple sources that serve as matching keys for statistical fusion."
  - Conditional Sampling: "A merge method that preserves correlations between variables by sampling conditionally on shared keys."

**`portfolio`:**
- Tips:
  - "Select two or more templates in step 1, then configure their parameters in step 2"
  - "Policy ordering matters — policies are applied in the sequence shown"
  - "Use year schedules to phase in rate changes over the simulation horizon"
  - "The conflict resolution strategy determines what happens when two policies modify the same parameter"
- Concepts:
  - Policy Portfolio: "A bundle of multiple policy templates combined into a single coherent reform package."
  - Conflict Resolution: "A strategy for handling cases where two policies set the same parameter (sum, first_wins, last_wins, max)."
  - Year Schedule: "A per-year rate mapping that allows gradual phase-in of policy changes over time."

**`configuration:population`:**
- Tips:
  - "Pre-built populations (e.g., French synthetic 2024) are ready to use immediately"
  - "Custom populations created in the Population Builder appear here automatically"
  - "The population defines household composition, income distributions, and consumption patterns used in the simulation"

**`configuration:template`:**
- Tips:
  - "Each template maps to an OpenFisca policy type with predefined parameters"
  - "Custom templates can be created with the 'Create Custom Template' button"
  - "The template determines which parameters are available for configuration in the next step"

**`configuration:parameters`:**
- Tips:
  - "Parameter values define the details of your reform — tax rates, thresholds, exemptions"
  - "Changes from default values are tracked and shown in the assumptions review"
  - "Use realistic values based on published policy proposals for meaningful analysis"
- Concepts:
  - Parameter Overrides: "Changes to default template values that define how your reform differs from the baseline."

**`configuration:assumptions`:**
- Tips:
  - "The assumption review lists every parameter value and data source used in the simulation"
  - "All assumptions are recorded in the run manifest for reproducibility"
  - "Proceed to simulation when you are satisfied with the configuration"

**`run`:**
- Tips:
  - "The simulation computes both baseline and reform scenarios year by year"
  - "Results include distributional impact, fiscal balance, and welfare indicators"
  - "Each run gets a unique ID for tracking, export, and cross-run comparison"

**`progress`:**
- Tips:
  - "Year-by-year computation ensures demographic transitions and behavioral responses are captured"
  - "Results are typically ready within a few seconds for standard-sized populations"

**`runner`:**
- Tips:
  - "Set start and end years to define the simulation horizon"
  - "An explicit seed ensures reproducible results — leave blank for random"
  - "Past simulation results are listed below the configuration form"

**`results`:**
- Tips:
  - "The bar chart shows net impact by income decile — positive values mean households gain"
  - "Summary statistics highlight the mean impact and the most affected groups"
  - "Use 'Compare Runs' to see side-by-side analysis of multiple scenarios"
  - "Export data as CSV (for spreadsheets) or Parquet (for programmatic analysis) from the Data & Export tab"

**`comparison`:**
- Tips:
  - "Select 2–5 completed runs from the list, then click Compare"
  - "The first selected run is treated as the baseline for relative comparisons"
  - "Toggle between absolute and relative views to see raw values or percentage changes"
  - "Click any chart bar to see detailed indicator values in the panel below"
- Concepts:
  - Baseline Run: "The reference run against which all other selected runs are compared to compute deltas."
  - Distributional Indicators: "Metrics showing how reform impact varies across income deciles."
  - Cross-Portfolio Metrics: "Aggregate metrics that rank and compare reform packages on key dimensions."

**`decisions`:**
- Tips:
  - "The transition chart shows year-by-year changes in household vehicle fleet or heating systems"
  - "Filter by income decile to see how behavioral responses vary across the population"
  - "Click a year on the chart to see detailed transition probabilities for that period"
- Concepts:
  - Discrete Choice Model: "A model of household decision-making that assigns probabilities to technology adoption choices based on costs and preferences."
  - Transition Probabilities: "The likelihood that a household switches from one technology to another in a given year."

### ContextualHelpPanel Component (`ContextualHelpPanel.tsx`)

```tsx
import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { getHelpEntry } from "@/components/help/help-content";

interface ContextualHelpPanelProps {
  viewMode: string;
  activeStep?: string;
}

export function ContextualHelpPanel({ viewMode, activeStep }: ContextualHelpPanelProps) {
  const help = getHelpEntry(viewMode, activeStep);
  const [conceptsOpen, setConceptsOpen] = useState(false);

  return (
    <div className="space-y-3">
      {/* Title */}
      <p className="text-sm font-semibold text-slate-900">{help.title}</p>

      {/* Summary */}
      <p className="text-xs leading-normal text-slate-600">{help.summary}</p>

      {/* Tips */}
      <ul className="list-disc space-y-1 pl-4">
        {help.tips.map((tip, i) => (
          <li key={i} className="text-xs text-slate-500">{tip}</li>
        ))}
      </ul>

      {/* Key Concepts (collapsible) */}
      {help.concepts && help.concepts.length > 0 ? (
        <Collapsible open={conceptsOpen} onOpenChange={setConceptsOpen}>
          <CollapsibleTrigger className="flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-800">
            <ChevronRight
              className={cn(
                "h-3 w-3 transition-transform",
                conceptsOpen && "rotate-90",
              )}
            />
            Key Concepts
          </CollapsibleTrigger>
          <CollapsibleContent>
            <dl className="mt-1.5 space-y-1.5 pl-4">
              {help.concepts.map((c) => (
                <div key={c.term}>
                  <dt className="text-xs font-medium text-slate-700">
                    {c.term}
                  </dt>
                  <dd className="text-xs leading-normal text-slate-500">
                    {c.definition}
                  </dd>
                </div>
              ))}
            </dl>
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </div>
  );
}
```

### RightPanel Changes (`RightPanel.tsx`)

**Before (line 20):**
```tsx
<span className="-rotate-90 pt-16 text-xs uppercase tracking-wide text-slate-500">Context</span>
```

**After:**
```tsx
<span className="-rotate-90 pt-16 text-xs uppercase tracking-wide text-slate-500">Help</span>
```

**Before (lines 28-32):**
```tsx
<div className="flex h-10 items-center justify-between border-b border-slate-200 px-3">
  <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Run Context</p>
  <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Collapse right panel">
    <ChevronLeft className="h-4 w-4" />
  </Button>
</div>
```

**After:**
```tsx
<div className="flex h-10 items-center justify-between border-b border-slate-200 px-3">
  <div className="flex items-center gap-1.5">
    <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Help</p>
  </div>
  <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Collapse right panel">
    <ChevronLeft className="h-4 w-4" />
  </Button>
</div>
```

Add `HelpCircle` to the existing `lucide-react` import: `import { ChevronLeft, HelpCircle } from "lucide-react";`

### App.tsx Changes

**Replace right panel children (lines 405-449):**

Before:
```tsx
rightPanel={
  <RightPanel collapsed={isNarrow ? true : rightCollapsed} onToggle={() => setRightCollapsed((current) => !current)}>
    <div className="space-y-3">
      {selectedScenario ? ( ... ) : null}
      <section>Population...</section>
      <section>Template...</section>
      <section>Workspace State...</section>
    </div>
  </RightPanel>
}
```

After:
```tsx
rightPanel={
  <RightPanel collapsed={isNarrow ? true : rightCollapsed} onToggle={() => setRightCollapsed((current) => !current)}>
    <ContextualHelpPanel viewMode={viewMode} activeStep={activeStep} />
  </RightPanel>
}
```

**Dead code cleanup:**
- Remove `Badge` import (line 23) — no remaining usage in App.tsx
- Remove `selectedPopulation` useMemo (lines 81-84) — no remaining usage
- Do NOT remove `selectedTemplate` (used at line 268 in mainPanelContent: `selectedTemplate?.name ?? "selected policy"`)
- Do NOT remove `selectedScenario` (used at line 294 for ResultsOverviewScreen `reformLabel` prop)

### Test Pattern

```tsx
import { render, screen } from "@testing-library/react";

import { ContextualHelpPanel } from "@/components/help/ContextualHelpPanel";

describe("ContextualHelpPanel", () => {
  it("renders Population Builder title for data-fusion viewMode", () => {
    render(<ContextualHelpPanel viewMode="data-fusion" />);
    expect(screen.getByText("Population Builder")).toBeInTheDocument();
  });

  it("renders Portfolio Designer title for portfolio viewMode", () => {
    render(<ContextualHelpPanel viewMode="portfolio" />);
    expect(screen.getByText("Portfolio Designer")).toBeInTheDocument();
  });

  it("renders Results Overview title for results viewMode", () => {
    render(<ContextualHelpPanel viewMode="results" />);
    expect(screen.getByText("Results Overview")).toBeInTheDocument();
  });

  it("renders Comparison Dashboard title for comparison viewMode", () => {
    render(<ContextualHelpPanel viewMode="comparison" />);
    expect(screen.getByText("Comparison Dashboard")).toBeInTheDocument();
  });

  it("renders sub-step help for configuration with activeStep", () => {
    render(<ContextualHelpPanel viewMode="configuration" activeStep="population" />);
    expect(screen.getByText("Select Population")).toBeInTheDocument();
  });

  it("renders tips as list items", () => {
    const { container } = render(<ContextualHelpPanel viewMode="results" />);
    const listItems = container.querySelectorAll("ul > li");
    expect(listItems.length).toBeGreaterThanOrEqual(3);
  });

  it("renders Key Concepts trigger for entries with concepts", () => {
    render(<ContextualHelpPanel viewMode="data-fusion" />);
    expect(screen.getByText("Key Concepts")).toBeInTheDocument();
  });

  it("does not render Key Concepts for entries without concepts", () => {
    render(<ContextualHelpPanel viewMode="progress" />);
    expect(screen.queryByText("Key Concepts")).not.toBeInTheDocument();
  });
});
```

### What NOT to Change

- **RightPanel collapse/expand behavior** — toggle button, Cmd+] keyboard shortcut, localStorage persistence, responsive auto-collapse at < 1024px. All of this is working and untouched.
- **WorkspaceLayout panel sizing** — ResizablePanel `defaultSize`, `minSize`, `maxSize` for the right panel. No changes.
- **LeftPanel content** — WorkflowNavRail, ScenarioCards. No changes. The WorkflowNavRail already shows stage summaries (population ID, portfolio count, run count) so context info removed from the right panel is not lost.
- **Any screen components** — No changes to any screen under `components/screens/`.
- **`selectedTemplate` in App.tsx** — Still used at line 268 in mainPanelContent (`selectedTemplate?.name ?? "selected policy"`). Do NOT remove.
- **`selectedScenario` in App.tsx** — Still used at line 294 for the ResultsOverviewScreen `reformLabel` prop. Do NOT remove.
- **Backend files** — Frontend-only story.

### Existing Tests That Cover Modified Files

| File | Test File | Risk |
|------|-----------|------|
| `App.tsx` | `App.test.tsx` | Low — tests only check auth prompt, no right panel content |
| `RightPanel.tsx` | None | No existing tests to break |

No existing tests assert on "Run Context", "Context", `selectedPopulation`, or `Badge` within the right panel. The changes should not break any existing tests.

### Project Structure Notes

**New files (3):**
- `frontend/src/components/help/help-content.ts`
- `frontend/src/components/help/ContextualHelpPanel.tsx`
- `frontend/src/components/help/__tests__/ContextualHelpPanel.test.tsx`

**Modified files (2):**
- `frontend/src/components/layout/RightPanel.tsx` — header text + icon change
- `frontend/src/App.tsx` — replace right panel children, remove dead code

### References

- [Source: `_bmad-output/planning-artifacts/epics.md:1789-1801` — Story 18.7 acceptance criteria]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:507-530` — Three-column layout: right panel width 280-360px, collapse to 48px icon rail]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:599-603` — MVP priority: "Context sidebar with metadata display — the right column"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:1266-1275` — Right panel: "Shows supporting information for whatever is selected in main content. Auto-updates when selection changes."]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:1197-1200` — Info feedback: "Subtle inline text for contextual help"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:488-500` — Typography: body/labels at text-sm, metadata at text-xs, help content uses leading-normal]
- [Source: `frontend/src/components/layout/RightPanel.tsx` — Current right panel: "Run Context" header, "Context" collapsed label, children-based composition]
- [Source: `frontend/src/App.tsx:405-449` — Current right panel content: scenario card, population, template, workspace state badges]
- [Source: `frontend/src/components/layout/WorkflowNavRail.tsx:44-83` — 4 workflow stages with viewMode mapping]
- [Source: `frontend/src/components/screens/ConfigurationScreen.tsx:26-31` — Configuration sub-steps: population, template, parameters, assumptions]
- [Source: `frontend/src/components/screens/DataFusionWorkbench.tsx:29-37` — Data fusion sub-steps: sources, overlap, method, generate, preview]
- [Source: `frontend/src/components/screens/PortfolioDesignerScreen.tsx:40-44` — Portfolio designer sub-steps: select, compose, review]
- [Source: `frontend/src/components/ui/collapsible.tsx` — Collapsible component wrapping @radix-ui/react-collapsible]
- [Source: `_bmad-output/implementation-artifacts/18-1-implement-workflow-navigation-rail.md` — WorkflowNavRail shows stage summaries]
- [Source: `_bmad-output/implementation-artifacts/18-3-extract-shared-components.md` — Shared components available (story 18.3 dependency)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes

### File List
