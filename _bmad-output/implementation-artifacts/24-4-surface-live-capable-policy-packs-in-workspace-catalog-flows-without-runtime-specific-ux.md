# Story 24.4: Surface live-capable policy packs in workspace catalog flows without runtime-specific UX

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want to see and use all live-capable policy packs (including newly surfaced subsidy, vehicle_malus, and energy_poverty_aid) in the policy catalog and portfolio composition flows,
so that I can discover, configure, and execute these policies through the standard workspace interface without needing to understand runtime internals or engine selection.

## Acceptance Criteria

1. Given the policy browser and composition flows (PortfolioTemplateBrowser, PoliciesStageScreen), when rendered, then newly surfaced live-capable packs (subsidy, vehicle_malus, energy_poverty_aid) are available alongside existing packs (carbon_tax, rebate, feebate) with correct type labels and colors.
2. Given a surfaced pack with a readiness caveat (runtime_availability="live_ready"), when shown to the user, then the pack displays as available with appropriate visual indication (green "Ready" badge) without exposing backend runtime mechanics or engine terminology.
3. Given the first-slice policy workflows, when reviewed, then no runtime or engine selector is introduced — users select policies by name/type without choosing between execution engines.
4. Given a scenario or portfolio using a surfaced pack (subsidy, vehicle_malus, energy_poverty_aid), when saved and reloaded, then the pack reference remains stable and loads correctly.
5. Given template browsers across the workspace (PoliciesStageScreen, PortfolioDesignerScreen, TemplateSelectionScreen), when displaying policy types, then consistent type labels and colors are used for all policy types including newly surfaced ones.
6. Given policy type filtering or grouping, when applied, then vehicle_malus and energy_poverty_aid are correctly grouped by their type without being misclassified or hidden.
7. Given a portfolio containing surfaced policies, when the composition panel displays it, then each policy shows its correct type label and parameter groups.
8. Given the saved portfolios list, when displayed, then portfolios containing surfaced policies show the correct policy count and description without errors.

## Tasks / Subtasks

- [ ] Extend policy type labels and colors in PortfolioTemplateBrowser (AC: #1, #5)
  - [ ] Add "vehicle_malus" → "Vehicle Malus" to TYPE_LABELS
  - [ ] Add "energy_poverty_aid" → "Energy Poverty Aid" to TYPE_LABELS
  - [ ] Add "vehicle_malus" color mapping to TYPE_COLORS (e.g., "bg-rose-100 text-rose-800")
  - [ ] Add "energy_poverty_aid" color mapping to TYPE_COLORS (e.g., "bg-cyan-100 text-cyan-800")
  - [ ] Verify existing types (carbon_tax, subsidy, rebate, feebate) remain unchanged

- [ ] Verify runtime availability badges work correctly (AC: #2, #3)
  - [ ] Confirm surfaced packs display "Ready" badge (green) for live_ready status
  - [ ] Verify no engine/runtime selector appears in policy flows
  - [ ] Ensure availability_reason is not displayed for live_ready packs (only for unavailable)
  - [ ] Test that Badge variant and styling match Story 24.1 implementation

- [ ] Update mock data with surfaced packs (AC: #1, #6)
  - [ ] Add subsidy template variants to mockTemplates (if not present)
  - [ ] Add vehicle_malus template variants to mockTemplates with runtime_availability="live_ready"
  - [ ] Add energy_poverty_aid template variants to mockTemplates with runtime_availability="live_ready"
  - [ ] Ensure correct type, parameterCount, parameterGroups for each

- [ ] Verify portfolio loading with surfaced packs (AC: #4, #7)
  - [ ] Test portfolio load with vehicle_malus policy maps correctly to template
  - [ ] Test portfolio load with energy_poverty_aid policy maps correctly to template
  - [ ] Verify policy_type matching handles underscore conversion correctly (vehicle_malus ↔ vehicle-malus)
  - [ ] Ensure composition panel displays correct parameter groups for surfaced types

- [ ] Add frontend tests for surfaced pack display (AC: #1, #5, #6)
  - [ ] Test PortfolioTemplateBrowser renders vehicle_malus with correct label/color
  - [ ] Test PortfolioTemplateBrowser renders energy_poverty_aid with correct label/color
  - [ ] Test runtime availability badge displays correctly for surfaced packs
  - [ ] Test type grouping includes surfaced packs in correct groups
  - [ ] Test portfolio save/load with surfaced packs maintains stable references

- [ ] Verify PoliciesStageScreen works with surfaced packs (AC: #1, #7)
  - [ ] Confirm surfaced packs appear in template browser
  - [ ] Test adding surfaced packs to portfolio composition
  - [ ] Verify composition panel shows correct type labels for surfaced policies
  - [ ] Test portfolio save/load with surfaced packs through PoliciesStageScreen

- [ ] Non-regression: verify existing packs still work (AC: #1, #5, #8)
  - [ ] Test carbon_tax, rebate, feebate templates still display correctly
  - [ ] Test existing portfolios without surfaced packs still load/save correctly
  - [ ] Verify type labels and colors for existing types are unchanged
  - [ ] Ensure no visual regressions in template browsers or composition panels

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: None - story is ready for implementation

## Dev Notes

### Architecture Context

**Key Design Principle:** This story completes the UX surfacing of backend capabilities. Stories 24.1-24.3 did the backend work (catalog metadata, translation, portfolio execution). This story ensures the frontend properly displays and interacts with surfaced packs without introducing runtime-specific UI complexity.

**Epic 24 UX Requirement (from UX-DR4):** "Catalog and policy-editing surfaces must expose newly surfaced policy packs without requiring users to understand backend adapter distinctions."

**No Runtime Selector:** The first slice must NOT introduce any frontend runtime/execution engine selector. Users select policies by name/type; the system uses live execution by default (Epic 23). Runtime is backend implementation detail, not user-facing choice.

### Current State (After Stories 24.1-24.3)

**Backend:**
- Catalog API (`GET /api/templates`) returns all 12+ packs with runtime_availability metadata
- LIVE_READY_TYPES includes: carbon_tax, subsidy, rebate, feebate, vehicle_malus, energy_poverty_aid
- TemplateListItem includes: id, name, type, runtime_availability, availability_reason
- All surfaced packs are marked live_ready (Story 24.2)

**Frontend (Story 24.1 completed):**
- TypeScript types include RuntimeAvailability and TemplateListItem fields
- PortfolioTemplateBrowser shows runtime availability badges (Ready/Unavailable)
- TemplateSelectionScreen updated with availability indicators
- Backend API correctly surfaces all packs

**What's Missing (This Story):**
- Frontend type labels for vehicle_malus and energy_poverty_aid in PortfolioTemplateBrowser
- Frontend color mappings for new types
- Mock data updates to include surfaced packs
- Verification that portfolio flows work end-to-end with surfaced packs
- Consistent display across all template browsers

### File: `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx`

**Current TYPE_LABELS (missing surfaced types):**
```typescript
const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  // MISSING: "vehicle_malus", "energy_poverty_aid"
};
```

**Current TYPE_COLORS (missing surfaced types):**
```typescript
const TYPE_COLORS: Record<string, string> = {
  "carbon-tax": "bg-amber-100 text-amber-800",
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
  // MISSING: "vehicle_malus", "energy_poverty_aid"
};
```

**Required Updates:**
Add missing labels and colors. Note: Template type in backend uses underscores (vehicle_malus) but frontend TYPE_LABELS keys may use hyphens (carbon-tax) — verify which format the browser receives.

**Policy Type Name Conversion:**
- Backend uses underscores: `vehicle_malus`, `energy_poverty_aid`
- Frontend templates may use hyphens: `carbon-tax`, `subsidy-energy-retrofit`
- PoliciesStageScreen does conversion: `(t?.type ?? "carbon_tax").replace(/-/g, "_")`
- Need to ensure PortfolioTemplateBrowser handles both formats

### File: `frontend/src/data/mock-data.ts`

**Current mockTemplates (Story 24.1 has partial updates):**
- Has runtime_availability and availability_reason fields
- Has some templates but may be missing surfaced packs
- Needs: vehicle_malus variants (2), energy_poverty_aid variants (2)

**Template IDs for surfaced packs (from backend YAML):**
- Vehicle Malus:
  - `vehicle-malus-flat-rate` — flat malus rate per g/km above threshold
  - `vehicle-malus-tiered` — tiered malus by emission bands
- Energy Poverty Aid:
  - `energy-poverty-aid-flat` — flat aid amount per eligible household
  - `energy-poverty-aid-income-scaled` — aid scaled by income level

**Mock Template Structure:**
```typescript
{
  id: "vehicle-malus-flat-rate",
  name: "Vehicle Malus — Flat Rate",
  type: "vehicle_malus",  // or "vehicle-malus" — verify format
  parameterCount: 3,
  description: "Flat-rate malus for vehicles exceeding emissions threshold",
  parameterGroups: ["emission_threshold", "malus_rate", "rate_schedule"],
  is_custom: true,  // CustomPolicyType
  runtime_availability: "live_ready",
  availability_reason: null,
}
```

### File: `frontend/src/components/screens/PoliciesStageScreen.tsx`

**Current Implementation (Story 20.3):**
- Uses PortfolioTemplateBrowser for template selection
- Handles portfolio composition with surfaced types via policy_type conversion
- Line 210: `policy_type: (t?.type ?? "carbon_tax").replace(/-/g, "_")`
- Line 254: `const t = templates.find((tmpl) => tmpl.type.replace(/-/g, "_") === p.policy_type)`

**Verification Needed:**
- Confirm surfaced packs (vehicle_malus, energy_poverty_aid) appear in browser
- Test add/remove/edit operations with surfaced policies
- Verify portfolio save/load maintains stable references
- Check type badge display in composition panel

### File: `frontend/src/components/screens/PortfolioDesignerScreen.tsx`

**Status:** Deprecated (Story 20.3) — marked `@deprecated` with comment to use PoliciesStageScreen instead. However, if still used in routing, may need updates for consistency.

**Action:** Verify if PortfolioDesignerScreen is still in active routing. If yes, update TYPE_LABELS/TYPE_COLORS there too. If no longer used, skip.

### File: `frontend/src/components/screens/TemplateSelectionScreen.tsx`

**Status:** Check if used in current routing. If yes, verify it displays surfaced packs correctly with runtime availability badges.

**Action:** Search for runtime_availability badge rendering similar to PortfolioTemplateBrowser. Ensure consistent display.

### Policy Type Name Convention

**Backend (Story 24.1-24.3):**
- PolicyType enum values: `CARBON_TAX`, `SUBSIDY`, `REBATE`, `FEEBATE`
- CustomPolicyType values: `vehicle_malus`, `energy_poverty_aid` (underscores)
- Template type in TemplateListItem: enum `.value` (underscores)
- YAML template stems: `vehicle-malus-flat-rate` (hyphens)

**Frontend:**
- TYPE_LABELS keys appear to use hyphens: `"carbon-tax"`, `"subsidy"`
- Need to verify actual template.type value from API response
- PoliciesStageScreen converts hyphens to underscores: `.replace(/-/g, "_")`

**Critical:** The TYPE_LABELS keys must match the template.type values received from the API. If API returns `"vehicle_malus"` (underscore), use that. If it returns `"vehicle-malus"` (hyphen), use that.

### Runtime Availability Badge Display

**Story 24.1 Implementation (PortfolioTemplateBrowser.tsx, lines 113-133):**
```typescript
{template.runtime_availability && (
  <Badge
    variant="outline"
    className={`text-xs ${
      template.runtime_availability === "live_ready"
        ? "bg-green-50 text-green-700 border-green-200"
        : "bg-amber-50 text-amber-700 border-amber-200"
    }`}
  >
    {template.runtime_availability === "live_ready" ? (
      <>
        <CheckCircle2 className="h-3 w-3 mr-1 inline" /> Ready
      </>
    ) : (
      <>
        <AlertCircle className="h-3 w-3 mr-1 inline" /> Unavailable
      </>
    )}
  </Badge>
)}
```

**For Story 24.4:** Ensure this badge pattern is applied consistently across all template browsers. No changes needed to badge logic — surfaced packs are `live_ready` so they show green "Ready" badge.

### Portfolio Composition with Surfaced Policies

**Policy Type Matching (PoliciesStageScreen.tsx, line 254):**
```typescript
const t = templates.find((tmpl) => tmpl.type.replace(/-/g, "_") === p.policy_type);
```

This conversion handles mismatched hyphen/underscore formats. Ensure:
1. Templates from API have correct type field
2. Portfolio policies have correct policy_type field
3. Matching works for vehicle_malus and energy_poverty_aid

**Parameter Groups Display:**
PortfolioCompositionPanel displays parameter groups from template. Verify surfaced packs have correct parameter groups:
- Vehicle Malus: emission_threshold, malus_rate_per_gkm, rate_schedule
- Energy Poverty Aid: income_ceiling, rate_schedule, eligible_categories

### Testing Standards

**Frontend Component Tests:** `frontend/src/components/simulation/__tests__/PortfolioTemplateBrowser.test.tsx`

```typescript
describe("Story 24.4: Surfaced Policy Packs", () => {
  describe("Policy Type Labels", () => {
    it("should display 'Vehicle Malus' label for vehicle_malus type", () => {
      const template = { id: "vehicle-malus-flat", type: "vehicle_malus", ... };
      render(<PortfolioTemplateBrowser templates={[template]} ... />);
      expect(screen.getByText("Vehicle Malus")).toBeInTheDocument();
    });

    it("should display 'Energy Poverty Aid' label for energy_poverty_aid type", () => {
      const template = { id: "energy-aid-flat", type: "energy_poverty_aid", ... };
      render(<PortfolioTemplateBrowser templates={[template]} ... />);
      expect(screen.getByText("Energy Poverty Aid")).toBeInTheDocument();
    });
  });

  describe("Runtime Availability Badges", () => {
    it("should show 'Ready' badge for live_ready surfaced packs", () => {
      const template = {
        id: "vehicle-malus-flat",
        type: "vehicle_malus",
        runtime_availability: "live_ready",
        availability_reason: null,
      };
      render(<PortfolioTemplateBrowser templates={[template]} ... />);
      expect(screen.getByText("Ready")).toBeInTheDocument();
      expect(screen.getByText("Ready")).toHaveClass("text-green-700");
    });

    it("should not show availability_reason for live_ready packs", () => {
      const template = {
        type: "vehicle_malus",
        runtime_availability: "live_ready",
        availability_reason: null,
      };
      render(<PortfolioTemplateBrowser templates={[template]} ... />);
      expect(screen.queryByText("Domain translation pending")).not.toBeInTheDocument();
    });
  });

  describe("No Runtime Selector", () => {
    it("should not display any runtime or engine selector", () => {
      render(<PortfolioTemplateBrowser templates={surfacedTemplates} ... />);
      expect(screen.queryByText(/runtime/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/engine/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/live|replay/i)).not.toBeInTheDocument();
    });
  });
});
```

**Portfolio Save/Load Tests:** `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx`

```typescript
describe("Story 24.4: Portfolio with Surfaced Policies", () => {
  it("should save portfolio containing vehicle_malus policy", async () => {
    // Add vehicle_malus template to composition
    // Save portfolio
    // Verify portfolio includes vehicle_malus
  });

  it("should load portfolio containing energy_poverty_aid policy", async () => {
    // Mock portfolio with energy_poverty_aid
    // Load portfolio
    // Verify policy appears in composition with correct type
  });

  it("should maintain stable references on save/load", async () => {
    // Create portfolio with surfaced policies
    // Save and reload
    // Verify template IDs and types match
  });
});
```

### Project Structure Notes

**Frontend Files to Modify:**
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Add TYPE_LABELS and TYPE_COLORS for surfaced types
- `frontend/src/data/mock-data.ts` — Add surfaced pack templates with runtime_availability="live_ready"

**Frontend Files to Extend (add tests):**
- `frontend/src/components/simulation/__tests__/PortfolioTemplateBrowser.test.tsx` — Add tests for surfaced pack display
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — Add portfolio save/load tests with surfaced policies

**Files to Verify (no changes expected, but verify):**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Confirm surfaced packs work correctly
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` — If still used, verify consistency

**Backend:** No changes required. Stories 24.1-24.3 completed all backend work. This story is pure UX completion.

### Implementation Order Recommendation

1. **Phase 1: Type Labels and Colors** (Visual completion)
   - Update PortfolioTemplateBrowser TYPE_LABELS with surfaced types
   - Update PortfolioTemplateBrowser TYPE_COLORS with surfaced types
   - Add component tests for label/color rendering

2. **Phase 2: Mock Data Updates** (Demo completeness)
   - Add surfaced pack templates to mock-data.ts
   - Verify runtime_availability="live_ready" for surfaced packs
   - Test template browser renders surfaced packs

3. **Phase 3: Portfolio Flow Verification** (End-to-end)
   - Test portfolio save with surfaced policies
   - Test portfolio load with surfaced policies
   - Verify stable references on reload
   - Add integration tests

4. **Phase 4: Cross-Screen Consistency** (UX polish)
   - Verify PoliciesStageScreen displays surfaced packs
   - Check TemplateSelectionScreen (if used) for consistency
   - Verify no runtime selector appears anywhere
   - Non-regression testing for existing packs

### Key Implementation Decisions

**Type Label Format:**
- Use descriptive, space-separated labels: "Vehicle Malus", "Energy Poverty Aid"
- Match existing pattern: "Carbon Tax", "Subsidy", "Rebate", "Feebate"
- Avoid technical jargon: use "Vehicle Malus" not "vehicle_malus"

**Color Assignment:**
- Vehicle Malus: Rose/red tones (penalty/connotation) — `bg-rose-100 text-rose-800`
- Energy Poverty Aid: Cyan/teal tones (aid/positive) — `bg-cyan-100 text-cyan-800`
- Maintain accessibility contrast ratios (Tailwind colors already compliant)

**No Runtime Selector:**
- This story explicitly DOES NOT add any runtime/execution engine UI
- Users select policies; system uses live execution by default
- Runtime choice is backend implementation detail, not user-facing

**Stable References:**
- Template IDs from backend YAML: `vehicle-malus-flat-rate`, `energy-poverty-aid-flat`
- These IDs must not change for saved portfolios to remain compatible
- Frontend displays user-friendly names; backend uses stable IDs

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-24] - Epic 24 requirements
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] - UX design specification (Revision 4.1, UX-DR4)
- [Source: frontend/src/components/simulation/PortfolioTemplateBrowser.tsx] - Template browser component with runtime availability badges (Story 24.1)
- [Source: frontend/src/components/screens/PoliciesStageScreen.tsx] - Stage 1 policies screen (Story 20.3)
- [Source: frontend/src/data/mock-data.ts] - Mock data with Template interface
- [Source: frontend/src/api/types.ts] - TypeScript types for runtime availability
- [Source: _bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md] - Story 24.1 (completed)
- [Source: _bmad-output/implementation-artifacts/24-2-implement-domain-layer-live-translation-for-subsidy-style-policies-without-adapter-interface-changes.md] - Story 24.2 (completed)
- [Source: _bmad-output/implementation-artifacts/24-3-enable-portfolio-execution-for-surfaced-subsidy-and-related-live-policy-packs.md] - Story 24.3 (completed)

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

Story created with comprehensive developer context:
- Current state summary after Stories 24.1-24.3
- Frontend type label and color mapping requirements
- Mock data structure for surfaced packs
- Portfolio save/load verification approach
- Complete testing standards with component and integration tests
- No-runtime-selector requirement (UX-DR4 compliance)
- Implementation order recommendations

### File List

**Story file created:**
- `_bmad-output/implementation-artifacts/24-4-surface-live-capable-policy-packs-in-workspace-catalog-flows-without-runtime-specific-ux.md`

**Files to modify (implementation):**
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Add TYPE_LABELS and TYPE_COLORS
- `frontend/src/data/mock-data.ts` — Add surfaced pack templates
- `frontend/src/components/simulation/__tests__/PortfolioTemplateBrowser.test.tsx` — Add tests
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — Add tests

**Files to verify (no changes expected):**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Verify surfaced packs work
- `frontend/src/api/types.ts` — Already has RuntimeAvailability type (Story 24.1)
- `src/reformlab/server/routes/templates.py` — No changes needed (Story 24.1-24.3 completed backend)

