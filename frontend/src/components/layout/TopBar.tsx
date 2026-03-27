// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * TopBar — 48px application top bar showing current stage and utility icons.
 *
 * Left: logo · scenario name (clickable) · Save button · separator · stage label.
 * Right: docs link, GitHub, API status dot, Settings — all Lucide line-style.
 *
 * Story 20.1 — AC-1.
 * Story 20.2 — AC-3: scenario name opens ScenarioEntryDialog; Save button persists scenario.
 */

import { useState } from "react";
import { BookOpen, Github, Save, Settings } from "lucide-react";

import { useAppState } from "@/contexts/AppContext";
import { STAGES } from "@/types/workspace";
import { Separator } from "@/components/ui/separator";
import { ScenarioEntryDialog } from "@/components/scenario/ScenarioEntryDialog";

export function TopBar() {
  const { activeStage, activeScenario, saveCurrentScenario, apiConnected } = useAppState();

  const currentStageLabel = STAGES.find((s) => s.key === activeStage)?.label ?? activeStage;

  const [scenarioDialogOpen, setScenarioDialogOpen] = useState(false);

  return (
    <div className="flex h-12 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4">
      {/* Logo + scenario name + separator + stage label */}
      <div className="flex items-center gap-2.5">
        <img src="/logo.svg" alt="ReformLab" className="h-6 w-auto" />

        {/* Scenario name (clickable) */}
        <button
          type="button"
          className="text-sm text-slate-500 truncate max-w-48 hover:text-slate-700 transition-colors"
          aria-label="Switch scenario"
          onClick={() => setScenarioDialogOpen(true)}
        >
          {activeScenario?.name ?? "No scenario"}
        </button>

        {/* Save scenario button */}
        <button
          type="button"
          className="text-slate-500 hover:text-slate-700 transition-colors disabled:opacity-40 disabled:pointer-events-none"
          aria-label="Save scenario"
          disabled={!activeScenario}
          onClick={saveCurrentScenario}
        >
          <Save className="h-4 w-4" />
        </button>

        <Separator orientation="vertical" className="h-5 mx-1" />

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

      {/* Scenario entry dialog */}
      <ScenarioEntryDialog open={scenarioDialogOpen} onOpenChange={setScenarioDialogOpen} />
    </div>
  );
}
