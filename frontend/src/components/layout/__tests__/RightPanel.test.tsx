// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";

import { RightPanel } from "@/components/layout/RightPanel";

describe("RightPanel", () => {
  it("renders children when expanded", () => {
    render(
      <RightPanel collapsed={false} onToggle={() => {}}>
        <p>Help content here</p>
      </RightPanel>,
    );

    expect(screen.getByText("Help content here")).toBeInTheDocument();
  });

  it("hides children when collapsed", () => {
    render(
      <RightPanel collapsed={true} onToggle={() => {}}>
        <p>Help content here</p>
      </RightPanel>,
    );

    expect(screen.queryByText("Help content here")).not.toBeInTheDocument();
  });

  it("calls onToggle when the expand button is clicked in collapsed state", async () => {
    const onToggle = vi.fn();
    render(
      <RightPanel collapsed={true} onToggle={onToggle}>
        <div />
      </RightPanel>,
    );

    await userEvent.click(screen.getByRole("button", { name: /expand/i }));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("calls onToggle when the collapse button is clicked in expanded state", async () => {
    const onToggle = vi.fn();
    render(
      <RightPanel collapsed={false} onToggle={onToggle}>
        <div />
      </RightPanel>,
    );

    await userEvent.click(screen.getByRole("button", { name: /collapse/i }));
    expect(onToggle).toHaveBeenCalledOnce();
  });
});
