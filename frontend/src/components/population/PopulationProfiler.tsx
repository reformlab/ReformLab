// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationProfiler — column profiler with histograms, value counts, and cross-tabs.
 *
 * Profile View tab within the Full Data Explorer.
 * Story 20.4 — AC-3(b).
 */

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { ColumnProfile, PopulationProfileResponse, PopulationCrosstabResponse } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface PopulationProfilerProps {
  profile: PopulationProfileResponse;
  crosstabData: PopulationCrosstabResponse | null;
  onCrosstabRequest: (colA: string, colB: string) => void;
}

// ============================================================================
// Stats card
// ============================================================================

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col rounded border border-slate-200 bg-slate-50 px-2 py-1.5">
      <span className="text-[10px] font-medium uppercase tracking-wide text-slate-400">{label}</span>
      <span className="text-xs font-semibold text-slate-800">{typeof value === "number" ? value.toLocaleString() : value}</span>
    </div>
  );
}

// ============================================================================
// Percentile bar
// ============================================================================

interface PercentileBarProps {
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
  min: number;
  max: number;
}

function PercentileBar({ p10, p25, p50, p75, p90, min, max }: PercentileBarProps) {
  const range = max - min || 1;
  const pct = (v: number) => `${((v - min) / range) * 100}%`;

  return (
    <div className="relative h-4 w-full rounded bg-slate-100">
      {/* IQR box */}
      <div
        className="absolute inset-y-0 rounded bg-blue-200"
        style={{ left: pct(p25), width: `calc(${pct(p75)} - ${pct(p25)})` }}
      />
      {/* Median line */}
      <div
        className="absolute inset-y-0 w-0.5 bg-blue-500"
        style={{ left: pct(p50) }}
      />
      {/* Whiskers */}
      <div className="absolute inset-y-[40%] w-px bg-slate-400" style={{ left: pct(p10) }} />
      <div className="absolute inset-y-[40%] w-px bg-slate-400" style={{ left: pct(p90) }} />
      {/* Labels */}
      <div className="absolute -bottom-4 flex w-full justify-between text-[10px] text-slate-400">
        <span style={{ marginLeft: pct(p10) }}>P10</span>
        <span style={{ marginLeft: pct(p50) }}>P50</span>
        <span>P90</span>
      </div>
    </div>
  );
}

// ============================================================================
// Numeric profile panel
// ============================================================================

function NumericProfile({
  name,
  profile,
  allColumnNames,
  onCrosstab,
}: {
  name: string;
  profile: Extract<ColumnProfile, { type: "numeric" }>;
  allColumnNames: string[];
  onCrosstab: (colB: string) => void;
}) {
  const [crosstabCol, setCrosstabCol] = useState("");

  const histData = profile.histogram_buckets.map((b) => ({
    bin: `${b.bin_start.toLocaleString()}`,
    count: b.count,
  }));

  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="mb-2 text-xs font-semibold text-slate-700">Distribution</p>
        <div aria-label={`Histogram for ${name}`}>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={histData} margin={{ top: 2, right: 4, bottom: 2, left: 4 }}>
            <XAxis dataKey="bin" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 9 }} width={40} />
            <Tooltip
              formatter={(v: number) => [v.toLocaleString(), "count"]}
              contentStyle={{ fontSize: 11 }}
            />
            <Bar dataKey="count" fill="#94a3b8" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        </div>
      </div>

      {/* Percentile bar */}
      <div className="mb-6">
        <p className="mb-2 text-xs font-semibold text-slate-700">Percentiles</p>
        <PercentileBar
          p10={profile.percentiles["p10"] ?? profile.min}
          p25={profile.percentiles["p25"] ?? profile.min}
          p50={profile.percentiles["p50"] ?? profile.mean}
          p75={profile.percentiles["p75"] ?? profile.max}
          p90={profile.percentiles["p90"] ?? profile.max}
          min={profile.min}
          max={profile.max}
        />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-1.5">
        <StatCard label="min" value={profile.min.toLocaleString()} />
        <StatCard label="max" value={profile.max.toLocaleString()} />
        <StatCard label="mean" value={Math.round(profile.mean).toLocaleString()} />
        <StatCard label="median" value={Math.round(profile.median).toLocaleString()} />
        <StatCard label="std" value={Math.round(profile.std).toLocaleString()} />
        <StatCard label="nulls" value={`${profile.null_pct.toFixed(1)}%`} />
      </div>

      {/* Cross-tab selector */}
      <div>
        <p className="mb-1.5 text-xs font-semibold text-slate-700">Cross-tabulate with</p>
        <select
          className="w-full rounded border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700"
          value={crosstabCol}
          onChange={(e) => {
            setCrosstabCol(e.target.value);
            if (e.target.value) onCrosstab(e.target.value);
          }}
          aria-label="Cross-tab column selector"
        >
          <option value="">Select column…</option>
          {allColumnNames.filter((c) => c !== name).map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

// ============================================================================
// Categorical profile panel
// ============================================================================

function CategoricalProfile({
  name,
  profile,
  allColumnNames,
  onCrosstab,
}: {
  name: string;
  profile: Extract<ColumnProfile, { type: "categorical" }>;
  allColumnNames: string[];
  onCrosstab: (colB: string) => void;
}) {
  const [crosstabCol, setCrosstabCol] = useState("");

  const topValues = profile.value_counts.slice(0, 20);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <p className="text-xs font-semibold text-slate-700">Value counts</p>
          <Badge variant="secondary" className="text-[10px]">
            {profile.cardinality.toLocaleString()} unique
          </Badge>
        </div>
        <div aria-label={`Value counts for ${name}`}>
        <ResponsiveContainer width="100%" height={Math.min(topValues.length * 22 + 20, 300)}>
          <BarChart
            data={topValues}
            layout="vertical"
            margin={{ top: 2, right: 40, bottom: 2, left: 4 }}
          >
            <XAxis type="number" tick={{ fontSize: 9 }} />
            <YAxis type="category" dataKey="value" tick={{ fontSize: 9 }} width={80} />
            <Tooltip
              formatter={(v: number) => [v.toLocaleString(), "count"]}
              contentStyle={{ fontSize: 11 }}
            />
            <Bar dataKey="count" fill="#94a3b8" radius={[0, 2, 2, 0]} />
          </BarChart>
        </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        <StatCard label="count" value={profile.count} />
        <StatCard label="nulls" value={`${profile.null_pct.toFixed(1)}%`} />
      </div>

      {/* Cross-tab selector */}
      <div>
        <p className="mb-1.5 text-xs font-semibold text-slate-700">Cross-tabulate with</p>
        <select
          className="w-full rounded border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700"
          value={crosstabCol}
          onChange={(e) => {
            setCrosstabCol(e.target.value);
            if (e.target.value) onCrosstab(e.target.value);
          }}
          aria-label="Cross-tab column selector"
        >
          <option value="">Select column…</option>
          {allColumnNames.filter((c) => c !== name).map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

// ============================================================================
// Boolean profile panel
// ============================================================================

function BooleanProfile({ profile }: { profile: Extract<ColumnProfile, { type: "boolean" }> }) {
  const trueRatio = profile.count > 0 ? profile.true_count / profile.count : 0;
  const falseRatio = 1 - trueRatio;

  return (
    <div className="flex flex-col gap-4">
      {/* Proportion bar */}
      <div>
        <p className="mb-2 text-xs font-semibold text-slate-700">Distribution</p>
        <div className="flex h-6 w-full overflow-hidden rounded">
          <div
            className="flex items-center justify-center bg-blue-500 text-[10px] font-medium text-white"
            style={{ width: `${trueRatio * 100}%` }}
          >
            {trueRatio > 0.1 ? `${(trueRatio * 100).toFixed(0)}%` : ""}
          </div>
          <div
            className="flex items-center justify-center bg-slate-300 text-[10px] font-medium text-slate-700"
            style={{ width: `${falseRatio * 100}%` }}
          >
            {falseRatio > 0.1 ? `${(falseRatio * 100).toFixed(0)}%` : ""}
          </div>
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-slate-400">
          <span>True ({profile.true_count.toLocaleString()})</span>
          <span>False ({profile.false_count.toLocaleString()})</span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        <StatCard label="count" value={profile.count} />
        <StatCard label="nulls" value={`${profile.null_pct.toFixed(1)}%`} />
      </div>
    </div>
  );
}

// ============================================================================
// Cross-tab chart
// ============================================================================

function CrosstabChart({
  data,
  colA,
  colB,
}: {
  data: Array<Record<string, unknown>>;
  colA: string;
  colB: string;
}) {
  if (data.length === 0) return null;

  // Determine category keys (all keys except colA)
  const categoryKeys = Object.keys(data[0]).filter((k) => k !== colA);
  const COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#6366f1"];

  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold text-slate-700">
        {colA} × {colB}
      </p>
      <div aria-label={`Cross-tab: ${colA} × ${colB}`}>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 2, right: 4, bottom: 20, left: 4 }}>
          <XAxis dataKey={colA} tick={{ fontSize: 9 }} angle={-30} textAnchor="end" />
          <YAxis tick={{ fontSize: 9 }} width={40} />
          <Tooltip contentStyle={{ fontSize: 11 }} />
          {categoryKeys.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="cross-tab"
              fill={COLORS[i % COLORS.length]}
              radius={i === categoryKeys.length - 1 ? [2, 2, 0, 0] : undefined}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationProfiler({
  profile,
  crosstabData,
  onCrosstabRequest,
}: PopulationProfilerProps) {
  const [selectedCol, setSelectedCol] = useState<string>(
    profile.columns[0]?.name ?? "",
  );

  const selectedEntry = profile.columns.find((c) => c.name === selectedCol);
  const allColumnNames = profile.columns.map((c) => c.name);

  function handleCrosstab(colB: string) {
    onCrosstabRequest(selectedCol, colB);
  }

  return (
    <div className="flex h-full">
      {/* Column list sidebar */}
      <div className="w-44 shrink-0 border-r border-slate-200">
        <div className="px-3 py-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Columns</p>
        </div>
        <ScrollArea className="h-[calc(100%-2rem)]">
          <div className="flex flex-col gap-0.5 px-2 pb-4">
            {profile.columns.map((col) => {
              const colProfile = col.profile;
              const badge =
                colProfile.type === "numeric"
                  ? "num"
                  : colProfile.type === "categorical"
                  ? "cat"
                  : "bool";
              return (
                <button
                  key={col.name}
                  type="button"
                  className={`flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-left text-xs transition-colors ${
                    selectedCol === col.name
                      ? "bg-blue-50 text-blue-700 font-medium"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                  onClick={() => { setSelectedCol(col.name); }}
                >
                  <Badge variant="secondary" className="shrink-0 text-[9px] px-1 py-0">
                    {badge}
                  </Badge>
                  <span className="truncate">{col.name}</span>
                </button>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* Profile panel */}
      <div className="flex-1 overflow-y-auto p-4">
        {selectedEntry ? (
          <div>
            <div className="mb-3 flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-900">{selectedEntry.name}</h3>
              <Badge variant="secondary" className="text-xs">
                {selectedEntry.profile.type}
              </Badge>
            </div>
            <Separator className="mb-4" />

            {selectedEntry.profile.type === "numeric" && (
              <NumericProfile
                name={selectedEntry.name}
                profile={selectedEntry.profile}
                allColumnNames={allColumnNames}
                onCrosstab={handleCrosstab}
              />
            )}
            {selectedEntry.profile.type === "categorical" && (
              <CategoricalProfile
                name={selectedEntry.name}
                profile={selectedEntry.profile}
                allColumnNames={allColumnNames}
                onCrosstab={handleCrosstab}
              />
            )}
            {selectedEntry.profile.type === "boolean" && (
              <BooleanProfile profile={selectedEntry.profile} />
            )}

            {/* Cross-tab result */}
            {crosstabData && crosstabData.col_a === selectedCol && (
              <CrosstabChart
                data={crosstabData.data}
                colA={crosstabData.col_a}
                colB={crosstabData.col_b}
              />
            )}
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Select a column to profile
          </div>
        )}
      </div>
    </div>
  );
}
