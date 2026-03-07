/** Portfolio CRUD API functions — Story 17.2. */

import { apiFetch } from "./client";
import type {
  ClonePortfolioRequest,
  CreatePortfolioRequest,
  PortfolioDetailResponse,
  PortfolioListItem,
  UpdatePortfolioRequest,
  ValidatePortfolioRequest,
  ValidatePortfolioResponse,
} from "./types";

/** List all saved portfolios. */
export async function listPortfolios(): Promise<PortfolioListItem[]> {
  return apiFetch<PortfolioListItem[]>("/api/portfolios");
}

/** Get portfolio detail including all policies. */
export async function getPortfolio(name: string): Promise<PortfolioDetailResponse> {
  return apiFetch<PortfolioDetailResponse>(`/api/portfolios/${encodeURIComponent(name)}`);
}

/** Create a new portfolio. Returns version_id. */
export async function createPortfolio(request: CreatePortfolioRequest): Promise<string> {
  const result = await apiFetch<{ version_id: string }>("/api/portfolios", {
    method: "POST",
    body: JSON.stringify(request),
  });
  return result.version_id;
}

/** Update an existing portfolio. */
export async function updatePortfolio(
  name: string,
  request: UpdatePortfolioRequest,
): Promise<PortfolioDetailResponse> {
  return apiFetch<PortfolioDetailResponse>(`/api/portfolios/${encodeURIComponent(name)}`, {
    method: "PUT",
    body: JSON.stringify(request),
  });
}

/** Delete a portfolio by name. */
export async function deletePortfolio(name: string): Promise<void> {
  await apiFetch<void>(`/api/portfolios/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

/** Clone a portfolio with a new name. */
export async function clonePortfolio(
  name: string,
  request: ClonePortfolioRequest,
): Promise<PortfolioDetailResponse> {
  return apiFetch<PortfolioDetailResponse>(
    `/api/portfolios/${encodeURIComponent(name)}/clone`,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

/** Validate a draft portfolio for conflicts (no save). */
export async function validatePortfolio(
  request: ValidatePortfolioRequest,
): Promise<ValidatePortfolioResponse> {
  return apiFetch<ValidatePortfolioResponse>("/api/portfolios/validate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
