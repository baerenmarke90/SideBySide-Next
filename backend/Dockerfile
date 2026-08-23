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
