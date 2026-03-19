/** Multi-series grouped bar chart for portfolio comparison — Story 17.4, AC-2. */

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

export interface SeriesSpec {
  /** Column key in the data array. */
  key: string;
  /** Human-readable label for legend and tooltip. */
  label: string;
  /** Optional CSS color override. Defaults to CHART_COLORS[index]. */
  color?: string;
}

// Sign-based colors for relative mode bars
const RELATIVE_POS_COLOR = "#10b981"; // emerald-500
const RELATIVE_NEG_COLOR = "#ef4444"; // red-500
const RELATIVE_ZERO_COLOR = "#94a3b8"; // slate-400

interface MultiRunChartProps {
  /** Row-oriented data array. Each row has xKey plus one entry per series key. */
  data: Record<string, unknown>[];
  /** The column to use as the X-axis (e.g. "decile"). */
  xKey: string;
  /** Series definitions — up to 5. */
  series: SeriesSpec[];
  /** Absolute shows raw values; relative shows deltas with positive=emerald, negative=red. */
  mode?: "absolute" | "relative";
  /** Chart title shown above the chart. */
  title?: string;
  /** Whether to show the companion data table beneath the chart. */
  showTable?: boolean;
  /** Called when a bar group is clicked; receives the row data for the clicked group. */
  onBarClick?: (row: Record<string, unknown>) => void;
}

/** Columnar dict from API to row-oriented array for Recharts. */
export function columnarToRows(
  data: Record<string, unknown[]>,
): Record<string, unknown>[] {
  const keys = Object.keys(data);
  if (keys.length === 0) return [];
  const rowCount = data[keys[0]]?.length ?? 0;
  return Array.from({ length: rowCount }, (_, i) =>
    Object.fromEntries(keys.map((k) => [k, data[k]?.[i]])),
  );
}

/**
 * Format a large number for compact display in tooltips/tables.
 * E.g. 2_100_000_000 → "2.1B"
 */
function formatValue(v: unknown): string {
  if (typeof v !== "number") return String(v ?? "");
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(v / 1e3).toFixed(1)}k`;
  return v.toFixed(0);
}

export function MultiRunChart({
  data,
  xKey,
  series,
  mode = "absolute",
  title,
  showTable = true,
  onBarClick,
}: MultiRunChartProps) {
  // In relative mode, use delta_<key> columns instead of raw series columns
  const activeSeries =
    mode === "relative"
      ? series
          .slice(1) // skip baseline — it's all zeros
          .map((s) => ({ ...s, key: `delta_${s.key}` }))
      : series;

  return (
    <div className="space-y-2">
      {title ? (
        <p className="text-sm font-semibold text-slate-800">{title}</p>
      ) : null}

      <div className="h-[280px] border border-slate-200 bg-white p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ bottom: 5 }}>
            <CartesianGrid strokeDasharray="2 2" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} tickFormatter={formatValue} />
            <Tooltip formatter={(value: unknown) => formatValue(value)} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 4 }} />
            {activeSeries.map((s, i) => {
              const baseColor = s.color ?? (CHART_COLORS[i] ?? CHART_COLORS[0]);
              return (
                <Bar
                  key={s.key}
                  dataKey={s.key}
                  fill={baseColor}
                  name={s.label}
                  onClick={
                    onBarClick
                      ? (barData: unknown) => {
                          if (
                            typeof barData === "object" &&
                            barData !== null &&
                            "payload" in barData
                          ) {
                            const payload = (
                              barData as { payload?: Record<string, unknown> }
                            ).payload;
                            if (payload) {
                              onBarClick(payload);
                            }
                          }
                        }
                      : undefined
                  }
                  style={onBarClick ? { cursor: "pointer" } : undefined}
                >
                  {mode === "relative"
                    ? data.map((row, rowIdx) => {
                        const val = row[s.key];
                        const numVal = typeof val === "number" ? val : 0;
                        const fill =
                          numVal > 0
                            ? RELATIVE_POS_COLOR
                            : numVal < 0
                              ? RELATIVE_NEG_COLOR
                              : RELATIVE_ZERO_COLOR;
                        return <Cell key={rowIdx} fill={fill} />;
                      })
                    : null}
                </Bar>
              );
            })}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {showTable && data.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-slate-200 text-xs">
            <thead>
              <tr className="bg-slate-50">
                <th className="border border-slate-200 px-2 py-1 text-left font-medium">
                  {xKey}
                </th>
                {activeSeries.map((s) => (
                  <th
                    key={s.key}
                    className="border border-slate-200 px-2 py-1 text-right font-medium"
                  >
                    {s.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr
                  key={idx}
                  className={idx % 2 === 0 ? "bg-white" : "bg-slate-50"}
                >
                  <td className="border border-slate-200 px-2 py-1">
                    {String(row[xKey] ?? "")}
                  </td>
                  {activeSeries.map((s) => {
                    const val = row[s.key];
                    const numVal = typeof val === "number" ? val : null;
                    const isNeg = numVal !== null && numVal < 0;
                    const isPos = numVal !== null && numVal > 0;
                    const cellClass =
                      mode === "relative"
                        ? isNeg
                          ? "text-red-600"
                          : isPos
                            ? "text-emerald-600"
                            : ""
                        : "";
                    return (
                      <td
                        key={s.key}
                        className={`border border-slate-200 px-2 py-1 text-right ${cellClass}`}
                      >
                        {formatValue(val)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
