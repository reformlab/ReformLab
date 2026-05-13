// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for status-variants.ts — Story 27.10, AC-8.
 */

import { describe, it, expect } from "vitest";
import { statusVariant } from "@/lib/status-variants";

describe("statusVariant", () => {
  it("returns success for completed status", () => {
    expect(statusVariant("completed")).toBe("success");
  });

  it("returns destructive for failed status", () => {
    expect(statusVariant("failed")).toBe("destructive");
  });

  it("returns warning for running status", () => {
    expect(statusVariant("running")).toBe("warning");
  });

  it("returns warning for pending status", () => {
    expect(statusVariant("pending")).toBe("warning");
  });

  it("returns warning for queued status", () => {
    expect(statusVariant("queued")).toBe("warning");
  });

  it("returns warning for unknown status", () => {
    expect(statusVariant("unknown")).toBe("warning");
  });

  it("returns warning for empty string", () => {
    expect(statusVariant("")).toBe("warning");
  });
});
