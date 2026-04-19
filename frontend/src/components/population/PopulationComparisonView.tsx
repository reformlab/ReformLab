// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationComparisonView — displays side-by-side comparison of observed and synthetic populations.
 *
 * Story 21.4 / AC8: Comparison view shows metrics with diff highlighting and trust badges.
 */

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { TrustStatusBadge } from "@/components/population/TrustStatusBadge";
import { SyntheticBadge } from "@/components/population/SyntheticBadge";
import { ErrorAlert, type ErrorState } from "@/components/simulation/ErrorAlert";
import { comparePopulations } from "@/api/populations";
import type { PopulationComparisonResponse, NumericColumnComparison } from "@/api/types";

export interface PopulationComparisonViewProps {
  observedId: string;
  syntheticId: string;
  onBack: () => void;
}

// Helper: extract detail from ApiError or raw thrown object
function extractErrorDetail(err: unknown): ErrorState | null {
  if (err == null || typeof err !== "object") return null;
  const e = err as Record<string, unknown>;
  if (typeof e["what"] === "string") {
    return {
      what: String(e["what"]),
      why: String(e["why"] ?? ""),
      fix: String(e["fix"] ?? ""),
    };
  }
  return null;
}

// Diff highlighting utilities
function getDiffColor(relativeDiffPct: number): string {
  const absDiff = Math.abs(relativeDiffPct);
  if (absDiff < 5) return "text-green-700 bg-green-50";
  if (absDiff < 20) return "text-yellow-700 bg-yellow-50";
  return "text-red-700 bg-red-50";
}

function formatDiffValue(relativeDiffPct: number): string {
  const sign = relativeDiffPct >= 0 ? "+" : "";
  return `${sign}${relativeDiffPct.toFixed(1)}%`;
}

export function PopulationComparisonView({
  observedId,
  syntheticId,
  onBack,
}: PopulationComparisonViewProps) {
  const [comparison, setComparison] = useState<PopulationComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ErrorState | null>(null);

  const loadComparison = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await comparePopulations(observedId, syntheticId);
      setComparison(data);
    } catch (err: unknown) {
      const detail = extractErrorDetail(err);
      setError(
        detail ?? {
          what: "Failed to load comparison",
          why: "The server returned an unexpected error.",
          fix: "Try again or contact support if the problem persists.",
        },
      );
    } finally {
      setLoading(false);
    }
  }, [observedId, syntheticId]);

  useEffect(() => {
    loadComparison();
  }, [loadComparison]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading comparison data…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col p-6">
        <div className="mb-4 flex items-center gap-3">
          <Button size="sm" variant="ghost" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-md">
            <ErrorAlert {...error} />
            <Button size="sm" variant="outline" className="mt-4" onClick={loadComparison}>
              <RefreshCw className="mr-1 h-3.5 w-3.5" />
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!comparison) {
    return null;
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-6 py-3">
        <Button size="sm" variant="ghost" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-base font-semibold text-slate-900">Population Comparison</h1>
        <div className="flex-1" />
        <div className="flex gap-4 text-xs">
          {/* Observed population header */}
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-700">
              Observed: {comparison.observed_asset_id}
            </span>
            <TrustStatusBadge
              trustStatus={comparison.trust_labels.observed.trust_status as "production-safe" | "exploratory" | "demo-only" | "validation-pending" | "not-for-public-inference"}
            />
            <SyntheticBadge
              canonicalOrigin={comparison.trust_labels.observed.origin as "open-official" | "synthetic-public" | "open-registered"}
              isSynthetic={false}
            />
          </div>
          {/* Synthetic population header */}
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-700">
              Synthetic: {comparison.synthetic_asset_id}
            </span>
            <TrustStatusBadge
              trustStatus={comparison.trust_labels.synthetic.trust_status as "production-safe" | "exploratory" | "demo-only" | "validation-pending" | "not-for-public-inference"}
            />
            <SyntheticBadge
              canonicalOrigin={comparison.trust_labels.synthetic.origin as "open-official" | "synthetic-public" | "open-registered"}
              isSynthetic={true}
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          {/* Overview cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-700">Row Counts</h3>
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-500">Observed</div>
                <div className="text-sm font-medium text-slate-900">
                  {comparison.row_counts.observed.toLocaleString()}
                </div>
              </div>
              <Separator className="my-2" />
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-500">Synthetic</div>
                <div className="text-sm font-medium text-slate-900">
                  {comparison.row_counts.synthetic.toLocaleString()}
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-700">Column Counts</h3>
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-500">Observed</div>
                <div className="text-sm font-medium text-slate-900">
                  {comparison.column_counts.observed}
                </div>
              </div>
              <Separator className="my-2" />
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-500">Synthetic</div>
                <div className="text-sm font-medium text-slate-900">
                  {comparison.column_counts.synthetic}
                </div>
              </div>
            </div>
          </div>

          {/* Common numeric columns */}
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">
              Common Numeric Columns ({comparison.common_numeric_columns.length})
            </h3>
            {comparison.common_numeric_columns.length === 0 ? (
              <p className="text-xs text-slate-500">No common numeric columns found.</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {comparison.common_numeric_columns.map((col) => (
                  <span
                    key={col}
                    className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700"
                  >
                    {col}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Numeric column comparisons */}
          {Object.entries(comparison.numeric_comparison).length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="mb-4 text-sm font-semibold text-slate-700">
                Distributional Comparison
              </h3>
              <div className="space-y-4">
                {Object.entries(comparison.numeric_comparison).map(
                  ([colName, colData]: [string, NumericColumnComparison]) => (
                    <div key={colName} className="rounded-md border border-slate-100 p-3">
                      <div className="mb-2 flex items-center justify-between">
                        <h4 className="text-sm font-medium text-slate-900">{colName}</h4>
                        <span
                          className={`rounded px-2 py-0.5 text-xs font-medium ${getDiffColor(
                            colData.relative_diff_pct,
                          )}`}
                        >
                          {formatDiffValue(colData.relative_diff_pct)}
                        </span>
                      </div>

                      {/* Statistics table */}
                      <div className="grid grid-cols-4 gap-2 text-xs">
                        <div>
                          <div className="text-slate-500">Obs Mean</div>
                          <div className="font-medium text-slate-900">
                            {colData.observed_mean.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Syn Mean</div>
                          <div className="font-medium text-slate-900">
                            {colData.synthetic_mean.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Obs Median</div>
                          <div className="font-medium text-slate-900">
                            {colData.observed_median.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Syn Median</div>
                          <div className="font-medium text-slate-900">
                            {colData.synthetic_median.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Obs Std</div>
                          <div className="font-medium text-slate-900">
                            {colData.observed_std.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Syn Std</div>
                          <div className="font-medium text-slate-900">
                            {colData.synthetic_std.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Obs P10</div>
                          <div className="font-medium text-slate-900">
                            {colData.observed_p10.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Syn P10</div>
                          <div className="font-medium text-slate-900">
                            {colData.synthetic_p10.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Obs P50</div>
                          <div className="font-medium text-slate-900">
                            {colData.observed_p50.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Syn P50</div>
                          <div className="font-medium text-slate-900">
                            {colData.synthetic_p50.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Obs P90</div>
                          <div className="font-medium text-slate-900">
                            {colData.observed_p90.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500">Syn P90</div>
                          <div className="font-medium text-slate-900">
                            {colData.synthetic_p90.toFixed(2)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
