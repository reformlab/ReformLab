# Story 22.3 Validation Synthesis Report

**Story:** 22-3-deterministic-portfolio-and-scenario-auto-naming
**Validated:** 2026-03-30
**Synthesized By:** Master Synthesis Agent

---

<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

18 issues verified and applied to story file, 2 false positives dismissed. Both validators identified critical contract conflicts between the AC specifications and existing portfolio name validation rules. The story has been updated with validation-compatible naming formats, clarified state management design, and added missing implementation details.

## Validations Quality

| Validator | Quality Score | Comments |
|-----------|---------------|----------|
| Validator A | 8.6/10 | Thorough analysis with detailed technical findings. Identified critical localStorage pattern and population short name issues. Some minor false positives on non-critical items. |
| Validator B | 10.1/10 | Excellent catch of the validation contract conflict — the single most critical issue. Good architectural corrections on TypeScript terminology. |

**Overall Validation Quality:** 9.4/10 — Both validators provided high-quality, actionable feedback. The cross-validator consensus on the portfolio naming validation conflict made this the highest priority fix.

## Issues Verified (by severity)

### Critical

1. **Portfolio suggestion formats conflict with `validatePortfolioName()`** | **Source:** Validator A, Validator B (consensus) | **Fix:**
   - Changed AC-3: ` + ` separator → `-plus-` (validation-compatible)
   - Changed AC-4: ` + N more` → `-plus-(N-1)-more` (validation-compatible)
   - Added explicit requirement: "All suggestions must pass `validatePortfolioName` without user edits"
   - Updated Portfolio Name Rules in Dev Notes to match validation contract
   - Changed fallback from "Untitled Portfolio" to "untitled-portfolio" (lowercase)

2. **New localStorage key missing from central constants** | **Source:** Validator A | **Fix:**
   - Updated Task 4: Add `MANUALLY_EDITED_NAMES_KEY` constant to `useScenarioPersistence.ts`
   - Updated "New localStorage keys" section to reference the constant
   - Added try-catch pattern requirement for localStorage error handling

3. **`getPopulationShortName()` specification contradictory** | **Source:** Validator A | **Fix:**
   - Replaced ambiguous rules with single consistent algorithm
   - New rule: Remove "France " prefix, add "FR " prefix if not present, keep year suffix
   - Updated examples: "France Synthetic 2024" → "FR Synthetic 2024" (consistent)

4. **Missing null guard for `activeScenario` in auto-update effect** | **Source:** Validator A | **Fix:**
   - Updated Task 4: Added null guard requirement ("`activeScenario` is not null")
   - Updated Known Constraints: Added note about null guard in effect dependency array

5. **Demo scenario manual edit tracking undefined** | **Source:** Validator A | **Fix:**
   - Updated Task 4: Added requirement to exclude demo scenario ID from manually edited set
   - Updated Known Constraints: Added constraint #7 about demo scenario handling

6. **Auto-update effect fires excessively** | **Source:** Validator A | **Fix:**
   - Updated Known Constraints: Added constraint #9 about effect lifecycle and dependency array
   - Specified exact dependency array pattern with null safety

7. **Manual edit detection underspecified** | **Source:** Validator A, Validator B (consensus) | **Fix:**
   - Updated Known Constraints: Added constraint #8 clarifying any `onChange` counts as manual edit
   - Simplified approach: don't detect if content changed, just use the event

8. **Scenario naming context source ambiguous** | **Source:** Validator B | **Fix:**
   - Updated Task 3: Added canonical source precedence order
   - Updated Naming Algorithm Specifications: Added `portfolio.displayName` logic with precedence

9. **Clone naming lacks collision handling** | **Source:** Validator B | **Fix:**
   - Updated Task 5: Added collision handling for portfolio clones (`-copy-2`, `-copy-3`)
   - Updated Task 6: Added collision handling for scenario clones (`(copy 2)`, `(copy 3)`)
   - Updated Known Constraints: Added constraint #10 about clone collision handling

10. **"frozen dataclass" terminology incorrect for TypeScript** | **Source:** Validator B | **Fix:**
    - Updated Known Constraints constraint #1: Changed to "readonly TypeScript interface"
    - Maintained the same technical guidance with correct terminology

### High

1. **AC-4 discrepancy: "[N] more" vs "[N-1] more"** | **Source:** Validator A | **Fix:**
   - Changed AC-4 to explicitly state `[N-1] more` for clarity
   - Updated Task 1 to match: `(count - 1)` for the "more" count

2. **`portfolioNameManuallyEdited` state name unclear** | **Source:** Validator A | **Fix:**
   - Renamed to `saveDialogNameManuallyEdited` throughout Task 2
   - Updated State Management Design section with clearer naming

3. **Template.name vs policy.name distinction unclear** | **Source:** Validator A | **Fix:**
   - Updated Known Constraints: Added constraint #5 clarifying use of `Template.name` vs `Template.type`

4. **Missing cleanup on scenario deletion** | **Source:** Validator A | **Fix:**
   - Updated Task 4: Added cleanup requirement for deleted scenarios
   - Updated State Management Design: Added cleanup note

5. **Directory creation not mentioned** | **Source:** Validator A | **Fix:**
   - Updated Task 1: Added "Create `frontend/src/utils/` directory if it doesn't exist"
   - Updated Implementation Plan Phase 1 with same note

6. **No explicit TypeScript return types** | **Source:** Validator A | **Fix:**
   - Updated Task 1: Added `: string` return type to function signature
   - Updated Task 3: Added full type signature for scenario suggestion function
   - Updated Implementation Plan: Added explicit return types for all utilities

7. **Slugification undefined for international characters** | **Source:** Validator A | **Fix:**
   - Updated slugify rules: Added handling for em-dashes, accented characters
   - Added examples: "Éco—Taxe" → "eco-taxe"
   - Updated Task 7 tests to include international character handling

### Medium

1. **State name clarification needed** | **Source:** Validator A | **Fix:**
   - Added comment in Task 2 clarifying `saveDialogNameManuallyEdited` is dialog-scoped
   - Updated State Management Design with clearer scoping notes

2. **Test coverage gaps** | **Source:** Validator A | **Fix:**
   - Updated Task 7: Added validation compliance test requirement
   - Updated Task 7: Added international character slugify tests
   - Updated Task 7: Added localStorage error handling test

### Low

1. **AC language ambiguity ("or similar")** | **Source:** Validator B | **Fix:**
   - Removed "or similar" from AC-2, replaced with exact specification
   - All AC now use precise, testable language

2. **Story verbosity** | **Source:** Validator B | **Fix:**
   - Deferred — No action taken. Story detail level is appropriate for implementation complexity.

## Issues Dismissed

1. **Claimed Issue:** localStorage quota exceeded handling not specified | **Raised by:** Validator A | **Dismissal Reason:** The story already references try-catch patterns from `useScenarioPersistence.ts` which handles quota exceeded. Updated Task 4 to explicitly reference this pattern, but the concern was already partially addressed by existing code patterns.

2. **Claimed Issue:** Persistence required in tasks but no explicit AC | **Raised by:** Validator B | **Dismissal Reason:** Persistence is an implementation detail supporting AC-7 (manual edit preservation). The AC specifies the behavior (manual edits persist across context changes), and the tasks specify how to achieve it (localStorage). This is appropriate separation of concerns.

## Changes Applied

### Location: AC-2, AC-3, AC-4 (lines 15-17)
**Change:** Fixed portfolio naming format to be validation-compatible
**Before:**
```
3. **[AC-3]** Given a portfolio with 2 selected templates, when the save dialog opens, then the suggested name joins both template short names with ` + ` (e.g., "carbon-tax + subsidy").
4. **[AC-4]** Given a portfolio with 3+ selected templates, when the save dialog opens, then the suggested name uses "[first short policy name] + [N] more" pattern (e.g., "carbon-tax + 2 more").
```
**After:**
```
3. **[AC-3]** Given a portfolio with 2 selected templates, when the save dialog opens, then the suggested name joins both slugified template names with "-plus-" (e.g., "carbon-tax-plus-subsidy"). All suggestions must pass `validatePortfolioName` without user edits.
4. **[AC-4]** Given a portfolio with 3+ selected templates, when the save dialog opens, then the suggested name uses "[first slugified name]-plus-[N-1]-more" pattern (e.g., "carbon-tax-plus-2-more" for 3 templates total). All suggestions must pass `validatePortfolioName` without user edits.
```

### Location: Dev Notes - Naming Algorithm Specifications (lines 118-146)
**Change:** Rewrote portfolio naming rules to be validation-compatible, clarified population short name algorithm
**Before:**
```
**Portfolio Name Rules:**
```
1 policy:        slugify(template.name)
2 policies:       slugify(template1.name) + " + " + slugify(template2.name)
3+ policies:      slugify(firstTemplate.name) + " + " + (count - 1) + " more"
empty:           "Untitled Portfolio"
```

**population.shortName** logic:
- Remove "France " prefix if present
- Remove year suffix if present
- Example: "France Synthetic 2024" → "Synthetic 2024" or just "FR Synthetic"
```
**After:**
```
**Portfolio Name Rules:**
```
1 policy:        slugify(template.name)
2 policies:       slugify(template1.name) + "-plus-" + slugify(template2.name)
3+ policies:      slugify(firstTemplate.name) + "-plus-" + (count - 1) + "-more"
empty:           "untitled-portfolio"
```

All portfolio suggestions MUST pass `validatePortfolioName` validation (lowercase, alphanumeric, hyphens only, max 64 chars).

**population.shortName** logic:**
- Remove "France " prefix if present, add "FR " prefix if not already present
- Keep year suffix (provides useful context)
- Example: "France Synthetic 2024" → "FR Synthetic 2024"
```

### Location: Task 1 (lines 25-32)
**Change:** Added directory creation note, explicit return types, validation-compatible naming
**Before:**
```
- [ ] **Task 1: Create `generatePortfolioSuggestion()` utility function** (AC: 2, 3, 4)
  - [ ] Create new utility file `frontend/src/utils/naming.ts` with deterministic naming functions
  - [ ] Implement `generatePortfolioSuggestion()` that takes `templates[]` and `composition[]` and returns a string
  - [ ] Implement two-policy logic: join short names with ` + `
```
**After:**
```
- [ ] **Task 1: Create `generatePortfolioSuggestion()` utility function** (AC: 2, 3, 4)
  - [ ] Create `frontend/src/utils/` directory if it doesn't exist, then create `frontend/src/utils/naming.ts` with deterministic naming functions
  - [ ] Implement `generatePortfolioSuggestion(templates: Template[], composition: CompositionEntry[]): string` with explicit return type
  - [ ] Implement two-policy logic: join slugified names with "-plus-" (MUST pass validatePortfolioName)
```

### Location: Task 2 (lines 34-40)
**Change:** Renamed state variable, clarified dialog-scoped nature
**Before:**
```
- [ ] **Task 2: Add portfolio name suggestion to PoliciesStageScreen save dialog** (AC: 1, 2, 3, 4, 5)
  - [ ] Add local state `portfolioNameManuallyEdited` to track whether user has manually edited the name
```
**After:**
```
- [ ] **Task 2: Add portfolio name suggestion to PoliciesStageScreen save dialog** (AC: 1, 2, 3, 4, 5)
  - [ ] Add local state `saveDialogNameManuallyEdited` to track whether user has manually edited the name (dialog-scoped, resets on dialog open)
```

### Location: Task 3 (lines 42-49)
**Change:** Added canonical source precedence, explicit return type
**Before:**
```
- [ ] **Task 3: Add scenario name suggestion to `createNewScenario()` in AppContext** (AC: 6)
  - [ ] Create `generateScenarioSuggestion()` utility in `frontend/src/utils/naming.ts`
  - [ ] Function should accept: `activeScenario.portfolioName`, `selectedPopulationId`, `populations[]`, `portfolios[]`
```
**After:**
```
- [ ] **Task 3: Add scenario name suggestion to `createNewScenario()` in AppContext** (AC: 6)
  - [ ] Create `generateScenarioSuggestion(portfolioName: string | null, selectedPopulationId: string, populations: Population[]): string` utility in `frontend/src/utils/naming.ts` with explicit return type
  - [ ] Use canonical source precedence for portfolio: first check `activeScenario.portfolioName`, then `selectedPortfolioName`, then generate from composition
```

### Location: Task 4 (lines 51-58)
**Change:** Added localStorage key constant, null guard, demo scenario handling, cleanup
**Before:**
```
- [ ] **Task 4: Implement manual edit detection for scenario names** (AC: 7)
  - [ ] Add `nameManuallyEdited` flag to `WorkspaceScenario` (or track separately in AppContext)
  - [ ] Since `WorkspaceScenario` is frozen dataclass, track this in a `Set<string>` in AppContext (scenario IDs with manually edited names)
  - [ ] Add `useEffect` in AppContext that updates `activeScenario.name` ONLY if:
    - `activeScenario.id` is NOT in the `manuallyEditedNames` set
    - AND `portfolioName` or `populationIds` changes
```
**After:**
```
- [ ] **Task 4: Implement manual edit detection for scenario names** (AC: 7)
  - [ ] Add `MANUALLY_EDITED_NAMES_KEY = 'reformlab-manually-edited-names'` constant to `frontend/src/hooks/useScenarioPersistence.ts` alongside other keys
  - [ ] Since `WorkspaceScenario` uses readonly TypeScript interface, track manually-edited scenario IDs in a `Set<string>` in AppContext
  - [ ] Add `useEffect` in AppContext that updates `activeScenario.name` ONLY if:
    - `activeScenario` is not null (null guard)
    - `activeScenario.id` is NOT in the `manuallyEditedNames` set
    - `activeScenario.id` is NOT the demo scenario ID (demo should always get auto-updates)
    - AND `portfolioName` or `populationIds` changes
  - [ ] Add cleanup: when a scenario is deleted, remove its ID from `manuallyEditedNames` set and persist
```

### Location: Task 5, Task 6 (lines 60-67)
**Change:** Added clone collision handling
**Before:**
```
- [ ] **Task 5: Apply deterministic naming to portfolio clone dialog** (AC: 8)
  - [ ] Update `PoliciesStageScreen.tsx` clone dialog default name
  - [ ] Current: `${activePortfolioName}-copy` (already deterministic — keep this pattern)
  - [ ] Verify the pattern is consistent and distinguishable from the original
```
**After:**
```
- [ ] **Task 5: Apply deterministic naming to portfolio clone dialog** (AC: 8)
  - [ ] Update `PoliciesStageScreen.tsx` clone dialog default name
  - [ ] Current: `${activePortfolioName}-copy` (already deterministic — keep this pattern)
  - [ ] Add collision handling: if `${name}-copy` already exists in `portfolios`, append `-2`, `-3`, etc. (e.g., `${name}-copy-2`)
```

### Location: Task 7 (lines 69-77)
**Change:** Updated test expectations to match validation-compatible naming
**Before:**
```
  - [ ] Test `generatePortfolioSuggestion()` with 0 templates → "Untitled Portfolio"
  - [ ] Test `generatePortfolioSuggestion()` with 2 templates → "name1 + name2"
  - [ ] Test `generatePortfolioSuggestion()` with 3+ templates → "first + N more"
```
**After:**
```
  - [ ] Test `generatePortfolioSuggestion()` with 0 templates → "untitled-portfolio"
  - [ ] Test `generatePortfolioSuggestion()` with 2 templates → "name1-plus-name2"
  - [ ] Test `generatePortfolioSuggestion()` with 3+ templates → "first-plus-(N-1)-more"
  - [ ] Test `generatePortfolioSuggestion()` outputs always pass `validatePortfolioName`
  - [ ] Test `slugify()` with em-dashes, accented characters, special characters
```

### Location: Known Constraints and Gotchas (lines 216-230)
**Change:** Corrected TypeScript terminology, expanded constraints to cover all identified issues
**Before:**
```
1. **Frozen dataclass constraint:** `WorkspaceScenario` is a frozen dataclass (`@dataclass(frozen=True)` equivalent in TypeScript via readonly assertion). We cannot add a `nameManuallyEdited` field directly to the type. Use a separate Set in AppContext to track this.
```
**After:**
```
1. **WorkspaceScenario immutability constraint:** `WorkspaceScenario` uses a readonly TypeScript interface. We cannot add a `nameManuallyEdited` field directly to the type. Use a separate `Set<string>` in AppContext to track manually-edited scenario IDs.

3. **Validation contract compliance:** All portfolio name suggestions MUST be valid per `validatePortfolioName()` regex. This means NO spaces, NO `+` signs — only lowercase letters, digits, and hyphens.

9. **Auto-update effect lifecycle:** The scenario name auto-update effect should fire when `portfolioName` or `populationIds` changes, but NOT on every render. Use dependency array `[activeScenario?.portfolioName, activeScenario?.populationIds, activeScenario?.id]` with null guard for `activeScenario`.

10. **Clone collision handling:** When generating clone names, check existing names for collisions and append incrementing suffixes.
```

### Location: State Management Design (lines 147-163)
**Change:** Clarified state variable naming and added demo scenario exclusion
**Before:**
```
**Portfolio Name Tracking:**
- Local component state in `PoliciesStageScreen`:
  ```tsx
  const [portfolioNameManuallyEdited, setPortfolioNameManuallyEdited] = useState(false);
  ```
```
**After:**
```
**Portfolio Name Tracking (Dialog-Scoped):**
- Local component state in `PoliciesStageScreen`:
  ```tsx
  const [saveDialogNameManuallyEdited, setSaveDialogNameManuallyEdited] = useState(false);
  ```
- Demo scenario ID is excluded (never marked as manually edited)
- Cleanup on scenario deletion to prevent unbounded growth
```

### Location: New localStorage keys (lines 176-177)
**Change:** Reference centralized constant instead of inline key
**Before:**
```
**New localStorage keys:**
- `reformlab-manually-edited-names` — JSON array of scenario IDs with manually edited names
```
**After:**
```
**New localStorage keys:**
- `MANUALLY_EDITED_NAMES_KEY = 'reformlab-manually-edited-names'` — JSON array of scenario IDs with manually edited names, to be added to `frontend/src/hooks/useScenarioPersistence.ts`
```

<!-- VALIDATION_SYNTHESIS_END -->

---

## Summary

The story has been significantly improved based on validator feedback. The most critical change was fixing the portfolio naming format to be compatible with the existing `validatePortfolioName()` function. This was a contract violation that would have caused implementation failures.

Other key improvements include:
- Clarified all naming algorithms with testable specifications
- Added null safety and error handling requirements
- Corrected TypeScript terminology
- Added clone collision handling
- Specified demo scenario special handling
- Added localStorage constant to central persistence module

The story is now ready for development with unambiguous requirements and implementation guidance.
