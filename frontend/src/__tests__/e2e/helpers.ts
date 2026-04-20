// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * End-to-end test helpers for ReformLab workspace flows (Story 20.8).
 *
 * Provides reusable utilities for E2E workflow tests:
 * - localStorage management for test isolation
 * - Hash-based navigation waiting
 * - DOM element polling
 * - Demo scenario setup
 * - Run completion polling
 * - Scenario lineage assertions
 *
 * Helpers are designed for EPIC-21 extensibility — evidence flows can extend
 * the FlowConfig interface without duplicating workspace flow logic.
 *
 * Story 20.8 — AC-1, AC-3.
 */

import { waitFor, within } from "@testing-library/react";
import type { StageKey, SubView, WorkspaceScenario } from "@/types/workspace";

import {
  HAS_LAUNCHED_KEY,
  SAVED_SCENARIOS_KEY,
  SCENARIO_STORAGE_KEY,
  STAGE_STORAGE_KEY,
} from "@/hooks/useScenarioPersistence";
import { createDemoScenario, DEMO_POPULATION_ID } from "@/data/demo-scenario";

// ============================================================================
// localStorage helpers — test isolation
// ============================================================================

/**
 * Clear all ReformLab localStorage keys.
 * Call this in beforeEach to ensure test isolation.
 */
export function cleanLocalStorage(): void {
  sessionStorage.clear();
  localStorage.removeItem(SCENARIO_STORAGE_KEY);
  localStorage.removeItem(STAGE_STORAGE_KEY);
  localStorage.removeItem(SAVED_SCENARIOS_KEY);
  localStorage.removeItem(HAS_LAUNCHED_KEY);
}

/**
 * Store a scenario in localStorage for "returning user" tests.
 * Also sets has-launched flag so the demo scenario doesn't auto-load.
 */
export function persistScenario(scenario: WorkspaceScenario, stage?: StageKey): void {
  localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(scenario));
  if (stage) {
    localStorage.setItem(STAGE_STORAGE_KEY, stage);
  }
  localStorage.setItem(HAS_LAUNCHED_KEY, "true");
}

// ============================================================================
// Navigation helpers — hash routing
// ============================================================================

/**
 * Wait for window.location.hash to match the expected stage and subview.
 * Times out after 5 seconds (default for waitFor).
 *
 * @param stage — The StageKey to expect in the hash
 * @param subView — Optional SubView to expect (e.g., "runner", "comparison")
 */
export async function waitForNavigation(
  stage: StageKey,
  subView?: SubView | null,
): Promise<void> {
  const expectedHash = subView ? `#${stage}/${subView}` : `#${stage}`;
  await waitFor(
    () => {
      expect(window.location.hash).toBe(expectedHash);
    },
    { timeout: 5000 },
  );
}

/**
 * Navigate to a stage/subview by setting window.location.hash.
 * Use this for direct navigation when testing click behavior isn't the focus.
 */
export function navigateTo(stage: StageKey, subView?: SubView | null): void {
  const hash = subView ? `#${stage}/${subView}` : `#${stage}`;
  window.location.hash = hash;
  // Dispatch hashchange event for listeners
  window.dispatchEvent(new HashChangeEvent("hashchange"));
}

// ============================================================================
// DOM helpers — element polling
// ============================================================================

/**
 * Wait for a DOM element matching the selector to appear.
 * Returns the element when found.
 *
 * @param selector — CSS selector (use test IDs when possible)
 * @param timeout — Milliseconds to wait (default 5000)
 */
export async function waitForElement(
  selector: string,
  timeout = 5000,
): Promise<HTMLElement> {
  let element: HTMLElement | null = null;
  await waitFor(
    () => {
      element = document.querySelector<HTMLElement>(selector);
      if (!element) {
        throw new Error(`Element not found: ${selector}`);
      }
    },
    { timeout },
  );
  return element as unknown as HTMLElement;
}

/**
 * Find text content within a container, with optional timeout.
 * Useful for waiting for toast messages or status updates.
 */
export async function waitForText(
  container: HTMLElement,
  text: string,
  timeout = 5000,
): Promise<void> {
  await waitFor(
    () => {
      expect(within(container).queryByText(text)).toBeInTheDocument();
    },
    { timeout },
  );
}

// ============================================================================
// Scenario helpers — demo scenario setup
// ============================================================================

/**
 * Set up the demo scenario in localStorage.
 * This simulates the first-launch flow without going through the UI.
 * Use this when testing downstream flows, not the first-launch itself.
 */
export function setupDemoScenario(options?: Partial<WorkspaceScenario>): WorkspaceScenario {
  const demo = { ...createDemoScenario(), ...options };
  localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(demo));
  localStorage.setItem(HAS_LAUNCHED_KEY, "true");
  return demo;
}

/**
 * Create a minimal test scenario for portfolio/editing flow tests.
 * Uses the demo template and population but allows customization.
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

// ============================================================================
// Run helpers — completion polling
// ============================================================================

/**
 * Poll for run completion by checking if the run result is available.
 * This is a stub implementation — the real version would poll the API.
 * For E2E tests, use waitFor with a condition that checks for results.
 *
 * Story 20.8 note: Real implementation requires backend to be running.
 * For now, tests should mock the runScenario API to return immediately.
 */
export async function waitForRunCompletion(
  runId: string,
  timeout = 30000,
): Promise<{ success: boolean; runId: string }> {
  // Stub: E2E tests mock runScenario to resolve immediately
  // When backend is available, this would poll GET /api/results/{runId}
  await waitFor(
    () => {
      // Check for result in DOM or state
      const resultElement = document.querySelector(`[data-run-id="${runId}"]`);
      if (!resultElement) {
        throw new Error(`Run ${runId} not completed yet`);
      }
    },
    { timeout },
  );
  return { success: true, runId };
}

/**
 * Stub for scenario lineage assertion.
 * When Story 20.6 is complete, this will verify ResultDetailResponse includes
 * scenario metadata (scenario_id, scenario_name, portfolio_name, population_id).
 *
 * @param runId — The run ID to check
 * @param _expectedFields — Expected lineage fields to assert (unused until Story 20.6)
 */
export async function assertScenarioLineage(
  runId: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _expectedFields: Record<string, unknown>,
): Promise<void> {
  // Stub: Verify lineage fields are present in results
  // When Story 20.6 backend is complete, fetch from API and assert fields
  await waitFor(() => {
    const resultElement = document.querySelector(`[data-run-id="${runId}"]`);
    expect(resultElement).toBeInTheDocument();
    // TODO: Assert lineage fields when 20.6 complete
  });
}

// ============================================================================
// Flow config interface — EPIC-21 extensibility
// ============================================================================

/**
 * Base flow configuration for E2E tests.
 * EPIC-21 Story 21.8 will extend this with evidence-specific fields.
 *
 * @example
 * ```typescript
 * const config: FlowConfig = {
 *   scenario: { policyType: "carbon-tax" },
 *   assertions: { lineage: { scenario_name: "Carbon Tax Scenario" } }
 * };
 * ```
 */
export interface FlowConfig {
  scenario: Partial<WorkspaceScenario>;
  assertions?: {
    lineage?: Record<string, unknown>;
  };
}

/**
 * Execute a workspace flow with the given configuration.
 * This is the base implementation — EPIC-21 will extend it for evidence flows.
 *
 * Story 20.8 — AC-3: Tests extensible for EPIC-21 evidence flows.
 */
export async function runFlow(config: FlowConfig): Promise<void> {
  // Base implementation: set up scenario and navigate
  const scenario = createTestScenario(config.scenario);
  setupDemoScenario(scenario);
  // TODO: Execute flow based on config
  // EPIC-21 will add evidence-specific logic here
}

// ============================================================================
// Constants — test IDs and selectors
// ============================================================================

/**
 * Test ID selectors for key E2E targets.
 * Use these in queries: screen.getByTestId(E2E_TEST_IDS.runSimulationButton)
 */
export const E2E_TEST_IDS = {
  // Navigation
  navRail: "nav-rail",
  stageButton: (stage: StageKey) => `stage-button-${stage}`,

  // Actions
  runSimulationButton: "run-simulation-button",
  saveScenarioButton: "save-scenario-button",
  cloneScenarioButton: "clone-scenario-button",

  // Results
  resultsContainer: "results-container",
  comparisonContainer: "comparison-container",
  runStatus: (runId: string) => `run-status-${runId}`,

  // Inputs
  portfolioNameInput: "portfolio-name-input",
  scenarioNameInput: "scenario-name-input",
  populationDropdown: "population-dropdown",
} as const;
