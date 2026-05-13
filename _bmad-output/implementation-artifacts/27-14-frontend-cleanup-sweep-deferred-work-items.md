# Story 27.14: Frontend cleanup sweep absorbing deferred-work items

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a frontend developer maintaining code quality,
I want to resolve the remaining frontend-local deferred work items from code reviews,
so that technical debt stops accumulating and the codebase follows consistent patterns.

## Background

The `deferred-work.md` file tracks items that were intentionally postponed during earlier stories. Several items are now ready to be absorbed into the active backlog:

1. **Error badge styling bypass** (from Story 25.6 review): `PolicyCard.tsx:271` uses `variant="default"` + `bg-red-500` instead of using the Badge component's built-in `destructive` variant.

2. **Editing badge styling bypass** (from Story 25.4 review): `PolicyCard.tsx:278` uses `variant="default"` + `bg-blue-500` instead of using a proper Badge variant.

3. **Active badge styling bypass** (from Story 20.x): `PoliciesStageScreen.tsx:1086` uses `variant="default"` + `bg-blue-100` instead of a semantic variant.

4. **AC-3 warning text structure** (from Story 25.6 review): The "Population data compatibility warning" at `PoliciesStageScreen.tsx:990-1002` splits text across a heading + multiple `<p>` elements. The heading improves scannability, but diverges from strict single-paragraph structure if that's ever required for testing or localization.

5. **Portfolio round-tripping fallback** (from Story 27.11 review): `usePortfolioDialog.ts:286` falls back to `policy.policy_type` as `templateId` when a template match fails. This can cause an unmatched loaded policy to save with the wrong type identifier.

**Items NOT in this story:**
- **CompositionEntry circular import**: Already resolved in Story 27.11 — the import is now from `@/api/types`
- **Auto-name effect dependencies**: Already resolved in Story 27.13 — the effect uses functional updater to avoid stale closure
- **Backend `pa.concat_tables()` regression tests**: Deferred to Epic 29 (backend work)

## Acceptance Criteria

1. **AC-1:** Given the PolicyCard error badge (line 271), when rendered, then it uses `variant="destructive"` without custom `bg-red-500 text-white` override classes.
   - Note: This changes appearance from dark red (`bg-red-500`) to light red (`bg-red-50`). This is intentional — the `destructive` variant is the canonical error badge style.

2. **AC-2:** Given the PolicyCard editing badge (line 278), when rendered, then it uses a semantic Badge variant (e.g., `info` for blue) without custom `bg-blue-500 text-white` override classes.
   - Note: This changes appearance from dark blue (`bg-blue-500`) to light blue (`bg-sky-50`). If dark blue is required, add a new variant to Badge instead of inline overrides.

3. **AC-3:** Given the PoliciesStageScreen active badge (line 1086), when rendered, then it uses a semantic Badge variant without custom `bg-blue-100 text-blue-700` override classes.
   - Note: `variant="secondary"` provides a similar appearance (`bg-slate-50 text-slate-600`). If the blue color is important, add an `active` variant to Badge.

4. **AC-4:** Given all Badge usages in the frontend, when inspected, then no Badge component uses `variant="default"` combined with `bg-*` color override classes (except legacy cases with documented rationale).

5. **AC-5:** Given the population compatibility warning at PoliciesStageScreen.tsx:990-1002, when inspected, then the multi-paragraph warning text structure is documented with a code comment explaining why it's intentional (scannability, accessibility).

6. **AC-6:** Given the portfolio load function in usePortfolioDialog.ts:284-286, when a template match fails and `policy.policy_type` is used as `templateId`, then a console warning logs the fallback so unmatched policies are traceable in dev tools, and code comments document the behavior.

7. **AC-7:** Given the deferred-work.md file, when this story is complete, then frontend-local items are marked as "Completed in Story 27.14" with rationale, and the backend `pa.concat_tables()` item remains as "Deferred to Epic 29".

## Tasks / Subtasks

- [ ] Task 1: Fix Badge variant bypasses in PolicyCard (AC: #1, #2, #4)
  - [ ] Subtask 1.1: Update PolicyCard.tsx:271 error badge from `variant="default" className="...bg-red-500 text-white"` to `variant="destructive"` (remove override classes)
  - [ ] Subtask 1.2: Update PolicyCard.tsx:278 editing badge from `variant="default" className="...bg-blue-500 text-white"` to `variant="info"` (remove override classes)
  - [ ] Subtask 1.3: Verify visual appearance in browser (expect lighter background colors)

- [ ] Task 2: Fix Badge variant bypass in PoliciesStageScreen (AC: #3, #4)
  - [ ] Subtask 2.1: Update PoliciesStageScreen.tsx:1086 active badge from `variant="default" className="...bg-blue-100 text-blue-700"` to `variant="secondary"` (remove override classes)
  - [ ] Subtask 2.2: If blue color is semantically important for "active" state, add a new `active` variant to badge.tsx with appropriate blue colors instead of using inline overrides

- [ ] Task 3: Audit remaining Badge bypasses (AC: #4)
  - [ ] Subtask 3.1: Run `grep -r 'variant="default"' frontend/src/components` to find all Badge usages with default variant
  - [ ] Subtask 3.2: For each result, check if it has inline `bg-*` color classes
  - [ ] Subtask 3.3: Fix or document each bypass — if the color is semantically important, add a proper variant to badge.tsx; otherwise, use an existing variant

- [ ] Task 4: Document warning text structure (AC: #5)
  - [ ] Subtask 4.1: Add code comment at PoliciesStageScreen.tsx:990 explaining why the multi-paragraph structure is intentional:
    ```tsx
    {/* Multi-paragraph structure intentional: heading improves scannability,
     * separate <p> elements group related information for accessibility.
     * Collapsed to single <p> would reduce readability. */}
    ```
  - [ ] Subtask 4.2: Consider adding `<h3>` for the heading if better heading hierarchy is needed (optional)

- [ ] Task 5: Document portfolio template-matching fallback (AC: #6)
  - [ ] Subtask 5.1: Add code comment at usePortfolioDialog.ts:284-286 explaining the fallback behavior and its implications:
    ```tsx
    // Fallback: when saved portfolio references a policy type that doesn't
    // match any current template, use policy_type as templateId. This allows
    // the portfolio to load but may cause issues if the policy is edited and
    // saved (will save with wrong templateId). Unmatched policies should be rare.
    ```
  - [ ] Subtask 5.2: Add console.warning when fallback is triggered:
    ```tsx
    if (!template) {
      console.warn(`Template not found for policy type "${policy.policy_type}", using fallback`);
    }
    ```

- [ ] Task 6: Update deferred-work.md (AC: #7)
  - [ ] Subtask 6.1: Create a "## Completed" section at the top of deferred-work.md
  - [ ] Subtask 6.2: Move these items to "Completed" with closing story reference:
    - "Circular-import risk: CompositionEntry" → Completed in Story 27.11
    - "Error badge styling" → Completed in Story 27.14
    - "AC-3 warning text split" → Reviewed and accepted in Story 27.14
    - "Auto-name effect dep array" → Completed in Story 27.13
    - "Portfolio round-tripping fallback" → Documented in Story 27.14
  - [ ] Subtask 6.3: Keep "pa.concat_tables() schema-mismatch tests" under "## Deferred to Epic 29"

- [ ] Task 7: Quality gates
  - [ ] Subtask 7.1: Run `npm test` — all tests pass
  - [ ] Subtask 7.2: Run `npm run typecheck` — no TypeScript errors
  - [ ] Subtask 7.3: Run `npm run lint` — no new lint errors
  - [ ] Subtask 7.4: Manual verification: open browser and check badge appearances in Policies stage

## Dev Notes

### Badge Variant System Reference

The Badge component at `frontend/src/components/ui/badge.tsx` defines these variants:

```tsx
const badgeVariants = cva(
  "inline-flex items-center border px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
  {
    variants: {
      variant: {
        default: "border-slate-200 bg-slate-100 text-slate-700",
        outline: "border-slate-300 bg-white text-slate-700",
        secondary: "border-slate-200 bg-slate-50 text-slate-600",
        success: "border-emerald-200 bg-emerald-50 text-emerald-700",
        warning: "border-amber-200 bg-amber-50 text-amber-700",
        destructive: "border-red-200 bg-red-50 text-red-700", // ⚠️ Use this for error badges
        info: "border-sky-200 bg-sky-50 text-sky-700",        // ⚠️ Use this for info/editing badges
        violet: "border-violet-200 bg-violet-50 text-violet-700",
      },
    },
  },
);
```

**Key insight:** All semantic variants use light backgrounds (`bg-*-50`) with darker borders and text. The current bypasses use dark backgrounds (`bg-red-500`, `bg-blue-500`) which are NOT part of the Badge design system.

**Migration path:**
- Error badge: `variant="default" + bg-red-500` → `variant="destructive"`
- Editing badge: `variant="default" + bg-blue-500` → `variant="info"` or `variant="violet"`
- Active badge: `variant="default" + bg-blue-100` → `variant="secondary"` or new `variant="active"`

If the dark background colors are semantically important (e.g., editing state needs to be very prominent), add a new variant to badge.tsx instead of using inline overrides.

### Warning Text Structure Decision

The population compatibility warning at `PoliciesStageScreen.tsx:990-1002`:

```tsx
<div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3 flex items-start gap-2">
  <Info className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
  <div className="text-xs text-amber-700">
    <p className="font-semibold mb-1">Population data compatibility warning</p>
    <p>Some policies require population columns that may not be available...</p>
    <p className="mt-1">Validate data compatibility in Stage 2 (Population) before running.</p>
  </div>
</div>
```

**Decision:** Keep the multi-paragraph structure. The heading (`font-semibold`) improves scannability, and separating the problem statement from the action item improves readability. This is acceptable for accessibility and user experience.

**Documentation:** Add a code comment explaining this decision so future reviewers understand it was intentional, not an oversight.

### Portfolio Template-Matching Fallback

From `usePortfolioDialog.ts:284-286`:

```tsx
const template = loadParams.templates.find(
  (tmpl) => normalizePolicyType(tmpl.type) === policy.policy_type,
);
const templateId = template?.id ?? policy.policy_type; // Fallback when no match
```

**Issue:** When a saved portfolio references a policy type that doesn't exist in the current template catalog, `templateId` becomes `policy.policy_type` (a string like `"carbon_tax"`). This is not a valid template ID, so:
- The policy can't display template-derived information
- If edited and saved, it saves with the wrong `templateId`
- This creates a persistent mismatch

**Acceptable for now because:**
- Template mismatches should be rare (only when templates are removed from catalog)
- The fallback allows the portfolio to load without crashing
- Users can manually fix by removing the unmatched policy

**Mitigation in this story:**
- Add a console warning when fallback occurs (dev-only, no user toast)
- Document the behavior with code comments
- Consider adding UI validation in a future story to warn users about unmatched policies

### Files to Modify

1. `frontend/src/components/simulation/PolicyCard.tsx` — Badge variant fixes (lines 271, 278)
2. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Active badge fix (line 1086), warning text documentation (line 990)
3. `frontend/src/hooks/usePortfolioDialog.ts` — Fallback behavior documentation + warning (line 284)
4. `frontend/src/components/ui/badge.tsx` — Optionally add new `active` variant if needed
5. `_bmad-output/implementation-artifacts/deferred-work.md` — Update item status

### Files to Read

- `frontend/src/components/ui/badge.tsx` — Badge variant definitions
- `frontend/src/utils/policyTypes.ts` — `normalizePolicyType` function
- `frontend/src/api/types.ts` — `CompositionEntry` interface (moved here in Story 27.11)
- `_bmad-output/implementation-artifacts/deferred-work.md` — Full list of deferred items

### Dependencies

- **Story 27.11** (Consolidate portfolio dialog hooks and unify policy types) — Must be complete because this story references the consolidated `usePortfolioDialog` hook and the `CompositionEntry` type location.
- **Story 27.13** (AppContext naming-state hardening) — Must be complete because the auto-name effect dependency item is marked done by reference to that story.

### Testing Strategy

**Unit tests:**
- No new unit tests needed — this is a cleanup story with behavior-preserving changes

**Visual regression:**
- Manual verification of badge appearances in browser
- Check that error badges are still visually distinct as error indicators
- Check that editing badges are still identifiable

**Integration tests:**
- Existing portfolio load/save tests should continue to pass
- The fallback behavior is unchanged (only documented with console warning)
- Badge appearance changes don't affect functionality

### Project Structure Notes

- Changes are localized to existing frontend components and hooks
- No new files or directories
- No breaking changes to public APIs
- Visual changes are intentional (aligning with Badge design system)

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md]
- [Source: frontend/src/components/ui/badge.tsx] (Badge variants)
- [Source: frontend/src/components/simulation/PolicyCard.tsx:268-281] (Badge bypasses)
- [Source: frontend/src/components/screens/PoliciesStageScreen.tsx:990-1002] (Warning text)
- [Source: frontend/src/components/screens/PoliciesStageScreen.tsx:1079-1089] (Active badge)
- [Source: frontend/src/hooks/usePortfolioDialog.ts:274-316] (Portfolio loading)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

None — story creation completed without issues.

### Completion Notes List

- Story 27.14 specification complete with enhanced context analysis
- All 7 acceptance criteria defined with implementation specifics
- 7 task groups with 23 subtasks
- Scope limited to frontend-local deferred items
- CompositionEntry circular import correctly marked as done (Story 27.11)
- Auto-name effect dependencies correctly marked as done (Story 27.13)
- Backend pa.concat_tables() issue correctly deferred to Epic 29
- Badge variant changes documented (light backgrounds vs dark backgrounds)
- Warning text structure decision documented (keep multi-paragraph)

### File List

Created:
- `_bmad-output/implementation-artifacts/27-14-frontend-cleanup-sweep-deferred-work-items.md` (this file)

To be modified during implementation:
- `frontend/src/components/simulation/PolicyCard.tsx` (Badge variants)
- `frontend/src/components/screens/PoliciesStageScreen.tsx` (Badge variant, warning docs)
- `frontend/src/hooks/usePortfolioDialog.ts` (Fallback docs + warning)
- `frontend/src/components/ui/badge.tsx` (Optional: add `active` variant)
- `_bmad-output/implementation-artifacts/deferred-work.md` (Update status)
