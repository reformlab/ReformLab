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
              formatter={(value: number) => [value.toLocaleString(), valueLabel]}
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
