import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { mockPopulations, mockTemplates, type Parameter } from "@/data/mock-data";

interface ReviewStepProps {
  /** Selected population id */
  populationId: string | null;
  /** Selected template id */
  templateId: string | null;
  /** Current parameter values */
  parameters: Parameter[];
}

function StatusIndicator({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      {ok ? (
        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
      ) : (
        <AlertTriangle className="h-4 w-4 text-amber-500" />
      )}
      <span
        className={cn(
          "text-sm",
          ok ? "text-slate-700" : "text-amber-700",
        )}
      >
        {label}
      </span>
    </div>
  );
}

export default function ReviewStep({
  populationId,
  templateId,
  parameters,
}: ReviewStepProps) {
  const population = mockPopulations.find((p) => p.id === populationId);
  const template = mockTemplates.find((t) => t.id === templateId);
  const modifiedParams = parameters.filter((p) => p.value !== p.baseline);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">
          Review Configuration
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Verify all settings before running the simulation.
        </p>
      </div>

      {/* Validation status */}
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
          Validation Status
        </h3>
        <StatusIndicator
          ok={!!population}
          label={population ? `Population: ${population.name}` : "Population: not selected"}
        />
        <StatusIndicator
          ok={!!template}
          label={template ? `Template: ${template.name}` : "Template: not selected"}
        />
        <StatusIndicator
          ok={true}
          label={`Parameters: ${parameters.length} configured, ${modifiedParams.length} modified`}
        />
      </div>

      {/* Population summary */}
      {population && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 mb-2">
            Population Source
          </h3>
          <div className="rounded-lg border border-slate-200 bg-white p-3">
            <p className="text-sm text-slate-800">{population.name}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {population.source} &middot; {population.year} &middot;{" "}
              {population.households.toLocaleString()} households
            </p>
          </div>
        </div>
      )}

      {/* Template summary */}
      {template && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 mb-2">
            Policy Template
          </h3>
          <div className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex items-center gap-2">
              <p className="text-sm text-slate-800">{template.name}</p>
              <Badge variant="outline" className="text-xs">
                {template.type}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {template.description}
            </p>
          </div>
        </div>
      )}

      {/* Parameters table */}
      <div>
        <h3 className="text-sm font-medium text-slate-700 mb-2">
          Parameter Values
        </h3>
        <div className="rounded-lg border border-slate-200 overflow-hidden">
          <Table>
            <TableHead>
              <TableRow className="bg-slate-50">
                <TableHeaderCell className="text-xs font-semibold">Parameter</TableHeaderCell>
                <TableHeaderCell className="text-xs font-semibold text-right">Value</TableHeaderCell>
                <TableHeaderCell className="text-xs font-semibold text-right">Baseline</TableHeaderCell>
                <TableHeaderCell className="text-xs font-semibold text-right">Unit</TableHeaderCell>
                <TableHeaderCell className="text-xs font-semibold text-center">Status</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {parameters.map((param) => {
                const isModified = param.value !== param.baseline;
                return (
                  <TableRow key={param.id}>
                    <TableCell className="text-sm">{param.label}</TableCell>
                    <TableCell
                      className={cn(
                        "text-sm text-right font-mono",
                        isModified && "text-sky-700 font-medium",
                      )}
                    >
                      {param.unit === "%"
                        ? param.value.toFixed(2)
                        : param.value.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-right font-mono text-slate-400">
                      {param.unit === "%"
                        ? param.baseline.toFixed(2)
                        : param.baseline.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs text-right text-slate-500">
                      {param.unit}
                    </TableCell>
                    <TableCell className="text-center">
                      {isModified ? (
                        <Badge className="bg-sky-50 text-sky-700 border-sky-200 text-xs">
                          modified
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs">
                          default
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
