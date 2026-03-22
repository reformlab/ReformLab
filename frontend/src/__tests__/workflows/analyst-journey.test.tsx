/**
 * Analyst Journey — cross-screen navigation workflow tests (Story 17.8, AC-1, AC-3).
 *
 * Renders the full <AppProvider><App /></AppProvider> tree and exercises:
 *   - Authentication flow (password prompt → workspace)
 *   - Left-panel navigation (Population → Portfolio → Simulation → Configure Policy)
 *   - Configuration step navigation (Population → Policy → Parameters → Validation)
 *   - Simulation run flow (Configure Policy → Simulation → results)
 *   - Comparison navigation (results → comparison → back)
 *
 * All API modules are mocked so no real HTTP calls are made.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// -----------------------------------------------------------------------
// Mock all API modules before any imports that trigger side-effects.
// -----------------------------------------------------------------------

vi.mock("@/api/auth", () => ({ login: vi.fn() }));
vi.mock("@/api/populations", () => ({ listPopulations: vi.fn() }));
vi.mock("@/api/templates", () => ({ listTemplates: vi.fn(), getTemplate: vi.fn() }));
vi.mock("@/api/scenarios", () => ({
  listScenarios: vi.fn(),
  getScenario: vi.fn(),
  createScenario: vi.fn(),
  cloneScenario: vi.fn(),
  deleteScenario: vi.fn(),
}));
vi.mock("@/api/results", () => ({
  listResults: vi.fn(),
  getResult: vi.fn(),
  deleteResult: vi.fn(),
  exportResultCsv: vi.fn(),
  exportResultParquet: vi.fn(),
}));
vi.mock("@/api/portfolios", () => ({
  listPortfolios: vi.fn(),
  createPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
  validatePortfolio: vi.fn(),
}));
vi.mock("@/api/data-fusion", () => ({
  listDataSources: vi.fn(),
  listMergeMethods: vi.fn(),
  generatePopulation: vi.fn(),
}));
vi.mock("@/api/runs", () => ({ runScenario: vi.fn() }));
vi.mock("@/api/indicators", () => ({
  getIndicators: vi.fn(),
  comparePortfolios: vi.fn(),
}));
vi.mock("@/api/decisions", () => ({ getDecisionSummary: vi.fn() }));
vi.mock("@/api/exports", () => ({ exportCsv: vi.fn(), exportParquet: vi.fn() }));

// -----------------------------------------------------------------------
// Imports after vi.mock hoisting
// -----------------------------------------------------------------------

import { login } from "@/api/auth";
import { listPortfolios } from "@/api/portfolios";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";
import { listPopulations } from "@/api/populations";
import { listResults } from "@/api/results";
import { getTemplate, listTemplates } from "@/api/templates";
import { runScenario } from "@/api/runs";
import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";
import { mockRunResponse, setupResizeObserver } from "./helpers";

// ============================================================================
// Render helper
// ============================================================================

function renderApp() {
  return render(
    <AppProvider>
      <App />
    </AppProvider>,
  );
}

// ============================================================================
// Authentication helper
// ============================================================================

async function authenticate(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });

  await user.type(screen.getByPlaceholderText(/password/i), "secret");
  await user.click(screen.getByRole("button", { name: /enter/i }));

  await waitFor(() => {
    expect(screen.getByText("ReformLab")).toBeInTheDocument();
  });
}

// ============================================================================
// Left-panel helper
//
// The workspace renders two <aside> elements (left and right panels). Navigation
// buttons (Population, Portfolio, Simulation, Configure Policy) live in the
// FIRST aside (leftPanel). Using within() prevents false matches against the
// ModelConfigStepper step buttons that share labels like "Population".
// ============================================================================

function getLeftPanel(): HTMLElement {
  return screen.getAllByRole("complementary")[0];
}

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  // Required for DistributionalChart rendered in "results" viewMode (test 6.5)
  setupResizeObserver();
});

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  vi.clearAllMocks();

  // Defaults: hooks fall back to mock data when API returns empty or rejects
  vi.mocked(listPopulations).mockResolvedValue([]);
  vi.mocked(listTemplates).mockResolvedValue([]);
  vi.mocked(getTemplate).mockRejectedValue(new Error("not found"));
  vi.mocked(listResults).mockResolvedValue([]);
  vi.mocked(listPortfolios).mockResolvedValue([]);
  vi.mocked(listDataSources).mockResolvedValue({});
  vi.mocked(listMergeMethods).mockResolvedValue([]);

  // Widen window so left panel is not auto-collapsed (requires > 1440px)
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: 1600,
  });
});

// ============================================================================
// Tests
// ============================================================================

describe("Analyst Journey — cross-screen navigation", () => {
  describe("Task 6.3 — authenticates and navigates through workspace views", () => {
    it("shows password prompt before auth and workspace heading after", async () => {
      const user = userEvent.setup();
      renderApp();

      // Pre-auth: password prompt visible
      expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /enter/i })).toBeInTheDocument();

      await authenticate(user);

      // Post-auth: main workspace heading visible
      expect(screen.getByText("ReformLab")).toBeInTheDocument();
    });

    it("navigates to Data Fusion Workbench via Population button", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Scope to left panel to avoid matching ModelConfigStepper "Population" step button
      await user.click(within(getLeftPanel()).getByRole("button", { name: /^population$/i }));

      await waitFor(() => {
        expect(screen.getByText("Data Fusion Workbench")).toBeInTheDocument();
      });
    });

    it("navigates to Portfolio Designer via Portfolio button", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      await user.click(within(getLeftPanel()).getByRole("button", { name: /^portfolio$/i }));

      await waitFor(() => {
        expect(screen.getByText(/select policy templates/i)).toBeInTheDocument();
      });
    });

    it("navigates to Simulation Runner via Simulation button", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Scope to left panel — in configuration viewMode, the header also has a "Simulation" button
      await user.click(within(getLeftPanel()).getByRole("button", { name: /^simulation$/i }));

      await waitFor(() => {
        // SimulationRunnerScreen renders "Run Simulation" configure view
        expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
      });
    });

    it("shows Configure Policy stepper as the default view on load", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Default viewMode is "configuration" — ModelConfigStepper renders immediately.
      // Configure Policy is now folded into the Simulation stage (Story 18.1).
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /next step/i })).toBeInTheDocument();
      });
    });
  });

  describe("Task 6.4 — navigates configuration steps and proceeds to simulation", () => {
    it("steps through Population → Policy → Parameters → Validation → Simulation run view", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Default view is "configuration" with "population" active step
      // Verify Population step is active (step 1 of ModelConfigStepper)
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /next step/i })).toBeInTheDocument();
      });

      // Step 1 → 2 (Population → Policy)
      await user.click(screen.getByRole("button", { name: /next step/i }));
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /next step/i })).toBeInTheDocument();
      });

      // Step 2 → 3 (Policy → Parameters)
      await user.click(screen.getByRole("button", { name: /next step/i }));
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /next step/i })).toBeInTheDocument();
      });

      // Step 3 → 4 (Parameters → Validation/Assumptions)
      await user.click(screen.getByRole("button", { name: /next step/i }));
      await waitFor(() => {
        // Last step: button text is "Go to Simulation"
        expect(screen.getByRole("button", { name: /go to simulation/i })).toBeInTheDocument();
      });

      // Navigate to simulation run view
      await user.click(screen.getByRole("button", { name: /go to simulation/i }));
      await waitFor(() => {
        // Run view: "Run Simulation" button
        expect(screen.getByRole("button", { name: /^run simulation$/i })).toBeInTheDocument();
      });
    });
  });

  describe("Task 6.5 — navigates to comparison and back", () => {
    it("opens comparison from results view and navigates back", async () => {
      vi.mocked(runScenario).mockResolvedValueOnce(mockRunResponse());

      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // In "configuration" viewMode the header shows a "Simulation" button (→ "run" viewMode).
      // It is NOT inside an <aside> (left panel) or <nav> (ModelConfigStepper step nav).
      const headerSimBtn = screen.getAllByRole("button", { name: /^simulation$/i })
        .find((btn) => !btn.closest("aside") && !btn.closest("nav"));
      if (!headerSimBtn) throw new Error("Header Simulation button not found");
      await user.click(headerSimBtn);

      // "run" viewMode: click Run Simulation (calls startRun() → runScenario mock)
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /^run simulation$/i })).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: /^run simulation$/i }));

      // After startRun() resolves, viewMode → "results" → "Open Comparison" button
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /compare runs/i })).toBeInTheDocument();
      });

      // Open Comparison → ComparisonDashboardScreen
      await user.click(screen.getByRole("button", { name: /compare runs/i }));
      await waitFor(() => {
        // ComparisonDashboardScreen renders a RunSelector with this heading.
        // (ScenarioCard "Compare" buttons in the left panel share the name "Compare",
        // so we target unique text from the RunSelector to confirm this screen is shown.)
        expect(screen.getByText(/select runs to compare/i)).toBeInTheDocument();
      });

      // Header "Back to Results" button (shown in comparison viewMode)
      await user.click(screen.getByRole("button", { name: /back to results/i }));
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /compare runs/i })).toBeInTheDocument();
      });
    });
  });
});
