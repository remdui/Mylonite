FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/tmp

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
COPY infra/docker/entrypoint.sh /usr/local/bin/mylonite-entrypoint

RUN find /app -type d -exec chmod 0755 {} \; \
    && find /app -type f -exec chmod 0644 {} \; \
    && chmod 0755 /usr/local/bin/mylonite-entrypoint \
    && python -m pip install --upgrade pip \
    && python -m pip install . \
    && mkdir -p /config /data /content \
    && chmod 0755 /config /data /content

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/mylonite-entrypoint"]
CMD ["gunicorn", "mylonite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--capture-output", "--error-logfile", "-", "--access-logfile", "-"]
