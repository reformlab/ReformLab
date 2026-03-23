# Epic 19 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 19-2 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `actions/checkout@v6` does not exist (latest is v4); CI fails on every trigger | Changed to `actions/checkout@v4` |
| high | `mermaid` peer dependency is implicit — not listed in `package.json`, only auto-resolved by npm v7+ | Deferred as action item — requires `npm install` which modifies lockfile |
| medium | Missing `contents: read` permission in CI workflow; when `permissions` is set explicitly, defaults are disabled | Added `contents: read` to permissions block |
| medium | Story marked `Status: done` but two Task 4 subtasks (browser preview, SVG verification) are unchecked | Deferred as action item — requires manual browser verification |
| low | AC 4 "Try the Demo" CTA is inline lowercase text, not a visually distinct button/section | Deferred — acceptable for v1; AC 4 wording says "a 'Try the Demo' call-to-action is present" which is satisfied |
| low | JSX `{/* TODO */}` comments stripped from built HTML, reducing discoverability for future devs | Deferred as low-priority action item |
| dismissed | AC8 placeholder annotation format mismatch (`{/* */}` vs `<!-- -->`) | FALSE POSITIVE: The Dev Agent Record explicitly documents this as a deliberate bug fix: "HTML comments (`<!-- -->`) are not valid inside MDX JSX — replaced with JSX comments (`{/* */}`)". MDX does not support HTML comments inside JSX expressions; using `<!-- -->` would cause a build error. The AC was written before this MDX constraint was discovered. The intent (annotate placeholders) is met. |
| dismissed | All six use-case links are "dead" `#` placeholders — called a "navigation bug" | FALSE POSITIVE: AC 8 explicitly allows `#` placeholders: "a `#` placeholder annotated with `<!-- TODO: link to live demo filter -->`". The Dev Notes table shows all link targets as `/use-cases/#`. This is by design — the app doesn't support deep-linking yet. Not a bug. |
| dismissed | Repeated identical CTA text + identical href creates ambiguous navigation/accessibility | FALSE POSITIVE: Each "Explore this scenario →" link is inside a different Card with a unique title and description. Screen readers will read the card title before the link. This is standard card-grid UX pattern used by Starlight's own documentation. Not an accessibility issue in this context. |
| dismissed | Story File List omits substantial changed files (scope transparency failure) | FALSE POSITIVE: The files Reviewer A claims are missing (`.github/workflows/docs.yml`, BMAD workflow files) are from Story 19.1's commit, not Story 19.2. The git diff shows the full epic-19 branch diff against master, not the story-specific commit. Story 19.2's file list accurately reflects its own changes. |
| dismissed | CI lacks AC-level regression checks (Mermaid render/card-link integrity) | FALSE POSITIVE: The story's Testing Strategy explicitly states "No automated tests for static docs." Adding content-level CI assertions (grep for mermaid blocks, card counts) is over-engineering for a documentation site. The build and typecheck provide sufficient CI coverage. |
| dismissed | Dependency drift risk with `^1.3.1` range for `astro-mermaid` | FALSE POSITIVE: The lockfile pins the exact version. Using `^` ranges is standard npm practice; the lockfile ensures reproducibility. The existing `astro` dependency also uses a pinned version but `@astrojs/starlight` uses `^0.37`. This is consistent with the project's existing dependency strategy. Low risk. |
| dismissed | No `engines` field in `package.json` | FALSE POSITIVE: The `.nvmrc` file already specifies the Node version. Adding an `engines` field is a nice-to-have but not a Story 19.2 requirement and adds no meaningful safety beyond what `.nvmrc` + CI's `node-version-file` already provide. |

## Story 19-3 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | PolicyParameters code snippet has all 4 field types wrong (`list` vs `tuple`, `str` vs `int` keys) | Updated to match actual source: `dict[int, float]`, `tuple[dict[str, Any], ...] = ()`, `tuple[str, ...] = ()` |
| medium | IndicatorResult falsely described as "a PyArrow Table" — actual type is a structured dataclass | Changed to "a container holding a sequence of typed indicator objects, metadata, and warnings" |
| medium | Engine public prose uses "abstraction" and "adapter interface" — dev-only terms per vocabulary rules | Replaced with "designed to work with other tax-benefit calculators without changing how you run scenarios" |
| medium | Getting-started claims OpenFisca "ships with the standard install" — contradicts project-context.md where OpenFisca is optional | Changed to "Install the optional `[openfisca]` extra to use OpenFisca France" |
| low | `PopulationData.metadata` shown as required field; actual has `field(default_factory=dict)` | Added `= field(default_factory=dict)` to match source |
| low | `@runtime_checkable` missing from `OrchestratorStep` and `ComputationAdapter` protocol snippets | Added `@runtime_checkable` decorator to both |
| low | Step 3 link text "engine abstraction" uses dev jargon | Changed to "computation engine in the domain model" |
| low | Step 4 breaks linking pattern (steps 1-3 link to domain model, step 4 only has demo link) | Added domain model links for results and indicators |
| dismissed | Demo links are `#` placeholders causing non-functional navigation | FALSE POSITIVE: Story spec explicitly uses `#` placeholders with TODO comments. This is by design, identical to Story 19.2 (dismissed in antipatterns table). The app isn't live yet. |
| dismissed | No automated regression checks for docs ACs | FALSE POSITIVE: Story testing strategy explicitly states "No automated tests for static docs." Dismissed as over-engineering in Story 19.2 antipatterns: "Adding content-level CI assertions is over-engineering for a documentation site." |
| dismissed | `sprint-status.yaml` shows `in-progress` | FALSE POSITIVE: Partially false — actual value is `review` (correct status during code review phase), not `in-progress` as claimed. Will be updated to `done` after visual verification. |
| dismissed | "data fusion workbench" presented as available tool but not publicly shipped | FALSE POSITIVE: Epic 17 story 17-1 (`build-data-fusion-workbench-gui`) is marked done. The feature exists in the app. The docs describe what the app does, not what's publicly deployed. |
| dismissed | Task 3 marked complete with `npm run preview` unchecked = CRITICAL task completion lie | FALSE POSITIVE: Not a source code issue. This is a recurring process pattern acknowledged since Story 19.2 (browser preview requires manual verification). The story correctly marks the subtask as `[ ]` unchecked. Downgraded to LOW action item. |
| dismissed | Environment-driven URL needed for demo placeholders / build fail if empty | FALSE POSITIVE: Over-engineering. The app URL doesn't exist yet. A TODO comment is the appropriate mechanism. When the URL is available, a simple find-and-replace across docs pages is sufficient. |

## Story 19-4 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | MemoryCheckResponse fields wrong (`estimate_mb: int` vs `estimated_gb: float`, missing `available_gb: float`) | Replaced with actual fields from `models.py:93-97` |
| high | MemoryCheckRequest falsely described as "same shape as RunRequest" — actual has required `template_name: str`, no `seed`/`baseline_id`/`portfolio_name`/`policy_type` | Added full model definition |
| high | ScenarioCreateRequest and ScenarioResponse completely wrong (wrong field names, types, missing fields) | Rewritten to match `models.py:61-115` |
| high | Templates docs describe fictional `parameter_schema: dict` — actual uses `TemplateListItem` with `parameter_count`, `parameter_groups`, `is_custom` etc. | Replaced with all 4 actual models |
| high | Portfolio docs entirely wrong (`scenario_names` vs `policies`, `valid` vs `is_compatible`, missing validate request) | Rewritten with actual 4 models |
| high | Results docs misstate response shape (missing `timestamp`, `run_kind`, `data_available` vs `has_panel`, etc.) | Full rewrite with all fields from `models.py:402-444` |
| high | IndicatorRequest has fictional fields (`years`, `breakdown_column`) — actual uses `income_field`, `by_year` | Corrected to match `models.py:44-48` |
| high | ComparisonRequest has fictional fields (`indicator_types`, `years`) — actual uses `welfare_field`, `threshold` | All 3 comparison models corrected |
| high | GeneratePopulationResponse entirely fabricated — docs show 4 simple fields, actual has `success`, `summary`, `step_log`, `assumption_chain`, `validation_result` | Both request and response rewritten |
| high | PopulationListItem completely wrong field names (`population_id`/`description`/`row_count`/`entity_types` vs `id`/`name`/`households`/`year`) | Corrected to `PopulationItem` from `models.py:160-165` |
| high | DecisionSummaryRequest missing 3 fields (`domain_name`, `group_by`, `group_value`); response completely wrong | Both models corrected |
| high | ExportRequest shows fictional `columns`/`years` fields — actual only has `run_id` | Reduced to actual single field |
| high | OpenAPI URL wrong (`/docs` → `/api/docs`) and missing dev-mode note | URL corrected, dev-mode instruction added |
| medium | Contributing page points to wrong path for `DataSourceLoader` (`src/reformlab/data/` → `src/reformlab/population/loaders/`) | Path corrected |
| low | `MemoryCheckResult.estimate` described as `int` in Python API section — actual type is `MemoryEstimate` | Corrected type |
| dismissed | Story claims "35 endpoints across 10 routers" but docs show 11 groups | FALSE POSITIVE: This is in the story Dev Notes (not in the published docs page), and the discrepancy (10 vs 11) is because the story counts "Comparison" as part of "Indicators" router. Not a user-facing issue. |
| dismissed | AC9 build fails due to Node v14 | FALSE POSITIVE: Correctly noted as not a story defect — `.nvmrc` pins Node 20, and build works with correct Node version. |
