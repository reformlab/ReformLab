// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * TransitionChart — Stacked area chart showing decision alternative composition over time.
 *
 * Story 17.5: Build Behavioral Decision Viewer, AC-2
 *
 * Renders a 100%-stacked area chart (Recharts AreaChart with stackOffset="expand")
 * where each band represents one decision alternative. A companion data table
 * shows exact counts and percentages per alternative per year.
 *
 * IMPORTANT: Pass raw `counts` (not percentages) as chart data.
 * With stackOffset="expand", Recharts normalizes to 100% automatically.
 * Using pre-computed percentages would cause double-normalization.
 */

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

// ============================================================================
// Types
// ============================================================================

export interface TransitionChartProps {
  data: YearlyOutcome[];
  alternativeIds: string[];
  alternativeLabels: Record<string, string>;
  /** Called when a year row is clicked (in chart or table). */
  onYearClick?: (year: number) => void;
}

// ============================================================================
// Helpers
// ============================================================================

/** Transform YearlyOutcome[] to Recharts chart data using raw counts. */
function toChartData(
  outcomes: YearlyOutcome[],
  alternativeIds: string[],
): Record<string, number>[] {
  return outcomes.map((o) => ({
    year: o.year,
    ...Object.fromEntries(alternativeIds.map((id) => [id, o.counts[id] ?? 0])),
  }));
}

// ============================================================================
// Component
// ============================================================================

export function TransitionChart({
  data,
  alternativeIds,
  alternativeLabels,
  onYearClick,
}: TransitionChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-slate-400 text-sm">
        No decision data available.
      </div>
    );
  }

  const chartData = toChartData(data, alternativeIds);

  return (
    <div className="space-y-4">
      {/* Stacked area chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            stackOffset="expand"
            onClick={(chartState) => {
              if (onYearClick && chartState?.activeLabel != null) {
                onYearClick(Number(chartState.activeLabel));
              }
            }}
            className={onYearClick ? "cursor-pointer" : ""}
          >
            <CartesianGrid {...GRID_PROPS} />
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
            <Tooltip
              formatter={(value: number | string | undefined, name: string | undefined) => [
                typeof value === "number" ? `${(value * 100).toFixed(1)}%` : String(value ?? ""),
                name ? (alternativeLabels[name] ?? name) : "",
              ]}
              labelFormatter={(label: unknown) => `Year ${String(label ?? "")}`}
              contentStyle={TOOLTIP_STYLE}
            />
            <Legend
              wrapperStyle={{ fontSize: 12, paddingTop: 4 }}
              formatter={(value: string) => alternativeLabels[value] ?? value}
            />
            {alternativeIds.map((altId, i) => (
              <Area
                key={altId}
                type="monotone"
                dataKey={altId}
                stackId="1"
                fill={DECISION_COLORS[i % DECISION_COLORS.length]}
                stroke={DECISION_COLORS[i % DECISION_COLORS.length]}
                name={altId}
                fillOpacity={0.85}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Companion data table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-1.5 px-2 font-medium text-slate-500">
                Year
              </th>
              {alternativeIds.map((altId) => (
                <th
                  key={altId}
                  className="text-right py-1.5 px-2 font-medium text-slate-500"
                >
                  {alternativeLabels[altId] ?? altId}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((outcome) => (
              <tr
                key={outcome.year}
                className={
                  "border-b border-slate-100 hover:bg-slate-50 transition-colors" +
                  (onYearClick ? " cursor-pointer" : "")
                }
                onClick={() => onYearClick?.(outcome.year)}
              >
                <td className="py-1.5 px-2 font-medium text-slate-700">
                  {outcome.year}
                </td>
                {alternativeIds.map((altId) => (
                  <td key={altId} className="text-right py-1.5 px-2 text-slate-600">
                    {(outcome.counts[altId] ?? 0).toLocaleString()}
                    <span className="ml-1 text-slate-400">
                      ({(outcome.percentages[altId] ?? 0).toFixed(1)}%)
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
