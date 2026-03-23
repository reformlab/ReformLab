---
title: 'Scaffold Astro Starlight Documentation Site'
slug: 'scaffold-starlight-docs'
created: '2026-03-23'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['astro-5.7.10', '@astrojs/starlight', '@fontsource-variable/inter', '@fontsource/ibm-plex-mono', 'typescript', 'github-actions', 'github-pages']
files_to_modify: ['docs/ (new)', '.github/workflows/docs.yml (new)', '.vscode/tasks.json (modify)', 'mkdocs.yml (delete)', 'pyproject.toml (modify)']
code_patterns: ['astro.config.mjs for Starlight config', 'Starlight color config in astro.config.mjs (not CSS custom properties)', 'Starlight custom CSS for fonts only', 'VSCode tasks: nvm + npm run dev pattern with isBackground + problemMatcher']
test_patterns: ['build success = test (npm run build zero errors)', 'no unit tests for static docs site']
---

# Tech-Spec: Scaffold Astro Starlight Documentation Site

**Created:** 2026-03-23

## Overview

### Problem Statement

ReformLab has MkDocs Material configured but never deployed. The brainstorming session decided on Astro Starlight for public-facing documentation at `docs.reform-lab.eu`. The project needs a branded, deployable documentation site with a lean 6-page structure targeting administration/policy personas first, developers second.

### Solution

Replace MkDocs with an Astro Starlight project in `docs/`, apply brand identity from the existing `website/src/styles/brand-theme.css`, set up GitHub Pages deployment via GitHub Actions, create placeholder structure for the 6 planned pages, and add a VSCode task for local preview.

### Scope

**In Scope:**
- Starlight project scaffold in `docs/`
- Brand theming (Inter, IBM Plex Mono, Emerald 500/Slate palette from `brand-theme.css`)
- GitHub Actions workflow for GitHub Pages deploy
- 6 placeholder pages (landing, use cases, getting started, domain model, contributing, API reference)
- Remove `mkdocs.yml`
- VSCode `tasks.json` entry to open docs locally

**Out of Scope:**
- Actual page content (follow-up work)
- Interactive domain model (v2)
- Guided tours (driver.js/shepherd.js — v2)
- DNS configuration for `docs.reform-lab.eu`

## Context for Development

### Codebase Patterns

- Existing Astro website in `website/` uses Astro 5.7.10 — match Astro version
- Brand tokens in `website/src/styles/brand-theme.css` use Tailwind v4 `@theme` blocks — but Starlight does NOT use Tailwind. The docs site uses Starlight's own theming: accent colors via `astro.config.mjs` color config, fonts via custom CSS with plain `:root` variables.
- VSCode tasks pattern: `source ~/.nvm/nvm.sh && cd <dir> && nvm use && npm run dev` with `isBackground: true`
- Background task problemMatcher for Astro: `beginsPattern: "^\\s*astro"`, `endsPattern: "localhost"`
- Existing MkDocs tasks to be replaced (exact labels): `"Docs: Install Dependencies"`, `"Docs: Serve (localhost:8100)"`, `"Docs: Build Static Site"`
- `pyproject.toml` has `docs` dependency group (3 packages: `mkdocs`, `mkdocs-material`, `pymdown-extensions`) to remove
- CI runs on `[push, pull_request]`; deploy runs on push to `master`; CI uses `uv sync --locked --all-extras --dev` which does NOT install the `docs` group, so removing it won't affect CI
- `docs/` directory is now empty — previous content moved to `_bmad-output/planning-artifacts/` or deleted. Starlight project will be scaffolded directly in `docs/`.
- Node version: `website/.nvmrc` specifies `20.19.6` — new project must match

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `website/src/styles/brand-theme.css` | Brand tokens: fonts (Inter, IBM Plex Mono), colors (Emerald 500, Slate, Blue 600 accent) |
| `website/package.json` | Reference for Astro 5.7.10, font packages, Tailwind v4 versions |
| `.github/workflows/ci.yml` | CI pattern: `actions/checkout@v6`, `on: [push, pull_request]` |
| `.github/workflows/deploy.yml` | Deploy on push to `master`, Kamal structure for reference |
| `.vscode/tasks.json` | Existing tasks to modify: replace 3 MkDocs tasks, add Starlight task |
| `mkdocs.yml` | To be deleted — MkDocs Material config (stale, references removed files) |
| `pyproject.toml` | Remove `docs` dependency group (search for `docs = [` under `[dependency-groups]`) |
| `_bmad-output/planning-artifacts/project-context.md` | Project conventions (won't change, but informs coding rules) |

### Technical Decisions

- **Starlight theming — two mechanisms:** (1) Accent colors configured in `astro.config.mjs` via Starlight's `color` config (NOT CSS custom properties — that's the legacy API). (2) Fonts configured via custom CSS with `--sl-font` and `--sl-font-mono` variables in `:root`. Do NOT import `brand-theme.css` — copy the raw values.
- **No Tailwind in docs:** Starlight has its own styling system. Adding Tailwind creates conflicts and unnecessary complexity. The `website/` uses Tailwind v4 but the docs site does NOT.
- **Starlight in `docs/`:** Previously held internal docs (now moved to `_bmad-output/planning-artifacts/` or deleted). Independent from `website/` (marketing). Own `package.json`, `astro.config.mjs`, `node_modules/`.
- **GitHub Pages deploy:** New workflow `docs.yml`, triggered on push to `master` when `docs/**` changes. Uses `actions/configure-pages` + `actions/upload-pages-artifact` + `actions/deploy-pages`.
- **Port 4322:** Set in `astro.config.mjs` only (not duplicated on CLI). VSCode task runs `npm run dev` without `--port` flag. Port: website `:4321`, docs `:4322`, frontend `:4173`, backend `:8000`.
- **Node version:** `20.19.6` — matching `website/.nvmrc`. New `docs/.nvmrc` with same value.
- **Replace MkDocs tasks, not append:** Remove `"Docs: Install Dependencies"`, `"Docs: Serve (localhost:8100)"`, `"Docs: Build Static Site"` from `tasks.json`; add `"Docs: Dev Server (localhost:4322)"` for Starlight.
- **`package-lock.json` must be committed:** Required for `npm ci` in GitHub Actions. Run `npm install` during scaffold, commit the lockfile.

## Implementation Plan

### Tasks

- [ ] Task 1: Initialize Starlight project in `docs/`
  - File: `docs/package.json` (new)
  - Action: Run `npm create astro@latest -- --template starlight` in `docs/`, or manually create `package.json` with these exact fields and dependencies:
    ```json
    {
      "name": "reformlab-docs",
      "type": "module",
      "version": "1.0.0",
      "private": true,
      "scripts": {
        "dev": "astro dev",
        "build": "astro build",
        "preview": "astro preview"
      },
      "dependencies": {
        "astro": "^5.7.10",
        "@astrojs/starlight": "^0.33",
        "@astrojs/check": "^0.9.4",
        "typescript": "^5.7.3",
        "@fontsource-variable/inter": "^5.2.8",
        "@fontsource/ibm-plex-mono": "^5.2.7"
      }
    }
    ```
  - Notes: No Tailwind — Starlight has its own styling. `"type": "module"` is required for ES module imports in `astro.config.mjs`. Pin Starlight to `^0.33` (check latest at install time and adjust).
  - File: `docs/astro.config.mjs` (new)
  - Action: Configure Starlight integration with accent color via config API (NOT CSS custom properties):
    ```js
    import { defineConfig } from 'astro/config';
    import starlight from '@astrojs/starlight';

    export default defineConfig({
      site: 'https://docs.reform-lab.eu',
      server: { port: 4322 },
      integrations: [
        starlight({
          title: 'ReformLab Docs',
          social: [
            { icon: 'github', link: 'https://github.com/reformlab/reformlab' },
          ],
          customCss: [
            '@fontsource-variable/inter',
            '@fontsource/ibm-plex-mono/400.css',
            './src/styles/custom.css',
          ],
          sidebar: [
            { label: 'Home', link: '/' },
            { label: 'Use Cases', link: '/use-cases/' },
            { label: 'Getting Started', link: '/getting-started/' },
            { label: 'Domain Model', link: '/domain-model/' },
            { label: 'Contributing', link: '/contributing/' },
            { label: 'API Reference', link: '/api-reference/' },
          ],
        }),
      ],
    });
    ```
  - Notes: The `social` field uses array-of-objects format (NOT the legacy `{ github: url }` object format). The `site` URL is set for canonical URLs but DNS config is out of scope. Port 4322 is set here only — NOT duplicated on CLI.
  - File: `docs/tsconfig.json` (new)
  - Action: `{ "extends": "astro/tsconfigs/strict" }`
  - File: `docs/.nvmrc` (new)
  - Action: Content: `20.19.6` (matches `website/.nvmrc`)
  - **Critical:** After creating `package.json`, run `npm install` to generate `package-lock.json`. Both files must be committed — `npm ci` in GitHub Actions requires the lockfile.

- [ ] Task 2: Create brand-themed custom CSS
  - File: `docs/src/styles/custom.css` (new)
  - Action: Map brand fonts to Starlight CSS variables. Accent colors are handled by Starlight's config API in `astro.config.mjs` (Task 1) — this file is for fonts and any minor overrides only:

    ```css
    /* Brand fonts — values from website/src/styles/brand-theme.css */
    :root {
      --sl-font: 'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      --sl-font-mono: 'IBM Plex Mono', Consolas, Monaco, monospace;
    }
    ```

  - Notes: Font CSS imports are in `astro.config.mjs` `customCss` array (already set in Task 1): `@fontsource-variable/inter` and `@fontsource/ibm-plex-mono/400.css`. Only import weight 400 for IBM Plex Mono — Starlight code blocks use 400 by default and 600 would be unused. Accent colors (Blue 600 `#2563eb`) are configured via Starlight's `color` option in `astro.config.mjs` if needed in a future iteration — the default Starlight accent is acceptable for the scaffold. Verify both light and dark modes render correctly with brand fonts.

- [ ] Task 3: Create 6 placeholder content pages
  - File: `docs/src/content/docs/index.mdx` (new)
  - Action: Landing page — title "ReformLab", hero with tagline "Open-source environmental policy analysis", placeholder for domain model diagram and demo CTA
  - File: `docs/src/content/docs/use-cases.mdx` (new)
  - Action: Use cases page — title "Use Cases", placeholder card grid description, note that 4-6 cards will be added in Story 19.2
  - File: `docs/src/content/docs/getting-started.mdx` (new)
  - Action: Getting started page — title "Getting Started", placeholder 4-step outline (population, policy, engine, simulate)
  - File: `docs/src/content/docs/domain-model.mdx` (new)
  - Action: Domain model page — title "Domain Model", placeholder listing the 5-6 core objects (Population, Policy, Engine, Simulation, Results)
  - File: `docs/src/content/docs/contributing.mdx` (new)
  - Action: Contributing page — title "Contributing", placeholder linking to repo CONTRIBUTING.md
  - File: `docs/src/content/docs/api-reference.mdx` (new)
  - Action: API reference page — title "API Reference", placeholder for condensed REST + Python API
  - Notes: All pages should have frontmatter with `title` and `description`. Each page should contain a brief placeholder paragraph indicating what content will be added in Stories 19.2–19.4. Use `.mdx` extension for future React component embedding.

- [ ] Task 4: Create GitHub Actions workflow for GitHub Pages
  - File: `.github/workflows/docs.yml` (new)
  - Action: Create workflow with:
    - `name: Docs`
    - Trigger: `on: push: branches: [master], paths: ['docs/**']` + `workflow_dispatch`
    - Permissions: `pages: write`, `id-token: write`
    - Concurrency: `group: pages`, `cancel-in-progress: false`
    - Environment: `github-pages`
    - Steps (in order):
      1. `actions/checkout@v6`
      2. Setup Node via `actions/setup-node@v4` with `node-version-file: 'docs/.nvmrc'`
      3. `npm ci` in `docs/` (requires `package-lock.json` — committed in Task 1)
      4. `npm run build` in `docs/`
      5. `actions/configure-pages@v4` (REQUIRED before deploy — configures Pages API)
      6. `actions/upload-pages-artifact@v3` with `path: docs/dist/`
      7. `actions/deploy-pages@v4`
  - File: `docs/public/CNAME` (new)
  - Action: Content: `docs.reform-lab.eu` — included in build output for future DNS setup
  - Notes: `configure-pages` must come before `upload-pages-artifact` and `deploy-pages`. Without it, the deploy step will fail with a permissions/configuration error. The `CNAME` file in `public/` is automatically copied to `dist/` during build. DNS setup is out of scope for this story.
  - **Testing note:** AC 7/AC 8 (deploy + path filter) can only be fully verified after merging to `master` with GitHub Pages enabled in repo settings (Settings → Pages → Source: GitHub Actions). Use `workflow_dispatch` to manually test the build+deploy steps on a branch before merging.

- [ ] Task 5: Update VSCode tasks — replace MkDocs tasks with Starlight
  - File: `.vscode/tasks.json` (modify)
  - Action: Remove these 3 tasks by their exact labels:
    - `"Docs: Install Dependencies"` (command was: `uv sync --group docs`)
    - `"Docs: Serve (localhost:8100)"` (command was: `uv run --group docs mkdocs serve --dev-addr 127.0.0.1:8100`)
    - `"Docs: Build Static Site"` (command was: `uv run --group docs mkdocs build`)
  - Action: Add new task (port comes from `astro.config.mjs`, no `--port` flag needed):

    ```json
    {
      "label": "Docs: Dev Server (localhost:4322)",
      "type": "shell",
      "command": "source ~/.nvm/nvm.sh && cd docs-site && nvm use && npm run dev",
      "options": {
        "cwd": "${workspaceFolder}",
        "shell": { "executable": "/bin/zsh", "args": ["-lc"] }
      },
      "isBackground": true,
      "problemMatcher": {
        "owner": "custom",
        "fileLocation": ["relative", "${workspaceFolder}"],
        "pattern": { "regexp": "^(?!x)x$", "file": 1, "location": 2, "message": 3 },
        "background": {
          "activeOnStart": true,
          "beginsPattern": "^\\s*astro",
          "endsPattern": "localhost"
        }
      },
      "presentation": { "reveal": "always", "panel": "dedicated", "clear": false },
      "runOptions": { "reevaluateOnRerun": true }
    }
    ```

  - Notes: Matches the existing `"Website: Dev Server (localhost:4321)"` task pattern. Port 4322 is configured in `astro.config.mjs` (Task 1) — single source of truth.

- [ ] Task 6: Remove MkDocs configuration
  - File: `mkdocs.yml` (delete)
  - Action: Delete the file entirely
  - File: `pyproject.toml` (modify)
  - Action: Remove the entire `docs` dependency group (search for `docs = [` under the `[dependency-groups]` section). The exact content to remove:
    ```toml
    docs = [
        "mkdocs>=1.6.0",
        "mkdocs-material>=9.5.0",
        "pymdown-extensions>=10.7.0",
    ]
    ```
  - Notes: After removing the dependency group, run `uv lock` to update `uv.lock`. This is safe because CI uses `uv sync --locked --all-extras --dev` — the `--all-extras` flag installs optional dependency groups defined under `[project.optional-dependencies]`, NOT `[dependency-groups]`. The `--dev` flag installs only the `dev` group. So the `docs` group was never installed in CI. Verify by running `uv sync --locked --all-extras --dev` locally after the change.

- [ ] Task 7: Verify build and dev server
  - Action: Run `cd docs-site && npm run build` — must complete with zero errors, `dist/` directory created
  - Action: Run `cd docs-site && npm run dev` — must serve on localhost:4322
  - Action: Verify all 6 pages are navigable via sidebar (note: Home may appear as logo link rather than sidebar item — if so, verify it's accessible by clicking the site title)
  - Action: Verify light and dark mode both render with Inter for body text and IBM Plex Mono for code blocks
  - Action: Verify `dist/CNAME` exists after build (from `public/CNAME`)
  - Action: Run `uv sync --locked --all-extras --dev` at repo root to verify Python CI still works after pyproject.toml change
  - Notes: This is a manual verification step before marking the story as done.

### Acceptance Criteria

- [ ] AC 1: Given a new `docs/` directory, when `npm run build` is run, then the build completes with zero errors and produces static output in `docs/dist/`.
- [ ] AC 2: Given the Starlight dev server, when `npm run dev` is run in `docs/`, then the site is accessible at `http://localhost:4322` with branded theme.
- [ ] AC 3: Given the brand theme, when the site renders in light mode, then headings and body text use Inter, code blocks use IBM Plex Mono.
- [ ] AC 4: Given the brand theme, when the site renders in dark mode, then the same font families apply and the Starlight default dark theme is used.
- [ ] AC 5: Given the site navigation, when a user visits the docs, then all 6 pages are reachable: Home (via site title or sidebar), Use Cases, Getting Started, Domain Model, Contributing, API Reference. Note: Starlight may show the homepage as a logo/title link rather than a sidebar item — this is acceptable as long as the page is accessible.
- [ ] AC 6: Given each placeholder page, when visited, then it has a title, description, and brief placeholder content indicating future work.
- [ ] AC 7: Given a push to `master` with changes in `docs/`, when the `docs.yml` GitHub Actions workflow runs, then the site is built and deployed to GitHub Pages without errors. Note: can only be fully verified after merge with Pages enabled in repo settings; use `workflow_dispatch` for pre-merge build testing.
- [ ] AC 8: Given a push to `master` with no changes in `docs/`, when the workflows run, then the `docs.yml` workflow is NOT triggered (path filter works). Note: verify via GitHub Actions UI after merge.
- [ ] AC 9: Given VSCode, when the user runs the "Docs: Dev Server (localhost:4322)" task, then the Starlight dev server starts and VSCode shows it as a running background task.
- [ ] AC 10: Given the old MkDocs setup, when this story is complete, then `mkdocs.yml` no longer exists, `pyproject.toml` has no `docs` dependency group, the 3 old `Docs:` tasks (`"Docs: Install Dependencies"`, `"Docs: Serve (localhost:8100)"`, `"Docs: Build Static Site"`) are removed from `.vscode/tasks.json`, and `uv sync --locked --all-extras --dev` still succeeds.
- [ ] AC 11: Given `docs/public/CNAME`, when the site is built, then the file is present in `dist/` output (ready for DNS configuration in the future).
- [ ] AC 12: Given the `docs/` directory, when inspected, then `package-lock.json` exists and is committed to version control (required for `npm ci` in CI).

## Additional Context

### Dependencies

- **npm packages (new):** `astro ^5.7.10`, `@astrojs/starlight ^0.33` (pin to minor), `@astrojs/check ^0.9.4`, `typescript ^5.7.3`, `@fontsource-variable/inter ^5.2.8`, `@fontsource/ibm-plex-mono ^5.2.7`
- **GitHub features:** GitHub Pages must be enabled on the repository (Settings → Pages → Source: GitHub Actions) — requires repo admin
- **No runtime dependencies** on `website/` or `frontend/` — `docs/` is fully independent
- **Node 20.19.6** — matching `website/.nvmrc`

### Testing Strategy

- **Build test:** `npm run build` in `docs/` — zero errors, `dist/` output exists, `dist/CNAME` present
- **Dev server test:** `npm run dev` — site loads at localhost:4322
- **Visual check:** Navigate all 6 pages, toggle light/dark mode, confirm Inter (body) and IBM Plex Mono (code)
- **CI regression:** `uv sync --locked --all-extras --dev` at repo root still succeeds after pyproject.toml change
- **Deploy test:** Use `workflow_dispatch` on a branch to test the build portion of `docs.yml` before merging; full deploy test requires merge to `master` with Pages enabled
- **No automated tests:** Static docs site — build success is the quality gate

### Notes

- **Epic:** EPIC-19, Story BKL-1901 (this spec covers Story 19.1 only)
- **Brainstorming session:** `_bmad-output/brainstorming/brainstorming-documentation-strategy-2026-03-23.md`
- **Risk — Starlight version compatibility:** Starlight is actively developed; pin to `^0.33` (or whatever is latest at install time) to avoid breaking changes across minor versions
- **Risk — GitHub Pages enablement:** Requires repo admin to enable Pages with "GitHub Actions" source if not already done. Without this, the deploy step will fail silently.
- **Risk — Starlight content collection:** Starlight auto-generates content collection config. If the scaffold uses `npm create astro` template this is handled automatically. If manual creation, ensure `src/content/` is structured correctly — Starlight expects docs in `src/content/docs/`.
- **Future:** Stories 19.2–19.4 will replace placeholder content; Stories 19.5–19.6 add interactivity
- **CNAME:** `docs/public/CNAME` with `docs.reform-lab.eu` is included for convenience but DNS configuration is out of scope
