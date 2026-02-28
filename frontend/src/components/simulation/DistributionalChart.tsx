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
    <div className="h-72 border border-slate-200 bg-white p-3">
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
