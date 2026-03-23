// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";

import { PortfolioDesignerScreen } from "@/components/screens/PortfolioDesignerScreen";
import { mockTemplates } from "@/data/mock-data";

// Mock the portfolio API so tests don't hit the network
vi.mock("@/api/portfolios", () => ({
  validatePortfolio: vi.fn().mockResolvedValue({ conflicts: [], is_compatible: true }),
  createPortfolio: vi.fn().mockResolvedValue("v-abc123"),
  deletePortfolio: vi.fn().mockResolvedValue(undefined),
  getPortfolio: vi.fn().mockResolvedValue({
    name: "green-deal-2030",
    description: "Green deal",
    version_id: "v1",
    policies: [
      { name: "Carbon Tax", policy_type: "carbon_tax", rate_schedule: { "2025": 44 }, parameters: {} },
      { name: "Vehicle Bonus", policy_type: "vehicle_bonus_malus", rate_schedule: {}, parameters: {} },
    ],
    resolution_strategy: "sum",
    policy_count: 2,
  }),
  clonePortfolio: vi.fn().mockResolvedValue({
    name: "green-deal-copy",
    description: "Green deal",
    version_id: "v2",
    policies: [],
    resolution_strategy: "sum",
    policy_count: 2,
  }),
}));

function renderScreen(props: Partial<React.ComponentProps<typeof PortfolioDesignerScreen>> = {}) {
  return render(
    <PortfolioDesignerScreen
      templates={mockTemplates}
      savedPortfolios={[]}
      onSaved={() => {}}
      {...props}
    />,
  );
}

describe("PortfolioDesignerScreen", () => {
  it("renders step navigation (AC-1)", () => {
    renderScreen();
    expect(screen.getByRole("navigation", { name: /designer steps/i })).toBeInTheDocument();
    expect(screen.getByText(/1\. Select Templates/i)).toBeInTheDocument();
    expect(screen.getByText(/2\. Compose & Configure/i)).toBeInTheDocument();
    expect(screen.getByText(/3\. Review & Save/i)).toBeInTheDocument();
  });

  it("starts on Select Templates step (AC-1)", () => {
    renderScreen();
    expect(screen.getByText(/Select Policy Templates/i)).toBeInTheDocument();
    expect(screen.getByText(/0 selected/i)).toBeInTheDocument();
  });

  it("Next button disabled when fewer than 2 templates selected (AC-2)", () => {
    renderScreen();
    const nextBtn = screen.getByRole("button", { name: /next/i });
    expect(nextBtn).toBeDisabled();
  });

  it("Next button enabled when 2 templates selected (AC-2)", () => {
    renderScreen();
    // Select two template toggle buttons
    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);

    const nextBtn = screen.getByRole("button", { name: /next/i });
    expect(nextBtn).not.toBeDisabled();
  });

  it("advances to Compose step after Next click with 2+ templates (AC-2)", () => {
    renderScreen();
    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);

    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    // Resolution strategy selector is only visible on compose step
    expect(screen.getByLabelText(/resolution strategy/i)).toBeInTheDocument();
  });

  it("navigates back from compose to select step (AC-2)", () => {
    renderScreen();
    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.getByText(/Select Policy Templates/i)).toBeInTheDocument();
  });

  it("can click step tabs to navigate (AC-1)", () => {
    renderScreen();
    fireEvent.click(screen.getByText(/2\. Compose & Configure/i));
    // Should navigate to compose step
    expect(screen.getByLabelText(/resolution strategy/i)).toBeInTheDocument();
  });

  it("shows resolution strategy selector on compose step (AC-6)", () => {
    renderScreen();
    fireEvent.click(screen.getByText(/2\. Compose & Configure/i));

    const select = screen.getByLabelText(/resolution strategy/i);
    expect(select).toBeInTheDocument();
    // Default is 'error'
    expect((select as HTMLSelectElement).value).toBe("error");
  });

  it("shows Save Portfolio button on review step (AC-5)", () => {
    renderScreen();
    fireEvent.click(screen.getByText(/3\. Review & Save/i));
    expect(screen.getByRole("button", { name: /save portfolio/i })).toBeInTheDocument();
  });

  it("Save Portfolio button disabled with < 2 policies (AC-5)", () => {
    renderScreen();
    fireEvent.click(screen.getByText(/3\. Review & Save/i));
    expect(screen.getByRole("button", { name: /save portfolio/i })).toBeDisabled();
  });

  it("shows save dialog on Save Portfolio click (AC-5)", async () => {
    renderScreen();
    // Add 2 templates and navigate to review via step tab
    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    fireEvent.click(screen.getByText("3. Review & Save"));
    fireEvent.click(screen.getByRole("button", { name: /save portfolio/i }));

    expect(screen.getByRole("dialog", { name: /save portfolio/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/portfolio name/i)).toBeInTheDocument();
  });

  it("shows name validation error for invalid portfolio name (AC-5)", async () => {
    renderScreen();
    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    fireEvent.click(screen.getByText("3. Review & Save"));
    fireEvent.click(screen.getByRole("button", { name: /save portfolio/i }));

    const nameInput = screen.getByLabelText(/portfolio name/i);
    fireEvent.change(nameInput, { target: { value: "INVALID NAME!" } });
    expect(screen.getByText(/lowercase slug/i)).toBeInTheDocument();
  });

  it("shows Check Conflicts button on review step (AC-6)", () => {
    renderScreen();
    fireEvent.click(screen.getByText(/3\. Review & Save/i));
    expect(screen.getByRole("button", { name: /check conflicts/i })).toBeInTheDocument();
  });

  it("shows saved portfolios list when provided (AC-5)", () => {
    renderScreen({
      savedPortfolios: [
        { name: "green-deal-2030", description: "Green deal", version_id: "v1", policy_count: 3 },
      ],
    });
    fireEvent.click(screen.getByText(/3\. Review & Save/i));
    expect(screen.getByText("green-deal-2030")).toBeInTheDocument();
    expect(screen.getByText(/3 policies/i)).toBeInTheDocument();
  });

  it("shows Load and Clone buttons for saved portfolios (AC-5)", () => {
    renderScreen({
      savedPortfolios: [
        { name: "green-deal-2030", description: "Green deal", version_id: "v1", policy_count: 3 },
      ],
    });
    fireEvent.click(screen.getByText(/3\. Review & Save/i));
    expect(screen.getByRole("button", { name: /load portfolio green-deal-2030/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /clone portfolio green-deal-2030/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete portfolio green-deal-2030/i })).toBeInTheDocument();
  });

  it("opens clone dialog when Clone button clicked (AC-5)", () => {
    renderScreen({
      savedPortfolios: [
        { name: "green-deal-2030", description: "Green deal", version_id: "v1", policy_count: 3 },
      ],
    });
    fireEvent.click(screen.getByText(/3\. Review & Save/i));
    fireEvent.click(screen.getByRole("button", { name: /clone portfolio green-deal-2030/i }));

    expect(screen.getByRole("dialog", { name: /clone portfolio/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/new name/i)).toBeInTheDocument();
  });
});
