import { render, screen, fireEvent } from "@testing-library/react";

import { MergeMethodSelector } from "@/components/simulation/MergeMethodSelector";
import { mockMergeMethods } from "@/data/mock-data";

describe("MergeMethodSelector", () => {
  const noop = () => {};

  it("renders all three merge methods (AC-3)", () => {
    render(
      <MergeMethodSelector
        methods={mockMergeMethods}
        selectedMethodId="uniform"
        onSelectMethod={noop}
      />,
    );

    expect(screen.getByText("Uniform Distribution")).toBeInTheDocument();
    expect(screen.getByText("Iterative Proportional Fitting (IPF)")).toBeInTheDocument();
    expect(screen.getByText("Conditional Sampling")).toBeInTheDocument();
  });

  it("shows plain-language description for selected method (AC-3)", () => {
    render(
      <MergeMethodSelector
        methods={mockMergeMethods}
        selectedMethodId="uniform"
        onSelectMethod={noop}
      />,
    );

    // Selected method shows assumption, when_appropriate, tradeoff
    expect(screen.getByText(/Assumption/)).toBeInTheDocument();
    expect(screen.getByText(/When appropriate/)).toBeInTheDocument();
    expect(screen.getByText(/Trade-off/)).toBeInTheDocument();
  });

  it("calls onSelectMethod with the method id when clicked (AC-3)", () => {
    const onSelect = vi.fn();
    render(
      <MergeMethodSelector
        methods={mockMergeMethods}
        selectedMethodId="uniform"
        onSelectMethod={onSelect}
      />,
    );

    const ipfButton = screen.getByRole("button", { name: /conditional sampling/i });
    fireEvent.click(ipfButton);
    expect(onSelect).toHaveBeenCalledWith("conditional");
  });

  it("marks the selected method button as pressed (AC-3)", () => {
    render(
      <MergeMethodSelector
        methods={mockMergeMethods}
        selectedMethodId="ipf"
        onSelectMethod={noop}
      />,
    );

    const ipfButton = screen.getByRole("button", {
      name: /iterative proportional fitting/i,
    });
    expect(ipfButton).toHaveAttribute("aria-pressed", "true");
  });
});
