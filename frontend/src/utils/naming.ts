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
// generatePortfolioSuggestion()
// ============================================================================

/**
 * Generate a deterministic portfolio name suggestion from the current composition.
 *
 * Naming algorithm:
 * - 0 policies: "untitled-portfolio"
 * - 1 policy: slugified template name
 * - 2 policies: "slug1-plus-slug2" (MUST pass validatePortfolioName)
 * - 3+ policies: "first-slug-plus-(N-1)-more" (MUST pass validatePortfolioName)
 *
 * All suggestions pass validatePortfolioName validation (lowercase, alphanumeric,
 * hyphens only, max 64 chars).
 *
 * @param templates - All available templates (for looking up names by templateId)
 * @param composition - Current portfolio composition
 * @returns A validation-compatible portfolio name suggestion
 */
export function generatePortfolioSuggestion(
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
    return `${slug1}-plus-${slug2}`;
  }

  // 3+ policies: use "first-slug-plus-(N-1)-more" pattern
  const firstSlug = slugify(composition[0]!.name);
  const remainingCount = composition.length - 1;
  return `${firstSlug}-plus-${remainingCount}-more`;
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

  // Remove "France " prefix
  if (name.startsWith("France ")) {
    name = name.slice(7);
  }

  // Add "FR " prefix if not already prefixed with "FR " or "EU "
  if (!name.startsWith("FR ") && !name.startsWith("EU ")) {
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
