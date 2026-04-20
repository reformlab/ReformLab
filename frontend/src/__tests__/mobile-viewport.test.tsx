// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Mobile viewport tests — Story 22.7
 *
 * AC-1: No horizontal overflow at 375px viewport width (iPhone SE)
 * AC-3: TopBar brand block remains visible at narrow widths
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";

// Mock all API dependencies
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
vi.mock("@/api/categories", () => ({ listCategories: vi.fn() }));
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
vi.mock("@/api/exports", () => ({
  exportCsv: vi.fn(),
  exportParquet: vi.fn(),
}));

import { login } from "@/api/auth";
import { listPopulations } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listCategories } from "@/api/categories";
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

describe("Mobile Viewport — Story 22.7", () => {
  beforeEach(() => {
    // Reset to mobile viewport (375px - iPhone SE)
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 375,
    });
    sessionStorage.clear();
    localStorage.clear();
    window.location.hash = "";
    vi.clearAllMocks();
    vi.mocked(listPopulations).mockResolvedValue([]);
    vi.mocked(listTemplates).mockResolvedValue([]);
    vi.mocked(getTemplate).mockRejectedValue(new Error("not found"));
    vi.mocked(listCategories).mockResolvedValue([]);
    vi.mocked(listResults).mockResolvedValue([]);
    vi.mocked(listPortfolios).mockResolvedValue([]);
    vi.mocked(listDataSources).mockResolvedValue({});
    vi.mocked(listMergeMethods).mockResolvedValue([]);
    // Trigger resize event
    window.dispatchEvent(new Event("resize"));
  });

  describe("AC-1: No horizontal overflow at 375px", () => {
    it("should not show desktop-only warning banner at 375px", async () => {
      vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
      const user = userEvent.setup();
      renderApp();

      await user.type(screen.getByPlaceholderText(/password/i), "secret");
      await user.click(screen.getByRole("button", { name: /enter/i }));

      await waitFor(() => {
        // The warning banner should not exist
        const warningBanner = screen.queryByText(/ReformLab is designed for desktop use/i);
        expect(warningBanner).not.toBeInTheDocument();
      });
    });

    it("should render app without horizontal scroll at phone viewport", async () => {
      vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
      const user = userEvent.setup();
      renderApp();

      await user.type(screen.getByPlaceholderText(/password/i), "secret");
      await user.click(screen.getByRole("button", { name: /enter/i }));

      await waitFor(() => {
        // AC-1: Verify responsive layout prevents horizontal overflow.
        // The app now renders only the active branch at a given viewport.
        const layoutContainer = document.querySelector(".flex.flex-1.flex-col.overflow-hidden");
        expect(layoutContainer).toBeTruthy();

        // Mobile stage switcher should be present at narrow widths.
        const mobileLayout = layoutContainer?.querySelector(".lg\\:hidden");
        expect(mobileLayout).toBeTruthy();

        // Desktop panel group should not be rendered in the mobile branch.
        const desktopLayout = layoutContainer?.querySelector("[data-panel-group-direction='horizontal']");
        expect(desktopLayout).toBeNull();
      });
    });
  });

  describe("AC-3: TopBar brand block remains visible at narrow widths", () => {
    it("should show logo and wordmark at 375px", async () => {
      vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
      const user = userEvent.setup();
      renderApp();

      await user.type(screen.getByPlaceholderText(/password/i), "secret");
      await user.click(screen.getByRole("button", { name: /enter/i }));

      await waitFor(() => {
        // Logo should be present
        const logo = screen.getByAltText("ReformLab");
        expect(logo).toBeInTheDocument();

        // "ReformLab" wordmark should be visible
        const wordmark = screen.getAllByText("ReformLab");
        expect(wordmark.length).toBeGreaterThan(0);
      });
    });
  });
});
