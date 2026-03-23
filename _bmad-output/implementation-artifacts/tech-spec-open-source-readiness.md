---
title: 'Open-Source Readiness Package'
slug: 'open-source-readiness'
created: '2026-03-23'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python 3.13', 'typescript', 'react 19', 'fastapi', 'vite 7', 'uv']
files_to_modify: ['README.md', 'frontend/package.json', 'CITATION.cff', 'CONTRIBUTING.md', '.github/ISSUE_TEMPLATE/bug_report.md', '.github/ISSUE_TEMPLATE/feature_request.md', 'scripts/add-spdx-headers.py']
code_patterns: ['py files start with docstrings (triple-quote)', 'ts/tsx files start with imports or JSDoc comments', 'all __init__.py are non-empty (have docstrings)', 'no existing SPDX headers anywhere']
test_patterns: ['pytest for Python (tests/)', 'vitest for TypeScript (frontend/src/__tests__)', 'test files start with docstrings']
---

# Tech-Spec: Open-Source Readiness Package

**Created:** 2026-03-23

## Overview

### Problem Statement

The repo has AGPL v3 LICENSE and `pyproject.toml` set correctly, but lacks the standard open-source signals: no SPDX headers on ~479 source files (.py, .ts, .tsx), no `license` field in `frontend/package.json`, a minimal README without installation/usage/license sections, no CONTRIBUTING.md, no issue templates, and no CITATION.cff for academic use. This makes the project look private/unfinished to potential contributors, grant evaluators (NGI Zero, Sovereign Tech Fund), and the OpenFisca community.

### Solution

Add the minimum viable set of open-source community files and metadata, following conventions of scientific Python projects (OpenFisca, scikit-learn). Keep everything lean and scientific — no marketing language. Use a script for SPDX headers across all source files.

### Scope

**In Scope:**
- SPDX license headers on all `.py`, `.ts`, `.tsx` source files (via script)
- `license` field in `frontend/package.json`
- README rewrite: scientific abstract-style (problem, method, quick start, architecture one-liner, license, citation)
- `CONTRIBUTING.md` (minimal: setup, standards, submitting)
- `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`
- `CITATION.cff` for academic citation

**Out of Scope:**
- Code of Conduct
- PR template (defer until contributors exist)
- Changelog / release process
- GitHub Sponsors setup
- CI changes
- Documentation site
- Security policy (SECURITY.md)

## Context for Development

### Codebase Patterns

- Python source: `src/reformlab/` — 26 `__init__.py` (all non-empty with docstrings) + 121 other `.py` files
- Python tests: `tests/` — 193 `.py` files (start with docstrings like `"""Tests for ...`)
- Frontend source: `frontend/src/` — 139 `.ts`/`.tsx` files (start with imports or JSDoc `/**` comments)
- Total files needing SPDX headers: ~479 (147 src + 193 tests + 139 frontend)
- LICENSE file: Already AGPL v3 with copyright Lucas Vivier 2026
- pyproject.toml: Already `license = "AGPL-3.0-or-later"`
- frontend/package.json: Missing `license` field — `"private": true` set, no license key
- No existing SPDX headers on any source files
- Existing CI: `.github/workflows/ci.yml` (ruff, mypy, pytest)
- Deployment: Kamal 2, GHCR, Hetzner
- SPDX header insertion: must go BEFORE existing docstrings/comments (first lines of file)

### Files to Reference

| File | Purpose |
| ---- | ------- |
| LICENSE | AGPL v3 full text + copyright notice |
| pyproject.toml | Python package metadata (license already set) |
| frontend/package.json | Frontend package metadata (missing license) |
| README.md | Current minimal README (live service links only) |
| .github/workflows/ci.yml | Existing CI workflow |

### Technical Decisions

- **SPDX header format (Python):** `# SPDX-License-Identifier: AGPL-3.0-or-later` + `# Copyright 2026 Lucas Vivier` as first two lines
- **SPDX header format (TypeScript):** `// SPDX-License-Identifier: AGPL-3.0-or-later` + `// Copyright 2026 Lucas Vivier` as first two lines
- **README style:** Scientific abstract structure inspired by OpenFisca-France — problem, method, quick start, architecture, license, citation
- **CONTRIBUTING.md:** Three sections only (Setup, Standards, Submitting)
- **CITATION.cff:** CFF v1.2.0 format, minimal fields
- **Script for headers:** Python script to prepend SPDX headers, idempotent (skip files that already have them)
- **No shebang handling needed:** No `.py` files use shebangs in this project

## Implementation Plan

### Tasks

- [x] Task 1: Create SPDX header script
  - File: `scripts/add-spdx-headers.py`
  - Action: Create a Python script that:
    - Walks `src/`, `tests/`, `frontend/src/` directories
    - For `.py` files: prepends `# SPDX-License-Identifier: AGPL-3.0-or-later\n# Copyright 2026 Lucas Vivier\n` before existing content
    - For `.ts`/`.tsx` files: prepends `// SPDX-License-Identifier: AGPL-3.0-or-later\n// Copyright 2026 Lucas Vivier\n` before existing content
    - Idempotent: skips files whose first line already contains `SPDX-License-Identifier`
    - Prints count of modified vs skipped files
    - Uses `pathlib` only, no external deps
  - Notes: Run once, then delete or keep in `scripts/` for future use

- [x] Task 2: Run SPDX header script
  - File: All `.py`, `.ts`, `.tsx` files in `src/`, `tests/`, `frontend/src/`
  - Action: Execute `python scripts/add-spdx-headers.py` and verify output
  - Notes: Expect ~479 files modified, 0 skipped (no existing headers)

- [x] Task 3: Add license field to frontend/package.json
  - File: `frontend/package.json`
  - Action: Add `"license": "AGPL-3.0-or-later"` after the `"version"` field
  - Notes: Standard SPDX identifier, matches pyproject.toml

- [x] Task 4: Create CITATION.cff
  - File: `CITATION.cff`
  - Action: Create CFF v1.2.0 file with:
    - `cff-version: 1.2.0`
    - `title: ReformLab`
    - `message: "If you use this software, please cite it as below."`
    - `type: software`
    - `authors:` with Lucas Vivier entry
    - `repository-code:` GitHub URL
    - `license: AGPL-3.0-or-later`
    - `keywords:` microsimulation, policy-analysis, openfisca, carbon-tax, distributional-analysis
  - Notes: Minimal fields. No `doi` or `version` until first release.

- [x] Task 5: Rewrite README.md
  - File: `README.md`
  - Action: Replace current content with scientific abstract-style README:
    1. **Title + badges** — license badge, CI badge, Python version badge
    2. **One-liner description** — "OpenFisca-first environmental policy analysis platform"
    3. **What it does** — 3 sentences: what problem, what method, what output. Concrete example: "Simulate a €100/tCO2 carbon tax across French households over 10 years."
    4. **Quick start** — `git clone`, `uv sync`, `uv run pytest` (4 commands to a running result)
    5. **Architecture** — One sentence + Mermaid diagram showing: Data Layer → Scenario Templates → Dynamic Orchestrator → Indicators → Governance → Interfaces, with OpenFisca as external computation backend
    6. **Live services** — Keep existing table (reform-lab.eu links)
    7. **License** — "AGPL-3.0-or-later. See [LICENSE](LICENSE)."
    8. **Citation** — Point to CITATION.cff
  - Notes: No marketing language. Scientific tone. Inspired by OpenFisca-France README structure.

- [x] Task 6: Create CONTRIBUTING.md
  - File: `CONTRIBUTING.md`
  - Action: Create minimal contributor guide with three sections:
    1. **Setup** — Clone, `uv sync --all-extras`, `cd frontend && npm install`
    2. **Standards** — `uv run ruff check src/ tests/`, `uv run mypy src/`, `npm run typecheck`, `npm run lint`, `uv run pytest`, `npm test`. All must pass.
    3. **Submitting** — Fork, create branch, make changes, open PR against `master`
  - Notes: No Code of Conduct reference. No governance section. Add those when contributors appear.

- [x] Task 7: Create GitHub issue templates
  - File: `.github/ISSUE_TEMPLATE/bug_report.md`
  - Action: Create bug report template with YAML frontmatter (`name`, `about`, `labels: bug`) and sections: Description, Steps to Reproduce, Expected Behavior, Environment (Python version, OS)
  - File: `.github/ISSUE_TEMPLATE/feature_request.md`
  - Action: Create feature request template with YAML frontmatter (`name`, `about`, `labels: enhancement`) and sections: Problem, Proposed Solution, Alternatives Considered
  - Notes: Keep both templates short (under 30 lines each)

- [x] Task 8: Verify CI passes
  - Action: Run `uv run ruff check src/ tests/` and `uv run mypy src/` and `cd frontend && npm run typecheck && npm run lint`
  - Notes: SPDX comment headers should not affect ruff/mypy/typecheck. Verify no false positives.

### Acceptance Criteria

- [ ] AC 1: Given any `.py` file in `src/` or `tests/`, when reading its first line, then it contains `# SPDX-License-Identifier: AGPL-3.0-or-later` and the second line contains `# Copyright 2026 Lucas Vivier`
- [ ] AC 2: Given any `.ts` or `.tsx` file in `frontend/src/`, when reading its first line, then it contains `// SPDX-License-Identifier: AGPL-3.0-or-later` and the second line contains `// Copyright 2026 Lucas Vivier`
- [ ] AC 3: Given `frontend/package.json`, when parsed as JSON, then `license` field equals `"AGPL-3.0-or-later"`
- [ ] AC 4: Given `CITATION.cff`, when parsed as YAML, then it contains valid CFF v1.2.0 with `title: ReformLab` and `license: AGPL-3.0-or-later`
- [ ] AC 5: Given `README.md`, when reading its content, then it contains: a license badge, a quick start section with install commands, an architecture section, and a citation section
- [ ] AC 6: Given `CONTRIBUTING.md`, when reading its content, then it contains Setup, Standards, and Submitting sections with the exact lint/test commands
- [ ] AC 7: Given `.github/ISSUE_TEMPLATE/bug_report.md`, when GitHub parses it, then it renders a bug report form with Description, Steps to Reproduce, Expected Behavior, and Environment sections
- [ ] AC 8: Given `.github/ISSUE_TEMPLATE/feature_request.md`, when GitHub parses it, then it renders a feature request form with Problem, Proposed Solution, and Alternatives Considered sections
- [ ] AC 9: Given the SPDX headers are added, when running `uv run ruff check src/ tests/` and `uv run mypy src/` and `npm run typecheck` and `npm run lint`, then all pass with zero errors

## Additional Context

### Dependencies

None — all changes are metadata/documentation files and SPDX comment headers. No new packages or services.

### Testing Strategy

- **Automated:** Run existing CI checks (ruff, mypy, pytest, typecheck, lint) after SPDX headers are added — all must pass
- **Script verification:** SPDX header script prints counts; verify ~479 files modified
- **Spot check:** Manually verify 3 Python files and 3 TypeScript files have correct header format and existing content preserved
- **CITATION.cff:** Parse with `python -c "import yaml; yaml.safe_load(open('CITATION.cff'))"`

### Notes

- Party Mode feedback (Winston, John, Paige): defer PR template, add CITATION.cff, use script for headers, README = scientific abstract style
- Reference projects for README: OpenFisca-France, scikit-learn, PyArrow
- Grant evaluators (NGI Zero, Sovereign Tech Fund) will judge the repo — issue templates provide "ready for contributors" signal at low cost
- The SPDX header script can be kept in `scripts/` for adding headers to future files, or deleted after use
- CITATION.cff will need `version` and `date-released` fields added at first official release
