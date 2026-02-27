import { fireEvent, render, screen } from "@testing-library/react";

import App from "@/App";

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1600,
    });
  });

  it("renders and allows starting a simulation run", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /^Simulation$/i }));
    expect(screen.getByRole("heading", { name: /Run Trigger/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Run Simulation/i }));
    expect(screen.getByText(/Running Simulation/i)).toBeInTheDocument();
  });
});
