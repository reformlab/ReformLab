# Story 18.8: Chart Polish and Color Palette Refinement

Status: draft

## Story

As a policy analyst reviewing simulation results,
I want charts to have clear titles, labeled axes with units, subtle animations, and a warmer overall color palette,
so that visualizations are immediately interpretable and the application feels less austere during long analysis sessions.

## Acceptance Criteria

1. **AC-1: Chart titles** — Given every chart component (DistributionalChart, MultiRunChart, TransitionChart, PopulationDistributionChart, YearDetailPanel chart), when rendered, then a clear title is displayed above the chart area (not inside Recharts). Titles use `text-sm font-semibold text-slate-900` and describe the data shown (e.g., "Income Distribution by Decile", "Policy Impact Comparison", "Technology Transition Rates").

2. **AC-2: Axis labels with units** — Given chart Y-axes, when rendered, then they include unit annotations. Distributional charts: "EUR/year"; fiscal charts: "EUR (millions)"; transition charts: "Share (%)"; welfare charts: units appropriate to the metric. X-axes include labels where not obvious (e.g., "Income Decile", "Year", "Run").

3. **AC-3: Entry animations** — Given any chart rendering for the first time or receiving new data, when the chart appears, then bars/areas animate in over 300ms (`animationDuration={300}`). This applies to DistributionalChart, MultiRunChart, and TransitionChart.

4. **AC-4: Warmer neutral palette** — Given the application's neutral color scheme, when the base grays are updated, then `slate` references in non-semantic positions (backgrounds, borders, muted text) are shifted to `stone` for a warmer tone. Semantic colors (error=red, success=emerald, active=blue) remain unchanged. Specifically:
   - Body background gradient: shift from `#f8fafc → #eef2ff` to `#fafaf9 → #f5f0ff` (stone-50 → violet-50)
   - Panel backgrounds: `bg-white` stays, but border color shifts from `slate-200` to `stone-200`
   - Muted text: `text-slate-500` → `text-stone-500`
   - Section headers: `text-slate-500` → `text-stone-500`

5. **AC-5: Chart container cleanup** — Given chart container divs, when rendered, then they have no visible border (remove `border border-slate-200` from chart wrappers). Charts sit in Cards or panels that already provide the border — double-bordering creates visual noise.

6. **AC-6: Tooltip refinement** — Given chart tooltips, when a user hovers over a data point, then tooltips use `rounded-lg shadow-md` styling with a white background and subtle border, matching the app's visual polish from story 18.2.

## Tasks / Subtasks

- [ ] Task 1: Add chart titles and axis labels
  - [ ] 1.1: Update `DistributionalChart.tsx` — add title prop, render as `<h3>` above `ResponsiveContainer`, add YAxis label "EUR/year", XAxis label "Income Decile"
  - [ ] 1.2: Update `MultiRunChart.tsx` — add title prop, add YAxis label based on indicator type
  - [ ] 1.3: Update `TransitionChart.tsx` — add title "Technology Transition Rates", YAxis label "Share (%)", XAxis label "Year"
  - [ ] 1.4: Update `PopulationDistributionChart.tsx` — add title based on variable name
  - [ ] 1.5: Update `YearDetailPanel.tsx` chart section — add title "Outcome Probabilities"

- [ ] Task 2: Add animations
  - [ ] 2.1: Add `animationDuration={300}` to Bar/Area/Line components in all chart files
  - [ ] 2.2: Add `animationEasing="ease-out"` for smoother entry

- [ ] Task 3: Color palette shift
  - [ ] 3.1: Update `index.css` body background gradient to warmer tones
  - [ ] 3.2: Global search-replace `border-slate-200` → `border-stone-200` in component files (careful: only non-semantic uses)
  - [ ] 3.3: Global search-replace `text-slate-500` → `text-stone-500` for muted text
  - [ ] 3.4: Update `text-slate-600` → `text-stone-600` for secondary text
  - [ ] 3.5: Keep `slate` for chart baseline color (`--chart-baseline`) and any semantic uses
  - [ ] 3.6: Update CSS custom properties in `index.css` if needed

- [ ] Task 4: Chart container and tooltip cleanup
  - [ ] 4.1: Remove double-border patterns where charts are already inside Cards
  - [ ] 4.2: Update Recharts Tooltip `contentStyle` to use `borderRadius: 8, boxShadow: ...` matching app design
  - [ ] 4.3: Ensure tooltip text uses `font-size: 12px` consistently

- [ ] Task 5: Tests
  - [ ] 5.1: Update chart component tests to verify title rendering
  - [ ] 5.2: Verify no color-related test assertions break from palette shift
  - [ ] 5.3: Visual check all charts at standard viewport widths
  - [ ] 5.4: Run full test suite — zero regressions

## Dev Notes

- The slate → stone shift is subtle (stone is slightly warmer/brownish vs slate's blue-gray). At 200/500/600 levels the difference is visible but not jarring. Preview the change on a few screens before committing to the full replacement
- Chart titles should be props with sensible defaults, not hardcoded — some charts are reused in different contexts
- The `animationDuration` on Recharts components defaults to 1500ms which is too slow — 300ms feels snappy without being abrupt
- For axis labels, Recharts `Label` component inside `<YAxis>` / `<XAxis>` with `position="insideLeft"` / `position="insideBottom"` works well
- The double-border issue: many charts render inside `div className="border border-slate-200 bg-white p-3"` AND are themselves inside a Card. Only one border layer should exist
