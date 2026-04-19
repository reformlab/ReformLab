---
title: 'Add behavioral assertions to chart tests'
type: 'chore'
created: '2026-04-19'
status: 'done'
baseline_commit: '86f188ec043cd12c580306e3d9e9831d645a2471'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** All four chart test files (DistributionalChart, MultiRunChart, PopulationDistributionChart, TransitionChart) only assert that title text exists in the DOM. They pass even if the chart renders nothing but a heading. This creates false coverage — tests look green but catch zero data-rendering bugs.

**Approach:** Add SVG-level assertions (querying rendered `<rect>`, `<path>`, `<text>` elements) and companion-table assertions where applicable. Recharts 3.x renders real SVG in JSDOM — confirmed by existing `container.querySelector("svg")` usage elsewhere in the codebase. Legend text is documented as unreliable in JSDOM, so skip legend assertions.

## Boundaries & Constraints

**Always:** Keep existing title/render assertions — add to them, don't replace. Use `container.querySelectorAll` for SVG queries since Recharts elements don't have roles or test-ids. Assert on element counts (bars matching data length) and presence, not exact pixel coordinates.

**Ask First:** Adding `data-testid` attributes to chart components — only if SVG querying proves too fragile for a specific chart type.

**Never:** Do not modify chart component production code. Do not add snapshot tests. Do not assert on Legend content (documented JSDOM limitation). Do not assert on Tooltip content (rendered outside normal DOM flow).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Bar chart with N deciles | mockDecileData (10 items) | >=10 `<rect>` SVG elements rendered (2 series × 10) | N/A |
| Empty data array | `[]` | PopulationDistributionChart returns null; others render chart shell with no bars | N/A |
| Companion table present | MultiRunChart / TransitionChart with data | HTML `<table>` with correct row count matching data | N/A |

</frozen-after-approval>

## Code Map

- `frontend/src/components/simulation/__tests__/DistributionalChart.test.tsx` -- 3 title-only tests; needs bar count + axis assertions
- `frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx` -- title-only tests; needs bar count + table value assertions
- `frontend/src/components/simulation/__tests__/PopulationDistributionChart.test.tsx` -- title-only tests; needs bar count + empty-data assertion
- `frontend/src/components/simulation/__tests__/TransitionChart.test.tsx` -- title-only tests; needs area path + table row assertions
- `frontend/src/components/simulation/DistributionalChart.tsx` -- BarChart with 2 Bar series (baseline + reform)
- `frontend/src/components/simulation/MultiRunChart.tsx` -- BarChart with dynamic Bar count + HTML companion table
- `frontend/src/components/simulation/PopulationDistributionChart.tsx` -- BarChart with 1 Bar series; returns null on empty data
- `frontend/src/components/simulation/TransitionChart.tsx` -- AreaChart (stacked) + HTML companion table

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/components/simulation/__tests__/DistributionalChart.test.tsx` -- Add test: given 10-item mock data, assert >=10 `<rect>` elements rendered (2 series × 10 deciles). Add test: assert XAxis renders decile label text.
- [x] `frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx` -- Add test: assert `<rect>` count matches data × series. Add test: assert companion `<table>` has correct number of `<tr>` rows.
- [x] `frontend/src/components/simulation/__tests__/PopulationDistributionChart.test.tsx` -- Add test: given data, assert `<rect>` count matches data length. Add test: given empty array, assert component renders nothing (container empty or null).
- [x] `frontend/src/components/simulation/__tests__/TransitionChart.test.tsx` -- Add test: assert `<path>` elements rendered for stacked areas. Add test: assert companion `<table>` row count matches year data.

**Acceptance Criteria:**
- Given each chart test file, when tests run, then at least one test asserts on SVG element presence or count (not just text)
- Given PopulationDistributionChart with empty data, when rendered, then container has no chart output
- Given MultiRunChart/TransitionChart, when rendered with data, then companion table row count matches input data length

## Design Notes

Recharts in JSDOM renders SVG elements but ResizeObserver must be polyfilled (already done in existing test setup). Query pattern:

```tsx
const { container } = render(<DistributionalChart data={mockData} />);
const bars = container.querySelectorAll("rect");
// 2 series × 10 data points = at least 20 rects (Recharts may add grid rects)
expect(bars.length).toBeGreaterThanOrEqual(20);
```

Use `>=` not `===` because Recharts may render additional `<rect>` for grid/background.

## Verification

**Commands:**
- `cd frontend && npx vitest run src/components/simulation/__tests__/DistributionalChart.test.tsx src/components/simulation/__tests__/MultiRunChart.test.tsx src/components/simulation/__tests__/PopulationDistributionChart.test.tsx src/components/simulation/__tests__/TransitionChart.test.tsx` -- expected: all tests pass
- `cd frontend && npm run typecheck` -- expected: no new errors

## Suggested Review Order

**Test Harness**

- Shared Recharts sizing mock makes ResponsiveContainer render real SVG in JSDOM.
  [`recharts-test-utils.ts:26`](../../frontend/src/components/simulation/__tests__/recharts-test-utils.ts#L26)

- Centralized SVG selectors document intentional Recharts DOM coupling.
  [`recharts-test-utils.ts:58`](../../frontend/src/components/simulation/__tests__/recharts-test-utils.ts#L58)

**SVG Behavioral Assertions**

- DistributionalChart now proves both bar series render, then checks axis labels.
  [`DistributionalChart.test.tsx:20`](../../frontend/src/components/simulation/__tests__/DistributionalChart.test.tsx#L20)

- MultiRunChart uses positive data to avoid zero-height bar count ambiguity.
  [`MultiRunChart.test.tsx:36`](../../frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx#L36)

- PopulationDistributionChart keeps empty-state coverage beside bar rendering coverage.
  [`PopulationDistributionChart.test.tsx:25`](../../frontend/src/components/simulation/__tests__/PopulationDistributionChart.test.tsx#L25)

- TransitionChart waits for concrete stacked-area paths, not generic SVG paths.
  [`TransitionChart.test.tsx:52`](../../frontend/src/components/simulation/__tests__/TransitionChart.test.tsx#L52)

**Companion Tables**

- MultiRunChart table rows are tied directly to input row count.
  [`MultiRunChart.test.tsx:54`](../../frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx#L54)

- TransitionChart table rows are tied directly to yearly outcome count.
  [`TransitionChart.test.tsx:67`](../../frontend/src/components/simulation/__tests__/TransitionChart.test.tsx#L67)
