/** Barrel export for comparison sub-components — Story 18.5, AC-2. */

export { RunSelector } from "./RunSelector";
export type { RunSelectorProps } from "./RunSelector";
export { FiscalTab } from "./FiscalTab";
export { WelfareTab } from "./WelfareTab";
export { DetailPanel } from "./DetailPanel";
export {
  type ViewMode,
  type ActiveTab,
  type DetailTarget,
  MAX_RUNS,
  METHODOLOGY_DESCRIPTIONS,
  runLabel,
  statusVariant,
  buildSeries,
  escapeCsvField,
  exportComparisonCsv,
} from "./comparison-helpers";
