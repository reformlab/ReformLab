// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a logit model identifier (e.g., "multinomial_logit") for display.
 * Replaces underscores with spaces and capitalizes each word.
 * Story 26.2 — AC-4: Model name should be formatted for display.
 */
export function formatLogitModelLabel(model: string): string {
  return model
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
