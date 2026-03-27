// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * OriginBadge — displays population origin with color-coded badge.
 *
 * Story 20.4: Display origin (built-in, generated, uploaded) in population library.
 * Story 21.4: Extracted to shared component for reuse across population screens.
 */

import { Badge } from "@/components/ui/badge";
import type { PopulationLibraryItem } from "@/api/types";

export interface OriginBadgeProps {
  origin: PopulationLibraryItem["origin"];
}

export function OriginBadge({ origin }: OriginBadgeProps) {
  const label = origin === "built-in" ? "[Built-in]" : origin === "generated" ? "[Generated]" : "[Uploaded]";
  const variant = origin === "built-in" ? "secondary" : origin === "generated" ? "default" : "outline";
  return <Badge variant={variant} className="text-xs">{label}</Badge>;
}
