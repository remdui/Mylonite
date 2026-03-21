#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mylonite.settings")

    from pathlib import Path

    from mylonite.runtime import ensure_runtime_directories, resolve_runtime_paths

    base_dir = Path(__file__).resolve().parent
    runtime_paths = resolve_runtime_paths(base_dir)

    ensure_runtime_directories(
        [
            runtime_paths.config_root,
            runtime_paths.data_root,
            runtime_paths.db_path.parent,
            runtime_paths.static_root,
            runtime_paths.media_root,
        ]
    )

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
