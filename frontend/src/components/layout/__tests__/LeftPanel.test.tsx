// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { LeftPanel } from "@/components/layout/LeftPanel";

describe("LeftPanel", () => {
  it("renders children when expanded", () => {
    render(
      <LeftPanel collapsed={false} onToggle={vi.fn()}>
        <p>Scenario list</p>
      </LeftPanel>,
    );

    expect(screen.getByText("ReformLab")).toBeInTheDocument();
    expect(screen.getByText("Scenario list")).toBeInTheDocument();
  });

  it("shows expand button and rotated label when collapsed", () => {
    render(
      <LeftPanel collapsed={true} onToggle={vi.fn()}>
        <p>Hidden content</p>
      </LeftPanel>,
    );

    expect(screen.getByRole("button", { name: /Expand left panel/i })).toBeInTheDocument();
    expect(screen.getByText("RL")).toBeInTheDocument();
    expect(screen.queryByText("Hidden content")).not.toBeInTheDocument();
  });

  it("calls onToggle when collapse button is clicked", async () => {
    const onToggle = vi.fn();
    render(
      <LeftPanel collapsed={false} onToggle={onToggle}>
        <p>Content</p>
      </LeftPanel>,
    );

    await userEvent.click(screen.getByRole("button", { name: /Collapse left panel/i }));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("calls onToggle when expand button is clicked", async () => {
    const onToggle = vi.fn();
    render(
      <LeftPanel collapsed={true} onToggle={onToggle}>
        <p>Content</p>
      </LeftPanel>,
    );

    await userEvent.click(screen.getByRole("button", { name: /Expand left panel/i }));
    expect(onToggle).toHaveBeenCalledOnce();
  });
});
