// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for formatters.ts — Story 27.10, AC-1 through AC-7, AC-10.
 */

import { describe, it, expect } from "vitest";
import {
  formatNumber,
  formatCurrency,
  formatPercent,
  formatDate,
  formatTimestamp,
  formatLargeNumber,
} from "../formatters";

describe("formatNumber", () => {
  it("formats numbers with thousands separator and 0 decimals by default", () => {
    expect(formatNumber(1234.56)).toBe("1,235");
    expect(formatNumber(1234567)).toBe("1,234,567");
  });

  it("respects decimals option", () => {
    expect(formatNumber(1234.56, { decimals: 2 })).toBe("1,234.56");
    expect(formatNumber(1234.56, { decimals: 1 })).toBe("1,234.6");
  });

  it("handles null/undefined as em dash", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
  });

  it("handles NaN", () => {
    expect(formatNumber(NaN)).toBe("NaN");
  });

  it("handles Infinity", () => {
    expect(formatNumber(Infinity)).toBe("∞");
    expect(formatNumber(-Infinity)).toBe("-∞");
  });

  it("handles negative values", () => {
    expect(formatNumber(-1234.56)).toBe("-1,235");
  });

  it("handles zero", () => {
    expect(formatNumber(0)).toBe("0");
  });

  it("handles very large numbers", () => {
    expect(formatNumber(2100000000)).toBe("2,100,000,000");
  });
});

describe("formatCurrency", () => {
  it("formats currency with € prefix, thousands separator, 0 decimals by default", () => {
    expect(formatCurrency(1234.56)).toBe("€1,235");
    expect(formatCurrency(1234567)).toBe("€1,234,567");
  });

  it("handles null/undefined as em dash", () => {
    expect(formatCurrency(null)).toBe("—");
    expect(formatCurrency(undefined)).toBe("—");
  });

  it("respects decimals option", () => {
    expect(formatCurrency(1234.56, { decimals: 2 })).toBe("€1,234.56");
  });

  it("respects symbol option", () => {
    expect(formatCurrency(1234.56, { symbol: "$" })).toBe("$1,235");
  });

  it("appends /yr when perYear is true", () => {
    expect(formatCurrency(1234.56, { perYear: true })).toBe("€1,235/yr");
  });

  it("handles negative values", () => {
    expect(formatCurrency(-1234.56)).toBe("-€1,235");
  });
});

describe("formatPercent", () => {
  it("multiplies by 100 and appends %, 0 decimals by default", () => {
    expect(formatPercent(0.44)).toBe("44%");
    expect(formatPercent(0.5)).toBe("50%");
  });

  it("handles null/undefined as em dash", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(undefined)).toBe("—");
  });

  it("respects decimals option", () => {
    expect(formatPercent(0.444, { decimals: 1 })).toBe("44.4%");
    expect(formatPercent(0.444, { decimals: 2 })).toBe("44.40%");
  });

  it("handles multiplyBy100 option", () => {
    expect(formatPercent(44, { multiplyBy100: false })).toBe("44%");
  });

  it("handles negative values", () => {
    expect(formatPercent(-0.44)).toBe("-44%");
  });
});

describe("formatDate", () => {
  it("formats ISO date string as 'May 13, 2026'", () => {
    expect(formatDate("2026-05-13")).toBe("May 13, 2026");
    expect(formatDate("2026-12-31")).toBe("Dec 31, 2026");
  });

  it("handles Date objects", () => {
    expect(formatDate(new Date("2026-05-13"))).toBe("May 13, 2026");
  });

  it("handles null/undefined as em dash", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("returns original string for invalid dates", () => {
    expect(formatDate("invalid-date")).toBe("invalid-date");
  });
});

describe("formatTimestamp", () => {
  it("formats short style (default) without seconds", () => {
    // Match pattern: "Month DD, YYYY, HH:MM AM/PM"
    expect(formatTimestamp("2026-05-13T14:48:00Z")).toMatch(/May 13, 2026, \d{2}:\d{2} [AP]M/);
    expect(formatTimestamp("2026-05-13T09:05:00Z")).toMatch(/May 13, 2026, \d{2}:\d{2} [AP]M/);
  });

  it("formats full style with seconds", () => {
    // Match pattern with seconds: "Month DD, YYYY, HH:MM:SS AM/PM"
    expect(formatTimestamp("2026-05-13T14:48:00Z", "full")).toMatch(/May 13, 2026, \d{2}:\d{2}:\d{2} [AP]M/);
  });

  it("handles Date objects", () => {
    expect(formatTimestamp(new Date("2026-05-13T14:48:00Z"))).toMatch(/May 13, 2026, \d{2}:\d{2} [AP]M/);
  });

  it("handles null/undefined as em dash", () => {
    expect(formatTimestamp(null)).toBe("—");
    expect(formatTimestamp(undefined)).toBe("—");
  });

  it("returns original string for invalid dates", () => {
    expect(formatTimestamp("invalid-timestamp")).toBe("invalid-timestamp");
  });
});

describe("formatLargeNumber", () => {
  it("formats billions with B suffix", () => {
    expect(formatLargeNumber(2100000000)).toBe("2.1B");
    expect(formatLargeNumber(1000000000)).toBe("1.0B");
    expect(formatLargeNumber(1234567890)).toBe("1.2B");
  });

  it("formats millions with M suffix", () => {
    expect(formatLargeNumber(1500000)).toBe("1.5M");
    expect(formatLargeNumber(1000000)).toBe("1.0M");
    expect(formatLargeNumber(1234567)).toBe("1.2M");
  });

  it("formats thousands with k suffix", () => {
    expect(formatLargeNumber(2500)).toBe("2.5k");
    expect(formatLargeNumber(1000)).toBe("1.0k");
    expect(formatLargeNumber(1234)).toBe("1.2k");
  });

  it("handles small numbers without suffix", () => {
    expect(formatLargeNumber(999)).toBe("999");
    expect(formatLargeNumber(100)).toBe("100");
    expect(formatLargeNumber(0)).toBe("0");
  });

  it("handles negative values", () => {
    expect(formatLargeNumber(-2100000000)).toBe("-2.1B");
    expect(formatLargeNumber(-1500000)).toBe("-1.5M");
    expect(formatLargeNumber(-2500)).toBe("-2.5k");
  });

  it("handles abs < 1 as 0", () => {
    expect(formatLargeNumber(0.5)).toBe("0");
    expect(formatLargeNumber(-0.5)).toBe("0");
  });

  it("handles null/undefined as em dash", () => {
    expect(formatLargeNumber(null)).toBe("—");
    expect(formatLargeNumber(undefined)).toBe("—");
  });
});
