// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * ConflictList — shared component for displaying portfolio conflict warnings.
 *
 * Extracted from PortfolioDesignerScreen (Story 20.3, Task 5.2).
 * Used by PoliciesStageScreen (inline composition) and PortfolioDesignerScreen (deprecated).
 */

import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { PortfolioConflict } from "@/api/types";

interface ConflictListProps {
  conflicts: PortfolioConflict[];
}

export function ConflictList({ conflicts }: ConflictListProps) {
  if (conflicts.length === 0) {
    return (
      <div className="flex items-center gap-2 border border-emerald-200 bg-emerald-50 p-2 text-sm text-emerald-700">
        <CheckCircle2 className="h-4 w-4 shrink-0" />
        No conflicts detected.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {conflicts.map((c, i) => (
        <div
          key={i}
          className="border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800"
        >
          <div className="flex items-start gap-1.5">
            <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
            <div>
              <p className="font-medium">{c.conflict_type} — {c.parameter_name}</p>
              <p className="mt-0.5 text-amber-700">{c.description}</p>
              <p className="mt-0.5 text-amber-600">
                Policies: {c.policy_indices.map((idx) => `#${idx + 1}`).join(", ")}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
