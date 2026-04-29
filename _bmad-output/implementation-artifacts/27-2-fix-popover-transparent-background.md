# Story 27.2: Fix Popover transparent background

Status: done

## Story

As an analyst opening a formula-help popover on a policy card,
I want the popover to render with an opaque background,
so that the help text is readable against the page content underneath.

## Acceptance Criteria

1. Given the brand theme at `_bmad-output/branding/theme.css` ONLY (tokens must not be defined in `frontend/src/index.css`), when inspected, then `--color-popover` and `--color-popover-foreground` CSS custom properties are defined under the Tailwind v4 `@theme` block.
2. Given the formula-help popover on a policy template card, when opened, then the popover renders with an opaque white background and slate-900 foreground text that meets WCAG AA contrast requirements.
3. Given the two popover consumers at `PortfolioTemplateBrowser.tsx` and `PortfolioCompositionPanel.tsx`, when their className props are inspected, then neither includes `bg-` background overrides (only sizing/typography classes like `w-64 text-xs`).
4. Given the existing popover className `bg-popover text-popover-foreground` in `frontend/src/components/ui/popover.tsx` (PopoverContent component), when the new tokens resolve, then no className change is needed in popover.tsx.
5. Given a PopoverContent component is rendered in tests, when the element's classes are inspected, then the `bg-popover` class is present (verifies theme token contract).

## Tasks / Subtasks

- [x] Define popover theme tokens (AC: #1)
  - [x] Locate the canonical theme file (`_bmad-output/branding/theme.css` per the import in `frontend/src/index.css:3`)
  - [x] Add to the `@theme` block (after the existing surfaces section):
    - `--color-popover: var(--color-white);`
    - `--color-popover-foreground: var(--color-slate-900);`
  - [x] Verify NO popover tokens are added to `frontend/src/index.css` (must stay import-only)
  - [x] Verify Tailwind v4 generates `bg-popover` and `text-popover-foreground` utility classes
- [x] Verify all consumers (AC: #2, #3)
  - [x] Grep for `<PopoverContent` across `frontend/src/components/`
  - [x] Confirm formula-help popover in `PortfolioTemplateBrowser` renders opaque
  - [x] Confirm formula-help popover in `PortfolioCompositionPanel` renders opaque
  - [x] Verify both consumers only pass sizing/typography classes (no `bg-` overrides like `bg-transparent`)
- [x] Add regression test (AC: #5)
  - [x] In `frontend/src/components/screens/__tests__/PoliciesStageScreen.categories.test.tsx`, after existing popover tests, add:
    ```tsx
    it("popover has opaque background class", async () => {
      const user = userEvent.setup();
      render(<PoliciesStageScreen />);
      await waitFor(() => expect(listCategories).toHaveBeenCalled());

      const helpButton = screen.getAllByLabelText(/Formula help for/)[0];
      await user.click(helpButton);

      const popover = screen.getByText("Formula").closest("[class*='bg-popover']");
      expect(popover).toHaveClass('bg-popover');
    });
    ```
- [x] Run quality gates
  - [x] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

### Root Cause

The `PopoverContent` component uses `bg-popover` and `text-popover-foreground` Tailwind classes. These reference CSS custom properties that should be defined in the theme but are currently missing:

```tsx
// frontend/src/components/ui/popover.tsx
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

**Token availability:** `--color-white` is defined in Tailwind v4 defaults (no additional definition needed). Reference: `node_modules/tailwindcss/theme.css:323` as `#fff`.

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
- [Source: frontend/src/components/ui/popover.tsx] - PopoverContent class string using the tokens
- [Source: frontend/src/components/simulation/PortfolioTemplateBrowser.tsx:124-153] - Formula help popover usage
- [Source: frontend/src/index.css:3] - Import order: `@import "@brand/theme.css";`

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Code)

### Debug Log References

None - no debugging required for this theme token fix.

### Completion Notes List

- Added `--color-popover` and `--color-popover-foreground` tokens to `_bmad-output/branding/theme.css` under the `@theme` block
- Tokens defined as `var(--color-white)` and `var(--color-slate-900)` for WCAG AA contrast compliance
- Verified no popover tokens in `frontend/src/index.css` (import-only pattern maintained)
- Verified both consumers (`PortfolioTemplateBrowser.tsx`, `PortfolioCompositionPanel.tsx`) pass only sizing/typography classes (`w-64 text-xs`)
- Added regression test `popover has opaque background class` in `PoliciesStageScreen.categories.test.tsx`
- All quality gates pass: npm test (820 passed), typecheck (clean), lint (7 pre-existing warnings)
- Popover components now render with opaque white background and high-contrast text

### File List

- `_bmad-output/branding/theme.css` - Added popover theme tokens
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.categories.test.tsx` - Added regression test
