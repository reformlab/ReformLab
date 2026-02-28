/** Simulation run API functions. */

import { apiFetch } from "./client";
import type {
  MemoryCheckRequest,
  MemoryCheckResponse,
  RunRequest,
  RunResponse,
} from "./types";

/** Execute a simulation synchronously and return the result. */
export async function runScenario(request: RunRequest): Promise<RunResponse> {
  return apiFetch<RunResponse>("/api/runs", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/** Pre-flight memory estimation for a simulation configuration. */
export async function checkMemory(
  request: MemoryCheckRequest,
): Promise<MemoryCheckResponse> {
  return apiFetch<MemoryCheckResponse>("/api/runs/memory-check", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
