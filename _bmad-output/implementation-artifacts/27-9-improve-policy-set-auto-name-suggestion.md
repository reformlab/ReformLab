# Story 27.9: Improve policy-set auto-name suggestion

Status: ready-for-dev

## Story

As an analyst saving a policy set,
I want the suggested name to be informative beyond the first policy when I have three or more policies,
so that the auto-name actually helps me identify the policy set instead of degrading to "first-policy-plus-N-more".

## Acceptance Criteria

1. Given a portfolio with 3 policies (e.g., 2 Tax on Carbon Emissions, 1 Subsidy on Energy Consumption), when the suggestion runs, then the name reflects the dominant categories (e.g., `carbon-tax-energy-subsidy`) rather than `carbon-tax-plus-2-more`.
2. Given a portfolio with 4+ policies of mixed types and categories, when the suggestion runs, then the name is at most three category labels long, ordered by policy type (Tax → Subsidy → Transfer) and joined with `-`, falling back to type counts only if categories overlap (e.g., `2-tax-1-subsidy-1-transfer`).
3. Given a portfolio with a single policy, when the suggestion runs, then the name uses the template's slugified name (existing behaviour).
4. Given a portfolio with two policies, when the suggestion runs, then the name uses both category slugs joined with `-` (e.g., `carbon-tax-energy-subsidy`), removing the `-plus-` connector.
5. Given the analyst manually edits the name, when policies change later, then the manual name is preserved (Story 25.5 freeze rule still holds; tested via 27.13 hardening if needed).
6. Given the existing test suite at `frontend/src/utils/__tests__/naming.test.ts`, when this story is complete, then the new algorithm has full unit coverage including: 1-policy, 2-policy, 3-policy with same category, 3-policy with mixed categories, 4+-policy fallback to type counts.

## Tasks / Subtasks

- [ ] Replace algorithm in naming utility (AC: #1, #2, #3, #4)
  - [ ] At `frontend/src/utils/naming.ts:84-125`, replace the `slug-plus-N-more` fallback with the new algorithm:
    - 0 policies → `"untitled-policy-set"`
    - 1 policy → existing slug
    - 2 policies → `slug1-slug2` (no `-plus-`)
    - 3+ policies with ≤3 distinct categories → join those category slugs sorted by type
    - 3+ policies with >3 distinct categories → fall back to `{n}-tax-{m}-subsidy-{k}-transfer` (omit zero counts)
  - [ ] Sort policies by type (Tax → Subsidy → Transfer → Other) before slugifying
- [ ] Preserve manual-edit freeze (AC: #5)
  - [ ] Verify the existing freeze rule in `useScenarioPersistence` (or equivalent) still applies; do not modify it here
- [ ] Tests (AC: #6)
  - [ ] Unit tests for each branch: 0/1/2/3-distinct/3-mixed/4+/fallback
  - [ ] Manual-edit-freeze test (regression for Story 25.5)
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The existing naming utility is pure. Keep it pure. No I/O, no React, no localStorage.
- Slug helper exists in the same file or `frontend/src/utils/slug.ts`; reuse it.
- The "freeze after manual edit" rule lives elsewhere (probably AppContext); this story changes the suggestion only, not the freeze.

### Project Structure Notes

- Files touched: `frontend/src/utils/naming.ts`, `frontend/src/utils/__tests__/naming.test.ts`
- No new files

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.9]
- [Source: frontend/src/utils/naming.ts:84-125]
- [Source: Story 25.5 acceptance criteria for manual-edit freeze]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
