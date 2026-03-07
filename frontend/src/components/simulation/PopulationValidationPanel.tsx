/** Population marginal validation panel (Story 17.1, AC-5). */

import { CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ValidationResultResponse } from "@/api/types";

interface PopulationValidationPanelProps {
  validation: ValidationResultResponse;
}

export function PopulationValidationPanel({ validation }: PopulationValidationPanelProps) {
  const overallIcon = validation.all_passed ? (
    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
  ) : (
    <XCircle className="h-5 w-5 text-red-500" />
  );

  return (
    <section aria-label="Population validation" className="border border-slate-200 bg-white p-3 space-y-3">
      <div className="flex items-center gap-2">
        {overallIcon}
        <p className="text-sm font-semibold text-slate-900">Validation</p>
        <Badge
          variant={validation.all_passed ? "success" : "destructive"}
          className="ml-auto"
        >
          {validation.all_passed ? "All passed" : `${validation.failed_count} failed`}
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="border border-slate-200 p-2">
          <p className="data-mono text-lg font-semibold text-slate-900">
            {validation.total_constraints}
          </p>
          <p className="text-xs text-slate-500">Total checks</p>
        </div>
        <div className="border border-slate-200 p-2">
          <p className="data-mono text-lg font-semibold text-emerald-600">
            {validation.total_constraints - validation.failed_count}
          </p>
          <p className="text-xs text-slate-500">Passed</p>
        </div>
        <div className="border border-slate-200 p-2">
          <p className="data-mono text-lg font-semibold text-red-600">
            {validation.failed_count}
          </p>
          <p className="text-xs text-slate-500">Failed</p>
        </div>
      </div>

      {validation.marginal_results.length > 0 ? (
        <div>
          <p className="mb-1 text-xs font-semibold text-slate-600">Per-marginal results</p>
          <div className="space-y-1.5">
            {validation.marginal_results.map((m, i) => (
              <div
                key={i}
                className="flex items-start gap-2 border border-slate-200 p-2"
              >
                {m.passed ? (
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                ) : (
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="data-mono text-xs font-semibold text-slate-800">{m.dimension}</p>
                  <p className="text-xs text-slate-600">
                    Max deviation:{" "}
                    <span className={m.passed ? "text-emerald-600" : "text-red-600"}>
                      {(m.max_deviation * 100).toFixed(2)}%
                    </span>{" "}
                    (tolerance: {(m.tolerance * 100).toFixed(2)}%)
                  </p>
                </div>
                <Badge variant={m.passed ? "success" : "destructive"} className="text-xs">
                  {m.passed ? "Pass" : "Fail"}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-xs text-slate-500">
          No marginal constraints were checked. Marginals from catalog metadata will be applied
          automatically when available.
        </p>
      )}
    </section>
  );
}
