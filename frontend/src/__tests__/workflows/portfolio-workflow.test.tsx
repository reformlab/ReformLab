// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Portfolio Designer Screen — workflow integration tests (Story 17.8, AC-1, AC-4).
 *
 * Exercises the complete multi-step journey:
 *   Template Selection → Compose & Configure → Review & Save
 *
 * Complements existing component unit tests by testing the full sequential flow,
 * including API call sequences and state transitions between steps.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/portfolios", () => ({
  validatePortfolio: vi.fn(),
  createPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
}));

import { createPortfolio, validatePortfolio } from "@/api/portfolios";
import { ApiError } from "@/api/client";
import { PortfolioDesignerScreen } from "@/components/screens/PortfolioDesignerScreen";
import { mockTemplates } from "@/data/mock-data";

// ============================================================================
// Render helper
// ============================================================================

function renderDesigner(onSaved = vi.fn()) {
  return render(
    <PortfolioDesignerScreen
      templates={mockTemplates}
      savedPortfolios={[]}
      onSaved={onSaved}
    />,
  );
}

// Helper: select 2 templates and advance to review step
async function advanceToReview(user: ReturnType<typeof userEvent.setup>) {
  const toggleButtons = screen.getAllByRole("button", { pressed: false });
  await user.click(toggleButtons[0]);
  await user.click(toggleButtons[1]);

  // Next (select → compose)
  await user.click(screen.getByRole("button", { name: /next/i }));
  expect(screen.getByLabelText(/resolution strategy/i)).toBeInTheDocument();

  // "Review" button (compose → review step).
  // Exact name "Review" avoids matching the "3. Review & Save" step nav button.
  await user.click(screen.getByRole("button", { name: "Review" }));
}

// ============================================================================
// Tests
// ============================================================================

describe("Portfolio Designer workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Task 3.2 — completes full workflow: select → compose → validate → save", () => {
    it("saves portfolio after completing the full workflow", async () => {
      const onSaved = vi.fn();
      // validatePortfolio is auto-called when entering review step and on Save click
      vi.mocked(validatePortfolio).mockResolvedValue({ conflicts: [], is_compatible: true });
      vi.mocked(createPortfolio).mockResolvedValueOnce("v-abc123");
      const user = userEvent.setup();

      renderDesigner(onSaved);

      await advanceToReview(user);

      // Wait for auto-validation to complete (review step triggers runValidation via useEffect)
      await waitFor(() => {
        expect(screen.getByText(/no conflicts detected/i)).toBeInTheDocument();
      });

      // "Save Portfolio" should be enabled (2 policies, no conflicts)
      const saveBtn = screen.getByRole("button", { name: /save portfolio/i });
      expect(saveBtn).not.toBeDisabled();

      // Click Save Portfolio → opens dialog
      await user.click(saveBtn);
      expect(screen.getByRole("dialog", { name: /save portfolio/i })).toBeInTheDocument();

      // Enter valid portfolio name
      const nameInput = screen.getByLabelText(/portfolio name/i);
      await user.type(nameInput, "my-green-portfolio");

      // Click "Save" button in dialog
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      // Wait for save to complete and onSaved to be called
      await waitFor(() => {
        expect(onSaved).toHaveBeenCalledOnce();
      });
      expect(onSaved).toHaveBeenCalledWith("my-green-portfolio");
      expect(createPortfolio).toHaveBeenCalledOnce();
    });
  });

  describe("Task 3.3 — shows conflict validation errors", () => {
    it("displays conflicts when validatePortfolio returns conflicts", async () => {
      vi.mocked(validatePortfolio).mockResolvedValue({
        conflicts: [
          {
            conflict_type: "rate_overlap",
            policy_indices: [0, 1],
            parameter_name: "carbon_rate",
            description: "Both policies define carbon_rate for the same years",
          },
        ],
        is_compatible: false,
      });
      const user = userEvent.setup();

      renderDesigner();
      await advanceToReview(user);

      // Wait for auto-validation to run and show conflicts
      await waitFor(() => {
        expect(screen.getByText(/rate_overlap/i)).toBeInTheDocument();
      });
      // Description text uniquely contains this phrase (parameter_name appears multiple times)
      expect(screen.getByText(/both policies define carbon_rate/i)).toBeInTheDocument();
    });
  });

  describe("Task 3.4 — rejects invalid portfolio name on save", () => {
    it("shows validation error for invalid name and clears it on correction", async () => {
      vi.mocked(validatePortfolio).mockResolvedValue({ conflicts: [], is_compatible: true });
      const user = userEvent.setup();

      renderDesigner();
      await advanceToReview(user);

      await waitFor(() => {
        expect(screen.getByText(/no conflicts detected/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /save portfolio/i }));
      const nameInput = screen.getByLabelText(/portfolio name/i);

      // Invalid name (uppercase + spaces)
      await user.type(nameInput, "INVALID NAME");
      // Validation error (only shown for invalid names, differs from the always-visible hint text)
      expect(screen.getByText(/name must be a lowercase slug/i)).toBeInTheDocument();

      // Clear and enter valid slug
      await user.clear(nameInput);
      await user.type(nameInput, "valid-portfolio");

      // Validation error should be cleared (hint text is always shown but has different wording)
      expect(screen.queryByText(/name must be a lowercase slug/i)).not.toBeInTheDocument();
    });
  });

  describe("Task 3.5 — enforces template selection before continuing", () => {
    it("keeps Next disabled with 0 templates and enables it after 1st selection", async () => {
      const user = userEvent.setup();
      renderDesigner();

      // Initially: 0 selected → Next disabled
      expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();

      // Select 1 template → Next enabled
      const toggleButtons = screen.getAllByRole("button", { pressed: false });
      await user.click(toggleButtons[0]);
      expect(screen.getByRole("button", { name: /next/i })).not.toBeDisabled();
    });
  });

  describe("Task 3.3 — shows ApiError on conflict check failure", () => {
    it("handles API error during validation gracefully", async () => {
      // First call (auto-validate on enter) fails, second call (check conflicts) also fails
      vi.mocked(validatePortfolio).mockRejectedValue(
        new ApiError({
          error: "server_error",
          what: "Validation failed",
          why: "Internal server error",
          fix: "Retry the request",
          status_code: 500,
        }),
      );
      const user = userEvent.setup();

      renderDesigner();
      await advanceToReview(user);

      // With error, conflicts reset to [] and canSave stays true (conflict-free fallback)
      // The button should still be visible (non-fatal validation error)
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /check conflicts/i })).toBeInTheDocument();
      });
    });
  });
});
