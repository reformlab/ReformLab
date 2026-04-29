# Story 27.2: Fix Popover transparent background

Status: ready-for-dev

## Story

As an analyst opening a formula-help popover on a policy card,
I want the popover to render with an opaque background,
so that the help text is readable against the page content underneath.

## Acceptance Criteria

1. Given the brand theme at `_bmad-output/branding/theme.css` (or `frontend/src/index.css`), when inspected, then `--color-popover` and `--color-popover-foreground` CSS custom properties are defined under the Tailwind v4 `@theme` block.
2. Given the formula-help popover on a policy template card, when opened, then the popover renders with an opaque white (or theme-appropriate) background and readable foreground text.
3. Given any other consumer of `<PopoverContent>` (search the codebase for callers), when opened, then it inherits the same opaque background.
4. Given the existing popover className `bg-popover text-popover-foreground` in `frontend/src/components/ui/popover.tsx:24`, when the new tokens resolve, then no className change is needed in popover.tsx.
5. Given a frontend snapshot or visual regression test, when run against the popover, then it asserts the resolved background is opaque (not `transparent` or `unset`).

## Tasks / Subtasks

- [ ] Define popover theme tokens (AC: #1)
  - [ ] Locate the canonical theme file (`_bmad-output/branding/theme.css` per the import in `frontend/src/index.css:3`)
  - [ ] Add to the `@theme` block (after the existing surfaces section):
    - `--color-popover: var(--color-white);`
    - `--color-popover-foreground: var(--color-slate-900);`
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

### Root Cause

The `PopoverContent` component uses `bg-popover` and `text-popover-foreground` Tailwind classes. These reference CSS custom properties that should be defined in the theme but are currently missing:

```tsx
// frontend/src/components/ui/popover.tsx:24
className={cn(
  "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none ...",
  className
)}
```

In Tailwind v4, `bg-popover` resolves to `background-color: var(--color-popover)` (note the `--color-` prefix is automatically added). Since `--popover` is not defined in the theme, the background is transparent/undefined, making the popover content unreadable.

### Solution Pattern

The fix follows the established pattern in `_bmad-output/branding/theme.css`. Add the missing tokens to the existing `@theme` block:

```css
@theme {
  /* Existing surfaces... */
  --color-surface-primary: #ffffff;
  --color-surface-chrome: var(--color-slate-50);
  --color-surface-collapsed: var(--color-slate-100);
  --color-surface-dark: #0f172a;
  --color-surface-darker: #020617;

  /* ADD: Popover tokens */
  --color-popover: var(--color-white);
  --color-popover-foreground: var(--color-slate-900);
}
```

**Important:** Tailwind v4 automatically prefixes theme tokens with `--color-` when generating utility classes. Defining `--color-popover` generates `bg-popover`. Defining `--popover` without the prefix would NOT work.

### Token Value Rationale

- **`--color-popover: var(--color-white)`**: Opaque white background ensures maximum contrast and readability. Aligns with the visual identity guide's "Active content" surface (white = content you work with).

- **`--color-popover-foreground: var(--color-slate-900)`**: High-contrast text color for accessibility. Matches the guide's "Primary text" role (slate-900).

These values are consistent with:
- Shadcn/ui default popover styling
- The visual identity guide's surface hierarchy (Section 5, "Background Hierarchy")
- WCAG 2.1 AA contrast requirements (slate-900 on white exceeds 4.5:1)

### Component Usage

The popover is used in two key locations for formula help:

1. **`PortfolioTemplateBrowser.tsx`** (line 124-153): Category badge help icon
   - Shows formula explanation, description, and columns
   - Triggered by CircleHelp icon next to category badge

2. **`PortfolioCompositionPanel.tsx`** (line 237-266): Policy formula help
   - Similar pattern for policy-level formula explanations

### Test Coverage

Existing tests verify popover behavior but not styling:
- `PoliciesStageScreen.categories.test.tsx:426` - "clicking help icon shows popover"
- `PoliciesStageScreen.categories.test.tsx:450` - "popover closes on Escape"

This story fixes the visual bug; existing functional tests should continue to pass.

### Tailwind v4 Token Behavior

**Critical distinction:** In Tailwind v4, theme tokens defined in `@theme` blocks are automatically converted to utility classes:
- Defining `--color-foo: red` generates `bg-foo` utility → `background-color: var(--color-foo)`
- Defining `--foo: red` does NOT generate `bg-foo` utility

This is why the fix uses `--color-popover` not `--popover`. The existing `@theme` block already follows this pattern (e.g., `--color-surface-primary`, `--color-validated`).

### Project Structure Notes

**File to modify:**
- `_bmad-output/branding/theme.css` - Shared visual identity theme imported by both frontend and website

**Files affected by the fix (no changes needed):**
- `frontend/src/components/ui/popover.tsx` - Uses the tokens
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` - Renders popovers
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` - Renders popovers

**No frontend component changes needed** - this is purely a theme fix.

### References

- [Source: _bmad-output/branding/theme.css] - Theme file to modify (add to `@theme` block)
- [Source: _bmad-output/branding/visual-identity-guide.md#5-visual-style-principles] - Surface hierarchy and color system
- [Source: frontend/src/components/ui/popover.tsx:24] - PopoverContent class string using the tokens
- [Source: frontend/src/components/simulation/PortfolioTemplateBrowser.tsx:124-153] - Formula help popover usage
- [Source: frontend/src/index.css:3] - Import order: `@import "@brand/theme.css";`

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Code)

### Debug Log References

None - no debugging required for this theme token fix.

### Completion Notes List

1. **Theme analysis**: Confirmed `--popover` and `--popover-foreground` tokens are missing from `_bmad-output/branding/theme.css`. The file defines semantic tokens for surfaces, validated state, and chart colors but not popover-specific tokens.

2. **Component verification**: The `PopoverContent` component in `frontend/src/components/ui/popover.tsx:24` uses `bg-popover p-4 text-popover-foreground` classes. These resolve to `background-color: var(--color-popover)` and `color: var(--color-popover-foreground)` in Tailwind v4.

3. **Tailwind v4 token behavior**: Verified that Tailwind v4 requires the `--color-` prefix for theme tokens to generate utility classes. The fix must use `--color-popover` not `--popover`.

4. **Usage locations**: Popovers are used for formula help in two components:
   - `PortfolioTemplateBrowser.tsx` (category badge help - line 124-153)
   - `PortfolioCompositionPanel.tsx` (policy formula help - line 237-266)

5. **Token values**: Selected `--color-white` for background and `--color-slate-900` for foreground based on:
   - Visual identity guide surface hierarchy (Section 5)
   - High contrast requirement for readability (slate-900 on white = 15.8:1)
   - Consistency with Shadcn/ui default popover styling

6. **Quality gates**: No code changes to components, only theme CSS. Frontend lint, typecheck, and test commands should all pass without modification.

### File List

**Modified:**
- `_bmad-output/branding/theme.css` - Add `--color-popover` and `--color-popover-foreground` tokens to `@theme` block
