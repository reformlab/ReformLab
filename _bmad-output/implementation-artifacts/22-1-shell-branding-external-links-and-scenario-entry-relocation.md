# Story 22.1: Shell branding, external links, and scenario entry relocation

Status: ready-for-dev

## Story

As a policy analyst using the ReformLab workspace,
I want the application shell to present a clear ReformLab brand with working external links while scenario controls are in their own dedicated area,
so that the interface reads like a professional product rather than a prototype and I can access documentation and repository without cluttering the brand.

## Acceptance Criteria

1. **[AC-1]** Given the top bar on desktop, when rendered, then it shows a stronger ReformLab brand block with logo plus wordmark "ReformLab" (not just icon).
2. **[AC-2]** Given the website and GitHub link icons in the top bar, when clicked, then they open the configured external destinations (`https://reform-lab.eu` and GitHub repo URL) in a new tab (`target="_blank"`, `rel="noopener noreferrer"`).
3. **[AC-3]** Given scenario switching controls, when used from the shell, then they are accessible from a dedicated controls area separate from the brand block (not beside the logo).
4. **[AC-4]** Given narrow screens (< 768px), when space is constrained, then the brand block remains visible while secondary utilities (Settings, docs/GitHub links) can collapse into an overflow menu or hide.
5. **[AC-5]** Given the brand block, when rendered, then it uses the correct logo icon and wordmark styling per the visual identity guide (Slate 700 for wordmark, bimodal histogram icon).

## Tasks / Subtasks

- [ ] **Task 1: Strengthen brand block in TopBar** (AC: 1, 5)
  - [ ] Add wordmark "ReformLab" text next to the logo icon
  - [ ] Style wordmark per visual identity guide (Inter semibold, slate-700)
  - [ ] Ensure proper spacing between icon and wordmark
  - [ ] Verify logo.svg renders correctly at h-6 (24px) height

- [ ] **Task 2: Make docs and GitHub links functional** (AC: 2)
  - [ ] Wrap `BookOpen` icon in anchor tag with `href` to `https://reform-lab.eu` or docs URL
  - [ ] Wrap `Github` icon in anchor tag with `href` to GitHub repo URL
  - [ ] Add `target="_blank"` and `rel="noopener noreferrer"` to both links
  - [ ] Add hover state (`hover:text-slate-700`) for affordance
  - [ ] Ensure `aria-label` is present on both links

- [ ] **Task 3: Relocate scenario controls to dedicated area** (AC: 3)
  - [ ] Move scenario-name button and Save button to a dedicated "Scenario Controls" section
  - [ ] Create visual separation between brand block and scenario controls
  - [ ] Ensure `ScenarioEntryDialog` still triggers correctly from scenario name
  - [ ] Maintain current stage label display (moved from left side)

- [ ] **Task 4: Implement responsive behavior for narrow screens** (AC: 4)
  - [ ] Add breakpoint at 768px for narrow-screen behavior
  - [ ] Keep brand block (logo + wordmark) visible at all widths
  - [ ] Hide secondary utilities (Settings, docs, GitHub) on very narrow screens or move to overflow
  - [ ] Test at 375px (mobile) and 768px (tablet breakpoints)

- [ ] **Task 5: Add or update TopBar tests** (AC: 1, 2, 3, 4)
  - [ ] Test brand block renders with logo + wordmark
  - [ ] Test external links have correct hrefs and open in new tab
  - [ ] Test scenario controls are in dedicated area
  - [ ] Test responsive behavior at different breakpoints
  - [ ] Verify `aria-label` and accessibility attributes

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

```
┌─────────────────────────────────────────────────────────────┐
│ [Logo+Wordmark]  │  Scenario: [Name] [Save]  │  Stage Label │
│                  │  (dedicated area)        │              │
│                           [stage]                        │
├─────────────────────────────────────────────────────────────┤
│ [Docs] [GitHub]  •  [API Status]  [Settings]              │
└─────────────────────────────────────────────────────────────┘
```

**Desktop (≥768px):**
- Left: Brand block (logo + "ReformLab" wordmark)
- Center-left: Scenario controls (scenario name, save button, stage label)
- Right: External links (docs, GitHub) · API status · Settings

**Narrow (<768px):**
- Left: Brand block (always visible)
- Scenario controls may stack or reflow
- Secondary utilities hide or move to overflow

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
- `text-base` (16px) or `text-sm` (14px) for wordmark
- `font-semibold` (600 weight) for wordmark

### External Links Configuration

External link URLs should be configurable but have sensible defaults:
- **Docs/Website:** `https://reform-lab.eu` or docs subdomain
- **GitHub:** `https://github.com/lucasvivier/reformlab` (or actual repo URL)

For Story 22.1, hardcode these URLs. Future story can make them configurable.

### Responsive Strategy

Per visual identity guide breakpoints [Source: `_bmad-output/branding/visual-identity-guide.md#7-layout-principles`]:
- Small laptop: 1280–1365px — panels collapse (not relevant for top bar)
- For this story: Use standard Tailwind breakpoints (`md:` at 768px)

**Priority order for narrow screens:**
1. Brand block (logo + wordmark) — MUST remain visible
2. Scenario name — critical for context
3. Stage label — important context
4. External links (docs, GitHub) — can hide on very narrow
5. Settings — can hide on very narrow

### Component Architecture

**Files to modify:**
- `frontend/src/components/layout/TopBar.tsx` — main changes
- `frontend/src/components/layout/__tests__/TopBar.test.tsx` — create if not exists

**Components to reference:**
- `ScenarioEntryDialog` — already exists, triggers from scenario-name button
- `LeftPanel` — has "ReformLab" header text in expanded state; may need coordination

**State management:**
- Uses `useAppState()` for: `activeStage`, `activeScenario`, `saveCurrentScenario`, `apiConnected`
- No new state needed for this story

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
- Test responsive behavior with viewport width changes or CSS classes

**Test coverage targets:**
- Brand block renders with correct styling
- External links have correct href attributes
- External links open in new tab (`target="_blank"`)
- Scenario controls trigger correct actions
- Responsive classes apply correctly
- Accessibility attributes present

### Project Structure Notes

**Frontend module location:**
- All layout components: `frontend/src/components/layout/`
- Tests: `frontend/src/components/layout/__tests__/`

**Styling conventions:**
- Tailwind utility classes only — no CSS modules or styled-components
- Use `cn()` utility from `@/lib/utils` for conditional classes
- Shadcn/ui components where appropriate (Button, Separator, etc.)

### Known Constraints and Gotchas

1. **Logo file location:** `frontend/public/logo.svg` — current file is complex SVG with embedded paths
2. **LeftPanel has "ReformLab" header** — avoid duplication; may need to remove from LeftPanel when TopBar wordmark is added (but that's optional for this story)
3. **Dialog is stub implementation** — `ScenarioEntryDialog` is currently a fixed-overlay div, not a Shadcn Dialog. Don't refactor it in this story — just trigger it correctly.
4. **Height constraint:** TopBar is `h-12` (48px). Don't increase height significantly.
5. **Wordmark sizing:** Keep wordmark modest — `text-sm` or `text-base` to avoid dominating the bar.

### References

- [Source: `_bmad-output/branding/visual-identity-guide.md`] — Complete visual identity rules
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-22`] — Epic 22 context
- [Source: `frontend/src/components/layout/TopBar.tsx`] — Current implementation
- [Source: `frontend/src/components/layout/LeftPanel.tsx`] — Coordination needed for "ReformLab" header
- [Source: `frontend/src/components/scenario/ScenarioEntryDialog.tsx`] — Scenario entry dialog
- [Source: `_bmad-output/implementation-artifacts/retrospectives/epic-21-retro-20260330.md`] — Latest retrospective context

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Debug Log References

None — story creation phase.

### Completion Notes List

- Story 22.1 is frontend-only — no backend changes required
- Does NOT depend on incomplete Epic 21 stories (21.4, 21.5, 21.6)
- Backend regressions from Epic 21 retro are not relevant to this story
- Story file ready for dev with comprehensive context

### File List

**Source files to modify:**
- `frontend/src/components/layout/TopBar.tsx` (main changes)
- `frontend/src/components/layout/__tests__/TopBar.test.tsx` (create or update)

**Reference files:**
- `frontend/public/logo.svg` — logo asset
- `frontend/src/components/scenario/ScenarioEntryDialog.tsx` — scenario entry dialog
- `frontend/src/components/layout/LeftPanel.tsx` — consider for "ReformLab" header deduplication
- `frontend/src/contexts/AppContext.tsx` — state management

**Planning artifacts:**
- `_bmad-output/planning-artifacts/epics.md` — epic and story definitions
- `_bmad-output/branding/visual-identity-guide.md` — visual identity rules
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — sprint tracking

