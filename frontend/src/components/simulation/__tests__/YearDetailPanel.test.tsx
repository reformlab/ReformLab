// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { YearDetailPanel } from "@/components/simulation/YearDetailPanel";
import type { YearlyOutcome, DomainSummary } from "@/api/types";

// Recharts uses ResizeObserver which jsdom doesn't support
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const MOCK_DOMAIN: DomainSummary = {
  domain_name: "vehicle",
  alternative_ids: ["keep_current", "buy_ev"],
  alternative_labels: { keep_current: "Keep Current", buy_ev: "Electric (EV)" },
  yearly_outcomes: [],
  eligibility: { n_total: 100, n_eligible: 70, n_ineligible: 30 },
};

const MOCK_OUTCOME_WITH_PROBS: YearlyOutcome = {
  year: 2025,
  total_households: 100,
  counts: { keep_current: 80, buy_ev: 20 },
  percentages: { keep_current: 80, buy_ev: 20 },
  mean_probabilities: { keep_current: 0.72, buy_ev: 0.28 },
};

const MOCK_OUTCOME_NO_PROBS: YearlyOutcome = {
  year: 2025,
  total_households: 100,
  counts: { keep_current: 80, buy_ev: 20 },
  percentages: { keep_current: 80, buy_ev: 20 },
  mean_probabilities: null,
};

describe("YearDetailPanel", () => {
  describe("rendering", () => {
    it("renders year in header", () => {
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={MOCK_DOMAIN}
          onClose={vi.fn()}
        />,
      );
      expect(screen.getByText(/Year 2025/)).toBeInTheDocument();
    });

    it("shows mean probabilities table when probabilities are present", () => {
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={MOCK_DOMAIN}
          onClose={vi.fn()}
        />,
      );
      expect(screen.getByText("Mean Choice Probabilities")).toBeInTheDocument();
      expect(screen.queryByText(/Probability data not available/i)).not.toBeInTheDocument();
    });

    it("shows 'Probability data not available' when mean_probabilities is null", () => {
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_NO_PROBS}
          domain={MOCK_DOMAIN}
          onClose={vi.fn()}
        />,
      );
      expect(screen.getByText(/Probability data not available/i)).toBeInTheDocument();
    });

    it("shows eligibility section when domain.eligibility is non-null", () => {
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={MOCK_DOMAIN}
          onClose={vi.fn()}
        />,
      );
      expect(screen.getByText("Eligibility")).toBeInTheDocument();
      expect(screen.getByText("70")).toBeInTheDocument(); // n_eligible
    });

    it("hides eligibility section when domain.eligibility is null", () => {
      const domainNoEligibility: DomainSummary = { ...MOCK_DOMAIN, eligibility: null };
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={domainNoEligibility}
          onClose={vi.fn()}
        />,
      );
      expect(screen.queryByText("Eligibility")).not.toBeInTheDocument();
    });

    it("renders alternative labels in probability table", () => {
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={MOCK_DOMAIN}
          onClose={vi.fn()}
        />,
      );
      // The labels appear in the probability table
      const labels = screen.getAllByText("Keep Current");
      expect(labels.length).toBeGreaterThan(0);
      const evLabels = screen.getAllByText("Electric (EV)");
      expect(evLabels.length).toBeGreaterThan(0);
    });
  });

  describe("dismiss behavior", () => {
    it("calls onClose when close button clicked", async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={MOCK_DOMAIN}
          onClose={onClose}
        />,
      );
      await user.click(screen.getByRole("button", { name: /close/i }));
      expect(onClose).toHaveBeenCalledOnce();
    });

    it("calls onClose when Escape key pressed", async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      render(
        <YearDetailPanel
          year={2025}
          outcome={MOCK_OUTCOME_WITH_PROBS}
          domain={MOCK_DOMAIN}
          onClose={onClose}
        />,
      );
      await user.keyboard("{Escape}");
      expect(onClose).toHaveBeenCalledOnce();
    });
  });
});
