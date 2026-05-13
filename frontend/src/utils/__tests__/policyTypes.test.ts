// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Policy type normalization tests (Story 27.11, Task 1).
 *
 * Tests for normalizePolicyType utility and TYPE_LABELS/TYPE_COLORS constants.
 */

import { describe, expect, it } from "vitest";
import { normalizePolicyType } from "../policyTypes";
import { TYPE_LABELS, TYPE_COLORS } from "@/components/simulation/typeConstants";

describe("normalizePolicyType", () => {
  describe("kebab-case to snake_case conversion", () => {
    it("converts carbon-tax to carbon_tax", () => {
      expect(normalizePolicyType("carbon-tax")).toBe("carbon_tax");
    });

    it("converts multi-hyphen types like vehicle-malus to vehicle_malus", () => {
      expect(normalizePolicyType("vehicle-malus")).toBe("vehicle_malus");
    });

    it("converts energy-poverty-aid to energy_poverty_aid", () => {
      expect(normalizePolicyType("energy-poverty-aid")).toBe("energy_poverty_aid");
    });
  });

  describe("snake_case passthrough (no-op)", () => {
    it("returns carbon_tax unchanged", () => {
      expect(normalizePolicyType("carbon_tax")).toBe("carbon_tax");
    });

    it("returns vehicle_malus unchanged", () => {
      expect(normalizePolicyType("vehicle_malus")).toBe("vehicle_malus");
    });

    it("returns energy_poverty_aid unchanged", () => {
      expect(normalizePolicyType("energy_poverty_aid")).toBe("energy_poverty_aid");
    });
  });

  describe("lowercase fundamental types (no-op)", () => {
    it("returns tax unchanged", () => {
      expect(normalizePolicyType("tax")).toBe("tax");
    });

    it("returns subsidy unchanged", () => {
      expect(normalizePolicyType("subsidy")).toBe("subsidy");
    });

    it("returns transfer unchanged", () => {
      expect(normalizePolicyType("transfer")).toBe("transfer");
    });
  });

  describe("edge cases", () => {
    it("returns empty string for null input", () => {
      expect(normalizePolicyType(null)).toBe("");
    });

    it("returns empty string for undefined input", () => {
      expect(normalizePolicyType(undefined)).toBe("");
    });

    it("returns empty string for empty string input", () => {
      expect(normalizePolicyType("")).toBe("");
    });

    it("handles single word with no hyphens or underscores", () => {
      expect(normalizePolicyType("feebate")).toBe("feebate");
    });
  });

  describe("idempotency", () => {
    it("running twice produces same result", () => {
      const input = "carbon-tax";
      const first = normalizePolicyType(input);
      const second = normalizePolicyType(first);
      expect(first).toBe("carbon_tax");
      expect(second).toBe("carbon_tax");
      expect(first).toBe(second);
    });

    it("snake_case input is idempotent", () => {
      const input = "carbon_tax";
      const first = normalizePolicyType(input);
      const second = normalizePolicyType(first);
      expect(first).toBe("carbon_tax");
      expect(second).toBe("carbon_tax");
    });
  });
});

describe("TYPE_LABELS", () => {
  it("contains only snake_case keys (no kebab-case duplicates)", () => {
    const keys = Object.keys(TYPE_LABELS);
    const kebabCaseKeys = keys.filter((key) => key.includes("-"));

    expect(kebabCaseKeys).toHaveLength(0);
    expect(kebabCaseKeys).toEqual([]);

    // All known policy types should be present in snake_case
    const expectedSnakeCaseKeys = [
      "carbon_tax",
      "subsidy",
      "rebate",
      "feebate",
      "vehicle_malus",
      "energy_poverty_aid",
      "tax",
      "transfer",
    ];

    for (const key of expectedSnakeCaseKeys) {
      expect(keys).toContain(key);
    }
  });

  it("provides labels for all canonical policy types", () => {
    expect(TYPE_LABELS["carbon_tax"]).toBe("Carbon Tax");
    expect(TYPE_LABELS["subsidy"]).toBe("Subsidy");
    expect(TYPE_LABELS["rebate"]).toBe("Rebate");
    expect(TYPE_LABELS["feebate"]).toBe("Feebate");
    expect(TYPE_LABELS["vehicle_malus"]).toBe("Vehicle Malus");
    expect(TYPE_LABELS["energy_poverty_aid"]).toBe("Energy Poverty Aid");
    expect(TYPE_LABELS["tax"]).toBe("Tax");
    expect(TYPE_LABELS["transfer"]).toBe("Transfer");
  });
});

describe("TYPE_COLORS", () => {
  it("contains only snake_case keys (no kebab-case duplicates)", () => {
    const keys = Object.keys(TYPE_COLORS);
    const kebabCaseKeys = keys.filter((key) => key.includes("-"));

    expect(kebabCaseKeys).toHaveLength(0);
    expect(kebabCaseKeys).toEqual([]);

    // All known policy types should be present in snake_case
    const expectedSnakeCaseKeys = [
      "carbon_tax",
      "subsidy",
      "rebate",
      "feebate",
      "vehicle_malus",
      "energy_poverty_aid",
      "tax",
      "transfer",
    ];

    for (const key of expectedSnakeCaseKeys) {
      expect(keys).toContain(key);
    }
  });

  it("provides Tailwind color classes for all canonical policy types", () => {
    expect(TYPE_COLORS["carbon_tax"]).toBe("bg-amber-100 text-amber-800");
    expect(TYPE_COLORS["subsidy"]).toBe("bg-emerald-100 text-emerald-800");
    expect(TYPE_COLORS["rebate"]).toBe("bg-blue-100 text-blue-800");
    expect(TYPE_COLORS["feebate"]).toBe("bg-violet-100 text-violet-800");
    expect(TYPE_COLORS["vehicle_malus"]).toBe("bg-rose-100 text-rose-800");
    expect(TYPE_COLORS["energy_poverty_aid"]).toBe("bg-cyan-100 text-cyan-800");
    expect(TYPE_COLORS["tax"]).toBe("bg-amber-100 text-amber-800");
    expect(TYPE_COLORS["transfer"]).toBe("bg-blue-100 text-blue-800");
  });
});
