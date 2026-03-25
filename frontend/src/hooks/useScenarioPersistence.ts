// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Scenario persistence utilities — reads and writes workspace state to localStorage.
 *
 * Provides first-launch detection, scenario round-trips, stage persistence,
 * and a bounded saved-scenario library (max 20 entries, oldest dropped on overflow).
 *
 * Key schema:
 *   reformlab-active-scenario  → JSON<WorkspaceScenario | null>
 *   reformlab-active-stage     → StageKey
 *   reformlab-saved-scenarios  → JSON<WorkspaceScenario[]>
 *   reformlab-has-launched     → "true" | absent
 *
 * Story 20.2 — AC-2, AC-5.
 */

import type { StageKey, WorkspaceScenario } from "@/types/workspace";
import { isValidStage } from "@/types/workspace";

// ============================================================================
// localStorage key constants (exported for test access)
// ============================================================================

export const SCENARIO_STORAGE_KEY = "reformlab-active-scenario";
export const STAGE_STORAGE_KEY = "reformlab-active-stage";
export const SAVED_SCENARIOS_KEY = "reformlab-saved-scenarios";
export const HAS_LAUNCHED_KEY = "reformlab-has-launched";

const MAX_SAVED_SCENARIOS = 20;

// ============================================================================
// Module-level persistence functions (stable references, no React state)
// ============================================================================

export function saveScenario(scenario: WorkspaceScenario | null): void {
  try {
    localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(scenario));
  } catch {
    // Storage quota exceeded — silently ignore
  }
}

export function loadScenario(): WorkspaceScenario | null {
  try {
    const raw = localStorage.getItem(SCENARIO_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as WorkspaceScenario;
  } catch {
    return null;
  }
}

export function saveStage(stage: StageKey): void {
  try {
    localStorage.setItem(STAGE_STORAGE_KEY, stage);
  } catch {
    // Storage quota exceeded — silently ignore
  }
}

export function loadStage(): StageKey | null {
  try {
    const raw = localStorage.getItem(STAGE_STORAGE_KEY);
    if (!raw) return null;
    return isValidStage(raw) ? raw : null;
  } catch {
    return null;
  }
}

export function isFirstLaunch(): boolean {
  return localStorage.getItem(HAS_LAUNCHED_KEY) !== "true";
}

export function markLaunched(): void {
  try {
    localStorage.setItem(HAS_LAUNCHED_KEY, "true");
  } catch {
    // Storage quota exceeded — silently ignore
  }
}

export function getSavedScenarios(): WorkspaceScenario[] {
  try {
    const raw = localStorage.getItem(SAVED_SCENARIOS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as WorkspaceScenario[];
  } catch {
    return [];
  }
}

export function saveScenarioToList(scenario: WorkspaceScenario): void {
  try {
    const existing = getSavedScenarios();
    const idx = existing.findIndex((s) => s.id === scenario.id);
    let updated: WorkspaceScenario[];
    if (idx !== -1) {
      // Upsert: replace existing entry
      updated = [...existing.slice(0, idx), scenario, ...existing.slice(idx + 1)];
    } else {
      updated = [...existing, scenario];
    }
    // Cap at MAX_SAVED_SCENARIOS — drop oldest (front of array)
    if (updated.length > MAX_SAVED_SCENARIOS) {
      updated = updated.slice(updated.length - MAX_SAVED_SCENARIOS);
    }
    localStorage.setItem(SAVED_SCENARIOS_KEY, JSON.stringify(updated));
  } catch {
    // Storage quota exceeded — silently ignore
  }
}

// ============================================================================
// Hook (thin wrapper for backward-compatibility with existing call sites)
// ============================================================================

export interface ScenarioPersistence {
  saveScenario: (scenario: WorkspaceScenario | null) => void;
  loadScenario: () => WorkspaceScenario | null;
  saveStage: (stage: StageKey) => void;
  loadStage: () => StageKey | null;
  isFirstLaunch: () => boolean;
  markLaunched: () => void;
  getSavedScenarios: () => WorkspaceScenario[];
  saveScenarioToList: (scenario: WorkspaceScenario) => void;
}

/** @deprecated Use module-level exports directly instead. */
export function useScenarioPersistence(): ScenarioPersistence {
  return {
    saveScenario,
    loadScenario,
    saveStage,
    loadStage,
    isFirstLaunch,
    markLaunched,
    getSavedScenarios,
    saveScenarioToList,
  };
}
