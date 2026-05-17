// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Technology sets API client — Story 28.1.
 *
 * Provides typed fetch functions for the technology sets API endpoints.
 */

// ============================================================================
// Types
// ============================================================================

export type DecisionDomainKey = "heating" | "vehicle";

export interface TechnologyAlternative {
  id: string;
  name: string;
  attributes: Record<string, string | number>;
  isIncumbentOnly?: boolean;
}

export interface DomainTechnologySet {
  domain: DecisionDomainKey;
  enabled: boolean;
  alternatives: TechnologyAlternative[];
  referenceAlternativeId: string | null;
  costColumn?: string;
}

export interface TechnologySet {
  version: string;
  domains: Partial<Record<DecisionDomainKey, DomainTechnologySet>>;
}

// ============================================================================
// API client
// ============================================================================

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

/**
 * Get the default technology set for a domain.
 *
 * Story 28.1 / AC-3: GET /api/discrete-choice/technology-sets/default?domain=heating
 */
export async function getDefaultTechnologySet(
  domain: DecisionDomainKey,
): Promise<DomainTechnologySet> {
  const response = await fetch(
    `${BASE_URL}/discrete-choice/technology-sets/default?domain=${encodeURIComponent(domain)}`,
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ what: "Unknown error", why: `HTTP ${response.status}`, fix: "Try again later" }));
    throw new Error(`${error.what}: ${error.why}${error.fix ? `. ${error.fix}` : ""}`);
  }

  return response.json() as Promise<DomainTechnologySet>;
}

/**
 * Get all default technology sets.
 *
 * Story 28.1 / AC-3: GET /api/discrete-choice/technology-sets/default/all
 */
export async function getAllDefaultTechnologySets(): Promise<TechnologySet> {
  const response = await fetch(
    `${BASE_URL}/discrete-choice/technology-sets/default/all`,
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ what: "Unknown error", why: `HTTP ${response.status}`, fix: "Try again later" }));
    throw new Error(`${error.what}: ${error.why}${error.fix ? `. ${error.fix}` : ""}`);
  }

  return response.json() as Promise<TechnologySet>;
}
