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

- [ ] Add Technology step to wizard (AC: #1)
  - [ ] Update step list in `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` (around line 35) to include `technology` between `enable` and `model`
  - [ ] Update `goToStep` mapping and the step-indicator JSX
  - [ ] Coordinate with Story 27.7 to ensure clickable step labels support the new step (forward-jump disabled until visited; backward navigation always allowed)
- [ ] Per-domain UI (AC: #2, #3)
  - [ ] New component `frontend/src/components/engine/TechnologyStep.tsx` rendering per-domain sections
  - [ ] Inside each section: alternatives list (drag-and-drop or up/down arrows for reorder), add/remove buttons, reference radio
  - [ ] Wire to the canonical-set API from Story 28.1
- [ ] Population auto-detection (AC: #4)
  - [ ] Read the active scenario's selected primary population
  - [ ] Fetch (or use cached) population summary that includes `incumbent_<domain>` distinct values (extend an existing endpoint if needed; coordinate with population-summary infrastructure)
  - [ ] Render the green badge when matches are found
- [ ] Mismatch / missing warnings (AC: #5, #6)
  - [ ] Inline banner pattern (use the existing notification banner styling, NOT toasts)
  - [ ] "Add X to my set" action: scaffolds an alternative entry with id, name, empty attributes
- [ ] Match confirmation (AC: #7)
  - [ ] Compute match percentage; if 100%, render confirmation
- [ ] "Use default French set" CTA (AC: #8)
  - [ ] Primary button when no technology set is yet present
  - [ ] Calls the canonical-set API for both domains and applies
- [ ] Orphan-ASC validation (AC: #9)
  - [ ] On Next from the Parameters step OR on Next from Technology if Parameters was already configured, validate ASC keys against the current alternatives list
  - [ ] Surface orphans inline; block proceed
- [ ] Inline-only warnings (AC: #10)
  - [ ] No `toast.*` calls in this component; all surfaces are inline banners or status badges
- [ ] Tests
  - [ ] Render test: each step state (no set, partial set, full set, mismatch, missing column)
  - [ ] CTA test: "Use default French set" applies the canonical set
  - [ ] Add-from-banner test: clicking "Add X to my set" scaffolds an alternative
  - [ ] Orphan-ASC test: removing an alternative with a configured ASC blocks Next
  - [ ] Toast-policy test: assert no `toast.*` is invoked in this step's component tree
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- **No backend changes** in this story. All consumed APIs come from Story 28.1.
- This story depends on 28.1 (types + API) and benefits from 28.2 (incumbent columns), but it should *also* render gracefully if the population lacks the incumbent column (the missing-column warning is the canonical UX for that case).
- Coordinate with Story 27.7 (clickable wizard steps) — both touch `InvestmentDecisionsWizard.tsx`. Sequencing: 27.7 lands first, then 28.4 adds the new step into the existing clickable structure.
- The "Use default French set" CTA mirrors the explicit-action principle from the toast-policy memory: never auto-apply silently; always make the user click.

### Project Structure Notes

- New: `frontend/src/components/engine/TechnologyStep.tsx`, matching test
- Modified: `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` (step list + render switch)
- No backend changes

### References

- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-7]
- [Source: feedback memory: error toasts only on user-initiated actions]
- [Source: Story 28.1] (canonical-set API)
- [Source: Story 28.2] (incumbent column convention)
- [Source: Story 27.7] (clickable wizard steps)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
