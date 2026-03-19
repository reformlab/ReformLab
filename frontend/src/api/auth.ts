/** Authentication API functions. */

import type { LoginResponse } from "./types";
import { getAuthToken } from "./client";

/** Login with shared password. Does not use apiFetch to avoid auth loop. */
export async function login(password: string): Promise<LoginResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });

  if (!response.ok) {
    if (response.status === 429) {
      throw new Error("Too many login attempts. Try again in 15 minutes.");
    }
    throw new Error("Invalid password");
  }

  return (await response.json()) as LoginResponse;
}

/** Revoke the current session token on the server. Best-effort (fire-and-forget). */
export async function logout(): Promise<void> {
  const token = getAuthToken();
  if (!token) return;
  try {
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    // Best-effort — token cleared client-side regardless
  }
}
