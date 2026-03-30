// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Tests for PopulationLibraryScreen component.
 *
 * Story 20.4 — AC-1, AC-5, AC-6: Population library with grid of population cards.
 * Story 22.4 — AC-6, AC-8: Quick Test Population special treatment.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PopulationLibraryScreen, type PopulationLibraryScreenProps } from "@/components/screens/PopulationLibraryScreen";
import { QUICK_TEST_POPULATION_ID } from "@/data/quick-test-population";

// ============================================================================
// Helpers
// ============================================================================

function baseProps(overrides: Partial<PopulationLibraryScreenProps> = {}): PopulationLibraryScreenProps {
  return {
    populations: [
      {
        id: "fr-synthetic-2024",
        name: "France Synthetic 2024",
        households: 100_000,
        source: "INSEE marginals",
        year: 2024,
        origin: "built-in",
        canonical_origin: "synthetic-public",
        access_mode: "bundled",
        trust_status: "production-safe",
        is_synthetic: true,
        column_count: 15,
        created_date: "2024-01-01T00:00:00Z",
      },
      {
        id: QUICK_TEST_POPULATION_ID,
        name: "Quick Test Population",
        households: 100,
        source: "Built-in demo data",
        year: 2026,
        origin: "built-in",
        canonical_origin: "synthetic-public",
        access_mode: "bundled",
        trust_status: "demo-only",
        is_synthetic: true,
        column_count: 8,
        created_date: "2026-01-01T00:00:00Z",
      },
    ],
    selectedPopulationId: "",
    loading: false,
    onPreview: vi.fn(),
    onExplore: vi.fn(),
    onSelect: vi.fn(),
    onDelete: vi.fn(),
    onUpload: vi.fn(),
    onBuildNew: vi.fn(),
    ...overrides,
  };
}

// ============================================================================
// Story 20.4: Basic rendering
// ============================================================================

describe("PopulationLibraryScreen - basic rendering", () => {
  it("renders the population library header", () => {
    render(<PopulationLibraryScreen {...baseProps()} />);
    expect(screen.getByText("Population Library")).toBeInTheDocument();
  });

  it("renders population cards in a grid", () => {
    render(<PopulationLibraryScreen {...baseProps()} />);
    expect(screen.getByText("France Synthetic 2024")).toBeInTheDocument();
    expect(screen.getByText("Quick Test Population")).toBeInTheDocument();
  });

  it("shows loading state when loading is true", () => {
    render(<PopulationLibraryScreen {...baseProps({ loading: true })} />);
    expect(screen.getByText("Loading populations…")).toBeInTheDocument();
  });

  it("shows empty state when no populations exist", () => {
    render(<PopulationLibraryScreen {...baseProps({ populations: [] })} />);
    expect(screen.getByText("No populations available.")).toBeInTheDocument();
  });
});

// ============================================================================
// Story 22.4: Quick Test Population special treatment
// ============================================================================

describe("PopulationLibraryScreen - Quick Test Population (Story 22.4)", () => {
  it("renders Quick Test Population with demo-only trust status badge", () => {
    render(<PopulationLibraryScreen {...baseProps()} />);
    const demoOnlyBadges = screen.getAllByText("Demo Only");
    expect(demoOnlyBadges.length).toBeGreaterThan(0);
  });

  it("renders Quick Test Population with Fast demo / smoke test indicator", () => {
    render(<PopulationLibraryScreen {...baseProps()} />);
    expect(screen.getByText("Fast demo / smoke test")).toBeInTheDocument();
  });

  it("Quick Test Population has distinct visual treatment (amber border/background)", () => {
    const { container } = render(<PopulationLibraryScreen {...baseProps()} />);
    // The Quick Test Population card should have border-amber-200 class
    const quickTestCard = container.querySelector('[class*="border-amber-200"]');
    expect(quickTestCard).toBeInTheDocument();
  });

  it("Quick Test Population appears first in the grid regardless of order in array", () => {
    // Create populations array with Quick Test Population second
    const populations = [
      {
        id: "fr-synthetic-2024",
        name: "France Synthetic 2024",
        households: 100_000,
        source: "INSEE marginals",
        year: 2024,
        origin: "built-in" as const,
        canonical_origin: "synthetic-public" as const,
        access_mode: "bundled" as const,
        trust_status: "production-safe" as const,
        is_synthetic: true,
        column_count: 15,
        created_date: "2024-01-01T00:00:00Z",
      },
      {
        id: QUICK_TEST_POPULATION_ID,
        name: "Quick Test Population",
        households: 100,
        source: "Built-in demo data",
        year: 2026,
        origin: "built-in" as const,
        canonical_origin: "synthetic-public" as const,
        access_mode: "bundled" as const,
        trust_status: "demo-only" as const,
        is_synthetic: true,
        column_count: 8,
        created_date: "2026-01-01T00:00:00Z",
      },
    ];

    const { container } = render(<PopulationLibraryScreen {...baseProps({ populations })} />);

    // Get all population cards by finding elements with "rows" text (each card shows row count)
    const allCards = screen.getAllByText(/rows/);

    // The first card should be Quick Test Population (100 rows)
    expect(allCards[0]).toHaveTextContent("100 rows");
    // The second card should be France Synthetic (100,000 rows)
    expect(allCards[1]).toHaveTextContent("100,000 rows");
  });

  it("Quick Test Population is selectable and works with scenario flow", async () => {
    const onSelect = vi.fn();
    render(<PopulationLibraryScreen {...baseProps({ onSelect })} />);

    // Find the Quick Test Population card and click Select
    // Quick Test Population is first in the sorted list, so it appears first in the grid
    const selectButtons = screen.getAllByText("Select");
    // First Select button belongs to Quick Test Population (sorted first)
    await userEvent.click(selectButtons[0]);
    expect(onSelect).toHaveBeenCalledWith(QUICK_TEST_POPULATION_ID);
  });

  it("Quick Test Population has small household count (100-500 households)", () => {
    render(<PopulationLibraryScreen {...baseProps()} />);
    // Quick Test Population should show "100 rows"
    expect(screen.getByText((text) => text.includes("100 rows"))).toBeInTheDocument();
  });

  it("Quick Test Population displays tooltip explaining purpose", () => {
    render(<PopulationLibraryScreen {...baseProps()} />);
    // The Fast demo / smoke test indicator should have a title attribute
    const indicator = screen.getByText("Fast demo / smoke test");
    expect(indicator.closest("div")).toHaveAttribute(
      "title",
      "For fast demos and smoke testing only — not for substantive analysis",
    );
  });
});

// ============================================================================
// Story 20.4: Population card interactions
// ============================================================================

describe("PopulationLibraryScreen - population card interactions", () => {
  it("calls onPreview when Preview button is clicked", async () => {
    const onPreview = vi.fn();
    render(<PopulationLibraryScreen {...baseProps({ onPreview })} />);

    const previewButtons = screen.getAllByText("Preview");
    await userEvent.click(previewButtons[0]);
    expect(onPreview).toHaveBeenCalled();
  });

  it("calls onExplore when Explore button is clicked", async () => {
    const onExplore = vi.fn();
    render(<PopulationLibraryScreen {...baseProps({ onExplore })} />);

    const exploreButtons = screen.getAllByText("Explore");
    await userEvent.click(exploreButtons[0]);
    expect(onExplore).toHaveBeenCalled();
  });

  it("calls onSelect when Select button is clicked", async () => {
    const onSelect = vi.fn();
    render(<PopulationLibraryScreen {...baseProps({ onSelect })} />);

    const selectButtons = screen.getAllByText("Select");
    await userEvent.click(selectButtons[0]);
    expect(onSelect).toHaveBeenCalled();
  });

  it("shows Selected state when population is selected", () => {
    render(<PopulationLibraryScreen {...baseProps({ selectedPopulationId: "fr-synthetic-2024" })} />);
    // Should have a "Selected" button for the selected population
    const selectedButtons = screen.getAllByText("Selected");
    expect(selectedButtons.length).toBe(1);
  });
});

// ============================================================================
// Toolbar actions
// ============================================================================

describe("PopulationLibraryScreen - toolbar actions", () => {
  it("calls onUpload when Upload button is clicked", async () => {
    const onUpload = vi.fn();
    render(<PopulationLibraryScreen {...baseProps({ onUpload })} />);

    await userEvent.click(screen.getByText("Upload"));
    expect(onUpload).toHaveBeenCalled();
  });

  it("calls onBuildNew when Build New button is clicked", async () => {
    const onBuildNew = vi.fn();
    render(<PopulationLibraryScreen {...baseProps({ onBuildNew })} />);

    await userEvent.click(screen.getByText("Build New"));
    expect(onBuildNew).toHaveBeenCalled();
  });

  it("shows selected population name in toolbar when population is selected", () => {
    render(<PopulationLibraryScreen {...baseProps({ selectedPopulationId: "fr-synthetic-2024" })} />);
    // The text is split across multiple spans in the toolbar
    const selectedText = screen.getByText("Selected:");
    const toolbar = selectedText.closest("div");
    if (!toolbar) throw new Error("Toolbar not found");
    // Check that France Synthetic 2024 appears in the same toolbar container
    expect(toolbar).toHaveTextContent("Selected: France Synthetic 2024");
  });
});
