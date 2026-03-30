// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for TopBar — Story 22.1.
 *
 * Tests:
 * - AC-1: Top bar displays logo icon plus visible "ReformLab" wordmark text
 * - AC-2: Docs and GitHub links open correct URLs in new tab with security attributes
 * - AC-3: Scenario controls render in center-left container with visual separation
 * - AC-4: Narrow screens hide secondary utilities while brand block remains visible
 * - AC-5: Wordmark uses Inter semibold with slate-700 color
 */

import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { TopBar } from "@/components/layout/TopBar";
import type { WorkspaceScenario } from "@/types/workspace";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));

import { useAppState } from "@/contexts/AppContext";

// ============================================================================
// Helpers
// ============================================================================

function makeScenario(overrides: Partial<WorkspaceScenario> = {}): WorkspaceScenario {
  return {
    id: "test-scenario-1",
    name: "Test Scenario",
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
    },
    policyType: null,
    lastRunId: null,
    ...overrides,
  };
}

function makeDefaultAppState(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  return {
    isAuthenticated: true,
    authLoading: false,
    authenticate: vi.fn(),
    logout: vi.fn(),
    activeStage: "results" as const,
    activeSubView: null,
    navigateTo: vi.fn(),
    activeScenario: makeScenario(),
    setActiveScenario: vi.fn(),
    updateScenarioField: vi.fn(),
    savedScenarios: [],
    saveCurrentScenario: vi.fn(),
    loadSavedScenario: vi.fn(),
    resetToDemo: vi.fn(),
    createNewScenario: vi.fn(),
    cloneCurrentScenario: vi.fn(),
    populations: [],
    templates: [],
    parameters: [],
    parameterValues: {},
    setParameterValue: vi.fn(),
    scenarios: [],
    decileData: [],
    selectedPopulationId: "",
    setSelectedPopulationId: vi.fn(),
    selectedTemplateId: "",
    selectTemplate: vi.fn(),
    selectedScenarioId: "",
    setSelectedScenarioId: vi.fn(),
    startRun: vi.fn(),
    runLoading: false,
    runResult: null,
    cloneScenario: vi.fn(),
    deleteScenario: vi.fn(),
    populationsLoading: false,
    templatesLoading: false,
    parametersLoading: false,
    refetchPopulations: vi.fn(),
    refetchTemplates: vi.fn(),
    dataFusionSources: {},
    dataFusionMethods: [],
    dataFusionResult: null,
    setDataFusionResult: vi.fn(),
    dataFusionSourcesLoading: false,
    portfolios: [],
    portfoliosLoading: false,
    refetchPortfolios: vi.fn(),
    results: [],
    resultsLoading: false,
    refetchResults: vi.fn(),
    selectedPortfolioName: null,
    setSelectedPortfolioName: vi.fn(),
    selectedComparisonRunIds: [],
    setSelectedComparisonRunIds: vi.fn(),
    executionMatrix: {},
    updateExecutionCell: vi.fn(),
    apiConnected: true,
    ...overrides,
  };
}

function renderTopBar(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  vi.mocked(useAppState).mockReturnValue(
    makeDefaultAppState(overrides) as ReturnType<typeof useAppState>,
  );
  return render(<TopBar />);
}

// ============================================================================
// AC-1: Brand block with logo + wordmark
// ============================================================================

describe("AC-1: Brand block with logo + wordmark", () => {
  it("renders logo icon", () => {
    renderTopBar();
    const logo = screen.getByRole("img", { name: "ReformLab" });
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute("src", "/logo.svg");
  });

  it("renders visible ReformLab wordmark text", () => {
    renderTopBar();
    // Wordmark should be visible text next to logo
    const wordmark = screen.getByText("ReformLab");
    expect(wordmark).toBeInTheDocument();
  });

  it("applies correct wordmark styling (Inter semibold, slate-700)", () => {
    renderTopBar();
    const wordmark = screen.getByText("ReformLab");
    expect(wordmark).toHaveClass("text-sm", "font-semibold", "text-slate-700");
  });

  it("has gap-2 spacing between logo and wordmark", () => {
    renderTopBar();
    // The brand block div contains logo + wordmark with gap-2
    const wordmark = screen.getByText("ReformLab");
    const brandBlockDiv = wordmark.parentElement;
    expect(brandBlockDiv).toHaveClass("gap-2");
  });
});

// ============================================================================
// AC-2: External links (docs and GitHub)
// ============================================================================

describe("AC-2: External links (docs and GitHub)", () => {
  it("renders docs link with correct href", () => {
    renderTopBar();
    const docsLink = screen.getByRole("link", { name: /documentation/i });
    expect(docsLink).toBeInTheDocument();
    expect(docsLink).toHaveAttribute("href", "https://reform-lab.eu");
  });

  it("renders GitHub link with correct href", () => {
    renderTopBar();
    const githubLink = screen.getByRole("link", { name: /github/i });
    expect(githubLink).toBeInTheDocument();
    expect(githubLink).toHaveAttribute("href", "https://github.com/lucasvivier/reformlab");
  });

  it("external links have target='_blank'", () => {
    renderTopBar();
    const docsLink = screen.getByRole("link", { name: /documentation/i });
    const githubLink = screen.getByRole("link", { name: /github/i });

    expect(docsLink).toHaveAttribute("target", "_blank");
    expect(githubLink).toHaveAttribute("target", "_blank");
  });

  it("external links have rel='noopener noreferrer' security attributes", () => {
    renderTopBar();
    const docsLink = screen.getByRole("link", { name: /documentation/i });
    const githubLink = screen.getByRole("link", { name: /github/i });

    expect(docsLink).toHaveAttribute("rel", "noopener noreferrer");
    expect(githubLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("external links have hover states", () => {
    renderTopBar();
    const docsLink = screen.getByRole("link", { name: /documentation/i });
    const githubLink = screen.getByRole("link", { name: /github/i });

    expect(docsLink).toHaveClass("hover:text-slate-700");
    expect(githubLink).toHaveClass("hover:text-slate-700");
  });

  it("external links have aria-label describing destination", () => {
    renderTopBar();
    const docsLink = screen.getByRole("link", { name: /Open documentation at reform-lab.eu/i });
    const githubLink = screen.getByRole("link", { name: /View source code on GitHub/i });

    expect(docsLink).toBeInTheDocument();
    expect(githubLink).toBeInTheDocument();
  });
});

// ============================================================================
// AC-3: Scenario controls in center-left container
// ============================================================================

describe("AC-3: Scenario controls in center-left container", () => {
  it("renders scenario name button", () => {
    renderTopBar({ activeScenario: makeScenario({ name: "My Test Scenario" }) });
    const scenarioButton = screen.getByRole("button", { name: /Switch scenario/i });
    expect(scenarioButton).toBeInTheDocument();
    expect(scenarioButton).toHaveTextContent("My Test Scenario");
  });

  it("renders save button", () => {
    renderTopBar();
    const saveButton = screen.getByRole("button", { name: "Save scenario" });
    expect(saveButton).toBeInTheDocument();
  });

  it("scenario controls have visual separation from brand block", () => {
    renderTopBar();
    // The main left container should have gap-x-4 for separation
    // between brand block and scenario controls
    const brandBlock = screen.getByText("ReformLab").parentElement;
    const leftContainer = brandBlock?.parentElement;
    expect(leftContainer).toHaveClass("gap-x-4");
  });

  it("renders current stage label", () => {
    renderTopBar({ activeStage: "policies" as const });
    // Stage label should be visible - the actual text includes more than just "Policies"
    const stageLabel = screen.getByText(/policies/i);
    expect(stageLabel).toBeInTheDocument();
  });

  it("displays 'No scenario' when no active scenario", () => {
    renderTopBar({ activeScenario: null });
    const scenarioButton = screen.getByRole("button", { name: /Switch scenario/i });
    expect(scenarioButton).toHaveTextContent("No scenario");
  });
});

// ============================================================================
// AC-4: Responsive behavior for narrow screens
// ============================================================================

describe("AC-4: Responsive behavior for narrow screens", () => {
  it("brand block remains visible at all widths", () => {
    renderTopBar();
    const logo = screen.getByRole("img", { name: "ReformLab" });
    const wordmark = screen.getByText("ReformLab");

    // Both logo and wordmark should be visible without responsive hiding
    expect(logo).toBeInTheDocument();
    expect(wordmark).toBeInTheDocument();
    // Check that wordmark does NOT have hidden classes
    expect(wordmark.className).not.toMatch(/hidden|md:hidden|lg:hidden/);
  });

  it("secondary utilities have responsive hiding classes", () => {
    renderTopBar();
    // Settings icon should be hidden on small screens
    const settingsIcon = screen.getByLabelText("Settings");
    const settingsContainer = settingsIcon.closest("div");

    // Should have hidden md:flex classes
    expect(settingsContainer).toHaveClass("hidden");
    expect(settingsContainer).toHaveClass("md:flex");
  });

  it("docs link has responsive hiding classes", () => {
    renderTopBar();
    const docsLink = screen.getByRole("link", { name: /Open documentation at reform-lab.eu/i });

    // The link itself should have hidden md:flex classes
    expect(docsLink).toHaveClass("hidden");
    expect(docsLink).toHaveClass("md:flex");
  });

  it("GitHub link has responsive hiding classes", () => {
    renderTopBar();
    const githubLink = screen.getByRole("link", { name: /View source code on GitHub/i });

    // The link itself should have hidden md:flex classes
    expect(githubLink).toHaveClass("hidden");
    expect(githubLink).toHaveClass("md:flex");
  });
});

// ============================================================================
// AC-5: Wordmark styling
// ============================================================================

describe("AC-5: Wordmark styling", () => {
  it("wordmark uses text-sm (14px) font size", () => {
    renderTopBar();
    const wordmark = screen.getByText("ReformLab");
    expect(wordmark).toHaveClass("text-sm");
  });

  it("wordmark uses font-semibold (600 weight)", () => {
    renderTopBar();
    const wordmark = screen.getByText("ReformLab");
    expect(wordmark).toHaveClass("font-semibold");
  });

  it("wordmark uses text-slate-700 (#334155)", () => {
    renderTopBar();
    const wordmark = screen.getByText("ReformLab");
    expect(wordmark).toHaveClass("text-slate-700");
  });
});
