/**
 * BehavioralDecisionViewerScreen — Story 17.5, AC-1 through AC-4.
 *
 * Full-screen viewer for household behavioral decision outcomes:
 * - Domain selector tabs (vehicle, heating) — AC-1
 * - Year-by-year transition stacked area chart — AC-2
 * - Income decile filtering — AC-3
 * - Year detail panel with probabilities — AC-4
 */

import { useCallback, useEffect, useState } from "react";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { ErrorAlert, type ErrorState } from "@/components/simulation/ErrorAlert";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip } from "@/components/ui/tooltip";
import { TransitionChart } from "@/components/simulation/TransitionChart";
import { YearDetailPanel } from "@/components/simulation/YearDetailPanel";
import { getDecisionSummary } from "@/api/decisions";
import type {
  DecisionSummaryResponse,
  DomainSummary,
  YearlyOutcome,
} from "@/api/types";

// ============================================================================
// Constants
// ============================================================================

const DOMAIN_TAB_LABELS: Record<string, string> = {
  vehicle: "Vehicle Fleet",
  heating: "Heating System",
};

const DECILE_OPTIONS = [
  { value: "", label: "All Households" },
  { value: "1", label: "D1 (Lowest Income)" },
  { value: "2", label: "D2" },
  { value: "3", label: "D3" },
  { value: "4", label: "D4" },
  { value: "5", label: "D5" },
  { value: "6", label: "D6" },
  { value: "7", label: "D7" },
  { value: "8", label: "D8" },
  { value: "9", label: "D9" },
  { value: "10", label: "D10 (Highest Income)" },
];

const NO_DECISION_DATA_MESSAGE =
  "This simulation does not include behavioral decisions. Run a simulation with " +
  "discrete choice domains (vehicle, heating) to see decision outcomes.";

// ============================================================================
// Helper: extract detail from ApiError or raw thrown object
// ============================================================================

function extractErrorDetail(err: unknown): ErrorState | null {
  if (err == null || typeof err !== "object") return null;
  const e = err as Record<string, unknown>;
  // ApiError instance: { what, why, fix } directly on the error object
  if (typeof e["what"] === "string") {
    return {
      what: String(e["what"]),
      why: String(e["why"] ?? ""),
      fix: String(e["fix"] ?? ""),
    };
  }
  return null;
}

// ============================================================================
// Component
// ============================================================================

export interface BehavioralDecisionViewerScreenProps {
  runId: string;
  onBack: () => void;
}

export function BehavioralDecisionViewerScreen({
  runId,
  onBack,
}: BehavioralDecisionViewerScreenProps) {
  // ── State ────────────────────────────────────────────────────────────────
  const [summaryData, setSummaryData] = useState<DecisionSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const [noDecisionData, setNoDecisionData] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string>("");
  const [selectedDecile, setSelectedDecile] = useState<string>("");
  const [decileDisabled, setDecileDisabled] = useState(false);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [yearOutcome, setYearOutcome] = useState<YearlyOutcome | null>(null);

  // ── Data loading ─────────────────────────────────────────────────────────

  const loadSummary = useCallback(
    async (decile: string, currentDomain: string) => {
      setLoading(true);
      setError(null);
      try {
        const req = {
          run_id: runId,
          ...(decile !== "" ? { group_by: "decile", group_value: decile } : {}),
        };
        const data = await getDecisionSummary(req);
        setSummaryData(data);
        setNoDecisionData(false);
        if (!currentDomain && data.domains.length > 0) {
          setSelectedDomain(data.domains[0].domain_name);
        }
      } catch (err: unknown) {
        const detail = extractErrorDetail(err);
        if (detail?.what === "NoDecisionData") {
          setNoDecisionData(true);
          setSummaryData(null);
        } else if (detail?.what === "NoIncomeData") {
          setDecileDisabled(true);
          setSelectedDecile("");
          // Re-fetch without decile
          try {
            const data = await getDecisionSummary({ run_id: runId });
            setSummaryData(data);
            setNoDecisionData(false);
          } catch {
            // ignore secondary failure
          }
        } else {
          setError(
            detail ?? {
              what: "Unknown error",
              why: String(err),
              fix: "Try again",
            },
          );
        }
      } finally {
        setLoading(false);
      }
    },
    [runId],
  );

  // Initial load
  useEffect(() => {
    void loadSummary("", "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  // ── Year detail loading ──────────────────────────────────────────────────

  const handleYearClick = useCallback(
    async (year: number) => {
      setSelectedYear(year);
      try {
        const req = {
          run_id: runId,
          year,
          ...(selectedDecile !== ""
            ? { group_by: "decile", group_value: selectedDecile }
            : {}),
        };
        const data = await getDecisionSummary(req);
        setSummaryData(data);
        const currentDomain = selectedDomain || summaryData?.domains[0]?.domain_name || "";
        const domainData = data.domains.find((d) => d.domain_name === currentDomain);
        const outcome = domainData?.yearly_outcomes.find((o) => o.year === year);
        setYearOutcome(outcome ?? null);
      } catch {
        // Keep the panel open with existing (no-probability) data
        const currentDomain = selectedDomain || summaryData?.domains[0]?.domain_name || "";
        const domainData = summaryData?.domains.find(
          (d) => d.domain_name === currentDomain,
        );
        const outcome = domainData?.yearly_outcomes.find((o) => o.year === year);
        setYearOutcome(outcome ?? null);
      }
    },
    [runId, selectedDomain, selectedDecile, summaryData],
  );

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleDecileChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const value = e.target.value;
      setSelectedDecile(value);
      setSelectedYear(null);
      setYearOutcome(null);
      void loadSummary(value, selectedDomain);
    },
    [loadSummary, selectedDomain],
  );

  const handleDomainChange = useCallback((domain: string) => {
    setSelectedDomain(domain);
    setSelectedYear(null);
    setYearOutcome(null);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedYear(null);
    setYearOutcome(null);
  }, []);

  // ── Derived data ─────────────────────────────────────────────────────────

  // Fall back to first domain if selectedDomain hasn't been set yet
  const activeDomainName =
    selectedDomain || summaryData?.domains[0]?.domain_name || "";

  const activeDomain: DomainSummary | undefined = summaryData?.domains.find(
    (d) => d.domain_name === activeDomainName,
  );

  const activeYearOutcome: YearlyOutcome | null =
    selectedYear !== null && activeDomain
      ? (activeDomain.yearly_outcomes.find((o) => o.year === selectedYear) ?? null)
      : null;

  const displayYearOutcome = yearOutcome ?? activeYearOutcome;

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-200 flex-shrink-0">
        <Button variant="ghost" size="sm" onClick={onBack} className="gap-1.5 -ml-1">
          <ArrowLeft size={14} />
          Back
        </Button>
        <div className="h-4 w-px bg-slate-200" />
        <h1 className="text-base font-semibold text-slate-800">
          Behavioral Decision Viewer
        </h1>
        <span className="text-xs text-slate-400 font-mono ml-1">{runId.slice(0, 8)}</span>
        {loading && (
          <span className="text-xs text-slate-400 animate-pulse ml-2">Loading…</span>
        )}
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Main content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {/* Error state */}
          {error && (
            <ErrorAlert what={error.what} why={error.why} fix={error.fix} className="mb-5" />
          )}

          {/* No decision data state */}
          {noDecisionData && !error && (
            <div className="flex items-start gap-3 p-4 bg-slate-50 border border-slate-200 rounded-lg mb-5">
              <AlertCircle size={16} className="text-slate-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-slate-600">{NO_DECISION_DATA_MESSAGE}</p>
            </div>
          )}

          {/* Main viewer */}
          {summaryData && !noDecisionData && (
            <>
              {/* Filters row */}
              <div className="flex items-center gap-4 mb-5">
                <div className="w-52">
                  <Select
                    value={selectedDecile}
                    onChange={handleDecileChange}
                    disabled={decileDisabled}
                    aria-label="Filter by income decile"
                  >
                    {DECILE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </Select>
                  {decileDisabled && (
                    <Tooltip className="mt-1">
                      Income data unavailable for this run. Decile filtering requires
                      a population dataset with income data.
                    </Tooltip>
                  )}
                </div>
              </div>

              {/* Domain tabs */}
              <Tabs value={activeDomainName} onValueChange={handleDomainChange}>
                <TabsList className="mb-4">
                  {summaryData.domains.map((d) => (
                    <TabsTrigger
                      key={d.domain_name}
                      value={d.domain_name}
                      className="text-xs"
                    >
                      {DOMAIN_TAB_LABELS[d.domain_name] ?? d.domain_name}
                    </TabsTrigger>
                  ))}
                </TabsList>

                {summaryData.domains.map((domain) => (
                  <TabsContent key={domain.domain_name} value={domain.domain_name}>
                    <TransitionChart
                      data={domain.yearly_outcomes}
                      alternativeIds={domain.alternative_ids}
                      alternativeLabels={domain.alternative_labels}
                      onYearClick={handleYearClick}
                    />
                  </TabsContent>
                ))}
              </Tabs>

              {/* Warnings */}
              {summaryData.warnings.length > 0 && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-700">
                  {summaryData.warnings.map((w, i) => (
                    <p key={i}>{w}</p>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Year detail panel */}
        {selectedYear !== null && activeDomain && displayYearOutcome && (
          <YearDetailPanel
            year={selectedYear}
            outcome={displayYearOutcome}
            domain={activeDomain}
            onClose={handleCloseDetail}
          />
        )}
      </div>
    </div>
  );
}
