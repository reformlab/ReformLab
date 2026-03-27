// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for ValidationGate component.
 * Story 20.5 — AC-3, AC-4.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/api/runs", () => ({
  checkMemory: vi.fn(),
}));

import { checkMemory } from "@/api/runs";
import { ValidationGate } from "../ValidationGate";
import type { ValidationContext } from "../validationChecks";

// ============================================================================
// Helpers
// ============================================================================

function makeContext(overrides: Partial<ValidationContext> = {}): ValidationContext {
  return {
    scenario: {
      id: "s1",
      name: "Test",
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: "My Portfolio",
      populationIds: ["fr-synthetic-2024"],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: null,
        investmentDecisionsEnabled: false,
        logitModel: null,
        discountRate: 0.03,
      },
      policyType: "carbon-tax",
      lastRunId: null,
    },
    populations: [{ id: "fr-synthetic-2024", name: "FR 2024", households: 100000, source: "INSEE", year: 2024 }],
    dataFusionResult: null,
    portfolios: [{ name: "My Portfolio", description: "", version_id: "v1", policy_count: 1 }],
    ...overrides,
  };
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
  // Default: memory check passes
  vi.mocked(checkMemory).mockResolvedValue({
    should_warn: false,
    estimated_gb: 2.0,
    available_gb: 16.0,
    message: "",
  });
});

// ============================================================================
// Tests
// ============================================================================

describe("ValidationGate — Story 20.5", () => {
  describe("AC-3: Check list display", () => {
    it("shows all check labels", () => {
      const onRun = vi.fn();
      render(<ValidationGate context={makeContext()} onRun={onRun} runLoading={false} />);
      expect(screen.getByText("Portfolio selected")).toBeInTheDocument();
      expect(screen.getByText("Population selected")).toBeInTheDocument();
      expect(screen.getByText("Time horizon valid")).toBeInTheDocument();
      expect(screen.getByText("Investment decisions calibrated")).toBeInTheDocument();
      expect(screen.getByText("Memory preflight")).toBeInTheDocument();
    });

    it("all sync checks passing → Run button is enabled", () => {
      const onRun = vi.fn();
      render(<ValidationGate context={makeContext()} onRun={onRun} runLoading={false} />);
      expect(screen.getByRole("button", { name: /run simulation/i })).not.toBeDisabled();
    });

    it("shows error message when portfolio check fails", () => {
      const ctx = makeContext({ scenario: { ...makeContext().scenario!, portfolioName: null } });
      render(<ValidationGate context={ctx} onRun={vi.fn()} runLoading={false} />);
      expect(screen.getByText(/no portfolio selected/i)).toBeInTheDocument();
    });

    it("shows error message when population check fails", () => {
      const ctx = makeContext({ scenario: { ...makeContext().scenario!, populationIds: [] } });
      render(<ValidationGate context={ctx} onRun={vi.fn()} runLoading={false} />);
      expect(screen.getByText(/no population selected/i)).toBeInTheDocument();
    });
  });

  describe("AC-4: Execution blocked on validation failure", () => {
    it("Run button is disabled when portfolio check fails (error)", () => {
      const ctx = makeContext({ scenario: { ...makeContext().scenario!, portfolioName: null } });
      render(<ValidationGate context={ctx} onRun={vi.fn()} runLoading={false} />);
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeDisabled();
    });

    it("Run button is disabled when population check fails (error)", () => {
      const ctx = makeContext({ scenario: { ...makeContext().scenario!, populationIds: [] } });
      render(<ValidationGate context={ctx} onRun={vi.fn()} runLoading={false} />);
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeDisabled();
    });

    it("Run button is disabled when time horizon fails (startYear >= endYear)", () => {
      const ctx = makeContext({
        scenario: {
          ...makeContext().scenario!,
          engineConfig: { ...makeContext().scenario!.engineConfig, startYear: 2030, endYear: 2025 },
        },
      });
      render(<ValidationGate context={ctx} onRun={vi.fn()} runLoading={false} />);
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeDisabled();
    });

    it("Run button is NOT disabled when only a warning check fails (calibration)", () => {
      const ctx = makeContext({
        scenario: {
          ...makeContext().scenario!,
          engineConfig: {
            ...makeContext().scenario!.engineConfig,
            investmentDecisionsEnabled: true,
            logitModel: "multinomial_logit" as const,
          },
        },
      });
      render(<ValidationGate context={ctx} onRun={vi.fn()} runLoading={false} />);
      expect(screen.getByRole("button", { name: /run simulation/i })).not.toBeDisabled();
    });

    it("clicking Run when all errors pass calls onRun", async () => {
      const user = userEvent.setup();
      const onRun = vi.fn();
      render(<ValidationGate context={makeContext()} onRun={onRun} runLoading={false} />);
      await user.click(screen.getByRole("button", { name: /run simulation/i }));
      await waitFor(() => {
        expect(onRun).toHaveBeenCalledTimes(1);
      });
    });

    it("clicking Run triggers async memoryPreflightCheck and shows loading state", async () => {
      const user = userEvent.setup();
      const onRun = vi.fn();
      // Slow memory check to capture loading state
      let resolve: (v: unknown) => void;
      vi.mocked(checkMemory).mockReturnValueOnce(
        new Promise((res) => { resolve = res; }),
      );

      render(<ValidationGate context={makeContext()} onRun={onRun} runLoading={false} />);
      await user.click(screen.getByRole("button", { name: /run simulation/i }));

      // Loading state visible
      await waitFor(() => {
        expect(screen.getByText(/checking memory/i)).toBeInTheDocument();
      });

      // Resolve the promise
      resolve!({ should_warn: false, estimated_gb: 2, available_gb: 16, message: "" });

      await waitFor(() => {
        expect(onRun).toHaveBeenCalled();
      });
    });

    it("does NOT call onRun when memory preflight blocks (should_warn: true)", async () => {
      const user = userEvent.setup();
      const onRun = vi.fn();
      vi.mocked(checkMemory).mockResolvedValueOnce({
        should_warn: true,
        estimated_gb: 15,
        available_gb: 16,
        message: "Memory may be insufficient",
      });

      render(<ValidationGate context={makeContext()} onRun={onRun} runLoading={false} />);
      await user.click(screen.getByRole("button", { name: /run simulation/i }));

      await waitFor(() => {
        expect(screen.getByText(/memory may be insufficient/i)).toBeInTheDocument();
      });
      expect(onRun).not.toHaveBeenCalled();
    });
  });
});
