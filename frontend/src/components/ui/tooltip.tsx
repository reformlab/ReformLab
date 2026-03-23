// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Tooltip({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn("text-xs text-slate-500", className)} {...props} />;
}
