# Contributing to ReformLab

## Setup

```bash
git clone https://github.com/reformlab/ReformLab.git
cd ReformLab
uv sync --all-extras
cd frontend && npm install
```

## Standards

All checks must pass before submitting:

```bash
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest
```

```bash
cd frontend
npm run typecheck
npm run lint
npm test
```

## Submitting

1. Fork the repository
2. Create a feature branch (`git checkout -b my-feature`)
3. Make your changes
4. Ensure all checks pass (see above)
5. Open a pull request against `master`
