/** Shared chart color palette and styling constants.
 *
 * Story 18.8: Chart polish and color palette refinement.
 *
 * Centralizes all Recharts styling to ensure visual consistency across
 * DistributionalChart, MultiRunChart, TransitionChart,
 * PopulationDistributionChart, and YearDetailPanel.
 */

import { brand } from "@/lib/brand-tokens";

// ============================================================================
// Color palettes (CSS custom properties — defined in index.css :root)
// ============================================================================

/** Series colors for comparison charts (max 5 scenarios). */
export const CHART_COLORS = [
  "var(--chart-baseline)", // index 0 — baseline (slate-400)
  "var(--chart-reform-a)", // index 1 (blue-500)
  "var(--chart-reform-b)", // index 2 (violet-500)
  "var(--chart-reform-c)", // index 3 (emerald-500)
  "var(--chart-reform-d)", // index 4 (amber-500)
] as const;

/** Extended palette for decision/transition charts (6 colors). */
export const DECISION_COLORS = [
  "var(--chart-baseline)",  // slate-500  — keep_current (status quo)
  "var(--chart-reform-a)",  // blue-500
  "var(--chart-reform-b)",  // violet-500
  "var(--chart-reform-c)",  // emerald-500
  "var(--chart-reform-d)",  // amber-500
  "var(--chart-negative)",  // red-500
] as const;

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
  stroke: brand.slate200,
} as const;

/** Axis tick style — used as tick={AXIS_TICK} on XAxis and YAxis. */
export const AXIS_TICK = {
  fontSize: 12,
  fill: brand.slate500,
} as const;

/** Tooltip content style — used as contentStyle={TOOLTIP_STYLE}. */
export const TOOLTIP_STYLE = {
  fontSize: 12,
  border: `1px solid ${brand.slate200}`,
  borderRadius: 6,
} as const;
