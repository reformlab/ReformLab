// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Dialog state and submit handler for saving composed policy portfolios. */

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/api/client";
import { createPortfolio } from "@/api/portfolios";
import type { PortfolioConflict } from "@/api/types";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { validatePortfolioName } from "@/components/simulation/portfolioValidation";
import type { Template } from "@/data/mock-data";
import { generatePortfolioSuggestion } from "@/utils/naming";

interface LoadedPortfolioRef {
  current: string | null;
}

interface UsePortfolioSaveDialogParams {
  templates: Template[];
  composition: CompositionEntry[];
  resolutionStrategy: string;
  conflicts: PortfolioConflict[];
  loadedPortfolioRef: LoadedPortfolioRef;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
  refetchPortfolios: () => Promise<void>;
}

function buildPortfolioPolicies(
  composition: CompositionEntry[],
  templates: Template[],
) {
  return composition.map((entry) => {
    const template = templates.find((tmpl) => tmpl.id === entry.templateId);
    return {
      name: entry.name,
      policy_type: (template?.type ?? "carbon_tax").replace(/-/g, "_"),
      rate_schedule: entry.rateSchedule,
      exemptions: [],
      thresholds: [],
      covered_categories: [],
      extra_params: entry.parameters as Record<string, unknown>,
      // Story 25.3: Optional fields for from-scratch policies
      category_id: entry.category_id,
      parameter_groups: entry.parameter_groups,
      // Story 25.4: Editable parameter groups
      editable_parameter_groups: entry.editableParameterGroups,
    };
  });
}

export function usePortfolioSaveDialog({
  templates,
  composition,
  resolutionStrategy,
  conflicts,
  loadedPortfolioRef,
  setActivePortfolioName,
  updateScenarioPortfolioName,
  setSelectedPortfolioName,
  refetchPortfolios,
}: UsePortfolioSaveDialogParams) {
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [portfolioSaveName, setPortfolioSaveName] = useState("");
  const [portfolioSaveDesc, setPortfolioSaveDesc] = useState("");
  const [saveNameError, setSaveNameError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveDialogNameManuallyEdited, setSaveDialogNameManuallyEdited] = useState(false);

  useEffect(() => {
    if (!saveDialogOpen || saveDialogNameManuallyEdited) return;
    const suggestion = generatePortfolioSuggestion(templates, composition);
    setPortfolioSaveName(suggestion);
  }, [composition, templates, saveDialogOpen, saveDialogNameManuallyEdited]);

  const openSaveDialog = useCallback(() => {
    const suggestion = generatePortfolioSuggestion(templates, composition);
    setPortfolioSaveName(suggestion);
    setPortfolioSaveDesc("");
    setSaveNameError(null);
    setSaveDialogNameManuallyEdited(false);
    setSaveDialogOpen(true);
  }, [composition, templates]);

  const closeSaveDialog = useCallback(() => {
    setSaveDialogOpen(false);
    setSaveDialogNameManuallyEdited(false);
  }, []);

  const handleSaveNameChange = useCallback((name: string) => {
    setSaveDialogNameManuallyEdited(true);
    setPortfolioSaveName(name);
    setSaveNameError(validatePortfolioName(name));
  }, []);

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
        policies: buildPortfolioPolicies(composition, templates),
        resolution_strategy: resolutionStrategy,
      });

      loadedPortfolioRef.current = portfolioSaveName;
      setActivePortfolioName(portfolioSaveName);
      updateScenarioPortfolioName(portfolioSaveName);
      setSelectedPortfolioName(portfolioSaveName);
      void refetchPortfolios();

      toast.success(`Policy set '${portfolioSaveName}' saved`);
      setSaveDialogOpen(false);
      setPortfolioSaveName("");
      setPortfolioSaveDesc("");
      setSaveDialogNameManuallyEdited(false);
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
    loadedPortfolioRef,
    setActivePortfolioName,
    updateScenarioPortfolioName,
    setSelectedPortfolioName,
    refetchPortfolios,
  ]);

  return {
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
  };
}
