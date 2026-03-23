# Story 19.1: Scaffold Starlight Site with Brand Theming and GitHub Pages Deploy

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **open-source visitor or policy professional**,
I want a branded, concise documentation site deployed at `docs.reform-lab.eu`,
so that I can discover what ReformLab does, understand its domain model, and get started — without wading through internal planning artifacts.

## Acceptance Criteria

1. **Build succeeds:** Given the `docs/` directory, when `npm run build` is run, then the build completes with zero errors and produces static output in `docs/dist/`.
2. **Dev server works:** Given the `docs/` directory, when `npm run dev` is run, then the site is accessible at `http://localhost:4322` with branded theme.
3. **Light mode fonts:** Given the site in light mode, then headings and body text use Inter, code blocks use IBM Plex Mono.
4. **Dark mode fonts:** Given the site in dark mode, then the same font families apply and Starlight's dark theme renders correctly.
5. **All 6 pages reachable:** All pages are accessible: Home (via site title/logo link or sidebar), Use Cases, Getting Started, Domain Model, Contributing, API Reference.
6. **Placeholder content:** Each placeholder page has a title, description, and brief placeholder content indicating future work.
7. **Deploy workflow runs:** Given a push to `master` with changes in `docs/`, when `docs.yml` workflow runs, then the site is built and deployed to GitHub Pages. (Full verification requires merge + Pages enabled in repo settings; use `workflow_dispatch` for pre-merge build test.)
8. **Path filter works:** Given a push to `master` with no changes in `docs/`, then `docs.yml` workflow is NOT triggered.
9. **VSCode task works:** The "Docs: Dev Server (localhost:4322)" task starts the Starlight dev server as a running background task.
10. **MkDocs removed:** `mkdocs.yml` deleted, `pyproject.toml` has no `docs` dependency group, 3 old Docs tasks removed from `.vscode/tasks.json`, and `uv sync --locked --all-extras --dev` still succeeds.
11. **CNAME in dist:** `docs/public/CNAME` containing `docs.reform-lab.eu` is present in `dist/` after build.
12. **Lockfile committed:** `docs/package-lock.json` exists and is committed (required for `npm ci` in CI).

## Tasks / Subtasks

- [ ] Task 1: Initialize Starlight project in `docs/` (AC: 1, 2, 12)
  - [ ] Create `docs/package.json` with pinned dependencies (see Dev Notes for exact versions)
  - [ ] Create `docs/astro.config.mjs` with Starlight integration, sidebar, port 4322, site URL
  - [ ] Create `docs/tsconfig.json` extending `astro/tsconfigs/strict`
  - [ ] Create `docs/.nvmrc` with `20.19.6`
  - [ ] Run `npm install` in `docs/` to generate `package-lock.json` — commit the lockfile
- [ ] Task 2: Create brand-themed custom CSS (AC: 3, 4)
  - [ ] Create `docs/src/styles/custom.css` mapping Inter Variable → `--sl-font`, IBM Plex Mono → `--sl-font-mono`
  - [ ] Verify fonts render in both light and dark modes
- [ ] Task 3: Create 6 placeholder content pages (AC: 5, 6)
  - [ ] `docs/src/content/docs/index.mdx` — Landing page with hero
  - [ ] `docs/src/content/docs/use-cases.mdx` — Use Cases
  - [ ] `docs/src/content/docs/getting-started.mdx` — Getting Started
  - [ ] `docs/src/content/docs/domain-model.mdx` — Domain Model
  - [ ] `docs/src/content/docs/contributing.mdx` — Contributing
  - [ ] `docs/src/content/docs/api-reference.mdx` — API Reference
- [ ] Task 4: Create GitHub Actions workflow (AC: 7, 8, 11)
  - [ ] Create `.github/workflows/docs.yml` with path filter, Pages permissions, and deploy steps
  - [ ] Create `docs/public/CNAME` with `docs.reform-lab.eu`
- [ ] Task 5: Update VSCode tasks (AC: 9, 10)
  - [ ] Remove 3 old MkDocs tasks by exact label
  - [ ] Add "Docs: Dev Server (localhost:4322)" task matching Website task pattern
- [ ] Task 6: Remove MkDocs configuration (AC: 10)
  - [ ] Delete `mkdocs.yml`
  - [ ] Remove `docs` dependency group from `pyproject.toml`
  - [ ] Run `uv lock` to update `uv.lock`
  - [ ] Verify `uv sync --locked --all-extras --dev` still succeeds
- [ ] Task 7: Verify build and dev server (AC: all)
  - [ ] `npm run build` in `docs/` — zero errors, `dist/` exists, `dist/CNAME` present
  - [ ] `npm run dev` in `docs/` — site loads at localhost:4322
  - [ ] All 6 pages navigable, light/dark mode with correct fonts
  - [ ] `uv sync --locked --all-extras --dev` at repo root succeeds

## Dev Notes

### Primary Implementation Reference

The **tech spec** is the authoritative guide: `_bmad-output/implementation-artifacts/tech-spec-scaffold-starlight-docs.md`. It contains exact file contents, code snippets, and detailed rationale for every task. Read it first.

### Tech Spec Errata (bugs found during story creation)

**BUG: Wrong directory name in VSCode task command.** The tech spec (Task 5, line 211) uses `cd docs-site` in the VSCode task command. The correct directory is `docs`. Fix the command to: `source ~/.nvm/nvm.sh && cd docs && nvm use && npm run dev`. Same bug in Task 7 verification commands (lines 249–250).

### Critical Version Guardrails

| Dependency | Pin | Rationale |
|---|---|---|
| `astro` | `^5.7.10` | Must match `website/` project. **DO NOT use Astro 6.x** — it requires Node 22+ and drops Node 20 support. |
| `@astrojs/starlight` | `^0.33` | Starlight 0.38+ requires Astro 6. Stay on 0.33–0.37 range. Check latest compatible version at install time. |
| `@astrojs/check` | `^0.9.4` | Match `website/package.json` |
| `typescript` | `^5.7.3` | Match `website/package.json` |
| `@fontsource-variable/inter` | `^5.2.8` | Match `website/package.json` |
| `@fontsource/ibm-plex-mono` | `^5.2.7` | Match `website/package.json` |
| Node.js | `20.19.6` | From `website/.nvmrc`. **DO NOT use Node 22+** |

**Why not latest?** As of 2026-03-23, Astro 6.0.8 and Starlight 0.38.2 are the latest releases. Astro 6 drops Node 18/20 support and requires Node 22+. The existing `website/` project uses Astro 5.7.10 on Node 20.19.6 — the docs site must match to avoid maintaining two incompatible Node environments.

### Starlight Theming

**Two mechanisms — fonts vs. accent colors:**

1. **Fonts** — via custom CSS with Starlight CSS variables:
   ```css
   :root {
     --sl-font: 'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
     --sl-font-mono: 'IBM Plex Mono', Consolas, Monaco, monospace;
   }
   ```
   Font CSS is loaded via `customCss` array in `astro.config.mjs`. Font values are from `website/src/styles/brand-theme.css` — do NOT import that file (it uses Tailwind v4 `@theme` blocks, incompatible with Starlight).

2. **Accent colors** — The tech spec states "via Starlight's config API in `astro.config.mjs`, NOT CSS custom properties." However, Starlight's standard theming mechanism uses CSS custom properties (`--sl-color-accent-low`, `--sl-color-accent`, `--sl-color-accent-high`). For the scaffold, **use Starlight's default accent colors** — they are acceptable. Custom accent colors (Blue 600 `#2563eb` from brand) can be added in a future iteration if needed.

**No Tailwind in docs.** Starlight has its own styling system. The `website/` uses Tailwind v4 but the docs site does NOT.

### Brand Identity Reference

From `website/src/styles/brand-theme.css`:

| Token | Value | Usage |
|---|---|---|
| `--font-sans` | `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` | Body text |
| `--font-mono` | `"IBM Plex Mono", Consolas, Monaco, monospace` | Code blocks |
| Logo mark | Slate 700 `#334155` + Emerald 500 `#10B981` | Fixed, non-negotiable |
| Primary accent | Blue 600 `#2563eb` | CTAs, focus states |
| Brand accent | Emerald 500 `#10B981` | Logo, success, validated |
| Surface light | `#ffffff` | Light mode background |
| Surface dark | `#0f172a` (Slate 900) | Dark mode background |

### Port Allocation

| Service | Port |
|---|---|
| Website (Astro marketing) | 4321 |
| **Docs (Starlight)** | **4322** |
| Frontend (Vite/React) | 4173 |
| Backend (FastAPI) | 8000 |

Port 4322 is set in `astro.config.mjs` `server.port` only — NOT duplicated on CLI or in the VSCode task.

### GitHub Actions Pattern

New workflow `docs.yml` follows existing patterns:
- `actions/checkout@v6` (from `ci.yml`)
- `actions/setup-node@v4` with `node-version-file: 'docs/.nvmrc'`
- `npm ci` + `npm run build` in `docs/`
- **Critical ordering:** `actions/configure-pages@v4` → `actions/upload-pages-artifact@v3` → `actions/deploy-pages@v4`. The configure step MUST come before upload/deploy or the deploy step fails with a permissions error.
- Permissions: `pages: write`, `id-token: write`
- Environment: `github-pages`
- Concurrency: `group: pages`, `cancel-in-progress: false`

### Files to Create

| File | Purpose |
|---|---|
| `docs/package.json` | Starlight project manifest |
| `docs/package-lock.json` | Lockfile (generated by `npm install`, committed) |
| `docs/astro.config.mjs` | Starlight config, sidebar, port 4322 |
| `docs/tsconfig.json` | TypeScript strict config |
| `docs/.nvmrc` | Node 20.19.6 |
| `docs/src/styles/custom.css` | Brand font overrides |
| `docs/src/content/docs/index.mdx` | Landing page |
| `docs/src/content/docs/use-cases.mdx` | Use Cases |
| `docs/src/content/docs/getting-started.mdx` | Getting Started |
| `docs/src/content/docs/domain-model.mdx` | Domain Model |
| `docs/src/content/docs/contributing.mdx` | Contributing |
| `docs/src/content/docs/api-reference.mdx` | API Reference |
| `docs/public/CNAME` | GitHub Pages custom domain |
| `.github/workflows/docs.yml` | GitHub Pages deploy workflow |

### Files to Modify

| File | Change |
|---|---|
| `.vscode/tasks.json` | Remove 3 MkDocs tasks, add 1 Starlight task |
| `pyproject.toml` | Remove `docs` dependency group from `[dependency-groups]` |

### Files to Delete

| File | Reason |
|---|---|
| `mkdocs.yml` | MkDocs replaced by Starlight |

### Existing `docs/` Contents

The `docs/` directory currently contains only `docs/.archive/project-scan-report-2026-02-25.json`. This is a stale artifact — the Starlight project will be scaffolded alongside it. The `.archive/` directory can remain or be cleaned up at developer discretion.

### VSCode Tasks — Exact Labels to Remove

1. `"Docs: Install Dependencies"` — was `uv sync --group docs`
2. `"Docs: Serve (localhost:8100)"` — was `uv run --group docs mkdocs serve --dev-addr 127.0.0.1:8100`
3. `"Docs: Build Static Site"` — was `uv run --group docs mkdocs build`

Replace with one task: `"Docs: Dev Server (localhost:4322)"` using same pattern as `"Website: Dev Server (localhost:4321)"`. See tech spec Task 5 for exact JSON (but fix `cd docs-site` → `cd docs`).

### pyproject.toml — Exact Block to Remove

Under `[dependency-groups]`, remove:
```toml
docs = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.5.0",
    "pymdown-extensions>=10.7.0",
]
```

Then run `uv lock` to regenerate `uv.lock`. This is safe because CI uses `uv sync --locked --all-extras --dev` which installs `[project.optional-dependencies]` extras and the `dev` dependency group — never the `docs` group.

### Sidebar Configuration

Use manual sidebar links in `astro.config.mjs` (not autogenerate) to control exact ordering:
```js
sidebar: [
  { label: 'Home', link: '/' },
  { label: 'Use Cases', link: '/use-cases/' },
  { label: 'Getting Started', link: '/getting-started/' },
  { label: 'Domain Model', link: '/domain-model/' },
  { label: 'Contributing', link: '/contributing/' },
  { label: 'API Reference', link: '/api-reference/' },
],
```

Note: Starlight may display the Home/index page as the site title/logo link rather than as a sidebar item. This is acceptable per AC 5.

### Content Pages

All pages use `.mdx` extension (not `.md`) to support future React component embedding (Stories 19.5–19.6). Each page needs frontmatter with `title` and `description`. Placeholder content should be brief — 2-3 sentences indicating what content will be added in Stories 19.2–19.4.

### Testing Strategy

No automated tests for static docs site. Quality gates:
- `npm run build` completes with zero errors
- Visual verification of all 6 pages in both light/dark modes
- Font verification (Inter body, IBM Plex Mono code)
- `uv sync --locked --all-extras --dev` at repo root succeeds

### Risks

| Risk | Mitigation |
|---|---|
| Starlight version incompatibility | Pin to `^0.33`; verify compatible with Astro 5.7.10 at install time |
| GitHub Pages not enabled | Requires repo admin to set Settings → Pages → Source: "GitHub Actions". Deploy step will fail without this. Use `workflow_dispatch` to test build portion. |
| Starlight content collection structure | Must use `src/content/docs/` directory. If using `npm create astro --template starlight` this is auto-configured. If manual, ensure correct structure. |

### Project Structure Notes

- `docs/` is fully independent from `website/` (Astro marketing) and `frontend/` (React app)
- Three separate surfaces: `reform-lab.eu` (sell) / `docs.reform-lab.eu` (use) / `app.reformlab.fr` (try)
- BMAD planning artifacts in `_bmad-output/planning-artifacts/` are NOT part of the docs site
- The docs site targets **admin/policy personas first**, developers second
- **5-sentence rule:** no page exceeds 5 sentences before a visual or interactive element (enforced in Stories 19.2–19.4 when real content is added)

### References

- [Tech Spec: `_bmad-output/implementation-artifacts/tech-spec-scaffold-starlight-docs.md`] — Primary implementation reference with exact code snippets
- [Brainstorming: `_bmad-output/brainstorming/brainstorming-documentation-strategy-2026-03-23.md`] — Strategic decisions, audience analysis, 6-page structure rationale
- [Brand Theme: `website/src/styles/brand-theme.css`] — Font families and color tokens
- [Website package.json: `website/package.json`] — Astro 5.7.10 and font package versions to match
- [Website .nvmrc: `website/.nvmrc`] — Node 20.19.6
- [VSCode Tasks: `.vscode/tasks.json`] — Existing tasks to modify (lines 397–516)
- [CI Workflow: `.github/workflows/ci.yml`] — `actions/checkout@v6` pattern reference
- [Deploy Workflow: `.github/workflows/deploy.yml`] — Concurrency and branch trigger patterns
- [Epics: `_bmad-output/planning-artifacts/epics.md`] — Epic 19 definition and scope notes
- [Architecture: `_bmad-output/planning-artifacts/architecture.md`] — System overview and tech stack

## Dev Agent Record

### Agent Model Used

_(to be filled during implementation)_

### Debug Log References

_(to be filled during implementation)_

### Completion Notes List

_(to be filled during implementation)_

### File List

_(to be filled during implementation)_
