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
