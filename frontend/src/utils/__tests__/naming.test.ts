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
  extractTypeAndCategory,
  getDominantCategory,
  extractPrimaryParameterValue,
  formatParameterForName,
} from "@/utils/naming";
import { validatePortfolioName } from "@/components/simulation/portfolioValidation";
import type { Template } from "@/data/mock-data";
import type { Population } from "@/data/mock-data";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import type { Category } from "@/api/types";

// ============================================================================
// Mock data
// ============================================================================

const mockTemplates: Template[] = [
  { id: "carbon-tax-flat", name: "Carbon Tax — Flat Rate", type: "carbon-tax", parameterCount: 8, description: "Flat carbon tax", parameterGroups: ["Rates"], is_custom: false, runtime_availability: "live_ready", availability_reason: null },
  { id: "carbon-tax-progressive", name: "Carbon Tax — Progressive", type: "carbon-tax", parameterCount: 12, description: "Progressive carbon tax", parameterGroups: ["Rates"], is_custom: false, runtime_availability: "live_ready", availability_reason: null },
  { id: "subsidy-energy", name: "Energy Efficiency Subsidy", type: "subsidy", parameterCount: 6, description: "Energy subsidy", parameterGroups: ["Redistribution"], is_custom: false, runtime_availability: "live_ready", availability_reason: null },
  { id: "feebate-vehicle", name: "Vehicle Feebate", type: "feebate", parameterCount: 9, description: "Vehicle feebate", parameterGroups: ["Redistribution"], is_custom: false, runtime_availability: "live_ready", availability_reason: null },
];

const mockPopulations: Population[] = [
  { id: "fr-synthetic-2024", name: "France Synthetic 2024", households: 100_000, source: "INSEE", year: 2024 },
  { id: "fr-household-2023", name: "France Household Panel 2023", households: 50_000, source: "INSEE", year: 2023 },
  { id: "eu-silc-2022", name: "EU-SILC France Extract 2022", households: 50_000, source: "Eurostat", year: 2022 },
];

// Story 27.9: Mock categories for type-category naming
const mockCategories: Category[] = [
  { id: "carbon-emissions", label: "Carbon Emissions", columns: [], compatible_types: ["tax"], formula_explanation: "", description: "" },
  { id: "vehicle-emissions", label: "Vehicle Emissions", columns: [], compatible_types: ["tax", "subsidy"], formula_explanation: "", description: "" },
  { id: "energy-consumption", label: "Energy Consumption", columns: [], compatible_types: ["subsidy"], formula_explanation: "", description: "" },
  { id: "income", label: "Income", columns: [], compatible_types: ["tax", "transfer"], formula_explanation: "", description: "" },
];

// Story 27.9: Templates with category_id for testing
const mockTemplatesWithCategories: Template[] = [
  { id: "carbon-tax-flat", name: "Carbon Tax — Flat Rate", type: "carbon-tax", parameterCount: 8, description: "Flat carbon tax", parameterGroups: ["Rates"], is_custom: false, runtime_availability: "live_ready", availability_reason: null, category_id: "carbon-emissions" },
  { id: "carbon-tax-progressive", name: "Carbon Tax — Progressive", type: "carbon-tax", parameterCount: 12, description: "Progressive carbon tax", parameterGroups: ["Rates"], is_custom: false, runtime_availability: "live_ready", availability_reason: null, category_id: "carbon-emissions" },
  { id: "subsidy-energy", name: "Energy Efficiency Subsidy", type: "subsidy", parameterCount: 6, description: "Energy subsidy", parameterGroups: ["Redistribution"], is_custom: false, runtime_availability: "live_ready", availability_reason: null, category_id: "energy-consumption" },
  { id: "feebate-vehicle", name: "Vehicle Feebate", type: "feebate", parameterCount: 9, description: "Vehicle feebate", parameterGroups: ["Redistribution"], is_custom: false, runtime_availability: "live_ready", availability_reason: null, category_id: "vehicle-emissions" },
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

// Story 27.9: Helper to create composition with from-scratch policy
const makeFromScratchComposition = (policyType: string, categoryId: string): CompositionEntry[] => [
  {
    templateId: "",
    name: `${policyType.charAt(0).toUpperCase() + policyType.slice(1)} — Test`,
    parameters: {},
    rateSchedule: {},
    policy_type: policyType,
    category_id: categoryId,
  },
];

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
      expect(validationError, `Suggestion "${suggestion}" should pass validation`).toBeNull();
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
// Story 27.9: extractTypeAndCategory() tests
// ============================================================================

describe("extractTypeAndCategory()", () => {
  it("extracts type and category from template policy", () => {
    const entry: CompositionEntry = {
      templateId: "carbon-tax-flat",
      name: "Carbon Tax — Flat Rate",
      parameters: {},
      rateSchedule: {},
    };
    const result = extractTypeAndCategory(entry, mockTemplatesWithCategories, mockCategories);
    expect(result).toEqual({
      policyType: "tax",
      categoryId: "carbon-emissions",
      categoryLabel: "Carbon Emissions",
    });
  });

  it("extracts type and category from from-scratch policy", () => {
    const entry: CompositionEntry = {
      templateId: "",
      name: "Tax — Test",
      parameters: {},
      rateSchedule: {},
      policy_type: "tax",
      category_id: "income",
    };
    const result = extractTypeAndCategory(entry, mockTemplatesWithCategories, mockCategories);
    expect(result).toEqual({
      policyType: "tax",
      categoryId: "income",
      categoryLabel: "Income",
    });
  });

  it("returns 'policy' type when template.type not recognized", () => {
    const entry: CompositionEntry = {
      templateId: "unknown-template",
      name: "Unknown Template",
      parameters: {},
      rateSchedule: {},
    };
    const templatesWithUnknown: Template[] = [
      { id: "unknown-template", name: "Unknown", type: "unknown-type", parameterCount: 0, description: "", parameterGroups: [], is_custom: false, runtime_availability: "live_ready", availability_reason: null },
    ];
    const result = extractTypeAndCategory(entry, templatesWithUnknown, mockCategories);
    expect(result.policyType).toBe("policy");
  });

  it("returns 'other' category when category_id not found", () => {
    const entry: CompositionEntry = {
      templateId: "carbon-tax-flat",
      name: "Carbon Tax",
      parameters: {},
      rateSchedule: {},
    };
    const templatesWithBadCategory: Template[] = [
      { ...mockTemplatesWithCategories[0]!, category_id: "non-existent" },
    ];
    const result = extractTypeAndCategory(entry, templatesWithBadCategory, mockCategories);
    expect(result.categoryLabel).toBe("other");
  });

  it("handles null categories gracefully", () => {
    const entry: CompositionEntry = {
      templateId: "carbon-tax-flat",
      name: "Carbon Tax",
      parameters: {},
      rateSchedule: {},
    };
    const result = extractTypeAndCategory(entry, mockTemplatesWithCategories, null);
    expect(result.policyType).toBe("tax");
    expect(result.categoryId).toBeUndefined();
    expect(result.categoryLabel).toBe("other");
  });
});

// ============================================================================
// Story 27.9: getDominantCategory() tests
// ============================================================================

describe("getDominantCategory()", () => {
  it("returns most common category when clear winner", () => {
    const composition = makeComposition(["carbon-tax-flat", "carbon-tax-progressive", "subsidy-energy"]);
    const result = getDominantCategory(composition, mockTemplatesWithCategories, mockCategories);
    expect(result.categoryLabel).toBe("Carbon Emissions"); // 2 carbon, 1 energy
  });

  it("returns first policy's category on tie", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
    const result = getDominantCategory(composition, mockTemplatesWithCategories, mockCategories);
    expect(result.categoryLabel).toBe("Carbon Emissions"); // First policy's category
  });

  it("handles single policy composition", () => {
    const composition = makeComposition(["subsidy-energy"]);
    const result = getDominantCategory(composition, mockTemplatesWithCategories, mockCategories);
    expect(result.categoryLabel).toBe("Energy Consumption");
  });

  it("handles null categories", () => {
    const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
    const result = getDominantCategory(composition, mockTemplatesWithCategories, null);
    expect(result.categoryLabel).toBe("other");
  });

  it("handles from-scratch policies", () => {
    const composition: CompositionEntry[] = [
      { templateId: "", name: "Tax — Income", parameters: {}, rateSchedule: {}, policy_type: "tax", category_id: "income" },
      { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: {}, rateSchedule: {} },
    ];
    const templatesWithCarbon: Template[] = [mockTemplatesWithCategories[0]!];
    const result = getDominantCategory(composition, templatesWithCarbon, mockCategories);
    expect(result.categoryLabel).toBe("Income"); // First policy's category (tie)
  });
});

// ============================================================================
// Story 27.9: generatePortfolioSuggestion() with type-category tests
// ============================================================================

describe("generatePortfolioSuggestion() - Story 27.9 type-category naming", () => {
  describe("single policy naming", () => {
    it("uses 'type-category' pattern for single template policy", () => {
      const composition = makeComposition(["carbon-tax-flat"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toBe("tax-carbon-emissions");
    });

    it("uses 'type-category' pattern for single subsidy policy", () => {
      const composition = makeComposition(["subsidy-energy"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toBe("subsidy-energy-consumption");
    });

    it("reuses from-scratch policy name when already in '{Type} — {Category}' format", () => {
      // Create a from-scratch policy with a custom name that matches the pattern
      const composition: CompositionEntry[] = [
        {
          templateId: "",
          name: "Tax — Carbon Emissions",  // Matches "{Type} — {Category}" pattern
          parameters: {},
          rateSchedule: {},
          policy_type: "tax",
          category_id: "carbon-emissions",  // Category matches the name
        },
      ];
      const result = generatePortfolioSuggestion([], composition, mockCategories);
      // AC-2: Should reuse the slugified name, not extract type-category again
      expect(result).toBe("tax-carbon-emissions");
    });

    it("falls back to entry name when template not found", () => {
      const composition: CompositionEntry[] = [
        { templateId: "unknown", name: "Custom Policy Name", parameters: {}, rateSchedule: {} },
      ];
      const result = generatePortfolioSuggestion([], composition, mockCategories);
      expect(result).toBe("custom-policy-name");
    });
  });

  describe("multi-policy naming", () => {
    it("uses '{category}-policies' for same-category compositions", () => {
      const composition = makeComposition(["carbon-tax-flat", "carbon-tax-progressive"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toBe("carbon-emissions-policies");
    });

    it("uses '{dominant-category}-plus-{N-1}-more' for mixed categories", () => {
      const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toBe("carbon-emissions-plus-1-more");
    });

    it("correctly counts 'more' for 3+ mixed policies", () => {
      const composition = makeComposition(["carbon-tax-flat", "carbon-tax-progressive", "subsidy-energy", "feebate-vehicle"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toBe("carbon-emissions-plus-2-more"); // 2 carbon, 2 others
    });
  });

  describe("backward compatibility", () => {
    it("falls back to old naming when categories is null", () => {
      const composition = makeComposition(["carbon-tax-flat"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, null);
      expect(result).toBe("carbon-tax-flat-rate"); // Old behavior: slugified template name
    });

    it("falls back to old naming when categories is empty array", () => {
      const composition = makeComposition(["carbon-tax-flat"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, []);
      expect(result).toBe("carbon-tax-flat-rate"); // Old behavior: slugified template name
    });

    it("generateScenarioSuggestion still works with updated signature", () => {
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
  });

  describe("validation compliance", () => {
    it("all suggestions pass validatePortfolioName regex", () => {
      const testCases = [
        { composition: makeComposition(["carbon-tax-flat"]), desc: "single policy" },
        { composition: makeComposition(["carbon-tax-flat", "carbon-tax-progressive"]), desc: "same category" },
        { composition: makeComposition(["carbon-tax-flat", "subsidy-energy"]), desc: "mixed category" },
        { composition: makeFromScratchComposition("tax", "income"), desc: "from-scratch" },
        { composition: [], desc: "empty" },
      ];

      for (const { composition, desc } of testCases) {
        const suggestion = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
        const validationError = validatePortfolioName(suggestion);
        expect(validationError, `Suggestion "${suggestion}" (${desc}) should pass validation`).toBeNull();
      }
    });

    it("all suggestions are <= 64 characters", () => {
      const composition = makeComposition(["carbon-tax-flat", "carbon-tax-progressive", "subsidy-energy"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result.length).toBeLessThanOrEqual(64);
    });

    it("all suggestions are lowercase", () => {
      const composition = makeComposition(["carbon-tax-flat"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toBe(result.toLowerCase());
    });

    it("all suggestions contain only alphanumeric and hyphens", () => {
      const composition = makeComposition(["carbon-tax-flat", "subsidy-energy"]);
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories);
      expect(result).toMatch(/^[a-z0-9-]+$/);
    });
  });

  describe("Story 27.9: parameter-based enrichment", () => {
    // Mock parameter schemas for testing
    const mockParameterSchemas: Record<string, ReturnType<typeof import("@/data/mock-data").Parameter>[]> = {
      "carbon-tax-flat": [
        { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Rates", type: "slider" },
        { id: "exemption_threshold", label: "Exemption Threshold", value: 15000, baseline: 10000, unit: "€", group: "Exemptions", type: "number" },
      ],
      "subsidy-energy": [
        { id: "subsidy_rate", label: "Subsidy Rate", value: 0.2, baseline: 0.15, unit: "%", group: "Rates", type: "slider" },
      ],
      "feebate-vehicle": [
        { id: "budget", label: "Program Budget", value: 500000, baseline: 1000000, unit: "€", group: "Funding", type: "number" },
      ],
    };

    it("includes rate parameter in name for single policy", () => {
      const composition: CompositionEntry[] = [
        { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: { tax_rate: 44 }, rateSchedule: {} },
      ];
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories, mockParameterSchemas);
      expect(result).toBe("tax-carbon-emissions-44eur");
    });

    it("includes threshold parameter in name for single policy", () => {
      const composition: CompositionEntry[] = [
        { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: { exemption_threshold: 15000 }, rateSchedule: {} },
      ];
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories, mockParameterSchemas);
      expect(result).toBe("tax-carbon-emissions-15000eur");
    });

    it("includes percentage unit as 'pct' for rate parameters", () => {
      const composition: CompositionEntry[] = [
        { templateId: "subsidy-energy", name: "Energy Subsidy", parameters: { subsidy_rate: 0.2 }, rateSchedule: {} },
      ];
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories, mockParameterSchemas);
      expect(result).toBe("subsidy-energy-consumption-20pct");
    });

    it("skips enrichment if adding parameter would exceed 48 chars", () => {
      const composition: CompositionEntry[] = [
        { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: { exemption_threshold: 15000 }, rateSchedule: {} },
      ];
      // Create a very long category label
      const longCategories: Category[] = [
        { id: "long", label: "Very Long Category Name That Would Exceed Limit", columns: [], compatible_types: [], formula_explanation: "", description: "" },
      ];
      const templatesWithLongCategory: Template[] = [
        { ...mockTemplatesWithCategories[0]!, category_id: "long" },
      ];
      const longSchemas: Record<string, ReturnType<typeof import("@/data/mock-data").Parameter>[]> = {
        "carbon-tax-flat": [
          { id: "exemption_threshold", label: "Exemption", value: 15000, baseline: 10000, unit: "€", group: "Exemptions", type: "number" },
        ],
      };
      const result = generatePortfolioSuggestion(templatesWithLongCategory, composition, longCategories, longSchemas);
      // Base name is already > 48 chars, so enrichment is skipped
      expect(result).toBe("tax-very-long-category-name-that-would-exceed-limit");
    });

    it("returns null when no parameters configured", () => {
      const composition: CompositionEntry[] = [
        { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: {}, rateSchedule: {} },
      ];
      const result = extractPrimaryParameterValue(composition[0]!, mockParameterSchemas);
      expect(result).toBeNull();
    });

    it("returns null when parameter schemas not available", () => {
      const composition: CompositionEntry[] = [
        { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: { tax_rate: 44 }, rateSchedule: {} },
      ];
      const result = extractPrimaryParameterValue(composition[0]!, null);
      expect(result).toBeNull();
    });

    it("formats percentage unit correctly (0.2 → '20pct')", () => {
      const result = formatParameterForName(0.2, "%");
      expect(result).toBe("20pct");
    });

    it("formats currency unit correctly (44 → '44eur')", () => {
      const result = formatParameterForName(44, "€/tonne");
      expect(result).toBe("44eur");
    });

    it("handles zero values", () => {
      const result = formatParameterForName(0, "%");
      expect(result).toBe("0pct");
    });

    it("parameter enrichment passes validation", () => {
      const composition: CompositionEntry[] = [
        { templateId: "carbon-tax-flat", name: "Carbon Tax", parameters: { tax_rate: 44 }, rateSchedule: {} },
      ];
      const result = generatePortfolioSuggestion(mockTemplatesWithCategories, composition, mockCategories, mockParameterSchemas);
      const validationError = validatePortfolioName(result);
      expect(validationError).toBeNull();
    });
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
