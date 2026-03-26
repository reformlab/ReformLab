// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationDataTable — TanStack Table-based paginated, sortable, filterable table.
 *
 * Table View tab within the Full Data Explorer.
 * Story 20.4 — AC-3(a).
 */

import { useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type PaginationState,
} from "@tanstack/react-table";
import { ArrowUp, ArrowDown, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ColumnInfo } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface PopulationDataTableProps {
  rows: Record<string, unknown>[];
  columns: ColumnInfo[];
  totalRows: number;
}

// ============================================================================
// Column type badge
// ============================================================================

function TypeBadge({ type }: { type: string }) {
  const variant =
    type === "numeric" ? "secondary" : type === "categorical" ? "outline" : "default";
  return (
    <Badge variant={variant} className="ml-1 text-[10px] px-1 py-0">
      {type.slice(0, 3)}
    </Badge>
  );
}

// ============================================================================
// Column header with sort
// ============================================================================

interface SortableHeaderProps {
  label: string;
  colType: string;
  isSorted: "asc" | "desc" | false;
  onSort: () => void;
}

function SortableHeader({ label, colType, isSorted, onSort }: SortableHeaderProps) {
  const icon =
    isSorted === "asc" ? (
      <ArrowUp className="h-3 w-3 text-blue-500" />
    ) : isSorted === "desc" ? (
      <ArrowDown className="h-3 w-3 text-blue-500" />
    ) : (
      <ArrowUpDown className="h-3 w-3 opacity-30" />
    );

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        className="flex cursor-pointer items-center gap-1 text-left text-xs font-semibold text-slate-700 hover:text-slate-900"
        onClick={onSort}
      >
        {label}
        {icon}
        <TypeBadge type={colType} />
      </button>
    </div>
  );
}

// ============================================================================
// Main component
// ============================================================================

const PAGE_SIZE = 50;

export function PopulationDataTable({ rows, columns, totalRows }: PopulationDataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: PAGE_SIZE,
  });

  // Build column definitions from ColumnInfo
  const columnDefs = useMemo(
    (): ColumnDef<Record<string, unknown>>[] =>
      columns.map((col) => ({
        accessorKey: col.name,
        id: col.name,
        header: ({ column }) => (
          <SortableHeader
            label={col.name}
            colType={col.type}
            isSorted={column.getIsSorted()}
            onSort={() => { column.toggleSorting(); }}
          />
        ),
        cell: (info) => {
          const val = info.getValue();
          return (
            <span className="font-mono text-xs text-slate-700">
              {val === null || val === undefined ? (
                <span className="text-slate-300">—</span>
              ) : (
                String(val)
              )}
            </span>
          );
        },
        filterFn: "includesString",
      })),
    [columns],
  );

  const table = useReactTable({
    data: rows,
    columns: columnDefs,
    state: { sorting, columnFilters, pagination },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const { pageIndex, pageSize } = pagination;
  const filteredCount = table.getFilteredRowModel().rows.length;
  const fromRow = pageIndex * pageSize + 1;
  const toRow = Math.min((pageIndex + 1) * pageSize, filteredCount);

  return (
    <div className="flex h-full flex-col">
      {/* Table area */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10">
            {/* Column headers */}
            <tr className="border-b border-slate-200 bg-slate-50">
              {table.getFlatHeaders().map((header) => (
                <th
                  key={header.id}
                  className="whitespace-nowrap px-3 py-2 text-left first:pl-4"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
            {/* Filter row */}
            <tr className="border-b border-slate-200 bg-white">
              {table.getFlatHeaders().map((header) => (
                <th key={header.id} className="px-2 py-1 first:pl-3">
                  <Input
                    className="h-6 text-xs"
                    placeholder="filter…"
                    value={(header.column.getFilterValue() as string) ?? ""}
                    onChange={(e) => { header.column.setFilterValue(e.target.value); }}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-1.5 first:pl-4">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {table.getRowModel().rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-12 text-center text-sm text-slate-400"
                >
                  No rows match the current filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      <div className="flex shrink-0 items-center justify-between border-t border-slate-200 bg-white px-4 py-2">
        <span className="text-xs text-slate-500">
          Showing {fromRow.toLocaleString()}–{toRow.toLocaleString()} of{" "}
          {filteredCount.toLocaleString()}
          {filteredCount !== totalRows && (
            <> (filtered from {totalRows.toLocaleString()} total)</>
          )}
        </span>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            className="h-7 w-7 p-0"
            onClick={() => { table.previousPage(); }}
            disabled={!table.getCanPreviousPage()}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs text-slate-600">
            Page {pageIndex + 1} / {table.getPageCount() || 1}
          </span>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 w-7 p-0"
            onClick={() => { table.nextPage(); }}
            disabled={!table.getCanNextPage()}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
