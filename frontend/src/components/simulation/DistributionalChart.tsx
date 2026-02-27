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
}

export function DistributionalChart({ data }: DistributionalChartProps) {
  return (
    <div className="h-72 border border-slate-200 bg-white p-3">
      <p className="mb-2 text-sm font-semibold">Income Decile Impact (EUR/year)</p>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="2 2" />
          <XAxis dataKey="decile" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="baseline" fill="var(--chart-baseline)" name="Baseline" />
          <Bar dataKey="reform" fill="var(--chart-reform-a)" name="Reform A" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
