// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";

import { Skeleton } from "@/components/ui/skeleton";

describe("Skeleton", () => {
  it("renders with animate-pulse class", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel")).toHaveClass("animate-pulse");
  });

  it("renders with bg-slate-200 class", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel")).toHaveClass("bg-slate-200");
  });

  it("merges custom className", () => {
    render(<Skeleton data-testid="skel" className="h-4 w-full" />);
    const el = screen.getByTestId("skel");
    expect(el).toHaveClass("animate-pulse");
    expect(el).toHaveClass("h-4");
    expect(el).toHaveClass("w-full");
  });

  it("renders as a div element", () => {
    render(<Skeleton data-testid="skel" />);
    expect(screen.getByTestId("skel").tagName).toBe("DIV");
  });
});
