# Story 27.9: Improve policy-set auto-name suggestion

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst building a policy set,
I want the auto-suggested name to meaningfully describe my policy composition using policy types, categories, and key parameters,
so that the suggested name is immediately recognizable and useful without requiring manual editing.

## Acceptance Criteria

1. **AC-1 (single-policy type-category names):** Given a composition with exactly one policy, when the save dialog opens, then the suggested name uses the format `"{Type} — {Category}"` (e.g., "tax-carbon-emissions", "subsidy-energy-consumption") instead of just the slugified policy name.
2. **AC-2 (from-scratch policy names):** Given a composition with a from-scratch policy that already has a "{Type} — {Category}" name, when the save dialog opens, then the suggested name reuses that name without duplicating the type-category pattern (e.g., "tax-carbon-emissions" NOT "tax-tax-carbon-emissions").
3. **AC-3 (multi-policy dominant category):** Given a composition with 2+ policies from the same category (e.g., 3 carbon emission policies), when the save dialog opens, then the suggested name uses the dominant category: "{category}-policies" (e.g., "carbon-emissions-policies", "vehicle-emissions-policies").
4. **AC-4 (multi-policy mixed categories):** Given a composition with policies from different categories, when the save dialog opens, then the suggested name uses the pattern "{primary-category}-plus-{N}-more" (e.g., "carbon-emissions-plus-1-more") where "primary-category" is the category of the first policy.
5. **AC-5 (parameter-based enrichment for single policy):** Given a single policy with a configured primary parameter value (rate, threshold, or budget), when the save dialog opens, then the suggested name includes the parameter value if adding it keeps the slug under 48 chars (e.g., "tax-carbon-emissions-44eur", "subsidy-vehicles-20pct").
6. **AC-6 (manual-edit freeze rule preserved):** Given the analyst has manually edited the suggested name, when the composition changes, then the suggestion stops updating and the manual name is preserved. The freeze flag resets when the save dialog closes and reopens.
7. **AC-7 (backward compatibility with validation):** Given all generated names, when they are checked against `validatePortfolioName()`, then all names pass the regex `^(?:[a-z7-9]{1,64}|[a-z0-9][a-z0-9-]{0,62}[a-z0-9])$` and are ≤ 64 characters.
8. **AC-8 (empty composition fallback):** Given an empty composition (0 policies), when the save dialog opens, then the suggested name remains "untitled-portfolio" (no change to existing behavior).

## Tasks / Subtasks

- [ ] **Task 1: Enhance `generatePortfolioSuggestion()` with type-category awareness** (AC: #1, #2, #3, #4, #8)
  - [ ] Subtask 1.1: Update function signature to accept `categories?: Category[] | null` parameter
  - [ ] Subtask 1.2: Add helper `extractTypeAndCategory(entry, templates, categories)` that returns `{policyType, categoryId, categoryLabel}`:
    - For from-scratch policies: use `entry.policy_type` and `entry.category_id`
    - For template policies: use `template.type` and `template.category_id`
  - [ ] Subtask 1.3: Add helper `slugifyTypeAndCategory(policyType, categoryLabel)` that returns "{type}-{slugified-category}" (e.g., "tax-carbon-emissions")
  - [ ] Subtask 1.4: Add helper `getDominantCategory(composition, templates, categories)` that counts policies by category and returns the most common category ID (or first policy's category if tie)
  - [ ] Subtask 1.5: Update `generatePortfolioSuggestion()` to implement new naming patterns:
    - 0 policies: return "untitled-portfolio" (unchanged)
    - 1 policy: return `slugifyTypeAndCategory(type, categoryLabel)` unless from-scratch with "{Type} — {Category}" name pattern
    - 2+ same-category: return `{slugified-category}-policies`
    - 2+ mixed-category: return `{primary-category}-plus-{N-1}-more`
  - [ ] Subtask 1.6: Ensure all slugs pass `validatePortfolioName()` regex and ≤ 64 chars
  - [ ] Subtask 1.7: Export `extractTypeAndCategory` and `getDominantCategory` for testing

- [ ] **Task 2: Add parameter-based enrichment for single policies** (AC: #5)
  - [ ] Subtask 2.1: Add helper `extractPrimaryParameterValue(entry, schemas)` that finds the first "headline" parameter value:
    - Priority order: rate > threshold > budget > exemption
    - Returns `{paramId, value, unit}` or `null` if none configured
  - [ ] Subtask 2.2: Add helper `formatParameterForName(value, unit)` that returns slugifiable string:
    - Unit "%" → "pct" (e.g., "20pct")
    - Unit "€/tonne" → "eur" (e.g., "44eur")
    - Other units → slugified unit name
  - [ ] Subtask 2.3: Update single-policy naming to append parameter value if total length ≤ 48 chars:
    - Pattern: `{type-category}-{paramValue}` (e.g., "tax-carbon-emissions-44eur")
    - Skip if adding value would exceed 48 chars (leaves room for variations)
  - [ ] Subtask 2.4: Add tests for parameter extraction and formatting edge cases (zero values, null schemas, missing units)

- [ ] **Task 3: Update `usePortfolioSaveDialog` to pass categories** (AC: #1, #3, #4)
  - [ ] Subtask 3.1: Add `categories?: Category[] | null` to `UsePortfolioSaveDialogParams` interface
  - [ ] Subtask 3.2: Update hook calls to `generatePortfolioSuggestion()` to include `categories` parameter
  - [ ] Subtask 3.3: Update `openSaveDialog` effect to pass categories to suggestion generator
  - [ ] Subtask 3.4: Update manual-edit flag effect to regenerate suggestion when dialog reopens (resets freeze per AC-6)

- [ ] **Task 4: Update `PoliciesStageScreen` to provide categories** (AC: #1, #3, #4)
  - [ ] Subtask 4.1: Pass `categories` state to `usePortfolioSaveDialog` hook (categories already fetched in PoliciesStageScreen)
  - [ ] Subtask 4.2: Verify category loading state handling (null = loading, [] = failed/empty)

- [ ] **Task 5: Add tests** (AC: all)
  - [ ] Subtask 5.1: Add `generatePortfolioSuggestion` tests in `frontend/src/utils/__tests__/naming.test.ts`:
    - Single policy with category: "tax-carbon-emissions"
    - Single from-scratch policy: uses existing "{Type} — {Category}" name
    - Multi-policy same category: "carbon-emissions-policies"
    - Multi-policy mixed category: "carbon-emissions-plus-1-more"
    - Empty composition: "untitled-portfolio"
  - [ ] Subtask 5.2: Add parameter-based enrichment tests:
    - Rate parameter: "tax-carbon-emissions-44eur"
    - Threshold parameter: "tax-income-15000eur"
    - Percentage unit: "subsidy-vehicles-20pct"
    - Skip enrichment if too long (> 48 chars)
  - [ ] Subtask 5.3: Add manual-edit freeze behavior test:
    - User edits name → composition changes → name stays frozen
    - Dialog closes and reopens → freeze resets, suggestion updates
  - [ ] Subtask 5.4: Add validation tests: all suggestions pass `validatePortfolioName()`
  - [ ] Subtask 5.5: Add integration test in `PoliciesStageScreen.policySets.test.tsx`:
    - Open save dialog → verify suggested name uses type-category
    - Add policy → verify suggestion updates to multi-policy pattern

- [ ] **Task 6: Quality gates** (AC: all)
  - [ ] Subtask 6.1: Run `npm run typecheck` — must pass with new helper functions
  - [ ] Subtask 6.2: Run `npm run lint` — must pass
  - [ ] Subtask 6.3: Run `npm test` — all naming and save-dialog tests must pass
  - [ ] Subtask 6.4: Verify existing functionality: save/load/clone flows still work with new naming

## Dev Notes

### Current Behavior

**Existing `generatePortfolioSuggestion()` in `frontend/src/utils/naming.ts:100-125`:**
```typescript
export function generatePortfolioSuggestion(
  templates: readonly Template[],
  composition: readonly CompositionEntry[],
): string {
  if (composition.length === 0) {
    return "untitled-portfolio";
  }
  if (composition.length === 1) {
    const entry = composition[0]!;
    const template = templates.find((t) => t.id === entry.templateId);
    const name = template?.name ?? entry.name;
    return slugify(name);
  }
  if (composition.length === 2) {
    const slug1 = slugify(composition[0]!.name);
    const slug2 = slugify(composition[1]!.name);
    return truncateSlug(`${slug1}-plus-${slug2}`);
  }
  // 3+ policies: use "first-slug-plus-(N-1)-more" pattern
  const firstSlug = slugify(composition[0]!.name);
  const remainingCount = composition.length - 1;
  return truncateSlug(`${firstSlug}-plus-${remainingCount}-more`);
}
```

**Problems with current approach:**
1. Uses policy names (`entry.name`) which are human-friendly but not semantic
2. "slug1-plus-slug2" concatenates full names, quickly hitting 64-char limit
3. No visibility into policy types or categories (key differentiators)
4. No parameter context (e.g., "44€/tonne carbon tax" vs "100€/tonne")

### New Data Available (Post-Epic 25)

**Each `CompositionEntry` (PortfolioCompositionPanel.tsx:27-43) now has:**
```typescript
export interface CompositionEntry {
  templateId: string;
  name: string;
  parameters: Record<string, number>;  // ← Configured values (Story 27.3)
  rateSchedule: Record<string, number>;
  instanceId?: string;
  policy_type?: string;  // ← "tax" | "subsidy" | "transfer" (Story 25.3)
  category_id?: string;  // ← Category reference (Story 25.1)
  parameter_groups?: string[];
  editableParameterGroups?: EditableParameterGroup[];
}
```

**Categories API (`GET /api/categories`) - Story 25.1:**
```typescript
interface Category {
  id: string;           // e.g., "carbon-emissions", "vehicle-emissions"
  label: string;        // e.g., "Carbon Emissions", "Vehicle Emissions"
  columns: string[];
  compatible_types: string[];
  formula_explanation: string;
  description: string;
}
```

**Template type with category (frontend/src/data/mock-data.ts:28-38):**
```typescript
export interface Template {
  id: string;
  name: string;
  type: string;           // Policy type (e.g., "carbon-tax", "vehicle-subsidy")
  category_id?: string;   // Story 25.1 / Task 2.3: Category ID for grouping
  // ... other fields
}
```

### New Naming Algorithm

```
Given composition C, templates T, categories K:

If C.length === 0:
  Return "untitled-portfolio"

If C.length === 1:
  Let entry = C[0]
  Let {policyType, categoryId, categoryLabel} = extractTypeAndCategory(entry, T, K)

  // Avoid double-naming from-scratch policies
  If entry.name matches "{Type} — {Category}" pattern:
    Return slugify(entry.name)

  // Base name from type and category
  Let baseName = slugifyTypeAndCategory(policyType, categoryLabel)

  // Optional parameter enrichment (if ≤ 48 chars)
  Let paramValue = extractPrimaryParameterValue(entry, schemas)
  If paramValue AND (baseName.length + paramValue.length ≤ 48):
    Return baseName + "-" + paramValue

  Return baseName

If C.length >= 2:
  Let dominantCategory = getDominantCategory(C, T, K)
  Let categorySlug = slugify(dominantCategory.label)

  // Check if all policies share the same category
  If all policies in C have same category:
    Return categorySlug + "-policies"

  // Mixed categories: use first policy's category
  Return categorySlug + "-plus-" + (C.length - 1) + "-more"
```

### Type Normalization

**Policy types (taxonomy from Epic 25):**
- "tax" (from `policy_type` or template type mapping)
- "subsidy"
- "transfer"
- Fallback to "policy" if unrecognized

**Type slug mapping:**
```typescript
const TYPE_SLUGS: Record<string, string> = {
  "carbon-tax": "tax",
  "vehicle-subsidy": "subsidy",
  "housing-transfer": "transfer",
  // Add more as needed
};
```

### Parameter Extraction Strategy

**Priority order for "headline" parameter (Story 27.3 patterns):**
1. Parameters containing "rate" (e.g., `tax_rate`, `subsidy_rate`)
2. Parameters containing "threshold" (e.g., `exemption_threshold`)
3. Parameters containing "budget" (e.g., `program_budget`)
4. Parameters containing "exemption" (fallback)

**Value formatting for slug:**
- Percentage (`unit === "%"`) → strip decimal, append "pct" (e.g., 0.2 → "20pct")
- Currency-like units (€/tonne, €/vehicle) → strip symbol, append "eur" (e.g., 44 → "44eur")
- Other units → slugify unit name (e.g., "km" → "km")

**Resolution order (from Story 27.3):**
```typescript
// 1. Configured value (highest priority)
if (paramId in entry.parameters) {
  return entry.parameters[paramId];
}
// 2. Schema baseline
if (schema?.baseline !== undefined) {
  return schema.baseline;
}
// 3. No value available
return null;
```

### Manual-Edit Freeze Implementation

**Current behavior (usePortfolioSaveDialog.ts:76-82):**
```typescript
const [saveDialogNameManuallyEdited, setSaveDialogNameManuallyEdited] = useState(false);

useEffect(() => {
  if (!saveDialogOpen || saveDialogNameManuallyEdited) return;
  const suggestion = generatePortfolioSuggestion(templates, composition);
  setPortfolioSaveName(suggestion);
}, [composition, templates, saveDialogOpen, saveDialogNameManuallyEdited]);
```

**Freeze reset mechanism:**
- `openSaveDialog()` already sets `setSaveDialogNameManuallyEdited(false)` (line 89)
- Dialog close (`closeSaveDialog`) also resets flag (line 95)
- This AC is already satisfied by existing code — no changes needed

### Edge Cases

1. **No categories loaded (categories = null):** Fall back to policy name only (old behavior)
2. **Category not found for policy:** Use "other" as category slug
3. **Policy type missing:** Use "policy" as default type
4. **Parameter value is 0:** Still include it (0 is a valid configuration, e.g., 0% subsidy)
5. **Slug exceeds 64 chars:** Truncate at 64 chars, removing trailing hyphen (existing `truncateSlug`)
6. **All policies unconfigured:** Use type-category only, skip parameter enrichment
7. **From-scratch policy with custom name:** Detect "{Type} — {Category}" pattern via regex: `/^(Tax|Subsidy|Transfer) — /`

### Files to Modify

- **`frontend/src/utils/naming.ts`:**
  - Add `extractTypeAndCategory()` helper
  - Add `slugifyTypeAndCategory()` helper
  - Add `getDominantCategory()` helper
  - Add `extractPrimaryParameterValue()` helper
  - Add `formatParameterForName()` helper
  - Update `generatePortfolioSuggestion()` signature and implementation

- **`frontend/src/hooks/usePortfolioSaveDialog.ts`:**
  - Add `categories?: Category[] | null` to `UsePortfolioSaveDialogParams`
  - Pass `categories` to `generatePortfolioSuggestion()` calls (lines 80, 85)

- **`frontend/src/components/screens/PoliciesStageScreen.tsx`:**
  - Pass `categories` state to `usePortfolioSaveDialog({ ..., categories })` (around line 722)

- **`frontend/src/utils/__tests__/naming.test.ts`:** (NEW FILE if not exists)
  - All naming helper tests
  - Integration tests for `generatePortfolioSuggestion()`

- **`frontend/src/components/screens/__tests__/PoliciesStageScreen.policySets.test.tsx`:**
  - Add integration test for save dialog naming

### Testing Strategy

1. **Unit tests for helper functions:**
   - `extractTypeAndCategory`: template vs from-scratch, missing fields, null categories
   - `slugifyTypeAndCategory`: type + category combos
   - `getDominantCategory`: tie-breaking, empty categories, single policy
   - `extractPrimaryParameterValue`: parameter priority, missing schemas, zero values
   - `formatParameterForName`: percentage, currency, other units

2. **Unit tests for `generatePortfolioSuggestion()`:**
   - All naming patterns (single, multi-same-cat, multi-mixed-cat, empty)
   - Parameter enrichment (rate, threshold, percentage, skip-if-too-long)
   - From-scratch policy name reuse
   - Validation: all outputs pass `validatePortfolioName()`
   - Null categories: graceful degradation to old patterns

3. **Integration tests (usePortfolioSaveDialog):**
   - Save dialog opens with correct initial suggestion
   - Adding policies updates suggestion
   - Manual edit freezes suggestion
   - Dialog close/reopen resets freeze
   - Categories loading state (null vs []) handling

4. **Regression tests:**
   - Save/load/clone flows still work
   - Existing portfolio names load correctly
   - No changes to backend API contracts
   - Manual-edit freeze rule preserved

### Backward Compatibility

- **Existing portfolio names:** Load and display unchanged (names are user data)
- **Validation rules:** No changes to `validatePortfolioName()` regex (portfolioValidation.ts)
- **Slug format:** Still kebab-case, max 64 chars (no breaking changes)
- **Fallback behavior:** If categories unavailable, degrade gracefully to old patterns
- **API contracts:** No backend changes required

### Performance Considerations

- **Category lookup:** O(n) scan per policy where n = category count (typically < 10)
- **Parameter extraction:** O(m) scan per policy where m = parameter count (typically < 10)
- **Dominant category counting:** O(c) where c = composition length (typically < 20)
- **No memoization needed:** Suggestion only generated on dialog open and composition changes

### Project Structure Notes

- Follow existing utility pattern: helper functions in `frontend/src/utils/`, tests in `frontend/src/utils/__tests__/`
- No backend changes required (categories already fetched by Story 25.1)
- No changes to portfolio validation or persistence contracts
- `slugify()` and `truncateSlug()` helpers already exist in naming.ts

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-27.9]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX-DR10] - "Policy sets must be first-class reusable artifacts... with auto-suggested names derived from policy types and categories"
- [Source: frontend/src/utils/naming.ts] - Current `generatePortfolioSuggestion()` implementation
- [Source: frontend/src/hooks/usePortfolioSaveDialog.ts] - Dialog state and suggestion handling
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:27-43] - `CompositionEntry` interface
- [Source: frontend/src/api/types.ts:128-136] - `Category` interface
- [Source: frontend/src/components/simulation/portfolioValidation.ts] - `validatePortfolioName()` function
- [Source: _bmad-output/implementation-artifacts/27-3-show-actual-parameter-values-inline-in-policy-cards.md] - Parameter resolution order and formatting patterns
- [Source: _bmad-output/implementation-artifacts/27-5-auto-save-policy-set-composition-draft.md] - Manual-edit freeze pattern

## Dev Agent Record

### Agent Model Used

<!-- Populated after implementation is complete -->

### Debug Log References

<!-- Populated after implementation is complete -->

### Completion Notes List

<!-- Populated after implementation is complete -->

### File List

<!-- Populated after implementation is complete -->
