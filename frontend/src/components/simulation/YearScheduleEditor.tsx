/**
 * Year Schedule Editor (Story 17.2, AC-4).
 *
 * Editable table of year/value pairs with:
 * - Add/remove year buttons
 * - Inline number inputs per year-value pair
 * - Duplicate year detection with inline error
 * - Non-numeric input detection with inline error
 * - Rows sorted by year ascending
 * - Mini Recharts line chart preview of the trajectory
 *
 * Default year range 2025–2035. Dynamic scenario-driven range is out of scope.
 */

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const DEFAULT_START_YEAR = 2025;
const DEFAULT_END_YEAR = 2035;

interface YearRow {
  year: string; // Editable as string to allow partial input
  value: string; // Editable as string to allow partial input
  yearError?: string;
  valueError?: string;
}

interface YearScheduleEditorProps {
  schedule: Record<number, number>;
  onChange: (schedule: Record<number, number>) => void;
  unit?: string;
}

function scheduleToRows(schedule: Record<number, number>): YearRow[] {
  return Object.entries(schedule)
    .map(([year, value]) => ({ year: String(year), value: String(value) }))
    .sort((a, b) => Number(a.year) - Number(b.year));
}

function rowsToSchedule(rows: YearRow[]): Record<number, number> | null {
  const result: Record<number, number> = {};
  for (const row of rows) {
    const year = parseInt(row.year, 10);
    const value = parseFloat(row.value);
    if (isNaN(year) || isNaN(value)) return null;
    result[year] = value;
  }
  return result;
}

function validate(rows: YearRow[]): YearRow[] {
  const yearCounts: Record<string, number> = {};
  for (const r of rows) {
    yearCounts[r.year] = (yearCounts[r.year] ?? 0) + 1;
  }

  return rows.map((r) => {
    const yearError =
      !r.year.trim()
        ? "Year required"
        : !/^\d{4}$/.test(r.year.trim())
          ? "Must be a 4-digit year"
          : (yearCounts[r.year] ?? 0) > 1
            ? "Duplicate year"
            : undefined;
    const valueError =
      !r.value.trim()
        ? "Value required"
        : isNaN(parseFloat(r.value))
          ? "Must be a number"
          : undefined;
    return { ...r, yearError, valueError };
  });
}

export function YearScheduleEditor({
  schedule,
  onChange,
  unit = "",
}: YearScheduleEditorProps) {
  const [rows, setRows] = useState<YearRow[]>(() => {
    if (Object.keys(schedule).length > 0) {
      return scheduleToRows(schedule);
    }
    // Default: single row at start year
    return [{ year: String(DEFAULT_START_YEAR), value: "0" }];
  });

  const updateRows = (next: YearRow[]) => {
    const validated = validate(next);
    setRows(validated);

    // Only propagate if all rows are valid
    const hasErrors = validated.some((r) => r.yearError ?? r.valueError);
    if (!hasErrors) {
      const sched = rowsToSchedule(validated);
      if (sched) onChange(sched);
    }
  };

  const addYear = () => {
    // Find next year not already used
    const existingYears = new Set(rows.map((r) => parseInt(r.year, 10)).filter((y) => !isNaN(y)));
    let nextYear = DEFAULT_START_YEAR;
    while (existingYears.has(nextYear) && nextYear <= DEFAULT_END_YEAR + 10) {
      nextYear++;
    }
    updateRows([...rows, { year: String(nextYear), value: "0" }]);
  };

  const removeYear = (index: number) => {
    updateRows(rows.filter((_, i) => i !== index));
  };

  const updateRow = (index: number, field: "year" | "value", val: string) => {
    const next = rows.map((r, i) => (i === index ? { ...r, [field]: val } : r));
    updateRows(next);
  };

  // Chart data — only valid rows
  const chartData = rows
    .filter((r) => !r.yearError && !r.valueError)
    .map((r) => ({ year: parseInt(r.year, 10), value: parseFloat(r.value) }))
    .sort((a, b) => a.year - b.year);

  return (
    <div className="space-y-3">
      {/* Table */}
      <div className="border border-slate-200">
        <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-50 px-3 py-1.5">
          <span className="text-xs font-semibold text-slate-500 w-24">Year</span>
          <span className="text-xs font-semibold text-slate-500 flex-1">
            Value{unit ? ` (${unit})` : ""}
          </span>
          <span className="w-7" aria-hidden="true" />
        </div>

        {rows.length === 0 ? (
          <div className="px-3 py-2 text-xs text-slate-400">No entries. Add a year below.</div>
        ) : (
          rows.map((row, index) => (
            <div
              key={index}
              className="flex items-start gap-2 border-b border-slate-100 px-3 py-1.5 last:border-b-0"
            >
              <div className="w-24 shrink-0">
                <Input
                  type="text"
                  value={row.year}
                  onChange={(e) => updateRow(index, "year", e.target.value)}
                  className={`h-7 text-xs font-mono ${row.yearError ? "border-red-400" : ""}`}
                  aria-label={`Year ${index + 1}`}
                  placeholder="2025"
                />
                {row.yearError ? (
                  <p className="mt-0.5 text-xs text-red-600">{row.yearError}</p>
                ) : null}
              </div>

              <div className="flex-1">
                <Input
                  type="text"
                  value={row.value}
                  onChange={(e) => updateRow(index, "value", e.target.value)}
                  className={`h-7 text-xs font-mono ${row.valueError ? "border-red-400" : ""}`}
                  aria-label={`Value for year ${row.year}`}
                  placeholder="0"
                />
                {row.valueError ? (
                  <p className="mt-0.5 text-xs text-red-600">{row.valueError}</p>
                ) : null}
              </div>

              <button
                type="button"
                onClick={() => removeYear(index)}
                className="mt-0.5 border border-slate-200 p-1 text-red-500 hover:bg-red-50"
                aria-label={`Remove year ${row.year}`}
                title="Remove row"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))
        )}
      </div>

      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={addYear}
        className="text-xs"
      >
        <Plus className="mr-1 h-3 w-3" />
        Add Year
      </Button>

      {/* Mini trajectory chart */}
      {chartData.length >= 2 ? (
        <div className="border border-slate-200 bg-slate-50 p-2">
          <p className="mb-1 text-xs text-slate-500">Trajectory preview</p>
          <ResponsiveContainer width="100%" height={80}>
            <LineChart data={chartData}>
              <XAxis dataKey="year" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} width={40} />
              <Tooltip
                formatter={(val: number | string | undefined) => [
                  `${val ?? ""}${unit ? ` ${unit}` : ""}`,
                  "Value",
                ]}
                labelFormatter={(label) => `Year ${label}`}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={1.5}
                dot={{ r: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}
