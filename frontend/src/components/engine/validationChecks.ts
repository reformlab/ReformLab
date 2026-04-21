// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Cross-stage validation check registry for the Scenario preflight gate.
 *
 * Each ValidationCheck has an id, label, severity, and fn.
 * EPIC-21 Story 21.5 appends trust-status checks to VALIDATION_CHECKS
 * without modifying this file or ValidationGate.
 *
 * Story 20.5 — AC-3, AC-5.
 */

import { checkMemory } from "@/api/runs";
import type { WorkspaceScenario } from "@/types/workspace";
import type { GenerationResult, PortfolioListItem } from "@/api/types";
import type { Population } from "@/data/mock-data";

// ============================================================================
// Types
// ============================================================================

export interface ValidationCheckResult {
  passed: boolean;
  message: string;  // shown when not passed; empty string when passed
  severity: "error" | "warning";
}

export interface ValidationContext {
  scenario: WorkspaceScenario | null;
  populations: Population[];
  dataFusionResult: GenerationResult | null;
  portfolios: PortfolioListItem[];
}

export interface ValidationCheck {
  id: string;
  label: string;
  severity: "error" | "warning";
  fn: (ctx: ValidationContext) => ValidationCheckResult | Promise<ValidationCheckResult>;
}

// ============================================================================
// Built-in checks
// ============================================================================

const portfolioSelectedCheck: ValidationCheck = {
  id: "portfolio-selected",
  label: "Portfolio selected",
  severity: "error",
  fn: (ctx) => {
    const passed = typeof ctx.scenario?.portfolioName === "string" && ctx.scenario.portfolioName.length > 0;
    return {
      passed,
      message: passed ? "" : "No portfolio selected. Go to Stage 1 to compose a portfolio.",
      severity: "error",
    };
  },
};

const populationSelectedCheck: ValidationCheck = {
  id: "population-selected",
  label: "Population selected",
  severity: "error",
  fn: (ctx) => {
    const passed = (ctx.scenario?.populationIds ?? []).some((id) => id.trim().length > 0);
    return {
      passed,
      message: passed ? "" : "No population selected. Go to Stage 2 to select a population.",
      severity: "error",
    };
  },
};

const timeHorizonValidCheck: ValidationCheck = {
  id: "time-horizon-valid",
  label: "Time horizon valid",
  severity: "error",
  fn: (ctx) => {
    const cfg = ctx.scenario?.engineConfig;
    if (!cfg) {
      return { passed: false, message: "No scenario configuration.", severity: "error" };
    }
    const { startYear, endYear } = cfg;
    if (startYear >= endYear) {
      return { passed: false, message: "End year must be greater than start year.", severity: "error" };
    }
    if (endYear - startYear > 50) {
      return { passed: false, message: "Time horizon exceeds 50 years — reduce the range.", severity: "error" };
    }
    return { passed: true, message: "", severity: "error" };
  },
};

const investmentDecisionsCalibratedCheck: ValidationCheck = {
  id: "investment-decisions-calibrated",
  label: "Investment decisions calibrated",
  severity: "warning",
  fn: (ctx) => {
    const enabled = ctx.scenario?.engineConfig.investmentDecisionsEnabled ?? false;
    if (!enabled) {
      return { passed: true, message: "", severity: "warning" };
    }
    // Enabled but calibration status is "not_configured" (stub — always not configured in Story 20.5)
    return {
      passed: false,
      message: "Investment decisions are enabled but calibration is not configured. Results will use uncalibrated taste parameters.",
      severity: "warning",
    };
  },
};

// Story 22.6: Logit model required when investment decisions enabled
const logitModelRequiredCheck: ValidationCheck = {
  id: "logit-model-required",
  label: "Logit model selected",
  severity: "error",
  fn: (ctx) => {
    const enabled = ctx.scenario?.engineConfig.investmentDecisionsEnabled ?? false;
    if (!enabled) {
      return { passed: true, message: "", severity: "error" };
    }
    const model = ctx.scenario?.engineConfig.logitModel;
    const allowedModels = ["multinomial_logit", "nested_logit", "mixed_logit"] as const;
    const hasValidModel = model != null && allowedModels.includes(model);
    if (!hasValidModel) {
      return {
        passed: false,
        message: "Investment decisions require a logit model. Configure in Stage 3.",
        severity: "error",
      };
    }
    return { passed: true, message: "", severity: "error" };
  },
};

// Story 22.6: Taste parameters required when investment decisions enabled
const tasteParametersRequiredCheck: ValidationCheck = {
  id: "taste-parameters-required",
  label: "Taste parameters configured",
  severity: "error",
  fn: (ctx) => {
    const enabled = ctx.scenario?.engineConfig.investmentDecisionsEnabled ?? false;
    if (!enabled) {
      return { passed: true, message: "", severity: "error" };
    }
    const params = ctx.scenario?.engineConfig.tasteParameters;
    if (!params) {
      return {
        passed: false,
        message: "Investment decisions require taste parameters. Configure in Stage 3.",
        severity: "error",
      };
    }
    // Check all required fields exist and are within valid bounds
    const { priceSensitivity, rangeAnxiety, envPreference } = params;
    const hasPriceSensitivity = Number.isFinite(priceSensitivity) && priceSensitivity >= -5 && priceSensitivity <= 0;
    const hasRangeAnxiety = Number.isFinite(rangeAnxiety) && rangeAnxiety >= -3 && rangeAnxiety <= 0;
    const hasEnvPreference = Number.isFinite(envPreference) && envPreference >= 0 && envPreference <= 3;

    if (!hasPriceSensitivity || !hasRangeAnxiety || !hasEnvPreference) {
      return {
        passed: false,
        message: "Investment decisions require taste parameters. Configure in Stage 3.",
        severity: "error",
      };
    }
    return { passed: true, message: "", severity: "error" };
  },
};

const memoryPreflightCheck: ValidationCheck = {
  id: "memory-preflight",
  label: "Memory preflight",
  severity: "error",
  fn: async (ctx) => {
    if (!ctx.scenario) return { passed: true, message: "", severity: "error" };
    const { engineConfig, populationIds, policyType } = ctx.scenario;
    try {
      const resp = await checkMemory({
        template_name: policyType ?? "",
        start_year: engineConfig.startYear,
        end_year: engineConfig.endYear,
        population_id: populationIds[0] ?? null,
      });
      return {
        passed: !resp.should_warn,
        message: resp.should_warn ? resp.message : "",
        severity: "error",
      };
    } catch {
      // API unavailable → do not block execution
      return { passed: true, message: "", severity: "error" };
    }
  },
};

// ============================================================================
// Registry (extensible — EPIC-21 appends at import-time)
// ============================================================================

export const VALIDATION_CHECKS: ValidationCheck[] = [
  portfolioSelectedCheck,
  populationSelectedCheck,
  timeHorizonValidCheck,
  logitModelRequiredCheck,  // Story 22.6
  tasteParametersRequiredCheck,  // Story 22.6
  investmentDecisionsCalibratedCheck,
  memoryPreflightCheck,
];

// Export individual checks for unit testing
export {
  portfolioSelectedCheck,
  populationSelectedCheck,
  timeHorizonValidCheck,
  logitModelRequiredCheck,  // Story 22.6
  tasteParametersRequiredCheck,  // Story 22.6
  investmentDecisionsCalibratedCheck,
  memoryPreflightCheck,
};
