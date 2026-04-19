// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * TopBar — 48px application top bar showing brand, scenario controls, and utility icons.
 *
 * Story 22.1 — AC-1: Brand block with logo + "ReformLab" wordmark.
 * Story 22.1 — AC-2: Docs and GitHub links open in new tab with security attributes.
 * Story 22.1 — AC-3: Scenario controls in center-left container with visual separation.
 * Story 22.1 — AC-4: Narrow screens hide secondary utilities; brand block always visible.
 * Story 22.1 — AC-5: Wordmark uses Inter semibold (600) with slate-700 (#334155).
 *
 * Story 20.1 — AC-1: TopBar shows current stage.
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
      {/* Brand block (logo + wordmark) · Scenario controls · Stage label */}
      <div className="flex items-center gap-x-4">
        {/* Brand block: logo + wordmark */}
        <div className="flex items-center gap-2">
          <img src="/logo.svg" alt="ReformLab" className="h-6 w-auto" />
          <span className="text-sm font-semibold text-slate-700">ReformLab</span>
        </div>

        {/* Scenario controls: name (clickable) + Save button */}
        <div className="flex items-center gap-2">
          {/* Scenario name (clickable) */}
          <button
            type="button"
            className="text-sm text-slate-500 truncate max-w-48 hover:text-slate-700 transition-colors"
            aria-label="Switch scenario"
            title={activeScenario?.name ?? "No scenario"}
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
        </div>

        <Separator orientation="vertical" className="h-5 mx-1" />

        {/* Stage label */}
        <span className="text-lg font-semibold text-slate-900">{currentStageLabel}</span>
      </div>

      {/* Utility icons: docs, GitHub, API status, Settings */}
      <div className="flex items-center gap-3">
        {/* Documentation link */}
        <a
          href="https://reform-lab.eu"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Open documentation at reform-lab.eu"
          title="Open documentation at reform-lab.eu"
          className="hidden md:flex items-center text-slate-500 hover:text-slate-700 transition-colors"
        >
          <BookOpen className="h-4 w-4" />
        </a>

        {/* GitHub link */}
        <a
          href="https://github.com/lucasvivier/reformlab"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="View source code on GitHub"
          title="View source code on GitHub"
          className="hidden md:flex items-center text-slate-500 hover:text-slate-700 transition-colors"
        >
          <Github className="h-4 w-4" />
        </a>

        {/* API status indicator */}
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-1.5"
          title={apiConnected ? "Backend API is reachable" : "Cannot reach backend API"}
        >
          <div className={`h-2 w-2 rounded-full ${apiConnected ? "bg-emerald-500" : "bg-amber-500 animate-pulse"}`} />
          <span className={`hidden md:inline text-xs ${apiConnected ? "text-slate-400" : "text-amber-600 font-medium"}`}>
            {apiConnected ? "API" : "Disconnected"}
          </span>
        </div>

        {/* Settings icon (display-only, decorative - hidden from screen readers) */}
        <div className="hidden md:flex items-center text-slate-500" aria-hidden="true">
          <Settings className="h-4 w-4" />
        </div>
      </div>

      {/* Scenario entry dialog */}
      <ScenarioEntryDialog open={scenarioDialogOpen} onOpenChange={setScenarioDialogOpen} />
    </div>
  );
}
