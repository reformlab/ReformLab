# Epic 19: Public Documentation Site

**User outcome:** Open-source visitors and policy professionals can discover what ReformLab does, understand its domain model, and get started — through a branded, concise documentation site at `docs.reform-lab.eu`.

**Status:** backlog

**Builds on:** None (independent of application epics)

**Source:** `_bmad-output/brainstorming/brainstorming-documentation-strategy-2026-03-23.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1901 | Story | P0 | 5 | Scaffold Starlight site with brand theming and GitHub Pages deploy | backlog | — |
| BKL-1902 | Story | P0 | 3 | Create landing page and use case card grid | backlog | — |
| BKL-1903 | Story | P0 | 3 | Create getting started guide and domain model reference | backlog | — |
| BKL-1904 | Story | P0 | 3 | Create contributing page and API reference | backlog | — |
| BKL-1905 | Story | P1 | 5 | Build interactive domain model (React/MDX component) | backlog | — |
| BKL-1906 | Story | P1 | 3 | Add guided product tour (driver.js/shepherd.js) | backlog | — |

## Epic-Level Acceptance Criteria

- Starlight site builds and deploys to GitHub Pages on push to `master`.
- Site is branded with ReformLab visual identity (Inter, IBM Plex Mono, Emerald/Slate palette).
- 6 public pages exist: landing, use cases, getting started, domain model, contributing, API reference.
- BMAD planning artifacts (in `_bmad-output/planning-artifacts/`) are not part of the docs site.
- Every page links to the live demo where relevant.
- 5-sentence rule: no page exceeds 5 sentences before a visual or interactive element.
- Primary audience (administration/policy persona) can navigate without encountering developer jargon.

---

## Story 19.1: Scaffold Starlight site with brand theming and GitHub Pages deploy

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

**Tech Spec:** `_bmad-output/implementation-artifacts/tech-spec-scaffold-starlight-docs.md` — contains full implementation plan with 7 tasks, file paths, code snippets, and adversarial review fixes. Use the tech spec as the primary implementation reference for this story.

### Acceptance Criteria

- Given a new `docs/` directory, when `npm run dev` is run, then Starlight serves locally on port 4322 with branded theme.
- Given the brand theme, when the site renders, then fonts (Inter, IBM Plex Mono) and dark/light modes match the existing brand identity. Accent colors configured via Starlight's config API in `astro.config.mjs`, NOT via CSS custom properties.
- Given the `docs/` directory, when `npm run build` is run, then static output is generated with zero errors and `dist/CNAME` exists.
- Given a push to `master` with changes in `docs/`, when the `docs.yml` GitHub Actions workflow runs, then the site is built and deployed to GitHub Pages.
- Given the 6 planned pages, when the site is scaffolded, then placeholder pages exist in the Starlight content structure with correct navigation order.
- Given MkDocs configuration, when this story is complete, then `mkdocs.yml` is removed, `pyproject.toml` has no `docs` dependency group, and old `Docs:` tasks are removed from `.vscode/tasks.json`.
- Given VSCode, when the user runs the "Docs: Dev Server (localhost:4322)" task, then the Starlight dev server starts and is accessible in the browser.
- Given the `docs/` directory, when inspected, then `package-lock.json` exists and is committed (required for `npm ci` in CI).

---

## Story 19.2: Create landing page and use case card grid

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 19.1

### Acceptance Criteria

- Given the landing page, when visited, then it displays a tagline, a domain model diagram (Mermaid v1), and a "Try the Demo" call-to-action linking to the live app.
- Given the landing page, when viewed, then progressive disclosure is applied: the page is nearly empty, with depth one click away.
- Given the use cases page, when visited, then it displays a card grid (4-6 cards) with title, one-liner description, thumbnail, and "Try it" link per card.
- Given the use case cards, when viewed by a non-technical user, then descriptions use policy/administration language, not developer jargon.

---

## Story 19.3: Create getting started guide and domain model reference

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 19.1

### Acceptance Criteria

- Given the getting started page, when visited, then it presents the current staged path (policies, population, investment decisions, scenario, run/results) with clear visual progression.
- Given the domain model page, when visited, then each of the 5-6 core objects (Population, Policy Set, Investment Decisions, Scenario, Run, Results) is explained in 5 sentences or fewer.
- Given the domain model page, when a developer wants code details, then expandable "How it works in code" sections are available but hidden by default.
- Given both pages, when visited, then they link to the live demo at appropriate points.

---

## Story 19.4: Create contributing page and API reference

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 19.1

### Acceptance Criteria

- Given the contributing page, when visited, then it covers dev setup, architecture overview, and links to `CONTRIBUTING.md` at the repository root.
- Given the API reference page, when visited, then it presents a condensed, expandable reference of the Python API and REST endpoints.
- Given both pages, when visited by a developer, then information is developer-appropriate without requiring prior domain knowledge.

---

## Story 19.5: Build interactive domain model (React/MDX component)

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 19.3

### Acceptance Criteria

- Given the domain model page, when visited, then the static Mermaid diagram is replaced by a clickable React/MDX component showing the 5-6 core objects and their relationships.
- Given an object in the interactive diagram, when clicked, then a detail panel or tooltip displays the object's description and key properties.
- Given the interactive component, when rendered in Starlight, then it works in both light and dark modes with brand colors.

---

## Story 19.6: Add guided product tour (driver.js/shepherd.js)

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 19.5

### Acceptance Criteria

- Given the domain model page, when a "Take the tour" button is clicked, then a step-by-step guided tour highlights each core object in sequence with explanatory tooltips.
- Given the tour, when completed, then the user has been walked through the full domain model in a "product tour" feel.
- Given the tour, when dismissed at any step, then the user returns to the normal page state without errors.

---

## Scope Notes

- **Three separate surfaces:** reform-lab.eu (sell) / docs.reform-lab.eu (use) / app (try).
- **Admin persona first** — primary audience is civil servants and policy advisors, not developers.
- **Show, don't document** — the live demo is the primary front door; docs support it.
- **5-sentence rule** — enforces brevity on every page; progressive disclosure for depth.
- **Starlight in `docs/`** — separate from `website/` (Astro marketing site) and `docs/` (internal BMAD artifacts).
- **Stories 19.5 and 19.6 are v2** — scaffold and content come first, interactivity follows.

---
