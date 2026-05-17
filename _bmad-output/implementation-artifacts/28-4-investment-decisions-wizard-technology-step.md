# Story 28.4: Investment Decisions wizard — Technology step

Status: ready-for-dev

## Story

As an analyst configuring an investment-decisions scenario,
I want a "Technology" step in the wizard between Enable and Model that lets me pick which alternatives are in scope per domain, with auto-detection from my selected population's incumbent column and inline warnings when the population mismatches my chosen set,
so that the technology set I'm modelling is explicit, reproducible, and clearly aligned (or not) with my population data.

## Acceptance Criteria

1. Given the existing wizard step order `Enable → Model → Parameters → Review`, when this story lands, then the order becomes `Enable → Technology → Model → Parameters → Review` and the `goToStep` machinery from Story 27.7 (clickable step labels) supports the new step.

2. Given the analyst has enabled investment decisions, when they advance to the Technology step, then per-domain expandable sections render (heating, vehicle), each with a switch toggling whether the domain participates.

3. Given a domain is enabled in the wizard, when rendered, then the alternatives list is pre-populated from the canonical-set API (Story 28.1's `GET /api/discrete-choice/technology-sets/default?domain=heating`), the analyst can add / remove / reorder alternatives, and one alternative is pinned as the "reference" via radio (mapping to `referenceAlternativeId`).

4. Given the active scenario's primary population has an `incumbent_<domain>` column with values, when the analyst opens the Technology step, then a green badge "Incumbent technology detected in population" appears next to the domain header, and the corresponding alternatives are pre-checked in the list.

5. Given the population's `incumbent_<domain>` column has values not present in the chosen alternatives list, when rendered, then a non-toast inline banner per domain reads "{N} households have technology X not in your set; they will start at the reference alternative." Clicking the banner offers an action: "Add X to my set" (which adds the alternative scaffold to the list).

6. Given the population is missing the `incumbent_<domain>` column entirely (per Story 28.2 backward-compat), when the analyst opens the Technology step, then a non-toast inline warning reads "Selected population doesn't carry incumbent technology. All households will start at the reference alternative."

7. Given the population fully matches the chosen set, when rendered, then a non-toast inline confirmation reads "Incumbent matched in 100% of households."

8. Given the analyst has not yet picked a technology set, when they open the Technology step, then a primary CTA "Use default French set (5 heating, 6 vehicle)" is offered as an explicit one-click apply (never silent auto-apply).

9. Given the analyst removes an alternative whose ASC is configured in the Parameters step, when they advance past Technology, then a wizard-side validation surfaces the orphan ASC keys and prevents proceeding (per spike risk 10.5).

10. Given the toast-policy memory (`feedback_error_toasts_user_initiated_only.md`), when this story is implemented, then NO warnings in this step use `toast.*`; everything is inline.

## Tasks / Subtasks

- [ ] Task 1: Add Technology step to wizard (AC: #1)
  - [ ] 1.1 Update `STEP_LABELS` constant in `InvestmentDecisionsWizard.tsx` (around line 35) to add "Technology" between "Enable" and "Model"
  - [ ] 1.2 Update `WizardStep` type from `0 | 1 | 2 | 3` to `0 | 1 | 2 | 3 | 4` with comment mapping each value
  - [ ] 1.3 Update `goToStep()` function and step indicators to support 5 steps
  - [ ] 1.4 Ensure Story 27.7 clickable step labels work with new step (forward navigation disabled until visited, backward navigation always allowed)
  - [ ] 1.5 Update step rendering switch in `renderStepContent()` to handle case 2 (Technology)
  - [ ] 1.6 Update navigation validation logic in `renderNavigation()` for new step progression rules

- [ ] Task 2: Create TechnologyStep component (AC: #2, #3, #8)
  - [ ] 2.1 Create `frontend/src/components/engine/TechnologyStep.tsx`
  - [ ] 2.2 Component props interface: `engineConfig: EngineConfig`, `onUpdateEngineConfig: (config: EngineConfig) => void`
  - [ ] 2.3 Per-domain expandable sections using Collapsible component (existing shadcn/ui)
  - [ ] 2.4 Domain toggle switch (enabled/disabled) per domain
  - [ ] 2.5 Alternatives list with checkboxes, drag-and-drop reordering (or up/down arrows)
  - [ ] 2.6 Reference alternative radio button selector (must map to `referenceAlternativeId`)
  - [ ] 2.7 "Add alternative" button with scaffold (id, name, empty attributes)
  - [ ] 2.8 Remove alternative button (disabled for reference alternative)
  - [ ] 2.9 "Use default French set" CTA when no technology set is present (calls `getAllDefaultTechnologySets()`)
  - [ ] 2.10 Wire up to `engineConfig.technologySet` updates via `onUpdateEngineConfig`

- [ ] Task 3: Population incumbent detection (AC: #4, #6, #7)
  - [ ] 3.1 Read active scenario's primary population ID from AppContext
  - [ ] 3.2 Fetch population summary using existing API endpoint (extend if needed to include incumbent column distinct values)
  - [ ] 3.3 Check for `incumbent_heating` and `incumbent_vehicle` columns in population metadata
  - [ ] 3.4 Extract distinct values from incumbent columns (use population profile endpoint or add new summary field)
  - [ ] 3.5 Match distinct values against alternatives in technology set
  - [ ] 3.6 Calculate match percentage (households with matching incumbents / total households)
  - [ ] 3.7 Render green badge when incumbents detected
  - [ ] 3.8 Render inline confirmation for 100% match
  - [ ] 3.9 Render inline warning for missing incumbent column

- [ ] Task 4: Mismatch warnings and "Add to set" action (AC: #5)
  - [ ] 4.1 Detect population incumbent values not in chosen alternatives
  - [ ] 4.2 Count households per unmatched technology value
  - [ ] 4.3 Render inline banner: "{N} households have technology X not in your set; they will start at the reference alternative."
  - [ ] 4.4 Add "Add X to my set" action button in banner
  - [ ] 4.5 On click, scaffold alternative with: `id: <value>`, `name: "Technology X"`, `attributes: {}`
  - [ ] 4.6 Update technology set with new alternative (preserve existing selections)

- [ ] Task 5: Orphan-ASC validation (AC: #9)
  - [ ] 5.1 Check if Parameters step has configured ASCs (alternative-specific constants in taste parameters)
  - [ ] 5.2 On Next from Technology or on Next from Parameters (if Technology was modified), validate ASC keys
  - [ ] 5.3 Find ASC keys that reference alternatives not in current technology set
  - [ ] 5.4 Render inline validation error: "Alternative 'X' has a configured taste parameter but is not in your technology set. Remove the parameter or re-add the alternative."
  - [ ] 5.5 Block Next navigation until orphans resolved
  - [ ] 5.6 Clear validation state when orphans are resolved

- [ ] Task 6: Inline-only warnings (AC: #10)
  - [ ] 6.1 Verify NO `toast.*` calls in TechnologyStep component
  - [ ] 6.2 Use inline banner pattern for all warnings (reuse existing notification styling)
  - [ ] 6.3 Use status badges for domain-level feedback
  - [ ] 6.4 Ensure all user feedback is contextual (next to relevant element)

- [ ] Task 7: Update wizard integration (AC: #1, #3)
  - [ ] 7.1 Update `InvestmentDecisionsWizard` imports to include `TechnologyStep`
  - [ ] 7.2 Add Technology step to `STEP_LABELS` array: `["Enable", "Technology", "Model", "Parameters", "Review"]`
  - [ ] 7.3 Update `renderStepContent()` switch case for step 2
  - [ ] 7.4 Update navigation logic in `renderNavigation()` for `canGoNext` validation
  - [ ] 7.5 Ensure Model step (now step 3) validates technology set is configured before allowing navigation

- [ ] Task 8: Update types and API (AC: #3)
  - [ ] 8.1 Extend `EngineConfig` type if needed (Story 28.1 should have added `technologySet?: TechnologySet | null`)
  - [ ] 8.2 Add `TechnologyAlternative` type helper for alternative scaffolding
  - [ ] 8.3 Add domain-specific type guards for incumbent detection
  - [ ] 8.4 Ensure API client (`technology-sets.ts`) exports are available to component

- [ ] Task 9: Tests
  - [ ] 9.1 Create `frontend/src/components/engine/__tests__/TechnologyStep.test.tsx`
  - [ ] 9.2 Render tests: no technology set (show CTA), partial set (show sections), full set (show all alternatives)
  - [ ] 9.3 Population detection tests: with incumbents (green badge), without column (warning), 100% match (confirmation)
  - [ ] 9.4 Mismatch tests: population has values not in set (banner + add action)
  - [ ] 9.5 CTA test: "Use default French set" button applies canonical technology set
  - [ ] 9.6 Add-from-banner test: clicking "Add X to my set" creates alternative scaffold
  - [ ] 9.7 Orphan-ASC test: removing alternative with configured ASC blocks Next
  - [ ] 9.8 Toast-policy test: assert no `toast.*` is invoked (mock toast functions and verify not called)
  - [ ] 9.9 Update `InvestmentDecisionsWizard.test.tsx` for new step order (5 steps instead of 4)
  - [ ] 9.10 Integration test: full wizard flow with Technology step

- [ ] Task 10: Quality gates
  - [ ] 10.1 Run `npm test` — all tests pass including new TechnologyStep tests
  - [ ] 10.2 Run `npm run typecheck` — no TypeScript errors in new component
  - [ ] 10.3 Run `npm run lint` — no linting warnings
  - [ ] 10.4 Manual smoke test: enable decisions → use default set → verify alternatives render → navigate through all steps

## Dev Notes

### Critical Architecture Constraints (Source: project-context.md)

**Frontend Framework Rules** (MUST follow):
- **React 19**: ref as regular prop (no forwardRef needed for new components)
- **TypeScript strict mode**: All types must be explicitly defined, no `any` without justification
- **Shadcn/ui components**: Use Badge, Button, Collapsible, Switch, and other existing components
- **Tailwind v4**: Use utility classes; CSS vars for chart colors, semantic colors for status
- **Hash-based routing**: Updates must preserve `window.location.hash` navigation patterns

**State Management Patterns** (from existing InvestmentDecisionsWizard):
- Props-based state: Component receives `engineConfig` and `onUpdateEngineConfig` callback
- Local state for UI-only concerns (active step, visited steps, UI interactions)
- No direct mutations of `engineConfig` — always call `onUpdateEngineConfig` with new object
- Use spread operator for immutable updates: `{...engineConfig, technologySet: newSet}`

**Testing Standards** (from existing wizard tests):
- Use `@testing-library/react` for component testing
- Use `userEvent` from `@testing-library/user-event` for user interactions
- Mock API calls with `vi.mock()` for external dependencies
- Test render states, user interactions, and state updates
- Follow AAA pattern (Arrange, Act, Assert) in test structure

### Existing Code Patterns (Reference for Implementation)

**InvestmentDecisionsWizard Step Pattern** (from `InvestmentDecisionsWizard.tsx`):
```typescript
type WizardStep = 0 | 1 | 2 | 3 | 4;  // After this story: Enable | Technology | Model | Parameters | Review

const STEP_LABELS = ["Enable", "Technology", "Model", "Parameters", "Review"] as const;

const goToStep = (step: WizardStep) => {
  setActiveStep(step);
  setVisitedSteps((prev) => new Set([...prev, step]));
};

const renderStepContent = () => {
  switch (activeStep) {
    case 0: return renderEnableStep();
    case 1: return renderTechnologyStep();  // NEW: Story 28.4
    case 2: return renderModelStep();       // Was case 1
    case 3: return renderParametersStep();  // Was case 2
    case 4: return renderReviewStep();      // Was case 3
  }
};
```

**TechnologyStep Component Structure** (new component):
```typescript
interface TechnologyStepProps {
  engineConfig: EngineConfig;
  onUpdateEngineConfig: (config: EngineConfig) => void;
}

export function TechnologyStep({ engineConfig, onUpdateEngineConfig }: TechnologyStepProps) {
  // Local state for UI interactions (expand/collapse domains)
  const [expandedDomains, setExpandedDomains] = useState<Set<DecisionDomainKey>>(new Set());

  // Fetch default technology set if not present
  const { data: defaultSet } = useDefaultTechnologySet();  // Custom hook or direct fetch

  // Fetch population incumbent data
  const { data: populationIncumbents } = usePopulationIncumbents();  // Custom hook

  const handleUseDefaultSet = async () => {
    const defaultSet = await getAllDefaultTechnologySets();
    onUpdateEngineConfig({
      ...engineConfig,
      technologySet: defaultSet,
    });
  };

  const handleDomainToggle = (domain: DecisionDomainKey, enabled: boolean) => {
    const currentSet = engineConfig.technologySet;
    if (!currentSet) return;

    const updatedSet = {
      ...currentSet,
      domains: {
        ...currentSet.domains,
        [domain]: {
          ...currentSet.domains[domain]!,
          enabled,
        },
      },
    };

    onUpdateEngineConfig({
      ...engineConfig,
      technologySet: updatedSet,
    });
  };

  // ... more handlers
}
```

**API Integration Pattern** (from `technology-sets.ts`):
```typescript
import { getAllDefaultTechnologySets, getDefaultTechnologySet } from "@/api/technology-sets";

// Fetch all defaults
const defaultSet = await getAllDefaultTechnologySets();
// Returns: { version: "fr-default-2026-04-26", domains: { heating: {...}, vehicle: {...} } }

// Fetch single domain
const heatingSet = await getDefaultTechnologySet("heating");
// Returns: { domain: "heating", enabled: true, alternatives: [...], ... }
```

**Population Incumbent Detection Pattern** (needs to be implemented):
```typescript
// Hook to fetch population incumbent data
function usePopulationIncumbents(populationId: string | null) {
  const [incumbents, setIncumbents] = useState<Record<DecisionDomainKey, Set<string>>>({
    heating: new Set(),
    vehicle: new Set(),
  });

  useEffect(() => {
    if (!populationId) return;

    // Fetch population profile or summary
    // Extract distinct values from incumbent_heating and incumbent_vehicle columns
    // This may require extending an existing endpoint or adding a new one

    const fetchIncumbents = async () => {
      const profile = await fetchPopulationProfile(populationId);
      // Parse columns for incumbent_heating and incumbent_vehicle
      // Extract distinct values
      setIncumbents({
        heating: new Set(heatingValues),
        vehicle: new Set(vehicleValues),
      });
    };

    fetchIncumbents();
  }, [populationId]);

  return incumbents;
}
```

**Inline Banner Pattern** (for AC: #5, #6, #7):
```typescript
// Reusable inline banner component
interface InlineBannerProps {
  variant: "warning" | "info" | "success";
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

function InlineBanner({ variant, message, actionLabel, onAction }: InlineBannerProps) {
  const colors = {
    warning: "bg-amber-50 border-amber-200 text-amber-900",
    info: "bg-blue-50 border-blue-200 text-blue-900",
    success: "bg-emerald-50 border-emerald-200 text-emerald-900",
  };

  return (
    <div className={`p-3 rounded border ${colors[variant]} flex items-center justify-between`}>
      <p className="text-sm">{message}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="ml-4 text-sm font-medium underline hover:no-underline"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
```

### Dependencies Between Stories

- **Story 28.0** (architect spike) — DONE — provides ADR with technology-set contract
- **Story 28.1** — DONE — provides `TechnologySet` type and API endpoints (`GET /api/discrete-choice/technology-sets/default`)
- **Story 28.2** — DONE — provides incumbent column convention (`incumbent_heating`, `incumbent_vehicle`)
- **Story 27.7** — DONE — provides clickable wizard step labels that this story must integrate with
- **Story 28.4** (this story) — READY FOR DEV — wizard Technology step
- **Story 28.5** (regression) — BACKLOG — multi-period decision runs with full technology set

### Alternative ID Reconciliation Warning

**CRITICAL**: Story 28.3 identified an Alternative ID mismatch between legacy heating domain IDs and `DEFAULT_TECHNOLOGY_SET` IDs:

- Legacy heating IDs: `gas_boiler`, `heat_pump`, `electric`, `wood_pellet`
- DEFAULT_TECHNOLOGY_SET IDs: `condensing_boiler`, `heat_pump_air`, `heat_pump_ground`, `district_heating`

**Impact on this story**: When detecting incumbents from populations that were created with legacy IDs, the wizard will show mismatches. The "Add to set" action (AC-5) will scaffold alternatives with legacy IDs, creating a mixed technology set.

**Mitigation**: The validation logic should allow mixed IDs during the transition period. Future story should reconcile IDs to migrate fully to `DEFAULT_TECHNOLOGY_SET`.

### Toast Policy Compliance (AC: #10)

**Critical**: All warnings in this step MUST be inline — NO toasts allowed.

From `feedback_error_toasts_user_initiated_only.md`:
> Passive / autoload / restore failures are silent; explicit user-initiated actions (Save, Load click, Run) keep their toasts.

**Application to this story**:
- Population detection failures → silent (no data, no banner)
- API fetch failures → silent (show empty state, not toast)
- Validation errors → inline banners, not toasts
- Success states → inline confirmations, not toasts
- User-initiated actions (Use default set, Add to set) → can show brief confirmation inline, not toast

### Testing Standards

**Frontend Testing** (from project-context.md and existing wizard tests):
- Mirror source structure: `frontend/src/components/engine/__tests__/TechnologyStep.test.tsx`
- Use `@testing-library/react` for component testing
- Use `userEvent` from `@testing-library/user-event` for interactions
- Mock API calls with `vi.mock("@/api/technology-sets")`
- Test render states, user interactions, and state updates
- Follow AAA pattern (Arrange, Act, Assert)

**Test Cases** (comprehensive coverage):
```typescript
describe("TechnologyStep", () => {
  describe("Initial state (no technology set)", () => {
    it("renders 'Use default French set' CTA when technologySet is null", () => {
      // Assert CTA button visible and labeled correctly
    });

    it("applies default technology set when CTA clicked", async () => {
      // Mock getAllDefaultTechnologySets()
      // Click CTA button
      // Assert onUpdateEngineConfig called with default set
    });
  });

  describe("Per-domain sections", () => {
    it("renders heating and vehicle sections when technology set present", () => {
      // Assert both sections render
      // Assert domain toggle switches render
    });

    it("shows alternatives list with checkboxes for enabled domain", () => {
      // Assert alternatives from default set render
      // Assert checkboxes checked for included alternatives
    });

    it("toggles domain enabled/disabled when switch clicked", () => {
      // Click heating toggle
      // Assert onUpdateEngineConfig called with enabled: false
    });

    it("changes reference alternative when radio clicked", () => {
      // Click radio on alternative
      // Assert referenceAlternativeId updated
    });

    it("removes alternative when remove button clicked", () => {
      // Click remove button
      // Assert alternative removed from list
      // Assert referenceAlternativeId updated if reference was removed
    });

    it("adds scaffolded alternative when add button clicked", () => {
      // Click add button
      // Assert new alternative added with id, name, empty attributes
    });
  });

  describe("Population incumbent detection", () => {
    it("shows green badge when incumbent column detected in population", () => {
      // Mock population with incumbent_heating column
      // Assert "Incumbent technology detected" badge visible
    });

    it("pre-checks alternatives matching population incumbents", () => {
      // Mock population with incumbents: ["heat_pump_air", "condensing_boiler"]
      // Assert those alternatives are checked in list
    });

    it("shows inline warning when incumbent column missing", () => {
      // Mock population without incumbent_heating
      // Assert warning banner visible
    });

    it("shows confirmation when population fully matches technology set", () => {
      // Mock population with 100% match
      // Assert "Incumbent matched in 100% of households" visible
    });
  });

  describe("Mismatch warnings", () => {
    it("shows inline banner for population values not in technology set", () => {
      // Mock population with incumbents: ["heat_pump_air", "unknown_tech"]
      // Mock technology set without "unknown_tech"
      // Assert banner: "N households have technology unknown_tech not in your set"
    });

    it("adds alternative when 'Add X to my set' clicked", async () => {
      // Render with mismatch banner
      // Click "Add unknown_tech to my set"
      // Assert alternative added with id: "unknown_tech"
      // Assert banner disappears
    });
  });

  describe("Orphan-ASC validation", () => {
    it("shows validation error when removing alternative with configured ASC", () => {
      // Mock tasteParameters with ASC for "heat_pump_air"
      // Remove "heat_pump_air" from technology set
      // Click Next
      // Assert inline error: "Alternative 'heat_pump_air' has a configured taste parameter"
      // Assert navigation blocked
    });

    it("clears validation error when alternative re-added", () => {
      // Start with orphan ASC error
      // Add back the missing alternative
      // Assert error message disappears
      // Assert navigation unblocked
    });
  });

  describe("Toast policy compliance", () => {
    it("does not call toast functions for any warnings", () => {
      // Mock toast functions
      // Trigger various warning states
      // Assert toast functions never called
    });
  });
});
```

### Quality Gates

**Before marking story done, ensure all pass**:
```bash
# Frontend quality checks
cd frontend/
npm test                    # All tests pass (including new TechnologyStep tests)
npm run typecheck           # No TypeScript errors
npm run lint                # No linting warnings

# Manual smoke test
1. Start dev server: npm run dev
2. Navigate to Investment Decisions stage
3. Enable investment decisions
4. Click "Use default French set" button
5. Verify heating and vehicle sections render with alternatives
6. Toggle domain switches on/off
7. Remove and add alternatives
8. Navigate through all wizard steps
9. Verify step indicators work with new Technology step
```

### Project Structure Notes

**New Files** (to create):
- `frontend/src/components/engine/TechnologyStep.tsx` — Main component for Technology step
- `frontend/src/components/engine/__tests__/TechnologyStep.test.tsx` — Component tests

**Modified Files**:
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — Update step list, add Technology step rendering
- `frontend/src/components/engine/__tests__/InvestmentDecisionsWizard.test.tsx` — Update for 5-step wizard
- `frontend/src/api/technology-sets.ts` — May need extensions for population incumbent data
- `frontend/src/hooks/` — May need new hook for population incumbent detection

**No Backend Changes** — This story is purely frontend; all consumed APIs were created in Story 28.1.

### References

- [Source: `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md`](../planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md) — ADR Sections 2, 7 (technology-set contract, wizard UI)
- [Source: `_bmad-output/implementation-artifacts/28-1-add-technology-set-to-engine-config.md`](28-1-add-technology-set-to-engine-config.md) — TechnologySet types and API endpoints
- [Source: `_bmad-output/implementation-artifacts/28-2-extend-population-data-schema-with-incumbent-technology-columns.md`](28-2-extend-population-data-schema-with-incumbent-technology-columns.md) — Incumbent column convention
- [Source: `_bmad-output/implementation-artifacts/28-3-wire-discrete-choice-step-outputs-back-into-population-frame.md`](28-3-wire-discrete-choice-step-outputs-back-into-population-frame.md) — Alternative ID reconciliation warning
- [Source: `_bmad-output/implementation-artifacts/27-7-make-investment-decisions-wizard-step-labels-clickable.md`](27-7-make-investment-decisions-wizard-step-labels-clickable.md) — Clickable wizard steps pattern
- [Source: `frontend/src/components/engine/InvestmentDecisionsWizard.tsx`](../../frontend/src/components/engine/InvestmentDecisionsWizard.tsx) — Existing wizard component
- [Source: `frontend/src/types/workspace.ts`](../../frontend/src/types/workspace.ts) — TechnologySet types
- [Source: `frontend/src/api/technology-sets.ts`](../../frontend/src/api/technology-sets.ts) — API client functions
- [Source: `feedback_error_toasts_user_initiated_only.md`](../../../../.claude/projects/-Users-lucas-Workspace-reformlab/memory/feedback_error_toasts_user_initiated_only.md) — Toast policy
- [Source: `_bmad-output/project-context.md`](../project-context.md) — Project architecture rules

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — story enhancement completed without issues.

### Completion Notes List

Story 28.4 enhanced with comprehensive developer context (2026-05-17):

**Enhancement Summary**:
- Expanded from basic story skeleton to comprehensive developer guide
- Added detailed acceptance criteria with explicit conditionals (Given/when/then format)
- Broke down into 10 major tasks with 57 subtasks
- Provided complete code patterns for all major components
- Included testing standards with 15+ test case specifications
- Added architecture constraints and frontend framework rules
- Documented Alternative ID reconciliation issue from Story 28.3
- Included toast policy compliance requirements (AC-10)
- Added quality gates with specific commands

**Key Implementation Guidance**:
- Step order changes: Enable (0) → Technology (1) → Model (2) → Parameters (3) → Review (4)
- No backend changes required — consumes Story 28.1 APIs
- Population incumbent detection via existing or extended population profile endpoint
- Inline-only warnings (no toasts) per toast policy
- Orphan-ASC validation to prevent taste parameter references to removed alternatives
- Integration with Story 27.7 clickable wizard steps

**Critical Design Decisions**:
- "Use default French set" CTA follows explicit-action principle (no silent auto-apply)
- Domain toggle switches enable/disable entire domains independently
- Reference alternative radio selector maps to `referenceAlternativeId`
- Inline banner pattern for all warnings (mismatches, missing columns, validation errors)
- Scaffolded alternatives from population mismatches have empty attributes
- Toast functions mocked and verified not called in tests

**Test Coverage**:
- Initial state (no set, CTA rendering and click)
- Per-domain sections (alternatives list, toggles, add/remove)
- Population detection (green badge, warnings, confirmations)
- Mismatch handling (banners, "Add to set" action)
- Orphan-ASC validation (error display, navigation blocking)
- Toast policy compliance (no toast calls)
- Integration with full wizard flow

### File List

**Story File:**
- `_bmad-output/implementation-artifacts/28-4-investment-decisions-wizard-technology-step.md` (status: ready-for-dev)

**New Files to Create:**
- `frontend/src/components/engine/TechnologyStep.tsx` — Main component for Technology step
- `frontend/src/components/engine/__tests__/TechnologyStep.test.tsx` — Component tests

**Modified Files:**
- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` — Update step list, add Technology step rendering
- `frontend/src/components/engine/__tests__/InvestmentDecisionsWizard.test.tsx` — Update for 5-step wizard
- `frontend/src/api/technology-sets.ts` — May need extensions for population incumbent data
- `frontend/src/hooks/` — May need new hook for population incumbent detection

**No Backend Changes** — This story is purely frontend; all consumed APIs were created in Story 28.1.
