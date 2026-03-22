import { fireEvent, render, screen } from "@testing-library/react";

import { WorkbenchStepper, type StepDef } from "@/components/simulation/WorkbenchStepper";

const steps: StepDef[] = [
  { key: "sources", label: "1. Sources" },
  { key: "overlap", label: "2. Variables" },
  { key: "method", label: "3. Method" },
];

describe("WorkbenchStepper", () => {
  it("renders all steps", () => {
    render(
      <WorkbenchStepper steps={steps} activeStep="sources" onStepSelect={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: "1. Sources" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2. Variables" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "3. Method" })).toBeInTheDocument();
  });

  it("highlights the active step", () => {
    render(
      <WorkbenchStepper steps={steps} activeStep="overlap" onStepSelect={vi.fn()} />,
    );
    const activeBtn = screen.getByRole("button", { name: "2. Variables" });
    expect(activeBtn.className).toContain("border-blue-500");
    const inactiveBtn = screen.getByRole("button", { name: "1. Sources" });
    expect(inactiveBtn.className).not.toContain("border-blue-500");
  });

  it("calls onStepSelect with the key when a step is clicked", () => {
    const onStepSelect = vi.fn();
    render(
      <WorkbenchStepper steps={steps} activeStep="sources" onStepSelect={onStepSelect} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "3. Method" }));
    expect(onStepSelect).toHaveBeenCalledWith("method");
  });

  it("uses ariaLabel on the nav element", () => {
    render(
      <WorkbenchStepper
        steps={steps}
        activeStep="sources"
        onStepSelect={vi.fn()}
        ariaLabel="Workbench steps"
      />,
    );
    expect(screen.getByRole("navigation", { name: "Workbench steps" })).toBeInTheDocument();
  });

  it("uses default ariaLabel when not provided", () => {
    render(
      <WorkbenchStepper steps={steps} activeStep="sources" onStepSelect={vi.fn()} />,
    );
    expect(screen.getByRole("navigation", { name: "Steps" })).toBeInTheDocument();
  });
});
