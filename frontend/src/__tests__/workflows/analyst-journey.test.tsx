// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Analyst Journey — cross-screen navigation workflow tests (Story 20.1 update).
 *
 * Renders the full <AppProvider><App /></AppProvider> tree and exercises:
 *   - Authentication flow (password prompt → workspace)
 *   - Stage navigation via nav rail (Population, Portfolio, Engine)
 *   - Hash-based routing (direct hash navigation, hashchange events)
 *   - Comparison navigation via hash (#results/comparison → back to #results)
 *
 * All API modules are mocked so no real HTTP calls are made.
 *
 * Story 20.1 — AC-2, AC-4, AC-5.
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
import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";
import {
  HAS_LAUNCHED_KEY,
  SCENARIO_STORAGE_KEY,
  STAGE_STORAGE_KEY,
} from "@/hooks/useScenarioPersistence";
import { createDemoScenario } from "@/data/demo-scenario";
import { setupResizeObserver } from "./helpers";

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
    // After login, TopBar shows stage label and nav rail shows stage labels
    expect(screen.getAllByText("Policies & Portfolio")[0]).toBeInTheDocument();
  });
}

// ============================================================================
// Left-panel helper
//
// The workspace renders <aside> elements (left and right panels). Navigation
// buttons (Policies & Portfolio, Population, Engine, Run / Results / Compare)
// live in the FIRST aside (leftPanel). Using within() prevents false matches.
// ============================================================================

function getLeftPanel(): HTMLElement {
  return screen.getAllByRole("complementary")[0];
}

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  // Required for DistributionalChart rendered in "results" stage (test 6.5)
  setupResizeObserver();
});

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  window.location.hash = "";
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

      // Post-auth: stage navigation visible (stage label from TopBar)
      expect(screen.getAllByText("Policies & Portfolio")[0]).toBeInTheDocument();
    });

    it("navigates to Data Fusion Workbench via Population button", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Click the Population stage button in the nav rail
      await user.click(within(getLeftPanel()).getByRole("button", { name: /^population$/i }));

      await waitFor(() => {
        expect(screen.getByText("Data Fusion Workbench")).toBeInTheDocument();
      });
    });

    it("navigates to Portfolio Designer via Policies & Portfolio button", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Click the Policies & Portfolio stage button in the nav rail
      await user.click(within(getLeftPanel()).getByRole("button", { name: /policies.*portfolio/i }));

      await waitFor(() => {
        // PoliciesStageScreen renders PortfolioDesignerScreen
        expect(screen.getByText(/select policy templates/i)).toBeInTheDocument();
      });
    });

    it("navigates to Simulation Runner via hash #results/runner", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Navigate directly to the simulation runner via hash
      window.location.hash = "#results/runner";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        // SimulationRunnerScreen renders "Run Simulation" configure view
        expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
      });
    });

    it("returning user restores policies stage as the active view (Story 20.2 AC-2)", async () => {
      // Pre-populate localStorage so this is a returning user with policies stage saved
      localStorage.setItem(HAS_LAUNCHED_KEY, "true");
      localStorage.setItem(STAGE_STORAGE_KEY, "policies");
      localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(createDemoScenario()));

      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Returning user: restores saved stage "policies" — PortfolioDesignerScreen renders
      await waitFor(() => {
        expect(screen.getByText(/select policy templates/i)).toBeInTheDocument();
      });
    });

    it("renders Engine stub when navigating to #engine (AC-2)", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      window.location.hash = "#engine";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        expect(screen.getAllByText("Engine Configuration").length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe("Task 6.5 — navigates to comparison and back via hash (AC-2, AC-5)", () => {
    it("opens comparison from hash and navigates back to results overview", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Navigate directly to comparison via hash (Story 20.1, 9.3a)
      window.location.hash = "#results/comparison";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        // ComparisonDashboardScreen renders a RunSelector with this heading
        expect(screen.getByText(/select runs to compare/i)).toBeInTheDocument();
      });

      // Navigate back to results overview via hash (browser back equivalent, 9.3b)
      window.location.hash = "#results";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        // ResultsOverviewScreen renders — it has the "Compare Runs" button
        expect(screen.getByRole("button", { name: /compare runs/i })).toBeInTheDocument();
      });
    });
  });

  describe("Task 9.4 — hash routing tests (AC-2, AC-4)", () => {
    it("unrecognised hash defaults to policies stage without error (AC-4)", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      window.location.hash = "#not-a-real-stage";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        // Defaults to policies — PortfolioDesignerScreen
        expect(screen.getByText(/select policy templates/i)).toBeInTheDocument();
      });
    });

    it("valid stage with invalid subview sets activeSubView to null (AC-4)", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // results/badsubview -> results stage with activeSubView=null -> ResultsOverviewScreen
      window.location.hash = "#results/not-a-real-subview";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        // ResultsOverviewScreen (default results subview)
        expect(screen.getByRole("button", { name: /compare runs/i })).toBeInTheDocument();
      });
    });
  });

  describe("Task 9.5 — WorkspaceScenario type (AC-3, updated by Story 20.2)", () => {
    it("first-launch loads demo scenario and opens runner — distinct from portfolios (Story 20.2 AC-1)", async () => {
      // Empty localStorage = first launch
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // First-launch navigates to results/runner with demo scenario loaded.
      // SimulationRunnerScreen renders — no crash proves WorkspaceScenario and
      // PortfolioListItem are distinct object classes (AC-3).
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
      });
    });
  });

  describe("Task 9.6 — AC-5: existing stage-4 screens preserved", () => {
    it("renders empty-state for #results/decisions when no run result exists (AC-5)", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      window.location.hash = "#results/decisions";
      window.dispatchEvent(new HashChangeEvent("hashchange"));

      await waitFor(() => {
        expect(screen.getByText(/no simulation run available/i)).toBeInTheDocument();
      });
    });
  });

  // ===========================================================================
  // Story 20.2 tests
  // ===========================================================================

  describe("Story 20.2 — first-launch and returning-user flows", () => {
    it("first-launch loads demo scenario and opens runner (AC-1)", async () => {
      // Empty localStorage = first launch (cleared in beforeEach)
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Verify navigation to results/runner
      await waitFor(() => {
        expect(window.location.hash).toBe("#results/runner");
      });

      // Verify Run Simulation button is visible
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
    });

    it("returning user restores saved scenario and stage (AC-2)", async () => {
      // Pre-set localStorage to simulate returning user with saved engine stage
      const savedScenario = createDemoScenario();
      localStorage.setItem(HAS_LAUNCHED_KEY, "true");
      localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(savedScenario));
      localStorage.setItem(STAGE_STORAGE_KEY, "engine");

      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Returning user restores engine stage
      await waitFor(() => {
        expect(screen.getAllByText("Engine Configuration").length).toBeGreaterThanOrEqual(1);
      });
      expect(window.location.hash).toBe("#engine");
    });

    it("scenario entry dialog opens from TopBar and shows 4 options (AC-3)", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // After first-launch, we are on results/runner — click the scenario name in TopBar
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /switch scenario/i }));

      await waitFor(() => {
        expect(screen.getByText("New Scenario")).toBeInTheDocument();
        expect(screen.getByText("Open Saved")).toBeInTheDocument();
        expect(screen.getByText("Clone Current")).toBeInTheDocument();
        expect(screen.getByText("Demo Scenario")).toBeInTheDocument();
      });
    });

    it("reset to demo from entry dialog (AC-3)", async () => {
      const user = userEvent.setup();
      renderApp();
      await authenticate(user);

      // Wait for first-launch to complete
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
      });

      // Open entry dialog
      await user.click(screen.getByRole("button", { name: /switch scenario/i }));

      await waitFor(() => {
        expect(screen.getByText("Demo Scenario")).toBeInTheDocument();
      });

      // Click "Demo Scenario"
      await user.click(screen.getByText("Demo Scenario"));

      // Dialog closes and app navigates to results/runner
      await waitFor(() => {
        expect(screen.queryByText("Switch Scenario")).not.toBeInTheDocument();
        expect(window.location.hash).toBe("#results/runner");
      });
    });
  });
});
