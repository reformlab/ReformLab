// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Test data fixtures for E2E workflow tests (Story 20.8).
 *
 * Provides consistent test data across all E2E tests:
 * - Demo scenario configuration
 * - Portfolio configurations for editing flow
 * - Population references
 * - CSV fixture for upload flow
 *
 * Story 20.8 — AC-1, AC-3.
 */

import type { WorkspaceScenario } from "@/types/workspace";

import { createDemoScenario, DEMO_POPULATION_ID, DEMO_TEMPLATE_ID } from "@/data/demo-scenario";

// ============================================================================
// Scenario fixtures
// ============================================================================

/**
 * Demo scenario configuration matching first-launch behavior.
 * Use this when testing the demo scenario flow.
 */
export const demoScenarioConfig = createDemoScenario();

/**
 * Minimal portfolio configuration for editing flow tests.
 * Two-policy portfolio for conflict validation testing.
 */
export const testPortfolioConfig = {
  name: "Test Portfolio",
  policies: [
    {
      templateName: "carbon-tax",
      parameters: { carbon_tax_rate: 100 },
    },
    {
      templateName: "subsidy-rebate",
      parameters: { rebate_amount: 500 },
    },
  ],
};

/**
 * Single-policy portfolio for simple editing tests.
 */
export const singlePolicyConfig = {
  name: "Single Policy Test",
  policies: [
    {
      templateName: "carbon-tax",
      parameters: { carbon_tax_rate: 50 },
    },
  ],
};

/**
 * Portfolio with parameter conflicts for validation testing.
 * Two policies both setting the same parameter with different values.
 */
export const conflictingPortfolioConfig = {
  name: "Conflicting Portfolio",
  policies: [
    {
      templateName: "carbon-tax",
      parameters: { carbon_tax_rate: 100 },
    },
    {
      templateName: "carbon-tax", // Same template = conflict
      parameters: { carbon_tax_rate: 150 }, // Different rate = conflict
    },
  ],
};

// ============================================================================
// Scenario factory fixtures
// ============================================================================

/**
 * Create a test scenario with minimal valid configuration.
 * Generates unique ID using timestamp to avoid collisions.
 */
export function createTestScenario(overrides?: Partial<WorkspaceScenario>): WorkspaceScenario {
  const timestamp = Date.now();
  return {
    id: `test-scenario-${timestamp}`,
    name: `Test Scenario ${timestamp}`,
    version: "1.0",
    status: "ready",
    isBaseline: false,
    baselineRef: null,
    portfolioName: null,
    populationIds: [DEMO_POPULATION_ID],
    engineConfig: {
      startYear: 2025,
      endYear: 2030,
      seed: 42,
      investmentDecisionsEnabled: false,
      logitModel: null,
      discountRate: 0.03,
    },
    policyType: "carbon-tax",
    lastRunId: null,
    ...overrides,
  };
}

/**
 * Create a scenario with a portfolio for portfolio-editing flow tests.
 */
export function createPortfolioScenario(
  portfolioName: string,
  overrides?: Partial<WorkspaceScenario>,
): WorkspaceScenario {
  return createTestScenario({
    portfolioName,
    policyType: null, // Portfolios don't set single policyType
    ...overrides,
  });
}

// ============================================================================
// Population fixtures
// ============================================================================

/**
 * Built-in test population ID.
 * Always available in mockPopulations.
 */
export const testPopulationId = DEMO_POPULATION_ID;

/**
 * Additional population IDs for multi-population tests.
 * These match mock population data from Story 20.4.
 */
export const secondaryPopulationIds = [
  "fr-synthetic-2025",
  "eu-synthetic-2024",
];

/**
 * All available test population IDs.
 */
export const allTestPopulationIds = [
  testPopulationId,
  ...secondaryPopulationIds,
];

// ============================================================================
// File upload fixtures
// ============================================================================

/**
 * Minimal CSV fixture for upload flow testing.
 * Contains required columns: household_id, income, region.
 *
 * Story 20.8 note: Upload tests are BLOCKED until Story 20.7 complete.
 * This fixture is ready for when the upload endpoint exists.
 */
export const testUploadCsv = `household_id,income,region
1,50000,North
2,60000,South
3,55000,East
4,65000,West
5,70000,North
`;

/**
 * CSV fixture with additional columns for validation testing.
 */
export const testUploadCsvExtra = `household_id,income,region,age,household_size
1,50000,North,35,2
2,60000,South,42,3
3,55000,East,28,1
4,65000,West,55,2
5,70000,North,31,4
`;

/**
 * CSV fixture with invalid data for error handling tests.
 * Missing required column (income) and invalid region.
 */
export const testUploadCsvInvalid = `household_id,region
1,InvalidRegion
2,North
3,Moon
`;

/**
 * Create a File object from CSV content for upload testing.
 * Simulates a user selecting a file from their filesystem.
 */
export function createCsvFile(content: string, filename = "test-population.csv"): File {
  const blob = new Blob([content], { type: "text/csv" });
  return new File([blob], filename, { type: "text/csv" });
}

// ============================================================================
// Engine configuration fixtures
// ============================================================================

/**
 * Default engine configuration for tests.
 */
export const defaultEngineConfig = {
  startYear: 2025,
  endYear: 2030,
  seed: 42,
  investmentDecisionsEnabled: false,
  logitModel: null,
  discountRate: 0.03,
};

/**
 * Alternative engine configuration for parameter testing.
 */
export const alternativeEngineConfig = {
  startYear: 2026,
  endYear: 2035,
  seed: 123,
  investmentDecisionsEnabled: false,
  logitModel: null,
  discountRate: 0.04,
};

/**
 * Engine config with investment decisions enabled (for future testing).
 */
export const investmentEngineConfig = {
  startYear: 2025,
  endYear: 2030,
  seed: 42,
  investmentDecisionsEnabled: true,
  logitModel: "multinomial_logit" as const,
  discountRate: 0.03,
};

// ============================================================================
// Expected result fixtures
// ============================================================================

/**
 * Expected lineage fields for run result assertions.
 * When Story 20.6 is complete, these should be present in ResultDetailResponse.
 */
export const expectedLineageFields = {
  scenario_id: demoScenarioConfig.id,
  scenario_name: demoScenarioConfig.name,
  portfolio_name: demoScenarioConfig.portfolioName,
  population_id: DEMO_POPULATION_ID,
  start_year: demoScenarioConfig.engineConfig.startYear,
  end_year: demoScenarioConfig.engineConfig.endYear,
  seed: demoScenarioConfig.engineConfig.seed,
};

/**
 * Expected comparison warning for cross-population comparisons.
 * Story 20.6 specifies this warning message.
 */
export const crossPopulationWarning =
  "Comparing runs from different populations. Results may not be directly comparable.";

// ============================================================================
// Re-exports for convenience
// ============================================================================

/**
 * Re-export demo scenario constants for easy import.
 */
export const DEMO_CONSTANTS = {
  SCENARIO_ID: demoScenarioConfig.id,
  TEMPLATE_ID: DEMO_TEMPLATE_ID,
  POPULATION_ID: DEMO_POPULATION_ID,
  SEED: demoScenarioConfig.engineConfig.seed,
} as const;
