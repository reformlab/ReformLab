# Story 22.6: Guided investment decision wizard inside the Scenario stage

Status: ready-for-dev

## Story

As a policy analyst working in the ReformLab Scenario stage,
I want a guided wizard-like flow for configuring investment decisions,
so that I can understand and set up advanced behavioral modeling in a clear, ordered way without facing a dense accordion.

## Acceptance Criteria

1. **[AC-1]** Given the Scenario stage, when investment decisions are enabled, then the user can progress through a visible guided sequence for Enable, Model, Parameters, and Review steps.
2. **[AC-2]** Given investment decisions are disabled, when the user leaves the flow off, then the scenario remains valid and the stage returns to the simpler default path.
3. **[AC-3]** Given enabled investment decisions, when validation runs, then a logit model is required, required parameters have valid values, and the review step reflects calibration state.
4. **[AC-4]** Given taste parameters and related controls, when edited, then they persist in scenario state (EngineConfig) rather than existing only as transient local UI values.

## Tasks / Subtasks

- [ ] **Task 1: Extend EngineConfig with taste parameters** (AC: 4)
  - [ ] Add `tasteParameters` field to `EngineConfig` type in `workspace.ts`
  - [ ] Define `TasteParameters` interface with `priceSensitivity`, `rangeAnxiety`, `envPreference` (same bounds as current local state)
  - [ ] Add `calibrationState` field to track calibration status (`"not_configured" | "in_progress" | "completed"`)
  - [ ] Update `createDemoScenario` to include default taste parameters in `engineConfig`
  - [ ] Update all `EngineConfig` initialization sites (AppContext `createNewScenario`, EngineStageScreen defaults)

- [ ] **Task 2: Create InvestmentDecisionsWizard component with stepper** (AC: 1)
  - [ ] Create new component `frontend/src/components/engine/InvestmentDecisionsWizard.tsx`
  - [ ] Implement stepper UI with 4 steps: Enable, Model, Parameters, Review
  - [ ] Each step should have a visible indicator (circle with number or checkmark)
  - [ ] Step content should be vertically stacked, not horizontal accordion
  - [ ] Add step navigation: Next/Back buttons at bottom of each step
  - [ ] First step (Enable) should have the toggle switch
  - [ ] Last step (Review) should show summary and allow returning to previous steps

- [ ] **Task 3: Implement Enable step** (AC: 1, 2)
  - [ ] Render Switch toggle for `investmentDecisionsEnabled`
  - [ ] Include explanatory text about what investment decisions do
  - [ ] When disabled, show simple collapsed state (toggle only)
  - [ ] When enabled, auto-navigate to Model step
  - [ ] Do NOT show any parameter sliders or controls in Enable step

- [ ] **Task 4: Implement Model step** (AC: 1, 3)
  - [ ] Render logit model selector dropdown (multinomial_logit, nested_logit, mixed_logit)
  - [ ] Add brief description of each model type (helper text below selector)
  - [ ] Update `engineConfig.logitModel` on selection change
  - [ ] Validation: require model selection before enabling Next button

- [ ] **Task 5: Implement Parameters step** (AC: 1, 4)
  - [ ] Port existing taste parameter sliders from `InvestmentDecisionsAccordion`
  - [ ] Bind sliders to `engineConfig.tasteParameters` (NOT local state)
  - [ ] Keep all slider bounds: `priceSensitivity: [-5, 0]`, `rangeAnxiety: [-3, 0]`, `envPreference: [0, 3]`
  - [ ] Display current values in monospace font (as current)
  - [ ] Persist changes immediately to `activeScenario` via `updateScenarioField`

- [ ] **Task 6: Implement Review step** (AC: 1, 3)
  - [ ] Display read-only summary of all chosen settings:
    - Logit model selected
    - All taste parameter values
    - Calibration state badge
  - [ ] Show calibration status: "Not configured" (amber), "In progress" (blue), "Completed" (green)
  - [ ] Include "Edit" buttons to jump back to Model or Parameters steps
  - [ ] Keep existing `CalibrationPanel` stub embedded in Review step

- [ ] **Task 7: Replace accordion with wizard in EngineStageScreen** (AC: 1)
  - [ ] Import `InvestmentDecisionsWizard` in `EngineStageScreen.tsx`
  - [ ] Replace `<InvestmentDecisionsAccordion>` with `<InvestmentDecisionsWizard>`
  - [ ] Pass same props: `config`, `onEngineConfigChange`
  - [ ] Verify layout still works (wizard may be taller than accordion)

- [ ] **Task 8: Update validation for new wizard structure** (AC: 3)
  - [ ] Keep existing `investmentDecisionsCalibratedCheck` warning (still valid for default params)
  - [ ] Add new check: when enabled, `logitModel` must not be null
  - [ ] Add new check: when enabled, `tasteParameters` must have all required fields with valid values
  - [ ] Ensure Run button remains disabled when wizard steps are incomplete

- [ ] **Task 9: Write tests for InvestmentDecisionsWizard** (AC: 1, 2, 3, 4)
  - [ ] Test stepper navigation: Next/Back buttons move between steps
  - [ ] Test Enable step: toggle switches to Model step when enabled
  - [ ] Test Model step: selection persists to EngineConfig, validation requires selection
  - [ ] Test Parameters step: sliders update EngineConfig.tasteParameters, not local state
  - [ ] Test Review step: summary displays all selections correctly
  - [ ] Test disabled state: scenario valid when wizard collapsed

- [ ] **Task 10: Update and run all affected tests** (AC: all)
  - [ ] Update `EngineStageScreen.test.tsx` for wizard rendering instead of accordion
  - [ ] Update `validationChecks.test.tsx` for new validation rules
  - [ ] Update `analyst-journey.test.tsx` assertions if any reference investment decisions text
  - [ ] Run `npm test` in `frontend/` — all tests must pass
  - [ ] Run `npm run typecheck` — no TypeScript errors
  - [ ] Run `npm run lint` — no new lint errors

## Dev Notes

### Current Implementation Analysis

**InvestmentDecisionsAccordion** (to be replaced):
- Located at `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx`
- Renders Switch + inline accordion with logit selector, local taste params, CalibrationPanel stub
- **Critical flaw**: Taste parameters are local-only state (line 49): `const [tasteParams, setTasteParams] = useState<TasteParams>(DEFAULT_TASTE_PARAMS)`
- TODO comment (line 48): `// TODO(Story 20.6+): persist taste params to EngineConfig`

**CalibrationPanel** (stub to keep):
- Located at `frontend/src/components/engine/CalibrationPanel.tsx`
- Shows "Not configured" badge, disabled controls, "Run Calibration" button disabled
- Embed this into Review step unchanged

**EngineConfig** type (needs extension):
- Located at `frontend/src/types/workspace.ts` lines 52-58
- Current fields: `startYear`, `endYear`, `seed`, `investmentDecisionsEnabled`, `logitModel`, `discountRate`
- Missing: `tasteParameters`, `calibrationState`

**Validation** (needs extension):
- Located at `frontend/src/components/engine/validationChecks.ts`
- Current `investmentDecisionsCalibratedCheck` (lines 70-82) warns about uncalibrated state
- Needs new checks for: logit model required, taste params required when enabled

### Architecture Constraints

From `project-context.md`:
- **React 19**: ref as regular prop (no forwardRef)
- **Shadcn/ui components available**: Badge, Button, Card, Collapsible, Input, Popover, ScrollArea, Select, Separator, Sheet, Slider, Switch, Table, Tabs, Tooltip, Sonner
- **Tailwind v4**: use utility classes; CSS vars for chart colors
- No Dialog/DialogContent (use inline fixed-overlay pattern per Story 20.2)

### Scope Boundaries

**IN SCOPE:**
- Guided wizard with 4 steps (Enable, Model, Parameters, Review)
- Taste parameters persist to EngineConfig (fix current local-only bug)
- Step navigation with Next/Back buttons
- Validation updates for new structure
- Tests for wizard component

**OUT OF SCOPE:**
- Full calibration implementation (CalibrationPanel remains stub)
- Backend API changes (no new endpoints required)
- New logit models beyond the 3 existing options
- Advanced parameter editing beyond the 3 taste params
- Mobile-specific wizard behavior (deferred to Story 22.7)

### Wizard UX Specifications

From `ux-revision-3-implementation-spec.md` Change 7:

**Sub-step sequence:**
1. `Enable` — explain what investment decisions do, toggle feature on or off
2. `Model` — choose the logit model
3. `Parameters` — edit taste parameters and related controls
4. `Review` — summarize chosen settings and calibration state

**Content rules:**
- Feature label remains "Investment Decisions"
- Wizard should explain that this is an advanced scenario behavior layer
- Tone should be guided, not academic

**Layout rules:**
- Desktop: render wizard inline inside Scenario stage
- Phone: present as stacked sections (deferred to Story 22.7)
- This does NOT need to become a modal

### Testing Standards

Per project context:
- Use Vitest for frontend tests
- Test file structure mirrors source
- Test file: `frontend/src/components/engine/__tests__/InvestmentDecisionsWizard.test.tsx`
- Use `render`, `screen`, `waitFor` from `@testing-library/react`
- Mock `useAppState` hook for EngineConfig props
- Test stepper state transitions, not just visual rendering

### Persistence Requirements

**Critical**: Taste parameters MUST persist to `EngineConfig.tasteParameters`
- Current bug: Local-only state loses changes on re-render
- AC-4 explicitly requires durable scenario state
- Use `updateScenarioField("engineConfig", {...config, tasteParameters: ...})`
- Do NOT use `useState` for taste params in wizard

### Known Constraints and Gotchas

1. **CalibrationPanel is a stub** — do NOT attempt to implement full calibration
2. **Wizard is taller than accordion** — EngineStageScreen right panel may need overflow handling
3. **Step state management** — track activeStep as local state (0-3), not in EngineConfig
4. **Back button navigation** — allow jumping back from Review to any previous step
5. **Default taste parameters** — must match current values: `priceSensitivity: -1.5`, `rangeAnxiety: -0.8`, `envPreference: 0.5`
6. **Validation integration** — wizard does NOT replace ValidationGate, it supplements it
7. **Demo scenario compatibility** — `createDemoScenario` must initialize with default taste params

### References

- **Epic 22 definition:** `_bmad-output/planning-artifacts/epics.md#Epic-22`
- **UX Revision 3 spec:** `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 7 (Investment Decision Wizard)
- **InvestmentDecisionsAccordion source:** `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx`
- **CalibrationPanel source:** `frontend/src/components/engine/CalibrationPanel.tsx`
- **EngineConfig type:** `frontend/src/types/workspace.ts` (lines 52-58)
- **Validation checks:** `frontend/src/components/engine/validationChecks.ts`
- **EngineStageScreen source:** `frontend/src/components/screens/EngineStageScreen.tsx`

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Debug Log References

Analysis completed from source files:
- `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx` — Current accordion implementation with local-only taste params bug
- `frontend/src/components/engine/CalibrationPanel.tsx` — Stub component to embed in Review step
- `frontend/src/types/workspace.ts` — EngineConfig type definition requiring extension
- `frontend/src/components/engine/validationChecks.ts` — Existing validation requiring updates
- `frontend/src/components/screens/EngineStageScreen.tsx` — Parent component where wizard will be mounted
- `frontend/src/contexts/AppContext.tsx` — Scenario state management and EngineConfig initialization
- `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Full UX spec for wizard behavior

### Completion Notes List

- Story 22.6 replaces the dense InvestmentDecisionsAccordion with a guided 4-step wizard
- Four steps: Enable (toggle + explanation), Model (logit selector), Parameters (taste params), Review (summary)
- **Critical fix**: Taste parameters move from local-only state to persisted EngineConfig.tasteParameters
- Validation extends to check logit model requirement when enabled
- CalibrationPanel remains a stub (full calibration deferred)
- Wizard renders inline in Scenario stage, same position as current accordion
- Step state (0-3) is local wizard state; all configuration persists to EngineConfig
- Demo scenario compatibility: must initialize with default taste parameters
- **Story created:** 2026-03-30
- **Epic:** 22 (UX Revision 3 Workspace Fit and Mobile Demo Viability)

### File List

**Files to create:**
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — Main wizard component with stepper
- `frontend/src/components/engine/__tests__/InvestmentDecisionsWizard.test.tsx` — Wizard tests

**Files to modify:**
- `frontend/src/types/workspace.ts` — Extend EngineConfig with tasteParameters, calibrationState
- `frontend/src/components/screens/EngineStageScreen.tsx` — Replace accordion with wizard
- `frontend/src/components/engine/validationChecks.ts` — Add validation rules for wizard
- `frontend/src/data/demo-scenario.ts` — Update createDemoScenario with taste params
- `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx` — Update for wizard assertions
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — Update if needed

**Files to keep unchanged:**
- `frontend/src/components/engine/CalibrationPanel.tsx` — Stub component, embed in Review step
- `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx` — Can be deleted after wizard is working

---
**Story Status:** ready-for-dev
**Created:** 2026-03-30

---
