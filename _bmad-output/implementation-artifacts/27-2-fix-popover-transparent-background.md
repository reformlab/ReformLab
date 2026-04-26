# Story 27.2: Fix Popover transparent background

Status: ready-for-dev

## Story

As an analyst opening a formula-help popover on a policy card,
I want the popover to render with an opaque background,
so that the help text is readable against the page content underneath.

## Acceptance Criteria

1. Given the brand theme at `_bmad-output/branding/theme.css` (or `frontend/src/index.css`), when inspected, then `--popover` and `--popover-foreground` CSS custom properties are defined under the Tailwind v4 `@theme` block.
2. Given the formula-help popover on a policy template card, when opened, then the popover renders with an opaque white (or theme-appropriate) background and readable foreground text.
3. Given any other consumer of `<PopoverContent>` (search the codebase for callers), when opened, then it inherits the same opaque background.
4. Given the existing popover className `bg-popover text-popover-foreground` in `frontend/src/components/ui/popover.tsx:24`, when the new tokens resolve, then no className change is needed in popover.tsx.
5. Given a frontend snapshot or visual regression test, when run against the popover, then it asserts the resolved background is opaque (not `transparent` or `unset`).

## Tasks / Subtasks

- [ ] Define popover theme tokens (AC: #1)
  - [ ] Locate the canonical theme file (`_bmad-output/branding/theme.css` per the import in `frontend/src/index.css:3`)
  - [ ] Add to the `@theme` block:
    - `--popover: var(--color-white, #ffffff);`
    - `--popover-foreground: var(--color-slate-900, #0f172a);`
  - [ ] Verify Tailwind v4 generates `bg-popover` and `text-popover-foreground` utility classes
- [ ] Verify all consumers (AC: #2, #3)
  - [ ] Grep for `<PopoverContent` across `frontend/src/components/`
  - [ ] Confirm formula-help popover in `PortfolioTemplateBrowser` renders opaque
  - [ ] Confirm formula-help popover in `PortfolioCompositionPanel` renders opaque
  - [ ] If a consumer overrides `bg-` class with `bg-transparent` or similar, fix it
- [ ] Add regression test (AC: #5)
  - [ ] Add a test in `frontend/src/components/ui/__tests__/popover.test.tsx` (create if absent) asserting the rendered popover element has `bg-popover` class and the resolved style is not transparent
- [ ] Run quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The bug is that `bg-popover` was being applied but the underlying CSS custom property was undefined, leaving the background unset.
- Tailwind v4 reads `--color-*` and `--*` tokens from `@theme`. The popover token doesn't need `--color-` prefix — `--popover` is the canonical Shadcn semantic name and Tailwind v4 generates the matching class.
- If the theme file is read-only (in `_bmad-output/branding/`), copy the addition to `frontend/src/index.css` after the `@import "@brand/theme.css";` line.

### Project Structure Notes

- Files touched: `_bmad-output/branding/theme.css` (preferred) or `frontend/src/index.css`; optionally a new test file
- No changes to `popover.tsx` expected

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.2]
- [Source: frontend/src/components/ui/popover.tsx:23-26]
- [Source: frontend/src/index.css:3] (import order)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
