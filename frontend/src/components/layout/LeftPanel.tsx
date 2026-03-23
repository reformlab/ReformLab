// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface LeftPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  children: ReactNode;
}

export function LeftPanel({ collapsed, onToggle, children }: LeftPanelProps) {
  if (collapsed) {
    return (
      <aside className="h-full border-r border-slate-200 bg-slate-50">
        <div className="flex h-full flex-col items-center gap-2 py-2">
          <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Expand left panel">
            <ChevronRight className="h-4 w-4" />
          </Button>
          <span className="-rotate-90 pt-16 text-xs uppercase tracking-wide text-slate-500">Scenarios</span>
        </div>
      </aside>
    );
  }

  return (
    <aside className={cn("h-full border-r border-slate-200 bg-slate-50", "min-w-0")}>
      <div className="flex h-10 items-center justify-between border-b border-slate-200 px-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Scenarios</p>
        <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Collapse left panel">
          <ChevronRight className="h-4 w-4 rotate-180" />
        </Button>
      </div>
      <div className="h-[calc(100%-2.5rem)] overflow-auto p-2">{children}</div>
    </aside>
  );
}
