// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** CalibrationPanel — UI stub for Story 20.5.
 *
 * Full calibration implementation deferred. Shows intended UI structure with
 * disabled interactions. Backend calibration API not available in Story 20.5.
 *
 * Story 20.5 stub: full calibration implementation deferred.
 */

import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

// ============================================================================
// Component
// ============================================================================

export function CalibrationPanel() {
  return (
    <div className="rounded border border-slate-200 bg-slate-50 p-3 space-y-3 text-sm">
      {/* Status */}
      <div className="flex items-center justify-between">
        <span className="font-medium text-slate-700">Calibration</span>
        <Badge variant="outline" className="text-amber-700 border-amber-300 bg-amber-50">
          Not configured
        </Badge>
      </div>

      {/* Method select — display only */}
      <div className="space-y-1">
        <label className="text-xs text-slate-500">Calibration method</label>
        <select
          className="w-full rounded border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700"
          disabled
          defaultValue="mle"
        >
          <option value="mle">Maximum Likelihood (MLE)</option>
          <option value="smm">Simulated Method of Moments (SMM)</option>
        </select>
      </div>

      {/* Calibration targets table */}
      <div className="space-y-1">
        <label className="text-xs text-slate-500">Calibration targets</label>
        <table className="w-full text-xs border border-slate-200 rounded">
          <thead>
            <tr className="bg-slate-100 text-slate-600">
              <th className="text-left px-2 py-1 font-medium">Target</th>
              <th className="text-left px-2 py-1 font-medium">Observed</th>
              <th className="text-left px-2 py-1 font-medium">Weight</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={3} className="px-2 py-2 text-center text-slate-400 italic">
                No targets defined
              </td>
            </tr>
          </tbody>
        </table>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs text-slate-500 px-2"
          onClick={() => toast.info("Calibration targets coming soon")}
        >
          + Add target
        </Button>
      </div>

      {/* Run Calibration button — disabled stub */}
      <Button
        variant="outline"
        size="sm"
        disabled
        className="w-full"
        title="Full calibration available in a future release"
      >
        Run Calibration
      </Button>
    </div>
  );
}
