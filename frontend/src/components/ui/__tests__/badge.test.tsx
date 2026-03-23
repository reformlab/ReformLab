// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";

import { Badge } from "@/components/ui/badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>completed</Badge>);
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("applies default variant classes when no variant specified", () => {
    render(<Badge>default</Badge>);
    const badge = screen.getByText("default");
    expect(badge.className).toContain("bg-slate-100");
  });

  it("applies success variant classes", () => {
    render(<Badge variant="success">ok</Badge>);
    const badge = screen.getByText("ok");
    expect(badge.className).toContain("bg-emerald-50");
  });

  it("applies destructive variant classes", () => {
    render(<Badge variant="destructive">error</Badge>);
    const badge = screen.getByText("error");
    expect(badge.className).toContain("bg-red-50");
  });

  it("applies warning variant classes", () => {
    render(<Badge variant="warning">warn</Badge>);
    expect(screen.getByText("warn")).toHaveClass("bg-amber-50");
  });

  it("applies info variant classes", () => {
    render(<Badge variant="info">note</Badge>);
    expect(screen.getByText("note")).toHaveClass("bg-sky-50");
  });

  it("applies violet variant classes", () => {
    render(<Badge variant="violet">tag</Badge>);
    expect(screen.getByText("tag")).toHaveClass("bg-violet-50");
  });

  it("merges custom className", () => {
    render(<Badge className="my-custom">test</Badge>);
    const badge = screen.getByText("test");
    expect(badge.className).toContain("my-custom");
  });
});
