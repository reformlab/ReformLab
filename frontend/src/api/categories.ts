// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Categories API — Story 25.1, Task 2.5. */

import { apiFetch } from "./client";
import type { Category } from "./types";

/** List all policy categories with metadata — Story 25.1, AC-1. */
export async function listCategories(): Promise<Category[]> {
  const response = await apiFetch<Category[]>("/api/categories");
  return response;
}
