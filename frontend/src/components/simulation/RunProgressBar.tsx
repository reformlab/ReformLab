import { XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

interface RunProgressBarProps {
  progress: number;
  currentStep: string;
  eta: string;
  onCancel: () => void;
}

export function RunProgressBar({
  progress,
  currentStep,
  eta,
  onCancel,
}: RunProgressBarProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-3" aria-label="Simulation progress">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-slate-900">Running Simulation</p>
        <p className="data-mono text-sm text-slate-700">{progress}%</p>
      </div>
      <div className="h-2 border border-slate-200 bg-slate-50">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="mt-2 flex items-center justify-between gap-2">
        <p className="text-xs text-slate-600">{currentStep}</p>
        <p className="text-xs text-slate-500">ETA {eta}</p>
      </div>
      <div className="mt-3">
        <Button variant="destructive" size="sm" onClick={onCancel}>
          <XCircle className="h-4 w-4" />
          Cancel run
        </Button>
      </div>
    </section>
  );
}
