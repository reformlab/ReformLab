// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Detail panel sub-component for ComparisonDashboardScreen.
 * Extracted from ComparisonDashboardScreen.tsx lines 465-524 — Story 18.5, AC-2.
 */

import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { DetailTarget } from "./comparison-helpers";

export function DetailPanel({
  target,
  onDismiss,
}: {
  target: DetailTarget;
  onDismiss: () => void;
}) {
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onDismiss]);

  return (
    <aside
      ref={panelRef}
      className="rounded-lg border border-slate-200 bg-slate-50 p-3"
      aria-label="Indicator detail panel"
    >
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-800">{target.label}</p>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Close detail panel"
          className="text-slate-400 hover:text-slate-700"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="mb-3 text-xs text-slate-500">{target.methodology}</p>
      <div className="space-y-1">
        {Object.entries(target.values).map(([k, v]) => {
          if (k === "decile" || k === "year" || k === "field_name" || k === "metric") return null;
          const numVal = typeof v === "number" ? v : null;
          const isDelta = k.startsWith("delta_") || k.startsWith("pct_delta_");
          const isNeg = isDelta && numVal !== null && numVal < 0;
          const isPos = isDelta && numVal !== null && numVal > 0;
          const valueClass = isNeg
            ? "text-red-600 font-medium"
            : isPos
              ? "text-emerald-600 font-medium"
              : "text-slate-800";
          return (
            <div key={k} className="flex justify-between text-xs">
              <span className="text-slate-500">{k}</span>
              <span className={valueClass}>
                {typeof v === "number" ? v.toLocaleString() : String(v ?? "")}
              </span>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
