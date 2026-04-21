# Story 26.2: Extract Investment Decisions into a dedicated Stage 3 with skip-when-disabled routing

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want investment decisions to be configured in a dedicated Stage 3 (Investment Decisions) that can be skipped when disabled,
so that I can focus on core scenario configuration in Stage 4 (Scenario) and manage behavioral modeling as an optional advanced feature.

## Acceptance Criteria

1. Given Stage 3 renders with investment decisions disabled (`investmentDecisionsEnabled: false`), then the analyst sees the enable toggle and can continue directly to Scenario without being forced to configure investment decisions.
2. Given investment decisions are enabled in Stage 3, then the full four-step wizard (Enable, Model, Parameters, Review) renders and works correctly with all existing functionality preserved.
3. Given Stage 4 (Scenario) renders, then it does not include investment-decision editing controls—only a summary of the current state with a link back to Stage 3 for edits.
4. Given investment decisions are enabled and configured in Stage 3, then the nav rail summary shows the selected model (e.g., "Multinomial Logit") or calibration summary when available.
5. Given investment decisions are disabled, then cross-stage validation treats Stage 3 as skippable—the validation gate in Stage 4 should pass without requiring investment-decision configuration.
6. Given Stage 3 is the active stage, then the help panel shows the "Investment Decisions" help entry with appropriate content about the dedicated stage.
7. Given the analyst navigates between stages, then the wizard state (active step, visited steps) resets when leaving Stage 3 and re-enters at the appropriate step based on the current engineConfig state.

## Tasks / Subtasks

- [ ] Create InvestmentDecisionsStageScreen component (AC: #1, #2, #7)
  - [ ] Create new file `frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx`
  - [ ] Add null state handling (no active scenario → show "Create a scenario first" with CTA)
  - [ ] Add disabled-state view with enable toggle, optional-behavior summary copy, and "Continue to Scenario" action
  - [ ] Add enabled-state view with full InvestmentDecisionsWizard (reuse existing component)
  - [ ] Add "Back to Population" and "Continue to Scenario" navigation buttons
  - [ ] Ensure wizard state resets appropriately when stage is re-entered
  - [ ] Add module docstring referencing Story 26.2

- [ ] Update EngineStageScreen to remove investment-decision editor (AC: #3)
  - [ ] Remove the Investment Decisions section (lines 333-339 in current file)
  - [ ] Replace with read-only summary: enabled status, model name, link to Stage 3 for editing
  - [ ] Keep all other EngineStageScreen functionality (time horizon, population, seed, discount rate, validation gate)
  - [ ] Update module docstring to remove investment-decision editing reference

- [ ] Update WorkflowNavRail summary for investment-decisions stage (AC: #4)
  - [ ] Update `getSummary()` function to return proper summary states:
    - Disabled → "Disabled"
    - Enabled without model → "Incomplete"
    - Enabled with model → Model name (e.g., "Multinomial Logit")
  - [ ] Verify summary updates reactively when engineConfig changes

- [ ] Update validation checks for Stage 3 skip-when-disabled (AC: #5)
  - [ ] Verify `logitModelRequiredCheck` passes when `investmentDecisionsEnabled` is false (already does this)
  - [ ] Verify `tasteParametersRequiredCheck` passes when `investmentDecisionsEnabled` is false (already does this)
  - [ ] Verify `investmentDecisionsCalibratedCheck` passes when `investmentDecisionsEnabled` is false (already does this)
  - [ ] Add validation check message "Configure in Stage 3" when investment decisions are enabled but incomplete

- [ ] Update App.tsx routing for investment-decisions stage (AC: #1, #2, #3)
  - [ ] Replace placeholder div with InvestmentDecisionsStageScreen import and rendering
  - [ ] Ensure proper stage routing: `activeStage === "investment-decisions"` renders InvestmentDecisionsStageScreen

- [ ] Update help content for investment-decisions stage (AC: #6)
  - [ ] Update `help-content.ts` "investment-decisions" entry to reflect dedicated stage
  - [ ] Replace "Coming in Story 26.2" tip with actual stage guidance
  - [ ] Add tips about skip-when-disabled behavior and Continue to Scenario action

- [ ] Add InvestmentDecisionsStageScreen tests (AC: #1, #2, #7)
  - [ ] Test null state (no active scenario)
  - [ ] Test disabled state render (enable toggle, summary copy, Continue to Scenario button)
  - [ ] Test enabled state render (wizard appears)
  - [ ] Test enable toggle switches to wizard view
  - [ ] Test wizard functionality preserved (all 4 steps work)
  - [ ] Test Continue to Scenario navigation
  - [ ] Test Back to Population navigation
  - [ ] Test wizard state reset on re-entry

- [ ] Update EngineStageScreen tests for investment decision summary (AC: #3)
  - [ ] Remove tests for investment decision editing (wizard toggle, wizard render)
  - [ ] Add tests for read-only summary display
  - [ ] Add test for "Configure in Stage 3" link navigates to investment-decisions stage
  - [ ] Verify existing EngineStageScreen tests still pass

- [ ] Update WorkflowNavRail tests for investment-decisions summary (AC: #4)
  - [ ] Add tests for "Disabled" summary when investmentDecisionsEnabled is false
  - [ ] Add tests for "Incomplete" summary when enabled but no model selected
  - [ ] Add tests for model name summary when enabled and model selected

- [ ] Update integration tests for Stage 3 navigation (AC: #5, #7)
  - [ ] Test navigation flow: Population → Investment Decisions (disabled) → Scenario
  - [ ] Test navigation flow: Population → Investment Decisions (enabled) → Scenario
  - [ ] Test validation passes when Stage 3 is skipped (disabled)
  - [ ] Test cross-stage validation link from Scenario to Investment Decisions

- [ ] Update analyst-journey e2e tests for five-stage flow
  - [ ] Update investment decision steps to use dedicated Stage 3
  - [ ] Test skip-when-disabled path
  - [ ] Test configure-and-continue path

- [ ] Non-regression: verify existing functionality preserved
  - [ ] Verify InvestmentDecisionsWizard still works when embedded in new stage
  - [ ] Verify existing investment-decision tests still pass
  - [ ] Verify validation checks work correctly in new flow
  - [ ] Verify RunSummaryPanel still shows correct investment-decision status

## Dev Notes

### Architecture Context

**UX Revision 4.1 (from UX-DR11):** "Investment Decisions must be a dedicated Stage 3 that can be skipped when decision behavior is disabled, not a sub-wizard embedded in the Scenario/Engine stage."

**Key Design Decision:** This story extracts investment-decision configuration from EngineStageScreen (which will be renamed to ScenarioStageScreen in Story 26.3) into its own dedicated stage. The existing InvestmentDecisionsWizard component is reused without modification—this story is primarily about routing and stage separation, not rewriting wizard logic.

**Stage Completion Logic (from Story 26.1):**
- Stage 3 is complete when `activeScenario` exists AND either:
  - `investmentDecisionsEnabled` is false (disabled = complete), OR
  - `investmentDecisionsEnabled` is true AND `logitModel` is not null
- This allows the stage to be marked complete when disabled (skip behavior)

### Current State (After Story 26.1)

**Five-Stage Structure:**
```typescript
// frontend/src/types/workspace.ts
export type StageKey = "policies" | "population" | "investment-decisions" | "scenario" | "results";
```

**Current App.tsx routing (lines 209-213):**
```typescript
{activeStage === "investment-decisions" ? (
  <div className="flex items-center justify-center p-12 text-slate-500" data-testid="investment-decisions-placeholder">
    <p>Investment Decisions stage — coming in Story 26.2</p>
  </div>
) : null}
```

**Current EngineStageScreen investment-decision section (lines 333-339):**
```typescript
{/* Investment Decisions */}
<section className="space-y-3">
  <InvestmentDecisionsWizard
    engineConfig={engineConfig}
    onUpdateEngineConfig={updateEngineConfig}
  />
</section>
```

**Current WorkflowNavRail investment-decisions summary (lines 96-102):**
```typescript
case "investment-decisions": {
  if (!activeScenario) return null;
  if (!activeScenario.engineConfig.investmentDecisionsEnabled) {
    return "Disabled";
  }
  return activeScenario.engineConfig.logitModel ?? null;
}
```

**Current validation checks (validationChecks.ts):**
- `logitModelRequiredCheck` — requires model when enabled (line 112-133)
- `tasteParametersRequiredCheck` — requires taste params when enabled (line 136-168)
- `investmentDecisionsCalibratedCheck` — warning when enabled but not calibrated (line 93-109)

All three checks already pass when `investmentDecisionsEnabled` is false—no changes needed to validation logic, only validation messages may need updating.

### File: `frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx` (NEW)

**Component Structure:**

```typescript
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** InvestmentDecisionsStageScreen — Stage 3: Investment Decisions Configuration.
 *
 * Dedicated stage for behavioral response modeling. When disabled, shows a summary
 * with enable toggle and Continue to Scenario action. When enabled, renders the
 * full InvestmentDecisionsWizard (Enable, Model, Parameters, Review steps).
 *
 * Story 26.2 — AC-1, AC-2, AC-7.
 */

import { useAppState } from "@/contexts/AppContext";
import { InvestmentDecisionsWizard } from "@/components/engine/InvestmentDecisionsWizard";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function InvestmentDecisionsStageScreen() {
  const {
    activeScenario,
    updateScenarioField,
    navigateTo,
  } = useAppState();

  // ============================================================================
  // Null state
  // ============================================================================

  if (!activeScenario) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
        <p className="text-slate-500">No active scenario.</p>
        <Button onClick={() => navigateTo("scenario")}>Go to Scenario to create one</Button>
      </div>
    );
  }

  const engineConfig = activeScenario.engineConfig;
  const isEnabled = engineConfig.investmentDecisionsEnabled;

  const updateEngineConfig = (cfg: typeof engineConfig) => {
    updateScenarioField("engineConfig", cfg);
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="flex flex-col h-full">
      {/* ─── Toolbar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white">
        <h1 className="text-xl font-semibold text-slate-900">Investment Decisions</h1>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigateTo("population")}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to Population
          </Button>
          <Button
            size="sm"
            onClick={() => navigateTo("scenario")}
          >
            Continue to Scenario
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* ─── Body ────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-6">
        {isEnabled ? (
          // Enabled: show wizard
          <div className="max-w-2xl">
            <InvestmentDecisionsWizard
              engineConfig={engineConfig}
              onUpdateEngineConfig={updateEngineConfig}
            />
          </div>
        ) : (
          // Disabled: show summary with enable toggle
          <div className="max-w-2xl space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Investment Decisions</h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Investment decisions model household technology adoption choices (e.g., electric vehicles,
                heat pumps) using behavioral economics. This is an optional advanced feature.
              </p>
            </div>

            <div className="p-6 bg-slate-50 rounded-lg border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Enable investment decisions</h3>
                  <p className="text-xs text-slate-500">Model household technology adoption</p>
                </div>
                <Switch
                  checked={isEnabled}
                  onChange={(e) => updateEngineConfig({
                    ...engineConfig,
                    investmentDecisionsEnabled: e.target.checked,
                    logitModel: e.target.checked ? "multinomial_logit" : null,
                  })}
                  aria-label="Toggle investment decisions"
                />
              </div>

              <div className="pt-4 border-t border-slate-200">
                <p className="text-xs text-slate-500 mb-3">
                  When enabled, you can configure the logit model and taste parameters that govern
                  household behavioral responses to policy changes.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateTo("scenario")}
                >
                  Continue to Scenario (disabled)
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>

            <div className="text-sm text-slate-600">
              <p className="font-medium text-slate-700 mb-1">What are investment decisions?</p>
              <p className="text-xs">
                Investment decisions use discrete choice models (logit) to simulate how households
                choose between technologies like vehicles and heating systems based on costs and
                preferences. This adds behavioral realism to policy analysis but requires additional
                configuration and calibration data.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Key Implementation Notes:**
- The wizard state (`activeStep`, `visitedSteps`) is local to InvestmentDecisionsWizard and resets on unmount
- When re-entering Stage 3, the wizard shows the appropriate step based on `engineConfig` state (disabled → Enable step, enabled with no model → Model step, etc.)
- Navigation buttons use `navigateTo("population")` and `navigateTo("scenario")` for stage transitions

### File: `frontend/src/components/screens/EngineStageScreen.tsx` (MODIFY)

**Remove Investment Decisions section (lines 333-339):**
```typescript
// REMOVE THIS SECTION:
{/* Investment Decisions */}
<section className="space-y-3">
  <InvestmentDecisionsWizard
    engineConfig={engineConfig}
    onUpdateEngineConfig={updateEngineConfig}
  />
</section>
```

**Replace with read-only summary (insert after Discount Rate section):**
```typescript
<Separator />

{/* Investment Decisions Summary */}
<section className="space-y-3">
  <div className="flex items-center justify-between">
    <h3 className="text-sm font-semibold text-slate-700">Investment Decisions</h3>
    <Button
      variant="ghost"
      size="sm"
      className="h-6 text-xs text-blue-600 hover:text-blue-700 px-2"
      onClick={() => navigateTo("investment-decisions")}
    >
      Configure in Stage 3
    </Button>
  </div>
  <div className="text-xs text-slate-600">
    {engineConfig.investmentDecisionsEnabled ? (
      <span>
        Enabled — {engineConfig.logitModel ? engineConfig.logitModel.replace(/_/g, " ") : "no model selected"}
      </span>
    ) : (
      <span>Disabled</span>
    )}
  </div>
</section>
```

**Update module docstring (line 3-10):**
```typescript
/** EngineStageScreen — Stage 4: Scenario Configuration.
 *
 * Two-column layout: left config form (time horizon, population, seed,
 * discount rate) + right panel (RunSummaryPanel + ValidationGate).
 * Toolbar shows scenario name (editable), Save, and Clone.
 *
 * Story 20.5 — AC-1, AC-2, AC-3, AC-4.
 * Story 26.2 — AC-3: Investment decisions moved to dedicated Stage 3.
 */
```

### File: `frontend/src/App.tsx` (MODIFY)

**Replace placeholder with InvestmentDecisionsStageScreen (lines 209-213):**

```typescript
// Add import at top:
import { InvestmentDecisionsStageScreen } from "@/components/screens/InvestmentDecisionsStageScreen";

// Replace routing:
{activeStage === "investment-decisions" ? <InvestmentDecisionsStageScreen /> : null}
```

### File: `frontend/src/components/help/help-content.ts` (MODIFY)

**Update "investment-decisions" entry (lines 198-206):**

```typescript
"investment-decisions": {
  title: "Investment Decisions",
  summary: "Configure behavioral response models for household technology adoption (vehicles, heating systems). Optional advanced feature—skip when disabled.",
  tips: [
    "Investment decisions are disabled by default—enable the toggle to configure behavioral modeling",
    "When enabled, you must select a logit model and configure taste parameters",
    "The four-step wizard guides you through: Enable, Model selection, Parameters, and Review",
    "Use Continue to Scenario at any time—Stage 3 is optional and does not block validation when disabled",
    "Calibration is optional but recommended for realistic behavioral responses",
  ],
  concepts: [
    { term: "Discrete Choice Model", definition: "A statistical model that predicts household choices between alternatives (e.g., vehicle types) based on utility maximization." },
    { term: "Logit Model", definition: "A type of discrete choice model: Multinomial Logit (basic), Nested Logit (groups similar alternatives), Mixed Logit (allows preference variation)." },
    { term: "Taste Parameters", definition: "Coefficients that capture household preferences for technology attributes: price sensitivity, range anxiety, environmental preference." },
  ],
},
```

### File: `frontend/src/components/engine/validationChecks.ts` (NO CHANGES NEEDED)

**Validation logic already supports skip-when-disabled:**
- `logitModelRequiredCheck` — returns `{ passed: true }` when `!enabled`
- `tasteParametersRequiredCheck` — returns `{ passed: true }` when `!enabled`
- `investmentDecisionsCalibratedCheck` — returns `{ passed: true }` when `!enabled`

**Optional enhancement:** Update error messages to include "Configure in Stage 3" hint:

```typescript
// In logitModelRequiredCheck (line 127):
message: "Investment decisions require a logit model. Configure in Stage 3.",

// In tasteParametersRequiredCheck (line 162):
message: "Investment decisions require taste parameters. Configure in Stage 3.",
```

### Testing Standards

**Frontend Component Tests:** `frontend/src/components/screens/__tests__/InvestmentDecisionsStageScreen.test.tsx`

Required test coverage for Story 26.2:
- Test null state render (no active scenario)
- Test disabled state render (enable toggle, summary copy, Continue to Scenario button)
- Test enabled state render (InvestmentDecisionsWizard appears)
- Test enable toggle calls updateScenarioField with enabled state
- Test wizard state is preserved when enabled
- Test Continue to Scenario button navigates to scenario stage
- Test Back to Population button navigates to population stage
- Test wizard resets appropriately when stage is re-entered

**Frontend Component Tests:** `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx`

Updated test coverage:
- Remove: `investment decisions toggle shows wizard when clicked` (line 304-315)
- Remove: `wizard renders Enable Investment Decisions text` (line 317-321)
- Add: Test investment decisions summary displays correctly when disabled
- Add: Test investment decisions summary displays correctly when enabled
- Add: Test "Configure in Stage 3" button navigates to investment-decisions stage

**Frontend Integration Tests:** Update existing tests for five-stage flow

- Update `analyst-journey.test.tsx` for Stage 3 navigation
- Update validation tests for skip-when-disabled behavior
- Update workflow tests that include investment decision configuration

### Project Structure Notes

**Frontend Files to Create:**
- `frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx` — New stage screen
- `frontend/src/components/screens/__tests__/InvestmentDecisionsStageScreen.test.tsx` — Tests

**Frontend Files to Modify:**
- `frontend/src/App.tsx` — Add InvestmentDecisionsStageScreen import and routing
- `frontend/src/components/screens/EngineStageScreen.tsx` — Remove investment-decision section, add summary
- `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx` — Update tests
- `frontend/src/components/help/help-content.ts` — Update investment-decisions help entry
- `frontend/src/components/engine/validationChecks.ts` — Optional: enhance error messages

**Files to Verify (no changes expected):**
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — Should work unchanged
- `frontend/src/components/engine/__tests__/InvestmentDecisionsWizard.test.tsx` — Should pass unchanged
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Already has investment-decisions summary logic from Story 26.1
- `frontend/src/types/workspace.ts` — StageKey already includes "investment-decisions" from Story 26.1

### Implementation Order Recommendation

1. **Phase 1: Create InvestmentDecisionsStageScreen** (New component)
   - Create InvestmentDecisionsStageScreen.tsx with null state
   - Add disabled-state view with enable toggle and Continue button
   - Add enabled-state view with InvestmentDecisionsWizard
   - Add navigation buttons (Back to Population, Continue to Scenario)
   - Add component tests

2. **Phase 2: Update App.tsx routing** (Connect new stage)
   - Add InvestmentDecisionsStageScreen import
   - Replace placeholder div with component render

3. **Phase 3: Update EngineStageScreen** (Remove wizard, add summary)
   - Remove Investment Decisions section with wizard
   - Add read-only summary with "Configure in Stage 3" link
   - Update EngineStageScreen tests

4. **Phase 4: Update help content** (Stage 3 guidance)
   - Update investment-decisions help entry
   - Remove "Coming in Story 26.2" placeholder text

5. **Phase 5: Integration and regression** (Validate full flow)
   - Test navigation flow across all five stages
   - Test skip-when-disabled path (disabled → Scenario → validation passes)
   - Test configure-and-continue path (enabled → wizard → Scenario)
   - Verify wizard functionality preserved in new stage
   - Update analyst-journey e2e tests

### Key Implementation Decisions

**Reuse InvestmentDecisionsWizard without modification:**
- The wizard component is already well-tested and functional
- This story is about stage separation, not rewriting wizard logic
- The wizard's internal state (activeStep, visitedSteps) resets on unmount, which is appropriate for stage navigation

**Disable = Complete:**
- Stage 3 completion logic (from Story 26.1) treats disabled as complete
- This allows analysts to skip Stage 3 without blocking validation
- Nav rail shows checkmark when disabled OR when enabled and configured

**Stage 3 Navigation:**
- "Back to Population" button for backward navigation
- "Continue to Scenario" button for forward navigation
- Both buttons are always visible regardless of enabled/disabled state

**EngineStageScreen Summary:**
- Shows current state (Disabled or Enabled with model name)
- "Configure in Stage 3" link for easy navigation back to Stage 3
- No editing controls in EngineStageScreen—all edits happen in Stage 3

**Validation Check Messages (Optional Enhancement):**
- Update error messages to include "Configure in Stage 3" hint
- This helps analysts understand where to fix validation errors
- Existing validation logic already supports skip-when-disabled

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-26] - Epic 26 requirements
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] - UX design specification (Revision 4.1, UX-DR11)
- [Source: frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx] - New stage screen (this story)
- [Source: frontend/src/components/screens/EngineStageScreen.tsx] - Modified to remove wizard (this story)
- [Source: frontend/src/components/engine/InvestmentDecisionsWizard.tsx] - Reused wizard component (Story 22.6)
- [Source: frontend/src/components/engine/validationChecks.ts] - Validation checks (already support skip-when-disabled)
- [Source: frontend/src/types/workspace.ts] - StageKey and EngineConfig types

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

Story 26.2 created with comprehensive developer context:

**Files Analyzed:**
- InvestmentDecisionsWizard.tsx — Four-step wizard (Enable, Model, Parameters, Review)
- EngineStageScreen.tsx — Current home of wizard (lines 333-339)
- InvestmentDecisionsAccordion.tsx — Legacy accordion component (not used in current flow)
- workspace.ts — Five-stage type definitions (Story 26.1)
- App.tsx — Current placeholder for investment-decisions stage
- help-content.ts — Investment decisions help entry
- validationChecks.ts — Validation logic for investment decisions
- RunSummaryPanel.tsx — Shows investment-decision status in right panel

**Key Design Decisions Documented:**
- Reuse InvestmentDecisionsWizard without modification
- Disable = Complete for stage completion
- EngineStageScreen shows read-only summary with link to Stage 3
- Validation checks already support skip-when-disabled (no changes needed)
- Wizard state resets on stage re-entry (appropriate for UX)

**Testing Strategy:**
- New InvestmentDecisionsStageScreen component tests
- Updated EngineStageScreen tests (remove wizard tests, add summary tests)
- Integration tests for five-stage flow
- E2e tests for skip-when-disabled and configure paths

Status set to: ready-for-dev

