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
import { isValidStage, DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// localStorage key constants (exported for test access)
// ============================================================================

export const SCENARIO_STORAGE_KEY = "reformlab-active-scenario";
export const STAGE_STORAGE_KEY = "reformlab-active-stage";
export const SAVED_SCENARIOS_KEY = "reformlab-saved-scenarios";
export const HAS_LAUNCHED_KEY = "reformlab-has-launched";
// Story 22.3: Track scenario IDs with manually edited names
export const MANUALLY_EDITED_NAMES_KEY = "reformlab-manually-edited-names";

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
    const parsed = JSON.parse(raw) as WorkspaceScenario;

    // Story 22.6: Migration logic for legacy scenarios (immutable - returns new object)
    const needsTasteMigration = parsed.engineConfig?.tasteParameters === undefined;
    const needsCalibrationMigration = parsed.engineConfig?.calibrationState === undefined;

    if (!needsTasteMigration && !needsCalibrationMigration) {
      return parsed;
    }

    // Return new object with migrated fields (don't mutate parsed)
    return {
      ...parsed,
      engineConfig: {
        ...parsed.engineConfig,
        tasteParameters: parsed.engineConfig.tasteParameters ?? DEFAULT_TASTE_PARAMETERS,
        calibrationState: parsed.engineConfig.calibrationState ?? "not_configured",
      },
    };
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
    // Story 26.1: Migrate legacy "engine" stage to "scenario"
    const migrated = raw === "engine" ? "scenario" : raw;
    return isValidStage(migrated) ? migrated : null;
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
    const parsed = JSON.parse(raw) as WorkspaceScenario[];

    // Story 22.6: Migration logic for legacy scenarios (immutable - returns new objects)
    return parsed.map((scenario) => {
      const needsTasteMigration = scenario.engineConfig?.tasteParameters === undefined;
      const needsCalibrationMigration = scenario.engineConfig?.calibrationState === undefined;

      if (!needsTasteMigration && !needsCalibrationMigration) {
        return scenario;
      }

      // Return new object with migrated fields (don't mutate parsed)
      return {
        ...scenario,
        engineConfig: {
          ...scenario.engineConfig,
          tasteParameters: scenario.engineConfig.tasteParameters ?? DEFAULT_TASTE_PARAMETERS,
          calibrationState: scenario.engineConfig.calibrationState ?? "not_configured",
        },
      };
    });
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
// Story 22.3: Manually edited scenario names tracking
// ============================================================================

/** Load the set of manually edited scenario IDs from localStorage. */
export function getManuallyEditedNames(): Set<string> {
  try {
    const raw = localStorage.getItem(MANUALLY_EDITED_NAMES_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw) as string[];
    return new Set(parsed);
  } catch {
    return new Set();
  }
}

/** Save the set of manually edited scenario IDs to localStorage. */
export function saveManuallyEditedNames(ids: Set<string>): void {
  try {
    localStorage.setItem(MANUALLY_EDITED_NAMES_KEY, JSON.stringify([...ids]));
  } catch {
    // Storage quota exceeded — silently ignore
  }
}

/** Add a scenario ID to the manually edited names set. */
export function addManuallyEditedName(id: string): void {
  const current = getManuallyEditedNames();
  current.add(id);
  saveManuallyEditedNames(current);
}

/** Remove a scenario ID from the manually edited names set. */
export function removeManuallyEditedName(id: string): void {
  const current = getManuallyEditedNames();
  current.delete(id);
  saveManuallyEditedNames(current);
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
