FROM python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689

ARG SBS_BUILD_REVISION=local-checkout

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    SBS_BUILD_REVISION="$SBS_BUILD_REVISION" \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir "uv==0.12.5"

# Install only the locked runtime dependencies first. This keeps the expensive
# layer independent of application code, and uv must not modify the lock state.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project --no-editable

COPY src ./src
COPY demo_assets ./demo_assets
# Ship only the operational demo entrypoint, not the development/CI scripts.
COPY scripts/__init__.py scripts/demo_space.py ./scripts/
COPY alembic ./alembic
COPY alembic.ini ./

RUN uv sync --locked --no-editable
# Keep the deployment-time demo bootstrap contract covered by every production
# image build without creating data or requiring demo credentials.
RUN python -m scripts.demo_space --help >/dev/null
RUN python -m scripts.demo_space validate-assets >/dev/null

# Do not run as root: a process escape must not immediately own the container.
RUN useradd --system --uid 10001 sidebyside \
    && mkdir -p /var/lib/sidebyside/media \
    && chown -R sidebyside /var/lib/sidebyside
USER sidebyside

EXPOSE 8000

CMD ["uvicorn", "sidebyside.main:app", "--host", "0.0.0.0", "--port", "8000"]
