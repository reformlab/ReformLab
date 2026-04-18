# Story 24.4: Surface live-capable policy packs in workspace catalog flows without runtime-specific UX

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want to see and use all live-capable policy packs (including newly surfaced subsidy, vehicle_malus, and energy_poverty_aid) in the policy catalog and portfolio composition flows,
so that I can discover, configure, and execute these policies through the standard workspace interface without needing to understand runtime internals or engine selection.

## Acceptance Criteria

1. Given the policy browser and composition flows (PortfolioTemplateBrowser, PoliciesStageScreen), when rendered, then newly surfaced live-capable packs (subsidy, vehicle_malus, energy_poverty_aid) are available alongside existing packs (carbon_tax, rebate, feebate) with correct type labels and colors: "Vehicle Malus" with rose color (bg-rose-100 text-rose-800), "Energy Poverty Aid" with cyan color (bg-cyan-100 text-cyan-800).
2. Given a surfaced pack with live-ready status (runtime_availability="live_ready"), when shown to the user, then the pack displays as available with green "Ready" badge (bg-green-50 text-green-700 border-green-200) with CheckCircle2 icon, without exposing backend runtime mechanics or engine terminology.
3. Given the first-slice policy workflows, when reviewed, then no runtime or engine selector is introduced in any policy surface (PortfolioTemplateBrowser, PoliciesStageScreen, TemplateSelectionScreen if active) — users select policies by name/type without choosing between execution engines.
4. Given a scenario or portfolio using a surfaced pack (vehicle_malus, energy_poverty_aid), when saved and reloaded, then the pack reference remains stable (template_id, policy_type) and loads correctly with correct display label and color.
5. Given template browsers across the workspace (PoliciesStageScreen, PortfolioDesignerScreen if active, TemplateSelectionScreen if active), when displaying policy types, then consistent type labels and colors are used for all policy types including newly surfaced ones.
6. Given policy type filtering or grouping in PortfolioTemplateBrowser, when applied, then vehicle_malus templates are grouped under "Vehicle Malus" label and energy_poverty_aid templates under "Energy Poverty Aid" label without being misclassified or hidden.
7. Given a portfolio containing surfaced policies, when the composition panel (PortfolioCompositionPanel) displays it, then each policy shows its correct type label ("Vehicle Malus", "Energy Poverty Aid") and parameter groups (e.g., emission_threshold, malus_rate_per_gkm, rate_schedule for vehicle_malus).
8. Given the saved portfolios list, when displayed, then portfolios containing surfaced policies show the correct policy count (number of policies in portfolio) and description without errors.

## Tasks / Subtasks

- [x] Fix type format mismatch in PortfolioTemplateBrowser TYPE_LABELS and TYPE_COLORS (AC: #1, #5, #6)
  - [x] Add underscore-format keys for existing types: "carbon_tax", "subsidy", "rebate", "feebate"
  - [x] Add underscore-format entries for new types: "vehicle_malus" → "Vehicle Malus", "energy_poverty_aid" → "Energy Poverty Aid"
  - [x] Keep hyphen-format keys for backward compatibility with mock data
  - [x] Match PortfolioCompositionPanel's dual-format pattern for consistency
  - [x] Add underscore-format color mappings: "vehicle_malus" → "bg-rose-100 text-rose-800", "energy_poverty_aid" → "bg-cyan-100 text-cyan-800"

- [x] Verify runtime availability badges work correctly (AC: #2, #3)
  - [x] Confirm surfaced packs display "Ready" badge (green) for live_ready status
  - [x] Verify no engine/runtime selector appears in policy flows
  - [x] Ensure availability_reason is not displayed for live_ready packs (only for unavailable)
  - [x] Test that Badge variant and styling match Story 24.1 implementation

- [x] Add runtime_availability and availability_reason to ALL existing mockTemplates (AC: #1, #2)
  - [x] carbon-tax-flat, carbon-tax-progressive, carbon-tax-dividend: runtime_availability="live_ready", availability_reason=null
  - [x] subsidy-energy: runtime_availability="live_ready", availability_reason=null
  - [x] feebate-vehicle: runtime_availability="live_ready", availability_reason=null

- [x] Add surfaced pack templates to mock-data.ts with full runtime_availability metadata (AC: #1, #6)
  - [x] vehicle-malus-flat-rate: type="vehicle_malus", parameterGroups=["emission_threshold", "malus_rate_per_gkm", "rate_schedule", "threshold_schedule"], parameterCount=4, runtime_availability="live_ready"
  - [x] vehicle-malus-french-2026: type="vehicle_malus", parameterGroups=["emission_bands", "malus_schedule", "exemption_categories"], parameterCount=5, runtime_availability="live_ready"
  - [x] energy-poverty-cheque-energie: type="energy_poverty_aid", parameterGroups=["income_ceiling", "rate_schedule", "eligible_categories"], parameterCount=4, runtime_availability="live_ready"
  - [x] energy-poverty-generous: type="energy_poverty_aid", parameterGroups=["income_ceiling", "rate_schedule", "eligible_categories", "household_size_multiplier"], parameterCount=5, runtime_availability="live_ready"

- [x] Verify portfolio loading with surfaced packs (AC: #4, #7)
  - [x] Test portfolio load with vehicle_malus policy maps correctly to template
  - [x] Test portfolio load with energy_poverty_aid policy maps correctly to template
  - [x] Verify policy_type matching handles underscore conversion correctly (vehicle_malus ↔ vehicle-malus)
  - [x] Ensure composition panel displays correct parameter groups for surfaced types

- [x] Verify cross-browser consistency for type labels and colors (AC: #5)
  - [x] Check if TemplateSelectionScreen uses TYPE_LABELS/TYPE_COLORS - if yes, update same as PortfolioTemplateBrowser
  - [x] Check if PortfolioDesignerScreen uses TYPE_LABELS/TYPE_COLORS - if yes, update same as PortfolioTemplateBrowser
  - [x] Verify all browsers display surfaced packs with same labels and colors
  - [x] Document which screens were checked and updated

- [x] Add frontend tests for surfaced pack display (AC: #1, #5, #6)
  - [x] Test PortfolioTemplateBrowser renders vehicle_malus with correct label/color
  - [x] Test PortfolioTemplateBrowser renders energy_poverty_aid with correct label/color
  - [x] Test runtime availability badge displays correctly for surfaced packs
  - [x] Test type grouping includes surfaced packs in correct groups
  - [x] Test portfolio save/load with surfaced packs maintains stable references

- [x] Verify PoliciesStageScreen works with surfaced packs (AC: #1, #7)
  - [x] Confirm surfaced packs appear in template browser
  - [x] Test adding surfaced packs to portfolio composition
  - [x] Verify composition panel shows correct type labels for surfaced policies
  - [x] Test portfolio save/load with surfaced packs through PoliciesStageScreen

- [x] Non-regression: verify existing packs still work (AC: #1, #5, #8)
  - [x] Test carbon_tax templates display "Carbon Tax" label with amber color (bg-amber-100 text-amber-800)
  - [x] Test subsidy templates display "Subsidy" label with emerald color (bg-emerald-100 text-emerald-800)
  - [x] Test rebate templates display "Rebate" label with blue color (bg-blue-100 text-blue-800)
  - [x] Test feebate templates display "Feebate" label with violet color (bg-violet-100 text-violet-800)
  - [x] Test all existing templates show "Ready" badge (green bg-green-50 text-green-700)
  - [x] Test all existing templates have correct parameter groups displayed
  - [x] Test all existing templates are selectable and addable to portfolio
  - [x] Test saved portfolios with existing templates load without errors

#### Review Follow-ups (AI)
- [x] [AI-Review] CRITICAL: Fix type format mismatch in PortfolioTemplateBrowser - adopt dual-format pattern from PortfolioCompositionPanel (both hyphen and underscore keys)
- [x] [AI-Review] CRITICAL: Add runtime_availability and availability_reason to ALL existing mockTemplates entries
- [x] [AI-Review] HIGH: Specify exact surfaced pack templates to add to mock-data.ts (4 variants with complete parameterGroups)
- [x] [AI-Review] HIGH: Add cross-browser consistency verification task to ensure all template browsers use same labels and colors
- [x] [AI-Review] MEDIUM: Clarify expected type label and color values in acceptance criteria and dev notes
- [x] [Validation-Synthesis] Applied fixes from validation synthesis: type format contract, mock data completeness, cross-component verification checklist

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

**Current TYPE_LABELS (missing surfaced types and has type format mismatch):**
```typescript
const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",  // ❌ Backend returns "carbon_tax" (underscore)
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  // MISSING: underscore format for existing types, all surfaced types
};
```

**Current TYPE_COLORS (same issues as TYPE_LABELS):**
```typescript
const TYPE_COLORS: Record<string, string> = {
  "carbon-tax": "bg-amber-100 text-amber-800",
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
  // MISSING: underscore format for existing types, all surfaced types
};
```

**CRITICAL BUG FIX REQUIRED:**
- Backend API returns `type: "carbon_tax"` (underscore format from PolicyType enum value)
- PortfolioTemplateBrowser has hyphen-format keys: `"carbon-tax"`
- Lookup fails: `TYPE_LABELS["carbon_tax"]` → undefined
- Result: Falls back to displaying raw type name "carbon_tax" with default gray color

**Required Fix:**
Adopt PortfolioCompositionPanel's dual-format pattern (already handles both formats):
```typescript
const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",
  "carbon_tax": "Carbon Tax",  // Add underscore format
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  "vehicle_malus": "Vehicle Malus",  // Use underscore format
  "energy_poverty_aid": "Energy Poverty Aid",  // Use underscore format
};

const TYPE_COLORS: Record<string, string> = {
  "carbon-tax": "bg-amber-100 text-amber-800",
  "carbon_tax": "bg-amber-100 text-amber-800",  // Add underscore format
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
  "vehicle_malus": "bg-rose-100 text-rose-800",
  "energy_poverty_aid": "bg-cyan-100 text-cyan-800",
};
```

**Expected Type Label and Color Mappings:**

| Type Value (from API) | Label | Color Classes |
|-----------------------|-------|---------------|
| carbon_tax / carbon-tax | Carbon Tax | bg-amber-100 text-amber-800 |
| subsidy | Subsidy | bg-emerald-100 text-emerald-800 |
| rebate | Rebate | bg-blue-100 text-blue-800 |
| feebate | Feebate | bg-violet-100 text-violet-800 |
| vehicle_malus | Vehicle Malus | bg-rose-100 text-rose-800 |
| energy_poverty_aid | Energy Poverty Aid | bg-cyan-100 text-cyan-800 |

### File: `frontend/src/data/mock-data.ts`

**CRITICAL: Mock data is missing runtime_availability fields**
- Template interface (lines 21-23) defines runtime_availability and availability_reason as required fields (added in Story 24.1)
- However, mockTemplates entries (lines 97-138) do NOT include these fields
- This will cause TypeScript errors or runtime undefined errors when PortfolioTemplateBrowser tries to access template.runtime_availability

**Fix Required:**
Add runtime_availability and availability_reason to ALL existing mockTemplates:
```typescript
{
  id: "carbon-tax-flat",
  name: "Carbon Tax — Flat Rate",
  type: "carbon-tax",
  parameterCount: 8,
  description: "Flat carbon tax rate applied uniformly across all households",
  parameterGroups: ["Tax Rates", "Thresholds"],
  is_custom: false,
  runtime_availability: "live_ready",  // ADD THIS
  availability_reason: null,  // ADD THIS
}
```

**Surfaced Pack Templates to Add:**

Vehicle Malus templates (2 variants):
```typescript
{
  id: "vehicle-malus-flat-rate",
  name: "Vehicle Malus — Flat Rate",
  type: "vehicle_malus",  // Backend API returns underscore format
  parameterCount: 4,
  description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
  parameterGroups: ["emission_threshold", "malus_rate_per_gkm", "rate_schedule", "threshold_schedule"],
  is_custom: true,
  runtime_availability: "live_ready",
  availability_reason: null,
},
{
  id: "vehicle-malus-french-2026",
  name: "Vehicle Malus — French 2026 System",
  type: "vehicle_malus",
  parameterCount: 5,
  description: "Tiered malus system following French 2026 emission bands",
  parameterGroups: ["emission_bands", "malus_schedule", "exemption_categories"],
  is_custom: true,
  runtime_availability: "live_ready",
  availability_reason: null,
}
```

Energy Poverty Aid templates (2 variants):
```typescript
{
  id: "energy-poverty-cheque-energie",
  name: "Energy Poverty Aid — Cheque Énergie",
  type: "energy_poverty_aid",
  parameterCount: 4,
  description: "Flat energy voucher for eligible households based on income ceiling",
  parameterGroups: ["income_ceiling", "rate_schedule", "eligible_categories"],
  is_custom: true,
  runtime_availability: "live_ready",
  availability_reason: null,
},
{
  id: "energy-poverty-generous",
  name: "Energy Poverty Aid — Generous",
  type: "energy_poverty_aid",
  parameterCount: 5,
  description: "Enhanced aid with higher income ceiling and household size multiplier",
  parameterGroups: ["income_ceiling", "rate_schedule", "eligible_categories", "household_size_multiplier"],
  is_custom: true,
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

**Status:** Deprecated (Story 20.3) — marked `@deprecated` with comment to use PoliciesStageScreen instead.

**Routing Investigation Required:**
- Check App.tsx or routing config for PortfolioDesignerScreen references
- If route exists and is active: verify it uses PortfolioTemplateBrowser, update TYPE_LABELS/TYPE_COLORS if needed
- If route doesn't exist or is inactive: skip PortfolioDesignerScreen updates and document findings
- This investigation is part of the cross-browser consistency verification task

### File: `frontend/src/components/screens/TemplateSelectionScreen.tsx`

**Status:** Check if used in current routing. If yes, verify it displays surfaced packs correctly with runtime availability badges.

**Action:** Search for runtime_availability badge rendering similar to PortfolioTemplateBrowser. Ensure consistent display.

### Policy Type Name Convention

**Backend (Story 24.1-24.3):**
- PolicyType enum values: `CARBON_TAX`, `SUBSIDY`, `REBATE`, `FEEBATE`
- CustomPolicyType values: `vehicle_malus`, `energy_poverty_aid` (underscores)
- Template type in TemplateListItem: enum `.value` (underscores)
- YAML template stems: `vehicle-malus-flat-rate` (hyphens)

**Frontend Type Format Mismatch:**
- TYPE_LABELS in PortfolioTemplateBrowser use hyphen keys: `"carbon-tax"`
- Backend API returns underscore format: `"carbon_tax"` from PolicyType enum value
- This causes lookup failures and incorrect display

**Existing Pattern in PortfolioCompositionPanel:**
PortfolioCompositionPanel already handles the type format mismatch by having duplicate keys:
```typescript
const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",
  "carbon_tax": "Carbon Tax",  // Duplicate for underscore format
  // ... other types
};
```
This is a workaround for the type format mismatch. **This story should extend the same pattern to PortfolioTemplateBrowser for consistency.**

**Contract:**
- API `TemplateListItem.type` uses underscore values (`carbon_tax`, `vehicle_malus`, `energy_poverty_aid`)
- Mock data uses hyphen format for some templates (`"carbon-tax"`) for historical reasons
- UI maps display-only labels/colors using both hyphen and underscore keys for backward compatibility
- PoliciesStageScreen converts hyphens to underscores: `.replace(/-/g, "_")`
- PortfolioTemplateBrowser should adopt the same dual-format pattern as PortfolioCompositionPanel

**Why Both Formats Exist:**
- Backend PolicyType enum uses underscores: `CARBON_TAX` → value `"carbon_tax"`
- Mock data was created before Story 24.1 and used hyphens: `"carbon-tax"`
- PortfolioCompositionPanel added duplicate keys to handle both formats
- This story should extend the same pattern to PortfolioTemplateBrowser

### Runtime Availability Badge Display

**Story 24.1 Implementation Pattern (PortfolioTemplateBrowser.tsx, lines 114-133):**

This pattern should work for surfaced packs without changes since they have `runtime_availability="live_ready"`:
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

**Expected Badge Behavior for Surfaced Packs:**
- vehicle_malus templates: Shows green "Ready" badge with CheckCircle2 icon
- energy_poverty_aid templates: Shows green "Ready" badge with CheckCircle2 icon
- availability_reason is null for live_ready packs, so no reason text is displayed

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

Required test coverage for Story 24.4:
- Test vehicle_malus displays "Vehicle Malus" label with rose color (bg-rose-100 text-rose-800)
- Test energy_poverty_aid displays "Energy Poverty Aid" label with cyan color (bg-cyan-100 text-cyan-800)
- Test runtime availability badge shows "Ready" for live_ready surfaced packs (bg-green-50 text-green-700)
- Test type grouping includes surfaced packs in correct groups
- Test portfolio save/load maintains stable references (template_id, policy_type)
- Test no runtime selector controls exist in policy flows

Example test structure:
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

### Cross-Component Verification Checklist

**After implementing type labels and colors, verify consistency across all template browsers:**
- [ ] PortfolioTemplateBrowser displays vehicle_malus with "Vehicle Malus" label and rose color
- [ ] PortfolioTemplateBrowser displays energy_poverty_aid with "Energy Poverty Aid" label and cyan color
- [ ] PortfolioCompositionPanel displays same labels and colors for surfaced packs
- [ ] (If used) TemplateSelectionScreen displays same labels and colors
- [ ] (If used) PortfolioDesignerScreen displays same labels and colors
- [ ] All browsers show green "Ready" badge for surfaced packs (live_ready status)
- [ ] Type filtering/grouping works correctly for surfaced types across all browsers
- [ ] Document which screens were checked and any screens that were determined to be inactive

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

**Color Selection Rationale:**
- Vehicle Malus (rose/red): Penalty connotation, indicates negative financial impact
- Energy Poverty Aid (cyan/teal): Aid/positive connotation, indicates support
- Pattern follows semantic coloring: penalties=red/warm, support=green/cool
- Colors maintain Tailwind's accessibility compliance (contrast ratios)

**No Runtime Selector:**
- This story explicitly DOES NOT add any runtime/execution engine UI
- Users select policies; system uses live execution by default
- Runtime choice is backend implementation detail, not user-facing

**Stable References:**
- Template IDs from backend YAML: `vehicle-malus-flat-rate`, `vehicle-malus-french-2026`, `energy-poverty-cheque-energie`, `energy-poverty-generous`
- These IDs must not change for saved portfolios to remain compatible
- Frontend displays user-friendly names; backend uses stable IDs

**Backend Template IDs for Mock Data Reference:**

| Policy Type | Template ID (YAML filename) | Description |
|-------------|----------------------------|-------------|
| vehicle_malus | vehicle-malus-flat-rate | Flat malus rate per g/km above threshold |
| vehicle_malus | vehicle-malus-french-2026 | French 2026 tiered malus system |
| energy_poverty_aid | energy-poverty-cheque-energie | Energy check voucher system |
| energy_poverty_aid | energy-poverty-generous | Generous aid with higher income ceiling |

Use these IDs in mock data to match backend structure.

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

**Post-Validation Updates (2026-04-18):**
- Fixed critical type format mismatch: PortfolioTemplateBrowser must adopt dual-format pattern from PortfolioCompositionPanel (both hyphen and underscore keys)
- Added explicit mock data updates: all existing templates need runtime_availability and availability_reason fields
- Specified exact surfaced pack templates to add (4 variants with complete parameterGroups)
- Added cross-browser consistency verification task
- Added expected type label and color mappings table
- Added cross-component verification checklist
- Made acceptance criteria more objectively verifiable with specific color classes

**Implementation Completion (2026-04-18):**
- Fixed type format mismatch in PortfolioTemplateBrowser TYPE_LABELS and TYPE_COLORS by adopting dual-format pattern (both hyphen and underscore keys)
- Added surfaced type labels: "vehicle_malus" → "Vehicle Malus", "energy_poverty_aid" → "Energy Poverty Aid"
- Added surfaced type colors: "vehicle_malus" → "bg-rose-100 text-rose-800", "energy_poverty_aid" → "bg-cyan-100 text-cyan-800"
- Updated PortfolioCompositionPanel with same TYPE_LABELS and TYPE_COLORS for consistency
- Added runtime_availability="live_ready" and availability_reason=null to all 5 existing mockTemplates
- Added 4 surfaced pack templates to mock-data.ts with complete metadata (2 vehicle_malus, 2 energy_poverty_aid)
- Verified runtime availability badges work correctly (green "Ready" badge for live_ready packs)
- Verified no runtime/engine selector appears in policy flows
- Added 15 new tests (9 in PortfolioTemplateBrowser, 6 in PoliciesStageScreen) for surfaced pack display and portfolio operations
- All 61 tests pass for modified files (PortfolioTemplateBrowser: 16, PortfolioCompositionPanel: 8, PoliciesStageScreen: 37)
- Cross-browser verification: TemplateSelectionScreen doesn't use TYPE_LABELS/TYPE_COLORS; PortfolioDesignerScreen is deprecated and inactive
- Non-regression verified: existing packs (carbon_tax, subsidy, rebate, feebate) display correctly with proper labels and colors
- Added color selection rationale and backend template IDs reference

### File List

**Story file created:**
- `_bmad-output/implementation-artifacts/24-4-surface-live-capable-policy-packs-in-workspace-catalog-flows-without-runtime-specific-ux.md`

**Files modified (implementation):**
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Added TYPE_LABELS and TYPE_COLORS with dual-format keys and surfaced types
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Added surfaced types (vehicle_malus, energy_poverty_aid) for consistency
- `frontend/src/data/mock-data.ts` — Added runtime_availability/availability_reason to existing templates + 4 surfaced pack templates
- `frontend/src/components/simulation/__tests__/PortfolioTemplateBrowser.test.tsx` — Added 9 Story 24.4 tests
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — Added 6 Story 24.4 tests
- `_bmad-output/implementation-artifacts/24-4-surface-live-capable-policy-packs-in-workspace-catalog-flows-without-runtime-specific-ux.md` — Updated task checkboxes, status, and completion notes

**Files verified (no changes needed):**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Verified surfaced packs work correctly
- `frontend/src/components/screens/TemplateSelectionScreen.tsx` — Does not use TYPE_LABELS/TYPE_COLORS (checked)
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` — Deprecated, inactive (checked)
- `frontend/src/api/types.ts` — Already has RuntimeAvailability type (Story 24.1)

