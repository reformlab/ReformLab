import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Sheet({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("fixed inset-y-0 right-0 hidden", className)} {...props} />;
}
