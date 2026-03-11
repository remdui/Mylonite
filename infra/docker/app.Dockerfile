FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY manage.py /app/
COPY mylonite /app/mylonite
COPY apps /app/apps
COPY templates /app/templates
COPY static /app/static
COPY infra/docker/entrypoint.sh /entrypoint.sh

RUN pip install --upgrade pip && pip install .

RUN useradd --uid 1000 --create-home --shell /bin/bash appuser \
    && mkdir -p /app/runtime/data \
    && chown -R appuser:appuser /app /entrypoint.sh \
    && chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "mylonite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
