// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Status variant helper for Badge components.
 *
 * Story 27.10, AC-8.
 * Consolidates duplicate statusVariant functions from ResultsListPanel,
 * ResultDetailView, and comparison-helpers.
 */

import type { BadgeVariant } from "@/components/ui/badge";

export type StatusVariant = BadgeVariant;

/**
 * Returns the badge variant for a given status string.
 *
 * Consolidated behavior from three files:
 * - ResultsListPanel.tsx: completed→success, failed→destructive, default→warning
 * - ResultDetailView.tsx: completed→success, failed→destructive, default→default
 * - comparison-helpers.ts: completed→success, failed→destructive, default→warning
 *
 * The reconciliation uses "warning" for the default case.
 *
 * @example statusVariant("completed") // "success"
 * @example statusVariant("failed") // "destructive"
 * @example statusVariant("running") // "warning"
 * @example statusVariant("unknown") // "warning"
 */
export function statusVariant(status: string): StatusVariant {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  return "warning";
}
