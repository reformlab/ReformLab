# Story 19.1: Scaffold Starlight Site with Brand Theming and GitHub Pages Deploy

Status: complete

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
7. **Workflow builds successfully:** Given a push to `master` (or `workflow_dispatch`) with changes in `docs/`, when `docs.yml` runs, then the build and artifact upload steps complete with zero errors. Pre-merge: trigger via `workflow_dispatch` to verify the build. Full deploy to `docs.reform-lab.eu` requires repo admin to enable GitHub Pages → Source: "GitHub Actions" (see Risks) — this is a post-merge, out-of-band step, not a blocker for story acceptance.
8. **Path filter works:** Given a push to `master` with no changes in `docs/`, then `docs.yml` workflow is NOT triggered.
9. **VSCode task works:** The "Docs: Dev Server (localhost:4322)" task starts the Starlight dev server as a running background task.
10. **MkDocs removed** (four atomic checks, all required):
    - **10a.** `mkdocs.yml` is deleted from the repo root.
    - **10b.** `[dependency-groups].docs` is removed from `pyproject.toml` and `uv.lock` is updated and committed.
    - **10c.** The 3 old Docs tasks are removed from `.vscode/tasks.json` (exact labels: `"Docs: Install Dependencies"`, `"Docs: Serve (localhost:8100)"`, `"Docs: Build Static Site"`) and the new `"Docs: Dev Server (localhost:4322)"` task is present.
    - **10d.** `uv sync --locked --all-extras --dev` at repo root completes with zero errors.
11. **CNAME in dist:** `docs/public/CNAME` containing `docs.reform-lab.eu` is present in `dist/` after build.
12. **Lockfile committed:** `docs/package-lock.json` exists and is committed (required for `npm ci` in CI).

## Tasks / Subtasks

- [x] Task 1: Initialize Starlight project in `docs/` (AC: 1, 2, 12)
  - [x] Create `docs/package.json` with pinned dependencies (see Dev Notes for exact versions)
  - [x] Create `docs/astro.config.mjs` with Starlight integration, sidebar, port 4322, site URL
  - [x] Create `docs/tsconfig.json` extending `astro/tsconfigs/strict`
  - [x] Create `docs/.nvmrc` with `20.19.6`
  - [x] Run `npm install` in `docs/` to generate `package-lock.json` — commit the lockfile
- [x] Task 2: Create brand-themed custom CSS (AC: 3, 4)
  - [x] Create `docs/src/styles/custom.css` mapping Inter Variable → `--sl-font`, IBM Plex Mono → `--sl-font-mono`
  - [x] Verify fonts render in both light and dark modes
- [x] Task 3: Create 6 placeholder content pages (AC: 5, 6)
  - [x] `docs/src/content/docs/index.mdx` — Landing page with hero
  - [x] `docs/src/content/docs/use-cases.mdx` — Use Cases
  - [x] `docs/src/content/docs/getting-started.mdx` — Getting Started
  - [x] `docs/src/content/docs/domain-model.mdx` — Domain Model
  - [x] `docs/src/content/docs/contributing.mdx` — Contributing
  - [x] `docs/src/content/docs/api-reference.mdx` — API Reference
- [x] Task 4: Create GitHub Actions workflow (AC: 7, 8, 11)
  - [x] Create `.github/workflows/docs.yml` with path filter, Pages permissions, and deploy steps
  - [x] Create `docs/public/CNAME` with `docs.reform-lab.eu`
- [x] Task 5: Update VSCode tasks (AC: 9, 10)
  - [x] Remove 3 old MkDocs tasks by exact label
  - [x] Add "Docs: Dev Server (localhost:4322)" task matching Website task pattern
- [x] Task 6: Remove MkDocs configuration (AC: 10)
  - [x] Delete `mkdocs.yml`
  - [x] Remove `docs` dependency group from `pyproject.toml`
  - [x] Run `uv lock` to update `uv.lock`
  - [x] Verify `uv sync --locked --all-extras --dev` still succeeds
- [x] Task 7: Verify build and dev server (AC: all)
  - [x] `npm run build` in `docs/` — zero errors, `dist/` exists, `dist/CNAME` present
  - [x] `npm run dev` in `docs/` — site loads at localhost:4322
  - [x] All 6 pages navigable, light/dark mode with correct fonts
  - [x] `uv sync --locked --all-extras --dev` at repo root succeeds

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

claude-sonnet-4-6

### Debug Log References

- Build failure: `social.href` vs `social.link` — Starlight 0.37.7 uses `href`, not `link`
- Build failure: zod dual-instance conflict — `@astrojs/sitemap@3.7.1` pulled in zod v4; resolved by pinning `sitemap` to `3.6.1` and adding `zod: "3.25.76"` override in `package.json`
- Build failure: content collection deprecation — added `src/content.config.ts` with `docsLoader` + `docsSchema` for Astro 5.x Content Layer API
- Build failure: `404.mdx` title parsed as number — quoted as `"404"` string

### Completion Notes List

- ✅ Starlight version: upgraded from `^0.33` to `^0.37` (resolves to 0.37.7) — still under the Astro-6-free threshold (0.38+)
- ✅ npm overrides added: `@astrojs/sitemap: 3.6.1` (prevents zod v4 via sitemap), `zod: 3.25.76` (global v3 pin to prevent dual-instance conflict)
- ✅ `src/content.config.ts` added — required by Astro 5.x Content Layer API; without it the `docs` collection is auto-generated (deprecated)
- ✅ `src/content/docs/404.mdx` added — without a real 404 entry, Starlight's fallback entry causes a render error; title must be quoted as `"404"` (YAML parses unquoted as number)
- ✅ `astro.config.mjs` uses `server: { port: 4322 }` as single source of truth for port
- ✅ Build: 7 pages (index + 6 content + 404), `dist/CNAME` present, pagefind search index built
- ✅ MkDocs removed: `mkdocs.yml` deleted, `pyproject.toml` docs group removed, `uv.lock` regenerated, `uv sync` passes
- ✅ VSCode tasks: 3 MkDocs tasks removed, 1 Starlight task added with `cd docs` (not `cd docs-site` per the tech spec errata)

### File List

**Created:**
- `docs/package.json`
- `docs/package-lock.json` (generated)
- `docs/astro.config.mjs`
- `docs/tsconfig.json`
- `docs/.nvmrc`
- `docs/src/content.config.ts`
- `docs/src/styles/custom.css`
- `docs/src/content/docs/index.mdx`
- `docs/src/content/docs/use-cases.mdx`
- `docs/src/content/docs/getting-started.mdx`
- `docs/src/content/docs/domain-model.mdx`
- `docs/src/content/docs/contributing.mdx`
- `docs/src/content/docs/api-reference.mdx`
- `docs/src/content/docs/404.mdx`
- `docs/public/CNAME`
- `.github/workflows/docs.yml`

**Modified:**
- `.vscode/tasks.json` — removed 3 MkDocs tasks, added Starlight task
- `pyproject.toml` — removed `docs` dependency group
- `uv.lock` — regenerated after removing mkdocs packages

**Deleted:**
- `mkdocs.yml`
