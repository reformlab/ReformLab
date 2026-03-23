// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { ChevronLeft, HelpCircle } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

interface RightPanelProps {
  collapsed: boolean;
  onToggle: () => void;
  children: ReactNode;
}

export function RightPanel({ collapsed, onToggle, children }: RightPanelProps) {
  if (collapsed) {
    return (
      <aside className="h-full border-l border-slate-200 bg-slate-50">
        <div className="flex h-full flex-col items-center gap-2 py-2">
          <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Expand right panel">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="-rotate-90 pt-16 text-xs uppercase tracking-wide text-slate-500">Help</span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="h-full border-l border-slate-200 bg-slate-50">
      <div className="flex h-10 items-center justify-between border-b border-slate-200 px-3">
        <div className="flex items-center gap-1.5">
          <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Help</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Collapse right panel">
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>
      <div className="h-[calc(100%-2.5rem)] overflow-auto p-3">{children}</div>
    </aside>
  );
}
