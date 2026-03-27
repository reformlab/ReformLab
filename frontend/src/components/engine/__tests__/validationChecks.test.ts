// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for validation check registry.
 * Story 20.5 — AC-3, AC-5.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  portfolioSelectedCheck,
  populationSelectedCheck,
  timeHorizonValidCheck,
  investmentDecisionsCalibratedCheck,
  memoryPreflightCheck,
  type ValidationContext,
} from "../validationChecks";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/api/runs", () => ({
  checkMemory: vi.fn(),
}));

import { checkMemory } from "@/api/runs";

// ============================================================================
// Helpers
// ============================================================================

function makeContext(overrides: Partial<ValidationContext> = {}): ValidationContext {
  return {
    scenario: null,
    populations: [],
    dataFusionResult: null,
    portfolios: [],
    ...overrides,
  };
}

function makeScenario(overrides: Record<string, unknown> = {}) {
  return {
    id: "s1",
    name: "Test",
    version: "1.0",
    status: "draft",
    isBaseline: false,
    baselineRef: null,
    portfolioName: "My Portfolio",
    populationIds: ["fr-synthetic-2024"],
    engineConfig: {
      startYear: 2025,
      endYear: 2030,
      seed: null,
      investmentDecisionsEnabled: false,
      logitModel: null,
      discountRate: 0.03,
    },
    policyType: "carbon-tax",
    lastRunId: null,
    ...overrides,
  } as ValidationContext["scenario"] & { [k: string]: unknown };
}

// ============================================================================
// portfolioSelectedCheck
// ============================================================================

describe("portfolioSelectedCheck", () => {
  it("passes when portfolioName is set", () => {
    const ctx = makeContext({ scenario: makeScenario() });
    const result = portfolioSelectedCheck.fn(ctx) as ReturnType<typeof portfolioSelectedCheck.fn>;
    expect(result).toEqual({ passed: true, message: "", severity: "error" });
  });

  it("fails when portfolioName is null", () => {
    const ctx = makeContext({ scenario: makeScenario({ portfolioName: null }) });
    const result = portfolioSelectedCheck.fn(ctx) as ReturnType<typeof portfolioSelectedCheck.fn>;
    expect(result.passed).toBe(false);
    expect(result.severity).toBe("error");
    expect(result.message).toMatch(/portfolio/i);
  });

  it("fails when portfolioName is empty string", () => {
    const ctx = makeContext({ scenario: makeScenario({ portfolioName: "" }) });
    const result = portfolioSelectedCheck.fn(ctx) as ReturnType<typeof portfolioSelectedCheck.fn>;
    expect(result.passed).toBe(false);
  });

  it("fails when scenario is null", () => {
    const ctx = makeContext({ scenario: null });
    const result = portfolioSelectedCheck.fn(ctx) as ReturnType<typeof portfolioSelectedCheck.fn>;
    expect(result.passed).toBe(false);
  });
});

// ============================================================================
// populationSelectedCheck
// ============================================================================

describe("populationSelectedCheck", () => {
  it("passes when populationIds has at least one entry", () => {
    const ctx = makeContext({ scenario: makeScenario({ populationIds: ["fr-2024"] }) });
    const result = populationSelectedCheck.fn(ctx) as ReturnType<typeof populationSelectedCheck.fn>;
    expect(result.passed).toBe(true);
  });

  it("fails when populationIds is empty", () => {
    const ctx = makeContext({ scenario: makeScenario({ populationIds: [] }) });
    const result = populationSelectedCheck.fn(ctx) as ReturnType<typeof populationSelectedCheck.fn>;
    expect(result.passed).toBe(false);
    expect(result.severity).toBe("error");
  });

  it("fails when scenario is null", () => {
    const ctx = makeContext();
    const result = populationSelectedCheck.fn(ctx) as ReturnType<typeof populationSelectedCheck.fn>;
    expect(result.passed).toBe(false);
  });
});

// ============================================================================
// timeHorizonValidCheck
// ============================================================================

describe("timeHorizonValidCheck", () => {
  it("passes for valid range (startYear < endYear, ≤50 years)", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 } }) });
    const result = timeHorizonValidCheck.fn(ctx) as ReturnType<typeof timeHorizonValidCheck.fn>;
    expect(result.passed).toBe(true);
  });

  it("fails when startYear >= endYear", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2030, endYear: 2025, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 } }) });
    const result = timeHorizonValidCheck.fn(ctx) as ReturnType<typeof timeHorizonValidCheck.fn>;
    expect(result.passed).toBe(false);
    expect(result.message).toMatch(/end year/i);
  });

  it("fails when startYear === endYear", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2025, endYear: 2025, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 } }) });
    const result = timeHorizonValidCheck.fn(ctx) as ReturnType<typeof timeHorizonValidCheck.fn>;
    expect(result.passed).toBe(false);
  });

  it("fails when range exceeds 50 years", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2025, endYear: 2080, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 } }) });
    const result = timeHorizonValidCheck.fn(ctx) as ReturnType<typeof timeHorizonValidCheck.fn>;
    expect(result.passed).toBe(false);
    expect(result.message).toMatch(/50/);
  });

  it("passes for exactly 50 years", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2025, endYear: 2075, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 } }) });
    const result = timeHorizonValidCheck.fn(ctx) as ReturnType<typeof timeHorizonValidCheck.fn>;
    expect(result.passed).toBe(true);
  });
});

// ============================================================================
// investmentDecisionsCalibratedCheck
// ============================================================================

describe("investmentDecisionsCalibratedCheck", () => {
  it("passes (no warning) when investment decisions are disabled", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 } }) });
    const result = investmentDecisionsCalibratedCheck.fn(ctx) as ReturnType<typeof investmentDecisionsCalibratedCheck.fn>;
    expect(result.passed).toBe(true);
  });

  it("is a warning (not error) when investment decisions are enabled", () => {
    const ctx = makeContext({ scenario: makeScenario({ engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: true, logitModel: "multinomial_logit", discountRate: 0.03 } }) });
    const result = investmentDecisionsCalibratedCheck.fn(ctx) as ReturnType<typeof investmentDecisionsCalibratedCheck.fn>;
    expect(result.passed).toBe(false);
    expect(result.severity).toBe("warning");
    expect(result.message).toMatch(/calibration/i);
  });

  it("passes when scenario is null (investment decisions cannot be enabled)", () => {
    const ctx = makeContext();
    const result = investmentDecisionsCalibratedCheck.fn(ctx) as ReturnType<typeof investmentDecisionsCalibratedCheck.fn>;
    expect(result.passed).toBe(true);
  });
});

// ============================================================================
// memoryPreflightCheck
// ============================================================================

describe("memoryPreflightCheck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes when should_warn is false", async () => {
    vi.mocked(checkMemory).mockResolvedValueOnce({
      should_warn: false,
      estimated_gb: 2.0,
      available_gb: 16.0,
      message: "",
    });
    const ctx = makeContext({ scenario: makeScenario() });
    const result = await memoryPreflightCheck.fn(ctx);
    expect(result.passed).toBe(true);
    expect(checkMemory).toHaveBeenCalledWith({
      template_name: "carbon-tax",
      start_year: 2025,
      end_year: 2030,
      population_id: "fr-synthetic-2024",
    });
  });

  it("fails when should_warn is true", async () => {
    vi.mocked(checkMemory).mockResolvedValueOnce({
      should_warn: true,
      estimated_gb: 14.0,
      available_gb: 16.0,
      message: "Estimated memory may be insufficient",
    });
    const ctx = makeContext({ scenario: makeScenario() });
    const result = await memoryPreflightCheck.fn(ctx);
    expect(result.passed).toBe(false);
    expect(result.message).toBe("Estimated memory may be insufficient");
    expect(result.severity).toBe("error");
  });

  it("returns passed:true on API error (graceful degradation)", async () => {
    vi.mocked(checkMemory).mockRejectedValueOnce(new Error("Network error"));
    const ctx = makeContext({ scenario: makeScenario() });
    const result = await memoryPreflightCheck.fn(ctx);
    expect(result.passed).toBe(true);
    expect(result.message).toBe("");
  });

  it("returns passed:true when scenario is null", async () => {
    const ctx = makeContext({ scenario: null });
    const result = await memoryPreflightCheck.fn(ctx);
    expect(result.passed).toBe(true);
    expect(checkMemory).not.toHaveBeenCalled();
  });
});
