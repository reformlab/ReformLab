/** Template listing API functions. */

import { apiFetch } from "./client";
import type { TemplateDetailResponse, TemplateListItem } from "./types";

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
