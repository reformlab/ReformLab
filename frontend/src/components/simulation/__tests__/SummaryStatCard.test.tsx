import { render, screen } from "@testing-library/react";

import { SummaryStatCard } from "@/components/simulation/SummaryStatCard";
import type { SummaryStatistic } from "@/data/mock-data";

describe("SummaryStatCard", () => {
  it("renders label, value, and trend badge for a 'down' trend", () => {
    const stat: SummaryStatistic = {
      id: "gini",
      label: "Gini coefficient",
      value: "0.289",
      trend: "down",
      trendValue: "-0.012",
    };

    render(<SummaryStatCard stat={stat} />);

    expect(screen.getByText("Gini coefficient")).toBeInTheDocument();
    expect(screen.getByText("0.289")).toBeInTheDocument();
    const badge = screen.getByText("-0.012");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-emerald-50");
  });

  it("renders 'up' trend with warning variant", () => {
    const stat: SummaryStatistic = {
      id: "fiscal-cost",
      label: "Net fiscal cost",
      value: "€2.1B",
      trend: "up",
      trendValue: "+€0.3B",
    };

    render(<SummaryStatCard stat={stat} />);

    expect(screen.getByText("Net fiscal cost")).toBeInTheDocument();
    expect(screen.getByText("€2.1B")).toBeInTheDocument();
    const badge = screen.getByText("+€0.3B");
    expect(badge.className).toContain("bg-amber-50");
  });

  it("renders neutral trend with default variant", () => {
    const stat: SummaryStatistic = {
      id: "affected-pop",
      label: "Affected population",
      value: "78.4%",
      trend: "neutral",
      trendValue: "0.0%",
    };

    render(<SummaryStatCard stat={stat} />);

    const badge = screen.getByText("0.0%");
    expect(badge.className).toContain("bg-slate-100");
  });
});
