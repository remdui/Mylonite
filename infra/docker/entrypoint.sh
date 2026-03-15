#!/bin/sh
set -eu

CONFIG_ROOT="${MYLONITE_CONFIG_ROOT:-/config}"
DATA_ROOT="${MYLONITE_DATA_ROOT:-/data}"
CONTENT_ROOT="${MYLONITE_CONTENT_ROOT:-/content}"
DB_PATH="${MYLONITE_DB_PATH:-$DATA_ROOT/db/mylonite.sqlite3}"

ensure_dir() {
  install -d -m 0755 "$1"
}

probe_writable_dir() {
  dir="$1"
  probe="$dir/.mylonite-write-test.$$"

  if ! : > "$probe" 2>/dev/null; then
    echo >&2 "ERROR: directory '$dir' is not writable."
    echo >&2 "Check that the bind-mounted host path exists and is mounted read-write."
    exit 1
  fi

  rm -f "$probe"
}

umask 0022

ensure_dir "$CONFIG_ROOT"
ensure_dir "$DATA_ROOT"
ensure_dir "$(dirname "$DB_PATH")"
ensure_dir "$DATA_ROOT/static"
ensure_dir "$DATA_ROOT/media"

probe_writable_dir "$CONFIG_ROOT"
probe_writable_dir "$DATA_ROOT"
probe_writable_dir "$(dirname "$DB_PATH")"

touch "$DB_PATH"
chmod 0644 "$DB_PATH" || true

export MYLONITE_CONFIG_ROOT="$CONFIG_ROOT"
export MYLONITE_DATA_ROOT="$DATA_ROOT"
export MYLONITE_CONTENT_ROOT="$CONTENT_ROOT"
export MYLONITE_DB_PATH="$DB_PATH"

python - <<'PY'
import os
from pathlib import Path

from mylonite.runtime import ensure_runtime_env_file

config_root = Path(os.environ["MYLONITE_CONFIG_ROOT"])
env_file = config_root / ".env"

created, updated = ensure_runtime_env_file(env_file)

if created:
    print(f"Generated {env_file} with a unique Django secret key.")
elif updated:
    print(f"Updated {env_file} with a generated Django secret key.")
PY

python - <<'PY'
import os
from pathlib import Path

from apps.web.content_registry import ContentEntityRegistry
from apps.web.content_scaffold import sync_content_examples

content_root = Path(os.environ["MYLONITE_CONTENT_ROOT"])

try:
    sync_content_examples(content_root, ContentEntityRegistry())
except OSError as exc:
    print(
        f"WARNING: unable to generate content examples in {content_root}: {exc}",
        flush=True,
    )
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
