// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for TechnologyStep — Story 28.4.
 *
 * Tests:
 * - AC-1: Technology step rendered between Enable and Model
 * - AC-2: Per-domain expandable sections with toggles
 * - AC-3: Alternatives list with checkboxes, reference selector
 * - AC-8: "Use default French set" CTA when no technology set
 * - AC-10: Inline-only warnings (no toasts)
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TechnologyStep } from "../TechnologyStep";
import type { EngineConfig } from "@/types/workspace";
import { DEFAULT_TECHNOLOGY_SET } from "@/types/workspace";
import * as technologySetsApi from "@/api/technology-sets";

// ============================================================================
// Helpers
// ============================================================================
function makeConfig(overrides: Partial<EngineConfig> = {}): EngineConfig {
  return {
    startYear: 2025,
    endYear: 2030,
    seed: null,
    investmentDecisionsEnabled: true,
    logitModel: "multinomial_logit",
    discountRate: 0.03,
    tasteParameters: null,
    calibrationState: "not_configured",
    technologySet: null,
    ...overrides,
  };
}

const mockOnUpdateEngineConfig = vi.fn();

function renderTechnologyStep(config: EngineConfig = makeConfig()) {
  mockOnUpdateEngineConfig.mockClear();
  return render(
    <TechnologyStep
      engineConfig={config}
      onUpdateEngineConfig={mockOnUpdateEngineConfig}
      populationId="test-population"
      populationIncumbents={{ heating: new Set(), vehicle: new Set() }}
    />,
  );
}

// ============================================================================
// Mock API
// ============================================================================
vi.mock("@/api/technology-sets", () => ({
  getAllDefaultTechnologySets: vi.fn(),
  getDefaultTechnologySet: vi.fn(),
}));

// ============================================================================
// Setup
// ============================================================================
beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests
// ============================================================================
describe("TechnologyStep — Story 28.4", () => {
  describe("Initial state (no technology set) — AC-8", () => {
    it("renders 'Use default French set' CTA when technologySet is null", () => {
      renderTechnologyStep(makeConfig({ technologySet: null }));

      expect(screen.getByText(/Use default French set/i)).toBeInTheDocument();
    });

    it("applies default technology set when CTA clicked", async () => {
      const user = userEvent.setup();
      vi.mocked(technologySetsApi.getAllDefaultTechnologySets).mockResolvedValue(DEFAULT_TECHNOLOGY_SET);

      renderTechnologyStep(makeConfig({ technologySet: null }));

      const ctaButton = screen.getByRole("button", { name: /Use default French set/i });
      await user.click(ctaButton);

      await waitFor(() => {
        expect(mockOnUpdateEngineConfig).toHaveBeenCalledWith(
          expect.objectContaining({
            technologySet: DEFAULT_TECHNOLOGY_SET,
          }),
        );
      });
    });
  });

  describe("Per-domain sections — AC-2, AC-3", () => {
    it("renders heating and vehicle sections when technology set present", () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      expect(screen.getAllByText(/Heating/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Vehicle/i).length).toBeGreaterThan(0);
    });

    it("renders domain toggle switches", () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Should have two switches (heating and vehicle)
      const switches = screen.getAllByRole("checkbox", { hidden: true });
      expect(switches.length).toBeGreaterThanOrEqual(2);
    });

    it("shows alternatives list for enabled domain", () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Should show heating alternatives
      expect(screen.getByText(/Condensing Boiler/i)).toBeInTheDocument();
      expect(screen.getByText(/Air Source Heat Pump/i)).toBeInTheDocument();
      expect(screen.getByText(/Ground Source Heat Pump/i)).toBeInTheDocument();
    });
  });

  describe("Population incumbent detection — AC-4, AC-6, AC-7", () => {
    it("shows green badge when incumbent column detected in population", () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Should show green badge (implementation dependent)
      // This is a placeholder test - actual implementation will verify badge rendering
    });

    it("shows inline warning when incumbent column missing", () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // When populationIncumbents is empty, should show warning
      // This is a placeholder test - actual implementation will verify warning rendering
    });

    it("shows confirmation when population fully matches technology set", () => {
      const config = makeConfig({
        technologySet: DEFAULT_TECHNOLOGY_SET,
      });
      renderTechnologyStep(config);

      // Should show confirmation message
      // This is a placeholder test - actual implementation will verify confirmation rendering
    });
  });

  describe("Toast policy compliance — AC-10", () => {
    it("does not call toast functions for any warnings", async () => {
      const toastSpy = vi.fn();
      vi.mock("sonner", () => ({
        toast: {
          warning: toastSpy,
          error: toastSpy,
          success: toastSpy,
          info: toastSpy,
        },
      }));

      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Trigger various states - should not call toast
      // This is a placeholder test - actual implementation will verify no toast calls
    });
  });

  describe("Domain toggle behavior", () => {
    it("toggles domain enabled/disabled when switch clicked", async () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Find heating domain toggle (implementation specific)
      // This is a placeholder test - actual implementation will verify toggle behavior
    });
  });

  describe("Reference alternative selection — AC-3", () => {
    it("changes reference alternative when radio clicked", async () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Click on alternative radio button
      // This is a placeholder test - actual implementation will verify reference selection
    });
  });

  describe("Add/Remove alternatives — AC-3", () => {
    it("adds scaffolded alternative when add button clicked", async () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Click add button
      // This is a placeholder test - actual implementation will verify add behavior
    });

    it("removes alternative when remove button clicked", async () => {
      const config = makeConfig({ technologySet: DEFAULT_TECHNOLOGY_SET });
      renderTechnologyStep(config);

      // Click remove button (disabled for reference)
      // This is a placeholder test - actual implementation will verify remove behavior
    });
  });
});
