// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PoliciesStageScreen — Stage 1: Policies & Portfolio (Story 20.3, AC-1 through AC-6).
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

import { useState, useCallback, useEffect, useRef } from "react";
import {
  Save, FolderOpen, Copy, X, CheckCircle2, AlertTriangle, Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { PortfolioTemplateBrowser } from "@/components/simulation/PortfolioTemplateBrowser";
import { PortfolioCompositionPanel } from "@/components/simulation/PortfolioCompositionPanel";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { ConflictList } from "@/components/simulation/ConflictList";
import { validatePortfolioName } from "@/components/simulation/portfolioValidation";
import { ApiError } from "@/api/client";
import {
  clonePortfolio,
  createPortfolio,
  deletePortfolio,
  getPortfolio,
  validatePortfolio,
} from "@/api/portfolios";
import { useAppState } from "@/contexts/AppContext";
import type { PortfolioConflict } from "@/api/types";

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

  const [selectedTemplateIds, setSelectedTemplateIds] = useState<string[]>([]);
  const [composition, setComposition] = useState<CompositionEntry[]>([]);
  const [resolutionStrategy, setResolutionStrategy] = useState<ResolutionStrategy>("error");
  const [conflicts, setConflicts] = useState<PortfolioConflict[]>([]);
  const [validationLoading, setValidationLoading] = useState(false);

  // Track the portfolio name currently loaded into the composition panel
  const [activePortfolioName, setActivePortfolioName] = useState<string | null>(null);

  // Prevent auto-load from triggering after a save (which sets portfolioName, which fires effect)
  const loadedRef = useRef<string | null>(null);

  // ============================================================================
  // Dialog state
  // ============================================================================

  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [portfolioSaveName, setPortfolioSaveName] = useState("");
  const [portfolioSaveDesc, setPortfolioSaveDesc] = useState("");
  const [saveNameError, setSaveNameError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [loadDialogOpen, setLoadDialogOpen] = useState(false);

  const [cloneDialogName, setCloneDialogName] = useState<string | null>(null);
  const [cloneNewName, setCloneNewName] = useState("");
  const [cloneNameError, setCloneNameError] = useState<string | null>(null);
  const [cloning, setCloning] = useState(false);

  // ============================================================================
  // Computed validity
  // AC-6: valid = composition.length >= 1 AND (no conflicts OR strategy !== "error")
  // ============================================================================

  const isPortfolioValid =
    composition.length >= 1 &&
    (composition.length < 2 || conflicts.length === 0 || resolutionStrategy !== "error");

  // ============================================================================
  // Template selection → composition sync
  // ============================================================================

  useEffect(() => {
    setComposition((prev) => {
      const toAdd = selectedTemplateIds
        .filter((id) => !prev.some((e) => e.templateId === id))
        .map((id) => {
          const t = templates.find((tmpl) => tmpl.id === id);
          return { templateId: id, name: t?.name ?? id, parameters: {}, rateSchedule: {} };
        });
      const filtered = prev.filter((e) => selectedTemplateIds.includes(e.templateId));
      return [...filtered, ...toAdd];
    });
  }, [selectedTemplateIds, templates]);

  // ============================================================================
  // Composition handlers
  // ============================================================================

  const toggleTemplate = useCallback((id: string) => {
    setSelectedTemplateIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const handleReorder = useCallback((from: number, to: number) => {
    setComposition((prev) => {
      const next = [...prev];
      const [item] = next.splice(from, 1);
      if (item) next.splice(to, 0, item);
      return next;
    });
  }, []);

  const handleRemove = useCallback((index: number) => {
    const removedId = composition[index]?.templateId;
    setComposition((prev) => prev.filter((_, i) => i !== index));
    if (removedId) {
      setSelectedTemplateIds((prev) => prev.filter((id) => id !== removedId));
    }
  }, [composition]);

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

  // ============================================================================
  // Portfolio auto-load on mount (Task 3.5)
  // When the screen mounts and activeScenario.portfolioName is set, load it.
  // ============================================================================

  const loadPortfolioIntoComposition = useCallback(async (name: string): Promise<boolean> => {
    try {
      const detail = await getPortfolio(name);
      const entries: CompositionEntry[] = detail.policies.map((p) => {
        const t = templates.find((tmpl) => tmpl.type.replace(/-/g, "_") === p.policy_type);
        return {
          templateId: t?.id ?? p.policy_type,
          name: p.name,
          parameters: Object.fromEntries(
            Object.entries(p.parameters).filter(([, v]) => typeof v === "number"),
          ) as Record<string, number>,
          rateSchedule: p.rate_schedule,
        };
      });
      setComposition(entries);
      setSelectedTemplateIds(entries.map((e) => e.templateId));
      setResolutionStrategy(
        VALID_STRATEGIES.includes(detail.resolution_strategy as ResolutionStrategy)
          ? (detail.resolution_strategy as ResolutionStrategy)
          : "error",
      );
      setActivePortfolioName(name);
      return true;
    } catch (err) {
      if (err instanceof ApiError) {
        toast.warning(`Could not load portfolio '${name}': ${err.why}`);
      } else {
        toast.warning(`Could not load portfolio '${name}'`);
      }
      return false;
    }
  }, [templates]);

  useEffect(() => {
    if (!activeScenario?.portfolioName) return;
    if (composition.length > 0) return;
    if (loadedRef.current === activeScenario.portfolioName) return;

    loadedRef.current = activeScenario.portfolioName;
    void loadPortfolioIntoComposition(activeScenario.portfolioName);
  }, [activeScenario?.portfolioName, composition.length, loadPortfolioIntoComposition]);

  // ============================================================================
  // Portfolio Save (Task 6.1)
  // ============================================================================

  const handleSave = useCallback(async () => {
    const err = validatePortfolioName(portfolioSaveName);
    setSaveNameError(err);
    if (err) return;

    if (resolutionStrategy === "error" && conflicts.length > 0) {
      toast.error("Resolve conflicts before saving", {
        description: "Change resolution strategy or remove conflicting policies",
      });
      return;
    }

    setSaving(true);
    try {
      await createPortfolio({
        name: portfolioSaveName,
        description: portfolioSaveDesc,
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

      // Task 3.2: update loadedRef BEFORE updating scenario field to avoid reload loop
      loadedRef.current = portfolioSaveName;
      setActivePortfolioName(portfolioSaveName);
      updateScenarioField("portfolioName", portfolioSaveName);
      setSelectedPortfolioName(portfolioSaveName);
      void refetchPortfolios();

      toast.success(`Portfolio '${portfolioSaveName}' saved`);
      setSaveDialogOpen(false);
      setPortfolioSaveName("");
      setPortfolioSaveDesc("");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Save failed", { description: err.message });
      }
    } finally {
      setSaving(false);
    }
  }, [
    portfolioSaveName,
    portfolioSaveDesc,
    composition,
    templates,
    resolutionStrategy,
    conflicts,
    updateScenarioField,
    setSelectedPortfolioName,
    refetchPortfolios,
  ]);

  // ============================================================================
  // Portfolio Load (Task 6.2)
  // ============================================================================

  const handleLoad = useCallback(async (name: string) => {
    const ok = await loadPortfolioIntoComposition(name);
    if (!ok) return; // warning toast already shown
    loadedRef.current = name;
    updateScenarioField("portfolioName", name);
    setSelectedPortfolioName(name);
    setLoadDialogOpen(false);
    toast.success(`Loaded portfolio '${name}'`);
  }, [loadPortfolioIntoComposition, updateScenarioField, setSelectedPortfolioName]);

  // ============================================================================
  // Portfolio Clone (Task 6.3)
  // ============================================================================

  const handleClone = useCallback(async () => {
    if (!cloneDialogName) return;
    const err = validatePortfolioName(cloneNewName);
    setCloneNameError(err);
    if (err) return;

    setCloning(true);
    try {
      await clonePortfolio(cloneDialogName, { new_name: cloneNewName });
      void refetchPortfolios();
      toast.success(`Cloned '${cloneDialogName}' as '${cloneNewName}'`);
      setCloneDialogName(null);
      setCloneNewName("");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Clone failed", { description: err.message });
      }
    } finally {
      setCloning(false);
    }
  }, [cloneDialogName, cloneNewName, refetchPortfolios]);

  // ============================================================================
  // Portfolio Clear (Task 6.4)
  // ============================================================================

  const handleClear = useCallback(() => {
    setComposition([]);
    setSelectedTemplateIds([]);
    setConflicts([]);
    setActivePortfolioName(null);
    loadedRef.current = null;
    updateScenarioField("portfolioName", null);
    setSelectedPortfolioName(null);
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
            <span className="text-sm text-slate-400 italic">Unsaved portfolio</span>
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
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setPortfolioSaveName("");
              setPortfolioSaveDesc("");
              setSaveNameError(null);
              setSaveDialogOpen(true);
            }}
            disabled={composition.length < 1}
            title={composition.length < 1 ? "Add at least 1 policy template" : "Save portfolio"}
          >
            <Save className="mr-1.5 h-3 w-3" />
            Save
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setLoadDialogOpen(true)}
            title="Load a saved portfolio"
          >
            <FolderOpen className="mr-1.5 h-3 w-3" />
            Load
          </Button>
          {activePortfolioName ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setCloneDialogName(activePortfolioName);
                setCloneNewName(`${activePortfolioName}-copy`);
                setCloneNameError(null);
              }}
              title="Clone active portfolio"
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
        <div className="rounded-lg border border-slate-200 bg-white p-3 overflow-y-auto">
          <h2 className="text-sm font-semibold text-slate-900 mb-2">Policy Templates</h2>
          <PortfolioTemplateBrowser
            templates={templates}
            selectedIds={selectedTemplateIds}
            onToggleTemplate={toggleTemplate}
          />
        </div>

        {/* Right: Composition panel */}
        <div className="rounded-lg border border-slate-200 bg-white p-3 overflow-y-auto">
          <h2 className="text-sm font-semibold text-slate-900 mb-2">Portfolio Composition</h2>
          {composition.length === 0 ? (
            <div className="border border-slate-200 bg-slate-50 p-6 text-center mt-2">
              <p className="text-sm text-slate-500">
                Add at least 1 policy template to compose a portfolio.
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
            />
          )}
        </div>
      </div>

      {/* Saved portfolios section */}
      {portfolios.length > 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs font-semibold text-slate-700 mb-2">
            Saved Portfolios ({portfolios.length})
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
                  aria-label={`Load portfolio ${p.name}`}
                  title="Load into editor"
                >
                  <FolderOpen className="h-3 w-3" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setCloneDialogName(p.name);
                    setCloneNewName(`${p.name}-copy`);
                    setCloneNameError(null);
                  }}
                  className="shrink-0 border border-slate-200 p-1 text-slate-500 hover:bg-slate-50"
                  aria-label={`Clone portfolio ${p.name}`}
                  title="Clone"
                >
                  <Copy className="h-3 w-3" />
                </button>
                <button
                  type="button"
                  onClick={() => void handleDeletePortfolio(p.name)}
                  className="shrink-0 border border-slate-200 p-1 text-red-500 hover:bg-red-50"
                  aria-label={`Delete portfolio ${p.name}`}
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
          onKeyDown={(e) => { if (e.key === "Escape") setSaveDialogOpen(false); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setSaveDialogOpen(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 id="save-portfolio-dialog-title" className="text-sm font-semibold text-slate-900 mb-4">
              Save Portfolio
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1" htmlFor="save-portfolio-name">
                  Portfolio name <span className="text-red-500">*</span>
                </label>
                <Input
                  id="save-portfolio-name"
                  type="text"
                  value={portfolioSaveName}
                  onChange={(e) => {
                    setPortfolioSaveName(e.target.value);
                    setSaveNameError(validatePortfolioName(e.target.value));
                  }}
                  placeholder="my-portfolio-2030"
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
                  placeholder="Brief description of this portfolio"
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
                onClick={() => setSaveDialogOpen(false)}
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
          onKeyDown={(e) => { if (e.key === "Escape") setLoadDialogOpen(false); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setLoadDialogOpen(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 id="load-portfolio-dialog-title" className="text-sm font-semibold text-slate-900 mb-4">
              Load Portfolio
            </h3>

            {portfolios.length === 0 ? (
              <p className="text-sm text-slate-500">No saved portfolios found.</p>
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
              <Button variant="outline" size="sm" onClick={() => setLoadDialogOpen(false)}>
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
          onKeyDown={(e) => { if (e.key === "Escape") setCloneDialogName(null); }}
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setCloneDialogName(null)}
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
                  setCloneNewName(e.target.value);
                  setCloneNameError(validatePortfolioName(e.target.value));
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
                onClick={() => setCloneDialogName(null)}
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
    </div>
  );
}
