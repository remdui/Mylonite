import os
import tomllib
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

RUNTIME_CONFIG_ROOT = Path(os.getenv("MYLONITE_CONFIG_ROOT", BASE_DIR / "runtime" / "config"))
RUNTIME_ENV_FILE = RUNTIME_CONFIG_ROOT / ".env"
DATA_ROOT = Path(os.getenv("MYLONITE_DATA_ROOT", BASE_DIR / "runtime" / "data"))
DB_PATH = Path(os.getenv("MYLONITE_DB_PATH", DATA_ROOT / "db" / "mylonite.sqlite3"))
STATIC_ROOT = DATA_ROOT / "static"
MEDIA_ROOT = DATA_ROOT / "media"

for path in [RUNTIME_CONFIG_ROOT, DATA_ROOT, DB_PATH.parent, STATIC_ROOT, MEDIA_ROOT]:
    path.mkdir(parents=True, exist_ok=True)


def load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_simple_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in raw_line:
            continue

        key, value = raw_line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        values[key] = value

    return values


def get_setting(name: str, default: str = "") -> str:
    if name in os.environ:
        return os.environ[name]
    return RUNTIME_ENV.get(name, default)


def get_csv_setting(name: str) -> list[str]:
    value = get_setting(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


RUNTIME_ENV = load_simple_env(RUNTIME_ENV_FILE)

DEBUG = get_setting("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes", "on"}

SECRET_KEY = get_setting("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-secret-key"
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG=false."
        )

SECRET_KEY_FALLBACKS = get_csv_setting("DJANGO_SECRET_KEY_FALLBACKS")

deploy_config = load_toml(RUNTIME_CONFIG_ROOT / "deploy.toml")

public_base_url = deploy_config.get("public_base_url", "").strip()
additional_allowed_hosts = deploy_config.get("additional_allowed_hosts", [])
additional_csrf_trusted_origins = deploy_config.get("additional_csrf_trusted_origins", [])

ALLOWED_HOSTS = []
CSRF_TRUSTED_ORIGINS = []

if public_base_url:
    parsed_base_url = urlparse(public_base_url)

    if not parsed_base_url.scheme or not parsed_base_url.netloc:
        raise RuntimeError("runtime/config/deploy.toml: public_base_url must be a full URL.")

    primary_host = parsed_base_url.hostname
    if not primary_host:
        raise RuntimeError("runtime/config/deploy.toml: public_base_url must contain a hostname.")

    ALLOWED_HOSTS.append(primary_host)
    CSRF_TRUSTED_ORIGINS.append(f"{parsed_base_url.scheme}://{parsed_base_url.netloc}")

ALLOWED_HOSTS.extend(additional_allowed_hosts)
CSRF_TRUSTED_ORIGINS.extend(additional_csrf_trusted_origins)

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mylonite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.web.context_processors.portfolio_context",
            ],
        },
    },
]

WSGI_APPLICATION = "mylonite.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DB_PATH),
    }
}

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = STATIC_ROOT
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = MEDIA_ROOT

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
