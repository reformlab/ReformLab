import { render, screen } from "@testing-library/react";

import { PopulationValidationPanel } from "@/components/simulation/PopulationValidationPanel";
import type { ValidationResultResponse } from "@/api/types";

const passingValidation: ValidationResultResponse = {
  all_passed: true,
  total_constraints: 2,
  failed_count: 0,
  marginal_results: [
    {
      dimension: "income_decile",
      passed: true,
      max_deviation: 0.01,
      tolerance: 0.05,
      observed: { D1: 0.1 },
      expected: { D1: 0.1 },
      deviations: { D1: 0.01 },
    },
    {
      dimension: "fuel_type",
      passed: true,
      max_deviation: 0.02,
      tolerance: 0.05,
      observed: { electric: 0.15 },
      expected: { electric: 0.15 },
      deviations: { electric: 0.02 },
    },
  ],
};

const failingValidation: ValidationResultResponse = {
  all_passed: false,
  total_constraints: 1,
  failed_count: 1,
  marginal_results: [
    {
      dimension: "income_decile",
      passed: false,
      max_deviation: 0.12,
      tolerance: 0.05,
      observed: { D1: 0.22 },
      expected: { D1: 0.1 },
      deviations: { D1: 0.12 },
    },
  ],
};

describe("PopulationValidationPanel", () => {
  it("shows 'All passed' when all constraints pass (AC-5)", () => {
    render(<PopulationValidationPanel validation={passingValidation} />);
    expect(screen.getByText("All passed")).toBeInTheDocument();
  });

  it("shows failed count when some constraints fail (AC-5)", () => {
    render(<PopulationValidationPanel validation={failingValidation} />);
    expect(screen.getByText("1 failed")).toBeInTheDocument();
  });

  it("renders per-marginal pass/fail badges (AC-5)", () => {
    render(<PopulationValidationPanel validation={passingValidation} />);
    expect(screen.getAllByText("Pass").length).toBe(2);
  });

  it("renders per-marginal dimension names (AC-5)", () => {
    render(<PopulationValidationPanel validation={passingValidation} />);
    expect(screen.getByText("income_decile")).toBeInTheDocument();
    expect(screen.getByText("fuel_type")).toBeInTheDocument();
  });

  it("shows deviation values for each marginal (AC-5)", () => {
    render(<PopulationValidationPanel validation={passingValidation} />);
    // Max deviation 0.01 → 1.00%
    expect(screen.getByText(/1\.00%/)).toBeInTheDocument();
  });

  it("shows empty state when no marginals configured", () => {
    render(
      <PopulationValidationPanel
        validation={{ all_passed: true, total_constraints: 0, failed_count: 0, marginal_results: [] }}
      />,
    );
    expect(screen.getByText(/no marginal constraints/i)).toBeInTheDocument();
  });
});
