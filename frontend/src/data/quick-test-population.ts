// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Quick Test Population — fast demo population for smoke tests.
 *
 * This is a small demo population (100 households) optimized for fast walkthroughs
 * and smoke testing. It is NOT for substantive analysis — only for demos and testing.
 *
 * Story 22.4 — AC-6, AC-7, AC-8.
 */

import type { PopulationLibraryItem } from "@/api/types";

// ============================================================================
// Constants
// ============================================================================

export const QUICK_TEST_POPULATION_ID = "quick-test-population";

// ============================================================================
// Quick Test Population definition
// ============================================================================

/**
 * Quick Test Population data.
 *
 * WARNING: This is NOT for substantive analysis. Use only for:
 * - Fast demos and walkthroughs
 * - Smoke testing the UI
 * - Development testing
 *
 * For real analysis, use production-grade populations like France Synthetic 2024.
 */
export const QUICK_TEST_POPULATION: PopulationLibraryItem = {
  id: QUICK_TEST_POPULATION_ID,
  name: "Quick Test Population",
  households: 100, // Intentionally small for fast runs
  source: "Built-in demo data",
  year: 2026, // Current year
  origin: "built-in",
  canonical_origin: "synthetic-public",
  access_mode: "bundled",
  trust_status: "demo-only",
  is_synthetic: true,
  column_count: 8,
  created_date: new Date().toISOString(),
};

// ============================================================================
// Accessor
// ============================================================================

/**
 * Get the Quick Test Population definition.
 *
 * @returns The Quick Test Population data.
 */
export function getQuickTestPopulation(): PopulationLibraryItem {
  return QUICK_TEST_POPULATION;
}
