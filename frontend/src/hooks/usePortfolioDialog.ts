// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unified portfolio dialog hook (Story 27.11, Task 4).
 *
 * Consolidates three separate hooks (usePortfolioSaveDialog, usePortfolioLoadDialog,
 * usePortfolioCloneDialog) into a single hook with mode-specific behavior.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/api/client";
import { clonePortfolio, createPortfolio, getPortfolio, updatePortfolio } from "@/api/portfolios";
import type {
  Category,
  CompositionEntry,
  EditableParameterGroup,
  PortfolioConflict,
  PortfolioListItem,
  PortfolioPolicyItem,
} from "@/api/types";
import { validatePortfolioName } from "@/components/simulation/portfolioValidation";
import type { Template } from "@/data/mock-data";
import { generatePortfolioCloneName, generatePortfolioSuggestion } from "@/utils/naming";
import { normalizePolicyType } from "@/utils/policyTypes";

export type PortfolioDialogMode = "save" | "load" | "clone";

export interface LoadedPortfolioRef {
  current: string | null;
}

const DEFAULT_PARAM_ASSIGNMENTS: Record<string, string[]> = {
  "Mechanism": ["rate", "unit"],
  "Eligibility": ["threshold", "ceiling", "income_cap"],
  "Schedule": [],
  "Redistribution": ["divisible", "recipients", "income_weights"],
};

function buildPortfolioPolicies(composition: CompositionEntry[], templates: Template[]) {
  return composition.map((entry) => {
    const template = templates.find((tmpl) => tmpl.id === entry.templateId);
    const policyType = entry.policy_type ?? template?.type ?? "carbon_tax";

    return {
      name: entry.name,
      policy_type: normalizePolicyType(policyType),
      rate_schedule: entry.rateSchedule,
      exemptions: [],
      thresholds: [],
      covered_categories: [],
      extra_params: entry.parameters as Record<string, unknown>,
      category_id: entry.category_id,
      parameter_groups: entry.parameter_groups,
      editable_parameter_groups: entry.editableParameterGroups,
    };
  });
}

function validateClonePortfolioName(name: string, existingNames: Set<string>): string | null {
  const formatError = validatePortfolioName(name);
  if (formatError) return formatError;
  if (existingNames.has(name)) return "A policy set with this name already exists";
  return null;
}

export interface SaveDialogParams {
  templates: Template[];
  composition: CompositionEntry[];
  resolutionStrategy: string;
  conflicts: PortfolioConflict[];
  loadedPortfolioRef: LoadedPortfolioRef;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
  refetchPortfolios: () => Promise<void>;
  onSavedSuccessfully?: () => void;
  categories?: Category[] | null;
}

export interface LoadDialogParams<ResolutionStrategy extends string> {
  templates: Template[];
  activeScenarioPortfolioName: string | null | undefined;
  compositionLength: number;
  validStrategies: readonly ResolutionStrategy[];
  defaultResolutionStrategy: ResolutionStrategy;
  loadedPortfolioRef: LoadedPortfolioRef;
  setComposition: (composition: CompositionEntry[]) => void;
  setResolutionStrategy: (strategy: ResolutionStrategy) => void;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
  setInstanceCounter?: (value: number) => void;
  onLoadedSuccessfully?: () => void;
}

export interface CloneDialogParams {
  portfolios: PortfolioListItem[];
  refetchPortfolios: () => Promise<void>;
}

export interface SaveDialogState {
  mode: "save";
  saveDialogOpen: boolean;
  portfolioSaveName: string;
  portfolioSaveDesc: string;
  saveNameError: string | null;
  saving: boolean;
  openSaveDialog: () => void;
  closeSaveDialog: () => void;
  handleSaveNameChange: (name: string) => void;
  setPortfolioSaveDesc: (desc: string) => void;
  handleSave: () => Promise<void>;
}

export interface LoadDialogState {
  mode: "load";
  loadDialogOpen: boolean;
  openLoadDialog: () => void;
  closeLoadDialog: () => void;
  handleLoad: (name: string) => Promise<boolean>;
}

export interface CloneDialogState {
  mode: "clone";
  cloneDialogOpen: boolean;
  cloneDialogName: string | null;
  cloneNewName: string;
  cloneNameError: string | null;
  cloning: boolean;
  openCloneDialog: (name: string) => void;
  closeCloneDialog: () => void;
  handleCloneNameChange: (name: string) => void;
  handleClone: () => Promise<void>;
}

export type PortfolioDialogState =
  | SaveDialogState
  | LoadDialogState
  | CloneDialogState;

export function usePortfolioDialog(
  mode: "save",
  params: Omit<SaveDialogParams, "mode">,
): SaveDialogState;
export function usePortfolioDialog<ResolutionStrategy extends string>(
  mode: "load",
  params: Omit<LoadDialogParams<ResolutionStrategy>, "mode">,
): LoadDialogState;
export function usePortfolioDialog(
  mode: "clone",
  params: Omit<CloneDialogParams, "mode">,
): CloneDialogState;
export function usePortfolioDialog<ResolutionStrategy extends string>(
  mode: PortfolioDialogMode,
  params: Omit<SaveDialogParams | LoadDialogParams<ResolutionStrategy> | CloneDialogParams, "mode">,
): PortfolioDialogState {
  const saveParams = mode === "save" ? (params as Omit<SaveDialogParams, "mode">) : null;
  const loadParams = mode === "load"
    ? (params as Omit<LoadDialogParams<ResolutionStrategy>, "mode">)
    : null;
  const cloneParams = mode === "clone" ? (params as Omit<CloneDialogParams, "mode">) : null;

  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [portfolioSaveName, setPortfolioSaveName] = useState("");
  const [portfolioSaveDesc, setPortfolioSaveDesc] = useState("");
  const [saveNameError, setSaveNameError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveDialogNameManuallyEdited, setSaveDialogNameManuallyEdited] = useState(false);

  const [loadDialogOpen, setLoadDialogOpen] = useState(false);

  const [cloneDialogName, setCloneDialogName] = useState<string | null>(null);
  const [cloneNewName, setCloneNewName] = useState("");
  const [cloneNameError, setCloneNameError] = useState<string | null>(null);
  const [cloning, setCloning] = useState(false);

  const existingPortfolioNames = useMemo(
    () => new Set((cloneParams?.portfolios ?? []).map((portfolio) => portfolio.name)),
    [cloneParams?.portfolios],
  );

  useEffect(() => {
    if (!saveParams || !saveDialogOpen || saveDialogNameManuallyEdited) return;
    const suggestion = generatePortfolioSuggestion(
      saveParams.templates,
      saveParams.composition,
      saveParams.categories,
    );
    setPortfolioSaveName(suggestion);
  }, [saveDialogNameManuallyEdited, saveDialogOpen, saveParams]);

  const openSaveDialog = useCallback(() => {
    if (!saveParams) return;

    const suggestion = generatePortfolioSuggestion(
      saveParams.templates,
      saveParams.composition,
      saveParams.categories,
    );
    setPortfolioSaveName(suggestion);
    setPortfolioSaveDesc("");
    setSaveNameError(null);
    setSaveDialogNameManuallyEdited(false);
    setSaveDialogOpen(true);
  }, [saveParams]);

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
    if (!saveParams) return;

    const err = validatePortfolioName(portfolioSaveName);
    setSaveNameError(err);
    if (err) return;

    if (saveParams.resolutionStrategy === "error" && saveParams.conflicts.length > 0) {
      toast.error("Resolve conflicts before saving", {
        description: "Change resolution strategy or remove conflicting policies",
      });
      return;
    }

    setSaving(true);
    try {
      const isUpdate = portfolioSaveName === saveParams.loadedPortfolioRef.current;
      const portfolioData = {
        name: portfolioSaveName,
        description: portfolioSaveDesc,
        policies: buildPortfolioPolicies(saveParams.composition, saveParams.templates),
        resolution_strategy: saveParams.resolutionStrategy,
      };

      if (isUpdate) {
        await updatePortfolio(portfolioSaveName, portfolioData);
        toast.success(`Policy set '${portfolioSaveName}' updated`);
      } else {
        await createPortfolio(portfolioData);
        toast.success(`Policy set '${portfolioSaveName}' saved`);
      }

      saveParams.loadedPortfolioRef.current = portfolioSaveName;
      saveParams.setActivePortfolioName(portfolioSaveName);
      saveParams.updateScenarioPortfolioName(portfolioSaveName);
      saveParams.setSelectedPortfolioName(portfolioSaveName);
      void saveParams.refetchPortfolios();

      setSaveDialogOpen(false);
      setPortfolioSaveName("");
      setPortfolioSaveDesc("");
      setSaveDialogNameManuallyEdited(false);
      saveParams.onSavedSuccessfully?.();
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Save failed", { description: err.message });
      }
    } finally {
      setSaving(false);
    }
  }, [portfolioSaveDesc, portfolioSaveName, saveParams]);

  const loadPortfolioIntoComposition = useCallback(async (
    name: string,
    options?: { silent?: boolean },
  ): Promise<boolean> => {
    if (!loadParams) return false;

    try {
      const detail = await getPortfolio(name);
      const entries: CompositionEntry[] = detail.policies.map((policy, index) => {
        // Fallback: when saved portfolio references a policy type that doesn't
        // match any current template, use policy_type as templateId. This allows
        // the portfolio to load but may cause issues if the policy is edited and
        // saved (will save with wrong templateId). Unmatched policies should be rare.
        const template = loadParams.templates.find(
          (tmpl) => normalizePolicyType(tmpl.type) === policy.policy_type,
        );
        const templateId = template?.id ?? policy.policy_type;

        if (!template) {
          console.warn(`Template not found for policy type "${policy.policy_type}", using fallback`);
        }
        const policyParameterGroups = (
          policy as PortfolioPolicyItem & { parameter_groups?: string[] }
        ).parameter_groups;
        let editableParameterGroups: EditableParameterGroup[] | undefined;
        const policyEditableGroups = (
          policy as PortfolioPolicyItem & { editable_parameter_groups?: EditableParameterGroup[] }
        ).editable_parameter_groups;

        if (policyEditableGroups && policyEditableGroups.length > 0) {
          editableParameterGroups = policyEditableGroups;
        } else if (policyParameterGroups && policyParameterGroups.length > 0) {
          editableParameterGroups = policyParameterGroups.map((groupName, idx) => ({
            id: `group-${idx}`,
            name: groupName,
            parameterIds: DEFAULT_PARAM_ASSIGNMENTS[groupName] ?? [],
          }));
        }

        return {
          instanceId: `${templateId}-ins${index}`,
          templateId,
          name: policy.name,
          parameters: policy.parameters,
          rateSchedule: policy.rate_schedule,
          policy_type: policy.policy_type,
          category_id: policy.category_id,
          parameter_groups: policyParameterGroups,
          editableParameterGroups,
        };
      });

      loadParams.setComposition(entries);
      if (loadParams.setInstanceCounter) {
        loadParams.setInstanceCounter(detail.policies.length);
      }
      loadParams.setResolutionStrategy(
        loadParams.validStrategies.includes(detail.resolution_strategy as ResolutionStrategy)
          ? (detail.resolution_strategy as ResolutionStrategy)
          : loadParams.defaultResolutionStrategy,
      );
      loadParams.setActivePortfolioName(name);
      return true;
    } catch (err) {
      if (!options?.silent) {
        if (err instanceof ApiError) {
          toast.warning(`Could not load policy set '${name}': ${err.why}`);
        } else {
          toast.warning(`Could not load policy set '${name}'`);
        }
      }
      return false;
    }
  }, [loadParams]);

  useEffect(() => {
    if (!loadParams?.activeScenarioPortfolioName) return;
    if (loadParams.compositionLength > 0) return;
    if (loadParams.loadedPortfolioRef.current === loadParams.activeScenarioPortfolioName) return;

    loadParams.loadedPortfolioRef.current = loadParams.activeScenarioPortfolioName;
    void loadPortfolioIntoComposition(loadParams.activeScenarioPortfolioName, { silent: true }).then((loaded) => {
      if (!loaded && loadParams.loadedPortfolioRef.current === loadParams.activeScenarioPortfolioName) {
        loadParams.loadedPortfolioRef.current = null;
      }
      if (loaded) {
        loadParams.onLoadedSuccessfully?.();
      }
    });
  }, [loadParams, loadPortfolioIntoComposition]);

  const openLoadDialog = useCallback(() => {
    setLoadDialogOpen(true);
  }, []);

  const closeLoadDialog = useCallback(() => {
    setLoadDialogOpen(false);
  }, []);

  const handleLoad = useCallback(async (name: string) => {
    if (!loadParams) return false;

    const ok = await loadPortfolioIntoComposition(name);
    if (!ok) return false;

    loadParams.loadedPortfolioRef.current = name;
    loadParams.updateScenarioPortfolioName(name);
    loadParams.setSelectedPortfolioName(name);
    setLoadDialogOpen(false);
    toast.success(`Loaded policy set '${name}'`);
    loadParams.onLoadedSuccessfully?.();
    return true;
  }, [loadParams, loadPortfolioIntoComposition]);

  const openCloneDialog = useCallback((name: string) => {
    const cloneName = generatePortfolioCloneName(name, existingPortfolioNames);
    setCloneDialogName(name);
    setCloneNewName(cloneName);
    setCloneNameError(null);
  }, [existingPortfolioNames]);

  const closeCloneDialog = useCallback(() => {
    setCloneDialogName(null);
  }, []);

  const handleCloneNameChange = useCallback((name: string) => {
    setCloneNewName(name);
    setCloneNameError(validateClonePortfolioName(name, existingPortfolioNames));
  }, [existingPortfolioNames]);

  const handleClone = useCallback(async () => {
    if (!cloneParams || !cloneDialogName) return;

    const err = validateClonePortfolioName(cloneNewName, existingPortfolioNames);
    setCloneNameError(err);
    if (err) return;

    setCloning(true);
    try {
      await clonePortfolio(cloneDialogName, { new_name: cloneNewName });
      void cloneParams.refetchPortfolios();
      toast.success(`Policy set '${cloneDialogName}' cloned as '${cloneNewName}'`);
      setCloneDialogName(null);
      setCloneNewName("");
    } catch (err) {
      if (err instanceof ApiError) {
        setCloneNameError(err.why);
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Clone failed", { description: err.message });
      }
    } finally {
      setCloning(false);
    }
  }, [cloneDialogName, cloneNewName, cloneParams, existingPortfolioNames]);

  switch (mode) {
    case "save":
      return {
        mode: "save",
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
    case "load":
      return {
        mode: "load",
        loadDialogOpen,
        openLoadDialog,
        closeLoadDialog,
        handleLoad,
      };
    case "clone":
      return {
        mode: "clone",
        cloneDialogOpen: cloneDialogName !== null,
        cloneDialogName,
        cloneNewName,
        cloneNameError,
        cloning,
        openCloneDialog,
        closeCloneDialog,
        handleCloneNameChange,
        handleClone,
      };
    default:
      throw new Error(`Invalid mode: ${mode satisfies never}`);
  }
}
