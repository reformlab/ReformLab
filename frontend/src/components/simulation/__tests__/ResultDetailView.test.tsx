/** Tests for ResultDetailView — Story 17.3, AC-4. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ResultDetailView } from "@/components/simulation/ResultDetailView";
import type { ResultDetailResponse } from "@/api/types";

const mockDetail = (overrides: Partial<ResultDetailResponse> = {}): ResultDetailResponse => ({
  run_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  timestamp: "2026-03-07T22:15:30Z",
  run_kind: "scenario",
  start_year: 2025,
  end_year: 2030,
  population_id: "fr-synthetic-2024",
  seed: 42,
  row_count: 600000,
  status: "completed",
  data_available: true,
  template_name: "Carbon Tax — With Dividend",
  policy_type: "carbon_tax",
  portfolio_name: null,
  manifest_id: "manifest-001",
  scenario_id: "scenario-001",
  adapter_version: "1.0.0",
  started_at: "2026-03-07T22:15:00Z",
  finished_at: "2026-03-07T22:15:30Z",
  indicators: { row_count: 600000, columns: ["income", "tax"] },
  columns: ["income", "tax", "dividend"],
  column_count: 3,
  ...overrides,
});

describe("ResultDetailView", () => {
  describe("header", () => {
    it("shows policy/template label in header", () => {
      render(<ResultDetailView detail={mockDetail()} />);
      expect(screen.getByText("Carbon Tax — With Dividend")).toBeInTheDocument();
    });

    it("shows truncated run ID in header", () => {
      render(<ResultDetailView detail={mockDetail()} />);
      expect(screen.getByText("a1b2c3d4")).toBeInTheDocument();
    });

    it("shows status badge", () => {
      render(<ResultDetailView detail={mockDetail({ status: "completed" })} />);
      expect(screen.getByText("completed")).toBeInTheDocument();
    });

    it("shows 'metadata only' badge when data not available", () => {
      render(<ResultDetailView detail={mockDetail({ data_available: false })} />);
      expect(screen.getByText("metadata only")).toBeInTheDocument();
    });

    it("shows year range badge", () => {
      render(<ResultDetailView detail={mockDetail({ start_year: 2025, end_year: 2030 })} />);
      expect(screen.getByText("2025–2030")).toBeInTheDocument();
    });
  });

  describe("Indicators tab", () => {
    it("renders indicators tab by default", () => {
      render(<ResultDetailView detail={mockDetail()} />);
      expect(screen.getByRole("tab", { name: /Indicators/i })).toBeInTheDocument();
    });

    it("shows 'full data not available' when data_available is false", () => {
      render(<ResultDetailView detail={mockDetail({ data_available: false })} />);
      expect(screen.getByText(/Full data not available/i)).toBeInTheDocument();
    });
  });

  describe("Data Summary tab", () => {
    it("switches to data summary tab", async () => {
      render(<ResultDetailView detail={mockDetail()} />);
      await userEvent.click(screen.getByRole("tab", { name: /Data Summary/i }));
      expect(screen.getByText("600,000")).toBeInTheDocument();
    });

    it("export buttons are disabled when data not available", async () => {
      render(<ResultDetailView detail={mockDetail({ data_available: false })} />);
      await userEvent.click(screen.getByRole("tab", { name: /Data Summary/i }));
      const csvBtn = screen.getByRole("button", { name: /Export as CSV/i });
      const parquetBtn = screen.getByRole("button", { name: /Export as Parquet/i });
      expect(csvBtn).toBeDisabled();
      expect(parquetBtn).toBeDisabled();
    });

    it("export buttons are enabled when data_available is true", async () => {
      render(<ResultDetailView detail={mockDetail({ data_available: true })} />);
      await userEvent.click(screen.getByRole("tab", { name: /Data Summary/i }));
      const csvBtn = screen.getByRole("button", { name: /Export as CSV/i });
      const parquetBtn = screen.getByRole("button", { name: /Export as Parquet/i });
      expect(csvBtn).not.toBeDisabled();
      expect(parquetBtn).not.toBeDisabled();
    });
  });

  describe("Manifest tab", () => {
    it("switches to manifest tab and shows manifest ID", async () => {
      render(<ResultDetailView detail={mockDetail()} />);
      await userEvent.click(screen.getByRole("tab", { name: /Manifest/i }));
      expect(screen.getByText("manifest-001")).toBeInTheDocument();
    });

    it("shows scenario ID in manifest", async () => {
      render(<ResultDetailView detail={mockDetail()} />);
      await userEvent.click(screen.getByRole("tab", { name: /Manifest/i }));
      expect(screen.getByText("scenario-001")).toBeInTheDocument();
    });

    it("shows adapter version in manifest", async () => {
      render(<ResultDetailView detail={mockDetail()} />);
      await userEvent.click(screen.getByRole("tab", { name: /Manifest/i }));
      expect(screen.getByText("1.0.0")).toBeInTheDocument();
    });

    it("shows seed in manifest", async () => {
      render(<ResultDetailView detail={mockDetail({ seed: 42 })} />);
      await userEvent.click(screen.getByRole("tab", { name: /Manifest/i }));
      expect(screen.getByText("42")).toBeInTheDocument();
    });

    it("shows 'random' when seed is null", async () => {
      render(<ResultDetailView detail={mockDetail({ seed: null })} />);
      await userEvent.click(screen.getByRole("tab", { name: /Manifest/i }));
      expect(screen.getByText("random")).toBeInTheDocument();
    });
  });

  describe("portfolio runs", () => {
    it("shows portfolio name when run_kind is portfolio", () => {
      render(
        <ResultDetailView
          detail={mockDetail({
            run_kind: "portfolio",
            portfolio_name: "green-transition-2030",
            template_name: null,
          })}
        />,
      );
      expect(screen.getByText("green-transition-2030")).toBeInTheDocument();
    });
  });
});
