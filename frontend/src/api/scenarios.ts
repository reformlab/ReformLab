/** Scenario CRUD API functions. */

import { apiFetch } from "./client";
import type {
  CloneRequest,
  CreateScenarioRequest,
  ScenarioResponse,
} from "./types";

/** List all registered scenario names. */
export async function listScenarios(): Promise<string[]> {
  const result = await apiFetch<{ scenarios: string[] }>("/api/scenarios");
  return result.scenarios;
}

/** Get a scenario by name. */
export async function getScenario(name: string): Promise<ScenarioResponse> {
  return apiFetch<ScenarioResponse>(`/api/scenarios/${encodeURIComponent(name)}`);
}

/** Create and register a new scenario. */
export async function createScenario(
  request: CreateScenarioRequest,
): Promise<string> {
  const result = await apiFetch<{ version_id: string }>("/api/scenarios", {
    method: "POST",
    body: JSON.stringify(request),
  });
  return result.version_id;
}

/** Clone an existing scenario with a new name. */
export async function cloneScenario(
  name: string,
  newName: string,
): Promise<ScenarioResponse> {
  const body: CloneRequest = { new_name: newName };
  return apiFetch<ScenarioResponse>(
    `/api/scenarios/${encodeURIComponent(name)}/clone`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}
