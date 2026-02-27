import type { SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-8 w-full border border-slate-300 bg-white px-2 text-sm text-slate-900 outline-none focus:border-blue-500",
        className,
      )}
      {...props}
    />
  );
}
