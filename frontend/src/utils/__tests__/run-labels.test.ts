// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for run-labels.ts — Story 27.10, AC-12.
 */

import { describe, it, expect } from "vitest";
import { policyLabel } from "../run-labels";

describe("policyLabel", () => {
  it("returns portfolio_name when present", () => {
    expect(policyLabel({ portfolio_name: "Tax Reform A", template_name: null, run_kind: "portfolio" }))
      .toBe("Tax Reform A");
    expect(policyLabel({ portfolio_name: "My Portfolio", template_name: "Some Template", run_kind: "portfolio" }))
      .toBe("My Portfolio");
  });

  it("returns template_name when portfolio_name is absent", () => {
    expect(policyLabel({ portfolio_name: null, template_name: "Carbon Tax", run_kind: "scenario" }))
      .toBe("Carbon Tax");
    expect(policyLabel({ portfolio_name: null, template_name: "Subsidy Policy", run_kind: null }))
      .toBe("Subsidy Policy");
  });

  it("returns Portfolio run when run_kind is portfolio and no names", () => {
    expect(policyLabel({ portfolio_name: null, template_name: null, run_kind: "portfolio" }))
      .toBe("Portfolio run");
  });

  it("returns Scenario run when run_kind is scenario and no names", () => {
    expect(policyLabel({ portfolio_name: null, template_name: null, run_kind: "scenario" }))
      .toBe("Scenario run");
  });

  it("returns Scenario run as default when run_kind is null and no names", () => {
    expect(policyLabel({ portfolio_name: null, template_name: null, run_kind: null }))
      .toBe("Scenario run");
  });

  it("handles undefined values gracefully", () => {
    expect(policyLabel({ portfolio_name: undefined, template_name: undefined, run_kind: undefined }))
      .toBe("Scenario run");
  });
});
