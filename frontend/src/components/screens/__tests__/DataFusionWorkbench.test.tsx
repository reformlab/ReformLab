import { render, screen, fireEvent } from "@testing-library/react";

import { DataFusionWorkbench } from "@/components/screens/DataFusionWorkbench";
import { mockDataSources, mockMergeMethods } from "@/data/mock-data";

function renderWorkbench() {
  return render(
    <DataFusionWorkbench
      sources={mockDataSources}
      methods={mockMergeMethods}
      initialResult={null}
      onPopulationGenerated={() => {}}
    />,
  );
}

describe("DataFusionWorkbench", () => {
  it("renders the workbench heading (AC-1)", () => {
    renderWorkbench();
    expect(screen.getByText("Data Fusion Workbench")).toBeInTheDocument();
  });

  it("shows the step navigation (AC-1, AC-3, AC-4, AC-5)", () => {
    renderWorkbench();
    expect(screen.getByRole("navigation", { name: /workbench steps/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /1\. sources/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /2\. variables/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /3\. method/i })).toBeInTheDocument();
  });

  it("starts on the sources step (AC-1)", () => {
    renderWorkbench();
    expect(screen.getByRole("region", { name: /data source browser/i })).toBeInTheDocument();
  });

  it("shows source selection count (AC-1)", () => {
    renderWorkbench();
    expect(screen.getByText(/0 selected/i)).toBeInTheDocument();
  });

  it("prevents advancing to step 2 with fewer than 2 sources (AC-2)", () => {
    renderWorkbench();
    const nextButton = screen.getByRole("button", { name: /next/i });
    // Clicking next with 0 sources should show an error toast, not advance
    fireEvent.click(nextButton);
    // We remain on sources step
    expect(screen.getByRole("region", { name: /data source browser/i })).toBeInTheDocument();
  });

  it("advances to overlap step when 2 sources are selected (AC-2)", () => {
    renderWorkbench();

    // Click on first two dataset cards (from INSEE)
    const buttons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(buttons[0]);
    fireEvent.click(buttons[1]);

    // Click Next
    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton);

    // Should now be on overlap step
    expect(screen.getByRole("region", { name: /variable overlap/i })).toBeInTheDocument();
  });

  it("navigates back from overlap to sources (AC-2)", () => {
    renderWorkbench();

    // Select 2 sources and advance
    const buttons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(buttons[0]);
    fireEvent.click(buttons[1]);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    // Now go back
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.getByRole("region", { name: /data source browser/i })).toBeInTheDocument();
  });
});
