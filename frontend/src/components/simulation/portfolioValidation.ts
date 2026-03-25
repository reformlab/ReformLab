// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * portfolioValidation — shared portfolio name validation utilities.
 *
 * Extracted from PortfolioDesignerScreen (Story 20.3, Task 5.2).
 * Used by PoliciesStageScreen save/clone dialogs.
 */

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
