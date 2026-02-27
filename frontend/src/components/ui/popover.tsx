import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Popover({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("relative", className)} {...props} />;
}
