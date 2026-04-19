// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PoliciesStageScreen — Stage 1: Policy (Story 20.3, AC-1 through AC-6).
 *
 * Inline composition layout: template browser and portfolio composition panel side-by-side
 * on a single page (no multi-step wizard). Replaces the PortfolioDesignerScreen 3-step flow.
 *
 * Integrates:
 * - PortfolioTemplateBrowser (left column) — unchanged component
 * - PortfolioCompositionPanel (right column) — minimumPolicies=1
 * - Toolbar: save/load/clone/clear + validity indicator
 * - Inline conflict detection with debounce (AC-3)
 * - Portfolio ↔ activeScenario integration via updateScenarioField (AC-4, AC-5)
 * - Nav rail completion via activeScenario.portfolioName (AC-5)
 */

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import {
  Save, FolderOpen, Copy, X, CheckCircle2, AlertTriangle, Trash2, Plus,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { PortfolioTemplateBrowser } from "@/components/simulation/PortfolioTemplateBrowser";
import { PortfolioCompositionPanel } from "@/components/simulation/PortfolioCompositionPanel";
// Story 25.3: Import CreateFromScratchDialog for from-scratch flow
import { CreateFromScratchDialog } from "@/components/simulation/CreateFromScratchDialog";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { ConflictList } from "@/components/simulation/ConflictList";
import { ApiError } from "@/api/client";
import {
  deletePortfolio,
  validatePortfolio,
} from "@/api/portfolios";
// Story 25.1 / Task 3.1: Import listCategories
import { listCategories } from "@/api/categories";
// Story 25.3: Import createBlankPolicy for from-scratch flow
import { createBlankPolicy } from "@/api/templates";
import { useAppState } from "@/contexts/AppContext";
import type { PortfolioConflict, Category } from "@/api/types";
import { usePortfolioSaveDialog } from "@/hooks/usePortfolioSaveDialog";
import { usePortfolioLoadDialog } from "@/hooks/usePortfolioLoadDialog";
import { usePortfolioCloneDialog } from "@/hooks/usePortfolioCloneDialog";

// ============================================================================
// Constants
// ============================================================================

const VALID_STRATEGIES = ["error", "sum", "first_wins", "last_wins", "max"] as const;
type ResolutionStrategy = (typeof VALID_STRATEGIES)[number];

const STRATEGY_LABELS: Record<ResolutionStrategy, string> = {
  error: "Error on conflict",
  sum: "Sum conflicting values",
  first_wins: "First policy wins",
  last_wins: "Last policy wins",
  max: "Use maximum value",
};

// ============================================================================
// PoliciesStageScreen
// ============================================================================

export function PoliciesStageScreen() {
  const {
    templates,
    portfolios,
    refetchPortfolios,
    activeScenario,
    updateScenarioField,
    setSelectedPortfolioName,
  } = useAppState();

  // ============================================================================
  // Local composition state
  // ============================================================================

  // Story 25.2: Duplicate instance support - use monotonic counter instead of selection toggle
  // Use useRef for counter to avoid stale closure bugs with rapid-fire adds
  const instanceCounterRef = useRef(0);
  const [composition, setComposition] = useState<CompositionEntry[]>([]);
  const [resolutionStrategy, setResolutionStrategy] = useState<ResolutionStrategy>("error");
  const [conflicts, setConflicts] = useState<PortfolioConflict[]>([]);
  const [validationLoading, setValidationLoading] = useState(false);

  // Story 25.1 / Task 3.1: Categories state (null = loading, [] = failed/empty)
  const [categories, setCategories] = useState<Category[] | null>(null);

  // Story 25.3: Choice dialog state for "+ Add Policy" button
  const [choiceDialogOpen, setChoiceDialogOpen] = useState(false);

  // Story 25.3: From-scratch dialog state
  const [fromScratchDialogOpen, setFromScratchDialogOpen] = useState(false);
  const [autoExpandInstanceId, setAutoExpandInstanceId] = useState<string | null>(null);

  // Track the portfolio name currently loaded into the composition panel
  const [activePortfolioName, setActivePortfolioName] = useState<string | null>(null);

  // Prevent auto-load from triggering after a save (which sets portfolioName, which fires effect)
  const loadedRef = useRef<string | null>(null);

  // ============================================================================
  // Computed validity
  // AC-6: valid = composition.length >= 1 AND (no conflicts OR strategy !== "error")
  // ============================================================================

  const isPortfolioValid =
    composition.length >= 1 &&
    (composition.length < 2 || conflicts.length === 0 || resolutionStrategy !== "error");

  // Story 25.2: Derive browser highlighting from composition (templateIds in composition)
  const inCompositionTemplateIds = useMemo(
    () => composition.map((c) => c.templateId),
    [composition],
  );

  // Story 25.2: Count instances per template for browser badges
  const templateInstanceCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const entry of composition) {
      counts[entry.templateId] = (counts[entry.templateId] || 0) + 1;
    }
    return counts;
  }, [composition]);

  // ============================================================================
  // Composition handlers
  // ============================================================================

  // Story 25.2: Add template instance - creates unique instance using monotonic counter
  const addTemplateInstance = useCallback((templateId: string) => {
    const t = templates.find((tmpl) => tmpl.id === templateId);
    if (!t) return;

    const id = instanceCounterRef.current++;
    const newInstance: CompositionEntry = {
      instanceId: `${templateId}-ins${id}`, // Guaranteed unique via counter
      templateId,
      name: t?.name ?? templateId,
      parameters: {},
      rateSchedule: {},
    };

    setComposition((prev) => [...prev, newInstance]);
  }, [templates]);

  // Story 25.3: Handle blank policy creation from from-scratch flow
  const handleCreateBlankPolicy = useCallback(async (
    policyType: "tax" | "subsidy" | "transfer",
    categoryId: string,
  ) => {
    try {
      const response = await createBlankPolicy({
        policy_type: policyType,
        category_id: categoryId,
      });

      // Create new composition entry from blank policy response
      const id = instanceCounterRef.current++;
      const newInstance: CompositionEntry = {
        instanceId: `blank-${id}`, // MUST use counter pattern per story spec
        templateId: "", // Empty for from-scratch policies
        name: response.name,
        parameters: {},
        rateSchedule: response.rate_schedule,
        policy_type: response.policy_type,
        category_id: response.category_id,
        parameter_groups: response.parameter_groups,
      };

      setComposition((prev) => [...prev, newInstance]);

      // Set auto-expand instance ID to expand the newly created policy card
      setAutoExpandInstanceId(newInstance.instanceId);

      toast.success(`Created "${response.name}" policy from scratch`);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Failed to create policy from scratch", { description: err.message });
      }
    }
  }, []);

  // Removed: toggleTemplate (replaced by addTemplateInstance for duplicate support)

  const handleReorder = useCallback((from: number, to: number) => {
    setComposition((prev) => {
      const next = [...prev];
      const [item] = next.splice(from, 1);
      if (item) next.splice(to, 0, item);
      return next;
    });
  }, []);

  const handleRemove = useCallback((index: number) => {
    setComposition((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleParameterChange = useCallback(
    (index: number, paramId: string, value: number) => {
      setComposition((prev) =>
        prev.map((e, i) =>
          i === index ? { ...e, parameters: { ...e.parameters, [paramId]: value } } : e,
        ),
      );
    },
    [],
  );

  const handleRateScheduleChange = useCallback(
    (index: number, schedule: Record<string, number>) => {
      setComposition((prev) =>
        prev.map((e, i) => (i === index ? { ...e, rateSchedule: schedule } : e)),
      );
    },
    [],
  );

  // ============================================================================
  // Validation — debounced (AC-3, Task 5.1)
  // ============================================================================

  const runValidation = useCallback(async () => {
    if (composition.length < 2) {
      setConflicts([]);
      return;
    }
    setValidationLoading(true);
    try {
      const result = await validatePortfolio({
        policies: composition.map((e) => {
          const t = templates.find((tmpl) => tmpl.id === e.templateId);
          return {
            name: e.name,
            policy_type: (t?.type ?? "carbon_tax").replace(/-/g, "_"),
            rate_schedule: e.rateSchedule,
            exemptions: [],
            thresholds: [],
            covered_categories: [],
            extra_params: e.parameters as Record<string, unknown>,
          };
        }),
        resolution_strategy: resolutionStrategy,
      });
      setConflicts(result.conflicts);
    } catch {
      toast.warning("Conflict check failed — conflicts may not be detected");
      setConflicts([]);
    } finally {
      setValidationLoading(false);
    }
  }, [composition, templates, resolutionStrategy]);

  const validationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (composition.length < 2) {
      setConflicts([]);
      return;
    }
    if (validationTimerRef.current) clearTimeout(validationTimerRef.current);
    validationTimerRef.current = setTimeout(() => {
      void runValidation();
    }, 500);
    return () => {
      if (validationTimerRef.current) clearTimeout(validationTimerRef.current);
    };
  }, [composition, resolutionStrategy, runValidation]);

  // Story 25.1 / Task 3.1: Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const cats = await listCategories();
        setCategories(cats);
      } catch (err) {
        console.error("Failed to load categories:", err);
        // Story 25.1 / AC-6: Non-blocking warning - templates still shown ungrouped
        setCategories([]); // Empty categories array causes ungrouped display
      }
    };
    void fetchCategories();
  }, []);

  // ============================================================================
  // Portfolio dialog hooks (Task 6.1 through 6.3)
  // ============================================================================

  const {
    saveDialogOpen,
    portfolioSaveName,
    portfolioSaveDesc,
    saveNameError,
    saving,
    openSaveDialog,
    closeSaveDialog,
    handleSaveNameChange,
    setPortfolioSaveDesc,
    handleSave,
  } = usePortfolioSaveDialog({
    templates,
    composition,
    resolutionStrategy,
    conflicts,
    loadedPortfolioRef: loadedRef,
    setActivePortfolioName,
    updateScenarioPortfolioName: (name) => updateScenarioField("portfolioName", name),
    setSelectedPortfolioName,
    refetchPortfolios,
  });

  const {
    loadDialogOpen,
    openLoadDialog,
    closeLoadDialog,
    handleLoad,
  } = usePortfolioLoadDialog({
    templates,
    activeScenarioPortfolioName: activeScenario?.portfolioName,
    compositionLength: composition.length,
    validStrategies: VALID_STRATEGIES,
    defaultResolutionStrategy: "error",
    loadedPortfolioRef: loadedRef,
    setComposition,
    setResolutionStrategy,
    setActivePortfolioName,
    updateScenarioPortfolioName: (name) => updateScenarioField("portfolioName", name),
    setSelectedPortfolioName,
    setInstanceCounter: (value: number) => {
      instanceCounterRef.current = value;
    },
  });

  const {
    cloneDialogName,
    cloneNewName,
    cloneNameError,
    cloning,
    openCloneDialog,
    closeCloneDialog,
    handleCloneNameChange,
    handleClone,
  } = usePortfolioCloneDialog({
    portfolios,
    refetchPortfolios,
  });

  // ============================================================================
  // Portfolio Clear (Task 6.4)
  // ============================================================================

  const handleClear = useCallback(() => {
    setComposition([]);
    setConflicts([]);
    setActivePortfolioName(null);
    loadedRef.current = null;
    updateScenarioField("portfolioName", null);
    setSelectedPortfolioName(null);
    instanceCounterRef.current = 0; // Reset counter on clear
  }, [updateScenarioField, setSelectedPortfolioName]);

  // ============================================================================
  // Portfolio Delete (Task 6.5)
  // ============================================================================

  const handleDeletePortfolio = useCallback(async (name: string) => {
    try {
      await deletePortfolio(name);
      void refetchPortfolios();
      toast.success(`Portfolio '${name}' deleted`);
      // If the deleted portfolio is the active one, delink from scenario
      if (activeScenario?.portfolioName === name) {
        updateScenarioField("portfolioName", null);
        setSelectedPortfolioName(null);
        setActivePortfolioName(null);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Delete failed", { description: err.message });
      }
    }
  }, [activeScenario?.portfolioName, refetchPortfolios, updateScenarioField, setSelectedPortfolioName]);

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-3">
        {/* Portfolio name / status */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {activePortfolioName ? (
            <span className="text-sm font-medium text-slate-700 truncate">
              {activePortfolioName}
            </span>
          ) : (
            <span className="text-sm text-slate-400 italic">Unsaved policy set</span>
          )}
          {/* Validity indicator (AC-6) */}
          {composition.length >= 1 ? (
            isPortfolioValid ? (
              <CheckCircle2
                className="h-4 w-4 shrink-0 text-emerald-500"
                aria-label="Portfolio valid"
                data-testid="validity-indicator-valid"
              />
            ) : (
              <AlertTriangle
                className="h-4 w-4 shrink-0 text-amber-500"
                aria-label="Portfolio has issues"
                data-testid="validity-indicator-invalid"
              />
            )
          ) : null}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Story 25.3: "+ Add Policy" button with choice dialog */}
          <Button
            size="sm"
            onClick={() => setChoiceDialogOpen(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
            title="Add a policy to your composition"
          >
            <Plus className="mr-1.5 h-3 w-3" />
            Add Policy
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={openSaveDialog}
            disabled={composition.length < 1}
            title={composition.length < 1 ? "Add at least 1 policy template" : "Save policy set"}
          >
            <Save className="mr-1.5 h-3 w-3" />
            Save
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={openLoadDialog}
            title="Load a saved policy set"
          >
            <FolderOpen className="mr-1.5 h-3 w-3" />
            Load
          </Button>
          {activePortfolioName ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => openCloneDialog(activePortfolioName)}
              title="Clone active policy set"
            >
              <Copy className="mr-1.5 h-3 w-3" />
              Clone
            </Button>
          ) : null}
          {composition.length > 0 ? (
            <Button
              size="sm"
              variant="outline"
              onClick={handleClear}
              title="Clear composition"
            >
              <X className="mr-1.5 h-3 w-3" />
              Clear
            </Button>
          ) : null}
        </div>

        {/* Resolution strategy */}
        {composition.length >= 2 ? (
          <>
            <Separator orientation="vertical" className="h-6 mx-1" />
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 shrink-0">Conflict strategy:</span>
              <Select
                value={resolutionStrategy}
                onChange={(e) => setResolutionStrategy(e.target.value as ResolutionStrategy)}
                className="text-xs h-8"
                aria-label="Conflict resolution strategy"
              >
                {VALID_STRATEGIES.map((s) => (
                  <option key={s} value={s}>{STRATEGY_LABELS[s]}</option>
                ))}
              </Select>
            </div>
          </>
        ) : null}
      </div>

      {/* Conflict display (AC-3) */}
      {conflicts.length > 0 || (composition.length >= 2 && validationLoading) ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3">
          {validationLoading ? (
            <p className="text-xs text-slate-500">Checking for conflicts…</p>
          ) : (
            <ConflictList conflicts={conflicts} />
          )}
        </div>
      ) : null}

      {/* Main two-column layout (AC-1) - Story 22.2: 50/50 equal split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 flex-1 min-h-0">
        {/* Left: Template browser */}
        <div className="rounded-lg border border-slate-200 bg-white p-3 overflow-y-auto min-w-0">
          <h2 className="text-sm font-semibold text-slate-900 mb-2">Policy Templates</h2>
          {/* Story 25.2: Use add-instance instead of toggle selection; pass highlighting state */}
          <PortfolioTemplateBrowser
            templates={templates}
            selectedIds={inCompositionTemplateIds}
            onAddTemplate={addTemplateInstance}
            categories={categories}
            templateInstanceCounts={templateInstanceCounts}
          />
        </div>

        {/* Right: Composition panel */}
        <div className="rounded-lg border border-slate-200 bg-white p-3 overflow-y-auto min-w-0">
          <h2 className="text-sm font-semibold text-slate-900 mb-2">Policy Set Composition</h2>
          {composition.length === 0 ? (
            <div className="border border-slate-200 bg-slate-50 p-6 text-center mt-2">
              <p className="text-sm text-slate-500">
                Add at least 1 policy template to compose a policy set.
              </p>
            </div>
          ) : (
            <PortfolioCompositionPanel
              templates={templates}
              composition={composition}
              onReorder={handleReorder}
              onRemove={handleRemove}
              onParameterChange={handleParameterChange}
              onRateScheduleChange={handleRateScheduleChange}
              minimumPolicies={1}
              categories={categories}
              autoExpandInstanceId={autoExpandInstanceId}
            />
          )}
        </div>
      </div>

      {/* Saved policy sets section */}
      {portfolios.length > 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs font-semibold text-slate-700 mb-2">
            Saved Policy Sets ({portfolios.length})
          </p>
          <div className="space-y-1.5">
            {portfolios.map((p) => (
              <div
                key={p.name}
                className="flex items-center gap-2 text-xs text-slate-700"
              >
                <span className="font-mono flex-1 truncate">{p.name}</span>
                <Badge variant="default" className="text-xs shrink-0">
                  {p.policy_count} {p.policy_count === 1 ? "policy" : "policies"}
                </Badge>
                {p.description ? (
                  <span className="text-slate-400 truncate flex-1">{p.description}</span>
                ) : null}
                {activeScenario?.portfolioName === p.name ? (
                  <Badge variant="default" className="text-xs shrink-0 bg-blue-100 text-blue-700">
                    active
                  </Badge>
                ) : null}
                <button
                  type="button"
                  onClick={() => void handleLoad(p.name)}
                  className="shrink-0 border border-slate-200 p-1 text-blue-500 hover:bg-blue-50"
                  aria-label={`Load policy set ${p.name}`}
                  title="Load into editor"
                >
                  <FolderOpen className="h-3 w-3" />
                </button>
                <button
                  type="button"
                  onClick={() => openCloneDialog(p.name)}
                  className="shrink-0 border border-slate-200 p-1 text-slate-500 hover:bg-slate-50"
                  aria-label={`Clone policy set ${p.name}`}
                  title="Clone"
                >
                  <Copy className="h-3 w-3" />
                </button>
                <button
                  type="button"
                  onClick={() => void handleDeletePortfolio(p.name)}
                  className="shrink-0 border border-slate-200 p-1 text-red-500 hover:bg-red-50"
                  aria-label={`Delete policy set ${p.name}`}
                  title="Delete"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Save dialog (AC-4, Task 6.1) */}
      {saveDialogOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="save-portfolio-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center"
          onKeyDown={(e) => { if (e.key === "Escape") closeSaveDialog(); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={closeSaveDialog}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 id="save-portfolio-dialog-title" className="text-sm font-semibold text-slate-900 mb-4">
              Save Policy Set
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1" htmlFor="save-portfolio-name">
                  Policy set name <span className="text-red-500">*</span>
                </label>
                <Input
                  id="save-portfolio-name"
                  type="text"
                  value={portfolioSaveName}
                  onChange={(e) => {
                    handleSaveNameChange(e.target.value);
                  }}
                  placeholder="my-policy-set-2030"
                  className={saveNameError ? "border-red-400" : ""}
                  aria-describedby={saveNameError ? "save-name-error" : undefined}
                />
                {saveNameError ? (
                  <p id="save-name-error" className="mt-0.5 text-xs text-red-600">{saveNameError}</p>
                ) : (
                  <p className="mt-0.5 text-xs text-slate-400">
                    Lowercase slug: letters, digits, hyphens (max 64 chars)
                  </p>
                )}
              </div>

              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1" htmlFor="save-portfolio-desc">
                  Description
                </label>
                <Input
                  id="save-portfolio-desc"
                  type="text"
                  value={portfolioSaveDesc}
                  onChange={(e) => setPortfolioSaveDesc(e.target.value)}
                  placeholder="Brief description of this policy set"
                />
              </div>

              {resolutionStrategy === "error" && conflicts.length > 0 ? (
                <p className="text-xs text-red-600 border border-red-200 bg-red-50 p-2">
                  Cannot save: conflicts detected with &quot;error&quot; strategy. Change strategy or remove conflicting policies.
                </p>
              ) : null}
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={closeSaveDialog}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => void handleSave()}
                disabled={
                  saving ||
                  !!saveNameError ||
                  !portfolioSaveName.trim() ||
                  (resolutionStrategy === "error" && conflicts.length > 0)
                }
              >
                {saving ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Load dialog (Task 6.2) */}
      {loadDialogOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="load-portfolio-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center"
          onKeyDown={(e) => { if (e.key === "Escape") closeLoadDialog(); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={closeLoadDialog}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 id="load-portfolio-dialog-title" className="text-sm font-semibold text-slate-900 mb-4">
              Load Policy Set
            </h3>

            {portfolios.length === 0 ? (
              <p className="text-sm text-slate-500">No saved policy sets found.</p>
            ) : (
              <div className="space-y-1.5 max-h-64 overflow-y-auto">
                {portfolios.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    onClick={() => void handleLoad(p.name)}
                    className="w-full text-left border border-slate-200 p-3 hover:bg-slate-50 rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-slate-900 flex-1 truncate">{p.name}</span>
                      <Badge variant="default" className="text-xs shrink-0">
                        {p.policy_count} {p.policy_count === 1 ? "policy" : "policies"}
                      </Badge>
                    </div>
                    {p.description ? (
                      <p className="mt-0.5 text-xs text-slate-500 truncate">{p.description}</p>
                    ) : null}
                  </button>
                ))}
              </div>
            )}

            <div className="mt-4 flex justify-end">
              <Button variant="outline" size="sm" onClick={closeLoadDialog}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Clone dialog (Task 6.3) */}
      {cloneDialogName !== null ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="clone-portfolio-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center"
          onKeyDown={(e) => { if (e.key === "Escape") closeCloneDialog(); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={closeCloneDialog}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 id="clone-portfolio-dialog-title" className="text-sm font-semibold text-slate-900 mb-4">
              Clone &ldquo;{cloneDialogName}&rdquo;
            </h3>

            <div>
              <label className="text-xs font-medium text-slate-700 block mb-1" htmlFor="clone-name">
                New name <span className="text-red-500">*</span>
              </label>
              <Input
                id="clone-name"
                type="text"
                value={cloneNewName}
                onChange={(e) => {
                  handleCloneNameChange(e.target.value);
                }}
                placeholder="my-portfolio-copy"
                className={cloneNameError ? "border-red-400" : ""}
              />
              {cloneNameError ? (
                <p className="mt-0.5 text-xs text-red-600">{cloneNameError}</p>
              ) : (
                <p className="mt-0.5 text-xs text-slate-400">
                  Lowercase slug: letters, digits, hyphens (max 64 chars)
                </p>
              )}
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={closeCloneDialog}
                disabled={cloning}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => void handleClone()}
                disabled={cloning || !!cloneNameError || !cloneNewName.trim()}
              >
                {cloning ? "Cloning…" : "Clone"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Story 25.3: Choice dialog for "+ Add Policy" button */}
      {choiceDialogOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-policy-choice-title"
          className="fixed inset-0 z-50 flex items-center justify-center"
          onKeyDown={(e) => { if (e.key === "Escape") setChoiceDialogOpen(false); }}
          onClick={(e) => { if (e.target === e.currentTarget) setChoiceDialogOpen(false); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 id="add-policy-choice-title" className="text-sm font-semibold text-slate-900 mb-4">
              Add Policy
            </h3>

            <p className="text-sm text-slate-700 mb-4">
              How would you like to add a policy to your composition?
            </p>

            <div className="space-y-3">
              {/* From template: closes dialog, user clicks template cards */}
              <button
                type="button"
                onClick={() => {
                  setChoiceDialogOpen(false);
                  // User can now click template cards directly (existing behavior)
                }}
                className="w-full text-left border border-slate-200 p-4 hover:bg-slate-50 rounded-lg transition-colors"
              >
                <div className="font-medium text-sm text-slate-900">From template</div>
                <div className="text-xs text-slate-600 mt-1">
                  Select from existing policy templates in the browser
                </div>
              </button>

              {/* From scratch: opens CreateFromScratchDialog */}
              <button
                type="button"
                onClick={() => {
                  setChoiceDialogOpen(false);
                  setFromScratchDialogOpen(true);
                }}
                className="w-full text-left border border-slate-200 p-4 hover:bg-slate-50 rounded-lg transition-colors"
              >
                <div className="font-medium text-sm text-slate-900">From scratch</div>
                <div className="text-xs text-slate-600 mt-1">
                  Create a new policy by selecting type and category
                </div>
              </button>
            </div>

            <div className="mt-4 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setChoiceDialogOpen(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Story 25.3: Create from scratch dialog */}
      {fromScratchDialogOpen ? (
        <CreateFromScratchDialog
          categories={categories}
          onCreatePolicy={handleCreateBlankPolicy}
          onClose={() => setFromScratchDialogOpen(false)}
        />
      ) : null}
    </div>
  );
}
