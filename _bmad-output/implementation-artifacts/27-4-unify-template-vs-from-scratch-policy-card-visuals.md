# Story 27.4: Unify template vs from-scratch policy-card visuals

Status: ready-for-dev

## Story

As an analyst composing a policy set,
I want template-instantiated policies and from-scratch policies to look and behave identically in the composition panel,
so that the source of a policy is not visible in its UI treatment and editing affordances are consistent.

## Acceptance Criteria

1. Given two policies side by side (one from-template, one from-scratch), when displayed in the composition panel, then their card structure, controls, and editing affordances are visually identical.
2. Given a template-instantiated policy, when added to the composition, then `editableParameterGroups` is populated using the same scaffolding logic that from-scratch policies use, so the unified renderer has data.
3. Given a template policy, when "Edit groups" is clicked, then group rename, add, move, delete-empty, and block-delete-non-empty work with the same UI and behaviour as Story 25.4 specified for from-scratch policies.
4. Given group edits on a template policy, when the policy set is saved and reloaded, then group names, order, and parameter membership persist (extends Story 25.5 reload coverage).
5. Given the unified `<PolicyCard>` component (extracted in this story), when used by both the from-template and from-scratch flows, then no source-specific branching exists in the renderer (only data differs).
6. Given the existing template-add tests and the existing from-scratch-add tests, when run, then both cover the unified card with identical assertions.

## Tasks / Subtasks

- [ ] Extract `<PolicyCard>` component (AC: #1, #5)
  - [ ] In `PortfolioCompositionPanel.tsx:155-531`, identify the rendering logic and split it into a new component `frontend/src/components/policies/PolicyCard.tsx`
  - [ ] The component takes a single `entry: CompositionEntry` and emits the same callbacks the panel emits today (onParameterChange, onGroupRename, onGroupAdd, onGroupDelete, onGroupMove, onRemovePolicy)
- [ ] Populate `editableParameterGroups` for template policies (AC: #2, #3)
  - [ ] Find the template-add code path (likely in `usePortfolioLoadDialog` or the `+ Add` action handler)
  - [ ] On add, scaffold `editableParameterGroups` from the template's parameter schema using the same factory used for from-scratch policies (line ~204-207 referenced in the audit)
- [ ] Lift "Edit groups" affordance for both sources (AC: #3)
  - [ ] Remove the source-specific branch that hides the gear icon for template policies
  - [ ] Show the icon whenever `editableParameterGroups` is present
- [ ] Persistence + reload coverage (AC: #4)
  - [ ] Add or extend tests in `PoliciesStageScreen.test.tsx` (or a dedicated PolicyCard test file) covering: template policy → group rename → save → reload → name persisted
  - [ ] Same flow for: template policy → group add → save → reload
- [ ] Side-by-side test (AC: #1)
  - [ ] Render test: one template policy + one from-scratch policy → assert identical DOM structure for card frame, group section, controls
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- Sequencing: this story depends on Story 27.3 (live parameter values in cards) so the unified renderer has informative content.
- Cross-checks: this work does NOT change the underlying API contract for portfolios. `instanceId`, `templateId`, `parameters`, `rateSchedule`, and `editableParameterGroups` all already exist in `CompositionEntry`. We're only making the UI consistent.
- Story 27.11 will later unify the type system itself (`CompositionEntry` ↔ `PortfolioPolicyItem`), which makes this renderer extraction even cleaner.

### Project Structure Notes

- New file: `frontend/src/components/policies/PolicyCard.tsx` (or `frontend/src/components/simulation/PolicyCard.tsx` to match the existing simulation directory)
- Modified: `PortfolioCompositionPanel.tsx`, the template-add path (likely in a hook), tests
- Optionally: refactor the existing `editableParameterGroups` factory to a shared utility under `frontend/src/utils/`

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.4]
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:155-531]
- [Source: 25.4 acceptance criteria for editable parameter groups]
- [Source: 25.5 acceptance criteria for policy-set save/load round-trip]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
