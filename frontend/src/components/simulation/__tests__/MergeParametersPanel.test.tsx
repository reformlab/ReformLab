// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, fireEvent } from "@testing-library/react";

import { MergeParametersPanel } from "@/components/simulation/MergeParametersPanel";

describe("MergeParametersPanel", () => {
  const noop = () => {};

  it("renders seed parameter for all methods (AC-3)", () => {
    render(
      <MergeParametersPanel
        methodId="uniform"
        seed={42}
        strataColumns=""
        onSeedChange={noop}
        onStrataColumnsChange={noop}
      />,
    );

    expect(screen.getByLabelText(/random seed/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("42")).toBeInTheDocument();
  });

  it("shows strata columns input for conditional method (AC-3)", () => {
    render(
      <MergeParametersPanel
        methodId="conditional"
        seed={42}
        strataColumns=""
        onSeedChange={noop}
        onStrataColumnsChange={noop}
      />,
    );

    expect(screen.getByLabelText(/stratification columns/i)).toBeInTheDocument();
  });

  it("does not show strata columns input for uniform method (AC-3)", () => {
    render(
      <MergeParametersPanel
        methodId="uniform"
        seed={42}
        strataColumns=""
        onSeedChange={noop}
        onStrataColumnsChange={noop}
      />,
    );

    expect(screen.queryByLabelText(/stratification columns/i)).not.toBeInTheDocument();
  });

  it("shows IPF note for ipf method (AC-3)", () => {
    render(
      <MergeParametersPanel
        methodId="ipf"
        seed={42}
        strataColumns=""
        onSeedChange={noop}
        onStrataColumnsChange={noop}
      />,
    );

    expect(screen.getByText(/ipf constraints/i)).toBeInTheDocument();
  });

  it("calls onSeedChange when seed input changes (AC-6)", () => {
    const onSeedChange = vi.fn();
    render(
      <MergeParametersPanel
        methodId="uniform"
        seed={42}
        strataColumns=""
        onSeedChange={onSeedChange}
        onStrataColumnsChange={noop}
      />,
    );

    const seedInput = screen.getByLabelText(/random seed/i);
    fireEvent.change(seedInput, { target: { value: "99" } });
    expect(onSeedChange).toHaveBeenCalledWith(99);
  });
});
