// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";

import { ErrorAlert } from "@/components/simulation/ErrorAlert";

describe("ErrorAlert", () => {
  it("renders what, why, and fix text", () => {
    render(<ErrorAlert what="Bad input" why="Value out of range" fix="Enter a valid value" />);
    expect(screen.getByText("Bad input")).toBeInTheDocument();
    expect(screen.getByText("Value out of range")).toBeInTheDocument();
    expect(screen.getByText("Enter a valid value")).toBeInTheDocument();
  });

  it("has role='alert'", () => {
    render(<ErrorAlert what="Error" why="Because" fix="Fix it" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders an AlertCircle icon (svg)", () => {
    const { container } = render(<ErrorAlert what="Error" why="Because" fix="Fix it" />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("applies additional className when provided", () => {
    const { container } = render(
      <ErrorAlert what="Error" why="Because" fix="Fix it" className="mb-5" />,
    );
    expect(container.firstChild).toHaveClass("mb-5");
  });
});
