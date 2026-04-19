// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Template listing API functions. */

import { apiFetch } from "./client";
import type {
  BlankPolicyResponse,
  CreateBlankPolicyRequest,
  CreateCustomTemplateRequest,
  CustomTemplateResponse,
  TemplateDetailResponse,
  TemplateListItem,
} from "./types";

/** List available policy templates. */
export async function listTemplates(): Promise<TemplateListItem[]> {
  const result = await apiFetch<{ templates: TemplateListItem[] }>(
    "/api/templates",
  );
  return result.templates;
}

/** Get a template with full parameter details and defaults. */
export async function getTemplate(
  name: string,
): Promise<TemplateDetailResponse> {
  return apiFetch<TemplateDetailResponse>(
    `/api/templates/${encodeURIComponent(name)}`,
  );
}

/** Create a custom template. */
export async function createCustomTemplate(
  request: CreateCustomTemplateRequest,
): Promise<CustomTemplateResponse> {
  return apiFetch<CustomTemplateResponse>("/api/templates/custom", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/** Delete a custom template. */
export async function deleteCustomTemplate(name: string): Promise<void> {
  await apiFetch<void>(`/api/templates/custom/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

/** Create a blank policy from scratch — Story 25.3. */
export async function createBlankPolicy(
  request: CreateBlankPolicyRequest,
): Promise<BlankPolicyResponse> {
  // Normalize policy_type to lowercase for API call
  const normalizedRequest: CreateBlankPolicyRequest = {
    policy_type: request.policy_type.toLowerCase() as "tax" | "subsidy" | "transfer",
    category_id: request.category_id,
  };
  return apiFetch<BlankPolicyResponse>("/api/templates/from-scratch", {
    method: "POST",
    body: JSON.stringify(normalizedRequest),
  });
}
