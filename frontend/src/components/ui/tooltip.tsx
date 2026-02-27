import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Tooltip({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn("text-xs text-slate-500", className)} {...props} />;
}
