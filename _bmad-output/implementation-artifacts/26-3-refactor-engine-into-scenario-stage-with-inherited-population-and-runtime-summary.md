# Story 26.3: Refactor Engine into Scenario stage with inherited population and runtime summary

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want Stage 4 (Scenario) to show inherited primary population context, runtime summary with Live OpenFisca as the default, and strengthened cross-stage validation,
so that I can review my complete scenario configuration before running, understand execution context at a glance, and navigate to fixing stages when validation fails.

## Acceptance Criteria

1. Given Stage 4 (Scenario) renders, then inherited primary population appears as read-only context with name, origin badge (Built-in / Generated / Uploaded), household count, and link back to Population.
2. Given standard web execution, then the runtime summary shows "Live OpenFisca" as the default path and does not show a runtime selector.
3. Given a replay/demo flow is active (when runtime mode is explicitly set to "replay" in a demo context), then the runtime summary shows explicit replay/demo status badge.
4. Given investment decisions are enabled, then Scenario summarizes them (Enabled with model name) and links to Stage 3 for edits (already done in Story 26.2).
5. Given validation fails, then each failing check identifies the owning stage ("Go to Stage X") and the validation gate includes clickable links to navigate to the owning stage.
6. Given all validation checks pass, then the Ready to Run action is enabled and clicking it navigates to the runner sub-view.
7. Given the component renders, then the stage is named "Scenario Configuration" (no "Engine" terminology in user-facing text).

## Tasks / Subtasks

- [ ] Rename EngineStageScreen to ScenarioStageScreen (AC: #7)
  - [ ] Create new file `frontend/src/components/screens/ScenarioStageScreen.tsx` with renamed component
  - [ ] Update module docstring to reference "Scenario Configuration" and remove "Engine" terminology
  - [ ] Update imports and exports from EngineStageScreen to ScenarioStageScreen
  - [ ] Add Story 26.3 reference to docstring

- [ ] Update App.tsx routing to use ScenarioStageScreen (AC: #7)
  - [ ] Replace `<EngineStageScreen />` with `<ScenarioStageScreen />`
  - [ ] Update import from EngineStageScreen to ScenarioStageScreen

- [ ] Add inherited primary population summary section (AC: #1)
  - [ ] Add new section at top of left panel: "Inherited Primary Population"
  - [ ] Show population name as read-only text
  - [ ] Show origin badge (Built-in / Generated / Uploaded) using OriginBadge component
  - [ ] Show household count (e.g., "45,231 households")
  - [ ] Add "Change in Stage 2" link that navigates to "population" stage
  - [ ] Handle null population case (show "No population selected — go to Stage 2")
  - [ ] For data fusion result, show origin as "Generated" badge

- [ ] Add runtime summary section (AC: #2, #3)
  - [ ] Add new section after population: "Runtime"
  - [ ] Show "Live OpenFisca" as default with emerald badge for standard web execution
  - [ ] For demo/replay flow (check if activeScenario.lastRunId exists and run has runtime_mode="replay"), show "Replay" badge with amber color
  - [ ] Add helper text: "Live execution uses OpenFisca engine for real-time policy calculations"
  - [ ] Do NOT add a runtime selector — the standard path is always live

- [ ] Update investment decisions summary (AC: #4)
  - [ ] Already done in Story 26.2 — verify link to Stage 3 works
  - [ ] Ensure formatLogitModelLabel() is used for model name display

- [ ] Strengthen validation checks with stage-fix links (AC: #5)
  - [ ] Update portfolioSelectedCheck message to include "Go to Stage 1 (Policies)"
  - [ ] Update populationSelectedCheck message to include "Go to Stage 2 (Population)"
  - [ ] Update logitModelRequiredCheck message to include "Go to Stage 3 (Investment Decisions)"
  - [ ] Update tasteParametersRequiredCheck message to include "Go to Stage 3 (Investment Decisions)"
  - [ ] Update timeHorizonValidCheck message to include "Adjust time horizon in this stage"

- [ ] Update ValidationGate component with stage navigation (AC: #5, #6)
  - [ ] Make validation check messages render with clickable stage links
  - [ ] Add onStageNavigate callback prop to ValidationGate
  - [ ] Parse stage references from messages (e.g., "Go to Stage 1") and wrap in clickable links
  - [ ] Ensure Ready to Run button navigates to "results" with subView "runner"

- [ ] Update RunSummaryPanel for Scenario stage (AC: #2, #3, #4)
  - [ ] Add runtime summary row showing "Live OpenFisca" or "Replay" badge
  - [ ] Show runtime mode based on lastRunId lookup from results list
  - [ ] If no lastRunId, show "Live OpenFisca" as default
  - [ ] Keep existing summary rows (Type, Policy Set, Population, Time horizon, Inv. decisions, Seed, Estimated runs)

- [ ] Update help content for Scenario stage (AC: #1, #2, #3)
  - [ ] Update "scenario" help-content.ts entry to reference inherited population and runtime summary
  - [ ] Add tips about inherited primary population context
  - [ ] Add tips about runtime default (Live OpenFisca) and replay badge for demos
  - [ ] Update concepts to include "Runtime Mode" and "Inherited Population"

- [ ] Update tests for ScenarioStageScreen (AC: #1, #2, #3, #7)
  - [ ] Rename test file from EngineStageScreen.test.tsx to ScenarioStageScreen.test.tsx
  - [ ] Update all component references from EngineStageScreen to ScenarioStageScreen
  - [ ] Add test for inherited population section rendering
  - [ ] Add test for population origin badge display
  - [ ] Add test for "Change in Stage 2" link navigation
  - [ ] Add test for runtime summary showing "Live OpenFisca" by default
  - [ ] Add test for runtime summary showing "Replay" badge when applicable
  - [ ] Add test for validation messages with stage-fix links
  - [ ] Verify existing tests for time horizon, seed, discount rate, investment decisions still pass

- [ ] Update RunSummaryPanel tests (AC: #2, #3)
  - [ ] Add test for runtime summary row showing "Live OpenFisca"
  - [ ] Add test for runtime summary showing "Replay" badge
  - [ ] Add test for default runtime when no lastRunId

- [ ] Update ValidationGate tests (AC: #5, #6)
  - [ ] Add test for clickable stage links in validation messages
  - [ ] Add test for onStageNavigate callback when stage link is clicked
  - [ ] Add test for Ready to Run button navigation

- [ ] Non-regression: verify existing functionality preserved
  - [ ] Verify scenario name editing still works
  - [ ] Verify Save Scenario button still works
  - [ ] Verify Clone Scenario button still works
  - [ ] Verify time horizon controls still work
  - [ ] Verify seed controls still work
  - [ ] Verify discount rate slider still works
  - [ ] Verify population dropdowns still work (primary + sensitivity)
  - [ ] Verify validation checks still execute correctly
  - [ ] Verify RunSummaryPanel still displays correctly

## Dev Notes

### Architecture Context

**UX Revision 4.1 (from UX-DR12):** "Stage 4 (Scenario) must show inherited primary population context, own simulation mode and horizon controls, show runtime summary with Live OpenFisca default status, and serve as the cross-stage integration validation gate."

**Key Design Decision:** This story completes the Stage 4 redesign by:
1. Renaming "Engine" → "Scenario" for clarity
2. Showing inherited primary population as read-only context (not re-selectable)
3. Surfacing runtime mode truthfully via summary (Live OpenFisca default, Replay badge for demos)
4. Adding stage-fix navigation to validation errors

**No Runtime Selector:** Standard web execution always uses live runtime. A runtime selector is NOT added — analysts see the runtime mode truthfully via summary copy and badges. This is intentional per the UX spec.

**Cross-Stage Validation:** Stage 4 is the integration gate where all validation checks are evaluated together. Failing checks should link to the owning stage for quick navigation.

### Current State (After Story 26.2)

**EngineStageScreen Structure:**
```typescript
// Two-column layout: left config form + right panel (RunSummaryPanel + ValidationGate)
// Left sections:
// - Time Horizon (startYear, endYear)
// - Population (primary + sensitivity dropdowns)
// - Random Seed (toggle + value input)
// - Investment Decisions Summary (read-only, link to Stage 3)
// - Discount Rate (slider + number input)
// Right panel:
// - RunSummaryPanel (scenario summary card)
// - ValidationGate (validation checklist)
```

**Investment Decisions Summary (already added in Story 26.2):**
```typescript
// Shows "Disabled" or "Enabled — {model name}"
// "Configure in Stage 3" link navigates to investment-decisions stage
```

**Validation Checks (validationChecks.ts):**
- `portfolioSelectedCheck` — "No portfolio selected. Go to Stage 1 to compose a portfolio."
- `populationSelectedCheck` — "No population selected. Go to Stage 2 to select a population."
- `timeHorizonValidCheck` — "End year must be greater than start year" or "Time horizon exceeds 50 years"
- `logitModelRequiredCheck` — "Investment decisions require a logit model. Configure in Stage 3."
- `tasteParametersRequiredCheck` — "Investment decisions require taste parameters. Configure in Stage 3."
- `investmentDecisionsCalibratedCheck` — Warning when enabled but not calibrated
- `memoryPreflightCheck` — Memory check async validation

### File: `frontend/src/components/screens/ScenarioStageScreen.tsx` (NEW - RENAMED)

**Component Structure Changes:**

1. **Rename and Update Docstring:**
```typescript
/** ScenarioStageScreen — Stage 4: Scenario Configuration.
 *
 * Two-column layout: left config form (inherited population, time horizon,
 * seed, discount rate) + right panel (RunSummaryPanel + ValidationGate).
 * Toolbar shows scenario name (editable), Save, and Clone.
 *
 * Story 20.5 — AC-1, AC-2, AC-3, AC-4.
 * Story 26.2 — AC-3: Investment decisions moved to dedicated Stage 3.
 * Story 26.3 — AC-1, AC-2, AC-3, AC-7: Renamed from EngineStageScreen,
 * added inherited population summary and runtime summary.
 */
```

2. **Add Inherited Primary Population Section:**
```typescript
{/* Inherited Primary Population — Story 26.3 */}
<section className="space-y-3">
  <div className="flex items-center justify-between">
    <h3 className="text-sm font-semibold text-slate-700">Primary Population</h3>
    <span className="text-xs text-slate-400">Inherited from Stage 2</span>
  </div>

  {primaryPopulation ? (
    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900">{primaryPopulation.name}</span>
          <OriginBadge origin={primaryPopulation.origin} />
        </div>
        <p className="text-xs text-slate-600">
          {primaryPopulation.households.toLocaleString()} households
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 text-xs text-blue-600 hover:text-blue-700 px-2"
        onClick={() => navigateTo("population")}
      >
        Change in Stage 2
      </Button>
    </div>
  ) : (
    <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
      <p className="text-sm text-amber-800">No population selected.</p>
      <Button
        variant="outline"
        size="sm"
        className="mt-2 h-7 text-xs"
        onClick={() => navigateTo("population")}
      >
        Go to Stage 2 to select a population
      </Button>
    </div>
  )}
</section>
```

3. **Add Runtime Summary Section:**
```typescript
{/* Runtime — Story 26.3 */}
<section className="space-y-3">
  <h3 className="text-sm font-semibold text-slate-700">Runtime</h3>
  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
    <Badge variant="outline" className="text-xs border-emerald-600 text-emerald-700">
      Live OpenFisca
    </Badge>
    <p className="text-xs text-slate-600 flex-1">
      Live execution uses OpenFisca engine for real-time policy calculations.
    </p>
    {lastRuntimeMode === "replay" && (
      <Badge variant="outline" className="text-xs border-amber-600 text-amber-700">
        Replay
      </Badge>
    )}
  </div>
</section>
```

4. **Helper to Find Primary Population:**
```typescript
// Find primary population from populations or dataFusionResult
const primaryPopulation = useMemo(() => {
  const primaryId = activeScenario?.populationIds[0];
  if (!primaryId) return null;

  // Check dataFusionResult first
  if (primaryId === "data-fusion-result" && dataFusionResult) {
    return {
      id: "data-fusion-result",
      name: "Fused Population",
      households: dataFusionResult.summary.record_count,
      origin: "generated" as const,
    };
  }

  // Check built-in/uploaded populations
  return populations.find((p) => p.id === primaryId) ?? null;
}, [activeScenario?.populationIds, populations, dataFusionResult]);

// Get runtime mode from last run (for replay badge)
const lastRuntimeMode = useMemo(() => {
  if (!activeScenario?.lastRunId) return null;
  const lastRun = results.find((r) => r.run_id === activeScenario.lastRunId);
  return lastRun?.runtime_mode ?? null;
}, [activeScenario?.lastRunId, results]);
```

5. **Remove Population Editing Section:**
The existing Population section with dropdowns for primary and secondary populations should be modified:
- Keep the section for adding/removing sensitivity populations (secondary population)
- Remove the primary population dropdown (now shown as read-only inherited context)
- Update section label to "Sensitivity Population (Optional)"

**Modified Population Section:**
```typescript
{/* Sensitivity Population (Optional) — Story 26.3 */}
<section className="space-y-3">
  <h3 className="text-sm font-semibold text-slate-700">Sensitivity Population (Optional)</h3>
  {/* Secondary population dropdown and add/remove controls */}
  {/* Same as current secondary population logic */}
</section>
```

### File: `frontend/src/App.tsx` (MODIFY)

**Update Import and Routing:**
```typescript
// Replace import:
import { ScenarioStageScreen } from "@/components/screens/ScenarioStageScreen";

// Update mainPanelContent (line 211):
{activeStage === "scenario" ? <ScenarioStageScreen /> : null}
```

### File: `frontend/src/components/engine/RunSummaryPanel.tsx` (MODIFY)

**Add Runtime Summary Row:**
```typescript
{/* Runtime — Story 26.3 */}
<div className="flex justify-between">
  <span className="text-slate-500">Runtime</span>
  <span className="flex items-center gap-2">
    <Badge variant="outline" className="text-xs border-emerald-600 text-emerald-700">
      Live OpenFisca
    </Badge>
    {runtime_mode === "replay" && (
      <Badge variant="outline" className="text-xs border-amber-600 text-amber-700">
        Replay
      </Badge>
    )}
  </span>
</div>
```

**Props Update:**
```typescript
interface RunSummaryPanelProps {
  scenario: WorkspaceScenario | null;
  populations: Population[];
  portfolios: PortfolioListItem[];
  dataFusionResult: GenerationResult | null;
  results: ResultListItem[];  // Add results prop for runtime lookup
  runtime_mode?: "live" | "replay" | null;  // Or derive from scenario.lastRunId
}
```

### File: `frontend/src/components/engine/validationChecks.ts` (MODIFY)

**Update Validation Messages with Stage References:**

```typescript
// portfolioSelectedCheck
message: passed ? "" : "No portfolio selected. Go to Stage 1 (Policies) to compose a portfolio.",

// populationSelectedCheck
message: passed ? "" : "No population selected. Go to Stage 2 (Population) to select a population.",

// timeHorizonValidCheck
message: startYear >= endYear
  ? "End year must be greater than start year. Adjust in this stage."
  : "Time horizon exceeds 50 years — reduce the range. Adjust in this stage.",

// logitModelRequiredCheck
message: hasValidModel ? "" : "Investment decisions require a logit model. Go to Stage 3 (Investment Decisions).",

// tasteParametersRequiredCheck
message: hasPriceSensitivity && hasRangeAnxiety && hasEnvPreference
  ? ""
  : "Investment decisions require taste parameters. Go to Stage 3 (Investment Decisions).",
```

### File: `frontend/src/components/engine/ValidationGate.tsx` (MODIFY)

**Add Stage Navigation Support:**

```typescript
interface ValidationGateProps {
  context: ValidationContext;
  onRun: () => void;
  runLoading: boolean;
  onStageNavigate?: (stage: StageKey) => void;  // Story 26.3
}

// In component body, parse stage references from messages:
const parseStageLinks = (message: string) => {
  // Match "Stage 1", "Stage 2", etc. and wrap in clickable links
  const parts = message.split(/(Stage \d)/g);
  return parts.map((part, i) => {
    if (part.match(/Stage \d/)) {
      const stageNum = parseInt(part.split(" ")[1], 10);
      const stageKey: StageKey[] = ["", "policies", "population", "investment-decisions", "scenario"];
      return (
        <button
          key={i}
          className="text-blue-600 underline hover:text-blue-700"
          onClick={() => props.onStageNavigate?.(stageKey[stageNum])}
        >
          {part}
        </button>
      );
    }
    return part;
  });
};
```

### File: `frontend/src/components/help/help-content.ts` (MODIFY)

**Update "scenario" Entry:**
```typescript
"scenario": {
  title: "Scenario Configuration",
  summary: "Review your inherited primary population, configure time horizon and execution settings, and run cross-stage validation. This stage is the integration gate before execution.",
  tips: [
    "Primary population is inherited from Stage 2 — click 'Change in Stage 2' to modify your selection",
    "Runtime shows 'Live OpenFisca' for standard web execution — no runtime selector needed",
    "Replay badge appears for demo/replay runs from saved scenarios",
    "Sensitivity population is optional — add it for comparison analysis",
    "Set Start and End year — the 'N-year projection' label updates automatically. Max 50 years.",
    "Investment decisions show a read-only summary here — click 'Configure in Stage 3' to edit them",
    "The right panel shows a live validation checklist — all red checks must be resolved before Run is enabled.",
    "Click 'Go to Stage X' links in validation messages to jump directly to the fixing stage",
    "Save Scenario persists the full configuration (portfolio + population + settings) to your saved list.",
    "Clone Scenario creates a copy with '(copy)' appended — useful for sensitivity analysis variants.",
    "The memory preflight check runs when you click Run — it estimates if your population fits in RAM.",
  ],
  concepts: [
    { term: "Inherited Population", definition: "The primary population selected in Stage 2 that will be used for this scenario. Shown as read-only context in Stage 4 to prevent accidental changes during final review." },
    { term: "Runtime Mode", definition: "The execution mode for the simulation: 'live' uses OpenFisca for real-time calculations (standard web path), 'replay' reuses cached results from a previous run (demo/debug path)." },
    { term: "Cross-stage validation", definition: "A checklist that verifies portfolio, population, time horizon, investment decisions, and memory constraints are all satisfied before the simulation can run." },
    { term: "Sensitivity Population", definition: "An optional second population used for comparison analysis. Running with two populations executes the same scenario on both populations for side-by-side results." },
  ],
},
```

### Testing Standards

**Frontend Component Tests:** `frontend/src/components/screens/__tests__/ScenarioStageScreen.test.tsx` (RENAMED)

Required test coverage for Story 26.3:
- Test inherited population section renders with name, origin badge, household count
- Test inherited population "Change in Stage 2" link navigates to population stage
- Test null population state shows "Go to Stage 2" button
- Test data fusion result shows as "Generated" origin badge
- Test runtime summary shows "Live OpenFisca" badge by default
- Test runtime summary shows "Replay" badge when lastRunId has runtime_mode="replay"
- Test sensitivity population section still works (add/remove secondary)
- Test time horizon controls still work
- Test seed controls still work
- Test discount rate slider still works
- Test validation messages include stage references
- Test "Ready to Run" button is disabled when validation fails
- Test "Ready to Run" button navigates to "results/runner" when clicked

**Frontend Component Tests:** `frontend/src/components/engine/__tests__/RunSummaryPanel.test.tsx` (MODIFY)

Added test coverage:
- Test runtime summary row shows "Live OpenFisca" badge
- Test runtime summary row shows "Replay" badge when runtime_mode="replay"
- Test runtime summary shows default when no runtime_mode provided

**Frontend Component Tests:** `frontend/src/components/engine/__tests__/ValidationGate.test.tsx` (MODIFY)

Added test coverage:
- Test validation messages render with stage links
- Test clicking stage link calls onStageNavigate callback
- Test "Ready to Run" button calls onRun callback
- Test "Ready to Run" button is disabled when validation fails

### Project Structure Notes

**Frontend Files to Create:**
- `frontend/src/components/screens/ScenarioStageScreen.tsx` — Renamed from EngineStageScreen.tsx
- `frontend/src/components/screens/__tests__/ScenarioStageScreen.test.tsx` — Renamed from EngineStageScreen.test.tsx

**Frontend Files to Modify:**
- `frontend/src/App.tsx` — Update import and routing for ScenarioStageScreen
- `frontend/src/components/engine/RunSummaryPanel.tsx` — Add runtime summary row
- `frontend/src/components/engine/validationChecks.ts` — Update validation messages with stage references
- `frontend/src/components/engine/ValidationGate.tsx` — Add stage navigation support
- `frontend/src/components/help/help-content.ts` — Update "scenario" help entry

**Files to Delete (after rename):**
- `frontend/src/components/screens/EngineStageScreen.tsx` — Replaced by ScenarioStageScreen.tsx
- `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx` — Replaced by ScenarioStageScreen.test.tsx

**Files to Verify (no changes expected, but verify compatibility):**
- `frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx` — Should work unchanged
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — Should work unchanged
- `frontend/src/components/population/OriginBadge.tsx` — Reused for population origin display

### Implementation Order Recommendation

1. **Phase 1: Rename Component and Update Routing** (Foundation)
   - Create ScenarioStageScreen.tsx as copy of EngineStageScreen.tsx
   - Update module docstring and component name
   - Update App.tsx import and routing
   - Run tests to verify rename didn't break anything
   - Delete old EngineStageScreen.tsx and test file

2. **Phase 2: Add Inherited Population Section** (AC-1)
   - Add primaryPopulation helper (useMemo)
   - Add inherited population section to left panel
   - Add "Change in Stage 2" navigation button
   - Handle null population state
   - Handle dataFusionResult as generated population
   - Add OriginBadge import and usage
   - Update tests for inherited population rendering

3. **Phase 3: Add Runtime Summary Section** (AC-2, AC-3)
   - Add lastRuntimeMode helper (useMemo from results)
   - Add runtime summary section to left panel
   - Show "Live OpenFisca" badge by default
   - Show "Replay" badge when applicable
   - Update tests for runtime summary rendering

4. **Phase 4: Update Validation with Stage Navigation** (AC-5, AC-6)
   - Update validationChecks.ts messages with stage references
   - Update ValidationGate component to parse stage links
   - Add onStageNavigate callback to ValidationGate
   - Update ScenarioStageScreen to pass onStageNavigate to ValidationGate
   - Update tests for clickable stage links

5. **Phase 5: Update RunSummaryPanel** (AC-2, AC-3)
   - Add runtime summary row to RunSummaryPanel
   - Pass runtime_mode prop or derive from scenario.lastRunId
   - Update RunSummaryPanel tests

6. **Phase 6: Update Help Content** (AC-1, AC-2, AC-3)
   - Update "scenario" help entry with inherited population and runtime tips
   - Add new concepts for inherited population and runtime mode

7. **Phase 7: Integration and Regression** (Validation)
   - Test full Scenario stage render with all sections
   - Test navigation flow: Scenario → Population → back to Scenario
   - Test validation messages with stage links navigate correctly
   - Test Ready to Run button navigation
   - Verify existing controls (time horizon, seed, discount rate) still work
   - Non-regression testing for all existing EngineStageScreen functionality

### Key Implementation Decisions

**Rename Strategy:**
- Create new ScenarioStageScreen.tsx as a copy, then delete EngineStageScreen.tsx
- This ensures clean git history (rename is detected) and allows gradual migration
- All imports and tests are updated in one pass

**Population Display:**
- Primary population is read-only inherited context
- Uses OriginBadge component (existing) for visual differentiation
- "Change in Stage 2" link for easy navigation back
- Data fusion result shows as "Generated" origin

**Runtime Display:**
- Standard path: Always show "Live OpenFisca" (emerald badge)
- Replay path: Show "Replay" badge (amber) when lastRunId has runtime_mode="replay"
- No runtime selector added — intentional per UX spec

**Sensitivity Population:**
- Secondary population dropdown remains editable
- Section renamed to "Sensitivity Population (Optional)"
- Primary population selection is now read-only (inherited)

**Validation Navigation:**
- Stage references in messages are parsed and rendered as clickable links
- onStageNavigate callback allows ValidationGate to trigger navigation
- Pattern: "Go to Stage 1 (Policies)" → clickable "Stage 1" link

### Out of Scope

To avoid scope creep and conflicts with future stories:
- **Simulation mode controls** (annual vs horizon_step) — not implemented in this story, future work
- **Runtime selector UI** — intentionally NOT added, standard path is always live
- **Calibration UI** — separate feature, out of scope
- **Population schema validation** — handled in Stage 2, not duplicated here
- **Manifest viewer** — Story 26.4 will add dedicated manifest viewing in Stage 5

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-26] - Epic 26 requirements
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] - UX design specification (Revision 4.1, UX-DR12, Stage 4 section)
- [Source: frontend/src/components/screens/EngineStageScreen.tsx] - Current stage screen (being renamed)
- [Source: frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx] - Stage 3 screen (Story 26.2)
- [Source: frontend/src/components/population/OriginBadge.tsx] - Population origin badge component
- [Source: frontend/src/components/engine/RunSummaryPanel.tsx] - Run summary panel component
- [Source: frontend/src/components/engine/validationChecks.ts] - Validation check definitions
- [Source: frontend/src/components/engine/ValidationGate.tsx] - Validation gate component
- [Source: frontend/src/types/workspace.ts] - StageKey, WorkspaceScenario, EngineConfig types
- [Source: frontend/src/api/types.ts] - PopulationLibraryItem, origin types

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

Story 26.3 created with comprehensive developer context:

**Context Sources Analyzed:**
- Story 26.1 completion notes — five-stage migration, hash routing, terminology changes
- Story 26.2 completion notes — Investment Decisions stage extraction, validation messages
- UX design specification (Revision 4.1) — Stage 4 requirements, inherited population, runtime summary
- EngineStageScreen.tsx — current component structure, sections, controls
- validationChecks.ts — validation check definitions and current messages
- RunSummaryPanel.tsx — summary panel structure and content
- workspace.ts — StageKey types, EngineConfig, WorkspaceScenario
- OriginBadge.tsx — population origin badge component
- App.tsx — routing structure and mainPanelContent logic

**Key Design Decisions Documented:**
- Rename EngineStageScreen → ScenarioStageScreen for clarity
- Inherited primary population as read-only context (not re-selectable)
- Runtime summary shows Live OpenFisca default (no runtime selector)
- Validation messages include clickable stage-fix links
- Sensitivity population remains editable (secondary only)

**Testing Strategy:**
- Rename test file from EngineStageScreen.test.tsx to ScenarioStageScreen.test.tsx
- Add tests for inherited population section
- Add tests for runtime summary display
- Add tests for clickable stage links in validation
- Add tests for Ready to Run navigation
- Update RunSummaryPanel and ValidationGate tests

**Implementation Order:**
1. Rename component and update routing
2. Add inherited population section
3. Add runtime summary section
4. Update validation with stage navigation
5. Update RunSummaryPanel
6. Update help content
7. Integration and regression testing

Status set to: ready-for-dev
