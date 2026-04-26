// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * AppContext provider integration tests.
 *
 * Covers the scenario naming lifecycle that cannot be verified by pure
 * naming utility tests alone: provider auto-update, manual edit freeze,
 * loaded scenario preservation, and demo scenario protection.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    info: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}));

vi.mock("@/api/auth", () => ({
  login: vi.fn(),
  logout: vi.fn(),
}));

vi.mock("@/api/populations", () => ({
  listPopulations: vi.fn(),
}));

vi.mock("@/api/templates", () => ({
  getTemplate: vi.fn(),
  listTemplates: vi.fn(),
}));

vi.mock("@/api/scenarios", () => ({
  cloneScenario: vi.fn(),
  createScenario: vi.fn(),
}));

vi.mock("@/api/data-fusion", () => ({
  listDataSources: vi.fn(),
  listMergeMethods: vi.fn(),
}));

vi.mock("@/api/portfolios", () => ({
  listPortfolios: vi.fn(),
}));

vi.mock("@/api/results", () => ({
  listResults: vi.fn(),
}));

vi.mock("@/api/indicators", () => ({
  getIndicators: vi.fn(),
}));

import { setAuthToken } from "@/api/client";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";
import { getIndicators } from "@/api/indicators";
import { listPopulations } from "@/api/populations";
import { listPortfolios } from "@/api/portfolios";
import { listResults } from "@/api/results";
import { getTemplate, listTemplates } from "@/api/templates";
import { AppProvider, useAppState } from "@/contexts/AppContext";
import { createDemoScenario, DEMO_SCENARIO_ID } from "@/data/demo-scenario";
import {
  HAS_LAUNCHED_KEY,
  MANUALLY_EDITED_NAMES_KEY,
  SCENARIO_STORAGE_KEY,
  STAGE_STORAGE_KEY,
} from "@/hooks/useScenarioPersistence";
import type { WorkspaceScenario } from "@/types/workspace";

const TEST_POPULATIONS = [
  {
    id: "quick-test-population",
    name: "Quick Test Population",
    households: 100,
    source: "Built-in demo data",
    year: 2026,
    origin: "built-in",
    canonical_origin: "synthetic-public",
    access_mode: "bundled",
    trust_status: "demo-only",
    is_synthetic: true,
    column_count: 7,
    created_date: "2026-01-01T00:00:00Z",
  },
  {
    id: "fr-synthetic-2024",
    name: "France Synthetic 2024",
    households: 100_000,
    source: "INSEE marginals",
    year: 2024,
    origin: "built-in",
    canonical_origin: "synthetic-public",
    access_mode: "bundled",
    trust_status: "exploratory",
    is_synthetic: true,
    column_count: 10,
    created_date: null,
  },
];

const TEST_TEMPLATES = [
  {
    id: "carbon-tax-flat",
    name: "Carbon Tax — Flat Rate",
    type: "carbon-tax",
    parameter_count: 8,
    description: "Flat carbon tax rate applied uniformly across all households",
    parameter_groups: ["Tax Rates", "Thresholds"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
    category_id: "tax",
  },
];

function makeScenario(overrides: Partial<WorkspaceScenario> = {}): WorkspaceScenario {
  return {
    id: "scenario-under-test",
    name: "Initial Scenario Name",
    version: "1.0",
    status: "draft",
    isBaseline: false,
    baselineRef: null,
    portfolioName: null,
    populationIds: [],
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
    policyType: "carbon-tax-flat",
    lastRunId: null,
    ...overrides,
  };
}

function persistReturningScenario(scenario: WorkspaceScenario): void {
  localStorage.setItem(HAS_LAUNCHED_KEY, "true");
  localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(scenario));
  localStorage.setItem(STAGE_STORAGE_KEY, "scenario");
}

function ContextProbe() {
  const app = useAppState();

  return (
    <div>
      <output data-testid="scenario-id">{app.activeScenario?.id ?? ""}</output>
      <output data-testid="scenario-name">{app.activeScenario?.name ?? ""}</output>
      <output data-testid="selected-population">{app.selectedPopulationId}</output>
      <button type="button" onClick={() => app.setSelectedPortfolioName("Carbon Tax")}>
        Select Carbon Tax
      </button>
      <button type="button" onClick={() => app.setSelectedPortfolioName("Climate Dividend")}>
        Select Climate Dividend
      </button>
      <button type="button" onClick={() => app.setSelectedPopulationId("fr-synthetic-2024")}>
        Select France 2024
      </button>
      <button type="button" onClick={() => app.setSelectedPopulationId("quick-test-population")}>
        Select Quick Test
      </button>
      <button type="button" onClick={() => app.updateScenarioField("name", "Custom label")}>
        Manual Rename
      </button>
      <button type="button" onClick={() => app.resetToDemo()}>
        Reset Demo
      </button>
    </div>
  );
}

function renderProvider() {
  return render(
    <AppProvider>
      <ContextProbe />
    </AppProvider>,
  );
}

function readManualNameIds(): string[] {
  const raw = localStorage.getItem(MANUALLY_EDITED_NAMES_KEY);
  return raw ? JSON.parse(raw) as string[] : [];
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  window.location.hash = "";
  vi.clearAllMocks();

  setAuthToken("test-token");

  vi.mocked(listPopulations).mockResolvedValue(TEST_POPULATIONS);
  vi.mocked(listTemplates).mockResolvedValue(TEST_TEMPLATES);
  vi.mocked(getTemplate).mockResolvedValue({
    id: "carbon-tax-flat",
    name: "Carbon Tax — Flat Rate",
    type: "carbon-tax",
    description: "Flat carbon tax rate applied uniformly across all households",
    default_policy: { carbon_tax_rate: 50 },
    parameter_groups: ["Tax Rates"],
    metadata: {},
  });
  vi.mocked(listDataSources).mockResolvedValue({});
  vi.mocked(listMergeMethods).mockResolvedValue([]);
  vi.mocked(listPortfolios).mockResolvedValue([]);
  vi.mocked(listResults).mockResolvedValue([]);
  vi.mocked(getIndicators).mockResolvedValue(null);
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
});

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
  localStorage.clear();
  window.location.hash = "";
});

describe("AppContext naming lifecycle", () => {
  it("auto-updates a non-demo draft scenario name from policy set and primary population", async () => {
    persistReturningScenario(makeScenario());
    renderProvider();

    await waitFor(() => {
      expect(screen.getByTestId("scenario-id")).toHaveTextContent("scenario-under-test");
    });

    fireEvent.click(screen.getByRole("button", { name: "Select Carbon Tax" }));
    fireEvent.click(screen.getByRole("button", { name: "Select France 2024" }));

    await waitFor(() => {
      expect(screen.getByTestId("scenario-name")).toHaveTextContent("Carbon Tax — FR Synthetic 2024");
    });
  });

  it("preserves a manual scenario name after later policy set or population changes", async () => {
    persistReturningScenario(makeScenario());
    renderProvider();

    await waitFor(() => {
      expect(screen.getByTestId("scenario-id")).toHaveTextContent("scenario-under-test");
    });

    fireEvent.click(screen.getByRole("button", { name: "Manual Rename" }));
    fireEvent.click(screen.getByRole("button", { name: "Select Climate Dividend" }));
    fireEvent.click(screen.getByRole("button", { name: "Select France 2024" }));

    await waitFor(() => {
      expect(screen.getByTestId("scenario-name")).toHaveTextContent("Custom label");
    });
    expect(readManualNameIds()).toContain("scenario-under-test");
  });

  it("preserves a loaded scenario name through provider initialization and API refresh effects", async () => {
    persistReturningScenario(
      makeScenario({
        name: "Imported Policy Analysis",
        portfolioName: "Legacy Policy Set",
        populationIds: ["fr-synthetic-2024"],
      }),
    );
    renderProvider();

    await waitFor(() => {
      expect(screen.getByTestId("selected-population")).toHaveTextContent("fr-synthetic-2024");
    });

    await waitFor(() => {
      expect(screen.getByTestId("scenario-name")).toHaveTextContent("Imported Policy Analysis");
    });
  });

  it("never auto-updates the demo scenario name or marks it as manually renamed", async () => {
    renderProvider();

    await waitFor(() => {
      expect(screen.getByTestId("scenario-id")).toHaveTextContent(DEMO_SCENARIO_ID);
    });
    const demoName = createDemoScenario().name;
    expect(screen.getByTestId("scenario-name")).toHaveTextContent(demoName);

    fireEvent.click(screen.getByRole("button", { name: "Select Carbon Tax" }));
    fireEvent.click(screen.getByRole("button", { name: "Select France 2024" }));
    fireEvent.click(screen.getByRole("button", { name: "Manual Rename" }));

    await waitFor(() => {
      expect(screen.getByTestId("scenario-name")).toHaveTextContent("Custom label");
    });
    expect(readManualNameIds()).not.toContain(DEMO_SCENARIO_ID);

    fireEvent.click(screen.getByRole("button", { name: "Reset Demo" }));

    await waitFor(() => {
      expect(screen.getByTestId("scenario-name")).toHaveTextContent(demoName);
    });
    expect(readManualNameIds()).not.toContain(DEMO_SCENARIO_ID);
  });
});
