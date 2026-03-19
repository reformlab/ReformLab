/**
 * YearDetailPanel — Expandable detail panel for a single decision year.
 *
 * Story 17.5: Build Behavioral Decision Viewer, AC-4
 *
 * Shows:
 *   (a) Horizontal bar chart of chosen alternative distribution for the year
 *   (b) Table of mean probabilities per alternative (or "not available" message)
 *   (c) Eligibility summary (n_total / n_eligible) when present
 *
 * Dismissable via Escape key or close button.
 */

import { useEffect } from "react";
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
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { YearlyOutcome, DomainSummary } from "@/api/types";
import { DECISION_COLORS } from "./TransitionChart";

// ============================================================================
// Types
// ============================================================================

export interface YearDetailPanelProps {
  year: number;
  outcome: YearlyOutcome;
  domain: DomainSummary;
  onClose: () => void;
}

// ============================================================================
// Component
// ============================================================================

export function YearDetailPanel({
  year,
  outcome,
  domain,
  onClose,
}: YearDetailPanelProps) {
  // Dismiss on Escape key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  // Build horizontal bar chart data (sorted by count descending)
  const barData = domain.alternative_ids.map((altId, i) => ({
    name: domain.alternative_labels[altId] ?? altId,
    count: outcome.counts[altId] ?? 0,
    pct: outcome.percentages[altId] ?? 0,
    color: DECISION_COLORS[i % DECISION_COLORS.length],
  }));

  return (
    <aside className="border-l border-slate-200 bg-white w-80 flex-shrink-0 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
        <h3 className="text-sm font-semibold text-slate-800">
          Year {year} — Decision Detail
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label="Close year detail panel"
          className="h-6 w-6 p-0"
        >
          <X size={14} />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5">
        {/* (a) Horizontal bar chart — chosen distribution */}
        <section>
          <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
            Choice Distribution
          </h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={barData}
                layout="vertical"
                margin={{ top: 0, right: 8, bottom: 0, left: 0 }}
              >
                <CartesianGrid horizontal={false} strokeDasharray="2 2" stroke="#e2e8f0" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={80}
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  formatter={(value: number | string | undefined, _name, props) => {
                    const percent =
                      typeof props === "object" &&
                      props !== null &&
                      "payload" in props &&
                      typeof props.payload === "object" &&
                      props.payload !== null &&
                      "pct" in props.payload &&
                      typeof props.payload.pct === "number"
                        ? props.payload.pct
                        : 0;

                    return [
                      typeof value === "number"
                        ? `${value.toLocaleString()} (${percent.toFixed(1)}%)`
                        : String(value ?? ""),
                      "Count",
                    ];
                  }}
                  contentStyle={{ fontSize: 11, border: "1px solid #e2e8f0", borderRadius: 4 }}
                />
                <Bar dataKey="count" radius={[0, 3, 3, 0]}>
                  {barData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* (b) Mean probabilities table */}
        <section>
          <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
            Mean Choice Probabilities
          </h4>
          {outcome.mean_probabilities !== null ? (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-1 font-medium text-slate-500">
                    Alternative
                  </th>
                  <th className="text-right py-1 font-medium text-slate-500">
                    Probability
                  </th>
                </tr>
              </thead>
              <tbody>
                {domain.alternative_ids.map((altId) => (
                  <tr key={altId} className="border-b border-slate-100">
                    <td className="py-1 text-slate-700">
                      {domain.alternative_labels[altId] ?? altId}
                    </td>
                    <td className="text-right py-1 text-slate-600">
                      {((outcome.mean_probabilities?.[altId] ?? 0) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-slate-400 italic">
              Probability data not available
            </p>
          )}
        </section>

        {/* (c) Eligibility summary — only when eligibility is present */}
        {domain.eligibility !== null && (
          <section>
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
              Eligibility
            </h4>
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 bg-slate-50 rounded">
                <div className="text-sm font-semibold text-slate-700">
                  {domain.eligibility.n_total.toLocaleString()}
                </div>
                <div className="text-xs text-slate-400">Total</div>
              </div>
              <div className="text-center p-2 bg-emerald-50 rounded">
                <div className="text-sm font-semibold text-emerald-700">
                  {domain.eligibility.n_eligible.toLocaleString()}
                </div>
                <div className="text-xs text-slate-400">Eligible</div>
              </div>
              <div className="text-center p-2 bg-slate-50 rounded">
                <div className="text-sm font-semibold text-slate-500">
                  {domain.eligibility.n_ineligible.toLocaleString()}
                </div>
                <div className="text-xs text-slate-400">Ineligible</div>
              </div>
            </div>
          </section>
        )}
      </div>
    </aside>
  );
}
