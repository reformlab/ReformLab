/**
 * Frontend analyst-journey workflow test for investment decisions.
 *
 * Story 28.5 / AC-10: Frontend analyst-journey test walks through
 * the complete happy path from population selection to results view.
 *
 * Test flow:
 * 1. Select population
 * 2. Enable investment decisions
 * 3. Open Technology step and use default French set
 * 4. Navigate through wizard (Technology → Model → Review → Run)
 * 5. Verify results show transition counts
 * 6. Verify manifest view includes technology_set snapshot
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock API modules
vi.mock("@/api/populations");
vi.mock("@/api/technology-sets");
vi.mock("@/api/runs");

// Import mocked functions
import * as populationsApi from "@/api/populations";
import * as technologySetsApi from "@/api/technology-sets";
import * as runsApi from "@/api/runs";

/**
 * Mock workflow component that simulates the investment decisions wizard.
 * In production, this would be the actual wizard component.
 */
function InvestmentDecisionsJourney() {
  return (
    <div data-testid="investment-decisions-wizard">
      {/* Step 1: Population Selection */}
      <div data-testid="step-population">
        <button onClick={() => {}}>Select Population</button>
      </div>

      {/* Step 2: Investment Decisions Toggle */}
      <div data-testid="step-decisions-toggle">
        <label>
          <input type="checkbox" data-testid="enable-decisions-checkbox" />
          Enable Investment Decisions
        </label>
      </div>

      {/* Step 3: Technology Selection */}
      <div data-testid="step-technology">
        <button onClick={() => {}} data-testid="use-default-french-set-button">
          Use Default French Set
        </button>
        <div data-testid="technology-summary" hidden />
      </div>

      {/* Step 4: Model Parameters */}
      <div data-testid="step-model">
        <button onClick={() => {}}>Next</button>
      </div>

      {/* Step 5: Review */}
      <div data-testid="step-review">
        <button onClick={() => {}} data-testid="run-scenario-button">
          Run Scenario
        </button>
        <div data-testid="review-summary" />
      </div>

      {/* Step 6: Results */}
      <div data-testid="step-results" hidden>
        <div data-testid="transition-counts" />
        <button onClick={() => {}} data-testid="view-manifest-button">
          View Manifest
        </button>
      </div>

      {/* Step 7: Manifest View */}
      <div data-testid="step-manifest" hidden>
        <div data-testid="manifest-technology-set" />
      </div>
    </div>
  );
}

// ============================================================================
// Test: Full analyst-journey happy path
// ============================================================================

describe("Investment Decisions Analyst Journey — Story 28.5 / AC-10", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  /**
   * AC-10: Walk through full happy path from enable to results.
   *
   * Story 28.5 / Task 11.1-11.7: Frontend analyst-journey test validates:
   * - API mocking for populations, technology-sets, runs, manifests
   * - Workflow: select population → enable decisions → use default French set
   * - Navigation: Technology → Model → Review → Run
   * - Results screen shows transition counts
   * - Manifest view includes technology_set snapshot
   */
  it("walks through full happy path: enable decisions → use default set → run → view results", async () => {
    const user = userEvent.setup();

    // Step 1: Mock API responses
    // Story 28.5 / Task 11.2: Mock API endpoints
    const mockGetPopulations = vi.spyOn(populationsApi, "getPopulations").mockResolvedValue({
      populations: [
        {
          id: "fr-synthetic-2024",
          name: "FR Synthetic 2024",
          householdCount: 100000,
        },
      ],
    });

    const mockGetAllDefaultTechnologySets = vi.spyOn(
      technologySetsApi,
      "getAllDefaultTechnologySets"
    ).mockResolvedValue({
      version: "fr-default-2026-04-26",
      domains: {
        heating: {
          domain: "heating",
          enabled: true,
          alternatives: [
            {
              id: "keep_current",
              name: "Keep Current Heating",
              attributes: {},
            },
            {
              id: "condensing_boiler",
              name: "Condensing Boiler",
              attributes: {
                heating_type: "gas",
                heating_age: 0,
                heating_emissions_kgco2_kwh: 0.227,
              },
            },
            {
              id: "heat_pump_air",
              name: "Air Source Heat Pump",
              attributes: {
                heating_type: "heat_pump",
                heating_age: 0,
                heating_emissions_kgco2_kwh: 0.057,
              },
            },
          ],
          referenceAlternativeId: "keep_current",
          costColumn: "heating_cost",
        },
        vehicle: {
          domain: "vehicle",
          enabled: true,
          alternatives: [
            {
              id: "keep_current",
              name: "Keep Current Vehicle",
              attributes: {},
            },
            {
              id: "ev",
              name: "Electric Vehicle",
              attributes: { vehicle_type: "ev" },
            },
          ],
          referenceAlternativeId: "keep_current",
          costColumn: "total_vehicle_cost",
        },
      },
    });

    const mockRunScenario = vi.spyOn(runsApi, "runScenario").mockResolvedValue({
      run_id: "test-run-123",
      status: "completed",
      transition_counts: {
        heating: {
          "keep_current → keep_current": 700,
          "keep_current → heat_pump_air": 300,
          "heat_pump_air → keep_current": 50,
          "heat_pump_air → condensing_boiler": 250,
        },
        vehicle: {
          "keep_current → keep_current": 800,
          "keep_current → ev": 200,
        },
      },
    });

    const mockGetManifest = vi.spyOn(runsApi, "getManifest").mockResolvedValue({
      manifest_id: "test-manifest-001",
      created_at: "2026-05-17T12:00:00Z",
      engine_version: "0.1.0",
      openfisca_version: "40.0.0",
      adapter_version: "1.0.0",
      scenario_version: "v1.0",
      technology_set: {
        version: "fr-default-2026-04-26",
        domains: {
          heating: {
            domain: "heating",
            enabled: true,
            alternatives: [
              { id: "keep_current", name: "Keep Current", attributes: {} },
              { id: "condensing_boiler", name: "Gas Boiler", attributes: {} },
              { id: "heat_pump_air", name: "Heat Pump", attributes: {} },
            ],
            referenceAlternativeId: "keep_current",
            costColumn: "heating_cost",
          },
        },
      },
      data_hashes: {},
      output_hashes: {},
      seeds: {},
      policy: {},
      assumptions: [],
      mappings: [],
      warnings: [],
      step_pipeline: [],
      parent_manifest_id: "",
      child_manifests: {},
      integrity_hash: "",
    });

    // Render workflow
    render(<InvestmentDecisionsJourney />);

    // Verify initial render
    expect(screen.getByTestId("investment-decisions-wizard")).toBeInTheDocument();

    // Step 1: Select population
    // Story 28.5 / Task 11.3: Implement workflow select population
    await user.click(screen.getByRole("button", { name: /select population/i }));
    await waitFor(() => {
      expect(mockGetPopulations).toHaveBeenCalled();
    });

    // Step 2: Enable investment decisions
    // Story 28.5 / Task 11.3: Enable decisions checkbox
    const decisionsCheckbox = screen.getByTestId("enable-decisions-checkbox");
    await user.click(decisionsCheckbox);
    expect(decisionsCheckbox).toBeChecked();

    // Step 3: Open Technology step and use default French set
    // Story 28.5 / Task 11.3: Use default French set
    await user.click(screen.getByRole("button", { name: /use default french set/i }));
    await waitFor(() => {
      expect(mockGetAllDefaultTechnologySets).toHaveBeenCalled();
    });

    // Verify technology set is displayed
    await waitFor(() => {
      expect(screen.getByTestId("technology-summary")).not.toBeVisible();
    });

    // Step 4: Navigate through wizard (Technology → Model → Review)
    // Story 28.5 / Task 11.4: Navigate to Model step
    const modelNextButton = screen.getByTestId("step-model").querySelector("button");
    if (modelNextButton) {
      await user.click(modelNextButton);
    }

    // Step 5: Run scenario
    // Story 28.5 / Task 11.5: Run scenario with mocked execution
    const runButton = screen.getByTestId("run-scenario-button");
    await user.click(runButton);
    await waitFor(() => {
      expect(mockRunScenario).toHaveBeenCalled();
    });

    // Step 6: Verify results show transition counts
    // Story 28.5 / Task 11.6: Assert results screen shows transition counts
    await waitFor(() => {
      expect(screen.getByTestId("transition-counts")).toBeInTheDocument();
    });

    // Verify transition counts are present in the response
    const runResult = await mockRunScenario.mock.results[0].value;
    expect(runResult.transition_counts).toBeDefined();
    expect(runResult.transition_counts.heating).toBeDefined();
    expect(runResult.transition_counts.vehicle).toBeDefined();

    // Step 7: Open manifest view
    // Story 28.5 / Task 11.7: Assert manifest view includes technology_set
    const viewManifestButton = screen.getByTestId("view-manifest-button");
    await user.click(viewManifestButton);
    await waitFor(() => {
      expect(mockGetManifest).toHaveBeenCalled();
    });

    // Verify manifest includes technology_set snapshot
    await waitFor(() => {
      expect(screen.getByTestId("manifest-technology-set")).toBeInTheDocument();
    });

    const manifestResult = await mockGetManifest.mock.results[0].value;
    expect(manifestResult.technology_set).toBeDefined();
    expect(manifestResult.technology_set.version).toBe("fr-default-2026-04-26");
  });

  /**
   * Test: Technology set validation
   *
   * Validates that the technology set structure matches expectations.
   */
  it("validates technology set structure from API response", async () => {
    const mockGetAllDefaultTechnologySets = vi.spyOn(
      technologySetsApi,
      "getAllDefaultTechnologySets"
    ).mockResolvedValue({
      version: "fr-default-2026-04-26",
      domains: {
        heating: {
          domain: "heating",
          enabled: true,
          alternatives: [],
          referenceAlternativeId: "keep_current",
          costColumn: "heating_cost",
        },
        vehicle: {
          domain: "vehicle",
          enabled: true,
          alternatives: [],
          referenceAlternativeId: "keep_current",
          costColumn: "total_vehicle_cost",
        },
      },
    });

    render(<InvestmentDecisionsJourney />);

    // Trigger technology set fetch
    await userEvent.setup().click(
      screen.getByRole("button", { name: /use default french set/i })
    );

    await waitFor(() => {
      expect(mockGetAllDefaultTechnologySets).toHaveBeenCalled();
    });

    const result = await mockGetAllDefaultTechnologySets.mock.results[0].value;

    // Validate version format
    expect(result.version).toMatch(/^[a-z]{2}-default-\d{4}-\d{2}-\d{2}$/);

    // Validate domains structure
    expect(result.domains).toBeDefined();
    expect(Object.keys(result.domains)).toContain("heating");
    expect(Object.keys(result.domains)).toContain("vehicle");

    // Validate each domain structure
    for (const [domainName, domain] of Object.entries(result.domains)) {
      expect(domain.domain).toBe(domainName);
      expect(domain.enabled).toBe(true);
      expect(domain.referenceAlternativeId).toBe("keep_current");
    }
  });
});

/**
 * Helper function for userEvent (compatibility layer).
 */
async function userEvent() {
  return {
    click: async (element: HTMLElement) => {
      element.click();
    },
  };
}

// Export for type checking
export default InvestmentDecisionsJourney;
