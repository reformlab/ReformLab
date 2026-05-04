// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for the demo scenario factory.
 * Story 20.2 — Task 1.4, Task 7.1.
 */

import { describe, expect, it, beforeEach } from "vitest";

import {
  createDemoScenario,
  DEMO_POPULATION_ID,
  DEMO_SCENARIO_ID,
  DEMO_TEMPLATE_ID,
} from "@/data/demo-scenario";
import { loadScenario } from "@/hooks/useScenarioPersistence";
import { SCENARIO_STORAGE_KEY } from "@/hooks/useScenarioPersistence";

describe("createDemoScenario", () => {
  it("returns a WorkspaceScenario with id === DEMO_SCENARIO_ID", () => {
    const scenario = createDemoScenario();
    expect(scenario.id).toBe(DEMO_SCENARIO_ID);
  });

  it("has engineConfig.startYear === 2025 and endYear === 2030", () => {
    const { engineConfig } = createDemoScenario();
    expect(engineConfig.startYear).toBe(2025);
    expect(engineConfig.endYear).toBe(2030);
  });

  it("satisfies startYear < endYear", () => {
    const { engineConfig } = createDemoScenario();
    expect(engineConfig.startYear).toBeLessThan(engineConfig.endYear);
  });

  it("populationIds is EMPTY (Story 27.6: not pre-filled)", () => {
    const scenario = createDemoScenario();
    expect(scenario.populationIds).toEqual([]);
  });

  it("policyType is 'carbon-tax'", () => {
    const scenario = createDemoScenario();
    expect(scenario.policyType).toBe("carbon-tax");
  });

  it("status is 'ready'", () => {
    const scenario = createDemoScenario();
    expect(scenario.status).toBe("ready");
  });

  it("all required fields are defined", () => {
    const scenario = createDemoScenario();
    expect(scenario.id).toBeDefined();
    expect(scenario.name).toBeDefined();
    expect(scenario.version).toBeDefined();
    expect(scenario.status).toBeDefined();
    expect(scenario.engineConfig).toBeDefined();
    expect(scenario.populationIds).toBeDefined();
    expect(scenario.policyType).toBeDefined();
  });

  it("portfolioName is null (template-based run, no portfolio required)", () => {
    const scenario = createDemoScenario();
    expect(scenario.portfolioName).toBeNull();
  });

  it("lastRunId is null on fresh demo scenario", () => {
    const scenario = createDemoScenario();
    expect(scenario.lastRunId).toBeNull();
  });

  it("seed is 42 (deterministic)", () => {
    const { engineConfig } = createDemoScenario();
    expect(engineConfig.seed).toBe(42);
  });

  it("investmentDecisionsEnabled is NULL (Story 27.6: not started)", () => {
    const { engineConfig } = createDemoScenario();
    expect(engineConfig.investmentDecisionsEnabled).toBeNull();
  });

  it("returns a new object on each call (not a shared reference)", () => {
    const a = createDemoScenario();
    const b = createDemoScenario();
    expect(a).not.toBe(b);
  });
});

// ============================================================================
// Story 27.6: Demo scenario changes — not started state
// ============================================================================

describe("createDemoScenario - Story 27.6 changes", () => {
  it("populationIds is EMPTY array (not pre-filled)", () => {
    const scenario = createDemoScenario();
    expect(scenario.populationIds).toEqual([]);
  });

  it("investmentDecisionsEnabled is NULL (not false)", () => {
    const { engineConfig } = createDemoScenario();
    expect(engineConfig.investmentDecisionsEnabled).toBeNull();
  });

  it("stageTouched is EMPTY object (no stages pre-touched)", () => {
    const scenario = createDemoScenario();
    expect(scenario.stageTouched).toEqual({});
  });

  it("all other fields remain valid for demo scenario", () => {
    const scenario = createDemoScenario();
    expect(scenario.id).toBe(DEMO_SCENARIO_ID);
    expect(scenario.policyType).toBe("carbon-tax");
    expect(scenario.portfolioName).toBeNull();
    expect(scenario.lastRunId).toBeNull();
  });
});

describe("constants", () => {
  it("DEMO_SCENARIO_ID is a non-empty string", () => {
    expect(typeof DEMO_SCENARIO_ID).toBe("string");
    expect(DEMO_SCENARIO_ID.length).toBeGreaterThan(0);
  });

  it("DEMO_TEMPLATE_ID is 'carbon-tax-dividend'", () => {
    expect(DEMO_TEMPLATE_ID).toBe("carbon-tax-dividend");
  });

  it("DEMO_POPULATION_ID is 'fr-synthetic-2024'", () => {
    expect(DEMO_POPULATION_ID).toBe("fr-synthetic-2024");
  });
});

// ============================================================================
// Story 27.6: Migration tests for legacy investmentDecisionsEnabled state
// ============================================================================

describe("loadScenario - Story 27.6 migration", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("migrates legacy investmentDecisionsEnabled: false to stageTouched.engine: true", () => {
    const legacyScenario = {
      id: "s1",
      name: "Legacy Scenario",
      version: "1.0",
      status: "ready",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: [],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: null,
        investmentDecisionsEnabled: false, // Legacy: explicit false
        logitModel: null,
        discountRate: 0.03,
      },
      policyType: null,
      lastRunId: null,
    };
    localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(legacyScenario));

    const loaded = loadScenario();

    expect(loaded).not.toBeNull();
    expect(loaded?.stageTouched?.engine).toBe(true);
  });

  it("does NOT set stageTouched.engine when investmentDecisionsEnabled is null (new scenario)", () => {
    const newScenario = {
      id: "s1",
      name: "New Scenario",
      version: "1.0",
      status: "ready",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: [],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: null,
        investmentDecisionsEnabled: null, // New: null
        logitModel: null,
        discountRate: 0.03,
      },
      policyType: null,
      lastRunId: null,
      stageTouched: {}, // Already has stageTouched field
    };
    localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(newScenario));

    const loaded = loadScenario();

    expect(loaded).not.toBeNull();
    expect(loaded?.stageTouched?.engine).toBeUndefined();
  });
});
