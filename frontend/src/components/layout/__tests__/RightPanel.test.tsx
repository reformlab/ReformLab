import { render, screen } from "@testing-library/react";

import { RightPanel } from "@/components/layout/RightPanel";

describe("RightPanel", () => {
  it("shows Help header when expanded", () => {
    render(<RightPanel collapsed={false} onToggle={() => {}}><div /></RightPanel>);
    expect(screen.getByText("Help")).toBeInTheDocument();
    expect(screen.queryByText("Run Context")).not.toBeInTheDocument();
  });

  it("shows Help label when collapsed", () => {
    render(<RightPanel collapsed={true} onToggle={() => {}}><div /></RightPanel>);
    expect(screen.getByText("Help")).toBeInTheDocument();
    expect(screen.queryByText("Context")).not.toBeInTheDocument();
  });
});
