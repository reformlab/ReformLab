import { render, screen } from "@testing-library/react";

import { PopulationPreview } from "@/components/simulation/PopulationPreview";
import type { GenerationResult } from "@/api/types";

const mockResult: GenerationResult = {
  success: true,
  summary: {
    record_count: 5000,
    column_count: 4,
    columns: ["commune_code", "median_income", "fuel_type", "fleet_count_2022"],
  },
  step_log: [
    {
      step_index: 0,
      step_type: "load",
      label: "source_0",
      input_labels: [],
      output_rows: 5000,
      output_columns: ["commune_code", "median_income"],
      method_name: null,
      duration_ms: 12.5,
    },
  ],
  assumption_chain: [
    {
      step_index: 0,
      step_label: "merged_0",
      method: "UniformMergeMethod",
      description: "Uniform random matching with replacement",
    },
  ],
  validation_result: null,
};

describe("PopulationPreview", () => {
  it("displays record count in summary (AC-5)", () => {
    render(<PopulationPreview result={mockResult} />);
    expect(screen.getByText("5,000")).toBeInTheDocument();
  });

  it("displays column count in summary (AC-5)", () => {
    render(<PopulationPreview result={mockResult} />);
    expect(screen.getAllByText("4")[0]).toBeInTheDocument();
  });

  it("shows column list as badges (AC-5)", () => {
    render(<PopulationPreview result={mockResult} />);
    expect(screen.getByText("commune_code")).toBeInTheDocument();
    expect(screen.getByText("median_income")).toBeInTheDocument();
  });

  it("has tabs for Summary, Distributions, Assumptions (AC-5)", () => {
    render(<PopulationPreview result={mockResult} />);
    expect(screen.getByRole("tab", { name: /summary/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /distributions/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /assumptions/i })).toBeInTheDocument();
  });
});
