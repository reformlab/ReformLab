/** Tests for ResultsListPanel — Story 17.3, AC-3. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ResultsListPanel } from "@/components/simulation/ResultsListPanel";
import type { ResultListItem } from "@/api/types";

const mockItem = (overrides: Partial<ResultListItem> = {}): ResultListItem => ({
  run_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  timestamp: "2026-03-07T22:15:30Z",
  run_kind: "scenario",
  start_year: 2025,
  end_year: 2030,
  row_count: 600000,
  status: "completed",
  data_available: true,
  template_name: "Carbon Tax — With Dividend",
  policy_type: "carbon_tax",
  portfolio_name: null,
  ...overrides,
});

describe("ResultsListPanel", () => {
  describe("empty state", () => {
    it("shows empty state message when no results", () => {
      render(
        <ResultsListPanel
          results={[]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText(/No simulation runs yet/i)).toBeInTheDocument();
    });
  });

  describe("with results", () => {
    it("renders a result entry with truncated run ID", () => {
      render(
        <ResultsListPanel
          results={[mockItem()]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      // First 8 chars of run_id
      expect(screen.getByText("a1b2c3d4")).toBeInTheDocument();
    });

    it("renders policy label from template_name", () => {
      render(
        <ResultsListPanel
          results={[mockItem({ template_name: "Carbon Tax — With Dividend" })]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("Carbon Tax — With Dividend")).toBeInTheDocument();
    });

    it("renders portfolio_name when run_kind is portfolio", () => {
      render(
        <ResultsListPanel
          results={[mockItem({ run_kind: "portfolio", template_name: null, portfolio_name: "green-transition-2030" })]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("green-transition-2030")).toBeInTheDocument();
    });

    it("shows status badge for completed run", () => {
      render(
        <ResultsListPanel
          results={[mockItem({ status: "completed" })]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("completed")).toBeInTheDocument();
    });

    it("shows status badge for failed run", () => {
      render(
        <ResultsListPanel
          results={[mockItem({ status: "failed", row_count: 0 })]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("failed")).toBeInTheDocument();
    });

    it("calls onSelect when clicking a result entry", async () => {
      const onSelect = vi.fn();
      render(
        <ResultsListPanel
          results={[mockItem()]}
          selectedRunId={null}
          onSelect={onSelect}
          onDelete={vi.fn()}
        />,
      );
      await userEvent.click(screen.getByRole("button", { name: /Select run a1b2c3d4/i }));
      expect(onSelect).toHaveBeenCalledWith("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
    });

    it("calls onDelete when delete button is clicked", async () => {
      const onDelete = vi.fn();
      render(
        <ResultsListPanel
          results={[mockItem()]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={onDelete}
        />,
      );
      await userEvent.click(screen.getByRole("button", { name: /Delete run a1b2c3d4/i }));
      expect(onDelete).toHaveBeenCalledWith("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
    });

    it("renders multiple results", () => {
      const items = [
        mockItem({ run_id: "run-001-0000-0000-0000-000000000000", template_name: "Policy A" }),
        mockItem({ run_id: "run-002-0000-0000-0000-000000000000", template_name: "Policy B" }),
      ];
      render(
        <ResultsListPanel
          results={items}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("Policy A")).toBeInTheDocument();
      expect(screen.getByText("Policy B")).toBeInTheDocument();
    });

    it("shows evicted label for completed run without data_available", () => {
      render(
        <ResultsListPanel
          results={[mockItem({ data_available: false })]}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("(evicted)")).toBeInTheDocument();
    });

    it("shows Past Runs count in header", () => {
      const items = [
        mockItem({ run_id: "run-001-0000-0000-0000-000000000000" }),
        mockItem({ run_id: "run-002-0000-0000-0000-000000000000" }),
      ];
      render(
        <ResultsListPanel
          results={items}
          selectedRunId={null}
          onSelect={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      expect(screen.getByText("Past Runs (2)")).toBeInTheDocument();
    });
  });
});
