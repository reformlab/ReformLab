// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * SyntheticBadge — indicates whether a population is synthetic or observed.
 *
 * Story 21.4: Visual indicator for synthetic vs observed populations.
 * Used in comparison view to help users understand which populations they're comparing.
 */

import { Badge } from "@/components/ui/badge";
import type { PopulationLibraryItem } from "@/api/types";

export interface SyntheticBadgeProps {
  /** The population origin to classify */
  origin: PopulationLibraryItem["origin"];
  /** Whether the population is synthetic (computed from is_synthetic field) */
  isSynthetic?: boolean;
}

export function SyntheticBadge({ origin, isSynthetic }: SyntheticBadgeProps) {
  // Determine if synthetic based on origin or explicit flag
  const synthetic = isSynthetic ?? origin === "synthetic-public";

  if (synthetic) {
    return (
      <Badge className="bg-purple-100 text-purple-800 text-xs" title="Generated/synthetic data">
        Synthetic
      </Badge>
    );
  }

  // Observed data (open-official, open-registered, etc.)
  if (origin === "open-official" || origin === "open-registered") {
    return (
      <Badge className="bg-blue-100 text-blue-800 text-xs" title="Real-world observed data">
        Observed
      </Badge>
    );
  }

  // Built-in or uploaded data - no badge (ambiguous)
  return null;
}
