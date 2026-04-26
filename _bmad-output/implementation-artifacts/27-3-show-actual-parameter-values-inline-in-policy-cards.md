# Story 27.3: Show actual parameter values inline in policy cards

Status: ready-for-dev

## Story

As an analyst scanning a policy composition,
I want each policy card to surface its actual parameter values (rates, thresholds, schedules) without me having to expand it,
so that I can recognise and compare policies at a glance instead of reading uppercase parameter-group names that carry no information.

## Acceptance Criteria

1. Given a collapsed policy card with a populated rate schedule, when displayed, then the card shows headline parameter values per group (e.g., `Rate schedule → €45/tCO₂ in 2025`) instead of the generic chip `6 PARAMS` and the bare uppercase group names like `RATE_SCHEDULE`, `EXEMPTIONS`, etc.
2. Given a parameter group with no customised values, when displayed, then the default value is shown (no fake placeholder values like `rate: 0` or `unit: EUR` unless those are real defaults).
3. Given the analyst clicks a group chip on a collapsed card, when actioned, then the card expands and scrolls to that group with the relevant parameters visually highlighted.
4. Given the existing hardcoded placeholder block at `frontend/src/components/simulation/PortfolioCompositionPanel.tsx:471-513`, when this story is complete, then no hardcoded placeholder parameter values remain — all displayed values are derived from `entry.parameters` (or the equivalent live source).
5. Given a from-scratch policy whose parameter groups are empty by design, when displayed, then the card communicates "Parameters not yet set" per group rather than fake values.
6. Given the click-to-preview affordance, when group chip clicks are tested, then the card's expand state, scroll target, and highlight state are asserted in unit tests.

## Tasks / Subtasks

- [ ] Replace hardcoded placeholders (AC: #1, #2, #4)
  - [ ] At `PortfolioCompositionPanel.tsx:471-513`, remove the static `rate: 0`, `unit: EUR`, `threshold: 0`, `ceiling: null` hardcoded values
  - [ ] Derive headline values from `entry.parameters` keyed by parameter-group membership; if `entry.editableParameterGroups` exists, use it as the authoritative grouping source
  - [ ] If a parameter has no value and no default, display "—" rather than a fabricated zero
- [ ] Headline-value formatter (AC: #1)
  - [ ] Add a helper `summariseParameterGroup(group, parameters): string` that returns a one-line summary per group (e.g., `Rate schedule → €45/tCO₂ in 2025; €60/tCO₂ in 2030`)
  - [ ] For a rate schedule, prefer the first year's rate or "scheduled" label
  - [ ] For a threshold, show value+unit
  - [ ] For exemptions, show count of exempt categories
- [ ] Click-to-preview affordance (AC: #3, #6)
  - [ ] Wrap each group chip on the collapsed card in a `<button>` that triggers expand + scroll-to-group
  - [ ] Add a `data-group-id` on the expanded group container so the scroll/highlight target is unambiguous
  - [ ] Add a brief CSS highlight (`ring-2 ring-blue-300` for ~1s) on the targeted group
- [ ] Empty-state per group (AC: #5)
  - [ ] If a group has no parameters set, the headline reads "Not yet set" or equivalent; clicking still expands and scrolls
- [ ] Tests (AC: #6)
  - [ ] Render test: collapsed card shows real values for each group
  - [ ] Click test: clicking a group chip expands, scrolls, and highlights
  - [ ] Empty-state test: ungrouped/unset parameters show "—" or "Not yet set"
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The current renderer at `:471-513` predates EPIC-25's editable parameter groups; it uses static placeholders that look like data. This story replaces it with live derivation.
- Story 27.4 (unify template vs from-scratch) is the natural follow-up — once both card sources share a renderer, this story's improvements apply uniformly. Sequencing: 27.3 first (fix the renderer), then 27.4 (apply it to both sources).
- The screenshots in the user report show the issue: chips like `6 PARAMS`, `RATE_SCHEDULE`, `EXEMPTIONS` are label-only.

### Project Structure Notes

- Files touched: `frontend/src/components/simulation/PortfolioCompositionPanel.tsx`, possibly a new helper at `frontend/src/utils/policy-summary.ts` for `summariseParameterGroup`, and the matching test file
- No backend changes

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.3]
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:471-513]
- [Source: User report 2026-04-26 (screenshots showing 6 PARAMS chips)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
