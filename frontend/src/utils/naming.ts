// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * naming.ts — Deterministic naming utilities for portfolios and scenarios.
 *
 * Story 22.3 — AC-2 through AC-8:
 * - Portfolio name suggestions that pass validatePortfolioName validation
 * - Scenario name suggestions based on portfolio and population context
 * - Population short names with consistent "FR " prefix convention
 *
 * All functions are pure and deterministic — no side effects.
 */

import type { Template } from "@/data/mock-data";
import type { Population } from "@/data/mock-data";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import type { Category } from "@/api/types";
import type { Parameter } from "@/data/mock-data";

// ============================================================================
// Type Constants
// ============================================================================

/**
 * Story 27.9: Semantic policy types.
 */
const SEMANTIC_TYPES = ["tax", "subsidy", "transfer"] as const;

/**
 * Story 27.9: Policy type slug mapping.
 * Maps template.type hyphenated forms to semantic types.
 * Extracts first part before hyphen for unmapped types.
 */
const TYPE_SLUGS: Record<string, string> = {
  "carbon-tax": "tax",
  "vehicle-tax": "tax",
  "income-tax": "tax",
  "vehicle-subsidy": "subsidy",
  "energy-subsidy": "subsidy",
  "housing-subsidy": "subsidy",
  "housing-transfer": "transfer",
  "feebate": "subsidy",
};

/**
 * Extract semantic policy type from template type string.
 * @param templateType - Template type (e.g., "carbon-tax", "vehicle-subsidy", "tax")
 * @returns Semantic type ("tax" | "subsidy" | "transfer" | "policy")
 */
function extractSemanticType(templateType: string): string {
  // Direct semantic type check (e.g., "tax", "subsidy", "transfer")
  if (SEMANTIC_TYPES.includes(templateType as "tax" | "subsidy" | "transfer")) {
    return templateType;
  }

  // Direct mapping lookup
  if (templateType in TYPE_SLUGS) {
    return TYPE_SLUGS[templateType]!;
  }

  // Extract first part before hyphen (e.g., "consumption-tax" → "consumption")
  const hyphenIndex = templateType.indexOf("-");
  if (hyphenIndex !== -1) {
    const firstPart = templateType.slice(0, hyphenIndex);
    // Only use first part if it's a recognized semantic type
    if (SEMANTIC_TYPES.includes(firstPart as "tax" | "subsidy" | "transfer")) {
      return firstPart;
    }
  }

  // Fallback for unrecognized types
  return "policy";
}

// ============================================================================
// slugify()
// ============================================================================

/**
 * Convert a user-friendly name to a kebab-case slug suitable for portfolio names.
 *
 * Rules:
 * - Convert to lowercase
 * - Replace spaces, em-dashes, and special characters with hyphens
 * - Remove characters that are not alphanumeric or hyphens
 * - Collapse multiple consecutive hyphens to single hyphen
 * - Trim leading/trailing hyphens
 * - Truncate to 64 chars if needed
 *
 * Examples:
 * - "Carbon Tax — Flat Rate" → "carbon-tax-flat-rate"
 * - "Subsidy 2024" → "subsidy-2024"
 * - "Éco—Taxe" → "eco-taxe"
 *
 * @param name - The user-friendly name to slugify
 * @returns A slugified string suitable for portfolio names
 */
export function slugify(name: string): string {
  // Early return for empty or whitespace-only input
  if (!name || !name.trim()) {
    return "";
  }

  return (
    name
      // Normalize unicode (convert accented chars to base + combining chars)
      .normalize("NFD")
      // Remove combining diacritical marks
      .replace(/[\u0300-\u036f]/g, "")
      // Convert to lowercase
      .toLowerCase()
      // Replace spaces, em-dashes, en-dashes, and special chars with hyphens
      .replace(/[\s\u2013\u2014—–]/g, "-")
      // Remove characters that are not alphanumeric or hyphens
      .replace(/[^a-z0-9-]/g, "")
      // Collapse multiple consecutive hyphens to single hyphen
      .replace(/-+/g, "-")
      // Trim leading/trailing hyphens
      .replace(/^-+|-+$/g, "")
      // Truncate to 64 chars (portfolio name constraint)
      .slice(0, 64)
  );
}

// ============================================================================
// truncateSlug()
// ============================================================================

/**
 * Truncate a slug to 64 chars without leaving a trailing hyphen.
 */
function truncateSlug(slug: string): string {
  if (slug.length <= 64) return slug;
  return slug.slice(0, 64).replace(/-+$/, "");
}

// ============================================================================
// Story 27.9: Type-Category Helper Functions
// ============================================================================

/**
 * Result type for extractTypeAndCategory helper.
 */
interface TypeAndCategory {
  policyType: string;
  categoryId?: string;
  categoryLabel: string;
}

/**
 * Extract policy type and category from a composition entry.
 *
 * Story 27.9 / Task 1.2
 *
 * For from-scratch policies: uses entry.policy_type and entry.category_id
 * For template policies: uses template.type and template.category_id
 *
 * @param entry - Composition entry to extract from
 * @param templates - All available templates for lookup
 * @param categories - All available categories for label lookup
 * @returns Policy type and category info
 */
export function extractTypeAndCategory(
  entry: CompositionEntry,
  templates: readonly Template[],
  categories: Category[] | null,
): TypeAndCategory {
  let policyType: string;
  let categoryId: string | undefined;
  let categoryLabel = "other";

  if (entry.templateId === "" || entry.policy_type) {
    // From-scratch policy: use entry fields directly
    policyType = entry.policy_type ?? "policy";
    categoryId = entry.category_id;
  } else {
    // Template policy: look up from template
    const template = templates.find((t) => t.id === entry.templateId);
    if (template) {
      policyType = extractSemanticType(template.type);
      categoryId = template.category_id;
    } else {
      policyType = "policy";
    }
  }

  // Look up category label
  if (categories && categoryId) {
    const category = categories.find((c) => c.id === categoryId);
    if (category) {
      categoryLabel = category.label;
    } else {
      // Category ID not found in categories list
      categoryId = undefined;
    }
  } else if (categoryId && !categories) {
    // categories is null but categoryId exists: clear it
    categoryId = undefined;
  }

  return { policyType, categoryId, categoryLabel };
}

/**
 * Generate slug from policy type and category label.
 *
 * Story 27.9 / Task 1.3
 *
 * @param policyType - Semantic policy type (tax, subsidy, transfer, policy)
 * @param categoryLabel - Human-readable category label
 * @returns Slugified "{type}-{category}" string
 */
export function slugifyTypeAndCategory(policyType: string, categoryLabel: string): string {
  const categorySlug = slugify(categoryLabel);
  return `${policyType}-${categorySlug}`;
}

/**
 * Find the dominant (most common) category in a composition.
 *
 * Story 27.9 / Task 1.4
 *
 * Returns the category with the most policies. On tie, returns the first
 * policy's category.
 *
 * @param composition - Current portfolio composition
 * @param templates - All available templates for lookup
 * @param categories - All available categories for label lookup
 * @returns Dominant category info
 */
export function getDominantCategory(
  composition: readonly CompositionEntry[],
  templates: readonly Template[],
  categories: Category[] | null,
): TypeAndCategory {
  if (composition.length === 0) {
    return { policyType: "policy", categoryLabel: "other" };
  }

  // Count policies by category
  const categoryCounts = new Map<string, number>();

  for (const entry of composition) {
    const { categoryId } = extractTypeAndCategory(entry, templates, categories);
    if (categoryId) {
      categoryCounts.set(categoryId, (categoryCounts.get(categoryId) ?? 0) + 1);
    }
  }

  if (categoryCounts.size === 0) {
    return { policyType: "policy", categoryLabel: "other" };
  }

  // Find category with max count
  let dominantCategoryId = "";
  let maxCount = 0;

  for (const [categoryId, count] of categoryCounts) {
    if (count > maxCount) {
      maxCount = count;
      dominantCategoryId = categoryId;
    }
  }

  // Look up category label
  let categoryLabel = "other";
  if (categories && dominantCategoryId) {
    const category = categories.find((c) => c.id === dominantCategoryId);
    if (category) {
      categoryLabel = category.label;
    }
  }

  return { policyType: "policy", categoryId: dominantCategoryId, categoryLabel };
}

/**
 * Story 27.9: Parameter enrichment result type.
 */
interface ParameterValue {
  paramId: string;
  value: number;
  unit: string;
  formatted: string;
}

/**
 * Story 27.9 / Task 2.1: Extract primary parameter value for name enrichment.
 *
 * Priority order for "headline" parameter:
 * 1. Parameters containing "rate" (e.g., tax_rate, subsidy_rate)
 * 2. Parameters containing "threshold" (e.g., exemption_threshold)
 * 3. Parameters containing "budget" (e.g., program_budget)
 * 4. Parameters containing "exemption" (fallback)
 *
 * Resolution order:
 * 1. Configured value (entry.parameters[paramId]) - highest priority
 * 2. Schema baseline (template default)
 * 3. null (no value available)
 *
 * @param entry - Composition entry to extract from
 * @param schemas - Parameter schemas per template (templateId → Parameter[])
 * @returns Parameter value info or null if none found
 */
export function extractPrimaryParameterValue(
  entry: CompositionEntry,
  schemas: Record<string, Parameter[]> | null,
): ParameterValue | null {
  if (!schemas) {
    return null;
  }

  const templateParams = schemas[entry.templateId];
  if (!templateParams) {
    return null;
  }

  // Priority order for parameter ID
  const priorityPatterns = [/rate/, /threshold/, /budget/, /exemption/];

  for (const pattern of priorityPatterns) {
    // Find first parameter matching the pattern
    const param = templateParams.find((p) => pattern.test(p.id));
    if (!param) {
      continue;
    }

    // Only use explicitly configured value (key exists in entry.parameters)
    if (param.id in entry.parameters) {
      const value = entry.parameters[param.id];
      const formatted = formatParameterForName(value, param.unit);
      return { paramId: param.id, value, unit: param.unit, formatted };
    }

    // Parameter found but not configured: try next priority
  }

  return null;
}

/**
 * Story 27.9 / Task 2.2: Format parameter value for inclusion in slug.
 *
 * Formatting rules:
 * - Unit "%" → Math.round(value * 100) + "pct" (e.g., 0.2 → "20pct")
 * - Currency-like units (€/tonne, €/vehicle) → strip symbol, append "eur"
 * - Other units → slugify unit name
 *
 * @param value - Parameter value to format
 * @param unit - Unit string (e.g., "%", "€/tonne", "km")
 * @returns Formatted string suitable for slug inclusion
 */
export function formatParameterForName(value: number, unit: string): string {
  if (unit === "%") {
    // Percentage: convert decimal to integer (e.g., 0.2 → 20)
    return `${Math.round(value * 100)}pct`;
  }

  if (unit.includes("€") || unit.includes("EUR")) {
    // Currency: strip symbol, append "eur"
    return `${value}eur`;
  }

  // Other units: slugify the unit name
  const slugifiedUnit = slugify(unit);
  if (slugifiedUnit) {
    return `${value}${slugifiedUnit}`;
  }

  return `${value}`;
}

// ============================================================================
// generatePortfolioSuggestion()
// ============================================================================

/**
 * Generate a deterministic portfolio name suggestion from the current composition.
 *
 * Story 27.9 / Task 1: Enhanced type-category naming algorithm.
 * Story 27.9 / Task 2: Parameter-based enrichment for single policies.
 *
 * New naming algorithm (when categories provided):
 * - 0 policies: "untitled-portfolio"
 * - 1 policy: "{type}-{category}" (e.g., "tax-carbon-emissions")
 *   - From-scratch: reuses existing "{Type} — {Category}" name pattern
 *   - With parameter value (if ≤ 48 chars): "{type}-{category}-{value}" (e.g., "tax-carbon-emissions-44eur")
 * - 2+ same-category: "{category}-policies" (e.g., "carbon-emissions-policies")
 * - 2+ mixed categories: "{dominant-category}-plus-{non-dominant-count}-more" (e.g., "carbon-emissions-plus-1-more")
 *
 * Legacy algorithm (when categories not provided):
 * - 1 policy: slugified template name
 * - 2 policies: "slug1-plus-slug2"
 * - 3+ policies: "first-slug-plus-(N-1)-more"
 *
 * All suggestions pass validatePortfolioName validation (lowercase, alphanumeric,
 * hyphens only, max 64 chars).
 *
 * @param templates - All available templates (for looking up names by templateId)
 * @param composition - Current portfolio composition
 * @param categories - Optional categories for type-category naming (Story 27.9)
 * @param parameterSchemas - Optional parameter schemas for enrichment (Story 27.9)
 * @returns A validation-compatible portfolio name suggestion
 */
export function generatePortfolioSuggestion(
  templates: readonly Template[],
  composition: readonly CompositionEntry[],
  categories?: Category[] | null,
  parameterSchemas?: Record<string, Parameter[]> | null,
): string {
  // Empty composition: always "untitled-portfolio"
  if (composition.length === 0) {
    return "untitled-portfolio";
  }

  // Story 27.9: If categories not provided, fall back to legacy behavior
  if (!categories || categories.length === 0) {
    return generateLegacySuggestion(templates, composition);
  }

  // Single policy: use type-category pattern
  if (composition.length === 1) {
    const entry = composition[0]!;
    const { policyType, categoryLabel } = extractTypeAndCategory(entry, templates, categories);

    // For from-scratch policies, if entry has category_id, use category label
    if (entry.templateId === "" && entry.category_id) {
      return slugifyTypeAndCategory(policyType, categoryLabel);
    }

    // For template policies, always use type-category
    if (entry.templateId !== "") {
      const template = templates.find((t) => t.id === entry.templateId);
      if (!template) {
        // Template not found: fall back to legacy behavior
        return slugify(entry.name);
      }

      // Story 27.9 / Task 2: Parameter-based enrichment
      const baseName = slugifyTypeAndCategory(policyType, categoryLabel);

      // Only add parameter if total length would be ≤ 48 chars
      const paramValue = extractPrimaryParameterValue(entry, parameterSchemas ?? null);
      if (paramValue && (baseName.length + paramValue.formatted.length + 1) <= 48) {
        return `${baseName}-${paramValue.formatted}`;
      }

      return baseName;
    }

    return slugifyTypeAndCategory(policyType, categoryLabel);
  }

  // Multi-policy: check if all same category or mixed
  const dominantCategory = getDominantCategory(composition, templates, categories);
  const dominantCategorySlug = slugify(dominantCategory.categoryLabel);

  // Count how many policies have the dominant category
  let dominantCount = 0;
  for (const entry of composition) {
    const { categoryId } = extractTypeAndCategory(entry, templates, categories);
    if (categoryId === dominantCategory.categoryId) {
      dominantCount++;
    }
  }

  // All policies same category: "{category}-policies"
  if (dominantCount === composition.length) {
    return truncateSlug(`${dominantCategorySlug}-policies`);
  }

  // Mixed categories: "{dominant-category}-plus-{non-dominant-count}-more"
  const nonDominantCount = composition.length - dominantCount;
  return truncateSlug(`${dominantCategorySlug}-plus-${nonDominantCount}-more`);
}

/**
 * Legacy naming algorithm (pre-Story 27.9).
 * Used when categories not provided.
 */
function generateLegacySuggestion(
  templates: readonly Template[],
  composition: readonly CompositionEntry[],
): string {
  if (composition.length === 0) {
    return "untitled-portfolio";
  }

  if (composition.length === 1) {
    const entry = composition[0]!;
    const template = templates.find((t) => t.id === entry.templateId);
    const name = template?.name ?? entry.name;
    return slugify(name);
  }

  if (composition.length === 2) {
    const slug1 = slugify(composition[0]!.name);
    const slug2 = slugify(composition[1]!.name);
    return truncateSlug(`${slug1}-plus-${slug2}`);
  }

  // 3+ policies: use "first-slug-plus-(N-1)-more" pattern
  const firstSlug = slugify(composition[0]!.name);
  const remainingCount = composition.length - 1;
  return truncateSlug(`${firstSlug}-plus-${remainingCount}-more`);
}

// ============================================================================
// getPopulationShortName()
// ============================================================================

/**
 * Generate a consistent short name for population display in scenario names.
 *
 * Rules:
 * - Remove "France " prefix if present
 * - Add "FR " prefix if not already present (and not "EU ")
 * - Keep year suffix for context
 *
 * Examples:
 * - "France Synthetic 2024" → "FR Synthetic 2024"
 * - "France Household Panel 2023" → "FR Household 2023"
 * - "EU Survey 2025" → "EU Survey 2025" (no change)
 *
 * @param population - The population to get a short name for
 * @returns A consistent short name for display
 */
export function getPopulationShortName(population: Population): string {
  let name = population.name;

  // Remove "France " prefix (case-insensitive)
  if (name.toLowerCase().startsWith("france ")) {
    // Find the actual index of "France " (respecting original case)
    const franceIndex = name.toLowerCase().indexOf("france ");
    name = name.slice(franceIndex + 7);
  }

  // Add "FR " prefix if not already prefixed with FR or EU context.
  if (!name.startsWith("FR ") && !name.startsWith("EU ") && !name.startsWith("EU-")) {
    name = `FR ${name}`;
  }

  return name;
}

// ============================================================================
// generateScenarioSuggestion()
// ============================================================================

/**
 * Generate a deterministic scenario name suggestion from current context.
 *
 * Naming algorithm:
 * - Has portfolio: portfolio.displayName + (population ? " (population.shortName)" : "")
 * - No portfolio: population ? "Untitled (population.shortName)" : "Untitled Scenario"
 *
 * The portfolio.displayName follows this precedence:
 * 1. activeScenario.portfolioName (if set)
 * 2. selectedPortfolioName (if set)
 * 3. Generated from composition (via generatePortfolioSuggestion)
 *
 * @param portfolioName - The portfolio name (from activeScenario.portfolioName or selectedPortfolioName)
 * @param selectedPopulationId - Currently selected population ID
 * @param populations - All available populations
 * @param templates - All available templates (for generating portfolio name from composition)
 * @param composition - Current portfolio composition (for generating portfolio name if needed)
 * @returns A scenario name suggestion
 */
export function generateScenarioSuggestion(
  portfolioName: string | null,
  selectedPopulationId: string,
  populations: readonly Population[],
  templates: readonly Template[],
  composition: readonly CompositionEntry[],
): string {
  const population = populations.find((p) => p.id === selectedPopulationId);
  const populationPart = population ? ` (${getPopulationShortName(population)})` : "";

  if (portfolioName) {
    // Use portfolio display name as base
    return `${portfolioName}${populationPart}`;
  }

  // No portfolio set - generate from composition or use generic name
  if (composition.length > 0) {
    const generatedPortfolioName = generatePortfolioSuggestion(templates, composition);
    return `${generatedPortfolioName}${populationPart}`;
  }

  if (population) {
    return `Untitled${populationPart}`;
  }

  return "Untitled Scenario";
}

// ============================================================================
// Clone naming utilities
// ============================================================================

/**
 * Generate a clone name for a portfolio with collision handling.
 *
 * Pattern: originalName + "-copy"
 * If collision: originalName + "-copy-2", "-copy-3", etc.
 *
 * @param originalName - The original portfolio name
 * @param existingNames - Set of existing portfolio names to check for collisions
 * @returns A unique clone name
 */
export function generatePortfolioCloneName(
  originalName: string,
  existingNames: Set<string>,
): string {
  let cloneName = `${originalName}-copy`;
  let suffix = 1;

  while (existingNames.has(cloneName)) {
    suffix += 1;
    cloneName = `${originalName}-copy-${suffix}`;
  }

  return cloneName;
}

/**
 * Generate a clone name for a scenario with collision handling.
 *
 * Pattern: originalName + " (copy)"
 * If collision: originalName + " (copy 2)", " (copy 3)", etc.
 *
 * @param originalName - The original scenario name
 * @param existingNames - Set of existing scenario names to check for collisions
 * @returns A unique clone name
 */
export function generateScenarioCloneName(
  originalName: string,
  existingNames: Set<string>,
): string {
  let cloneName = `${originalName} (copy)`;
  let suffix = 1;

  while (existingNames.has(cloneName)) {
    suffix += 1;
    cloneName = `${originalName} (copy ${suffix})`;
  }

  return cloneName;
}
