import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

from mylonite.runtime import ensure_runtime_directories, resolve_runtime_paths

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mylonite.settings")

BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_PATHS = resolve_runtime_paths(BASE_DIR)

ensure_runtime_directories(
    [
        RUNTIME_PATHS.config_root,
        RUNTIME_PATHS.data_root,
        RUNTIME_PATHS.db_path.parent,
        RUNTIME_PATHS.static_root,
        RUNTIME_PATHS.media_root,
    ]
)

application = get_wsgi_application()
