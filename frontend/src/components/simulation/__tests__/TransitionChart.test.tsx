// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { TransitionChart } from "@/components/simulation/TransitionChart";
import type { YearlyOutcome } from "@/api/types";
import {
  renderedAreaPaths,
  setupRechartsResponsiveContainerMock,
} from "./recharts-test-utils";

setupRechartsResponsiveContainerMock();

const ALT_IDS = ["keep_current", "buy_ev"];
const ALT_LABELS: Record<string, string> = {
  keep_current: "Keep Current",
  buy_ev: "Electric (EV)",
};

const MOCK_OUTCOMES: YearlyOutcome[] = [
  {
    year: 2025,
    total_households: 100,
    counts: { keep_current: 80, buy_ev: 20 },
    percentages: { keep_current: 80, buy_ev: 20 },
    mean_probabilities: null,
  },
  {
    year: 2026,
    total_households: 100,
    counts: { keep_current: 60, buy_ev: 40 },
    percentages: { keep_current: 60, buy_ev: 40 },
    mean_probabilities: null,
  },
];

describe("TransitionChart", () => {
  describe("rendering", () => {
    it("renders without crashing with valid data", () => {
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("renders SVG paths for the stacked areas", async () => {
      const { container } = render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );

      await waitFor(() => {
        const areaPaths = renderedAreaPaths(container);
        expect(areaPaths.length).toBeGreaterThanOrEqual(ALT_IDS.length);
      });
    });

    it("renders one companion table body row per year", () => {
      const { container } = render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      const rows = container.querySelectorAll("tbody tr");

      expect(rows).toHaveLength(MOCK_OUTCOMES.length);
    });

    it("renders no-data message when data is empty", () => {
      render(
        <TransitionChart
          data={[]}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      expect(screen.queryByRole("table")).not.toBeInTheDocument();
      expect(screen.getByText(/No decision data available/i)).toBeInTheDocument();
    });

    it("shows alternative label headers in companion table", () => {
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      const table = within(screen.getByRole("table"));
      expect(table.getByText("Keep Current")).toBeInTheDocument();
      expect(table.getByText("Electric (EV)")).toBeInTheDocument();
    });

    it("shows year rows in companion table", () => {
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      const table = within(screen.getByRole("table"));
      expect(table.getByText("2025")).toBeInTheDocument();
      expect(table.getByText("2026")).toBeInTheDocument();
    });

    it("shows count values in companion table", () => {
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      const table = within(screen.getByRole("table"));
      expect(table.getByText("80")).toBeInTheDocument();
      expect(table.getByText("20")).toBeInTheDocument();
    });
  });

  describe("year click interaction", () => {
    it("calls onYearClick with correct year when row clicked", async () => {
      const onYearClick = vi.fn();
      const user = userEvent.setup();
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
          onYearClick={onYearClick}
        />,
      );
      await user.click(within(screen.getByRole("table")).getByText("2025"));
      expect(onYearClick).toHaveBeenCalledWith(2025);
    });

    it("does not call onYearClick when handler not provided", async () => {
      const user = userEvent.setup();
      // Should not throw
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      await user.click(within(screen.getByRole("table")).getByText("2025"));
      // No assertion needed — just verifying no crash
    });
  });
});
