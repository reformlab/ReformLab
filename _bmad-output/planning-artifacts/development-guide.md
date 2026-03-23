# Development Guide — ReformLab

**Generated:** 2026-03-08
**Status:** Phase 2 Complete

## Prerequisites

| Tool | Version | Purpose |
| ---- | ------- | ------- |
| Python | 3.13+ | Backend runtime |
| uv | latest | Python package manager (replaces pip) |
| Node.js | 22+ | Frontend runtime |
| npm | 10+ | Frontend package manager |
| Git | 2.40+ | Version control |

## Getting Started

### Backend Setup

```bash
# Clone and enter the project
git clone <repo-url> reformlab
cd reformlab

# Install Python dependencies (uv resolves from pyproject.toml)
uv sync --all-extras --dev

# Verify installation
uv run pytest tests/ -x --tb=short
```

**What `--all-extras` does:** Installs optional dependency groups — `openfisca` (tax-benefit engine), `server` (FastAPI + uvicorn), and `dev` (pytest, ruff, mypy, nbmake).

### Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm ci

# Start development server (proxies /api/* to localhost:8000)
npm run dev
```

### Running the Full Stack

Open two terminals:

```bash
# Terminal 1: Backend API server
uv run uvicorn reformlab.server.app:create_app --factory --reload --port 8000

# Terminal 2: Frontend dev server
cd frontend && npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies API calls to the backend on port 8000.

## Quality Checks

Run all of these before submitting work. CI enforces them automatically.

### Backend

```bash
# Linting — must produce 0 errors
uv run ruff check src/ tests/

# Type checking — strict mode, all files
uv run mypy src/

# Tests — 3,143 tests, 80%+ coverage required
uv run pytest tests/

# Tests with coverage report
uv run pytest --cov=src/reformlab --cov-report=term-missing tests/

# Notebook validation (CI runs these too)
uv run pytest --nbmake notebooks/quickstart.ipynb notebooks/advanced.ipynb
```

### Frontend

```bash
cd frontend

# TypeScript type checking
npm run typecheck

# ESLint
npm run lint

# Tests
npm test

# Tests in watch mode (during development)
npm run test:watch
```

### All-in-One Check

```bash
# Backend quality gate
uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest tests/

# Frontend quality gate
cd frontend && npm run typecheck && npm run lint && npm test
```

## Project Layout

```text
reformlab/
├── src/reformlab/         # Python package (13 subsystems)
├── frontend/src/          # React SPA (9 screens, 48 components)
├── tests/                 # Python tests (190 files, 3,143 tests)
├── notebooks/             # Jupyter guides
├── examples/              # API/workflow examples
├── config/                # Deployment config (Kamal)
├── scripts/               # Utilities
├── data/                  # Population data, emission factors
└── docs/                  # Generated documentation
```

See [Source Tree Analysis](./source-tree-analysis.md) for the full annotated tree.

## Coding Conventions

### Python

- **Style:** ruff with rules E, F, I, W. Line length 110.
- **Types:** mypy strict mode. All public functions fully typed.
- **Immutability:** Domain types use `@dataclass(frozen=True)`.
- **Data:** PyArrow Tables for all tabular data. No pandas in core.
- **Errors:** Three-field pattern: `what`, `why`, `fix`.
- **Testing:** pytest. Test files mirror source structure. Fixtures in `tests/fixtures/`.
- **Imports:** Absolute imports only. No circular dependencies between subsystems.

### TypeScript / React

- **Style:** ESLint with typescript-eslint strict rules. React hooks enforcement.
- **Types:** TypeScript 5.9 strict mode. All API types in `api/types.ts`.
- **Components:** Functional components only. React 19 (ref as regular prop).
- **Styling:** Tailwind v4 utility classes. CSS variables for chart colors.
- **State:** Centralized via `AppContext`. Custom hooks for data fetching.
- **Testing:** Vitest + Testing Library. Mock API calls with `vi.mock()`.

### Git

- **Commits:** Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`).
- **Branches:** Feature branches off `master`. PRs for all changes.
- **CI:** All checks must pass before merge.

## Test Markers

The backend test suite uses pytest markers to separate test categories:

```bash
# Default: runs unit tests only (skips integration, scale, network)
uv run pytest tests/

# Include integration tests (requires openfisca-france installed)
uv run pytest -m integration tests/

# Include scale tests (100k–500k population, may be slow)
uv run pytest -m scale tests/

# Include network tests (requires real API access)
uv run pytest -m network tests/

# Include benchmark validation tests
uv run pytest -m benchmark tests/
```

## Common Tasks

### Add a New Policy Template

1. Create a new package under `src/reformlab/templates/your_template/`
2. Define parameter class extending `PolicyParameters`
3. Implement `compute()` and `compare()` functions
4. Register with `register_custom_template()` and `register_policy_type()`
5. Add pack loader functions in `templates/packs/`
6. Add tests in `tests/templates/your_template/`

### Add a New API Endpoint

1. Create route function in `src/reformlab/server/routes/`
2. Add request/response models in `server/models.py`
3. Register router in `server/app.py`
4. Add TypeScript types in `frontend/src/api/types.ts`
5. Add API function in `frontend/src/api/`
6. Add tests in `tests/server/`

### Add a New Orchestrator Step

1. Create a class with `name` property and `execute(year, state)` method
2. It automatically satisfies the `OrchestratorStep` protocol — no registration needed
3. Add it to the step pipeline in your scenario configuration
4. Add tests in `tests/orchestrator/`

## Useful Scripts

```bash
# Generate a synthetic population (Parquet file)
uv run python scripts/generate_synthetic_population.py --size 100000 --seed 42

# Check AI provider usage (Claude, Codex, Gemini)
uv run python scripts/check_ai_usage.py

# Build Docker image
docker build -t reformlab .

# Run overnight build (BMAD story-driven development)
./overnight-build.sh <epic-number>
```

## CI/CD Pipeline

### CI (on every push/PR)

1. Install Python 3.13 + uv
2. `uv sync --locked --all-extras --dev`
3. `ruff check` → `mypy` → `pytest --cov` → `nbmake` (6 notebooks)

### CD (on push to master)

1. Ruby 3.3 + Kamal gem installed
2. Docker Buildx multi-platform build
3. `kamal deploy` to Hetzner VPS
4. Traefik handles HTTPS (Let's Encrypt) for `api.reformlab.fr` and `app.reformlab.fr`

See [Deployment Guide](./deployment-guide.md) for full deployment details.
