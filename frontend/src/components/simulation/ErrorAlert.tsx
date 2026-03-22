/** Shared structured error display for {what, why, fix} tuples (Story 18.3, AC-2). */

import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ErrorState {
  what: string;
  why: string;
  fix: string;
}

interface ErrorAlertProps {
  what: string;
  why: string;
  fix: string;
  className?: string;
}

export function ErrorAlert({ what, why, fix, className }: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3",
        className,
      )}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
      <div className="space-y-0.5 text-xs">
        <p className="font-semibold text-red-800">{what}</p>
        <p className="text-red-700">{why}</p>
        <p className="text-red-600">{fix}</p>
      </div>
    </div>
  );
}
