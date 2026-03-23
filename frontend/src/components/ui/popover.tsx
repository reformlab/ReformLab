// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Popover({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("relative", className)} {...props} />;
}
