import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Switch({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={cn("inline-flex cursor-pointer items-center gap-2 text-xs", className)}>
      <input type="checkbox" className="h-4 w-4 accent-blue-600" {...props} />
      <span>{props["aria-label"] ?? "Toggle"}</span>
    </label>
  );
}
