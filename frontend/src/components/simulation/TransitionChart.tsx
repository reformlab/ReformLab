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
          <AreaChart data={chartData} stackOffset="expand">
            <CartesianGrid strokeDasharray="2 2" stroke="#e2e8f0" />
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
            <Tooltip
              formatter={(value: number, name: string) => [
                `${(value * 100).toFixed(1)}%`,
                alternativeLabels[name] ?? name,
              ]}
              labelFormatter={(label: number) => `Year ${label}`}
              contentStyle={{
                fontSize: 12,
                border: "1px solid #e2e8f0",
                borderRadius: 6,
              }}
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
