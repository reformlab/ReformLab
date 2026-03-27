// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for the demo scenario factory.
 * Story 20.2 — Task 1.4, Task 7.1.
 */

import { describe, expect, it } from "vitest";

import {
  createDemoScenario,
  DEMO_POPULATION_ID,
  DEMO_SCENARIO_ID,
  DEMO_TEMPLATE_ID,
} from "@/data/demo-scenario";

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

  it("populationIds includes DEMO_POPULATION_ID", () => {
    const scenario = createDemoScenario();
    expect(scenario.populationIds).toContain(DEMO_POPULATION_ID);
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

  it("returns a new object on each call (not a shared reference)", () => {
    const a = createDemoScenario();
    const b = createDemoScenario();
    expect(a).not.toBe(b);
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
