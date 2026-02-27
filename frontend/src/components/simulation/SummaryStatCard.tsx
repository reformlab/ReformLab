import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SummaryStatistic } from "@/data/mock-data";

interface SummaryStatCardProps {
  stat: SummaryStatistic;
}

export function SummaryStatCard({ stat }: SummaryStatCardProps) {
  const variant =
    stat.trend === "up" ? "warning" : stat.trend === "down" ? "success" : "default";

  return (
    <Card>
      <CardHeader className="p-3">
        <CardTitle className="text-xs uppercase text-slate-500">{stat.label}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-2 p-3">
        <span className="data-mono text-lg font-semibold text-slate-900">{stat.value}</span>
        <Badge variant={variant}>{stat.trendValue}</Badge>
      </CardContent>
    </Card>
  );
}
