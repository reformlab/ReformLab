// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Policy type normalization utilities (Story 27.11, Task 1).
 *
 * Handles three formats in the codebase:
 * - Kebab-case (Template.type): "carbon-tax" → "carbon_tax"
 * - Snake_case (PortfolioPolicyItem.policy_type): "carbon_tax" → "carbon_tax" (no-op)
 * - Lowercase fundamental types (CreateBlankPolicyRequest): "tax" → "tax" (no-op)
 *
 * The canonical format is snake_case (backend API format).
 */

/**
 * Normalize a policy type to the canonical snake_case format used by the backend API.
 *
 * @example normalizePolicyType("carbon-tax") // "carbon_tax"
 * @example normalizePolicyType("carbon_tax") // "carbon_tax"
 * @example normalizePolicyType("tax") // "tax"
 * @example normalizePolicyType(null) // ""
 */
export function normalizePolicyType(type: string | null | undefined): string {
  if (!type) return "";
  // Convert kebab-case to snake_case, leave other formats unchanged
  return type.replace(/-/g, "_");
}
