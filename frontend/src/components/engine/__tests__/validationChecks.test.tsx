// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for validation checks — Story 22.6.
 *
 * Tests:
 * - AC-3: Logit model required when investment decisions enabled
 * - AC-3: Taste parameters required when investment decisions enabled
 * - AC-2: Both checks pass when investment decisions disabled
 */

import { describe, expect, it } from "vitest";
import {
  logitModelRequiredCheck,
  tasteParametersRequiredCheck,
} from "../validationChecks";
import type { ValidationContext } from "../validationChecks";
import { DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// Helpers
// ============================================================================

function makeContext(overrides: Partial<ValidationContext["scenario"]> = {}): ValidationContext {
  return {
    scenario: {
      id: "test-id",
      name: "Test Scenario",
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: "Test Portfolio",
      populationIds: ["fr-synthetic-2024"],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: null,
        investmentDecisionsEnabled: false,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,
        calibrationState: "not_configured",
      },
      policyType: "carbon-tax",
      lastRunId: null,
      ...overrides,
    },
    populations: [],
    dataFusionResult: null,
    portfolios: [],
  };
}

// ============================================================================
// Tests
// ============================================================================

describe("validationChecks — Story 22.6", () => {
  describe("logitModelRequiredCheck", () => {
    it("passes when investment decisions disabled", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: false,
          logitModel: null,
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const result = logitModelRequiredCheck.fn(ctx);
      expect(result.passed).toBe(true);
      expect(result.message).toBe("");
    });

    it("passes when investment decisions enabled with model selected", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const result = logitModelRequiredCheck.fn(ctx);
      expect(result.passed).toBe(true);
      expect(result.message).toBe("");
    });

    it("errors when investment decisions enabled without model", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: null,
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const result = logitModelRequiredCheck.fn(ctx);
      expect(result.passed).toBe(false);
      expect(result.message).toBe("Investment decisions require a logit model to be selected.");
      expect(result.severity).toBe("error");
    });
  });

  describe("tasteParametersRequiredCheck", () => {
    it("passes when investment decisions disabled", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: false,
          logitModel: null,
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const result = tasteParametersRequiredCheck.fn(ctx);
      expect(result.passed).toBe(true);
      expect(result.message).toBe("");
    });

    it("passes when investment decisions enabled with valid taste parameters", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          discountRate: 0.03,
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
          calibrationState: "not_configured",
        },
      });
      const result = tasteParametersRequiredCheck.fn(ctx);
      expect(result.passed).toBe(true);
      expect(result.message).toBe("");
    });

    it("errors when investment decisions enabled with null taste parameters", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const result = tasteParametersRequiredCheck.fn(ctx);
      expect(result.passed).toBe(false);
      expect(result.message).toBe("Investment decisions require taste parameters to be configured.");
      expect(result.severity).toBe("error");
    });

    it("errors when investment decisions enabled with missing taste parameter fields", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          discountRate: 0.03,
          tasteParameters: { priceSensitivity: -1.5, rangeAnxiety: -0.8, envPreference: undefined as unknown as number },
          calibrationState: "not_configured",
        },
      });
      const result = tasteParametersRequiredCheck.fn(ctx);
      expect(result.passed).toBe(false);
      expect(result.message).toBe("Investment decisions require taste parameters to be configured.");
    });

    it("errors when investment decisions enabled with out-of-bounds values", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          discountRate: 0.03,
          tasteParameters: { priceSensitivity: -10, rangeAnxiety: -0.8, envPreference: 0.5 }, // priceSensitivity out of bounds
          calibrationState: "not_configured",
        },
      });
      const result = tasteParametersRequiredCheck.fn(ctx);
      expect(result.passed).toBe(false);
      expect(result.message).toBe("Investment decisions require taste parameters to be configured.");
    });

    it("accepts all values within slider bounds", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          discountRate: 0.03,
          tasteParameters: { priceSensitivity: -5, rangeAnxiety: -3, envPreference: 3 }, // all at bounds
          calibrationState: "not_configured",
        },
      });
      const result = tasteParametersRequiredCheck.fn(ctx);
      expect(result.passed).toBe(true);
      expect(result.message).toBe("");
    });
  });

  describe("Integration: both checks together", () => {
    it("both pass when investment decisions disabled", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: false,
          logitModel: null,
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const modelResult = logitModelRequiredCheck.fn(ctx);
      const paramsResult = tasteParametersRequiredCheck.fn(ctx);
      expect(modelResult.passed).toBe(true);
      expect(paramsResult.passed).toBe(true);
    });

    it("both pass when enabled with valid model and parameters", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: "mixed_logit",
          discountRate: 0.03,
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
          calibrationState: "not_configured",
        },
      });
      const modelResult = logitModelRequiredCheck.fn(ctx);
      const paramsResult = tasteParametersRequiredCheck.fn(ctx);
      expect(modelResult.passed).toBe(true);
      expect(paramsResult.passed).toBe(true);
    });

    it("both fail when enabled without model or parameters", () => {
      const ctx = makeContext({
        engineConfig: {
          startYear: 2025,
          endYear: 2030,
          seed: null,
          investmentDecisionsEnabled: true,
          logitModel: null,
          discountRate: 0.03,
          tasteParameters: null,
          calibrationState: "not_configured",
        },
      });
      const modelResult = logitModelRequiredCheck.fn(ctx);
      const paramsResult = tasteParametersRequiredCheck.fn(ctx);
      expect(modelResult.passed).toBe(false);
      expect(paramsResult.passed).toBe(false);
    });
  });
});
