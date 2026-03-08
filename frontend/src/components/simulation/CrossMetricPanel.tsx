/** Cross-comparison metric ranking panel — Story 17.4, AC-5. */

import type { CrossMetricItem } from "@/api/types";

/** Human-readable labels for cross-metric criterion keys. */
const CRITERION_LABELS: Record<string, string> = {
  max_fiscal_revenue: "Max Fiscal Revenue",
  min_fiscal_cost: "Min Fiscal Cost",
  max_fiscal_balance: "Max Fiscal Balance",
  max_mean_welfare_net_change: "Max Welfare Net Change",
  max_total_winners: "Most Winners",
  min_total_losers: "Fewest Losers",
};

function formatValue(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(v / 1e3).toFixed(1)}k`;
  return v.toFixed(0);
}

interface CrossMetricCardProps {
  metric: CrossMetricItem;
}

function CrossMetricCard({ metric }: CrossMetricCardProps) {
  const label = CRITERION_LABELS[metric.criterion] ?? metric.criterion;
  // min_* criteria rank ascending (lower = better); max_* rank descending
  const isMin = metric.criterion.startsWith("min_");
  const allEntries = Object.entries(metric.all_values).sort(
    ([, a], [, b]) => isMin ? a - b : b - a,
  );

  return (
    <div className="border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-slate-900">
        {metric.best_portfolio}
      </p>
      <p className="data-mono text-sm text-slate-700">{formatValue(metric.value)}</p>
      {allEntries.length > 1 ? (
        <div className="mt-2 space-y-0.5">
          {allEntries.map(([portfolio, value]) => (
            <div key={portfolio} className="flex justify-between text-xs">
              <span
                className={
                  portfolio === metric.best_portfolio
                    ? "font-medium text-slate-800"
                    : "text-slate-500"
                }
              >
                {portfolio}
              </span>
              <span
                className={
                  portfolio === metric.best_portfolio
                    ? "font-medium text-slate-800"
                    : "text-slate-500"
                }
              >
                {formatValue(value)}
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

interface CrossMetricPanelProps {
  metrics: CrossMetricItem[];
}

/** Horizontal grid of KPI cards showing portfolio rankings per criterion. */
export function CrossMetricPanel({ metrics }: CrossMetricPanelProps) {
  if (metrics.length === 0) return null;

  return (
    <div>
      <p className="mb-2 text-sm font-semibold text-slate-800">
        Cross-Portfolio Rankings
      </p>
      <div className="grid grid-cols-2 gap-2 xl:grid-cols-3">
        {metrics.map((metric) => (
          <CrossMetricCard key={metric.criterion} metric={metric} />
        ))}
      </div>
    </div>
  );
}
