#!/bin/sh
set -eu

mkdir -p \
  /app/runtime/config \
  /app/runtime/data/db \
  /app/runtime/data/static \
  /app/runtime/data/media

python - <<'PY'
from pathlib import Path

from mylonite.runtime import ensure_runtime_env_file

env_file = Path("/app/runtime/config/.env")
created, updated = ensure_runtime_env_file(env_file)

if created:
    print("Generated runtime/config/.env with a unique Django secret key.")
elif updated:
    print("Updated runtime/config/.env with a generated Django secret key.")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
