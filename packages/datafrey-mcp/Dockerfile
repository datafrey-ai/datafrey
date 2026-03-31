FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS deps

WORKDIR /app

# Copy only dependency metadata first (cached unless deps change)
COPY pyproject.toml uv.lock ./
COPY packages/datafrey-api/pyproject.toml packages/datafrey-api/pyproject.toml
COPY packages/datafrey-mcp/pyproject.toml packages/datafrey-mcp/pyproject.toml

# Placeholder source so uv can resolve workspace members without real code
RUN mkdir -p packages/datafrey-api/src/datafrey_api \
    && touch packages/datafrey-api/src/datafrey_api/__init__.py \
    && mkdir -p packages/datafrey-mcp/src/datafrey_mcp \
    && touch packages/datafrey-mcp/src/datafrey_mcp/__init__.py

RUN uv sync --package datafrey-mcp --no-dev --frozen --no-editable

# ---
FROM deps AS source

# Copy real source (only this layer rebuilds on code changes)
COPY packages/datafrey-api/src packages/datafrey-api/src
COPY packages/datafrey-mcp/src packages/datafrey-mcp/src
RUN uv sync --package datafrey-mcp --no-dev --frozen --no-editable

# ---
FROM python:3.13-slim-bookworm

WORKDIR /app
COPY --from=source /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --system --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]

CMD ["datafrey-mcp"]
