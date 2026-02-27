import { fireEvent, render, screen } from "@testing-library/react";

import {
  ModelConfigStepper,
  type ConfigStep,
} from "@/components/simulation/ModelConfigStepper";

describe("ModelConfigStepper", () => {
  it("allows non-blocking navigation between all steps", () => {
    const onStepSelect = vi.fn<(step: ConfigStep["key"]) => void>();
    const steps: ConfigStep[] = [
      { key: "population", label: "Population", status: "complete" },
      { key: "template", label: "Policy", status: "complete" },
      { key: "parameters", label: "Parameters", status: "incomplete" },
      { key: "assumptions", label: "Validation", status: "incomplete" },
    ];

    render(
      <ModelConfigStepper
        activeStep="parameters"
        steps={steps}
        onStepSelect={onStepSelect}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /population/i }));
    fireEvent.click(screen.getByRole("button", { name: /validation/i }));

    expect(onStepSelect).toHaveBeenNthCalledWith(1, "population");
    expect(onStepSelect).toHaveBeenNthCalledWith(2, "assumptions");
  });
});
