// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Population dataset listing API functions. */

import { apiFetch } from "./client";
import type { PopulationItem } from "./types";

/** List available population datasets. */
export async function listPopulations(): Promise<PopulationItem[]> {
  const result = await apiFetch<{ populations: PopulationItem[] }>(
    "/api/populations",
  );
  return result.populations;
}
