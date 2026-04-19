// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * MobileStageSwitcher tests — Story 22.7, Task 3
 *
 * AC-2: Stage navigation reachable from every screen at phone width
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MobileStageSwitcher } from "@/components/layout/MobileStageSwitcher";

describe("MobileStageSwitcher — Story 22.7", () => {
  const mockNavigateTo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render all stage buttons", () => {
    render(
      <MobileStageSwitcher
        activeStage="policies"
        navigateTo={mockNavigateTo}
      />
    );

    // All 4 stages should be rendered
    expect(screen.getByRole("button", { name: /Policy/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Population/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Scenario/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run \/ Results \/ Compare/i })).toBeInTheDocument();
  });

  it("should highlight active stage", () => {
    render(
      <MobileStageSwitcher
        activeStage="population"
        navigateTo={mockNavigateTo}
      />
    );

    const activeButton = screen.getByRole("button", { name: /Population/i });
    expect(activeButton).toHaveClass("bg-blue-500");
    expect(activeButton).toHaveClass("text-white");
  });

  it("should navigate to stage on click", async () => {
    const user = userEvent.setup();
    render(
      <MobileStageSwitcher
        activeStage="policies"
        navigateTo={mockNavigateTo}
      />
    );

    const engineButton = screen.getByRole("button", { name: /Scenario/i });
    await user.click(engineButton);

    expect(mockNavigateTo).toHaveBeenCalledWith("engine");
  });

  it("should have horizontal scroll for many stages", () => {
    const { container } = render(
      <MobileStageSwitcher
        activeStage="policies"
        navigateTo={mockNavigateTo}
      />
    );

    const switcher = container.firstChild as HTMLElement;
    expect(switcher).toHaveClass("overflow-x-auto");
  });
});
