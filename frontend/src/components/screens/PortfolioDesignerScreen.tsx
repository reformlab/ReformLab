// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * @deprecated Use PoliciesStageScreen instead (Story 20.3).
 * PoliciesStageScreen is the new canonical Stage 1 inline composition screen.
 * PortfolioDesignerScreen is kept for reference but is no longer used in routing.
 *
 * Portfolio Designer Screen (Story 17.2, AC-1 through AC-6).
 *
 * Step flow: Template Selection → Portfolio Composition → Review & Save.
 * Follows the DataFusionWorkbench step-flow pattern with WorkbenchStepper nav.
 *
 * Integrates:
 * - PortfolioTemplateBrowser for template selection
 * - PortfolioCompositionPanel for ordering/parameter editing
 * - YearScheduleEditor via PortfolioCompositionPanel
 * - Conflict validation before save
 * - Save dialog with portfolio name + description
 */

import { useState, useCallback, useEffect } from "react";
import { ChevronLeft, ChevronRight, Save, AlertTriangle, CheckCircle2, Trash2, FolderOpen, Copy } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { PortfolioTemplateBrowser } from "@/components/simulation/PortfolioTemplateBrowser";
import { PortfolioCompositionPanel } from "@/components/simulation/PortfolioCompositionPanel";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { WorkbenchStepper } from "@/components/simulation/WorkbenchStepper";
import { ApiError } from "@/api/client";
import { clonePortfolio, createPortfolio, deletePortfolio, getPortfolio, validatePortfolio } from "@/api/portfolios";
import type { Template } from "@/data/mock-data";
import type { PortfolioConflict, PortfolioListItem } from "@/api/types";

// ============================================================================
// Step definitions
// ============================================================================

type DesignerStep = "select" | "compose" | "review";

const STEPS: Array<{ key: DesignerStep; label: string }> = [
  { key: "select", label: "1. Select Templates" },
  { key: "compose", label: "2. Compose & Configure" },
  { key: "review", label: "3. Review & Save" },
];

const VALID_STRATEGIES = ["error", "sum", "first_wins", "last_wins", "max"] as const;
type ResolutionStrategy = (typeof VALID_STRATEGIES)[number];

// ============================================================================
// Conflict list display
// ============================================================================

function ConflictList({ conflicts }: { conflicts: PortfolioConflict[] }) {
  if (conflicts.length === 0) {
    return (
      <div className="flex items-center gap-2 border border-emerald-200 bg-emerald-50 p-2 text-sm text-emerald-700">
        <CheckCircle2 className="h-4 w-4 shrink-0" />
        No conflicts detected.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {conflicts.map((c, i) => (
        <div
          key={i}
          className="border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800"
        >
          <div className="flex items-start gap-1.5">
            <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
            <div>
              <p className="font-medium">{c.conflict_type} — {c.parameter_name}</p>
              <p className="mt-0.5 text-amber-700">{c.description}</p>
              <p className="mt-0.5 text-amber-600">
                Policies: {c.policy_indices.map((i) => `#${i + 1}`).join(", ")}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// Portfolio name validator (same regex as backend)
// ============================================================================

const NAME_RE = /^(?:[a-z0-9]{1,64}|[a-z0-9][a-z0-9-]{0,62}[a-z0-9])$/;

function validatePortfolioName(name: string): string | null {
  if (!name.trim()) return "Portfolio name is required";
  if (!NAME_RE.test(name)) {
    return "Name must be a lowercase slug: letters, digits, hyphens only (max 64 chars)";
  }
  if (name === "validate" || name === "clone") {
    return `'${name}' is a reserved name`;
  }
  return null;
}

// ============================================================================
// Main screen
// ============================================================================

interface PortfolioDesignerScreenProps {
  templates: Template[];
  savedPortfolios?: PortfolioListItem[];
  onSaved?: (portfolioName: string) => void;
  onDeleted?: () => void;
}

export function PortfolioDesignerScreen({
  templates,
  savedPortfolios = [],
  onSaved,
  onDeleted,
}: PortfolioDesignerScreenProps) {
  const [activeStep, setActiveStep] = useState<DesignerStep>("select");
  const [selectedTemplateIds, setSelectedTemplateIds] = useState<string[]>([]);
  const [composition, setComposition] = useState<CompositionEntry[]>([]);
  const [resolutionStrategy, setResolutionStrategy] = useState<ResolutionStrategy>("error");
  const [conflicts, setConflicts] = useState<PortfolioConflict[]>([]);
  const [validationLoading, setValidationLoading] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [portfolioName, setPortfolioName] = useState("");
  const [portfolioDesc, setPortfolioDesc] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Sync composition when template selection changes
  useEffect(() => {
    setComposition((prev) => {
      // Add newly selected templates
      const toAdd = selectedTemplateIds
        .filter((id) => !prev.some((e) => e.templateId === id))
        .map((id) => {
          const t = templates.find((tmpl) => tmpl.id === id);
          return { templateId: id, name: t?.name ?? id, parameters: {}, rateSchedule: {} };
        });

      // Remove deselected templates
      const filtered = prev.filter((e) => selectedTemplateIds.includes(e.templateId));

      return [...filtered, ...toAdd];
    });
  }, [selectedTemplateIds, templates]);

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
    setComposition((prev) => prev.filter((_, i) => i !== index));
    setSelectedTemplateIds((prev) => {
      const removed = composition[index]?.templateId;
      return removed ? prev.filter((id) => id !== removed) : prev;
    });
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
            extra_params: {},
          };
        }),
        resolution_strategy: resolutionStrategy,
      });
      setConflicts(result.conflicts);
    } catch {
      // Non-fatal: validation failure doesn't block the UI
      setConflicts([]);
    } finally {
      setValidationLoading(false);
    }
  }, [composition, templates, resolutionStrategy]);

  // Auto-validate when moving to review step
  useEffect(() => {
    if (activeStep === "review") {
      void runValidation();
    }
  }, [activeStep, runValidation]);

  const handleSaveClick = () => {
    void runValidation();
    setSaveDialogOpen(true);
  };

  const handleSave = async () => {
    const err = validatePortfolioName(portfolioName);
    setNameError(err);
    if (err) return;

    if (composition.length < 2) {
      toast.error("Add at least 2 policies before saving");
      return;
    }

    // Block save on errors when resolution_strategy is "error"
    if (resolutionStrategy === "error" && conflicts.length > 0) {
      toast.error("Resolve conflicts before saving", {
        description: "Change resolution strategy or remove conflicting policies",
      });
      return;
    }

    setSaving(true);
    try {
      await createPortfolio({
        name: portfolioName,
        description: portfolioDesc,
        policies: composition.map((e) => {
          const t = templates.find((tmpl) => tmpl.id === e.templateId);
          return {
            name: e.name,
            policy_type: (t?.type ?? "carbon_tax").replace(/-/g, "_"),
            rate_schedule: e.rateSchedule,
            exemptions: [],
            thresholds: [],
            covered_categories: [],
            extra_params: {},
          };
        }),
        resolution_strategy: resolutionStrategy,
      });

      toast.success(`Portfolio '${portfolioName}' saved`);
      setSaveDialogOpen(false);
      onSaved?.(portfolioName);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Save failed", { description: err.message });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePortfolio = async (name: string) => {
    try {
      await deletePortfolio(name);
      toast.success(`Portfolio '${name}' deleted`);
      onDeleted?.();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Delete failed", { description: err.message });
      }
    }
  };

  // Clone dialog state
  const [cloneDialogName, setCloneDialogName] = useState<string | null>(null);
  const [cloneNewName, setCloneNewName] = useState("");
  const [cloneNameError, setCloneNameError] = useState<string | null>(null);
  const [cloning, setCloning] = useState(false);

  const handleLoadPortfolio = async (name: string) => {
    try {
      const detail = await getPortfolio(name);
      // Map portfolio policies back to composition entries
      const entries: CompositionEntry[] = detail.policies.map((p) => {
        // Try to find matching template by policy_type
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
      setActiveStep("compose");
      toast.success(`Loaded portfolio '${name}'`);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Load failed", { description: err.message });
      }
    }
  };

  const handleClonePortfolio = async () => {
    if (!cloneDialogName) return;
    const err = validatePortfolioName(cloneNewName);
    setCloneNameError(err);
    if (err) return;

    setCloning(true);
    try {
      await clonePortfolio(cloneDialogName, { new_name: cloneNewName });
      toast.success(`Cloned '${cloneDialogName}' as '${cloneNewName}'`);
      setCloneDialogName(null);
      setCloneNewName("");
      onSaved?.(cloneNewName);
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Clone failed", { description: err.message });
      }
    } finally {
      setCloning(false);
    }
  };

  const canSave = composition.length >= 2 &&
    (resolutionStrategy !== "error" || conflicts.length === 0);

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <WorkbenchStepper steps={STEPS} activeStep={activeStep} onStepSelect={(key) => setActiveStep(key as DesignerStep)} ariaLabel="Designer steps" />

      <div className="p-3">
        {/* Step 1: Select Templates */}
        {activeStep === "select" ? (
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Select Policy Templates</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Choose 2 or more templates to compose into a portfolio.{" "}
                  <span className="font-medium">{selectedTemplateIds.length} selected.</span>
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => setActiveStep("compose")}
                disabled={selectedTemplateIds.length < 2}
                title={selectedTemplateIds.length < 2 ? "Select at least 2 templates" : undefined}
              >
                Next
                <ChevronRight className="ml-1 h-3 w-3" />
              </Button>
            </div>
            <PortfolioTemplateBrowser
              templates={templates}
              selectedIds={selectedTemplateIds}
              onToggleTemplate={toggleTemplate}
            />
          </section>
        ) : null}

        {/* Step 2: Compose & Configure */}
        {activeStep === "compose" ? (
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Compose & Configure</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Reorder policies, configure parameters, and set conflict resolution.
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setActiveStep("select")}>
                  <ChevronLeft className="mr-1 h-3 w-3" />
                  Back
                </Button>
                <Button
                  size="sm"
                  onClick={() => setActiveStep("review")}
                  disabled={composition.length < 2}
                >
                  Review
                  <ChevronRight className="ml-1 h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Resolution strategy */}
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs font-semibold text-slate-700 mb-1.5">Conflict Resolution</p>
              <Select
                value={resolutionStrategy}
                onChange={(e) => setResolutionStrategy(e.target.value as ResolutionStrategy)}
                className="text-xs"
                aria-label="Resolution strategy"
              >
                {VALID_STRATEGIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </Select>
              <p className="mt-1 text-xs text-slate-500">
                {resolutionStrategy === "error" && "Save blocked if conflicts detected"}
                {resolutionStrategy === "sum" && "Add conflicting rate values"}
                {resolutionStrategy === "first_wins" && "Keep first policy's value"}
                {resolutionStrategy === "last_wins" && "Use last policy's value"}
                {resolutionStrategy === "max" && "Use maximum value"}
              </p>
            </div>

            <PortfolioCompositionPanel
              templates={templates}
              composition={composition}
              onReorder={handleReorder}
              onRemove={handleRemove}
              onParameterChange={handleParameterChange}
              onRateScheduleChange={handleRateScheduleChange}
            />
          </section>
        ) : null}

        {/* Step 3: Review & Save */}
        {activeStep === "review" ? (
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Review & Save</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {composition.length} policies · {resolutionStrategy} strategy
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setActiveStep("compose")}>
                  <ChevronLeft className="mr-1 h-3 w-3" />
                  Back
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveClick}
                  disabled={!canSave}
                  title={
                    !canSave
                      ? composition.length < 2
                        ? "Add at least 2 policies"
                        : "Resolve conflicts first"
                      : undefined
                  }
                >
                  <Save className="mr-1 h-3 w-3" />
                  Save Portfolio
                </Button>
              </div>
            </div>

            {/* Conflict validation */}
            <div className="rounded-lg border border-slate-200 p-3 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-slate-700">Conflict Check</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs h-6"
                  onClick={() => void runValidation()}
                  disabled={validationLoading}
                >
                  {validationLoading ? "Checking..." : "Check Conflicts"}
                </Button>
              </div>
              <ConflictList conflicts={conflicts} />
            </div>

            {/* Policy summary */}
            <div className="rounded-lg border border-slate-200 p-3 space-y-1.5">
              <p className="text-xs font-semibold text-slate-700">Policies ({composition.length})</p>
              {composition.map((entry, i) => {
                const t = templates.find((tmpl) => tmpl.id === entry.templateId);
                return (
                  <div key={i} className="flex items-center gap-2 text-xs text-slate-700">
                    <span className="text-slate-400 font-mono">{i + 1}.</span>
                    <span>{entry.name || t?.name || entry.templateId}</span>
                    {t ? (
                      <Badge variant="default" className="text-xs">{t.type}</Badge>
                    ) : null}
                  </div>
                );
              })}
            </div>

            {/* Saved portfolios */}
            {savedPortfolios.length > 0 ? (
              <div className="rounded-lg border border-slate-200 p-3 space-y-1.5">
                <p className="text-xs font-semibold text-slate-700">
                  Saved Portfolios ({savedPortfolios.length})
                </p>
                {savedPortfolios.map((p) => (
                  <div key={p.name} className="flex items-center gap-2 text-xs text-slate-700">
                    <span className="font-mono flex-1 truncate">{p.name}</span>
                    <Badge variant="default" className="text-xs shrink-0">{p.policy_count} policies</Badge>
                    <span className="text-slate-400 truncate flex-1">{p.description}</span>
                    <button
                      type="button"
                      onClick={() => void handleLoadPortfolio(p.name)}
                      className="shrink-0 border border-slate-200 p-1 text-blue-500 hover:bg-blue-50"
                      aria-label={`Load portfolio ${p.name}`}
                      title="Load into editor"
                    >
                      <FolderOpen className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => { setCloneDialogName(p.name); setCloneNewName(`${p.name}-copy`); setCloneNameError(null); }}
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
            ) : null}
          </section>
        ) : null}
      </div>

      {/* Save dialog */}
      {saveDialogOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Save portfolio"
          className="fixed inset-0 z-50 flex items-center justify-center"
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setSaveDialogOpen(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">Save Portfolio</h3>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1" htmlFor="portfolio-name">
                  Portfolio name <span className="text-red-500">*</span>
                </label>
                <Input
                  id="portfolio-name"
                  type="text"
                  value={portfolioName}
                  onChange={(e) => {
                    setPortfolioName(e.target.value);
                    setNameError(validatePortfolioName(e.target.value));
                  }}
                  placeholder="my-portfolio-2030"
                  className={nameError ? "border-red-400" : ""}
                  aria-describedby={nameError ? "name-error" : undefined}
                />
                {nameError ? (
                  <p id="name-error" className="mt-0.5 text-xs text-red-600">{nameError}</p>
                ) : (
                  <p className="mt-0.5 text-xs text-slate-400">
                    Lowercase slug: letters, digits, hyphens (max 64 chars)
                  </p>
                )}
              </div>

              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1" htmlFor="portfolio-desc">
                  Description
                </label>
                <Input
                  id="portfolio-desc"
                  type="text"
                  value={portfolioDesc}
                  onChange={(e) => setPortfolioDesc(e.target.value)}
                  placeholder="Brief description of this portfolio"
                />
              </div>

              {resolutionStrategy === "error" && conflicts.length > 0 ? (
                <p className="text-xs text-red-600 border border-red-200 bg-red-50 p-2">
                  Cannot save: conflicts detected and resolution strategy is &quot;error&quot;. Change strategy or remove conflicting policies.
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
                disabled={saving || !!nameError || !portfolioName.trim() || (resolutionStrategy === "error" && conflicts.length > 0)}
              >
                {saving ? "Saving..." : "Save"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Clone dialog */}
      {cloneDialogName !== null ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Clone portfolio"
          className="fixed inset-0 z-50 flex items-center justify-center"
        >
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setCloneDialogName(null)}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">
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
                onClick={() => void handleClonePortfolio()}
                disabled={cloning || !!cloneNameError || !cloneNewName.trim()}
              >
                {cloning ? "Cloning..." : "Clone"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
