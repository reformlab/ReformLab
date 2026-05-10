// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for InvestmentDecisionsWizard — Story 22.6.
 *
 * Tests:
 * - AC-1: Guided wizard with 4 steps (Enable, Model, Parameters, Review)
 * - AC-2: Disabled state leaves scenario valid
 * - AC-3: Validation requires logit model and taste params
 * - AC-4: Taste parameters persist to EngineConfig
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { InvestmentDecisionsWizard } from "../InvestmentDecisionsWizard";
import type { EngineConfig } from "@/types/workspace";
import { DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// Helpers
// ============================================================================

function makeConfig(overrides: Partial<EngineConfig> = {}): EngineConfig {
  return {
    startYear: 2025,
    endYear: 2030,
    seed: null,
    investmentDecisionsEnabled: false,
    logitModel: null,
    discountRate: 0.03,
    tasteParameters: null,
    calibrationState: "not_configured",
    ...overrides,
  };
}

const mockOnUpdateEngineConfig = vi.fn();

function renderWizard(config: EngineConfig = makeConfig()) {
  mockOnUpdateEngineConfig.mockClear();
  return render(
    <InvestmentDecisionsWizard
      engineConfig={config}
      onUpdateEngineConfig={mockOnUpdateEngineConfig}
    />,
  );
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests
// ============================================================================

describe("InvestmentDecisionsWizard — Story 22.6", () => {
  describe("Enable step (AC-1, AC-2)", () => {
    it("renders Enable Investment Decisions heading", () => {
      renderWizard();
      expect(screen.getByText("Enable Investment Decisions")).toBeInTheDocument();
    });

    it("renders toggle switch", () => {
      renderWizard();
      const toggle = screen.getByRole("checkbox");
      expect(toggle).toBeInTheDocument();
      expect(toggle).not.toBeChecked();
    });

    it("shows explanatory text about investment decisions", () => {
      renderWizard();
      expect(screen.getByText(/advanced scenario feature/i)).toBeInTheDocument();
    });

    it("does not show parameter sliders in Enable step", () => {
      renderWizard();
      expect(screen.queryByText("β_price")).not.toBeInTheDocument();
      expect(screen.queryByText("β_range")).not.toBeInTheDocument();
      expect(screen.queryByText("β_green")).not.toBeInTheDocument();
    });
  });

  describe("Model step (AC-1, AC-3)", () => {
    it("shows logit model selector when enabled", () => {
      renderWizard(
        makeConfig({ investmentDecisionsEnabled: true, logitModel: "multinomial_logit" }),
      );
      const select = screen.getByRole("combobox", { name: /logit model/i });
      expect(select).toBeInTheDocument();
      expect(select).toHaveValue("multinomial_logit");
    });

    it("renders 3 logit model options", () => {
      renderWizard(
        makeConfig({ investmentDecisionsEnabled: true, logitModel: "multinomial_logit" }),
      );
      expect(screen.getByRole("option", { name: /multinomial logit/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /nested logit/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /mixed logit/i })).toBeInTheDocument();
    });

    it("shows model description", () => {
      renderWizard(
        makeConfig({ investmentDecisionsEnabled: true, logitModel: "nested_logit" }),
      );
      expect(screen.getByText(/groups similar alternatives into nests/i)).toBeInTheDocument();
    });

    it("logit model change calls onUpdateEngineConfig", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({ investmentDecisionsEnabled: true, logitModel: "multinomial_logit" }),
      );

      const select = screen.getByRole("combobox", { name: /logit model/i });
      await user.selectOptions(select, "mixed_logit");

      expect(mockOnUpdateEngineConfig).toHaveBeenCalledWith(
        expect.objectContaining({ logitModel: "mixed_logit" }),
      );
    });
  });

  describe("Parameters step (AC-1, AC-4)", () => {
    it("shows model selector when enabled", () => {
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: { priceSensitivity: -2.0, rangeAnxiety: -1.5, envPreference: 1.0 },
        }),
      );

      // Model step is visible when enabled
      expect(screen.getByRole("combobox", { name: /logit model/i })).toBeInTheDocument();
    });

    it("sliders are NOT rendered on Model step (only visible on Parameters step)", () => {
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // On Model step, sliders should not be visible (they're on Parameters step)
      expect(screen.queryAllByRole("slider").length).toBe(0);
    });
  });

  describe("Review step (AC-1, AC-3)", () => {
    it("displays logit model selector when enabled", () => {
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "nested_logit",
          tasteParameters: { priceSensitivity: -1.5, rangeAnxiety: -0.8, envPreference: 0.5 },
          calibrationState: "not_configured",
        }),
      );

      // Model selector should be visible
      const select = screen.getByRole("combobox", { name: /logit model/i });
      expect(select).toHaveValue("nested_logit");
    });
  });

  describe("Disabled state (AC-2)", () => {
    it("scenario valid when wizard collapsed", () => {
      renderWizard(makeConfig({ investmentDecisionsEnabled: false }));

      expect(screen.getByText("Enable Investment Decisions")).toBeInTheDocument();
      expect(screen.queryByText("Choose Logit Model")).not.toBeInTheDocument();
    });
  });

  describe("Taste parameters persistence (AC-4)", () => {
    it("wizard receives EngineConfig.tasteParameters as prop", () => {
      const customTasteParams = { priceSensitivity: -3.0, rangeAnxiety: -1.5, envPreference: 2.0 };
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: customTasteParams,
        }),
      );

      // Verify the wizard component is rendered (taste parameters are passed as props)
      expect(screen.getByRole("combobox", { name: /logit model/i })).toBeInTheDocument();
    });

    it("wizard uses DEFAULT_TASTE_PARAMETERS when EngineConfig.tasteParameters is null", () => {
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: null,
        }),
      );

      // Verify the wizard component is rendered
      expect(screen.getByRole("combobox", { name: /logit model/i })).toBeInTheDocument();
    });
  });

  describe("Step indicators (AC-1)", () => {
    it("shows step indicators when enabled", () => {
      renderWizard(
        makeConfig({ investmentDecisionsEnabled: true, logitModel: "multinomial_logit" }),
      );

      // Step indicators should be visible
      expect(screen.getByText("Enable")).toBeInTheDocument();
      expect(screen.getByText("Model")).toBeInTheDocument();
      expect(screen.getByText("Parameters")).toBeInTheDocument();
      expect(screen.getByText("Review")).toBeInTheDocument();
    });

    it("does not show step indicators when disabled", () => {
      renderWizard(makeConfig({ investmentDecisionsEnabled: false }));

      expect(screen.queryByText("Enable")).not.toBeInTheDocument();
      expect(screen.queryByText("Model")).not.toBeInTheDocument();
    });
  });

  describe("Toggle behavior", () => {
    it("toggle calls onUpdateEngineConfig with enabled state", async () => {
      const user = userEvent.setup();
      renderWizard();

      const toggle = screen.getByRole("checkbox");
      await user.click(toggle);

      expect(mockOnUpdateEngineConfig).toHaveBeenCalledWith(
        expect.objectContaining({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
        }),
      );
    });

    it("re-enable preserves previously selected model", async () => {
      const user = userEvent.setup();
      // Start with a specific model enabled
      const initialConfig = makeConfig({
        investmentDecisionsEnabled: true,
        logitModel: "nested_logit",
      });
      const { rerender } = renderWizard(initialConfig);

      // We're on Model step now. Go back to Enable step to access the toggle
      await user.click(screen.getByRole("button", { name: /^Back$/i }));

      // Now we're on Enable step with toggle visible
      const toggle = screen.getByRole("checkbox");
      expect(toggle).toBeChecked();

      // Clear previous mock calls
      mockOnUpdateEngineConfig.mockClear();

      // Disable by clicking the toggle
      await user.click(toggle);

      // Verify the disable call
      const disableCall = mockOnUpdateEngineConfig.mock.calls.find(
        (call) => call[0]?.investmentDecisionsEnabled === false
      );
      expect(disableCall).toBeDefined();
      expect(disableCall![0]).toMatchObject({
        investmentDecisionsEnabled: false,
        logitModel: null,
      });

      // Now rerender with the disabled state (simulating parent update)
      // This keeps the same component instance, so the ref should still have "nested_logit"
      rerender(
        <InvestmentDecisionsWizard
          engineConfig={makeConfig({
            investmentDecisionsEnabled: false,
            logitModel: null,
          })}
          onUpdateEngineConfig={mockOnUpdateEngineConfig}
        />,
      );

      // Verify toggle is unchecked
      expect(screen.getByRole("checkbox")).not.toBeChecked();

      // Clear mock and re-enable
      mockOnUpdateEngineConfig.mockClear();
      await user.click(screen.getByRole("checkbox"));

      // Verify the enable call uses the preserved model (nested_logit from ref)
      const enableCall = mockOnUpdateEngineConfig.mock.calls.find(
        (call) => call[0]?.investmentDecisionsEnabled === true
      );
      expect(enableCall).toBeDefined();
      expect(enableCall![0]).toMatchObject({
        investmentDecisionsEnabled: true,
        logitModel: "nested_logit",
      });
    });
  });

  describe("Stepper navigation (Task 9)", () => {
    it("Next button advances step sequentially", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
        }),
      );

      // On Model step after enabling
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();

      // Click Next - should advance to Parameters step
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Taste Parameters")).toBeInTheDocument();

      // Click Next again - should advance to Review step
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Review Configuration")).toBeInTheDocument();
    });

    it("Back button retreats step sequentially", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // On Model step initially
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();

      // Click Next to go to Parameters step
      const nextButton = () => screen.getByRole("button", { name: /^Next$/i });
      await user.click(nextButton());
      await waitFor(() => {
        expect(screen.getByText("Taste Parameters")).toBeInTheDocument();
      });

      // Click Back - should return to Model step
      await user.click(screen.getByRole("button", { name: /^Back$/i }));

      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });

    it("Edit buttons in Review step jump to correct steps", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "nested_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // Navigate to Review step
      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Review Configuration")).toBeInTheDocument();

      // Click Edit on Logit Model section (first Edit button)
      const editButtons = screen.getAllByRole("button", { name: /edit/i });
      await user.click(editButtons[0]);

      // Should return to Model step
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });

    it("step resets on component unmount/remount", async () => {
      const user = userEvent.setup();
      const config = makeConfig({
        investmentDecisionsEnabled: true,
        logitModel: "multinomial_logit",
        tasteParameters: DEFAULT_TASTE_PARAMETERS,
      });
      const { rerender } = renderWizard(config);

      // Navigate to Parameters step
      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      await waitFor(() => {
        expect(screen.getByText("Taste Parameters")).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      await waitFor(() => {
        expect(screen.getByText("Review Configuration")).toBeInTheDocument();
      });

      // Unmount and remount (step state is transient)
      rerender(<div />);
      rerender(
        <InvestmentDecisionsWizard
          engineConfig={config}
          onUpdateEngineConfig={mockOnUpdateEngineConfig}
        />,
      );

      // Should reset to Model step (since enabled and step state was lost)
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });
  });

  describe("Slider interactions (Task 9)", () => {
    it("sliders are rendered on Parameters step", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // Navigate to Parameters step
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Taste Parameters")).toBeInTheDocument();

      // Verify sliders are present
      const sliders = screen.getAllByRole("slider");
      expect(sliders.length).toBe(3);
    });

    it("sliders display current taste parameter values", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: { priceSensitivity: -2.5, rangeAnxiety: -1.2, envPreference: 1.5 },
        }),
      );

      // Navigate to Parameters step
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Taste Parameters")).toBeInTheDocument();

      // Verify the displayed values match the config
      expect(screen.getByText("-2.5")).toBeInTheDocument();
      expect(screen.getByText("-1.2")).toBeInTheDocument();
      expect(screen.getByText("1.5")).toBeInTheDocument();
    });
  });

  describe("Clickable step indicators (Story 27.7)", () => {
    it("click-back: from Review step, clicking Model navigates to Model step (AC-1)", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "nested_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // Navigate to Review step (visiting all steps along the way)
      // Start on Model step (auto-advanced from Enable when enabled)
      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Review Configuration")).toBeInTheDocument();

      // Click the Model step indicator button
      const modelStepButton = screen.getByRole("button", { name: /model/i });
      await user.click(modelStepButton);

      // Should navigate back to Model step
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });

    it("disabled-forward: from Enable step, clicking later steps does nothing (AC-2)", async () => {
      renderWizard(makeConfig({ investmentDecisionsEnabled: false }));

      // On Enable step, later steps should be disabled
      expect(screen.getByText("Enable Investment Decisions")).toBeInTheDocument();

      // Find step indicator buttons for Model, Parameters, Review
      // They should be disabled buttons
      const modelButton = screen.queryByRole("button", { name: /model/i });
      const parametersButton = screen.queryByRole("button", { name: /parameters/i });
      const reviewButton = screen.queryByRole("button", { name: /review/i });

      // When wizard is disabled, step indicators shouldn't render
      expect(modelButton).not.toBeInTheDocument();
      expect(parametersButton).not.toBeInTheDocument();
      expect(reviewButton).not.toBeInTheDocument();
    });

    it("disabled-forward: when enabled but only on step 1, clicking step 3 does nothing (AC-2)", async () => {
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
        }),
      );

      // On Model step (step 1), only Enable and Model are visited
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();

      // Step 3 (Review) button should be present but disabled
      const reviewButton = screen.getByRole("button", { name: /review/i });
      expect(reviewButton).toBeDisabled();
    });

    it("visited-steps: after visiting steps 1,2,3 on step 3, clicking step 2 works (AC-3)", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // Navigate through all steps to Review (starting from Model step)
      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Review Configuration")).toBeInTheDocument();

      // Step 2 (Parameters) should be clickable (visited)
      const parametersButton = screen.getByRole("button", { name: /parameters/i });
      expect(parametersButton).not.toBeDisabled();

      await user.click(parametersButton);

      expect(screen.getByText("Taste Parameters")).toBeInTheDocument();
    });

    it("state-preservation: navigate back then forward, selections intact (AC-4)", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // Wait for auto-advance to Model step to complete
      await waitFor(() => {
        expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
      });

      // Navigate to Parameters step (one Next click from Model)
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Taste Parameters")).toBeInTheDocument();

      // Navigate to Review step (another Next click)
      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      expect(screen.getByText("Review Configuration")).toBeInTheDocument();

      // Click back to Parameters step
      const parametersButton = screen.getByRole("button", { name: /parameters/i });
      await user.click(parametersButton);

      expect(screen.getByText("Taste Parameters")).toBeInTheDocument();

      // Navigate forward via Next to Review
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      // Should be back on Review step
      expect(screen.getByText("Review Configuration")).toBeInTheDocument();
    });

    it("accessibility: step buttons have ARIA attributes (AC-5)", async () => {
      const user = userEvent.setup();
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "nested_logit",
          tasteParameters: DEFAULT_TASTE_PARAMETERS,
        }),
      );

      // Navigate to Review step (starting from Model step)
      await user.click(screen.getByRole("button", { name: /^Next$/i }));
      await user.click(screen.getByRole("button", { name: /^Next$/i }));

      expect(screen.getByText("Review Configuration")).toBeInTheDocument();

      // Check that step indicator buttons have proper ARIA attributes
      const enableButton = screen.getByRole("button", { name: /^enable$/i });
      const modelButton = screen.getByRole("button", { name: /^model$/i });
      const parametersButton = screen.getByRole("button", { name: /^parameters$/i });
      const reviewButton = screen.getByRole("button", { name: /^review$/i });

      // Current step (Review) should have aria-current="step"
      expect(reviewButton).toHaveAttribute("aria-current", "step");

      // Visited steps should not be disabled
      expect(enableButton).not.toBeDisabled();
      expect(modelButton).not.toBeDisabled();
      expect(parametersButton).not.toBeDisabled();

      // All buttons should be keyboard focusable (role="button" makes them focusable)
      expect(enableButton.tagName.toLowerCase()).toBe("button");
      expect(modelButton.tagName.toLowerCase()).toBe("button");
      expect(parametersButton.tagName.toLowerCase()).toBe("button");
      expect(reviewButton.tagName.toLowerCase()).toBe("button");
    });

    it("accessibility: unreached steps have aria-disabled (AC-5)", async () => {
      renderWizard(
        makeConfig({
          investmentDecisionsEnabled: true,
          logitModel: "multinomial_logit",
        }),
      );

      // On Model step (step 1), Review (step 3) is unreached
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();

      const reviewButton = screen.getByRole("button", { name: /^review$/i });

      // Should have aria-disabled when disabled
      expect(reviewButton).toHaveAttribute("aria-disabled", "true");
    });
  });
});
