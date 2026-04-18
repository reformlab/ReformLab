// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Typed fetch wrapper with error handling and auth token injection. */

import type { ErrorResponse } from "./types";

const AUTH_TOKEN_KEY = "reformlab-auth-token";

/** Callback invoked on any 401 — set by AppContext to trigger re-auth UI. */
let _onAuthInvalid: (() => void) | null = null;

/** Register a global callback for auth invalidation (called once from AppContext). */
export function setOnAuthInvalid(cb: (() => void) | null): void {
  _onAuthInvalid = cb;
}

/** Retrieve the stored auth token from sessionStorage. */
export function getAuthToken(): string | null {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
}

/** Store (or clear) the auth token in sessionStorage. */
export function setAuthToken(token: string | null): void {
  if (token) {
    sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

/** Error thrown when the API returns a structured error response. */
export class ApiError extends Error {
  readonly what: string;
  readonly why: string;
  readonly fix: string;
  readonly statusCode: number;

  constructor(response: ErrorResponse) {
    super(`${response.what} — ${response.why}`);
    this.name = "ApiError";
    this.what = response.what;
    this.why = response.why;
    this.fix = response.fix;
    this.statusCode = response.status_code;
  }
}

/** Error thrown on 401 — triggers password prompt. */
export class AuthError extends Error {
  constructor() {
    super("Authentication required");
    this.name = "AuthError";
  }
}

/**
 * Make an authenticated API request.
 * All paths are relative (e.g. "/api/scenarios") — Vite proxy handles routing.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...options, headers });

  if (response.status === 401) {
    setAuthToken(null);
    _onAuthInvalid?.();
    throw new AuthError();
  }

  if (!response.ok) {
    let rawBody: Record<string, unknown> | undefined;
    try {
      rawBody = (await response.json()) as Record<string, unknown>;
    } catch {
      // Response body wasn't valid JSON
    }

    // Top-level what/why/fix — from custom exception handlers (ConfigurationError etc.)
    const topLevel = rawBody as Partial<ErrorResponse> | undefined;
    if (topLevel?.what) {
      throw new ApiError(topLevel as ErrorResponse);
    }

    // Nested under "detail" — from FastAPI HTTPException(detail={...})
    const detail = rawBody?.detail;
    if (detail !== null && typeof detail === "object" && !Array.isArray(detail) && "what" in detail) {
      throw new ApiError({
        ...(detail as Partial<ErrorResponse>),
        status_code: response.status,
      } as ErrorResponse);
    }

    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/**
 * Make an authenticated API request that returns a file download.
 * Returns a Blob for the caller to trigger a browser download.
 */
export async function apiFetchBlob(
  path: string,
  options: RequestInit = {},
): Promise<{ blob: Blob; filename: string }> {
  const token = getAuthToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...options, headers });

  if (response.status === 401) {
    setAuthToken(null);
    _onAuthInvalid?.();
    throw new AuthError();
  }

  if (!response.ok) {
    let rawBody: Record<string, unknown> | undefined;
    try {
      rawBody = (await response.json()) as Record<string, unknown>;
    } catch {
      // Response body wasn't valid JSON
    }

    const topLevel = rawBody as Partial<ErrorResponse> | undefined;
    if (topLevel?.what) {
      throw new ApiError(topLevel as ErrorResponse);
    }

    const detail = rawBody?.detail;
    if (detail !== null && typeof detail === "object" && !Array.isArray(detail) && "what" in detail) {
      throw new ApiError({
        ...(detail as Partial<ErrorResponse>),
        status_code: response.status,
      } as ErrorResponse);
    }

    throw new Error(`Export failed: ${response.status} ${response.statusText}`);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch?.[1] ?? "reformlab-export";

  const blob = await response.blob();
  return { blob, filename };
}
