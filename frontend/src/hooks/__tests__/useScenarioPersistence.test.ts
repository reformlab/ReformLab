// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for useScenarioPersistence hook.
 * Story 20.2 — Task 2, Task 7.2.
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

// ============================================================================
// Helpers
// ============================================================================

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
    engineConfig: { startYear: 2025, endYear: 2030, seed: 42, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 },
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
    const scenario = makeScenario({ engineConfig: { startYear: 2026, endYear: 2035, seed: 99, investmentDecisionsEnabled: true, logitModel: "multinomial_logit", discountRate: 0.05 } });
    saveScenario(scenario);
    const loaded = loadScenario();
    expect(loaded?.engineConfig.seed).toBe(99);
    expect(loaded?.engineConfig.investmentDecisionsEnabled).toBe(true);
  });
});

// ============================================================================
// saveStage / loadStage
// ============================================================================

describe("saveStage / loadStage", () => {
  it("round-trip preserves stage key", () => {
    const { saveStage, loadStage } = getHook();
    saveStage("engine");
    expect(loadStage()).toBe("engine");
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
