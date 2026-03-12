#!/bin/sh
set -eu

CONFIG_ROOT="${MYLONITE_CONFIG_ROOT:-/config}"
DATA_ROOT="${MYLONITE_DATA_ROOT:-/data}"
CONTENT_ROOT="${MYLONITE_CONTENT_ROOT:-/content}"

pick_runtime_owner() {
  for candidate in "$CONFIG_ROOT" "$CONTENT_ROOT" "$DATA_ROOT"; do
    if [ -e "$candidate" ]; then
      candidate_uid="$(stat -c '%u' "$candidate")"
      candidate_gid="$(stat -c '%g' "$candidate")"

      if [ "$candidate_uid" != "0" ] || [ "$candidate_gid" != "0" ]; then
        echo "${candidate_uid}:${candidate_gid}"
        return 0
      fi
    fi
  done

  echo "0:0"
}

ensure_owner() {
  path="$1"
  owner="$2"

  if [ ! -e "$path" ]; then
    return 0
  fi

  current_owner="$(stat -c '%u:%g' "$path")"
  if [ "$current_owner" != "$owner" ]; then
    chown -R "$owner" "$path"
  fi
}

run_as_runtime_user() {
  if [ "$RUN_AS_OWNER" = "0:0" ]; then
    "$@"
  else
    gosu "$RUN_AS_OWNER" "$@"
  fi
}

umask 0022

mkdir -p \
  "$CONFIG_ROOT" \
  "$DATA_ROOT/db" \
  "$DATA_ROOT/static" \
  "$DATA_ROOT/media"

RUN_AS_OWNER="$(pick_runtime_owner)"

if [ "$RUN_AS_OWNER" != "0:0" ]; then
  ensure_owner "$CONFIG_ROOT" "$RUN_AS_OWNER"
  ensure_owner "$DATA_ROOT" "$RUN_AS_OWNER"
fi

export MYLONITE_CONFIG_ROOT="$CONFIG_ROOT"
export MYLONITE_DATA_ROOT="$DATA_ROOT"
export MYLONITE_CONTENT_ROOT="$CONTENT_ROOT"

run_as_runtime_user python - <<'PY'
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

run_as_runtime_user python manage.py migrate --noinput
run_as_runtime_user python manage.py collectstatic --noinput

if [ "$RUN_AS_OWNER" = "0:0" ]; then
  exec "$@"
else
  exec gosu "$RUN_AS_OWNER" "$@"
fi
