import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Population } from "@/data/mock-data";

interface PopulationSelectionScreenProps {
  populations: Population[];
  selectedPopulationId: string;
  onSelectPopulation: (id: string) => void;
}

export function PopulationSelectionScreen({
  populations,
  selectedPopulationId,
  onSelectPopulation,
}: PopulationSelectionScreenProps) {
  return (
    <section className="grid gap-2 xl:grid-cols-2">
      {populations.map((population) => {
        const selected = population.id === selectedPopulationId;
        return (
          <button
            type="button"
            key={population.id}
            onClick={() => onSelectPopulation(population.id)}
            className="text-left"
          >
            <Card className={selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white"}>
              <CardHeader>
                <CardTitle>{population.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700">Source: {population.source}</p>
                <p className="data-mono text-sm text-slate-700">
                  {population.households.toLocaleString()} households
                </p>
                <p className="text-sm text-slate-700">Year: {population.year}</p>
              </CardContent>
            </Card>
          </button>
        );
      })}
    </section>
  );
}
