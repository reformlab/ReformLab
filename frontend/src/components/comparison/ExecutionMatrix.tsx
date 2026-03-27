// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Execution Matrix Component — Story 20.6, AC-1.
 *
 * Displays a scenario-by-population execution matrix showing:
 * - Rows: Scenarios (by name/portfolio)
 * - Columns: Populations (by name/source)
 * - Cells: Execution status (ExecutionStatus enum)
 *
 * Cell click behavior:
 * - COMPLETED: navigate to ResultsOverviewScreen with runId
 * - NOT_EXECUTED/FAILED: navigate to SimulationRunnerScreen
 * - RUNNING/QUEUED: show in-progress indicator
 */

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table";
import type { ExecutionMatrixCell, WorkspaceScenario } from "@/api/types";
import type { StageKey, SubView } from "@/types/workspace";

// ============================================================================
// Status helpers
// ============================================================================

function statusVariant(status: ExecutionStatus): "success" | "destructive" | "warning" | "default" {
  switch (status) {
    case "COMPLETED":
      return "success";
    case "FAILED":
      return "destructive";
    case "RUNNING":
    case "QUEUED":
      return "warning";
    default:
      return "default";
  }
}

function statusLabel(status: ExecutionStatus): string {
  switch (status) {
    case "NOT_EXECUTED":
      return "—";
    case "QUEUED":
      return "Queued";
    case "RUNNING":
      return "Running";
    case "COMPLETED":
      return "Done";
    case "FAILED":
      return "Failed";
  }
}

function statusTooltip(cell: ExecutionMatrixCell): string {
  switch (cell.status) {
    case "NOT_EXECUTED":
      return "Click to run simulation";
    case "QUEUED":
      return "Simulation queued";
    case "RUNNING":
      return "Simulation in progress...";
    case "COMPLETED":
      return cell.finishedAt
        ? `Run ${cell.runId?.slice(0, 8)} completed at ${new Date(cell.finishedAt).toLocaleString()}`
        : "Run completed";
    case "FAILED":
      return cell.error
        ? `Run failed: ${cell.error}. Click to retry.`
        : "Run failed. Click to retry.";
  }
}

// ============================================================================
// Props
// ============================================================================

interface ExecutionMatrixProps {
  scenarios: WorkspaceScenario[];
  populations: Array<{ id: string; name: string; source: string }>;
  matrix: Record<string, Record<string, ExecutionMatrixCell>>;
  loading?: boolean;
  onCellClick: (cell: ExecutionMatrixCell) => void;
  onNavigateTo: (stage: StageKey, subView?: SubView) => void;
  onCloneScenario: (scenarioId: string) => void;
  onDeleteRun: (runId: string) => void;
  onExportRun: (runId: string) => void;
  onRetryRun: (cell: ExecutionMatrixCell) => void;
}

// ============================================================================
// Component
// ============================================================================

export function ExecutionMatrix({
  scenarios,
  populations,
  matrix,
  loading = false,
  onCellClick,
  onNavigateTo,
  onCloneScenario,
  onDeleteRun,
  onExportRun,
  onRetryRun,
}: ExecutionMatrixProps) {
  const [contextMenuCell, setContextMenuCell] = useState<ExecutionMatrixCell | null>(null);

  // Empty states
  if (loading) {
    return (
      <Card className="p-6">
        <div className="space-y-3">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </Card>
    );
  }

  if (scenarios.length === 0) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-slate-500 mb-3">
          No scenarios defined yet. Create a scenario first.
        </p>
        <Button variant="outline" size="sm" onClick={() => onNavigateTo("policies")}>
          Go to Policies Stage
        </Button>
      </Card>
    );
  }

  if (populations.length === 0) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-slate-500 mb-3">
          No populations available. Select populations in the Population stage.
        </p>
        <Button variant="outline" size="sm" onClick={() => onNavigateTo("population")}>
          Go to Population Stage
        </Button>
      </Card>
    );
  }

  // Check if any executions exist
  const hasExecutions = Object.values(matrix).some((popMap) =>
    Object.values(popMap).some((cell) => cell.status !== "NOT_EXECUTED")
  );

  if (!hasExecutions) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-slate-500 mb-3">
          No simulations run yet. Execute scenarios to see results.
        </p>
        <Button size="sm" onClick={() => onNavigateTo("results", "runner")}>
          Run Simulation
        </Button>
      </Card>
    );
  }

  // Render the matrix
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell className="sticky left-0 bg-slate-50 z-10 min-w-[200px] border-r">
                Scenario
              </TableHeaderCell>
              {populations.map((pop) => (
                <TableHeaderCell key={pop.id} className="min-w-[150px] text-center">
                  <div className="flex flex-col items-center">
                    <span className="font-medium">{pop.name}</span>
                    <span className="text-xs text-slate-500">{pop.source}</span>
                  </div>
                </TableHeaderCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {scenarios.map((scenario) => (
              <TableRow key={scenario.id}>
                <TableCell className="sticky left-0 bg-white z-10 border-r font-medium">
                  <div className="flex flex-col">
                    <span className="text-sm text-slate-900">{scenario.name}</span>
                    {scenario.portfolioName && (
                      <span className="text-xs text-slate-500">{scenario.portfolioName}</span>
                    )}
                  </div>
                </TableCell>
                {populations.map((pop) => {
                  const cell = matrix[scenario.id]?.[pop.id] ?? {
                    scenarioId: scenario.id,
                    populationId: pop.id,
                    status: "NOT_EXECUTED" as const,
                  };
                  return <MatrixCell
                    key={`${scenario.id}-${pop.id}`}
                    cell={cell}
                    onClick={() => onCellClick(cell)}
                    onContextMenu={() => setContextMenuCell(cell)}
                    scenarioName={scenario.name}
                    populationName={pop.name}
                  />;
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Context menu */}
      {contextMenuCell && (
        <ContextMenu
          cell={contextMenuCell}
          onClose={() => setContextMenuCell(null)}
          onClone={() => {
            onCloneScenario(contextMenuCell.scenarioId);
            setContextMenuCell(null);
          }}
          onDelete={() => {
            if (contextMenuCell.runId) {
              onDeleteRun(contextMenuCell.runId);
            }
            setContextMenuCell(null);
          }}
          onExport={() => {
            if (contextMenuCell.runId) {
              onExportRun(contextMenuCell.runId);
            }
            setContextMenuCell(null);
          }}
          onRetry={() => {
            onRetryRun(contextMenuCell);
            setContextMenuCell(null);
          }}
        />
      )}
    </Card>
  );
}

// ============================================================================
// MatrixCell component
// ============================================================================

interface MatrixCellProps {
  cell: ExecutionMatrixCell;
  onClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
  scenarioName: string;
  populationName: string;
}

function MatrixCell({ cell, onClick, onContextMenu, scenarioName, populationName }: MatrixCellProps) {
  const variant = statusVariant(cell.status);
  const label = statusLabel(cell.status);
  const tooltip = statusTooltip(cell);

  return (
    <TableCell
      className="text-center cursor-pointer hover:bg-slate-50"
      onClick={onClick}
      onContextMenu={onContextMenu}
      title={`${tooltip}\n${scenarioName} × ${populationName}`}
    >
      <Badge variant={variant} className="text-xs">
        {label}
      </Badge>
    </TableCell>
  );
}

// ============================================================================
// Context menu component (using Popover since DropdownMenu not available)
// ============================================================================

interface ContextMenuProps {
  cell: ExecutionMatrixCell;
  onClose: () => void;
  onClone: () => void;
  onDelete: () => void;
  onExport: () => void;
  onRetry: () => void;
}

function ContextMenu({ cell, onClose, onClone, onDelete, onExport, onRetry }: ContextMenuProps) {
  const canView = cell.status === "COMPLETED" && !!cell.runId;
  const canDelete = cell.status !== "RUNNING" && cell.status !== "QUEUED";
  const canExport = cell.status === "COMPLETED" && !!cell.runId;
  const canRetry = cell.status === "FAILED";

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <Popover open={true} onOpenChange={onClose}>
        <PopoverTrigger asChild>
          <div />
        </PopoverTrigger>
        <PopoverContent
          className="w-48 p-1"
          align="start"
          onPointerDownOutside={onClose}
        >
          <div className="space-y-0.5">
            <button
              className="w-full text-left px-2 py-1.5 text-sm hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!canView}
              onClick={(e) => { e.stopPropagation(); onClose(); }}
            >
              View Results
            </button>
            <button
              className="w-full text-left px-2 py-1.5 text-sm hover:bg-slate-100 rounded"
              onClick={(e) => { e.stopPropagation(); onClone(); }}
            >
              Clone Scenario
            </button>
            <button
              className="w-full text-left px-2 py-1.5 text-sm hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!canDelete}
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
            >
              Delete Run
            </button>
            <button
              className="w-full text-left px-2 py-1.5 text-sm hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!canExport}
              onClick={(e) => { e.stopPropagation(); onExport(); }}
            >
              Export
            </button>
            <button
              className="w-full text-left px-2 py-1.5 text-sm hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!canRetry}
              onClick={(e) => { e.stopPropagation(); onRetry(); }}
            >
              Retry Run
            </button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
