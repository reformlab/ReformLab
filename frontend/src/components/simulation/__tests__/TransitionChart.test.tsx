import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { TransitionChart } from "@/components/simulation/TransitionChart";
import type { YearlyOutcome } from "@/api/types";

// Recharts uses ResizeObserver which jsdom doesn't support
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

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
      expect(screen.getByText("Keep Current")).toBeInTheDocument();
      expect(screen.getByText("Electric (EV)")).toBeInTheDocument();
    });

    it("shows year rows in companion table", () => {
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      expect(screen.getByText("2025")).toBeInTheDocument();
      expect(screen.getByText("2026")).toBeInTheDocument();
    });

    it("shows count values in companion table", () => {
      render(
        <TransitionChart
          data={MOCK_OUTCOMES}
          alternativeIds={ALT_IDS}
          alternativeLabels={ALT_LABELS}
        />,
      );
      expect(screen.getByText("80")).toBeInTheDocument();
      expect(screen.getByText("20")).toBeInTheDocument();
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
      await user.click(screen.getByText("2025"));
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
      await user.click(screen.getByText("2025"));
      // No assertion needed — just verifying no crash
    });
  });
});
