// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for useCompositionDraft hook.
 * Story 27.5 — Task 1, Task 5.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  COMPOSITION_DRAFT_KEY,
  saveCompositionDraft,
  loadCompositionDraft,
} from "@/hooks/useCompositionDraft";
import type { CompositionDraft } from "@/hooks/useCompositionDraft";

// ============================================================================
// Helpers
// ============================================================================

function makeDraft(overrides: Partial<CompositionDraft> = {}): CompositionDraft {
  return {
    composition: [
      {
        templateId: "carbon-tax-flat",
        name: "Carbon Tax",
        parameters: { tax_rate: 44 },
        rateSchedule: {},
        instanceId: "carbon-tax-flat-ins0",
        editableParameterGroups: [],
      },
    ],
    resolutionStrategy: "error",
    instanceCounter: 1,
    savedPortfolioName: null,
    timestamp: Date.now(),
    ...overrides,
  };
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  localStorage.clear();
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-04-30T00:00:00Z"));
});

afterEach(() => {
  vi.useRealTimers();
});

// ============================================================================
// saveCompositionDraft / loadCompositionDraft
// ============================================================================

describe("Story 27.5: saveCompositionDraft / loadCompositionDraft", () => {
  describe("AC-1: Auto-save composition changes", () => {
    it("round-trip preserves all draft fields", () => {
      const draft = makeDraft();
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded).toEqual(draft);
    });

    it("loadCompositionDraft returns null when localStorage is empty", () => {
      const loaded = loadCompositionDraft();
      expect(loaded).toBeNull();
    });

    it("includes timestamp auto-generated on save", () => {
      // Create a draft and manually construct one without timestamp
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { timestamp: _timestamp, ...draftWithoutTimestampField } = makeDraft();
      // Explicitly cast to allow passing without timestamp field (will be auto-generated)
      saveCompositionDraft(draftWithoutTimestampField as CompositionDraft);
      const loaded = loadCompositionDraft();
      expect(loaded?.timestamp).toBeDefined();
      expect(loaded?.timestamp).toBe(Date.now());
    });

    it("saves composition array correctly", () => {
      const draft = makeDraft({
        composition: [
          {
            templateId: "tax1",
            name: "Tax 1",
            parameters: { rate: 10 },
            rateSchedule: {},
            instanceId: "tax1-ins0",
            editableParameterGroups: [],
          },
          {
            templateId: "tax2",
            name: "Tax 2",
            parameters: { rate: 20 },
            rateSchedule: {},
            instanceId: "tax2-ins1",
            editableParameterGroups: [],
          },
        ],
      });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.composition).toHaveLength(2);
      expect(loaded?.composition[0].templateId).toBe("tax1");
      expect(loaded?.composition[1].templateId).toBe("tax2");
    });

    it("saves resolution strategy correctly", () => {
      const draft = makeDraft({ resolutionStrategy: "sum" });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.resolutionStrategy).toBe("sum");
    });

    it("saves instance counter correctly", () => {
      const draft = makeDraft({ instanceCounter: 42 });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.instanceCounter).toBe(42);
    });

    it("saves savedPortfolioName correctly", () => {
      const draft = makeDraft({ savedPortfolioName: "my-portfolio" });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.savedPortfolioName).toBe("my-portfolio");
    });

    it("saves null savedPortfolioName correctly", () => {
      const draft = makeDraft({ savedPortfolioName: null });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.savedPortfolioName).toBeNull();
    });
  });

  describe("AC-7: Silent degradation on localStorage quota errors", () => {
    it("saveCompositionDraft silently handles quota exceeded errors", () => {
      // Mock setItem to throw quota exceeded error
      vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
        throw new DOMException("QuotaExceededError", "QuotaExceededError");
      });

      const draft = makeDraft();
      expect(() => saveCompositionDraft(draft)).not.toThrow();

      vi.spyOn(Storage.prototype, "setItem").mockRestore();
    });

    it("saveCompositionDraft silently handles other localStorage errors", () => {
      vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
        throw new Error("Random error");
      });

      const draft = makeDraft();
      expect(() => saveCompositionDraft(draft)).not.toThrow();

      vi.spyOn(Storage.prototype, "setItem").mockRestore();
    });
  });

  describe("AC-8: Silent degradation on parse errors", () => {
    it("loadCompositionDraft returns null on corrupted JSON", () => {
      localStorage.setItem(COMPOSITION_DRAFT_KEY, "{not valid json");
      const loaded = loadCompositionDraft();
      expect(loaded).toBeNull();
    });

    it("loadCompositionDraft returns null on missing data", () => {
      localStorage.removeItem(COMPOSITION_DRAFT_KEY);
      const loaded = loadCompositionDraft();
      expect(loaded).toBeNull();
    });

    it("loadCompositionDraft returns null on malformed draft object", () => {
      localStorage.setItem(COMPOSITION_DRAFT_KEY, JSON.stringify({ invalid: "data" }));
      const loaded = loadCompositionDraft();
      expect(loaded).toBeNull();
    });

    it("loadCompositionDraft never throws on parse errors", () => {
      localStorage.setItem(COMPOSITION_DRAFT_KEY, "{corrupted");
      expect(() => loadCompositionDraft()).not.toThrow();
    });
  });

  describe("Draft clear functionality", () => {
    it("saveCompositionDraft(null) clears the draft from localStorage", () => {
      const draft = makeDraft();
      saveCompositionDraft(draft);
      expect(loadCompositionDraft()).not.toBeNull();

      saveCompositionDraft(null);
      expect(loadCompositionDraft()).toBeNull();
    });

    it("saveCompositionDraft(null) is idempotent (safe to call multiple times)", () => {
      saveCompositionDraft(null);
      saveCompositionDraft(null);
      saveCompositionDraft(null);
      expect(loadCompositionDraft()).toBeNull();
    });
  });

  describe("Complex composition entries", () => {
    it("round-trip preserves editableParameterGroups", () => {
      const draft = makeDraft({
        composition: [
          {
            templateId: "tax1",
            name: "Tax 1",
            parameters: { rate: 10 },
            rateSchedule: {},
            instanceId: "tax1-ins0",
            editableParameterGroups: [
              { id: "group-0", name: "Tax Rates", parameterIds: ["rate"] },
              { id: "group-1", name: "Thresholds", parameterIds: ["threshold"] },
            ],
          },
        ],
      });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.composition[0].editableParameterGroups).toEqual([
        { id: "group-0", name: "Tax Rates", parameterIds: ["rate"] },
        { id: "group-1", name: "Thresholds", parameterIds: ["threshold"] },
      ]);
    });

    it("round-trip preserves from-scratch policy fields", () => {
      const draft = makeDraft({
        composition: [
          {
            templateId: "",
            name: "Custom Policy",
            parameters: { rate: 10 },
            rateSchedule: {},
            instanceId: "blank-0",
            policy_type: "tax",
            category_id: "custom",
            parameter_groups: ["Mechanism", "Schedule"],
            editableParameterGroups: [],
          },
        ],
      });
      saveCompositionDraft(draft);
      const loaded = loadCompositionDraft();
      expect(loaded?.composition[0].policy_type).toBe("tax");
      expect(loaded?.composition[0].category_id).toBe("custom");
      expect(loaded?.composition[0].parameter_groups).toEqual(["Mechanism", "Schedule"]);
    });
  });
});

// ============================================================================
// Key constants
// ============================================================================

describe("exported key constants", () => {
  it("COMPOSITION_DRAFT_KEY is 'reformlab-policy-draft'", () => {
    expect(COMPOSITION_DRAFT_KEY).toBe("reformlab-policy-draft");
  });
});
