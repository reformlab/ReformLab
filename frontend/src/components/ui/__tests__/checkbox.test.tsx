import { render, screen } from "@testing-library/react";

import { Checkbox } from "@/components/ui/checkbox";

describe("Checkbox", () => {
  it("renders as input[type='checkbox']", () => {
    render(<Checkbox data-testid="cb" />);
    const el = screen.getByTestId("cb");
    expect(el.tagName).toBe("INPUT");
    expect(el).toHaveAttribute("type", "checkbox");
  });

  it("has cursor-pointer class", () => {
    render(<Checkbox data-testid="cb" />);
    expect(screen.getByTestId("cb")).toHaveClass("cursor-pointer");
  });

  it("merges custom className", () => {
    render(<Checkbox data-testid="cb" className="h-3.5 w-3.5" />);
    const el = screen.getByTestId("cb");
    expect(el).toHaveClass("cursor-pointer");
    expect(el).toHaveClass("h-3.5");
    expect(el).toHaveClass("w-3.5");
  });

  it("applies opacity-50 when disabled", () => {
    render(<Checkbox data-testid="cb" disabled />);
    expect(screen.getByTestId("cb")).toHaveClass("disabled:opacity-50");
  });
});
