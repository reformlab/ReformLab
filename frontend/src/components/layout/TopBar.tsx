// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * TopBar — 48px application top bar showing current stage and utility icons.
 *
 * Left: current stage label (text-lg font-semibold, Inter).
 * Right: docs link, GitHub, API status dot, Settings — all Lucide line-style.
 *
 * Story 20.1 — AC-1.
 */

import { BookOpen, Github, Settings } from "lucide-react";

import { useAppState } from "@/contexts/AppContext";
import { STAGES } from "@/types/workspace";

export function TopBar() {
  const { activeStage, apiConnected } = useAppState();

  const currentStageLabel = STAGES.find((s) => s.key === activeStage)?.label ?? activeStage;

  return (
    <div className="flex h-12 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4">
      {/* Logo + Stage label */}
      <div className="flex items-center gap-2.5">
        <img src="/logo.svg" alt="ReformLab" className="h-6 w-auto" />
        <span className="text-lg font-semibold text-slate-900">{currentStageLabel}</span>
      </div>

      {/* Utility icons */}
      <div className="flex items-center gap-3">
        <BookOpen className="h-4 w-4 text-slate-500" aria-label="Documentation" />
        <Github className="h-4 w-4 text-slate-500" aria-label="GitHub" />

        {/* API status dot with title tooltip */}
        <div
          className={`h-2 w-2 rounded-full ${apiConnected ? "bg-emerald-500" : "bg-amber-500"}`}
          title={apiConnected ? "API connected" : "Using sample data"}
          aria-label={apiConnected ? "API connected" : "API disconnected — using sample data"}
        />

        <Settings className="h-4 w-4 text-slate-500" aria-label="Settings" />
      </div>
    </div>
  );
}
