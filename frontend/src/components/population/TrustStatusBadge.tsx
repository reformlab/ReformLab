// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * TrustStatusBadge — displays trust status with color-coded badge.
 *
 * Story 21.2 / AC8: Display trust status using canonical evidence field.
 * Story 21.4: Extracted to shared component for reuse across population screens.
 */

import { Badge } from "@/components/ui/badge";
import type { PopulationLibraryItem } from "@/api/types";

export interface TrustStatusBadgeProps {
  trustStatus: PopulationLibraryItem["trust_status"];
}

export function TrustStatusBadge({ trustStatus }: TrustStatusBadgeProps) {
  switch (trustStatus) {
    case "production-safe":
      return <Badge className="bg-green-100 text-green-800 text-xs">Production-Safe</Badge>;
    case "exploratory":
      return <Badge className="bg-yellow-100 text-yellow-800 text-xs">Exploratory</Badge>;
    case "demo-only":
      return <Badge className="bg-gray-100 text-gray-800 text-xs">Demo Only</Badge>;
    case "validation-pending":
      return <Badge className="bg-orange-100 text-orange-800 text-xs">Validation Pending</Badge>;
    case "not-for-public-inference":
      return <Badge className="bg-red-100 text-red-800 text-xs">Internal Use Only</Badge>;
    default:
      return <Badge variant="outline" className="text-xs">{trustStatus}</Badge>;
  }
}
