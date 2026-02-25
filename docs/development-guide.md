# Development Guide — Microsimulation

**Generated:** 2026-02-25
**Status:** Pre-implementation (planned setup)

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.13+ | Required by architecture spec |
| uv | Latest | Python package manager |
| OpenFisca | TBD (version-pinned) | Core computation dependency |
| Git | Latest | Version control |

## Project Setup (Planned)

The project uses standard scientific Python tooling:

```bash
# Clone the repository
git clone <repository-url>
cd Microsimulation

# Install dependencies with uv
uv sync

# Verify installation
uv run python -c "import microsimulation; print(microsimulation.__version__)"
```

## Package Configuration

The project will use `pyproject.toml` for packaging with the following planned tooling:

| Tool | Purpose |
|------|---------|
| `uv` | Dependency management and virtual environments |
| `pytest` | Test framework |
| `ruff` | Linting and formatting |
| `mypy` | Static type checking |

## Build and Run Commands (Planned)

```bash
# Run tests
uv run pytest

# Run fast tests only (adapter/unit)
uv run pytest tests/unit tests/contract

# Run integration tests
uv run pytest tests/integration

# Lint
uv run ruff check .

# Type check
uv run mypy microsimulation/

# Format
uv run ruff format .
```

## CI Strategy (Planned)

The CI pipeline is planned to be split into:

1. **Fast lane:** Adapter contract tests + unit tests (runs on every push)
2. **Slow lane:** Integration and regression tests (runs on PR merge)

Coverage focus areas:
- Adapter contracts (ComputationAdapter interface compliance)
- Orchestrator determinism (same inputs = same outputs)
- Vintage transitions (cohort aging correctness)
- Template correctness (carbon tax, subsidy calculations)

## Environment Configuration

- The project targets **fully offline operation** in the user environment
- No cloud dependencies for core functionality
- Target hardware: single machine with 16GB RAM (laptop-scale)
- Data contracts use CSV/Parquet for interoperability

## Data Setup

The project will work with:
- **Open data (default):** Synthetic populations and public datasets for immediate use
- **Custom data (optional):** Restricted microdata from national statistical offices

No environment variables or API keys are required for core functionality.

## Development Workflow

1. All code changes require tests
2. Adapter interface changes require contract test updates
3. Scenario template changes require validation test updates
4. Run manifests must be reproducible (seed-controlled)
5. PR process TBD (to be established with CONTRIBUTING.md)

## Key Architecture Decisions for Developers

- **Never call OpenFisca directly** — Always go through `ComputationAdapter`
- **Environmental policy logic is Python code** — No YAML formula strings or custom compilers
- **Steps are plugins** — Register new orchestrator steps without modifying the engine
- **Contract failures are blocking** — Field-level validation errors at every ingestion boundary
- **Manifests are mandatory** — Every run produces a JSON manifest with full lineage

## Current State

This project is in the **planning phase**. Implementation has not started. The Phase 1 backlog (7 epics) is defined in the planning artifacts. Development begins with EPIC-1 (Computation Adapter and Data Layer).

## Relevant Documentation

- [Project Overview](./project-overview.md) — High-level project summary
- [Architecture](./architecture.md) — Architecture decisions and design
- [Source Tree Analysis](./source-tree-analysis.md) — Project structure
- Planning artifacts: `_bmad-output/planning-artifacts/`
