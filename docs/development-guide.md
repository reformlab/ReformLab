# Development Guide — ReformLab

**Generated:** 2026-02-28
**Status:** Phase 1 Complete

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.13+ | Required by architecture spec |
| uv | Latest | Python package manager |
| Node.js | 18+ | For frontend development (optional) |
| Git | Latest | Version control |

OpenFisca is an **optional** dependency — core functionality works without it.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/lucas-vivier/reformlab.git
cd reformlab

# Install Python dependencies
uv sync

# Run tests (1374 tests)
uv run pytest

# Type check
uv run mypy src

# Lint
uv run ruff check src tests
```

## Frontend Setup (Optional)

```bash
cd frontend

# Install Node dependencies
npm install

# Start dev server
npm run dev

# Run frontend tests
npm test

# Type check
npm run typecheck

# Lint
npm run lint

# Build for production
npm run build
```

## Package Configuration

### Python (pyproject.toml)

| Tool | Purpose | Command |
|------|---------|---------|
| uv | Dependency management | `uv sync` |
| pytest | Test framework (1374 tests) | `uv run pytest` |
| pytest-cov | Coverage (80%+ enforced) | `uv run pytest --cov` |
| nbmake | Notebook validation | `uv run pytest --nbmake notebooks/*.ipynb` |
| ruff | Linting (E, F, I, W rules) | `uv run ruff check src tests` |
| mypy | Type checking (strict mode) | `uv run mypy src` |

### Frontend (package.json)

| Tool | Purpose | Command |
|------|---------|---------|
| Vite 7 | Dev server + build | `npm run dev` / `npm run build` |
| Vitest | Component tests | `npm test` |
| TypeScript 5.9 | Type checking | `npm run typecheck` |
| ESLint | Linting | `npm run lint` |

## Build Commands

```bash
# === Python ===

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/reformlab --cov-report=term-missing

# Run specific subsystem tests
uv run pytest tests/computation/
uv run pytest tests/templates/
uv run pytest tests/orchestrator/
uv run pytest tests/indicators/
uv run pytest tests/governance/

# Run benchmarks only
uv run pytest -m benchmark

# Validate notebooks (no kernel execution)
uv run pytest --nbmake notebooks/quickstart.ipynb -v
uv run pytest --nbmake notebooks/advanced.ipynb -v

# Lint
uv run ruff check src tests

# Type check
uv run mypy src

# Build Python package
uv build

# === Frontend ===

cd frontend
npm run dev          # Start dev server (Vite)
npm run build        # Production build (tsc + vite)
npm test             # Run vitest
npm run typecheck    # TypeScript check
npm run lint         # ESLint
```

## CI Pipeline

The CI runs on every push and pull request (`.github/workflows/ci.yml`):

1. **Setup:** Python 3.13 via uv with caching
2. **Lint:** `uv run ruff check src tests`
3. **Type check:** `uv run mypy src`
4. **Test:** `uv run pytest --cov=src/reformlab --cov-report=term-missing tests/`
5. **Notebooks:** `uv run pytest --nbmake notebooks/quickstart.ipynb -v`
6. **Notebooks:** `uv run pytest --nbmake notebooks/advanced.ipynb -v`

Coverage threshold: **80%** (enforced in `pyproject.toml`).

## Deployment

Deployment is automated on push to `master` (`.github/workflows/deploy.yml`):

1. **Build:** Docker image from `Dockerfile` (Python 3.13-slim)
2. **Deploy:** Kamal 2 to Hetzner VPS
3. **Domains:** `api.reformlab.fr` (backend), `app.reformlab.fr` (frontend)
4. **TLS:** Let's Encrypt via Traefik

See [Deployment Guide](./deployment-guide.md) for full details.

## Project Structure

```
src/reformlab/          # 72 Python modules across 8 subsystems
tests/                  # 93 test files, 1374 tests
frontend/src/           # 46 TypeScript/React files
notebooks/              # 7 Jupyter notebooks
examples/workflows/     # 3 workflow configuration examples
```

See [Source Tree Analysis](./source-tree-analysis.md) for the full annotated tree.

## Development Conventions

### Code Style

- **Line length:** 110 characters (ruff)
- **Import sorting:** isort-compatible (ruff I rules)
- **Type annotations:** Required on all public functions (mypy strict)
- **Docstrings:** On public API only — internal code uses self-documenting names

### Architecture Rules

1. **Never call OpenFisca directly** — Always go through `ComputationAdapter`
2. **Environmental policy logic is Python code** — No YAML formula strings or custom compilers
3. **Steps are plugins** — Register new orchestrator steps without modifying the engine
4. **Contract failures are blocking** — Field-level validation errors at every ingestion boundary
5. **Manifests are mandatory** — Every run produces a JSON manifest with full lineage
6. **Frozen dataclasses** — All data structures are immutable
7. **Structured errors** — Follow `[What] — [Why] — [How to fix]` pattern

### Testing Requirements

- All code changes require tests
- Tests mirror the source structure (`tests/computation/` tests `src/reformlab/computation/`)
- Adapter interface changes require contract test updates
- Scenario template changes require validation test updates
- Run manifests must be reproducible (seed-controlled)
- Golden file tests validate output determinism

### Git Workflow

- Branch protection on `master` with required status check `check`
- Require branches to be up to date before merging
- All CI checks must pass before merge

## Key Files Reference

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package config, dependencies, tool settings |
| `uv.lock` | Locked dependency versions |
| `Dockerfile` | Container build for deployment |
| `config/deploy.yml` | Kamal deployment configuration |
| `.github/workflows/ci.yml` | CI pipeline definition |
| `.github/workflows/deploy.yml` | Deploy pipeline definition |
| `CLAUDE.md` | AI assistant project instructions |
| `README.md` | Public-facing project readme |

## Related Documentation

- [Project Overview](./project-overview.md) — Executive summary
- [Architecture](./architecture.md) — Design decisions and subsystem details
- [Source Tree Analysis](./source-tree-analysis.md) — Annotated directory structure
- [Deployment Guide](./deployment-guide.md) — Docker + Kamal deployment
- [Compatibility Matrix](./compatibility.md) — OpenFisca version support
