// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Centralized formatting utilities for numbers, currency, percentages, dates, and timestamps.
 *
 * Story 27.10, AC-1 through AC-7.
 * All numeric, currency, date, timestamp, and status values display consistently.
 */

// ============================================================================
// Types
// ============================================================================

export interface NumberFormatOptions {
  /** Number of decimal places. Default: 0. */
  decimals?: number;
  /** Locale for formatting. Default: undefined (user locale). */
  locale?: string;
}

export interface CurrencyFormatOptions extends NumberFormatOptions {
  /** Currency symbol. Default: "€". */
  symbol?: string;
  /** Append "/yr" suffix. Default: false. */
  perYear?: boolean;
}

export interface PercentFormatOptions {
  /** Number of decimal places. Default: 0. */
  decimals?: number;
  /** Multiply input by 100. Default: true. */
  multiplyBy100?: boolean;
}

export type TimestampStyle = "short" | "full";

// ============================================================================
// Number formatting
// ============================================================================

/**
 * Format a number for display with thousands separator.
 * @example formatNumber(1234.56) // "1,235"
 * @example formatNumber(1234.56, { decimals: 2 }) // "1,234.56"
 */
export function formatNumber(
  value: number | null | undefined,
  options: NumberFormatOptions = {},
): string {
  if (value === null || value === undefined) return "—";
  if (Number.isNaN(value)) return "NaN";
  if (!Number.isFinite(value)) return value > 0 ? "∞" : "-∞";

  const { decimals = 0, locale } = options;
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

// ============================================================================
// Currency formatting
// ============================================================================

/**
 * Format a currency value for display.
 * @example formatCurrency(1234.56) // "€1,235"
 * @example formatCurrency(1234.56, { perYear: true }) // "€1,235/yr"
 */
export function formatCurrency(
  value: number | null | undefined,
  options: CurrencyFormatOptions = {},
): string {
  if (value === null || value === undefined) return "—";
  if (Number.isNaN(value)) return "NaN";
  if (!Number.isFinite(value)) return value > 0 ? "∞" : "-∞";

  const { decimals = 0, locale, symbol = "€", perYear = false } = options;
  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);

  const sign = value < 0 ? "-" : "";
  const absFormatted = formatted.startsWith("-") ? formatted.slice(1) : formatted;
  const suffix = perYear ? "/yr" : "";

  return `${sign}${symbol}${absFormatted}${suffix}`;
}

// ============================================================================
// Percentage formatting
// ============================================================================

/**
 * Format a percentage value for display.
 * @example formatPercent(0.44) // "44%"
 * @example formatPercent(0.444, { decimals: 1 }) // "44.4%"
 */
export function formatPercent(
  value: number | null | undefined,
  options: PercentFormatOptions = {},
): string {
  if (value === null || value === undefined) return "—";
  if (Number.isNaN(value)) return "NaN";
  if (!Number.isFinite(value)) return value > 0 ? "∞%" : "-∞%";

  const { decimals = 0, multiplyBy100 = true } = options;
  const multiplied = multiplyBy100 ? value * 100 : value;

  return `${multiplied.toFixed(decimals)}%`;
}

// ============================================================================
// Date formatting
// ============================================================================

/**
 * Format a date for display.
 * @example formatDate("2026-05-13") // "May 13, 2026"
 */
export function formatDate(value: string | Date | null | undefined): string {
  if (value === null || value === undefined) return "—";

  const date = typeof value === "string" ? new Date(value) : value;

  if (isNaN(date.getTime())) {
    // Return original string for invalid dates
    return typeof value === "string" ? value : String(value);
  }

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}

// ============================================================================
// Timestamp formatting
// ============================================================================

/**
 * Format a timestamp with time for display.
 * @example formatTimestamp("2026-05-13T14:48:00Z") // "May 13, 2026, 02:48 PM"
 * @example formatTimestamp("2026-05-13T14:48:00Z", "full") // "May 13, 2026, 02:48:00 PM"
 */
export function formatTimestamp(
  value: string | Date | null | undefined,
  style: TimestampStyle = "short",
): string {
  if (value === null || value === undefined) return "—";

  const date = typeof value === "string" ? new Date(value) : value;

  if (isNaN(date.getTime())) {
    return typeof value === "string" ? value : String(value);
  }

  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  };

  if (style === "full") {
    options.second = "2-digit";
  }

  return new Intl.DateTimeFormat(undefined, options).format(date);
}

// ============================================================================
// Compact/large number formatting
// ============================================================================

/**
 * Format a large number compactly with B/M/k suffixes.
 * Matches MultiRunChart.tsx behavior exactly.
 * @example formatLargeNumber(2100000000) // "2.1B"
 * @example formatLargeNumber(1500000) // "1.5M"
 * @example formatLargeNumber(2500) // "2.5k"
 */
export function formatLargeNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (Number.isNaN(value)) return "NaN";
  if (!Number.isFinite(value)) return value > 0 ? "∞" : "-∞";

  const abs = Math.abs(value);

  if (abs < 1) return "0";
  if (abs >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}k`;

  return value.toFixed(0);
}
