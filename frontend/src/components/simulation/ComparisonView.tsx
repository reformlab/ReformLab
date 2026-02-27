import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { DecileData, Scenario } from "@/data/mock-data";

interface ComparisonViewProps {
  scenarios: Scenario[];
  selectedScenarioIds: string[];
  onChangeSelectedScenarioIds: (ids: string[]) => void;
  decileData: DecileData[];
}

function asCurrency(value: number): string {
  return `${value.toFixed(0)} EUR`;
}

export function ComparisonView({
  scenarios,
  selectedScenarioIds,
  onChangeSelectedScenarioIds,
  decileData,
}: ComparisonViewProps) {
  const [mode, setMode] = useState("side-by-side");

  const selectedScenarios = useMemo(
    () => scenarios.filter((scenario) => selectedScenarioIds.includes(scenario.id)),
    [scenarios, selectedScenarioIds],
  );

  return (
    <section className="border border-slate-200 bg-white p-3">
      <div className="mb-3 flex flex-wrap items-end gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-slate-500">Scenario A</p>
          <Select
            value={selectedScenarioIds[0]}
            onChange={(event) =>
              onChangeSelectedScenarioIds([event.target.value, selectedScenarioIds[1]].filter(Boolean))
            }
          >
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase text-slate-500">Scenario B</p>
          <Select
            value={selectedScenarioIds[1]}
            onChange={(event) =>
              onChangeSelectedScenarioIds([selectedScenarioIds[0], event.target.value].filter(Boolean))
            }
          >
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.name}
              </option>
            ))}
          </Select>
        </div>

        <Badge variant="violet">Max 5 scenarios</Badge>
      </div>

      <Tabs value={mode} onValueChange={setMode}>
        <TabsList>
          <TabsTrigger value="side-by-side">Side-by-side</TabsTrigger>
          <TabsTrigger value="overlay">Overlay</TabsTrigger>
          <TabsTrigger value="delta">Delta</TabsTrigger>
        </TabsList>

        <TabsContent value="side-by-side">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Decile</TableHeaderCell>
                <TableHeaderCell>{selectedScenarios[0]?.name ?? "Scenario A"}</TableHeaderCell>
                <TableHeaderCell>{selectedScenarios[1]?.name ?? "Scenario B"}</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {decileData.map((row) => (
                <TableRow key={row.decile}>
                  <TableCell>{row.decile}</TableCell>
                  <TableCell className="data-mono">{asCurrency(row.baseline)}</TableCell>
                  <TableCell className="data-mono">{asCurrency(row.reform)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="overlay">
          <p className="text-sm text-slate-700">
            Overlay mode highlights both scenarios on a shared axis. Use the results chart to compare shapes
            quickly.
          </p>
        </TabsContent>

        <TabsContent value="delta">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Decile</TableHeaderCell>
                <TableHeaderCell>Delta (Reform - Baseline)</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {decileData.map((row) => (
                <TableRow key={row.decile}>
                  <TableCell>{row.decile}</TableCell>
                  <TableCell className="data-mono">{asCurrency(row.delta)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>
    </section>
  );
}
