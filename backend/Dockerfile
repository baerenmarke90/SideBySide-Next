FROM python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir "uv==0.12.5"

# Zuerst nur die gesperrten Laufzeitabhaengigkeiten. So ist die teure Schicht
# unabhaengig vom Anwendungscode und uv darf den Lockstand nicht veraendern.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project --no-editable

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN uv sync --locked --no-editable

# Nicht als root laufen: ein Prozessausbruch soll nicht direkt den
# Container besitzen.
RUN useradd --system --uid 10001 sidebyside \
    && mkdir -p /var/lib/sidebyside/media \
    && chown -R sidebyside /var/lib/sidebyside
USER sidebyside

EXPOSE 8000

CMD ["uvicorn", "sidebyside.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir .

# Nicht als root laufen: ein Prozessausbruch soll nicht direkt den
# Container besitzen.
RUN useradd --system --uid 10001 sidebyside \
    && mkdir -p /var/lib/sidebyside/media \
    && chown -R sidebyside /var/lib/sidebyside
USER sidebyside

EXPOSE 8000

CMD ["uvicorn", "sidebyside.main:app", "--host", "0.0.0.0", "--port", "8000"]
