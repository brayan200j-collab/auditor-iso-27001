# syntax=docker/dockerfile:1.7
# Build context: repository root (the API needs /prompts and /seeds).

FROM python:3.12-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# System libraries required by WeasyPrint (Pango/HarfBuzz) plus fonts for the PDF report.
RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "20";\n' > /etc/apt/apt.conf.d/80-retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 \
        fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

FROM base AS uv
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Development/test image: the repository is bind-mounted at /workspace.
FROM uv AS dev
WORKDIR /workspace/apps/api
COPY apps/api/docker/dev-entrypoint.sh /usr/local/bin/dev-entrypoint.sh
RUN chmod +x /usr/local/bin/dev-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/dev-entrypoint.sh"]

FROM uv AS builder
WORKDIR /build
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project
COPY apps/api/src ./src
COPY apps/api/README.md ./README.md
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime
# A home directory gives Fontconfig (WeasyPrint) a writable cache for the non-root user.
RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /home/app app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
COPY prompts /app/prompts
COPY seeds /app/seeds
ENV PATH="/opt/venv/bin:$PATH" \
    PROMPTS_DIR=/app/prompts \
    SEEDS_DIR=/app/seeds \
    APP_ENV=production
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).status == 200 else 1)"
CMD ["uvicorn", "--factory", "auditor.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
