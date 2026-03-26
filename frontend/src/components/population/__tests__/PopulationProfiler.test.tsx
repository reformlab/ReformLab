// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for PopulationProfiler — Story 20.4.
 *
 * Tests:
 * - Column list renders all columns from profile data
 * - Selecting a numeric column shows histogram container
 * - Selecting a categorical column shows value counts container
 * - Cross-tab selector triggers crosstab callback
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { setupResizeObserver } from "@/__tests__/workflows/helpers";

import { PopulationProfiler } from "@/components/population/PopulationProfiler";
import { mockPopulationProfile, mockCrosstabData } from "@/data/mock-population-explorer";

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  setupResizeObserver();
});

beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests
// ============================================================================

describe("PopulationProfiler — Story 20.4", () => {
  const defaultProps = {
    profile: mockPopulationProfile,
    crosstabData: null,
    onCrosstabRequest: vi.fn(),
  };

  it("renders the column list with all profile column names", () => {
    render(<PopulationProfiler {...defaultProps} />);
    // Column names appear in both sidebar and panel header — at least one match expected
    expect(screen.getAllByText("income").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("region").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("housing_type").length).toBeGreaterThanOrEqual(1);
  });

  it("first column (income) is selected by default and shows numeric profile", () => {
    render(<PopulationProfiler {...defaultProps} />);
    // The panel header should show the column name
    expect(screen.getByText("Distribution")).toBeInTheDocument();
    expect(screen.getByText("Percentiles")).toBeInTheDocument();
  });

  it("shows histogram aria-label for numeric column", () => {
    render(<PopulationProfiler {...defaultProps} />);
    expect(screen.getByLabelText(/histogram for income/i)).toBeInTheDocument();
  });

  it("shows stats labels for numeric profile (min, max, mean)", () => {
    render(<PopulationProfiler {...defaultProps} />);
    expect(screen.getByText("min")).toBeInTheDocument();
    expect(screen.getByText("max")).toBeInTheDocument();
    expect(screen.getByText("mean")).toBeInTheDocument();
  });

  it("clicking a categorical column shows value counts chart", async () => {
    const user = userEvent.setup();
    render(<PopulationProfiler {...defaultProps} />);
    // Click on the region column in the sidebar
    const regionBtn = screen.getByRole("button", { name: /region/i });
    await user.click(regionBtn);
    await waitFor(() => {
      expect(screen.getByLabelText(/value counts for region/i)).toBeInTheDocument();
    });
  });

  it("cross-tab selector triggers onCrosstabRequest when a column is selected", async () => {
    const onCrosstabRequest = vi.fn();
    const user = userEvent.setup();
    render(
      <PopulationProfiler
        {...defaultProps}
        onCrosstabRequest={onCrosstabRequest}
      />,
    );

    // The cross-tab selector is visible for numeric column (income is selected by default)
    const selector = screen.getByRole("combobox", { name: /cross-tab column selector/i });
    await user.selectOptions(selector, "region");
    expect(onCrosstabRequest).toHaveBeenCalledWith("income", "region");
  });

  it("shows crosstab chart when crosstabData is provided and matches selected col", async () => {
    render(
      <PopulationProfiler
        {...defaultProps}
        crosstabData={{ ...mockCrosstabData, col_a: "income", col_b: "region" }}
      />,
    );
    await waitFor(() => {
      expect(screen.getByLabelText(/cross-tab: income × region/i)).toBeInTheDocument();
    });
  });

  it("renders column type badges (num/cat) in sidebar", () => {
    render(<PopulationProfiler {...defaultProps} />);
    const numBadges = screen.getAllByText("num");
    const catBadges = screen.getAllByText("cat");
    expect(numBadges.length).toBeGreaterThan(0);
    expect(catBadges.length).toBeGreaterThan(0);
  });
});
