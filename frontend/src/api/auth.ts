/** Authentication API functions. */

import type { LoginResponse } from "./types";

/** Login with shared password. Does not use apiFetch to avoid auth loop. */
export async function login(password: string): Promise<LoginResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });

  if (!response.ok) {
    throw new Error("Invalid password");
  }

  return (await response.json()) as LoginResponse;
}
