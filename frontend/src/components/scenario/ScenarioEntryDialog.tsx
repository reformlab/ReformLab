// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * ScenarioEntryDialog — four-action scenario entry flow.
 *
 * Provides: New Scenario, Open Saved, Clone Current, Demo Scenario.
 * Triggered from TopBar scenario-name button.
 *
 * Story 20.2 — AC-3.
 */

import { useEffect, useState } from "react";
import { Copy, FilePlus, FolderOpen, Play, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { useAppState } from "@/contexts/AppContext";

// ============================================================================
// Props
// ============================================================================

interface ScenarioEntryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// ============================================================================
// Component
// ============================================================================

export function ScenarioEntryDialog({ open, onOpenChange }: ScenarioEntryDialogProps) {
  const {
    activeScenario,
    savedScenarios,
    createNewScenario,
    cloneCurrentScenario,
    loadSavedScenario,
    resetToDemo,
  } = useAppState();

  const [showSavedList, setShowSavedList] = useState(false);

  // Reset saved list state when dialog closes
  useEffect(() => {
    if (!open) setShowSavedList(false);
  }, [open]);

  if (!open) return null;

  function handleClose() {
    onOpenChange(false);
  }

  function handleNewScenario() {
    createNewScenario();
    handleClose();
  }

  function handleOpenSaved() {
    setShowSavedList((prev) => !prev);
  }

  function handleClone() {
    if (!activeScenario) return;
    cloneCurrentScenario();
    handleClose();
  }

  function handleDemo() {
    resetToDemo();
    handleClose();
  }

  function handleLoadSaved(id: string) {
    loadSavedScenario(id);
    handleClose();
  }

  const cardBase =
    "border border-slate-200 rounded-md p-3 hover:bg-slate-50 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300 text-left w-full";
  const cardDisabled = "opacity-50 pointer-events-none";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="scenario-dialog-title"
      onKeyDown={(e) => { if (e.key === "Escape") handleClose(); }}
      onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div>
            <h2 id="scenario-dialog-title" className="text-base font-semibold text-slate-900">Switch Scenario</h2>
            {activeScenario && (
              <p className="text-sm text-slate-500">Current: {activeScenario.name}</p>
            )}
          </div>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Close dialog"
            className="text-slate-400 hover:text-slate-600 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300 rounded"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* 2×2 action grid */}
        <div className="grid grid-cols-2 gap-3 p-4">
          {/* New Scenario */}
          <button
            type="button"
            className={cardBase}
            onClick={handleNewScenario}
            aria-label="New Scenario"
          >
            <FilePlus className="h-5 w-5 text-slate-600 mb-1" />
            <div className="text-sm font-medium text-slate-800">New Scenario</div>
            <div className="text-xs text-slate-500">Start fresh from a template</div>
          </button>

          {/* Open Saved */}
          <button
            type="button"
            className={cardBase}
            onClick={handleOpenSaved}
            aria-label="Open Saved"
          >
            <FolderOpen className="h-5 w-5 text-slate-600 mb-1" />
            <div className="text-sm font-medium text-slate-800">Open Saved</div>
            <div className="text-xs text-slate-500">Resume a previous scenario</div>
          </button>

          {/* Clone Current */}
          <button
            type="button"
            className={`${cardBase} ${!activeScenario ? cardDisabled : ""}`}
            onClick={handleClone}
            disabled={!activeScenario}
            aria-label="Clone Current"
          >
            <Copy className="h-5 w-5 text-slate-600 mb-1" />
            <div className="text-sm font-medium text-slate-800">Clone Current</div>
            <div className="text-xs text-slate-500">Duplicate the active scenario</div>
          </button>

          {/* Demo Scenario */}
          <button
            type="button"
            className={cardBase}
            onClick={handleDemo}
            aria-label="Demo Scenario"
          >
            <Play className="h-5 w-5 text-slate-600 mb-1" />
            <div className="text-sm font-medium text-slate-800">Demo Scenario</div>
            <div className="text-xs text-slate-500">Carbon Tax + Dividend example</div>
          </button>
        </div>

        {/* Saved scenario list (conditional) */}
        {showSavedList && (
          <div className="border-t border-slate-100 px-4 pb-4">
            {savedScenarios.length === 0 ? (
              <p className="text-sm text-slate-400 py-3">No saved scenarios yet</p>
            ) : (
              <ul className="mt-3 space-y-1">
                {savedScenarios.map((s) => (
                  <li key={s.id}>
                    <button
                      type="button"
                      className="w-full flex items-center gap-2 py-2 px-2 rounded hover:bg-slate-50 transition-colors text-left"
                      onClick={() => handleLoadSaved(s.id)}
                    >
                      <span className="text-sm font-medium text-slate-800 flex-1 truncate">{s.name}</span>
                      {s.policyType && (
                        <Badge variant="secondary" className="shrink-0 text-xs">
                          {s.policyType}
                        </Badge>
                      )}
                      {s.engineConfig && (
                        <span className="text-xs text-slate-400 shrink-0">
                          {s.engineConfig.startYear}–{s.engineConfig.endYear}
                        </span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
