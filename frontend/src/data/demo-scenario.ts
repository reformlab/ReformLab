// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Pre-seeded demo scenario for ReformLab first-launch onboarding.
 *
 * The demo uses the "Carbon Tax + Dividend" template (FR34 quickstart) —
 * the flagship example that produces a visually compelling distributional chart.
 *
 * Story 20.2 — AC-1, AC-4.
 */

import type { WorkspaceScenario } from "@/types/workspace";
import { DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// Constants
// ============================================================================

export const DEMO_SCENARIO_ID = "demo-carbon-tax-dividend";

/** Template ID matching mockTemplates entry and OpenFisca policy type. */
export const DEMO_TEMPLATE_ID = "carbon-tax-dividend";

/** Population ID always present in mockPopulations. */
export const DEMO_POPULATION_ID = "fr-synthetic-2024";

// ============================================================================
// Factory
// ============================================================================

/** Create a fresh demo WorkspaceScenario with deterministic seed 42.
 * Story 27.6: Demo no longer pre-fills decisions; populationIds is empty,
 * investmentDecisionsEnabled is null (not started), stageTouched is empty.
 */
export function createDemoScenario(): WorkspaceScenario {
  return {
    id: DEMO_SCENARIO_ID,
    name: "Demo \u2014 Carbon Tax + Dividend",
    version: "1.0",
    status: "ready",
    isBaseline: false,
    baselineRef: null,
    portfolioName: null,
    populationIds: [],  // Story 27.6: Empty (not pre-filled)
    engineConfig: {
      startYear: 2025,
      endYear: 2030,
      seed: 42,
      investmentDecisionsEnabled: null,  // Story 27.6: null (not started) instead of false
      logitModel: null,
      discountRate: 0.03,
      tasteParameters: DEFAULT_TASTE_PARAMETERS,  // Story 22.6
      calibrationState: "not_configured",  // Story 22.6
    },
    policyType: "carbon-tax",
    lastRunId: null,
    stageTouched: {},  // Story 27.6: No stages pre-touched
  };
}

/** Create the pre-filled demo state for "Try the demo" affordance (Story 27.6).
 * This restores the old first-launch shortcuts that matter for this story:
 * population pre-selected and investment decisions explicitly skipped.
 *
 * It does not fabricate a saved policy set or a completed run history.
 */
export function createFullDemoScenario(): WorkspaceScenario {
  return {
    id: DEMO_SCENARIO_ID,
    name: "Demo \u2014 Carbon Tax + Dividend",
    version: "1.0",
    status: "ready",
    isBaseline: false,
    baselineRef: null,
    portfolioName: null,
    populationIds: [DEMO_POPULATION_ID],  // Pre-selected population
    engineConfig: {
      startYear: 2025,
      endYear: 2030,
      seed: 42,
      investmentDecisionsEnabled: false,  // Explicitly skipped
      logitModel: null,
      discountRate: 0.03,
      tasteParameters: DEFAULT_TASTE_PARAMETERS,
      calibrationState: "not_configured",
    },
    policyType: "carbon-tax",
    lastRunId: null,
    stageTouched: {
      // Mark the stages this affordance explicitly pre-fills.
      population: true,
      engine: true,
    },
  };
}
