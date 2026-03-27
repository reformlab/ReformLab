// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * SyntheticBadge — indicates whether a population is synthetic or observed.
 *
 * Story 21.4: Visual indicator for synthetic vs observed populations.
 * Used in comparison view to help users understand which populations they're comparing.
 */

import { Badge } from "@/components/ui/badge";

export interface SyntheticBadgeProps {
  /** Whether the population is synthetic (computed from is_synthetic field or canonical_origin) */
  isSynthetic?: boolean;
  /** The canonical origin for classification (optional, for explicit classification) */
  canonicalOrigin?: "open-official" | "synthetic-public" | "open-registered";
}

export function SyntheticBadge({ isSynthetic, canonicalOrigin }: SyntheticBadgeProps) {
  // Determine if synthetic based on explicit flag first, then canonical origin
  const synthetic = isSynthetic ?? canonicalOrigin === "synthetic-public";

  if (synthetic) {
    return (
      <Badge className="bg-purple-100 text-purple-800 text-xs" title="Generated/synthetic data">
        Synthetic
      </Badge>
    );
  }

  // Observed data (open-official, open-registered)
  if (canonicalOrigin === "open-official" || canonicalOrigin === "open-registered") {
    return (
      <Badge className="bg-blue-100 text-blue-800 text-xs" title="Real-world observed data">
        Observed
      </Badge>
    );
  }

  // Unknown origin - no badge
  return null;
}
