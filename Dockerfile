FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install a temporary build toolchain for packages without prebuilt wheels.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install server dependencies first (cached layer), without the local package.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --extra server --no-install-project

# Copy application code and bundled data
COPY src/ ./src/
COPY data/ ./data/

# Install the local package, then remove the build toolchain.
RUN uv sync --frozen --no-dev --extra server && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create data directory and set ownership for non-root user
RUN mkdir -p /app/data && \
    adduser --disabled-password --gecos "" --uid 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["/app/.venv/bin/uvicorn", "reformlab.server.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
