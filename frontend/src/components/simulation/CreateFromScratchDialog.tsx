// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * CreateFromScratchDialog — Story 25.3.
 *
 * Three-step wizard for creating policies from scratch:
 * Step 1: Select policy type (Tax / Subsidy / Transfer)
 * Step 2: Select category (filtered by compatible_types)
 * Step 3: Confirm and create
 */

import { useState, useCallback, useEffect } from "react";
import { X, ChevronRight, ChevronLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TYPE_COLORS, TYPE_LABELS } from "@/components/simulation/typeConstants";
import { cn } from "@/lib/utils";
import type { Category } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export type PolicyType = "tax" | "subsidy" | "transfer";
export type PolicyTypeLabel = "Tax" | "Subsidy" | "Transfer";

interface CreateFromScratchDialogProps {
  categories: Category[] | null;
  onCreatePolicy: (policyType: PolicyType, categoryId: string) => Promise<void> | void;
  onClose: () => void;
}

// ============================================================================
// Policy type definitions (Step 1)
// ============================================================================

const POLICY_TYPES: Array<{
  id: PolicyType;
  label: PolicyTypeLabel;
  description: string;
  colorClass: string;
}> = [
  {
    id: "tax",
    label: "Tax",
    description: "Charges on emissions, consumption, or activities",
    colorClass: "border-amber-300 bg-amber-50 hover:bg-amber-100",
  },
  {
    id: "subsidy",
    label: "Subsidy",
    description: "Payments to encourage behavior",
    colorClass: "border-emerald-300 bg-emerald-50 hover:bg-emerald-100",
  },
  {
    id: "transfer",
    label: "Transfer",
    description: "Means-tested social payments",
    colorClass: "border-blue-300 bg-blue-50 hover:bg-blue-100",
  },
];

// ============================================================================
// CreateFromScratchDialog Component
// ============================================================================

export function CreateFromScratchDialog({
  categories,
  onCreatePolicy,
  onClose,
}: CreateFromScratchDialogProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedType, setSelectedType] = useState<PolicyType | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Step 2: Filter categories by compatible_types
  const compatibleCategories = categories
    ? categories.filter((cat) =>
      selectedType ? cat.compatible_types.includes(selectedType) : false,
    )
    : [];

  // Step 3: Generate policy name from type and category
  const policyName = useCallback(() => {
    if (!selectedType || !selectedCategoryId) return "";
    const typeLabel = TYPE_LABELS[selectedType];
    const category = categories?.find((c) => c.id === selectedCategoryId);
    const categoryLabel = category?.label ?? selectedCategoryId;
    return `${typeLabel} — ${categoryLabel}`;
  }, [selectedType, selectedCategoryId, categories]);

  // Step 3: Handle create policy
  const handleCreate = useCallback(async () => {
    if (selectedType && selectedCategoryId) {
      setIsCreating(true);
      try {
        await onCreatePolicy(selectedType, selectedCategoryId);
        onClose();
      } finally {
        setIsCreating(false);
      }
    }
  }, [selectedType, selectedCategoryId, onCreatePolicy, onClose]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Step navigation
  const canProceedToStep2 = selectedType !== null &&
    categories !== null &&
    categories.length > 0 &&
    compatibleCategories.length > 0;

  const canProceedToStep3 = selectedType !== null &&
    selectedCategoryId !== null;

  const canCreate = canProceedToStep3;

  // AC-8: Categories not loaded
  if (categories === null || categories.length === 0) {
    return (
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="from-scratch-title"
        className="fixed inset-0 z-50 flex items-center justify-center"
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div className="absolute inset-0 bg-black/30" aria-hidden="true" />
        <div className="relative z-10 w-full max-w-lg rounded-lg border border-slate-200 bg-white p-6 shadow-lg">
          <h3 id="from-scratch-title" className="text-sm font-semibold text-slate-900 mb-4">
            Create Policy from Scratch
          </h3>
          <div className="border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm text-amber-900">
              Categories not loaded — cannot create from scratch. Try again later.
            </p>
          </div>
          <div className="mt-4 flex justify-end">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="from-scratch-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="absolute inset-0 bg-black/30" aria-hidden="true" />
      <div className="relative z-10 w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 p-4">
          <h3 id="from-scratch-title" className="text-sm font-semibold text-slate-900">
            Create Policy from Scratch
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 p-1 text-slate-500 hover:text-slate-700"
            aria-label="Close dialog"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 px-4 pt-4 pb-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-1">
              <div
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium",
                  step === s
                    ? "bg-blue-600 text-white"
                    : step > s
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-100 text-slate-500",
                )}
              >
                {step > s ? <Check className="h-3 w-3" /> : s}
              </div>
              <span className="text-xs text-slate-600">
                {s === 1 && "Type"}
                {s === 2 && "Category"}
                {s === 3 && "Confirm"}
              </span>
              {s < 3 && (
                <ChevronRight className="h-3 w-3 text-slate-400" />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="p-4">
          {/* Step 1: Policy Type Selection */}
          {step === 1 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-700">
                Select the type of policy you want to create:
              </p>
              <div className="grid grid-cols-1 gap-3">
                {POLICY_TYPES.map((type) => (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setSelectedType(type.id)}
                    className={cn(
                      "relative rounded-lg border-2 p-4 text-left transition-colors",
                      selectedType === type.id
                        ? `${type.colorClass} border-current`
                        : "border-slate-200 bg-white hover:bg-slate-50",
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-slate-900">
                          {type.label}
                        </h4>
                        <p className="mt-1 text-xs text-slate-600">
                          {type.description}
                        </p>
                      </div>
                      {selectedType === type.id && (
                        <Check className="h-5 w-5 text-slate-700" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Category Selection */}
          {step === 2 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-700">
                Select a category for your{" "}
                <span className={cn(
                  "font-semibold",
                  selectedType === "tax" && "text-amber-700",
                  selectedType === "subsidy" && "text-emerald-700",
                  selectedType === "transfer" && "text-blue-700",
                )}>
                  {selectedType && TYPE_LABELS[selectedType]}
                </span>{" "}
                policy:
              </p>

              {/* AC-2: Empty state when no compatible categories */}
              {compatibleCategories.length === 0 ? (
                <div className="border border-amber-200 bg-amber-50 p-4">
                  <p className="text-sm text-amber-900">
                    No categories available for {TYPE_LABELS[selectedType || ""]} policies
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {compatibleCategories.map((category) => (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => setSelectedCategoryId(category.id)}
                      className={cn(
                        "relative rounded-lg border-2 p-3 text-left transition-colors",
                        selectedCategoryId === category.id
                          ? "border-blue-500 bg-blue-50"
                          : "border-slate-200 bg-white hover:bg-slate-50",
                      )}
                    >
                      <div className="flex items-start gap-2">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-slate-900 truncate">
                            {category.label}
                          </h4>
                          <p className="mt-0.5 text-xs text-slate-600 line-clamp-2">
                            {category.description}
                          </p>
                        </div>
                        {selectedCategoryId === category.id && (
                          <Check className="h-4 w-4 text-blue-600 shrink-0" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 3: Confirmation */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-slate-700">
                Review and confirm your new policy:
              </p>

              <div className="border border-slate-200 rounded-lg bg-slate-50 p-4 space-y-3">
                {/* Policy name */}
                <div>
                  <p className="text-xs font-medium text-slate-700 mb-1">Policy Name</p>
                  <p className="text-sm font-semibold text-slate-900">
                    {policyName()}
                  </p>
                </div>

                {/* Type badge */}
                <div>
                  <p className="text-xs font-medium text-slate-700 mb-1">Policy Type</p>
                  {selectedType && (
                    <Badge
                      className={TYPE_COLORS[selectedType] ?? "bg-slate-100 text-slate-700"}
                    >
                      {TYPE_LABELS[selectedType]}
                    </Badge>
                  )}
                </div>

                {/* Category badge */}
                <div>
                  <p className="text-xs font-medium text-slate-700 mb-1">Category</p>
                  {selectedCategoryId && (
                    <Badge className="bg-slate-100 text-slate-800">
                      {categories?.find((c) => c.id === selectedCategoryId)?.label ?? selectedCategoryId}
                    </Badge>
                  )}
                </div>

                {/* Default parameter groups */}
                {selectedType && (
                  <div>
                    <p className="text-xs font-medium text-slate-700 mb-1">Default Parameter Groups</p>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedType === "tax" && (
                        <>
                          <Badge variant="outline" className="text-xs">Mechanism</Badge>
                          <Badge variant="outline" className="text-xs">Eligibility</Badge>
                          <Badge variant="outline" className="text-xs">Schedule</Badge>
                          <Badge variant="outline" className="text-xs">Redistribution</Badge>
                        </>
                      )}
                      {(selectedType === "subsidy" || selectedType === "transfer") && (
                        <>
                          <Badge variant="outline" className="text-xs">Mechanism</Badge>
                          <Badge variant="outline" className="text-xs">Eligibility</Badge>
                          <Badge variant="outline" className="text-xs">Schedule</Badge>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between border-t border-slate-200 p-4">
          <div>
            {step > 1 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep((step - 1) as 1 | 2)}
              >
                <ChevronLeft className="h-3 w-3 mr-1" />
                Back
              </Button>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              Cancel
            </Button>

            {step === 1 && (
              <Button
                size="sm"
                onClick={() => setStep(2)}
                disabled={!canProceedToStep2}
              >
                Next
                <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            )}

            {step === 2 && (
              <Button
                size="sm"
                onClick={() => setStep(3)}
                disabled={!canProceedToStep3}
              >
                Next
                <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            )}

            {step === 3 && (
              <Button
                size="sm"
                onClick={handleCreate}
                disabled={!canCreate || isCreating}
              >
                {isCreating ? "Creating..." : "Create Policy"}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
