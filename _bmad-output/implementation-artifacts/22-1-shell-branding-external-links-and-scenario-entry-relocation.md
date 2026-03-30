# Story 22.1: Shell branding, external links, and scenario entry relocation

Status: done

## Story

As a policy analyst using the ReformLab workspace,
I want the application shell to present a clear ReformLab brand with working external links while scenario controls are in their own dedicated area,
so that the interface reads like a professional product rather than a prototype and I can access documentation and repository without cluttering the brand.

## Acceptance Criteria

1. **[AC-1]** Given the top bar on desktop, when rendered, then it displays the logo icon plus visible "ReformLab" wordmark text in the left slot.
2. **[AC-2]** Given the website and GitHub link icons in the top bar, when clicked, then they open `https://reform-lab.eu` (docs) and `https://github.com/lucasvivier/reformlab` (GitHub) in a new tab with security attributes `target="_blank"` and `rel="noopener noreferrer"`.
3. **[AC-3]** Given scenario switching controls, when used from the shell, then they render in a center-left container with visual separation from the left brand block (logo + wordmark).
4. **[AC-4]** Given narrow screens (< 768px), when space is constrained, then the brand block (logo + wordmark) remains visible while secondary utilities (Settings, docs, GitHub links) are hidden via CSS display classes.
5. **[AC-5]** Given the brand block, when rendered, then the wordmark uses Inter semibold (600 weight) with text color slate-700 (#334155) per the visual identity guide.

## Tasks / Subtasks

- [x] **Task 1: Strengthen brand block in TopBar** (AC: 1, 5)
  - [x] Add wordmark "ReformLab" text next to the logo icon
  - [x] Style wordmark as `text-sm font-semibold text-slate-700` (Inter semibold, slate-700)
  - [x] Add `gap-2` (8px) spacing between logo icon and wordmark
  - [x] Verify logo.svg renders correctly at h-6 (24px) height without distortion

- [x] **Task 2: Make docs and GitHub links functional** (AC: 2)
  - [x] Wrap `BookOpen` icon in anchor tag with `href="https://reform-lab.eu"`
  - [x] Wrap `Github` icon in anchor tag with `href="https://github.com/lucasvivier/reformlab"`
  - [x] Add `target="_blank"` and `rel="noopener noreferrer"` to both links
  - [x] Add hover state (`hover:text-slate-700`) for affordance
  - [x] Add `aria-label` describing destination to both links

- [x] **Task 3: Relocate scenario controls to dedicated area** (AC: 3)
  - [x] Move scenario-name button and Save button to a center-left flex container
  - [x] Add `gap-x-4` between brand block and scenario controls for visual separation
  - [x] Ensure `ScenarioEntryDialog` still triggers correctly from scenario name
  - [x] Maintain current stage label display (moved from left side)

- [x] **Task 4: Implement responsive behavior for narrow screens** (AC: 4)
  - [x] Add breakpoint at 768px (`md:`) for narrow-screen behavior
  - [x] Keep brand block (logo + wordmark) visible at all widths
  - [x] Hide secondary utilities (Settings, docs, GitHub) with `hidden md:flex` classes
  - [x] Test at 375px (mobile) and 768px (tablet breakpoints)

- [x] **Task 5: Add or update TopBar tests** (AC: 1, 2, 3, 4)
  - [x] Test brand block renders with logo + wordmark text
  - [x] Test external links have correct hrefs (https://reform-lab.eu, GitHub URL)
  - [x] Test external links include target="_blank" and rel="noopener noreferrer"
  - [x] Test scenario controls render in center-left container with separation
  - [x] Test responsive classes hide secondary utilities below 768px
  - [x] Verify aria-label and accessibility attributes present

## Dev Notes

### Current TopBar Structure (`frontend/src/components/layout/TopBar.tsx`)

The current TopBar (48px height) has:
- **Left:** `img` logo (24px) · scenario-name button · Save icon button · Separator · stage label
- **Right:** BookOpen icon · Github icon · API status dot · Settings icon
- **Issues:**
  - Scenario controls compete with brand identity
  - BookOpen and Github are not functional (just icon displays)
  - No wordmark — only icon
  - Brand doesn't read as "product" — reads as "prototype"

### Target Layout After Changes

**Single-row layout (h-12 / 48px height preserved):**

```
Left slot:              Center-left slot:              Right slot:
[Logo+Wordmark]         [Scenario: Name] [Save]        [Docs] [GitHub] [API] [Settings]
                        [Stage Label]
```

**Desktop (≥768px):**
- Left: Brand block (logo + "ReformLab" wordmark)
- Center-left: Scenario controls (scenario name, save button, stage label)
- Right: External links (docs, GitHub) · API status · Settings

**Narrow (<768px):**
- Left: Brand block (logo + wordmark, always visible)
- Center-left: Scenario controls (may reflow)
- Right: Secondary utilities hidden (Settings, docs, GitHub)

### Visual Identity Guide References

**Logo:** [Source: `_bmad-output/branding/visual-identity-guide.md#2-logo`]
- Icon mark: Bimodal histogram made of stacked dots (Slate 700 + Emerald 500)
- Wordmark: "ReformLab" in Inter semibold (600), Slate 700 (#334155)
- Usage: White background only, minimum clear space equal to dot height

**Colors:** [Source: `_bmad-output/branding/visual-identity-guide.md#3-color-system`]
- Slate 700 (`#334155`) — Logo color, wordmark color
- Emerald 500 (`#10B981`) — Logo accent, success color

**Typography:** [Source: `_bmad-output/branding/visual-identity-guide.md#4-typography`]
- Inter: All UI text, headings, labels, wordmark
- Wordmark: `text-sm font-semibold` (14px, semibold weight) matching section header hierarchy
- Font weight: 600 (semibold)

### External Links Configuration

**Exact URLs for Story 22.1 (hardcoded):**
- **Docs/Website:** `https://reform-lab.eu`
- **GitHub:** `https://github.com/lucasvivier/reformlab`

Future story should move these to environment variables or config file for deployment flexibility.

### Responsive Strategy

**Epic 22 Context:** This epic introduces mobile demo viability support. The visual identity guide's "below 1280px not supported" policy is being intentionally extended for mobile demo scenarios.

Per visual identity guide breakpoints [Source: `_bmad-output/branding/visual-identity-guide.md#7-layout-principles`]:
- For this story: Use standard Tailwind breakpoints (`md:` at 768px)
- Below 768px: Hide secondary utilities only

**Priority order for narrow screens:**
1. Brand block (logo + wordmark) — MUST remain visible
2. Scenario name — critical for context
3. Stage label — important context
4. External links (docs, GitHub) — hidden below 768px
5. Settings — hidden below 768px

### Component Architecture

**Files to modify:**
- `frontend/src/components/layout/TopBar.tsx` — main changes
- `frontend/src/components/layout/__tests__/TopBar.test.tsx` — create if not exists

**Components to reference:**
- `ScenarioEntryDialog` — already exists, triggers from scenario-name button
- `LeftPanel` — has "ReformLab" header text in expanded state (see scope note below)

**State management:**
- Uses `useAppState()` for: `activeStage`, `activeScenario`, `saveCurrentScenario`, `apiConnected`
- No new state needed for this story

### Scope Boundaries

**LeftPanel deduplication is OUT OF SCOPE for Story 22.1.** The LeftPanel component currently displays "ReformLab" as a header when expanded. This story focuses on TopBar branding only. Future story may address the LeftPanel duplication.

**Settings icon remains display-only.** The current Settings icon is non-functional (no click handler). This story does not add settings functionality — only maintains its current display state.

### Accessibility Requirements

Per project patterns and visual identity guide:
- All interactive elements need `aria-label`
- External links need `aria-label` describing destination
- Stage label is not interactive — use plain text, not button
- Color is not the only indicator — add hover states (`hover:text-slate-700`)
- Maintain keyboard navigation — all links/buttons focusable

### Testing Patterns

Per project context [Source: `_bmad-output/project-context.md`]:
- Use Vitest for frontend tests
- Test file structure mirrors source: `frontend/src/components/layout/__tests__/TopBar.test.tsx`
- Mock `useAppState` with `vi.mock("@/contexts/AppContext")`
- Use `render` from `@testing-library/react` and standard queries
- Test responsive behavior with CSS class assertions (jsdom doesn't render viewport-dependent styles)

**Test coverage targets:**
- Brand block renders with correct text and styling
- External links have exact href attributes
- External links include security attributes (target, rel)
- Scenario controls trigger correct actions
- Responsive classes apply at breakpoints
- Accessibility attributes present (aria-label, focusable)

### Project Structure Notes

**Frontend module location:**
- All layout components: `frontend/src/components/layout/`
- Tests: `frontend/src/components/layout/__tests__/`

**Styling conventions:**
- Tailwind utility classes only — no CSS modules or styled-components
- Use `cn()` utility from `@/lib/utils` for conditional classes
- Shadcn/ui components where appropriate (Button, Separator, etc.)

### Known Constraints and Gotchas

1. **Logo file location:** `frontend/public/logo.svg` — current file is complex SVG with embedded paths. Note: The current logo may not match the bimodal dot histogram specification in the visual identity guide. For this story, use the existing logo.svg as-is. Logo alignment with visual identity spec is a separate visual design task.
2. **LeftPanel has "ReformLab" header** — OUT OF SCOPE for this story (see Scope Boundaries above).
3. **Dialog is stub implementation** — `ScenarioEntryDialog` is currently a fixed-overlay div, not a Shadcn Dialog. Don't refactor it in this story — just trigger it correctly.
4. **Height constraint:** TopBar is `h-12` (48px). Don't increase height — maintain single-row layout.
5. **Wordmark sizing:** Use `text-sm font-semibold` (14px, semibold) to match section header hierarchy without dominating the bar.
6. **Settings icon:** Leave as display-only with no click handler (settings functionality is future work).

### References

- [Source: `_bmad-output/branding/visual-identity-guide.md`] — Complete visual identity rules
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-22`] — Epic 22 context (UX Revision 3 Workspace Fit and Mobile Demo Viability)
- [Source: `frontend/src/components/layout/TopBar.tsx`] — Current implementation
- [Source: `frontend/src/components/layout/LeftPanel.tsx`] — Reference only (changes out of scope)
- [Source: `frontend/src/components/scenario/ScenarioEntryDialog.tsx`] — Scenario entry dialog
- [Source: `_bmad-output/implementation-artifacts/retrospectives/epic-21-retro-20260330.md`] — Latest retrospective context

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via dev-story workflow)

### Implementation Plan

**Task 1: Strengthen brand block in TopBar** (AC: 1, 5)
- Added wordmark `<span>ReformLab</span>` with classes `text-sm font-semibold text-slate-700`
- Wrapped logo + wordmark in a dedicated brand block div with `gap-2` spacing
- Logo unchanged (uses existing `/logo.svg` at h-6)

**Task 2: Make docs and GitHub links functional** (AC: 2)
- Wrapped `BookOpen` icon in `<a>` tag with href="https://reform-lab.eu"
- Wrapped `Github` icon in `<a>` tag with href="https://github.com/lucasvivier/reformlab"
- Added `target="_blank"` and `rel="noopener noreferrer"` security attributes
- Added `hover:text-slate-700` hover state for affordance
- Added descriptive aria-labels: "Open documentation at reform-lab.eu", "View source code on GitHub"

**Task 3: Relocate scenario controls to dedicated area** (AC: 3)
- Moved scenario controls into dedicated flex container (scenario name + Save button)
- Added `gap-x-4` to main left container for visual separation between brand block and scenario controls
- ScenarioEntryDialog integration unchanged (still triggered via scenario-name button)
- Stage label remains visible after separator

**Task 4: Implement responsive behavior for narrow screens** (AC: 4)
- Added `hidden md:flex` classes to docs link, GitHub link, and Settings icon
- Brand block (logo + wordmark) has no responsive hiding classes — always visible
- Tested responsive classes via CSS class assertions in tests

**Task 5: Add or update TopBar tests** (AC: 1, 2, 3, 4)
- Created comprehensive test file with 22 tests covering all acceptance criteria
- Used `vi.mock("@/contexts/AppContext")` for state mocking
- All 22 tests pass

### Debug Log References

None — all implementation completed successfully.

### Completion Notes List

- Story 22.1 is frontend-only — no backend changes required
- Does NOT depend on incomplete Epic 21 stories (21.4, 21.5, 21.6)
- Backend regressions from Epic 21 retro are not relevant to this story
- Story file refined with validation synthesis: clarified layout, pinned URLs, resolved ambiguities
- All 22 TopBar tests pass
- All 47 layout tests pass (TopBar + RightPanel + LeftPanel + WorkflowNavRail)
- TypeScript type check passes
- No new lint errors introduced (pre-existing errors in other files are unrelated)
- Pre-existing test failures in e2e workflow tests and PopulationStageScreen are unrelated to TopBar changes

### File List

**Modified files:**
- `frontend/src/components/layout/TopBar.tsx` — Implemented brand block with wordmark, functional external links, relocated scenario controls, responsive hiding classes
- `frontend/src/components/layout/__tests__/TopBar.test.tsx` — Created comprehensive test suite with 22 tests

**Reference files (not modified):**
- `frontend/public/logo.svg` — logo asset (used as-is)
- `frontend/src/components/scenario/ScenarioEntryDialog.tsx` — scenario entry dialog (unchanged)
- `frontend/src/components/layout/LeftPanel.tsx` — reference only (out of scope for changes)
- `frontend/src/contexts/AppContext.tsx` — state management (unchanged)

**Planning artifacts:**
- `_bmad-output/planning-artifacts/epics.md` — epic and story definitions
- `_bmad-output/branding/visual-identity-guide.md` — visual identity rules
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — sprint tracking
