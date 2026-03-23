// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Data Fusion Workbench — workflow integration tests (Story 17.8, AC-1, AC-3, AC-4).
 *
 * Exercises the complete multi-step journey:
 *   Source Selection → Variable Review → Method Selection → Generation → Preview
 *
 * These tests verify the API call sequence and state transitions
 * across the full 5-step flow, complementing the existing component unit tests.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/data-fusion", () => ({
  generatePopulation: vi.fn(),
}));

import { generatePopulation } from "@/api/data-fusion";
import { ApiError } from "@/api/client";
import { DataFusionWorkbench } from "@/components/screens/DataFusionWorkbench";
import { mockDataSources, mockMergeMethods } from "@/data/mock-data";
import { mockGenerationResult } from "./helpers";

// ============================================================================
// Render helper
// ============================================================================

function renderWorkbench(onPopulationGenerated = vi.fn()) {
  return render(
    <DataFusionWorkbench
      sources={mockDataSources}
      methods={mockMergeMethods}
      initialResult={null}
      onPopulationGenerated={onPopulationGenerated}
    />,
  );
}

// ============================================================================
// Tests
// ============================================================================

describe("Data Fusion workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Task 2.2 — completes full workflow: sources → overlap → method → generate → preview", () => {
    it("generates population and shows preview after full workflow", async () => {
      const onPopulationGenerated = vi.fn();
      vi.mocked(generatePopulation).mockResolvedValueOnce(mockGenerationResult());
      const user = userEvent.setup();

      renderWorkbench(onPopulationGenerated);

      // Sources step: select 2 data sources
      const toggleButtons = screen.getAllByRole("button", { pressed: false });
      await user.click(toggleButtons[0]);
      await user.click(toggleButtons[1]);

      // Advance to overlap step
      await user.click(screen.getByRole("button", { name: /next/i }));
      expect(screen.getByRole("region", { name: /variable overlap/i })).toBeInTheDocument();

      // Advance to method step
      await user.click(screen.getByRole("button", { name: /next/i }));
      // Method step: button text is "Generate Population"
      expect(screen.getByRole("button", { name: /generate population/i })).toBeInTheDocument();

      // Click "Generate Population" → triggers API → moves to preview
      await user.click(screen.getByRole("button", { name: /generate population/i }));

      // Wait for the async generation to complete and preview step to render
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /regenerate/i })).toBeInTheDocument();
      });

      // Verify callback was invoked with the result
      expect(onPopulationGenerated).toHaveBeenCalledOnce();
      expect(onPopulationGenerated).toHaveBeenCalledWith(mockGenerationResult());
    });
  });

  describe("Task 2.3 — shows error when generation fails", () => {
    it("displays error state when generatePopulation rejects", async () => {
      vi.mocked(generatePopulation).mockRejectedValueOnce(
        new ApiError({
          error: "generation_failed",
          what: "Population generation failed",
          why: "Incompatible variable schemas between sources",
          fix: "Select sources with overlapping variables",
          status_code: 422,
        }),
      );
      const user = userEvent.setup();

      renderWorkbench();

      // Select 2 sources → overlap → method
      const toggleButtons = screen.getAllByRole("button", { pressed: false });
      await user.click(toggleButtons[0]);
      await user.click(toggleButtons[1]);
      await user.click(screen.getByRole("button", { name: /next/i }));
      await user.click(screen.getByRole("button", { name: /next/i }));

      // Trigger generation
      await user.click(screen.getByRole("button", { name: /generate population/i }));

      // Generation is async — wait for error section to appear.
      // PopulationGenerationProgress renders aria-label="Generation failed" when errorDetail is set.
      await waitFor(() => {
        expect(screen.getByLabelText("Generation failed")).toBeInTheDocument();
      });
      expect(vi.mocked(generatePopulation)).toHaveBeenCalledOnce();
      // Verify what/why/fix content is rendered (AC-3: regression detection)
      expect(screen.getByText("Population generation failed")).toBeInTheDocument();
      expect(screen.getByText("Incompatible variable schemas between sources")).toBeInTheDocument();
    });
  });

  describe("Task 2.4 — enforces minimum 2 source selection before advancing", () => {
    it("keeps Next disabled with 0 sources and enables it after 2nd selection", async () => {
      const user = userEvent.setup();
      renderWorkbench();

      // Initially: 0 selected → Next disabled
      expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();

      // Select first source
      const toggleButtons = screen.getAllByRole("button", { pressed: false });
      await user.click(toggleButtons[0]);
      expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();

      // Select second source → Next enabled
      await user.click(toggleButtons[1]);
      expect(screen.getByRole("button", { name: /next/i })).not.toBeDisabled();

      // Advance to overlap step
      await user.click(screen.getByRole("button", { name: /next/i }));
      expect(screen.getByRole("region", { name: /variable overlap/i })).toBeInTheDocument();
    });
  });

  describe("Task 2.5 — allows navigating back through completed steps", () => {
    it("navigates back through steps preserving selections", async () => {
      const user = userEvent.setup();
      renderWorkbench();

      // Select 2 sources and advance to overlap
      const toggleButtons = screen.getAllByRole("button", { pressed: false });
      await user.click(toggleButtons[0]);
      await user.click(toggleButtons[1]);
      await user.click(screen.getByRole("button", { name: /next/i }));
      expect(screen.getByRole("region", { name: /variable overlap/i })).toBeInTheDocument();

      // Advance to method step
      await user.click(screen.getByRole("button", { name: /next/i }));
      expect(screen.getByRole("button", { name: /generate population/i })).toBeInTheDocument();

      // Back to overlap
      await user.click(screen.getByRole("button", { name: /back/i }));
      expect(screen.getByRole("region", { name: /variable overlap/i })).toBeInTheDocument();

      // Back to sources — verify selection count preserved (2 selected)
      await user.click(screen.getByRole("button", { name: /back/i }));
      expect(screen.getByRole("region", { name: /data source browser/i })).toBeInTheDocument();
      expect(screen.getByText(/2 selected/i)).toBeInTheDocument();
    });
  });
});
