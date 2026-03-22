/** Population generation progress, step log, and error display (Story 17.1, AC-4). */

import { CheckCircle2, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ErrorAlert } from "@/components/simulation/ErrorAlert";
import type { GenerationResult, StepLogItem } from "@/api/types";

interface PopulationGenerationProgressProps {
  loading: boolean;
  result: GenerationResult | null;
  error: string | null;
  errorDetail: { what: string; why: string; fix: string } | null;
}

function StepLogEntry({ entry }: { entry: StepLogItem }) {
  const isLoad = entry.step_type === "load";
  return (
    <div className="flex items-start gap-2 border-b border-slate-100 py-1.5">
      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-700">
          <span className="font-medium">{isLoad ? "Load" : "Merge"}</span>:{" "}
          <span className="data-mono">{entry.label}</span>
          {entry.method_name ? (
            <Badge variant="info" className="ml-1 text-xs">
              {entry.method_name}
            </Badge>
          ) : null}
        </p>
        <p className="text-xs text-slate-500">
          {entry.output_rows.toLocaleString()} rows · {entry.output_columns.length} columns ·{" "}
          {entry.duration_ms.toFixed(1)} ms
        </p>
      </div>
    </div>
  );
}

export function PopulationGenerationProgress({
  loading,
  result,
  error,
  errorDetail,
}: PopulationGenerationProgressProps) {
  if (loading) {
    return (
      <section
        aria-label="Generation in progress"
        className="border border-slate-200 bg-white p-3 flex items-center gap-3"
        aria-busy="true"
      >
        <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
        <div>
          <p className="text-sm font-medium text-slate-900">Generating population…</p>
          <p className="text-xs text-slate-500">Running pipeline steps synchronously</p>
        </div>
      </section>
    );
  }

  if (error || errorDetail) {
    return (
      <section aria-label="Generation failed" className="space-y-2">
        {errorDetail ? (
          <ErrorAlert what={errorDetail.what} why={errorDetail.why} fix={errorDetail.fix} />
        ) : (
          <p className="text-xs text-red-600">{error}</p>
        )}
      </section>
    );
  }

  if (!result) return null;

  return (
    <section
      aria-label="Generation complete"
      className="border border-emerald-200 bg-emerald-50 p-3 space-y-3"
    >
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
        <p className="text-sm font-semibold text-emerald-800">Population generated</p>
        <Badge variant="success" className="ml-auto">
          {result.summary.record_count.toLocaleString()} records
        </Badge>
      </div>

      <div>
        <p className="mb-1 text-xs font-semibold text-slate-600">Execution log</p>
        <div className="border border-slate-200 bg-white">
          {result.step_log.map((entry) => (
            <StepLogEntry key={entry.step_index} entry={entry} />
          ))}
        </div>
      </div>
    </section>
  );
}
