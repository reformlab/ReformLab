# Ideas & Parking Lot

A lightweight capture list for raw ideas, feature requests, and things to explore later.
When ready to act on an item, promote it to a brainstorming session, quick spec, story, or course correction.

---

## Ideas

<!-- Add new ideas at the top with a date -->

- **2026-03-24** — **Unify loader and ingestion data model + JSON-driven loaders**: Two related improvements:
  1. **Converge loaders with the ingestion/PopulationData stack**: Loaders currently use raw `pa.Schema` and return `pa.Table`, while `load_population()` uses `DataSchema` and returns `PopulationData`. Align them so loaders use `DataSchema` (with required/optional columns) and return `PopulationData`. Column renaming stays in `_fetch()`, schema validation happens after rename. Result: one mental model for all data sources.
  2. **JSON-driven loader definitions**: Move dataset catalog entries, schemas, column rename mappings, and source metadata out of Python code into JSON files. Benefits: (a) auditors can review data contracts without reading Python, (b) adding a new data source = adding JSON files instead of writing a loader subclass, (c) connects to the file-based schema idea below. A loader definition folder could look like `loaders/insee/filosofi_2021_commune/` with `source.json` (url, provider, description, license), `schema.json` (columns, types, required/optional), `mapping.json` (raw_name → project_name renames), `parse_options.json` (separator, encoding, null_markers, file_format). A generic `JsonDrivenLoader(CachedLoader)` reads these files and handles download/parse/rename/validate without custom Python per provider.

- **2026-03-24** — **File-based DataSchema & DataSourceMetadata for user datasets**: Let users define schemas and provenance metadata via JSON files alongside their CSV/Parquet data, instead of requiring Python code. A folder convention like `my-population/{data.csv, schema.json, source.json}` with a single `load_population_folder(path)` entry point. Lowers the barrier for non-developer users bringing their own datasets. (This is the user-facing counterpart to the JSON-driven loaders above.)

- **2026-02-23** — **Community template marketplace**: Living ecosystem where researchers publish model templates, others review and rate them, popular templates get "verified" status. npm/PyPI for policy models. Network effects — every new template makes the framework more valuable. *(from architecture brainstorming #37)*

- **2026-02-23** — **"People Like Me" comparison**: Beyond personal result, show how a reform affects households similar to yours (same income range, region, family structure) and the impact across all income groups. Citizen-facing feature. *(from architecture brainstorming #21)*

- **2026-02-23** — **Smart output size advisor**: Before exporting, warn about output size and suggest aggregation alternatives ("This export will generate 2.3 GB — would you like to aggregate by decile instead? 12 KB."). *(from architecture brainstorming #6)*

- **2026-02-23** — **"Minister-Ready" export template**: Pre-formatted export mode — clean charts, summary table, methodology footnote, comparison against baseline — formatted for a slide deck or 2-page policy brief. One click, ready for the cabinet meeting. *(from architecture brainstorming #7)*

- **2026-02-23** — **Election app**: Citizen-facing tool for exploring policy impacts during elections. Scope & design + media partnerships for distribution. *(from architecture brainstorming + GTM strategy)*

- **2026-02-27** — **Policy Document Ingestion Agent (AI)**: Accept PDFs of legislative texts, extract parameters (rates, thresholds, dates, eligibility criteria), map to OpenFisca variables, produce draft model config with confidence-scored triage (green/yellow/red). Genuinely needs AI — documents are unstructured. Star idea from custom agents brainstorming. *(from BMAD agents brainstorming #10-11+22)*

- **2026-02-27** — **Run Failure Diagnostician Agent (AI)**: Examine run manifests, logs, intermediate outputs, and data vintages to diagnose orchestration failures. Detective work across multiple layers — data mismatch? Parameter out of range? OpenFisca version incompatibility? *(from BMAD agents brainstorming #13)*

- **2026-02-27** — **Results Communication Agent (AI)**: Produce audience-appropriate outputs from simulation runs: technical appendix for economists, executive summary for politicians, public-facing explainer. Includes divergence narration for multi-scenario comparisons. *(from BMAD agents brainstorming #20+23)*

- **2026-02-25** — **GTM: PyPI package publication**: `pip install reformlab` ready for users. *(from GTM strategy)*

- **2026-02-25** — **GTM: OpenFisca community engagement**: Engage maintainers, position ReformLab as companion tool. *(from GTM strategy)*

- **2026-02-25** — **GTM: Government outreach**: Ministries, evaluation departments, pilot partnerships. *(from GTM strategy)*

- **2026-02-25** — **GTM: Academic track**: Data partnerships (INSEE, Eurostat, real microdata access) → Working paper (methodology, architecture, carbon tax case study) → Journal submission (peer-reviewed publication using ReformLab). *(from GTM strategy)*

- **2026-02-25** — **GTM: Conferences & demos**: Policy events, Python meetups, live showcase. *(from GTM strategy)*

## Bugs

<!-- Add new bugs at the top with a date -->

- **2026-03-24** — **ADEME loader broken**: `base_carbone` download fails with `ArrowKeyError: Column 'Identifiant de l'élément'` — the apostrophe in the French column name breaks column matching after encoding decode. Either the file encoding changed on data.gouv.fr or the apostrophe character itself changed (curly vs straight). Needs investigation of actual downloaded bytes vs expected column names in `_BASE_CARBONE_COLUMNS`.

- **2026-03-24** — **SDES loader broken**: `vehicle_fleet` download fails with `ArrowKeyError: Column 'REGION_CODE' in include_columns does not exist in CSV file`. The data.gouv.fr resource has changed its column naming convention. Need to download the raw file, inspect actual headers, and update `_VEHICLE_FLEET_COLUMNS` mapping and schema accordingly.

<!-- Example:
- **2026-03-24** — Add CSV export to comparison dashboard
- **2026-03-24** — Explore i18n for French UI labels
-->
