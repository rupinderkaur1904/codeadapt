# Image for the API and the worker (development compose stack; production hardening in M8).
FROM python:3.13-slim

# docker CLI for the worker only; the API never uses it (security.md §2).
COPY --from=docker:29-cli /usr/local/bin/docker /usr/local/bin/docker
RUN pip install --no-cache-dir uv==0.11.32

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH
WORKDIR /app/backend
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN uv sync --locked --no-dev

ENV CODEADAPT_CONTENT_DIR=/app/content/demo
EXPOSE 8000
CMD ["uvicorn", "codeadapt.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
