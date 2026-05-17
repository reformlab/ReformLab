// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier

import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";

import { ApiError } from "@/api/client";
import { clonePortfolio, createPortfolio, getPortfolio, updatePortfolio } from "@/api/portfolios";
import type { Category, CompositionEntry, PortfolioConflict } from "@/api/types";
import type { Template } from "@/data/mock-data";
import { usePortfolioDialog } from "../usePortfolioDialog";

vi.mock("@/api/portfolios", () => ({
  createPortfolio: vi.fn(),
  updatePortfolio: vi.fn(),
  getPortfolio: vi.fn(),
  clonePortfolio: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

const mockToast = vi.mocked(toast);
const mockCreatePortfolio = vi.mocked(createPortfolio);
const mockUpdatePortfolio = vi.mocked(updatePortfolio);
const mockGetPortfolio = vi.mocked(getPortfolio);
const mockClonePortfolio = vi.mocked(clonePortfolio);

const mockTemplates: Template[] = [
  {
    id: "carbon-tax",
    type: "carbon-tax",
    name: "Carbon Tax",
    description: "Carbon tax",
    parameterCount: 2,
    parameterGroups: ["Mechanism"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "subsidy",
    type: "subsidy",
    name: "Subsidy",
    description: "Subsidy",
    parameterCount: 1,
    parameterGroups: ["Mechanism"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
];

const mockComposition: CompositionEntry[] = [
  {
    templateId: "carbon-tax",
    instanceId: "carbon-tax-ins0",
    name: "Carbon Tax 2030",
    parameters: { carbon_rate: 50 },
    rateSchedule: {},
    policy_type: "carbon_tax",
  },
];

const mockCategories: Category[] = [
  {
    id: "climate",
    label: "Climate",
    columns: [],
    compatible_types: ["tax", "subsidy"],
    formula_explanation: "",
    description: "",
  },
];

describe("usePortfolioDialog — save mode", () => {
  const mockLoadedRef = { current: null as string | null };
  const mockSetActivePortfolioName = vi.fn();
  const mockUpdateScenarioPortfolioName = vi.fn();
  const mockSetSelectedPortfolioName = vi.fn();
  const mockRefetchPortfolios = vi.fn();
  const mockOnSavedSuccessfully = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLoadedRef.current = null;
  });

  it("opens save dialog with a generated suggestion", () => {
    const { result } = renderHook(() =>
      usePortfolioDialog("save", {
        templates: mockTemplates,
        composition: mockComposition,
        resolutionStrategy: "error",
        conflicts: [],
        loadedPortfolioRef: mockLoadedRef,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        refetchPortfolios: mockRefetchPortfolios,
        categories: mockCategories,
      }),
    );

    act(() => {
      result.current.openSaveDialog();
    });

    expect(result.current.mode).toBe("save");
    expect(result.current.saveDialogOpen).toBe(true);
    expect(result.current.portfolioSaveName).toBeTruthy();
    expect(result.current.saveNameError).toBeNull();
  });

  it("freezes the suggestion after manual edits", () => {
    const { result } = renderHook(() =>
      usePortfolioDialog("save", {
        templates: mockTemplates,
        composition: mockComposition,
        resolutionStrategy: "error",
        conflicts: [],
        loadedPortfolioRef: mockLoadedRef,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        refetchPortfolios: mockRefetchPortfolios,
        categories: mockCategories,
      }),
    );

    act(() => {
      result.current.openSaveDialog();
      result.current.handleSaveNameChange("my-custom-name");
    });

    expect(result.current.portfolioSaveName).toBe("my-custom-name");
  });

  it("prevents saving conflicting portfolios when strategy is error", async () => {
    const conflicts: PortfolioConflict[] = [
      {
        conflict_type: "rate_overlap",
        policy_indices: [0, 1],
        parameter_name: "carbon_rate",
        description: "Conflict",
      },
    ];

    const { result } = renderHook(() =>
      usePortfolioDialog("save", {
        templates: mockTemplates,
        composition: mockComposition,
        resolutionStrategy: "error",
        conflicts,
        loadedPortfolioRef: mockLoadedRef,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        refetchPortfolios: mockRefetchPortfolios,
      }),
    );

    act(() => {
      result.current.handleSaveNameChange("valid-portfolio");
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(mockCreatePortfolio).not.toHaveBeenCalled();
    expect(mockToast.error).toHaveBeenCalledWith(
      "Resolve conflicts before saving",
      expect.any(Object),
    );
  });

  it("saves a new portfolio with canonical policy types", async () => {
    mockCreatePortfolio.mockResolvedValue("v-abc123");

    const { result } = renderHook(() =>
      usePortfolioDialog("save", {
        templates: mockTemplates,
        composition: mockComposition,
        resolutionStrategy: "sum",
        conflicts: [],
        loadedPortfolioRef: mockLoadedRef,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        refetchPortfolios: mockRefetchPortfolios,
        onSavedSuccessfully: mockOnSavedSuccessfully,
      }),
    );

    act(() => {
      result.current.handleSaveNameChange("my-portfolio");
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(mockCreatePortfolio).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "my-portfolio",
        policies: expect.arrayContaining([
          expect.objectContaining({
            name: "Carbon Tax 2030",
            policy_type: "carbon_tax",
          }),
        ]),
      }),
    );
    expect(mockToast.success).toHaveBeenCalledWith("Policy set 'my-portfolio' saved");
    expect(mockOnSavedSuccessfully).toHaveBeenCalledOnce();
  });

  it("updates an existing portfolio when the loaded ref matches", async () => {
    mockLoadedRef.current = "existing-portfolio";
    mockUpdatePortfolio.mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePortfolioDialog("save", {
        templates: mockTemplates,
        composition: mockComposition,
        resolutionStrategy: "sum",
        conflicts: [],
        loadedPortfolioRef: mockLoadedRef,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        refetchPortfolios: mockRefetchPortfolios,
      }),
    );

    act(() => {
      result.current.handleSaveNameChange("existing-portfolio");
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(mockUpdatePortfolio).toHaveBeenCalledOnce();
    expect(mockCreatePortfolio).not.toHaveBeenCalled();
    expect(mockToast.success).toHaveBeenCalledWith("Policy set 'existing-portfolio' updated");
  });

  it("surfaces API errors from save", async () => {
    mockCreatePortfolio.mockRejectedValue(
      new ApiError({
        error: "server_error",
        what: "Save failed",
        why: "Internal server error",
        fix: "Retry the request",
        status_code: 500,
      }),
    );

    const { result } = renderHook(() =>
      usePortfolioDialog("save", {
        templates: mockTemplates,
        composition: mockComposition,
        resolutionStrategy: "sum",
        conflicts: [],
        loadedPortfolioRef: mockLoadedRef,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        refetchPortfolios: mockRefetchPortfolios,
      }),
    );

    act(() => {
      result.current.handleSaveNameChange("my-portfolio");
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(mockToast.error).toHaveBeenCalled();
  });
});

describe("usePortfolioDialog — load mode", () => {
  const mockLoadedRef = { current: null as string | null };
  const mockSetComposition = vi.fn();
  const mockSetResolutionStrategy = vi.fn();
  const mockSetActivePortfolioName = vi.fn();
  const mockUpdateScenarioPortfolioName = vi.fn();
  const mockSetSelectedPortfolioName = vi.fn();
  const mockSetInstanceCounter = vi.fn();
  const mockOnLoadedSuccessfully = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLoadedRef.current = null;
  });

  it("opens and closes the load dialog", () => {
    const { result } = renderHook(() =>
      usePortfolioDialog("load", {
        templates: mockTemplates,
        activeScenarioPortfolioName: null,
        compositionLength: 0,
        validStrategies: ["error", "sum"],
        defaultResolutionStrategy: "error",
        loadedPortfolioRef: mockLoadedRef,
        setComposition: mockSetComposition,
        setResolutionStrategy: mockSetResolutionStrategy,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
      }),
    );

    act(() => {
      result.current.openLoadDialog();
    });
    expect(result.current.loadDialogOpen).toBe(true);

    act(() => {
      result.current.closeLoadDialog();
    });
    expect(result.current.loadDialogOpen).toBe(false);
  });

  it("auto-loads without warning toasts", async () => {
    mockGetPortfolio.mockResolvedValue({
      name: "test-portfolio",
      description: "Test",
      version_id: "v-123",
      policies: [
        {
          name: "Carbon Tax",
          policy_type: "carbon_tax",
          rate_schedule: {},
          parameters: { carbon_rate: 50 },
        },
      ],
      resolution_strategy: "sum",
      policy_count: 1,
    });

    const { rerender } = renderHook(
      ({ activeName }) =>
        usePortfolioDialog("load", {
          templates: mockTemplates,
          activeScenarioPortfolioName: activeName,
          compositionLength: 0,
          validStrategies: ["error", "sum"],
          defaultResolutionStrategy: "error",
          loadedPortfolioRef: mockLoadedRef,
          setComposition: mockSetComposition,
          setResolutionStrategy: mockSetResolutionStrategy,
          setActivePortfolioName: mockSetActivePortfolioName,
          updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
          setSelectedPortfolioName: mockSetSelectedPortfolioName,
          setInstanceCounter: mockSetInstanceCounter,
          onLoadedSuccessfully: mockOnLoadedSuccessfully,
        }),
      { initialProps: { activeName: null as string | null } },
    );

    await act(async () => {
      rerender({ activeName: "test-portfolio" });
    });

    await waitFor(() => {
      expect(mockGetPortfolio).toHaveBeenCalledWith("test-portfolio");
    });

    expect(mockSetComposition).toHaveBeenCalled();
    expect(mockOnLoadedSuccessfully).toHaveBeenCalledOnce();
    expect(mockToast.warning).not.toHaveBeenCalled();
  });

  it("keeps auto-load failures silent", async () => {
    mockGetPortfolio.mockRejectedValue(new Error("network"));

    const { rerender } = renderHook(
      ({ activeName }) =>
        usePortfolioDialog("load", {
          templates: mockTemplates,
          activeScenarioPortfolioName: activeName,
          compositionLength: 0,
          validStrategies: ["error", "sum"],
          defaultResolutionStrategy: "error",
          loadedPortfolioRef: mockLoadedRef,
          setComposition: mockSetComposition,
          setResolutionStrategy: mockSetResolutionStrategy,
          setActivePortfolioName: mockSetActivePortfolioName,
          updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
          setSelectedPortfolioName: mockSetSelectedPortfolioName,
        }),
      { initialProps: { activeName: null as string | null } },
    );

    await act(async () => {
      rerender({ activeName: "missing-portfolio" });
    });

    await waitFor(() => {
      expect(mockGetPortfolio).toHaveBeenCalledWith("missing-portfolio");
    });

    expect(mockToast.warning).not.toHaveBeenCalled();
    expect(mockLoadedRef.current).toBeNull();
  });

  it("loads a portfolio on explicit request", async () => {
    mockGetPortfolio.mockResolvedValue({
      name: "test-portfolio",
      description: "Test",
      version_id: "v-123",
      policies: [
        {
          name: "Carbon Tax",
          policy_type: "carbon_tax",
          rate_schedule: {},
          parameters: { carbon_rate: 50 },
        },
      ],
      resolution_strategy: "sum",
      policy_count: 1,
    });

    const { result } = renderHook(() =>
      usePortfolioDialog("load", {
        templates: mockTemplates,
        activeScenarioPortfolioName: null,
        compositionLength: 0,
        validStrategies: ["error", "sum"],
        defaultResolutionStrategy: "error",
        loadedPortfolioRef: mockLoadedRef,
        setComposition: mockSetComposition,
        setResolutionStrategy: mockSetResolutionStrategy,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
        onLoadedSuccessfully: mockOnLoadedSuccessfully,
      }),
    );

    await act(async () => {
      await result.current.handleLoad("test-portfolio");
    });

    expect(mockToast.success).toHaveBeenCalledWith("Loaded policy set 'test-portfolio'");
    expect(mockOnLoadedSuccessfully).toHaveBeenCalledOnce();
  });

  it("shows a warning toast on explicit load failure", async () => {
    mockGetPortfolio.mockRejectedValue(
      new ApiError({
        error: "not_found",
        what: "Portfolio not found",
        why: "Portfolio does not exist",
        fix: "Check the portfolio name",
        status_code: 404,
      }),
    );

    const { result } = renderHook(() =>
      usePortfolioDialog("load", {
        templates: mockTemplates,
        activeScenarioPortfolioName: null,
        compositionLength: 0,
        validStrategies: ["error", "sum"],
        defaultResolutionStrategy: "error",
        loadedPortfolioRef: mockLoadedRef,
        setComposition: mockSetComposition,
        setResolutionStrategy: mockSetResolutionStrategy,
        setActivePortfolioName: mockSetActivePortfolioName,
        updateScenarioPortfolioName: mockUpdateScenarioPortfolioName,
        setSelectedPortfolioName: mockSetSelectedPortfolioName,
      }),
    );

    await act(async () => {
      await result.current.handleLoad("missing-portfolio");
    });

    expect(mockToast.warning).toHaveBeenCalled();
  });
});

describe("usePortfolioDialog — clone mode", () => {
  const mockPortfolios = [
    { name: "portfolio-1", description: "Portfolio 1", version_id: "v-1", policy_count: 2 },
    { name: "portfolio-2", description: "Portfolio 2", version_id: "v-2", policy_count: 1 },
  ];
  const mockRefetchPortfolios = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("opens clone dialog with a generated name", () => {
    const { result } = renderHook(() =>
      usePortfolioDialog("clone", {
        portfolios: mockPortfolios,
        refetchPortfolios: mockRefetchPortfolios,
      }),
    );

    act(() => {
      result.current.openCloneDialog("portfolio-1");
    });

    expect(result.current.cloneDialogOpen).toBe(true);
    expect(result.current.cloneNewName).toMatch(/portfolio-1-copy/);
  });

  it("rejects duplicate clone names", () => {
    const { result } = renderHook(() =>
      usePortfolioDialog("clone", {
        portfolios: mockPortfolios,
        refetchPortfolios: mockRefetchPortfolios,
      }),
    );

    act(() => {
      result.current.openCloneDialog("portfolio-1");
      result.current.handleCloneNameChange("portfolio-2");
    });

    expect(result.current.cloneNameError).toMatch(/already exists/);
  });

  it("clones a portfolio successfully", async () => {
    mockClonePortfolio.mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePortfolioDialog("clone", {
        portfolios: mockPortfolios,
        refetchPortfolios: mockRefetchPortfolios,
      }),
    );

    act(() => {
      result.current.openCloneDialog("portfolio-1");
      result.current.handleCloneNameChange("my-cloned-portfolio");
    });

    await act(async () => {
      await result.current.handleClone();
    });

    expect(mockClonePortfolio).toHaveBeenCalledWith("portfolio-1", {
      new_name: "my-cloned-portfolio",
    });
    expect(mockToast.success).toHaveBeenCalledWith(
      "Policy set 'portfolio-1' cloned as 'my-cloned-portfolio'",
    );
    expect(mockRefetchPortfolios).toHaveBeenCalledOnce();
  });
});
