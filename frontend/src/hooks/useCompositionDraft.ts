// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Composition draft persistence utilities — reads and writes policy set composition drafts to localStorage.
 *
 * Provides automatic draft saving and restoration for the Policies stage.
 * Drafts are local-only state that represent unsaved work-in-progress compositions.
 *
 * Key schema:
 *   reformlab-policy-draft → JSON<CompositionDraft | null>
 *
 * Draft lifecycle:
 *   - Auto-saved on any composition change (add, remove, reorder, parameter edit)
 *   - Auto-restored on mount if composition is empty
 *   - Cleared on portfolio load, portfolio save, or Clear button
 *   - Silent degradation on quota errors or corrupted data
 *
 * Story 27.5 — AC-1, AC-2, AC-7, AC-8.
 */

import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";

// ============================================================================
// localStorage key constants (exported for test access)
// ============================================================================

export const COMPOSITION_DRAFT_KEY = "reformlab-policy-draft";

// ============================================================================
// Types
// ============================================================================

/**
 * Draft data structure for auto-saved policy set compositions.
 * Stored in localStorage under COMPOSITION_DRAFT_KEY.
 */
export interface CompositionDraft {
  /** Current composition entries (policies in the panel) */
  composition: CompositionEntry[];
  /** Selected conflict resolution strategy */
  resolutionStrategy: string;
  /** Instance counter value (prevents duplicate instanceIds on restore) */
  instanceCounter: number;
  /** Name of the portfolio this draft was based on (if any) */
  savedPortfolioName: string | null;
  /** ISO timestamp of when the draft was last saved (auto-generated if omitted) */
  timestamp?: number;
}

// ============================================================================
// Module-level persistence functions (stable references, no React state)
// ============================================================================

/**
 * Save composition draft to localStorage.
 *
 * @param draft - Draft to save, or null to clear existing draft
 *
 * Silent failure on:
 * - localStorage quota exceeded
 * - Private browsing mode (localStorage disabled)
 * - Any other localStorage errors
 *
 * Story 27.5 — AC-1, AC-7.
 */
export function saveCompositionDraft(draft: CompositionDraft | null): void {
  try {
    if (draft === null) {
      localStorage.removeItem(COMPOSITION_DRAFT_KEY);
      return;
    }
    // Auto-generate timestamp if not provided
    const draftToSave = {
      ...draft,
      timestamp: draft.timestamp ?? Date.now(),
    };
    localStorage.setItem(COMPOSITION_DRAFT_KEY, JSON.stringify(draftToSave));
  } catch {
    // Storage quota exceeded or localStorage unavailable — silently ignore
    // AC-7: No errors or toasts on quota exceeded
  }
}

/**
 * Load composition draft from localStorage.
 *
 * @returns Draft object if found and valid, null otherwise
 *
 * Silent failure on:
 * - Missing draft data
 * - Corrupted JSON (parse errors)
 * - Malformed draft object (missing required fields)
 *
 * Story 27.5 — AC-2, AC-8.
 */
export function loadCompositionDraft(): CompositionDraft | null {
  try {
    const raw = localStorage.getItem(COMPOSITION_DRAFT_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw);

    // Validate required fields (defensive programming)
    if (
      !parsed ||
      typeof parsed !== "object" ||
      !Array.isArray(parsed.composition) ||
      typeof parsed.resolutionStrategy !== "string" ||
      typeof parsed.instanceCounter !== "number"
    ) {
      // AC-8: Corrupted data is discarded silently — remove bad key to prevent re-parse
      try {
        localStorage.removeItem(COMPOSITION_DRAFT_KEY);
      } catch {
        // Silently ignore removal failures
      }
      return null;
    }

    // timestamp is optional; if present, validate type
    if (parsed.timestamp !== undefined && typeof parsed.timestamp !== "number") {
      try {
        localStorage.removeItem(COMPOSITION_DRAFT_KEY);
      } catch {
        // Silently ignore removal failures
      }
      return null;
    }

    return parsed as CompositionDraft;
  } catch {
    // Parse error or other exception — remove bad key and return null
    // AC-8: Corrupted data is discarded silently
    try {
      localStorage.removeItem(COMPOSITION_DRAFT_KEY);
    } catch {
      // Silently ignore removal failures
    }
    return null;
  }
}

// No React hook wrapper — use module-level exports directly for stable references.
// This differs from useScenarioPersistence which needed backward compatibility.
