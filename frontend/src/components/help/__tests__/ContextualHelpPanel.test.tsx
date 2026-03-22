import { render, screen } from "@testing-library/react";

import { ContextualHelpPanel } from "@/components/help/ContextualHelpPanel";

describe("ContextualHelpPanel", () => {
  it("renders Population Builder title for data-fusion viewMode", () => {
    render(<ContextualHelpPanel viewMode="data-fusion" />);
    expect(screen.getByText("Population Builder")).toBeInTheDocument();
  });

  it("renders Portfolio Designer title for portfolio viewMode", () => {
    render(<ContextualHelpPanel viewMode="portfolio" />);
    expect(screen.getByText("Portfolio Designer")).toBeInTheDocument();
  });

  it("renders Results Overview title for results viewMode", () => {
    render(<ContextualHelpPanel viewMode="results" />);
    expect(screen.getByText("Results Overview")).toBeInTheDocument();
  });

  it("renders Comparison Dashboard title for comparison viewMode", () => {
    render(<ContextualHelpPanel viewMode="comparison" />);
    expect(screen.getByText("Comparison Dashboard")).toBeInTheDocument();
  });

  it("renders sub-step help for configuration:population", () => {
    render(<ContextualHelpPanel viewMode="configuration" activeStep="population" />);
    expect(screen.getByText("Select Population")).toBeInTheDocument();
  });

  it("renders sub-step help for configuration:template", () => {
    render(<ContextualHelpPanel viewMode="configuration" activeStep="template" />);
    expect(screen.getByText("Choose Policy Template")).toBeInTheDocument();
  });

  it("renders sub-step help for configuration:parameters", () => {
    render(<ContextualHelpPanel viewMode="configuration" activeStep="parameters" />);
    expect(screen.getByText("Configure Parameters")).toBeInTheDocument();
  });

  it("renders sub-step help for configuration:assumptions", () => {
    render(<ContextualHelpPanel viewMode="configuration" activeStep="assumptions" />);
    expect(screen.getByText("Review Assumptions")).toBeInTheDocument();
  });

  it("falls back to configuration:population for unrecognized viewMode", () => {
    render(<ContextualHelpPanel viewMode="unknown-mode" />);
    expect(screen.getByText("Select Population")).toBeInTheDocument();
  });

  it("renders tips as list items", () => {
    const { container } = render(<ContextualHelpPanel viewMode="results" />);
    const listItems = container.querySelectorAll("ul > li");
    expect(listItems.length).toBeGreaterThanOrEqual(3);
  });

  it("renders Key Concepts trigger for entries with concepts", () => {
    render(<ContextualHelpPanel viewMode="data-fusion" />);
    expect(screen.getByText("Key Concepts")).toBeInTheDocument();
  });

  it("does not render Key Concepts for entries without concepts", () => {
    render(<ContextualHelpPanel viewMode="progress" />);
    expect(screen.queryByText("Key Concepts")).not.toBeInTheDocument();
  });
});
