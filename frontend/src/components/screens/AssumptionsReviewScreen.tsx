import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table";
import type { Parameter, Population, Template } from "@/data/mock-data";

interface AssumptionsReviewScreenProps {
  population: Population | undefined;
  template: Template | undefined;
  parameters: Parameter[];
  parameterValues: Record<string, number>;
}

export function AssumptionsReviewScreen({
  population,
  template,
  parameters,
  parameterValues,
}: AssumptionsReviewScreenProps) {
  return (
    <section className="space-y-3">
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <p className="text-sm font-semibold">Configuration Summary</p>
        <p className="mt-1 text-sm text-slate-700">Population: {population?.name ?? "Not selected"}</p>
        <p className="text-sm text-slate-700">Template: {template?.name ?? "Not selected"}</p>
        <div className="mt-2">
          <Badge variant="success">Validated</Badge>
        </div>
      </div>

      <Table className="rounded-lg border border-slate-200 bg-white">
        <TableHead>
          <TableRow>
            <TableHeaderCell>Parameter</TableHeaderCell>
            <TableHeaderCell>Value</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parameters.map((parameter) => {
            const value = parameterValues[parameter.id] ?? parameter.value;
            const modified = value !== parameter.baseline;
            return (
              <TableRow key={parameter.id}>
                <TableCell>{parameter.label}</TableCell>
                <TableCell className="data-mono">{value}</TableCell>
                <TableCell>
                  <Badge variant={modified ? "info" : "default"}>
                    {modified ? "Edited" : "Default"}
                  </Badge>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </section>
  );
}
