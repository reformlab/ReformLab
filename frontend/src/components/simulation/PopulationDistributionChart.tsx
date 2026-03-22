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
