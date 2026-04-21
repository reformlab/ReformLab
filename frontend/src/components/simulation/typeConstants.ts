// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Shared type label and color constants for policy type badges.
 *
 * Story 25.3: Extracted from PortfolioTemplateBrowser to share with CreateFromScratchDialog.
 */

/** Human-readable labels for policy types. */
export const TYPE_LABELS: Record<string, string> = {
  // Legacy policy types
  "carbon-tax": "Carbon Tax",
  "carbon_tax": "Carbon Tax",
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  // Story 24.4: Surfaced policy packs
  "vehicle_malus": "Vehicle Malus",
  "energy_poverty_aid": "Energy Poverty Aid",
  // Story 25.3: From-scratch fundamental types
  "tax": "Tax",
  // Note: "subsidy" is already defined above in legacy types
  "transfer": "Transfer",
};

/** Tailwind CSS color classes for policy type badges. */
export const TYPE_COLORS: Record<string, string> = {
  // Legacy policy types
  "carbon-tax": "bg-amber-100 text-amber-800",
  "carbon_tax": "bg-amber-100 text-amber-800",
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
  // Story 24.4: Surfaced policy packs
  "vehicle_malus": "bg-rose-100 text-rose-800",
  "energy_poverty_aid": "bg-cyan-100 text-cyan-800",
  // Story 25.3: From-scratch fundamental types
  "tax": "bg-amber-100 text-amber-800",
  // Note: "subsidy" is already defined above in legacy types
  "transfer": "bg-blue-100 text-blue-800",
};
