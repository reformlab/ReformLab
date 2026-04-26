# Story 27.15: UX-spec amendments (not-started, Population IA, clickable wizard, Stage 5 breadcrumb)

Status: ready-for-dev

## Story

As a tech writer maintaining the UX specification,
I want the Revision 4.1 spec to reflect the decisions made in EPIC-27,
so that future stories can cite the spec as the source of truth instead of relying on this proposal or commit history.

## Acceptance Criteria

1. Given the nav-rail status table in the UX spec (around line 1365 of `_bmad-output/planning-artifacts/ux-design-specification.md`), when this story is complete, then the table documents four states: Active, Complete, Incomplete, **Not started** (the new state from Story 27.6) with visual treatment per state.
2. Given the Population stage prose at line ~1703 ("Population Library is the entry point"), when this story is complete, then the spec's Population IA section explicitly documents the two-sub-step model (Source → Inspect) implemented in Story 27.8.
3. Given the Investment Decisions section, when this story is complete, then it documents that wizard step labels are clickable for back-navigation (Story 27.7) and the "Skip" path for disabled decisions (interaction with Story 27.6's not-started semantics).
4. Given the Stage 5 (Run / Results / Compare) section, when this story is complete, then it documents the sub-view breadcrumb (Story 27.12), the semantic baseline/reform palette (Story 27.12), and unit conventions for Fiscal/Welfare tables (Story 27.12).
5. Given the popover background tokens added in Story 27.2, when this story is complete, then the spec's "Tokens & Theming" section (or equivalent) documents `--popover` and `--popover-foreground` as canonical Shadcn semantic tokens.
6. Given the spec is updated, when reviewed, then the version metadata is bumped (e.g., Revision 4.1.1 with a "Changed in EPIC-27" changelog entry pointing to this story).

## Tasks / Subtasks

- [ ] Update nav-rail status table (AC: #1)
  - [ ] Edit the status table to add the "Not started" row
  - [ ] Document the visual treatment (lighter outline, dashed border, no fill) decided in Story 27.6
- [ ] Document Population IA (AC: #2)
  - [ ] Reconcile prose and IA: Source contains Library and Build as inline switches; Inspect is the gated Explorer
  - [ ] Update wireframe references if applicable
- [ ] Document wizard back-navigation (AC: #3)
  - [ ] Add a sentence explaining clickable step labels in the Investment Decisions section
  - [ ] Document the disabled-forward-jump rule
- [ ] Document Stage 5 conventions (AC: #4)
  - [ ] Sub-view breadcrumb pattern
  - [ ] Semantic palette tokens (`--chart-baseline`, `--chart-reform-a..d`)
  - [ ] Unit-label convention for tables
- [ ] Document popover tokens (AC: #5)
  - [ ] List `--popover`, `--popover-foreground` alongside other semantic tokens
- [ ] Bump version (AC: #6)
  - [ ] Update version field in front matter and add changelog entry
- [ ] Quality gates
  - [ ] No code changes; verify markdown lints clean (or at least no new violations)

## Dev Notes

- This is a documentation-only story. No code changes.
- Owner: tech writer agent (`bmad-tech-writer`) with UX-designer (`bmad-ux-designer`) review for visual decisions.
- This story should land last in EPIC-27 because it documents decisions made by other stories. Sequencing: after stories 27.2, 27.6, 27.7, 27.8, 27.12 land.

### Project Structure Notes

- Files touched: `_bmad-output/planning-artifacts/ux-design-specification.md` only
- No new files

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.15]
- [Source: stories 27.2, 27.6, 27.7, 27.8, 27.12]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
