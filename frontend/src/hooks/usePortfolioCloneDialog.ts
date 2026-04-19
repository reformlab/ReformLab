// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Dialog state and submit handler for cloning saved policy portfolios. */

import { useCallback, useMemo, useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/api/client";
import { clonePortfolio } from "@/api/portfolios";
import type { PortfolioListItem } from "@/api/types";
import { validatePortfolioName } from "@/components/simulation/portfolioValidation";
import { generatePortfolioCloneName } from "@/utils/naming";

interface UsePortfolioCloneDialogParams {
  portfolios: PortfolioListItem[];
  refetchPortfolios: () => Promise<void>;
}

function validateClonePortfolioName(name: string, existingNames: Set<string>): string | null {
  const formatError = validatePortfolioName(name);
  if (formatError) return formatError;
  if (existingNames.has(name)) return "A portfolio with this name already exists";
  return null;
}

export function usePortfolioCloneDialog({
  portfolios,
  refetchPortfolios,
}: UsePortfolioCloneDialogParams) {
  const [cloneDialogName, setCloneDialogName] = useState<string | null>(null);
  const [cloneNewName, setCloneNewName] = useState("");
  const [cloneNameError, setCloneNameError] = useState<string | null>(null);
  const [cloning, setCloning] = useState(false);

  const existingPortfolioNames = useMemo(
    () => new Set(portfolios.map((portfolio) => portfolio.name)),
    [portfolios],
  );

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
    if (!cloneDialogName) return;

    const err = validateClonePortfolioName(cloneNewName, existingPortfolioNames);
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
        setCloneNameError(err.why);
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Clone failed", { description: err.message });
      }
    } finally {
      setCloning(false);
    }
  }, [cloneDialogName, cloneNewName, existingPortfolioNames, refetchPortfolios]);

  return {
    cloneDialogName,
    cloneNewName,
    cloneNameError,
    cloning,
    openCloneDialog,
    closeCloneDialog,
    handleCloneNameChange,
    handleClone,
  };
}
