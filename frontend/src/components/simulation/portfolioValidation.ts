// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * portfolioValidation — shared portfolio name validation utilities.
 *
 * Extracted from PortfolioDesignerScreen (Story 20.3, Task 5.2).
 * Used by PoliciesStageScreen save/clone dialogs.
 *
 * Story 25.6: Added per-policy validation with field-level error messages.
 */

import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";

/** Same regex as backend: lowercase slug, letters/digits/hyphens, max 64 chars. */
export const NAME_RE = /^(?:[a-z0-9]{1,64}|[a-z0-9][a-z0-9-]{0,62}[a-z0-9])$/;

/** Validates a portfolio name. Returns an error message or null if valid. */
export function validatePortfolioName(name: string): string | null {
  if (!name.trim()) return "Portfolio name is required";
  if (!NAME_RE.test(name)) {
    return "Name must be a lowercase slug: letters, digits, hyphens only (max 64 chars)";
  }
  if (name === "validate" || name === "clone") {
    return `'${name}' is a reserved name`;
  }
  return null;
}

// ============================================================================
// Story 25.6: Per-policy validation
// ============================================================================

/**
 * Validation error for a single policy in the composition.
 *
 * Story 25.6 / Task 1: Field-level error messages for policy validation.
 */
export interface PolicyValidationError {
  /** Index of the policy in the composition array. Set by validateComposition(); omitted when validating a single entry. */
  policyIndex?: number;
  /** Display name of the policy */
  policyName: string;
  /** Field names that are missing (e.g., ["policy_type", "category_id"]) */
  missingFields: string[];
  /** Field names that are invalid (e.g., ["rateSchedule (malformed entries)"]) */
  invalidFields: string[];
}

/**
 * Validates a single composition entry for field-level errors.
 *
 * Story 25.6 / Task 1: Checks for:
 * - Missing policy_type (for from-scratch policies only)
 * - Missing category_id (for from-scratch policies only)
 * - Empty parameters object (no parameters set at all)
 * - Invalid rate schedule structure (malformed entries, not emptiness)
 *
 * @param entry - The composition entry to validate
 * @returns A PolicyValidationError if validation fails, null if valid
 */
export function validateCompositionEntry(
  entry: CompositionEntry,
): PolicyValidationError | null {
  const missingFields: string[] = [];
  const invalidFields: string[] = [];

  // Check from-scratch policy fields (only when no templateId)
  if (!entry.templateId) {
    // From-scratch policy must have policy_type
    if (!entry.policy_type) {
      missingFields.push("policy_type");
    }
    // From-scratch policy must have category_id
    if (!entry.category_id) {
      missingFields.push("category_id");
    }
  }

  // Template-based policies inherit their template defaults. Empty parameters
  // only means no overrides; from-scratch policies need explicit parameters.
  if (!entry.templateId && Object.keys(entry.parameters).length === 0) {
    missingFields.push("parameters");
  }

  // Check rate schedule structure (not emptiness—some policies don't require schedules)
  // Only validate if schedule exists and has entries
  if (Object.keys(entry.rateSchedule).length > 0) {
    const YEAR_RE = /^-?\d+$/;
    const hasInvalidEntry = Object.entries(entry.rateSchedule).some(([year, value]) => {
      const yearIsValid = YEAR_RE.test(year);
      const valueIsValid =
        typeof value === "number" ||
        (typeof value === "object" && value !== null && !Array.isArray(value));
      return !yearIsValid || !valueIsValid;
    });
    if (hasInvalidEntry) {
      invalidFields.push("rateSchedule (malformed entries)");
    }
  }
  // Note: Empty rate schedule is NOT invalid—some policies don't use schedules

  if (missingFields.length === 0 && invalidFields.length === 0) {
    return null;
  }

  return {
    policyName: entry.name,
    missingFields,
    invalidFields,
  };
}

/**
 * Validates all composition entries and returns validation errors.
 *
 * Story 25.6 / Task 1: Run validation on all policies in the composition.
 *
 * @param composition - Array of composition entries to validate
 * @returns Array of PolicyValidationError objects (empty if all valid)
 */
export function validateComposition(
  composition: CompositionEntry[],
): PolicyValidationError[] {
  const errors: PolicyValidationError[] = [];

  for (let i = 0; i < composition.length; i++) {
    const entry = composition[i];
    const error = validateCompositionEntry(entry);
    if (error) {
      errors.push({ ...error, policyIndex: i });
    }
  }

  return errors;
}
