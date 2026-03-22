/** Template listing API functions. */

import { apiFetch } from "./client";
import type {
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
