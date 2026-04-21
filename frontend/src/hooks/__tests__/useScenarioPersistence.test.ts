// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for useScenarioPersistence hook.
 * Story 20.2 — Task 2, Task 7.2.
 * Story 26.1 — Migrate from four-stage to five-stage workspace (localStorage migration).
 */

import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import {
  HAS_LAUNCHED_KEY,
  SAVED_SCENARIOS_KEY,
  SCENARIO_STORAGE_KEY,
  STAGE_STORAGE_KEY,
  useScenarioPersistence,
} from "@/hooks/useScenarioPersistence";
import type { WorkspaceScenario } from "@/types/workspace";
import { DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// Helpers
// ============================================================================

type LegacyEngineConfig = WorkspaceScenario["engineConfig"] & {
  tasteParameters?: unknown;
  calibrationState?: unknown;
};

function makeScenario(overrides: Partial<WorkspaceScenario> = {}): WorkspaceScenario {
  return {
    id: "test-scenario-1",
    name: "Test Scenario",
    version: "1.0",
    status: "ready",
    isBaseline: false,
    baselineRef: null,
    portfolioName: null,
    populationIds: ["fr-synthetic-2024"],
    engineConfig: {
      startYear: 2025,
      endYear: 2030,
      seed: 42,
      investmentDecisionsEnabled: false,
      logitModel: null,
      discountRate: 0.03,
      tasteParameters: DEFAULT_TASTE_PARAMETERS,  // Story 22.6
      calibrationState: "not_configured",  // Story 22.6
    },
    policyType: "carbon-tax",
    lastRunId: null,
    ...overrides,
  };
}

function getHook() {
  const { result } = renderHook(() => useScenarioPersistence());
  return result.current;
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  localStorage.clear();
});

// ============================================================================
// saveScenario / loadScenario
// ============================================================================

describe("saveScenario / loadScenario", () => {
  it("round-trip preserves all fields", () => {
    const { saveScenario, loadScenario } = getHook();
    const scenario = makeScenario();
    saveScenario(scenario);
    const loaded = loadScenario();
    expect(loaded).toEqual(scenario);
  });

  it("loadScenario returns null on empty localStorage", () => {
    const { loadScenario } = getHook();
    expect(loadScenario()).toBeNull();
  });

  it("loadScenario returns null on corrupted JSON (never throws)", () => {
    localStorage.setItem(SCENARIO_STORAGE_KEY, "{not valid json");
    const { loadScenario } = getHook();
    expect(() => loadScenario()).not.toThrow();
    expect(loadScenario()).toBeNull();
  });

  it("saveScenario(null) stores null and loadScenario returns null", () => {
    const { saveScenario, loadScenario } = getHook();
    saveScenario(null);
    expect(loadScenario()).toBeNull();
  });

  it("preserves engineConfig fields in round-trip", () => {
    const { saveScenario, loadScenario } = getHook();
    const scenario = makeScenario({
      engineConfig: {
        startYear: 2026,
        endYear: 2035,
        seed: 99,
        investmentDecisionsEnabled: true,
        logitModel: "multinomial_logit",
        discountRate: 0.05,
        tasteParameters: DEFAULT_TASTE_PARAMETERS,  // Story 22.6
        calibrationState: "not_configured",  // Story 22.6
      },
    });
    saveScenario(scenario);
    const loaded = loadScenario();
    expect(loaded?.engineConfig.seed).toBe(99);
    expect(loaded?.engineConfig.investmentDecisionsEnabled).toBe(true);
  });

  describe("Story 22.6: Migration logic", () => {
    it("loadScenario migrates missing tasteParameters with defaults", () => {
      // Save a legacy scenario without tasteParameters
      const legacyScenario = makeScenario();
      delete (legacyScenario.engineConfig as LegacyEngineConfig).tasteParameters;
      delete (legacyScenario.engineConfig as LegacyEngineConfig).calibrationState;

      localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(legacyScenario));

      const { loadScenario } = getHook();
      const loaded = loadScenario();

      expect(loaded?.engineConfig.tasteParameters).toEqual(DEFAULT_TASTE_PARAMETERS);
      expect(loaded?.engineConfig.calibrationState).toBe("not_configured");
    });

    it("loadScenario does not mutate the stored scenario object", () => {
      // Save a legacy scenario
      const legacyScenario = makeScenario();
      delete (legacyScenario.engineConfig as LegacyEngineConfig).tasteParameters;

      const rawJson = JSON.stringify(legacyScenario);
      localStorage.setItem(SCENARIO_STORAGE_KEY, rawJson);

      const { loadScenario } = getHook();
      const loaded = loadScenario();

      // The stored JSON should remain unchanged
      expect(localStorage.getItem(SCENARIO_STORAGE_KEY)).toBe(rawJson);

      // But the loaded object should have the migrated fields
      expect(loaded?.engineConfig.tasteParameters).toEqual(DEFAULT_TASTE_PARAMETERS);
    });

    it("getSavedScenarios migrates missing tasteParameters with defaults", () => {
      const legacyScenarios = [
        makeScenario({ id: "s1" }),
        makeScenario({ id: "s2" }),
      ];

      // Remove tasteParameters from one scenario
      delete (legacyScenarios[0].engineConfig as LegacyEngineConfig).tasteParameters;
      delete (legacyScenarios[0].engineConfig as LegacyEngineConfig).calibrationState;

      localStorage.setItem(SAVED_SCENARIOS_KEY, JSON.stringify(legacyScenarios));

      const { getSavedScenarios } = getHook();
      const loaded = getSavedScenarios();

      expect(loaded).toHaveLength(2);
      expect(loaded[0].engineConfig.tasteParameters).toEqual(DEFAULT_TASTE_PARAMETERS);
      expect(loaded[0].engineConfig.calibrationState).toBe("not_configured");
      // Second scenario should be unchanged
      expect(loaded[1].engineConfig.tasteParameters).toEqual(DEFAULT_TASTE_PARAMETERS);
    });
  });
});

// ============================================================================
// saveStage / loadStage
// ============================================================================

describe("saveStage / loadStage", () => {
  it("round-trip preserves stage key", () => {
    const { saveStage, loadStage } = getHook();
    saveStage("scenario");
    expect(loadStage()).toBe("scenario");
  });

  it("loadStage returns null on empty localStorage", () => {
    const { loadStage } = getHook();
    expect(loadStage()).toBeNull();
  });

  it("writes under STAGE_STORAGE_KEY constant", () => {
    const { saveStage } = getHook();
    saveStage("population");
    expect(localStorage.getItem(STAGE_STORAGE_KEY)).toBe("population");
  });

  describe("Story 26.1: localStorage migration for 'engine' → 'scenario'", () => {
    it("migrates stored 'engine' stage to 'scenario' on load", () => {
      localStorage.setItem(STAGE_STORAGE_KEY, "engine");
      const { loadStage } = getHook();
      const loaded = loadStage();
      expect(loaded).toBe("scenario");
    });

    it("returns 'scenario' for stored 'engine' even after migration (idempotent)", () => {
      localStorage.setItem(STAGE_STORAGE_KEY, "engine");
      const { loadStage } = getHook();
      const firstLoad = loadStage();
      expect(firstLoad).toBe("scenario");
      // Simulate app re-load - localStorage still has "engine"
      const secondLoad = loadStage();
      expect(secondLoad).toBe("scenario");
    });

    it("preserves other stored stages", () => {
      const { loadStage } = getHook();
      localStorage.setItem(STAGE_STORAGE_KEY, "policies");
      expect(loadStage()).toBe("policies");
      localStorage.setItem(STAGE_STORAGE_KEY, "population");
      expect(loadStage()).toBe("population");
      localStorage.setItem(STAGE_STORAGE_KEY, "investment-decisions");
      expect(loadStage()).toBe("investment-decisions");
      localStorage.setItem(STAGE_STORAGE_KEY, "scenario");
      expect(loadStage()).toBe("scenario");
      localStorage.setItem(STAGE_STORAGE_KEY, "results");
      expect(loadStage()).toBe("results");
    });

    it("returns null for invalid stage", () => {
      localStorage.setItem(STAGE_STORAGE_KEY, "invalid-stage");
      const { loadStage } = getHook();
      expect(loadStage()).toBeNull();
    });

    it("updates localStorage on migration (one-time write to avoid repeated migrations)", () => {
      localStorage.setItem(STAGE_STORAGE_KEY, "engine");
      const { loadStage } = getHook();
      const loaded = loadStage(); // This migrates "engine" → "scenario" and writes back to localStorage
      expect(loaded).toBe("scenario");
      // localStorage should now have "scenario" (one-time migration)
      expect(localStorage.getItem(STAGE_STORAGE_KEY)).toBe("scenario");
    });

    it("handles hash+localStorage conflict scenario (hash empty, localStorage has engine)", () => {
      localStorage.setItem(STAGE_STORAGE_KEY, "engine");
      const { loadStage } = getHook();
      const loaded = loadStage();
      expect(loaded).toBe("scenario");
      // After migration, hash routing would use "scenario"
    });
  });
});

// ============================================================================
// isFirstLaunch / markLaunched
// ============================================================================

describe("isFirstLaunch / markLaunched", () => {
  it("isFirstLaunch returns true when HAS_LAUNCHED_KEY is absent", () => {
    const { isFirstLaunch } = getHook();
    expect(isFirstLaunch()).toBe(true);
  });

  it("isFirstLaunch returns false after markLaunched()", () => {
    const { isFirstLaunch, markLaunched } = getHook();
    markLaunched();
    expect(isFirstLaunch()).toBe(false);
  });

  it("markLaunched sets HAS_LAUNCHED_KEY to 'true'", () => {
    const { markLaunched } = getHook();
    markLaunched();
    expect(localStorage.getItem(HAS_LAUNCHED_KEY)).toBe("true");
  });

  it("isFirstLaunch returns false even if key is set externally", () => {
    localStorage.setItem(HAS_LAUNCHED_KEY, "true");
    const { isFirstLaunch } = getHook();
    expect(isFirstLaunch()).toBe(false);
  });
});

// ============================================================================
// getSavedScenarios / saveScenarioToList
// ============================================================================

describe("getSavedScenarios / saveScenarioToList", () => {
  it("getSavedScenarios returns empty array when localStorage is empty", () => {
    const { getSavedScenarios } = getHook();
    expect(getSavedScenarios()).toEqual([]);
  });

  it("saveScenarioToList appends a new scenario", () => {
    const { saveScenarioToList, getSavedScenarios } = getHook();
    const s = makeScenario({ id: "s1" });
    saveScenarioToList(s);
    const list = getSavedScenarios();
    expect(list).toHaveLength(1);
    expect(list[0].id).toBe("s1");
  });

  it("saveScenarioToList upserts by id (replaces existing)", () => {
    const { saveScenarioToList, getSavedScenarios } = getHook();
    const original = makeScenario({ id: "s1", name: "Original" });
    const updated = makeScenario({ id: "s1", name: "Updated" });
    saveScenarioToList(original);
    saveScenarioToList(updated);
    const list = getSavedScenarios();
    expect(list).toHaveLength(1);
    expect(list[0].name).toBe("Updated");
  });

  it("saveScenarioToList caps at 20 entries (oldest dropped)", () => {
    const { saveScenarioToList, getSavedScenarios } = getHook();
    for (let i = 0; i < 25; i++) {
      saveScenarioToList(makeScenario({ id: `s${i}`, name: `Scenario ${i}` }));
    }
    const list = getSavedScenarios();
    expect(list).toHaveLength(20);
    // Oldest (s0–s4) should be dropped; newest (s5–s24) should remain
    expect(list[0].id).toBe("s5");
    expect(list[19].id).toBe("s24");
  });

  it("getSavedScenarios returns empty array on corrupted JSON (never throws)", () => {
    localStorage.setItem(SAVED_SCENARIOS_KEY, "{bad json");
    const { getSavedScenarios } = getHook();
    expect(() => getSavedScenarios()).not.toThrow();
    expect(getSavedScenarios()).toEqual([]);
  });

  it("multiple different scenarios are all stored", () => {
    const { saveScenarioToList, getSavedScenarios } = getHook();
    saveScenarioToList(makeScenario({ id: "a" }));
    saveScenarioToList(makeScenario({ id: "b" }));
    saveScenarioToList(makeScenario({ id: "c" }));
    expect(getSavedScenarios()).toHaveLength(3);
  });
});

// ============================================================================
// Key constants
// ============================================================================

describe("exported key constants", () => {
  it("SCENARIO_STORAGE_KEY is 'reformlab-active-scenario'", () => {
    expect(SCENARIO_STORAGE_KEY).toBe("reformlab-active-scenario");
  });

  it("STAGE_STORAGE_KEY is 'reformlab-active-stage'", () => {
    expect(STAGE_STORAGE_KEY).toBe("reformlab-active-stage");
  });

  it("SAVED_SCENARIOS_KEY is 'reformlab-saved-scenarios'", () => {
    expect(SAVED_SCENARIOS_KEY).toBe("reformlab-saved-scenarios");
  });

  it("HAS_LAUNCHED_KEY is 'reformlab-has-launched'", () => {
    expect(HAS_LAUNCHED_KEY).toBe("reformlab-has-launched");
  });
});
