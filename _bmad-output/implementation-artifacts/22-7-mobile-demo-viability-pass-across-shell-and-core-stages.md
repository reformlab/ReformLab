# Story 22.7: Mobile demo viability pass across shell and core stages

Status: ready-for-dev

## Story

As a policy analyst giving a demo on a phone,
I want the ReformLab workspace to remain usable for walkthroughs and light edits on narrow screens,
so that I can demonstrate key features without requiring a laptop.

## Acceptance Criteria

1. **[AC-1]** Given a 375px viewport (iPhone SE), when the application is used, then there is no page-level horizontal overflow (no horizontal scroll on body/html elements).
2. **[AC-2]** Given phone-width navigation, when the user needs to change stage, then stage switching is reachable from every screen in one tap or equivalent compact interaction.
3. **[AC-3]** Given the top bar at narrow widths, when rendered, then brand (logo + wordmark), current stage label, and scenario name remain visible while secondary utilities (docs, GitHub, settings) move into overflow or are hidden.
4. **[AC-4]** Given Policies, Population, and Scenario screens at phone width, when used, then split layouts stack vertically and secondary panels (right panel: Help) move below primary editing surfaces.
5. **[AC-5]** Given desktop widths above the mobile breakpoint, when the workspace is viewed, then the existing desktop layouts remain intact with three-panel resizable layout (left nav, main content, right help).

## Tasks / Subtasks

- [ ] **Task 1: Remove desktop-only warning banner from App.tsx** (AC: 1, 2, 3, 4)
  - [ ] Delete the `window.innerWidth < 1280` warning banner from `frontend/src/App.tsx` (lines 216-220)
  - [ ] Remove or restructure the `isNarrow` state logic that forces left/right panel collapse at 1024px
  - [ ] Keep the keyboard shortcuts (⌘[ / ⌘] for panel toggling) as they don't conflict with mobile
  - [ ] Verify the app loads without the warning banner at 375px viewport width

- [ ] **Task 2: Update TopBar for narrow screen viability** (AC: 2, 3)
  - [ ] Verify current TopBar responsive behavior in `frontend/src/components/layout/TopBar.tsx`
  - [ ] Ensure brand block (logo + wordmark) remains visible at narrow widths
  - [ ] Ensure scenario name trigger remains accessible (truncate with ellipsis if needed)
  - [ ] Verify secondary utilities already use `hidden md:flex` classes (docs, GitHub, settings icons)
  - [ ] Add overflow menu for utilities if needed (optional, only if current `hidden md:flex` is insufficient)

- [ ] **Task 3: Replace desktop nav rail with compact mobile stage switcher** (AC: 2)
  - [ ] Create mobile stage switcher component for narrow screens
  - [ ] At desktop breakpoints, keep existing `WorkflowNavRail` in left panel
  - [ ] At mobile breakpoints (sm, md), replace left panel with horizontal stage selector
  - [ ] Mobile selector should use: `flex gap-2 overflow-x-auto` with labeled buttons or tabs
  - [ ] Ensure stage navigation remains reachable from every screen at phone width
  - [ ] Consider hiding left/right panels completely on mobile and showing stage switcher above main content

- [ ] **Task 4: Make WorkspaceLayout responsive with mobile-first panels** (AC: 4)
  - [ ] Update `frontend/src/components/layout/WorkspaceLayout.tsx` to handle mobile widths
  - [ ] At desktop (lg+): keep existing three-panel resizable layout (ResizablePanelGroup)
  - [ ] At mobile (< 768px): hide ResizablePanelGroup, render single column layout
  - [ ] Mobile layout: TopBar → Mobile Stage Switcher → Main Content → (Right Panel collapsed/drawer)
  - [ ] Use `hidden lg:flex` for desktop panels, `flex lg:hidden` for mobile layout
  - [ ] Ensure no fixed-width constraints cause horizontal overflow (use `w-full`, `min-w-0`, `flex-1`)

- [ ] **Task 5: Stack Policies stage layout vertically on mobile** (AC: 4)
  - [ ] Review current `grid-cols-1 lg:grid-cols-2` in `PoliciesStageScreen.tsx` (line 569)
  - [ ] Verify single-column stacking works at mobile breakpoints
  - [ ] Ensure toolbar actions wrap or scroll without overflow (`flex-wrap`, `overflow-x-auto`)
  - [ ] Test that template browser and portfolio composition panels stack vertically
  - [ ] Ensure Save/Load/Clone buttons remain accessible on mobile

- [ ] **Task 6: Stack Population library as single-column cards on mobile** (AC: 4)
  - [ ] Review current `grid-cols-2 gap-4 xl:grid-cols-3 2xl:grid-cols-4` in `PopulationLibraryScreen.tsx` (line 242)
  - [ ] Add mobile breakpoint: `grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
  - [ ] Ensure population cards render full-width at phone breakpoint
  - [ ] Verify toolbar actions (Upload, Build New) don't overflow horizontally
  - [ ] Test Quick Test Population card renders correctly at 375px

- [ ] **Task 7: Stack Scenario (Engine) stage layout vertically on mobile** (AC: 4)
  - [ ] Review current two-column layout in `EngineStageScreen.tsx`
  - [ ] Left column: configuration form (time horizon, population, seed, investment decisions, discount rate)
  - [ ] Right column: `RunSummaryPanel` + `ValidationGate` (fixed-width `w-80`)
  - [ ] At mobile: stack right panel below main form, remove fixed `w-80` constraint
  - [ ] Use `lg:w-80 w-full` for right panel at mobile breakpoints
  - [ ] Ensure Investment Decisions Wizard renders correctly on narrow screens
  - [ ] Test Run Simulation button remains visible and accessible on mobile

- [ ] **Task 8: Update LeftPanel and RightPanel for mobile responsiveness** (AC: 4)
  - [ ] Review `LeftPanel.tsx` and `RightPanel.tsx` collapse variants
  - [ ] At mobile: hide left nav rail and right help panel by default
  - [ ] Add collapsible drawer or bottom sheet for help panel on mobile (optional, if space permits)
  - [ ] Ensure panel toggle buttons don't interfere with mobile stage switcher
  - [ ] Test that panels collapse correctly when `isNarrow` is true at mobile widths

- [ ] **Task 9: Update viewport meta tag and CSS base styles** (AC: 1)
  - [ ] Verify `frontend/index.html` has correct viewport meta: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
  - [ ] Verify `frontend/src/index.css` has `box-sizing: border-box` and `width: 100%` on html/body
  - [ ] Ensure no `min-width` constraints on body/html that prevent mobile rendering
  - [ ] Add CSS override if needed: `* { max-width: 100vw; }` to prevent overflow

- [ ] **Task 10: Write tests for mobile responsive behavior** (AC: 1, 2, 3, 4, 5)
  - [ ] Test viewport width 375px (iPhone SE) renders without horizontal overflow
  - [ ] Test stage navigation is reachable via mobile stage switcher
  - [ ] Test TopBar brand block remains visible at narrow widths
  - [ ] Test Policies stage stacks vertically at mobile breakpoints
  - [ ] Test Population library uses single-column grid at mobile breakpoints
  - [ ] Test Scenario (Engine) stage stacks right panel below form at mobile breakpoints
  - [ ] Test desktop layouts remain unchanged at 1280px+ viewport width

## Dev Notes

### Current Implementation Analysis

**Desktop-only Warning Banner (CRITICAL)**
- Location: `frontend/src/App.tsx` lines 216-220
- Shows amber banner at widths < 1280px: "ReformLab is designed for desktop use..."
- **Must be removed** for mobile viability — this banner blocks the entire AC-1 goal

**Three-Panel Resizable Layout**
- `WorkspaceLayout.tsx` uses ResizablePanelGroup with fixed percentage sizes
- Left panel: 22% (18-30%), Main: 56% (40-100%), Right: 22% (18-35%)
- ResizableHandle requires pointer events — may need to be hidden on touch devices

**Current Responsive Behavior**
- `TopBar.tsx` has some responsive handling: `hidden md:flex` for docs/GitHub/settings icons
- `PoliciesStageScreen.tsx` uses `grid-cols-1 lg:grid-cols-2` (stacks at mobile)
- `PopulationLibraryScreen.tsx` uses `grid-cols-2 gap-4 xl:grid-cols-3` — NOT mobile-friendly (2 cols at 375px)
- `EngineStageScreen.tsx` has fixed `w-80` right panel — will overflow at mobile widths

**Left/Right Panel Collapse Logic**
- `App.tsx` sets `isNarrow = width < 1024` and forces panel collapse
- At mobile, both panels collapse to 3px width with vertical text "RL" / "Help"
- This is NOT usable — need full hiding + compact stage switcher instead

### Architecture Constraints

From `project-context.md`:
- **Tailwind v4**: Use utility classes; mobile-first responsive design with `sm:`, `md:`, `lg:`, `xl:` breakpoints
- **React 19**: ref as regular prop (no forwardRef)
- **Shadcn/ui components**: Sheet (mobile drawer), Tabs, ScrollArea available for mobile patterns
- **No Dialog/DialogContent**: Use inline fixed-overlay pattern or Sheet for mobile

### Responsive Breakpoints (Tailwind v4 default)

```
sm:  640px   (landscape phones, small tablets)
md:  768px   (tablets)
lg:  1024px  (small laptops, large tablets)
xl:  1280px  (desktops, laptops)
2xl: 1536px  (large desktops)
```

### Mobile-First Implementation Strategy

**Layout Pattern:**
- Mobile (< 768px): Single column, no resizable panels, compact stage switcher
- Tablet (768-1023px): Transition zone — may keep panels but collapse by default
- Desktop (1024+): Existing three-panel resizable layout

**Stage Switcher Pattern:**
```tsx
// Desktop: WorkflowNavRail in left panel
// Mobile: Horizontal tabs above main content
<div className="flex lg:hidden items-center gap-2 overflow-x-auto px-4 py-2 border-b">
  {STAGES.map(stage => (
    <button key={stage.key} onClick={() => navigateTo(stage.key)}
      className={cn("flex-shrink-0 px-3 py-1 text-sm rounded-full",
        activeStage === stage.key ? "bg-blue-500 text-white" : "bg-slate-100 text-slate-600")}>
      {stage.label}
    </button>
  ))}
</div>
```

**WorkspaceLayout Conditional Rendering:**
```tsx
// Desktop: ResizablePanelGroup with three panels
// Mobile: TopBar + StageSwitcher + MainContent (no left/right panels)
<div className="flex lg:hidden flex-col h-full">
  {topBar}
  {mobileStageSwitcher}
  <main className="flex-1 overflow-auto">{mainPanel}</main>
</div>
```

### Scope Boundaries

**IN SCOPE:**
- Remove desktop-only warning banner
- Mobile stage switcher at narrow widths
- Vertical stacking of split layouts on mobile
- TopBar remains usable at 375px
- No horizontal overflow at phone width
- Desktop layouts unchanged above 1024px

**OUT OF SCOPE:**
- Full mobile-first redesign of results analytics
- Touch gesture optimization (pinch-zoom, swipe-to-nav)
- Offline mobile support
- Progressive Web App (PWA) features
- Mobile-specific result chart interactions
- Bottom navigation bar pattern (use compact tabs instead)

### Testing Strategy

**Viewport Tests (Vitest + Testing Library):**
```tsx
// Mock window.innerWidth for responsive testing
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 375,
});
window.dispatchEvent(new Event('resize'));

// Assert no horizontal overflow
expect(document.body).not.toHaveStyle({ overflowX: 'auto' });
```

**CSS Class Assertions:**
Since jsdom doesn't render viewport-dependent styles, test via CSS class presence:
```tsx
// At mobile breakpoint
expect(container).toHaveClass('grid-cols-1');
// At desktop breakpoint
expect(container).toHaveClass('lg:grid-cols-2');
```

### Known Constraints and Gotchas

1. **ResizablePanelGroup assumes desktop** — The shadcn/ui ResizablePanel component uses pointer events and fixed percentages. At mobile widths, this component should be conditionally replaced with a simple flex column layout.

2. **Population library grid needs mobile breakpoint** — Current `grid-cols-2` will render two narrow columns at 375px. Add `grid-cols-1` for base (mobile) then `sm:grid-cols-2`.

3. **Fixed `w-80` right panel will overflow** — Use conditional width: `w-full lg:w-80` to allow full width at mobile.

4. **isNarrow state forces panel collapse** — The current `width < 1024` logic creates 3px panels. At mobile (< 768px), panels should be fully hidden, not collapsed.

5. **Window resize in tests** — jsdom doesn't trigger resize observers. Use `window.dispatchEvent(new Event('resize'))` and test CSS classes rather than computed styles.

6. **Story 22.4 Population sub-steps** — Population stage has Library/Build/Explorer sub-steps. Mobile stage switcher should show main stages only; sub-steps can use back navigation or inline tabs within the stage.

7. **Investment Decisions Wizard** — Story 22.6 wizard has 4 steps. Ensure step indicators don't overflow horizontally on mobile (stack vertically or use compact stepper).

8. **ScenarioEntryDialog** — Dialog is fixed overlay. At mobile, ensure it fits within viewport (max-height, overflow-y-auto) and doesn't get cut off.

### References

- **Epic 22 definition:** `_bmad-output/planning-artifacts/epics.md#Epic-22`
- **UX Revision 3 spec:** `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 9 (Mobile Demo Viability)
- **TopBar source:** `frontend/src/components/layout/TopBar.tsx`
- **WorkspaceLayout source:** `frontend/src/components/layout/WorkspaceLayout.tsx`
- **LeftPanel source:** `frontend/src/components/layout/LeftPanel.tsx`
- **RightPanel source:** `frontend/src/components/layout/RightPanel.tsx`
- **WorkflowNavRail source:** `frontend/src/components/layout/WorkflowNavRail.tsx`
- **PoliciesStageScreen source:** `frontend/src/components/screens/PoliciesStageScreen.tsx`
- **PopulationLibraryScreen source:** `frontend/src/components/screens/PopulationLibraryScreen.tsx`
- **EngineStageScreen source:** `frontend/src/components/screens/EngineStageScreen.tsx`
- **App source:** `frontend/src/App.tsx`
- **Story 22.1:** `_bmad-output/implementation-artifacts/22-1-shell-branding-external-links-scenario-entry-relocation.md`
- **Story 22.2:** `_bmad-output/implementation-artifacts/22-2-policies-stage-layout-rebalance-denser-parameter-typography.md`
- **Story 22.4:** `_bmad-output/implementation-artifacts/22-4-population-sub-steps-and-quick-test-population.md`
- **Story 22.5:** `_bmad-output/implementation-artifacts/22-5-user-facing-engine-to-scenario-rename-across-shell-and-stage-copy.md`
- **Story 22.6:** `_bmad-output/implementation-artifacts/22-6-guided-investment-decision-wizard-inside-the-scenario-stage.md`

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Debug Log References

Analysis completed from source files:
- `frontend/src/App.tsx` — Desktop-only warning banner, isNarrow state logic, panel collapse behavior
- `frontend/src/components/layout/TopBar.tsx` — Current responsive handling, utility icons
- `frontend/src/components/layout/WorkspaceLayout.tsx` — ResizablePanelGroup three-panel layout
- `frontend/src/components/layout/LeftPanel.tsx` — Collapse variant with vertical "RL" text
- `frontend/src/components/layout/RightPanel.tsx` — Collapse variant with vertical "Help" text
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Desktop nav rail with Population sub-steps
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Two-column grid with lg: breakpoint
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — Multi-column grid without mobile breakpoint
- `frontend/src/components/screens/EngineStageScreen.tsx` — Fixed w-80 right panel
- `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 9 specification

### Completion Notes List

- Story 22.7 targets mobile demo viability — NOT full mobile parity
- Key blocker: Desktop-only warning banner in App.tsx must be removed
- WorkspaceLayout needs conditional rendering: ResizablePanelGroup (desktop) vs simple flex column (mobile)
- Mobile stage switcher needed: Horizontal tabs replacing left nav rail at narrow widths
- Population library grid needs mobile-first breakpoint: `grid-cols-1 sm:grid-cols-2...`
- EngineStageScreen right panel needs conditional width: `w-full lg:w-80`
- Tests should assert CSS classes for responsive behavior, not computed styles (jsdom limitation)
- Desktop layouts must remain intact above 1024px breakpoint
- **Story created:** 2026-03-30
- **Epic:** 22 (UX Revision 3 Workspace Fit and Mobile Demo Viability)

### File List

**Files to be modified:**
- `frontend/src/App.tsx` — Remove warning banner, update isNarrow logic
- `frontend/src/components/layout/WorkspaceLayout.tsx` — Add mobile conditional rendering
- `frontend/src/components/layout/LeftPanel.tsx` — Mobile hide behavior
- `frontend/src/components/layout/RightPanel.tsx` — Mobile hide behavior
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — Add mobile grid breakpoint
- `frontend/src/components/screens/EngineStageScreen.tsx` — Conditional right panel width

**Files potentially created:**
- `frontend/src/components/layout/MobileStageSwitcher.tsx` — Horizontal tabs for narrow screens
- `frontend/src/components/layout/__tests__/MobileStageSwitcher.test.tsx` — Tests
- `frontend/src/components/layout/__tests__/WorkspaceLayout.test.tsx` — Responsive tests

**Files to review but likely unchanged:**
- `frontend/src/components/layout/TopBar.tsx` — Already has `hidden md:flex` for utilities
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Desktop-only, hidden via WorkspaceLayout
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Already has `lg:` breakpoint
- `frontend/index.html` — Already has correct viewport meta
- `frontend/src/index.css` — Already has box-sizing and width rules

---
**Story Status:** ready-for-dev
**Created:** 2026-03-30

---
