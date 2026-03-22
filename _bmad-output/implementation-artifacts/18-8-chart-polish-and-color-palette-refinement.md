
# Story 18.8: Chart Polish and Color Palette Refinement

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst using the ReformLab workspace,
I want all charts to use a refined, consistent color palette and uniform styling,
so that the data visualizations feel cohesive and professional across every screen rather than appearing as independently styled components.

## Acceptance Criteria

1. **AC-1: Centralized chart color palette via CSS custom properties** — Given all chart components (`DistributionalChart`, `MultiRunChart`, `TransitionChart`, `PopulationDistributionChart`, `YearDetailPanel`), when rendered, then all chart colors (series, decision, semantic) reference CSS custom properties defined in `index.css :root`. No hardcoded hex color values remain in chart component source files. Three new CSS variables are added:
   - `--chart-positive: var(--color-emerald-500)` — positive delta values
   - `--chart-negative: var(--color-red-500)` — negative delta values
   - `--chart-neutral: var(--color-slate-400)` — zero/neutral values

2. **AC-2: Shared chart styling module** — Given a new `chart-theme.ts` module in `frontend/src/components/simulation/`, when chart components import styling constants, then all 5 chart components use identical:
   - Grid: `strokeDasharray="2 2"`, `stroke="#e2e8f0"` (slate-200)
   - Axis ticks: `fontSize: 12`, `fill: "#64748b"` (slate-500), `tickLine={false}`, `axisLine={false}`
   - Tooltip: `fontSize: 12`, `border: "1px solid #e2e8f0"`, `borderRadius: 6`

3. **AC-3: Chart containers render correctly in rounded parents** — Given `PopulationDistributionChart`, when rendered, then its container div has `rounded-lg` class (matching `DistributionalChart` and `MultiRunChart` containers which already have `rounded-lg`).

4. **AC-4: Single-color population distribution chart** — Given `PopulationDistributionChart`, when rendered, then all bars use a single consistent fill color `var(--chart-reform-a)` instead of per-bar dynamically-generated HSL colors. The `Cell` import from recharts is removed.

5. **AC-5: No regressions** — Given all changes, when tests run, then:
   - The full test suite passes (0 failures)
   - `npm run typecheck` reports 0 errors
   - `npm run lint` reports 0 errors (pre-existing fast-refresh warnings OK)

## Tasks / Subtasks

- [ ] Task 1: Add CSS custom properties to index.css (AC: 1)
  - [ ] 1.1: Add `--chart-positive`, `--chart-negative`, `--chart-neutral` to `:root` block in `frontend/src/index.css`

- [ ] Task 2: Create chart-theme.ts shared module (AC: 1, 2)
  - [ ] 2.1: Create `frontend/src/components/simulation/chart-theme.ts` with `CHART_COLORS`, `DECISION_COLORS`, `RELATIVE_COLORS`, `GRID_PROPS`, `AXIS_TICK`, `TOOLTIP_STYLE` exports (see Dev Notes for verbatim code)

- [ ] Task 3: Update DistributionalChart.tsx (AC: 2)
  - [ ] 3.1: Import `GRID_PROPS`, `AXIS_TICK`, `TOOLTIP_STYLE` from `./chart-theme`
  - [ ] 3.2: Replace inline `CartesianGrid` props with spread `{...GRID_PROPS}`
  - [ ] 3.3: Replace inline axis `tick` props with `AXIS_TICK`; add `tickLine={false} axisLine={false}` to both axes
  - [ ] 3.4: Add `contentStyle={TOOLTIP_STYLE}` to `<Tooltip />`

- [ ] Task 4: Update MultiRunChart.tsx (AC: 1, 2)
  - [ ] 4.1: Import `CHART_COLORS`, `RELATIVE_COLORS`, `GRID_PROPS`, `AXIS_TICK`, `TOOLTIP_STYLE` from `./chart-theme`; re-export `CHART_COLORS` for backward compatibility
  - [ ] 4.2: Remove local `CHART_COLORS` const (lines 16-22), `RELATIVE_POS_COLOR`, `RELATIVE_NEG_COLOR`, `RELATIVE_ZERO_COLOR` consts (lines 34-36)
  - [ ] 4.3: Update Cell fill logic in relative mode to use `RELATIVE_COLORS.positive`, `RELATIVE_COLORS.negative`, `RELATIVE_COLORS.zero`
  - [ ] 4.4: Replace inline `CartesianGrid` props with `{...GRID_PROPS}`
  - [ ] 4.5: Replace inline axis `tick` props with `AXIS_TICK`; add `tickLine={false} axisLine={false}` to both axes
  - [ ] 4.6: Add `contentStyle={TOOLTIP_STYLE}` to `<Tooltip>`

- [ ] Task 5: Update TransitionChart.tsx (AC: 1, 2)
  - [ ] 5.1: Import `DECISION_COLORS`, `GRID_PROPS`, `AXIS_TICK`, `TOOLTIP_STYLE` from `./chart-theme`; remove local `DECISION_COLORS` const (lines 32-39) and its section separator comments (lines 28-31)
  - [ ] 5.2: Replace inline `CartesianGrid` props with `{...GRID_PROPS}`
  - [ ] 5.3: Replace inline axis `tick` props with `AXIS_TICK` (keep `tickLine={false}` on XAxis; add `axisLine={false}` to XAxis; keep `tickLine={false} axisLine={false}` on YAxis)
  - [ ] 5.4: Replace inline tooltip `contentStyle` with `TOOLTIP_STYLE`

- [ ] Task 6: Update PopulationDistributionChart.tsx (AC: 2, 3, 4)
  - [ ] 6.1: Import `GRID_PROPS`, `AXIS_TICK`, `TOOLTIP_STYLE` from `./chart-theme`
  - [ ] 6.2: Remove `Cell` from recharts import
  - [ ] 6.3: Add `rounded-lg` to container div className
  - [ ] 6.4: Replace `<Bar>` element: remove `Cell` children and dynamic HSL fill; add `fill="var(--chart-reform-a)"` to `<Bar>` (self-closing)
  - [ ] 6.5: Change axis tick fontSize from 10 to 12 via `AXIS_TICK`; add `tickLine={false} axisLine={false}` to both axes
  - [ ] 6.6: Replace inline `CartesianGrid` props with `{...GRID_PROPS}`
  - [ ] 6.7: Replace inline tooltip `contentStyle` with `TOOLTIP_STYLE`; keep custom formatter

- [ ] Task 7: Update YearDetailPanel.tsx (AC: 1, 2)
  - [ ] 7.1: Change import source of `DECISION_COLORS` from `"./TransitionChart"` to `"./chart-theme"`; also import `GRID_PROPS`, `AXIS_TICK`, `TOOLTIP_STYLE`
  - [ ] 7.2: Replace inline `CartesianGrid` props with `horizontal={false} {...GRID_PROPS}`
  - [ ] 7.3: Replace inline XAxis/YAxis `tick` props (`fontSize: 11, fill: "#64748b"`) with `AXIS_TICK` (fontSize becomes 12)
  - [ ] 7.4: Replace inline tooltip `contentStyle` with `TOOLTIP_STYLE` (fontSize becomes 12, borderRadius becomes 6)

- [ ] Task 8: Verify no regressions (AC: 5)
  - [ ] 8.1: Run `npm test` — full test suite passes (0 failures)
  - [ ] 8.2: Run `npm run typecheck` — 0 errors
  - [ ] 8.3: Run `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)

## Dev Notes

### New CSS Custom Properties (`index.css`)

**Before (lines 14-20):**
```css
:root {
  --chart-baseline: var(--color-slate-500);
  --chart-reform-a: var(--color-blue-500);
  --chart-reform-b: var(--color-violet-500);
  --chart-reform-c: var(--color-emerald-500);
  --chart-reform-d: var(--color-amber-500);
}
```

**After:**
```css
:root {
  --chart-baseline: var(--color-slate-500);
  --chart-reform-a: var(--color-blue-500);
  --chart-reform-b: var(--color-violet-500);
  --chart-reform-c: var(--color-emerald-500);
  --chart-reform-d: var(--color-amber-500);
  --chart-positive: var(--color-emerald-500);
  --chart-negative: var(--color-red-500);
  --chart-neutral: var(--color-slate-400);
}
```

### chart-theme.ts (new file — copy verbatim)

```typescript
/** Shared chart color palette and styling constants.
 *
 * Story 18.8: Chart polish and color palette refinement.
 *
 * Centralizes all Recharts styling to ensure visual consistency across
 * DistributionalChart, MultiRunChart, TransitionChart,
 * PopulationDistributionChart, and YearDetailPanel.
 */

// ============================================================================
// Color palettes (CSS custom properties — defined in index.css :root)
// ============================================================================

/** Series colors for comparison charts (max 5 scenarios). */
export const CHART_COLORS = [
  "var(--chart-baseline)", // index 0 — baseline (slate-500)
  "var(--chart-reform-a)", // index 1 (blue-500)
  "var(--chart-reform-b)", // index 2 (violet-500)
  "var(--chart-reform-c)", // index 3 (emerald-500)
  "var(--chart-reform-d)", // index 4 (amber-500)
];

/** Extended palette for decision/transition charts (6 colors). */
export const DECISION_COLORS = [
  "var(--chart-baseline)",  // slate-500  — keep_current (status quo)
  "var(--chart-reform-a)",  // blue-500
  "var(--chart-reform-b)",  // violet-500
  "var(--chart-reform-c)",  // emerald-500
  "var(--chart-reform-d)",  // amber-500
  "var(--chart-negative)",  // red-500
];

/** Semantic colors for relative/delta mode bar fills. */
export const RELATIVE_COLORS = {
  positive: "var(--chart-positive)",
  negative: "var(--chart-negative)",
  zero: "var(--chart-neutral)",
} as const;

// ============================================================================
// Shared Recharts styling constants
// ============================================================================

/** CartesianGrid props — spread into <CartesianGrid {...GRID_PROPS} />. */
export const GRID_PROPS = {
  strokeDasharray: "2 2",
  stroke: "#e2e8f0",
} as const;

/** Axis tick style — used as tick={AXIS_TICK} on XAxis and YAxis. */
export const AXIS_TICK = {
  fontSize: 12,
  fill: "#64748b",
} as const;

/** Tooltip content style — used as contentStyle={TOOLTIP_STYLE}. */
export const TOOLTIP_STYLE = {
  fontSize: 12,
  border: "1px solid #e2e8f0",
  borderRadius: 6,
} as const;
```

### DistributionalChart.tsx Changes

**Before (full file):**
```tsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DecileData } from "@/data/mock-data";

interface DistributionalChartProps {
  data: DecileData[];
  reformLabel?: string;
}

export function DistributionalChart({ data, reformLabel = "Reform" }: DistributionalChartProps) {
  return (
    <div className="h-72 rounded-lg border border-slate-200 bg-white p-3">
      <p className="mb-2 text-sm font-semibold">Income Decile Impact (EUR/year)</p>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data} margin={{ bottom: 5 }}>
          <CartesianGrid strokeDasharray="2 2" />
          <XAxis dataKey="decile" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 4 }} />
          <Bar dataKey="baseline" fill="var(--chart-baseline)" name="Baseline" />
          <Bar dataKey="reform" fill="var(--chart-reform-a)" name={reformLabel} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

**After (full file):**
```tsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DecileData } from "@/data/mock-data";
import { GRID_PROPS, AXIS_TICK, TOOLTIP_STYLE } from "./chart-theme";

interface DistributionalChartProps {
  data: DecileData[];
  reformLabel?: string;
}

export function DistributionalChart({ data, reformLabel = "Reform" }: DistributionalChartProps) {
  return (
    <div className="h-72 rounded-lg border border-slate-200 bg-white p-3">
      <p className="mb-2 text-sm font-semibold">Income Decile Impact (EUR/year)</p>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data} margin={{ bottom: 5 }}>
          <CartesianGrid {...GRID_PROPS} />
          <XAxis dataKey="decile" tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 4 }} />
          <Bar dataKey="baseline" fill="var(--chart-baseline)" name="Baseline" />
          <Bar dataKey="reform" fill="var(--chart-reform-a)" name={reformLabel} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### MultiRunChart.tsx Changes

**Import section — before:**
```tsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/** CSS color variables for chart series (matches project UX spec). */
export const CHART_COLORS = [
  "var(--chart-baseline)",  // index 0 — baseline
  "var(--chart-reform-a)",  // index 1
  "var(--chart-reform-b)",  // index 2
  "var(--chart-reform-c)",  // index 3
  "var(--chart-reform-d)",  // index 4
];
```

**Import section — after:**
```tsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  CHART_COLORS,
  RELATIVE_COLORS,
  GRID_PROPS,
  AXIS_TICK,
  TOOLTIP_STYLE,
} from "./chart-theme";

export { CHART_COLORS };
```

**Remove local relative color constants (lines 33-36):**

Delete:
```tsx
// Sign-based colors for relative mode bars
const RELATIVE_POS_COLOR = "#10b981"; // emerald-500
const RELATIVE_NEG_COLOR = "#ef4444"; // red-500
const RELATIVE_ZERO_COLOR = "#94a3b8"; // slate-400
```

**Chart JSX — before:**
```tsx
          <CartesianGrid strokeDasharray="2 2" />
          <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} tickFormatter={formatValue} />
          <Tooltip formatter={(value: unknown) => formatValue(value)} />
```

**Chart JSX — after:**
```tsx
          <CartesianGrid {...GRID_PROPS} />
          <XAxis dataKey={xKey} tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} tickFormatter={formatValue} />
          <Tooltip formatter={(value: unknown) => formatValue(value)} contentStyle={TOOLTIP_STYLE} />
```

**Relative mode cell fill — before:**
```tsx
                        const fill =
                          numVal > 0
                            ? RELATIVE_POS_COLOR
                            : numVal < 0
                              ? RELATIVE_NEG_COLOR
                              : RELATIVE_ZERO_COLOR;
```

**Relative mode cell fill — after:**
```tsx
                        const fill =
                          numVal > 0
                            ? RELATIVE_COLORS.positive
                            : numVal < 0
                              ? RELATIVE_COLORS.negative
                              : RELATIVE_COLORS.zero;
```

### TransitionChart.tsx Changes

**Import section — before:**
```tsx
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { YearlyOutcome } from "@/api/types";

// ============================================================================
// Decision color palette — distinct from comparison chart colors
// ============================================================================

export const DECISION_COLORS = [
  "#64748b", // slate-500  — keep_current (status quo / neutral)
  "#3b82f6", // blue-500
  "#8b5cf6", // violet-500
  "#10b981", // emerald-500
  "#f59e0b", // amber-500
  "#ef4444", // red-500
];
```

**Import section — after:**
```tsx
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { YearlyOutcome } from "@/api/types";
import { DECISION_COLORS, GRID_PROPS, AXIS_TICK, TOOLTIP_STYLE } from "./chart-theme";
```

**Grid — before:**
```tsx
            <CartesianGrid strokeDasharray="2 2" stroke="#e2e8f0" />
```

**Grid — after:**
```tsx
            <CartesianGrid {...GRID_PROPS} />
```

**Axes — before:**
```tsx
            <XAxis
              dataKey="year"
              tick={{ fontSize: 12, fill: "#64748b" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              tick={{ fontSize: 12, fill: "#64748b" }}
              tickLine={false}
              axisLine={false}
            />
```

**Axes — after:**
```tsx
            <XAxis
              dataKey="year"
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
            />
```

**Tooltip — before:**
```tsx
            <Tooltip
              formatter={(value: number | string | undefined, name: string | undefined) => [
                typeof value === "number" ? `${(value * 100).toFixed(1)}%` : String(value ?? ""),
                name ? (alternativeLabels[name] ?? name) : "",
              ]}
              labelFormatter={(label: unknown) => `Year ${String(label ?? "")}`}
              contentStyle={{
                fontSize: 12,
                border: "1px solid #e2e8f0",
                borderRadius: 6,
              }}
            />
```

**Tooltip — after:**
```tsx
            <Tooltip
              formatter={(value: number | string | undefined, name: string | undefined) => [
                typeof value === "number" ? `${(value * 100).toFixed(1)}%` : String(value ?? ""),
                name ? (alternativeLabels[name] ?? name) : "",
              ]}
              labelFormatter={(label: unknown) => `Year ${String(label ?? "")}`}
              contentStyle={TOOLTIP_STYLE}
            />
```

### PopulationDistributionChart.tsx Changes

**Before (full file):**
```tsx
/** Population distribution bar chart using Recharts (Story 17.1, AC-5). */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface DistributionDataPoint {
  name: string;
  value: number;
}

interface PopulationDistributionChartProps {
  title: string;
  data: DistributionDataPoint[];
  valueLabel?: string;
}

export function PopulationDistributionChart({
  title,
  data,
  valueLabel = "Count",
}: PopulationDistributionChartProps) {
  if (data.length === 0) return null;

  return (
    <div className="border border-slate-200 bg-white p-3">
      <p className="mb-2 text-xs font-semibold text-slate-700">{title}</p>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ bottom: 5, left: 0, right: 0, top: 5 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="#e2e8f0" />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(value: number | string | undefined) => [
                typeof value === "number" ? value.toLocaleString() : String(value ?? ""),
                valueLabel,
              ]}
            />
            <Bar dataKey="value" maxBarSize={40}>
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={`hsl(${220 + index * 15}, 60%, ${55 + (index % 3) * 5}%)`}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

**After (full file):**
```tsx
/** Population distribution bar chart using Recharts (Story 17.1, AC-5). */

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { GRID_PROPS, AXIS_TICK, TOOLTIP_STYLE } from "./chart-theme";

interface DistributionDataPoint {
  name: string;
  value: number;
}

interface PopulationDistributionChartProps {
  title: string;
  data: DistributionDataPoint[];
  valueLabel?: string;
}

export function PopulationDistributionChart({
  title,
  data,
  valueLabel = "Count",
}: PopulationDistributionChartProps) {
  if (data.length === 0) return null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="mb-2 text-xs font-semibold text-slate-700">{title}</p>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ bottom: 5, left: 0, right: 0, top: 5 }}>
            <CartesianGrid {...GRID_PROPS} />
            <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={false} />
            <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value: number | string | undefined) => [
                typeof value === "number" ? value.toLocaleString() : String(value ?? ""),
                valueLabel,
              ]}
            />
            <Bar dataKey="value" maxBarSize={40} fill="var(--chart-reform-a)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

**Key changes:**
- Removed `Cell` from recharts import
- Added `rounded-lg` to container div (AC-3)
- Changed `<Bar>` from having `Cell` children with HSL fills to self-closing with `fill="var(--chart-reform-a)"` (AC-4)
- Axis tick fontSize from 10 → 12 (via `AXIS_TICK`)
- Added `tickLine={false} axisLine={false}` to both axes
- Tooltip `contentStyle` from `{{ fontSize: 12 }}` → `TOOLTIP_STYLE` (adds border and borderRadius)

### YearDetailPanel.tsx Changes

**Import — before:**
```tsx
import { DECISION_COLORS } from "./TransitionChart";
```

**Import — after:**
```tsx
import { DECISION_COLORS, GRID_PROPS, AXIS_TICK, TOOLTIP_STYLE } from "./chart-theme";
```

**Grid — before:**
```tsx
                <CartesianGrid horizontal={false} strokeDasharray="2 2" stroke="#e2e8f0" />
```

**Grid — after:**
```tsx
                <CartesianGrid horizontal={false} {...GRID_PROPS} />
```

**XAxis — before:**
```tsx
                <XAxis
                  type="number"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={false}
                />
```

**XAxis — after:**
```tsx
                <XAxis
                  type="number"
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={false}
                />
```

**YAxis — before:**
```tsx
                <YAxis
                  dataKey="name"
                  type="category"
                  width={80}
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={false}
                />
```

**YAxis — after:**
```tsx
                <YAxis
                  dataKey="name"
                  type="category"
                  width={80}
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={false}
                />
```

**Tooltip — before:**
```tsx
                <Tooltip
                  formatter={(value: number | string | undefined, _name, props) => {
                    ...
                  }}
                  contentStyle={{ fontSize: 11, border: "1px solid #e2e8f0", borderRadius: 4 }}
                />
```

**Tooltip — after:**
```tsx
                <Tooltip
                  formatter={(value: number | string | undefined, _name, props) => {
                    ...
                  }}
                  contentStyle={TOOLTIP_STYLE}
                />
```

Note: fontSize changes from 11→12 and borderRadius from 4→6. Minor standardization.

### Backward Compatibility — Import Chain

The `CHART_COLORS` re-export from `MultiRunChart.tsx` (`export { CHART_COLORS }`) preserves backward compatibility for these consumers:
- `comparison-helpers.ts` line 6: `import { CHART_COLORS } from "@/components/simulation/MultiRunChart"` — **no change needed**
- `RunSelector.tsx` line 8: `import { CHART_COLORS } from "@/components/simulation/MultiRunChart"` — **no change needed**

The `DECISION_COLORS` export is removed from `TransitionChart.tsx`. Only one consumer imported it:
- `YearDetailPanel.tsx` line 29: `import { DECISION_COLORS } from "./TransitionChart"` — **updated to import from `./chart-theme`**

### What NOT to Change

- **MultiRunChart companion table** — Table cell text colors (`text-red-600`, `text-emerald-600`) use Tailwind classes, not CSS vars. These are correct for text coloring and should not change.
- **Legend styling** — All charts use `wrapperStyle={{ fontSize: 12, paddingTop: 4 }}`. This is already consistent across all charts. No change needed.
- **Chart heights and margins** — Each chart has context-appropriate heights (`h-72`, `h-[280px]`, `h-64`, `h-40`, `h-48`). Do not standardize these.
- **Chart-specific formatters** — Each tooltip/axis has domain-specific formatters (percentage, localized numbers, compact notation). These stay as-is.
- **TransitionChart `fillOpacity={0.85}`** — Area-specific opacity. Leave as-is.
- **YearDetailPanel `radius={[0, 3, 3, 0]}`** — Bar radius for horizontal bars. Already has the right styling.
- **Backend files** — Frontend-only story.
- **comparison-helpers.ts** — Re-exports from MultiRunChart; no changes needed since MultiRunChart still exports CHART_COLORS.
- **RunSelector.tsx** — Imports CHART_COLORS from MultiRunChart; no changes needed.
- **Any screen components** — No changes to files under `components/screens/`.
- **WelfareTab.tsx / FiscalTab.tsx / DetailPanel.tsx** — Comparison sub-components that use tables, not charts. No changes.
- **Body background, borders, text colors** — No global slate→stone shift. The story scope is chart components only.
- **Chart titles and axis labels** — No new titles or label annotations. Existing titles stay as-is.
- **Animations** — No animation changes. Recharts default animation behavior is preserved.

### Existing Tests That Cover Modified Files

| File | Test File | Risk |
|------|-----------|------|
| `DistributionalChart.tsx` | `__tests__/DistributionalChart.test.tsx` | Low — tests check title text and element presence, not styling props |
| `MultiRunChart.tsx` | `__tests__/MultiRunChart.test.tsx` | Low — tests check rendering, table content, and `columnarToRows()`. No color assertions |
| `TransitionChart.tsx` | `__tests__/TransitionChart.test.tsx` | Low — tests check chart rendering, year click, labels. No color assertions |
| `PopulationDistributionChart.tsx` | None | Zero risk — no existing tests |
| `YearDetailPanel.tsx` | None (tested indirectly via `BehavioralDecisionViewerScreen.test.tsx`) | Low — screen test checks year detail rendering, not chart props |

All existing tests verify behavioral output (text content, element presence, interactions), not visual styling. The changes in this story modify only styling props and color constants, so existing tests should pass without modification.

### ResizeObserver Mock Pattern (for reference)

All chart test files use this pattern:
```typescript
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});
```

### CSS Variables in SVG Context

CSS custom properties (`var(--chart-*)`) work in Recharts because Recharts renders inline SVG. The `fill` attribute on SVG elements accepts CSS custom property references in all modern browsers. The existing codebase already uses this pattern (`DistributionalChart.tsx` lines 30-31, `MultiRunChart.tsx` via `CHART_COLORS`). In jsdom (Vitest), CSS vars don't resolve to actual colors, but existing tests don't assert on rendered colors — they check element presence and text content.

### Project Structure Notes

**New files (1):**
- `frontend/src/components/simulation/chart-theme.ts`

**Modified files (6):**
- `frontend/src/index.css` — add 3 CSS custom properties
- `frontend/src/components/simulation/DistributionalChart.tsx` — import chart-theme; apply shared styling
- `frontend/src/components/simulation/MultiRunChart.tsx` — import chart-theme; remove local color consts; re-export CHART_COLORS
- `frontend/src/components/simulation/TransitionChart.tsx` — import chart-theme; remove local DECISION_COLORS
- `frontend/src/components/simulation/PopulationDistributionChart.tsx` — import chart-theme; remove Cell; add rounded-lg; single fill color
- `frontend/src/components/simulation/YearDetailPanel.tsx` — change import source; apply shared styling

### References

- [Source: `_bmad-output/planning-artifacts/epics.md:1804-1810` — Story 18.8 acceptance criteria]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:430-470` — Color system and chart palette specification]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:450-465` — Chart CSS custom property definitions]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:488-492` — Typography: chart axis labels at text-sm, chart titles at text-base]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:555` — Motion: chart transitions 150ms ease-out, respect prefers-reduced-motion]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:1347-1365` — Accessibility: color contrast 4.5:1, color not sole indicator]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md:1385` — Color blindness validation note]
- [Source: `frontend/src/index.css:14-20` — Current chart CSS custom properties]
- [Source: `frontend/src/components/simulation/DistributionalChart.tsx` — Current chart implementation]
- [Source: `frontend/src/components/simulation/MultiRunChart.tsx:16-36` — Current CHART_COLORS and RELATIVE_*_COLOR constants]
- [Source: `frontend/src/components/simulation/TransitionChart.tsx:32-39` — Current DECISION_COLORS hardcoded hex values]
- [Source: `frontend/src/components/simulation/PopulationDistributionChart.tsx:33,49-54` — Missing rounded-lg and dynamic HSL colors]
- [Source: `frontend/src/components/simulation/YearDetailPanel.tsx:29` — Current DECISION_COLORS import from TransitionChart]
- [Source: `frontend/src/components/comparison/comparison-helpers.ts:6` — CHART_COLORS import from MultiRunChart (backward compat)]
- [Source: `frontend/src/components/comparison/RunSelector.tsx:8` — CHART_COLORS import from MultiRunChart (backward compat)]

## Dev Agent Record

### Agent Model Used

<!-- filled by dev agent -->

### Debug Log References

### Completion Notes

### File List
