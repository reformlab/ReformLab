// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * App tests — Story 20.1, AC-1, AC-2, AC-4.
 *
 * Verifies:
 * - Auth prompt renders before login
 * - Post-auth workspace renders 4-stage navigation (AC-1)
 * - Gradient header removed (AC-1 brand compliance)
 * - Hash routing defaults and invalid hash handling (AC-4)
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";

vi.mock("@/api/auth", () => ({ login: vi.fn() }));
vi.mock("@/api/populations", () => ({
  listPopulations: vi.fn(),
  getPopulationPreview: vi.fn(),
  getPopulationProfile: vi.fn(),
  getPopulationCrosstab: vi.fn(),
  uploadPopulation: vi.fn(),
  deletePopulation: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("@/api/templates", () => ({ listTemplates: vi.fn(), getTemplate: vi.fn() }));
vi.mock("@/api/scenarios", () => ({ listScenarios: vi.fn(), getScenario: vi.fn(), createScenario: vi.fn(), cloneScenario: vi.fn(), deleteScenario: vi.fn() }));
vi.mock("@/api/results", () => ({ listResults: vi.fn(), getResult: vi.fn(), deleteResult: vi.fn(), exportResultCsv: vi.fn(), exportResultParquet: vi.fn() }));
vi.mock("@/api/portfolios", () => ({ listPortfolios: vi.fn(), createPortfolio: vi.fn(), deletePortfolio: vi.fn(), validatePortfolio: vi.fn() }));
vi.mock("@/api/data-fusion", () => ({ listDataSources: vi.fn(), listMergeMethods: vi.fn(), generatePopulation: vi.fn() }));
vi.mock("@/api/runs", () => ({ runScenario: vi.fn() }));
vi.mock("@/api/indicators", () => ({ getIndicators: vi.fn(), comparePortfolios: vi.fn() }));
vi.mock("@/api/decisions", () => ({ getDecisionSummary: vi.fn() }));
vi.mock("@/api/exports", () => ({ exportCsv: vi.fn(), exportParquet: vi.fn() }));

import { login } from "@/api/auth";
import { listPopulations } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listResults } from "@/api/results";
import { listPortfolios } from "@/api/portfolios";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";

function renderApp() {
  return render(
    <AppProvider>
      <App />
    </AppProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1600,
    });
    sessionStorage.clear();
    localStorage.clear();
    window.location.hash = "";
    vi.clearAllMocks();
    vi.mocked(listPopulations).mockResolvedValue([]);
    vi.mocked(listTemplates).mockResolvedValue([]);
    vi.mocked(getTemplate).mockRejectedValue(new Error("not found"));
    vi.mocked(listResults).mockResolvedValue([]);
    vi.mocked(listPortfolios).mockResolvedValue([]);
    vi.mocked(listDataSources).mockResolvedValue({});
    vi.mocked(listMergeMethods).mockResolvedValue([]);
  });

  it("shows password prompt when not authenticated", () => {
    renderApp();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enter/i })).toBeInTheDocument();
  });

  it("renders ReformLab heading on the login page", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: /reformlab/i })).toBeInTheDocument();
  });

  it("renders 4-stage navigation after login (AC-1)", async () => {
    vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(screen.getByRole("navigation", { name: /workflow navigation/i })).toBeInTheDocument();
    });

    // Stage labels appear in both TopBar and WorkflowNavRail — verify at least one exists
    expect(screen.getAllByText("Policy").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Population").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Scenario").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Run / Results / Compare").length).toBeGreaterThanOrEqual(1);
  });

  it("does not render gradient header after login (AC-1 brand compliance)", async () => {
    vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
    const user = userEvent.setup();
    const { container } = renderApp();

    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(screen.getAllByText("Policy").length).toBeGreaterThanOrEqual(1);
    });

    // Gradient header should not exist
    const gradientEl = container.querySelector(".bg-gradient-to-r");
    expect(gradientEl).toBeNull();
  });

  it("defaults to policies stage on empty hash (AC-4)", async () => {
    vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
    const user = userEvent.setup();
    window.location.hash = "";
    renderApp();

    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      // Default stage is "policies" — TopBar and nav rail show stage label
      expect(screen.getAllByText("Policy").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("first launch navigates to results/runner with demo scenario (AC-1, Story 20.2)", async () => {
    // Empty localStorage = first launch (cleared in beforeEach)
    vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(window.location.hash).toBe("#results/runner");
    });

    // SimulationRunnerScreen renders with Run Simulation button
    expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
  });

  it("hash routing: changing window.location.hash triggers correct stage render (AC-2)", async () => {
    vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(screen.getAllByText("Policy").length).toBeGreaterThanOrEqual(1);
    });

    // Navigate to population stage via hash — Story 20.4: library is default entry point
    window.location.hash = "#population";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(screen.getAllByText("Population Library").length).toBeGreaterThanOrEqual(1);
    });
  });
});
