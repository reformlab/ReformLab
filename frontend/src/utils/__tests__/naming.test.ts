// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for naming.ts utilities — Story 22.3.
 *
 * Tests:
 * - slugify() with various edge cases
 * - generatePortfolioSuggestion() with 0, 1, 2, 3+ templates
 * - generatePortfolioSuggestion() outputs always pass validatePortfolioName
 * - generateScenarioSuggestion() with portfolio + population
 * - generateScenarioSuggestion() with portfolio only
 * - generateScenarioSuggestion() with no context
 * - getPopulationShortName() with "France " prefix removal
 * - generatePortfolioCloneName() with collision handling
 * - generateScenarioCloneName() with collision handling
 */

import { describe, expect, it } from "vitest";

import {
  slugify,
  generatePortfolioSuggestion,
  getPopulationShortName,
  generateScenarioSuggestion,
  generatePortfolioCloneName,
  generateScenarioCloneName,
} from "@/utils/naming";
import { validatePortfolioName } from "@/components/simulation/portfolioValidation";
import type { Template } from "@/data/mock-data";
import type { Population } from "@/data/mock-data";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";

// ============================================================================
// Mock data
// ============================================================================

const mockTemplates: Template[] = [
  { id: "carbon-tax-flat", name: "Carbon Tax — Flat Rate", type: "carbon-tax", parameterCount: 8, description: "Flat carbon tax", parameterGroups: ["Rates"] },
  { id: "carbon-tax-progressive", name: "Carbon Tax — Progressive", type: "carbon-tax", parameterCount: 12, description: "Progressive carbon tax", parameterGroups: ["Rates"] },
  { id: "subsidy-energy", name: "Energy Efficiency Subsidy", type: "subsidy", parameterCount: 6, description: "Energy subsidy", parameterGroups: ["Redistribution"] },
  { id: "feebate-vehicle", name: "Vehicle Feebate", type: "feebate", parameterCount: 9, description: "Vehicle feebate", parameterGroups: ["Redistribution"] },
];

const mockPopulations: Population[] = [
  { id: "fr-synthetic-2024", name: "France Synthetic 2024", households: 100_000, source: "INSEE", year: 2024 },
  { id: "fr-household-2023", name: "France Household Panel 2023", households: 50_000, source: "INSEE", year: 2023 },
  { id: "eu-silc-2022", name: "EU-SILC France Extract 2022", households: 50_000, source: "Eurostat", year: 2022 },
];

const makeComposition = (templateIds: string[]): CompositionEntry[] =>
  templateIds.map((id) => {
    const template = mockTemplates.find((t) => t.id === id);
    return {
      templateId: id,
      name: template?.name ?? id,
      parameters: {},
      rateSchedule: {},
    };
  });

// ============================================================================
// slugify() tests
// ============================================================================

describe("slugify()", () => {
  it("converts spaces to hyphens", () => {
    expect(slugify("Carbon Tax Flat Rate")).toBe("carbon-tax-flat-rate");
  });

  it("converts em-dashes to hyphens", () => {
    expect(slugify("Carbon Tax — Flat Rate")).toBe("carbon-tax-flat-rate");
  });

  it("converts en-dashes to hyphens", () => {
    expect(slugify("Carbon Tax – Flat Rate")).toBe("carbon-tax-flat-rate");
  });

  it("removes accented characters", () => {
    expect(slugify("Éco—Taxe")).toBe("eco-taxe");
  });

  it("collapses multiple consecutive hyphens", () => {
    expect(slugify("Carbon  Tax    Flat")).toBe("carbon-tax-flat");
  });

  it("trims leading hyphens", () => {
    expect(slugify("  Carbon Tax")).toBe("carbon-tax");
  });

  it("trims trailing hyphens", () => {
    expect(slugify("Carbon Tax  ")).toBe("carbon-tax");
  });

  it("removes special characters", () => {
    expect(slugify("Tax@Rate#2024!")).toBe("taxrate2024");
  });

  it("preserves digits", () => {
    expect(slugify("Subsidy 2024")).toBe("subsidy-2024");
  });

  it("truncates to 64 characters", () => {
    const longName = "A".repeat(100);
    expect(slugify(longName)).toHaveLength(64);
  });

  it("handles empty string", () => {
    expect(slugify("")).toBe("");
  });

  it("handles special unicode characters", () => {
    expect(slugify("Naïve — façade")).toBe("naive-facade");
  });
});

// ============================================================================
// generatePortfolioSuggestion() tests
// ============================================================================

describe("generatePortfolioSuggestion()", () => {
  it("returns 'untitled-portfolio' for empty composition", () => {
    const result = generatePortfolioSuggestion(mockTemplates, []);
    expect(result).toBe("untitled-portfolio");
  });

  it("uses slugified template name for single policy", () => {
    const composition = makeComposition(["carbon-tax-flat"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result).toBe("carbon-tax-flat-rate");
  });

  it("joins two slugified names with '-plus-' for two policies", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result).toBe("carbon-tax-flat-rate-plus-energy-efficiency-subsidy");
  });

  it("uses 'first-plus-(N-1)-more' pattern for 3+ policies", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy", "feebate-vehicle"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result).toBe("carbon-tax-flat-rate-plus-2-more");
  });

  it("uses 'first-plus-(N-1)-more' pattern for 4 policies", () => {
    const composition = makeComposition(["carbon-tax-flat", "carbon-tax-progressive", "subsidy-energy", "feebate-vehicle"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result).toBe("carbon-tax-flat-rate-plus-3-more");
  });

  it("uses entry name when template not found in templates list", () => {
    const composition: CompositionEntry[] = [
      { templateId: "unknown-id", name: "Custom Policy Name", parameters: {}, rateSchedule: {} },
    ];
    const result = generatePortfolioSuggestion([], composition);
    expect(result).toBe("custom-policy-name");
  });

  it("all suggestions pass validatePortfolioName validation", () => {
    const testCases = [
      [],
      makeComposition(["carbon-tax-flat"]),
      makeComposition(["carbon-tax-flat", "subsidy-energy"]),
      makeComposition(["carbon-tax-flat", "subsidy-energy", "feebate-vehicle"]),
      makeComposition(["carbon-tax-flat", "carbon-tax-progressive", "subsidy-energy", "feebate-vehicle"]),
    ];

    for (const composition of testCases) {
      const suggestion = generatePortfolioSuggestion(mockTemplates, composition);
      const validationError = validatePortfolioName(suggestion);
      expect(validationError).toBeNull();
      expect(validationError).withContext(`Suggestion "${suggestion}" should pass validation`).toBeNull();
    }
  });

  it("suggestions are lowercase (validatePortfolioName requirement)", () => {
    const composition = makeComposition(["carbon-tax-flat"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result).toBe(result.toLowerCase());
  });

  it("suggestions contain only alphanumeric and hyphens (validatePortfolioName requirement)", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result).toMatch(/^[a-z0-9-]+$/);
  });

  it("suggestions are max 64 characters (validatePortfolioName requirement)", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
    const result = generatePortfolioSuggestion(mockTemplates, composition);
    expect(result.length).toBeLessThanOrEqual(64);
  });
});

// ============================================================================
// getPopulationShortName() tests
// ============================================================================

describe("getPopulationShortName()", () => {
  it("removes 'France ' prefix and adds 'FR ' prefix", () => {
    const population = mockPopulations[0]!;
    const result = getPopulationShortName(population);
    expect(result).toBe("FR Synthetic 2024");
  });

  it("removes 'France ' prefix for household panel", () => {
    const population = mockPopulations[1]!;
    const result = getPopulationShortName(population);
    expect(result).toBe("FR Household Panel 2023");
  });

  it("does not modify 'EU ' prefix populations", () => {
    const population = mockPopulations[2]!;
    const result = getPopulationShortName(population);
    expect(result).toBe("EU-SILC France Extract 2022");
  });

  it("keeps year suffix for context", () => {
    const population: Population = {
      id: "test",
      name: "France Test 2030",
      households: 1000,
      source: "Test",
      year: 2030,
    };
    const result = getPopulationShortName(population);
    expect(result).toContain("2030");
  });
});

// ============================================================================
// generateScenarioSuggestion() tests
// ============================================================================

describe("generateScenarioSuggestion()", () => {
  it("uses portfolio name with population in parentheses", () => {
    const composition = makeComposition(["carbon-tax-flat"]);
    const result = generateScenarioSuggestion(
      "my-portfolio",
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      composition,
    );
    expect(result).toBe("my-portfolio (FR Synthetic 2024)");
  });

  it("uses portfolio name only when no population selected", () => {
    const composition = makeComposition(["carbon-tax-flat"]);
    const result = generateScenarioSuggestion(
      "my-portfolio",
      "",
      [],
      mockTemplates,
      composition,
    );
    expect(result).toBe("my-portfolio");
  });

  it("generates from composition when portfolioName is null", () => {
    const composition = makeComposition(["carbon-tax-flat"]);
    const result = generateScenarioSuggestion(
      null,
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      composition,
    );
    expect(result).toBe("carbon-tax-flat-rate (FR Synthetic 2024)");
  });

  it("returns 'Untitled (population)' when no portfolio and empty composition", () => {
    const result = generateScenarioSuggestion(
      null,
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      [],
    );
    expect(result).toBe("Untitled (FR Synthetic 2024)");
  });

  it("returns 'Untitled Scenario' when no context at all", () => {
    const result = generateScenarioSuggestion(
      null,
      "",
      [],
      mockTemplates,
      [],
    );
    expect(result).toBe("Untitled Scenario");
  });

  it("handles 2-policy composition in scenario suggestion", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
    const result = generateScenarioSuggestion(
      null,
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      composition,
    );
    expect(result).toBe("carbon-tax-flat-rate-plus-energy-efficiency-subsidy (FR Synthetic 2024)");
  });

  it("handles 3+ policy composition in scenario suggestion", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy", "feebate-vehicle"]);
    const result = generateScenarioSuggestion(
      null,
      "fr-synthetic-2024",
      mockPopulations,
      mockTemplates,
      composition,
    );
    expect(result).toBe("carbon-tax-flat-rate-plus-2-more (FR Synthetic 2024)");
  });
});

// ============================================================================
// generatePortfolioCloneName() tests
// ============================================================================

describe("generatePortfolioCloneName()", () => {
  it("appends '-copy' to original name", () => {
    const existingNames = new Set<string>();
    const result = generatePortfolioCloneName("my-portfolio", existingNames);
    expect(result).toBe("my-portfolio-copy");
  });

  it("appends '-copy-2' when '-copy' already exists", () => {
    const existingNames = new Set(["my-portfolio-copy"]);
    const result = generatePortfolioCloneName("my-portfolio", existingNames);
    expect(result).toBe("my-portfolio-copy-2");
  });

  it("appends '-copy-3' when '-copy' and '-copy-2' exist", () => {
    const existingNames = new Set(["my-portfolio-copy", "my-portfolio-copy-2"]);
    const result = generatePortfolioCloneName("my-portfolio", existingNames);
    expect(result).toBe("my-portfolio-copy-3");
  });

  it("handles multiple existing clones", () => {
    const existingNames = new Set(["my-portfolio-copy", "my-portfolio-copy-2", "my-portfolio-copy-3", "my-portfolio-copy-4"]);
    const result = generatePortfolioCloneName("my-portfolio", existingNames);
    expect(result).toBe("my-portfolio-copy-5");
  });

  it("does not collide with unrelated names", () => {
    const existingNames = new Set(["other-portfolio-copy"]);
    const result = generatePortfolioCloneName("my-portfolio", existingNames);
    expect(result).toBe("my-portfolio-copy");
  });
});

// ============================================================================
// generateScenarioCloneName() tests
// ============================================================================

describe("generateScenarioCloneName()", () => {
  it("appends ' (copy)' to original name", () => {
    const existingNames = new Set<string>();
    const result = generateScenarioCloneName("My Scenario", existingNames);
    expect(result).toBe("My Scenario (copy)");
  });

  it("appends ' (copy 2)' when ' (copy)' already exists", () => {
    const existingNames = new Set(["My Scenario (copy)"]);
    const result = generateScenarioCloneName("My Scenario", existingNames);
    expect(result).toBe("My Scenario (copy 2)");
  });

  it("appends ' (copy 3)' when ' (copy)' and ' (copy 2)' exist", () => {
    const existingNames = new Set(["My Scenario (copy)", "My Scenario (copy 2)"]);
    const result = generateScenarioCloneName("My Scenario", existingNames);
    expect(result).toBe("My Scenario (copy 3)");
  });

  it("handles multiple existing clones", () => {
    const existingNames = new Set([
      "My Scenario (copy)",
      "My Scenario (copy 2)",
      "My Scenario (copy 3)",
      "My Scenario (copy 4)",
    ]);
    const result = generateScenarioCloneName("My Scenario", existingNames);
    expect(result).toBe("My Scenario (copy 5)");
  });

  it("does not collide with unrelated names", () => {
    const existingNames = new Set(["Other Scenario (copy)"]);
    const result = generateScenarioCloneName("My Scenario", existingNames);
    expect(result).toBe("My Scenario (copy)");
  });
});
