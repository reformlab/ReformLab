import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RunProgressBar } from "@/components/simulation/RunProgressBar";

describe("RunProgressBar", () => {
  it("renders current step, progress percentage, and ETA", () => {
    render(
      <RunProgressBar
        progress={45}
        currentStep="Computing year 2027..."
        eta="~12s"
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByText("Running Simulation")).toBeInTheDocument();
    expect(screen.getByText("45%")).toBeInTheDocument();
    expect(screen.getByText("Computing year 2027...")).toBeInTheDocument();
    expect(screen.getByText("ETA ~12s")).toBeInTheDocument();
  });

  it("renders progress bar at correct width", () => {
    const { container } = render(
      <RunProgressBar progress={75} currentStep="Step" eta="~5s" onCancel={vi.fn()} />,
    );

    const progressFill = container.querySelector("[style*='width: 75%']");
    expect(progressFill).toBeInTheDocument();
  });

  it("calls onCancel when cancel button is clicked", async () => {
    const onCancel = vi.fn();
    render(
      <RunProgressBar progress={50} currentStep="Step" eta="~10s" onCancel={onCancel} />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Cancel run/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("renders correctly at 0% progress", () => {
    const { container } = render(
      <RunProgressBar progress={0} currentStep="Initializing..." eta="~30s" onCancel={vi.fn()} />,
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(container.querySelector("[style*='width: 0%']")).toBeInTheDocument();
  });

  it("renders correctly at 100% progress", () => {
    const { container } = render(
      <RunProgressBar progress={100} currentStep="Done" eta="0s" onCancel={vi.fn()} />,
    );
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(container.querySelector("[style*='width: 100%']")).toBeInTheDocument();
  });
});
