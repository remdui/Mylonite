#!/usr/bin/env sh
set -eu

CONTENT_DIR="${MYLONITE_CONTENT_DIR:-./content}"

if [ ! -d "$CONTENT_DIR" ]; then
  echo "Content directory '$CONTENT_DIR' does not exist." >&2
  exit 1
fi

find "$CONTENT_DIR" -type f -name '*.example' | sort | while IFS= read -r example_path; do
  target_path="${example_path%.example}"
  target_dir="$(dirname "$target_path")"

  mkdir -p "$target_dir"

  if [ ! -e "$target_path" ]; then
    cp "$example_path" "$target_path"
    echo "Created $target_path"
  fi
done

echo "Content initialization complete."
