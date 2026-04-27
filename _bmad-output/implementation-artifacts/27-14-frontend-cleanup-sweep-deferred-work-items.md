# Story 27.14: Frontend cleanup sweep absorbing `deferred-work.md` items

Status: ready-for-dev

## Story

As a frontend developer maintaining a healthy codebase,
I want to absorb the three frontend-local cleanup items currently parked in `deferred-work.md` (circular-import risk, error-badge variant, prose-collapse),
so that the deferred-work file no longer accumulates stale items and these small fixes don't drift further while AppContext-owned cleanup stays with story 27.13.

## Acceptance Criteria

1. Given the circular-import risk noted in `deferred-work.md:3` (`portfolioValidation.ts:11` imports `CompositionEntry` from `PortfolioCompositionPanel`), when this story is complete, then `CompositionEntry` lives in `frontend/src/api/types.ts` and `portfolioValidation.ts` imports from there. (NOTE: if Story 27.11 has already moved this type, mark this AC done by reference.)
2. Given the error-badge styling at `PortfolioCompositionPanel.tsx:786` using `variant="default"` + `bg-red-500`, when this story is complete, then the Badge component has a `destructive` variant (or equivalent error-color token) and the call site uses it without inline `bg-red-500`.
3. Given the AC-3 warning text split across heading + two `<p>` elements at `PoliciesStageScreen.tsx:760-776`, when this story is complete, then either (a) the prose remains as-is with a code comment justifying the structure, or (b) it is collapsed to a single `<p>` matching strict-grading expectations — pick whichever the team prefers; document the choice.
4. Given `_bmad-output/implementation-artifacts/deferred-work.md`, when this story is complete, then the three frontend-local items are marked `migrated to story 27.11/27.14` with the closing PR reference, while the AppContext dep-array item remains owned by story 27.13.

## Tasks / Subtasks

- [ ] Move `CompositionEntry` type (AC: #1)
  - [ ] If Story 27.11 has already done this, note as "completed by 27.11" in the PR description
  - [ ] Otherwise, move the type from `PortfolioCompositionPanel.tsx` to `frontend/src/api/types.ts`
  - [ ] Update `portfolioValidation.ts:11` import
- [ ] Add `destructive` Badge variant (AC: #2)
  - [ ] Update `frontend/src/components/ui/badge.tsx` to define a `destructive` variant using a theme token
  - [ ] Replace `variant="default"` + `bg-red-500` in `PortfolioCompositionPanel.tsx:786` with `variant="destructive"`
  - [ ] Search the codebase for any other inline `bg-red-500` on Badges; switch to the variant
- [ ] AC-3 prose decision (AC: #3)
  - [ ] Confirm with whoever owns Stage 1 grading whether strict-match is required
  - [ ] If yes: collapse to a single `<p>` at `PoliciesStageScreen.tsx:760-776`
  - [ ] If no: add a code comment explaining the heading + paragraphs structure and leave it
- [ ] Update `deferred-work.md` (AC: #4)
  - [ ] Edit the file to mark each frontend-local item with its closing story reference
  - [ ] Leave the AppContext dep-array item owned by story 27.13
  - [ ] Reorder so closed items appear in a "## Closed (migrated to EPIC-27)" section
  - [ ] Open items (the 2026-04-19 panel.py concat-tables tests, the policy-type fallback) move under "## Still open"
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- This story is intentionally a small cleanup sweep. It exists so the deferred-work file gets routinely closed out instead of growing forever.
- The three frontend-local items here have small blast radius. Each task should be commit-sized and reviewable.
- The AppContext dep-array cleanup is intentionally excluded; story 27.13 owns it end-to-end.
- The 2026-04-19 deferred item about `pa.concat_tables()` schema-mismatch tests is BACKEND, not frontend, and is owned by Story 29.5 — do not touch it here.

### Project Structure Notes

- Files touched: `frontend/src/api/types.ts`, `frontend/src/components/simulation/PortfolioCompositionPanel.tsx`, `frontend/src/components/simulation/portfolioValidation.ts`, `frontend/src/components/ui/badge.tsx`, possibly `frontend/src/components/screens/PoliciesStageScreen.tsx`, `_bmad-output/implementation-artifacts/deferred-work.md`
- No new files

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.14]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] (full file)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
