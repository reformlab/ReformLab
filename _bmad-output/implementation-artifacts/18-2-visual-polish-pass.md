# Story 18.2: Visual Polish Pass — Rounded Corners, Shadows, Header, Login

Status: draft

## Story

As a policy analyst,
I want the application to feel polished and professional with rounded containers, subtle depth, a branded header, and a welcoming login screen,
so that I feel confident using the tool for serious policy analysis work.

## Acceptance Criteria

1. **AC-1: Rounded corners on containers** — Given all Card, section, and panel containers across all 9 screens, when rendered, then they use `rounded-lg` (8px radius). Buttons and inputs use `rounded-md` (6px radius). The workspace outer container uses `rounded-xl` (12px radius).

2. **AC-2: Elevation and shadows** — Given primary content containers (Cards, section panels), when rendered, then they use `shadow-sm` for subtle depth. Elevated overlays (modals, dialogs, detail panels like YearDetailPanel) use `shadow-lg`. The workspace outer frame uses `shadow-md`.

3. **AC-3: Branded header bar** — Given the main workspace header (`App.tsx:248-282`), when rendered, then it displays a gradient background (`bg-gradient-to-r from-blue-600 to-violet-600`) with white text, includes a simple icon/logo mark (use `Activity` or `BarChart3` from lucide-react as placeholder), and the subtitle text is `text-blue-100`.

4. **AC-4: Polished login screen** — Given the PasswordPrompt screen, when rendered, then the login card uses `rounded-xl shadow-lg`, the background shows a centered layout with the ReformLab brand mark above the form, and the card has a max-width of `sm` with generous padding (`p-8`).

5. **AC-5: Consistent border treatment** — Given all `border border-slate-200` instances, when the rounded corners are applied, then borders remain but are softened with the radius. Replace any hard `border` on outer containers with `ring-1 ring-slate-200` for a cleaner look at rounded corners.

6. **AC-6: No visual regressions** — Given all existing screens, when rendered at 1280px+ viewport, then no layouts are broken, no content is clipped by border radius, and chart containers render correctly within rounded parents.

## Tasks / Subtasks

- [ ] Task 1: Global style updates
  - [ ] 1.1: Update `index.css` — add default border-radius to the shadcn Card component layer if possible, or document the manual approach
  - [ ] 1.2: Update shadcn `Card` component in `components/ui/card.tsx` to include `rounded-lg shadow-sm` by default
  - [ ] 1.3: Update shadcn `Button` component to ensure `rounded-md` is applied
  - [ ] 1.4: Update shadcn `Input` component to ensure `rounded-md` is applied
  - [ ] 1.5: Update shadcn `Badge` component to use `rounded-md` (currently likely `rounded-full` or none)

- [ ] Task 2: Header redesign
  - [ ] 2.1: Update the header div in `App.tsx:248-282` with gradient background and white text
  - [ ] 2.2: Add an icon from lucide-react (e.g., `Activity`, `BarChart3`, or `Leaf` for environmental theme)
  - [ ] 2.3: Update header action buttons to use `variant="ghost"` with white text styling or a `variant="secondary"` that works on dark backgrounds

- [ ] Task 3: Login screen polish
  - [ ] 3.1: Update `PasswordPrompt.tsx` — larger card padding, rounded-xl, shadow-lg, brand mark
  - [ ] 3.2: Add a subtle tagline below "ReformLab" (e.g., "Environmental Policy Analysis Platform")
  - [ ] 3.3: Background: use the existing body gradient, add a centered decorative element or just clean spacing

- [ ] Task 4: Panel and section updates
  - [ ] 4.1: Search-and-update all `border border-slate-200 bg-white p-3` patterns to add `rounded-lg shadow-sm`
  - [ ] 4.2: Update WorkspaceLayout outer container from sharp border to `rounded-xl shadow-md ring-1 ring-slate-200`
  - [ ] 4.3: Update modal/dialog components to use `rounded-xl shadow-lg`
  - [ ] 4.4: Update YearDetailPanel sidebar to use `rounded-l-lg shadow-lg`

- [ ] Task 5: Verification
  - [ ] 5.1: Visual check all 9 screens at 1280px, 1440px, 1920px
  - [ ] 5.2: Verify Recharts containers render correctly inside rounded parents
  - [ ] 5.3: Run existing component tests — no failures

## Dev Notes

- The `border border-slate-200 bg-white p-3` pattern appears in ~40+ places across all screens. A bulk find-and-replace is possible but review each instance — some are inline table rows or chart wrappers where radius may not apply
- Consider adding a CSS utility class `.panel` that bundles `rounded-lg border border-slate-200 bg-white p-3 shadow-sm` to avoid repeating 5 classes everywhere
- Shadows: `shadow-sm` is very subtle (just enough to lift off the background). Don't over-shadow — this isn't Material Design, aim for clean and modern
- For the header gradient, test with both light and dark mode to ensure contrast. Current app is light-only so just ensure WCAG contrast on white text over blue-600→violet-600 gradient
