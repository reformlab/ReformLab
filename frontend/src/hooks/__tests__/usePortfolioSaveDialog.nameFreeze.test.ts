// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Tests for name suggestion freeze after manual edit — Story 25.5.
 *
 * AC-2: Deterministic name suggestions from policy types
 * AC-3: Manual name edit freezes suggestion (composition changes don't override)
 */

import { renderHook, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { usePortfolioSaveDialog } from "@/hooks/usePortfolioSaveDialog";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import type { Template } from "@/data/mock-data";

// Mock the API
vi.mock("@/api/portfolios", () => ({
  createPortfolio: vi.fn(),
}));

// Mock toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

// ============================================================================
// Test data
// ============================================================================

const mockTemplates: Template[] = [
  {
    id: "carbon-tax",
    name: "Tax on Carbon Emissions",
    type: "carbon_tax",
    description: "Carbon tax policy",
    parameter_count: 2,
    parameter_groups: ["Mechanism", "Schedule"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
    category_id: "climate",
  },
  {
    id: "energy-subsidy",
    name: "Subsidy on Energy Consumption",
    type: "subsidy",
    description: "Energy subsidy policy",
    parameter_count: 3,
    parameter_groups: ["Mechanism", "Schedule", "Eligibility"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
    category_id: "energy",
  },
  {
    id: "transfer",
    name: "Income Transfer",
    type: "transfer",
    description: "Transfer policy",
    parameter_count: 2,
    parameter_groups: ["Mechanism", "Redistribution"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
    category_id: "social",
  },
];

const createCompositionEntry = (
  id: string,
  templateId: string,
  name: string,
): CompositionEntry => ({
  instanceId: id,
  templateId,
  name,
  parameters: {},
  rateSchedule: { "2025": 100 },
});

const createLoadedRef = () => ({ current: null as string | null });

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests
// ============================================================================

describe("usePortfolioSaveDialog — name suggestion freeze (Story 25.5)", () => {
  describe("AC-2: Deterministic name suggestions", () => {
    it("should suggest 'untitled-portfolio' for empty composition", () => {
      const loadedRef = createLoadedRef();
      const { result } = renderHook(() =>
        usePortfolioSaveDialog({
          templates: mockTemplates,
          composition: [],
          resolutionStrategy: "error",
          conflicts: [],
          loadedPortfolioRef: loadedRef,
          setActivePortfolioName: vi.fn(),
          updateScenarioPortfolioName: vi.fn(),
          setSelectedPortfolioName: vi.fn(),
          refetchPortfolios: vi.fn(),
        }),
      );

      act(() => {
        result.current.openSaveDialog();
      });

      expect(result.current.portfolioSaveName).toBe("untitled-portfolio");
    });

    it("should suggest slugified policy name for single policy", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
      ];
      const { result } = renderHook(() =>
        usePortfolioSaveDialog({
          templates: mockTemplates,
          composition,
          resolutionStrategy: "error",
          conflicts: [],
          loadedPortfolioRef: loadedRef,
          setActivePortfolioName: vi.fn(),
          updateScenarioPortfolioName: vi.fn(),
          setSelectedPortfolioName: vi.fn(),
          refetchPortfolios: vi.fn(),
        }),
      );

      act(() => {
        result.current.openSaveDialog();
      });

      expect(result.current.portfolioSaveName).toBe("tax-on-carbon-emissions");
    });

    it("should suggest 'slug1-plus-slug2' for two policies", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
        createCompositionEntry("ins2", "energy-subsidy", "Subsidy on Energy Consumption"),
      ];
      const { result } = renderHook(() =>
        usePortfolioSaveDialog({
          templates: mockTemplates,
          composition,
          resolutionStrategy: "error",
          conflicts: [],
          loadedPortfolioRef: loadedRef,
          setActivePortfolioName: vi.fn(),
          updateScenarioPortfolioName: vi.fn(),
          setSelectedPortfolioName: vi.fn(),
          refetchPortfolios: vi.fn(),
        }),
      );

      act(() => {
        result.current.openSaveDialog();
      });

      expect(result.current.portfolioSaveName).toBe(
        "tax-on-carbon-emissions-plus-subsidy-on-energy-consumption",
      );
    });

    it("should suggest 'first-slug-plus-(N-1)-more' for three+ policies", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
        createCompositionEntry("ins2", "energy-subsidy", "Subsidy on Energy Consumption"),
        createCompositionEntry("ins3", "transfer", "Income Transfer"),
      ];
      const { result } = renderHook(() =>
        usePortfolioSaveDialog({
          templates: mockTemplates,
          composition,
          resolutionStrategy: "error",
          conflicts: [],
          loadedPortfolioRef: loadedRef,
          setActivePortfolioName: vi.fn(),
          updateScenarioPortfolioName: vi.fn(),
          setSelectedPortfolioName: vi.fn(),
          refetchPortfolios: vi.fn(),
        }),
      );

      act(() => {
        result.current.openSaveDialog();
      });

      expect(result.current.portfolioSaveName).toBe("tax-on-carbon-emissions-plus-2-more");
    });
  });

  describe("AC-3: Manual name edit freezes suggestion", () => {
    it("should update suggestion when dialog reopens after composition change", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
      ];

      const { result, rerender } = renderHook(
        ({ composition }) =>
          usePortfolioSaveDialog({
            templates: mockTemplates,
            composition,
            resolutionStrategy: "error",
            conflicts: [],
            loadedPortfolioRef: loadedRef,
            setActivePortfolioName: vi.fn(),
            updateScenarioPortfolioName: vi.fn(),
            setSelectedPortfolioName: vi.fn(),
            refetchPortfolios: vi.fn(),
          }),
        { initialProps: { composition } },
      );

      // Open dialog with 1 policy
      act(() => {
        result.current.openSaveDialog();
      });
      expect(result.current.portfolioSaveName).toBe("tax-on-carbon-emissions");

      // Close dialog
      act(() => {
        result.current.closeSaveDialog();
      });

      // Add second policy
      const updatedComposition = [
        ...composition,
        createCompositionEntry("ins2", "energy-subsidy", "Subsidy on Energy Consumption"),
      ];

      rerender({ composition: updatedComposition });

      // Reopen dialog - should get new suggestion
      act(() => {
        result.current.openSaveDialog();
      });
      expect(result.current.portfolioSaveName).toBe(
        "tax-on-carbon-emissions-plus-subsidy-on-energy-consumption",
      );
    });

    it("should preserve manual name edit when composition changes", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
      ];

      const { result, rerender } = renderHook(
        ({ composition }) =>
          usePortfolioSaveDialog({
            templates: mockTemplates,
            composition,
            resolutionStrategy: "error",
            conflicts: [],
            loadedPortfolioRef: loadedRef,
            setActivePortfolioName: vi.fn(),
            updateScenarioPortfolioName: vi.fn(),
            setSelectedPortfolioName: vi.fn(),
            refetchPortfolios: vi.fn(),
          }),
        { initialProps: { composition } },
      );

      // Open dialog
      act(() => {
        result.current.openSaveDialog();
      });
      expect(result.current.portfolioSaveName).toBe("tax-on-carbon-emissions");

      // User manually edits name
      act(() => {
        result.current.handleSaveNameChange("my-custom-name");
      });
      expect(result.current.portfolioSaveName).toBe("my-custom-name");

      // Add second policy (simulated via rerender)
      const updatedComposition = [
        ...composition,
        createCompositionEntry("ins2", "energy-subsidy", "Subsidy on Energy Consumption"),
      ];

      rerender({ composition: updatedComposition });

      // Name should still be the manually edited one, NOT the new suggestion
      expect(result.current.portfolioSaveName).toBe("my-custom-name");
    });

    it("should reset manual edit flag when dialog closes and reopens", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
      ];

      const { result } = renderHook(() =>
        usePortfolioSaveDialog({
          templates: mockTemplates,
          composition,
          resolutionStrategy: "error",
          conflicts: [],
          loadedPortfolioRef: loadedRef,
          setActivePortfolioName: vi.fn(),
          updateScenarioPortfolioName: vi.fn(),
          setSelectedPortfolioName: vi.fn(),
          refetchPortfolios: vi.fn(),
        }),
      );

      // Open dialog
      act(() => {
        result.current.openSaveDialog();
      });
      expect(result.current.portfolioSaveName).toBe("tax-on-carbon-emissions");

      // User manually edits name
      act(() => {
        result.current.handleSaveNameChange("my-custom-name");
      });
      expect(result.current.portfolioSaveName).toBe("my-custom-name");

      // Close dialog
      act(() => {
        result.current.closeSaveDialog();
      });

      // Reopen dialog - should get fresh suggestion
      act(() => {
        result.current.openSaveDialog();
      });
      expect(result.current.portfolioSaveName).toBe("tax-on-carbon-emissions"); // Back to suggestion
    });

    it("should mark name as manually edited when user types in the input", () => {
      const loadedRef = createLoadedRef();
      const composition = [
        createCompositionEntry("ins1", "carbon-tax", "Tax on Carbon Emissions"),
      ];

      const { result } = renderHook(() =>
        usePortfolioSaveDialog({
          templates: mockTemplates,
          composition,
          resolutionStrategy: "error",
          conflicts: [],
          loadedPortfolioRef: loadedRef,
          setActivePortfolioName: vi.fn(),
          updateScenarioPortfolioName: vi.fn(),
          setSelectedPortfolioName: vi.fn(),
          refetchPortfolios: vi.fn(),
        }),
      );

      act(() => {
        result.current.openSaveDialog();
      });

      // User manually edits name
      act(() => {
        result.current.handleSaveNameChange("my-edited-name");
      });

      expect(result.current.portfolioSaveName).toBe("my-edited-name");
    });
  });
});
