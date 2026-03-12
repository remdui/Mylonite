import os
import tomllib
from ipaddress import ip_network
from pathlib import Path
from urllib.parse import urlparse

from mylonite.runtime import load_simple_env

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_ROOT = Path(os.getenv("MYLONITE_CONFIG_ROOT", BASE_DIR / "runtime" / "config"))
RUNTIME_ENV_FILE = CONFIG_ROOT / ".env"
DATA_ROOT = Path(os.getenv("MYLONITE_DATA_ROOT", BASE_DIR / "runtime" / "data"))
CONTENT_ROOT = Path(os.getenv("MYLONITE_CONTENT_ROOT", BASE_DIR / "content"))
DB_PATH = Path(os.getenv("MYLONITE_DB_PATH", DATA_ROOT / "db" / "mylonite.sqlite3"))
STATIC_ROOT_PATH = DATA_ROOT / "static"
MEDIA_ROOT_PATH = DATA_ROOT / "media"
DEPLOY_CONFIG_PATH = CONFIG_ROOT / "deploy.toml"

for path in [CONFIG_ROOT, DATA_ROOT, DB_PATH.parent, STATIC_ROOT_PATH, MEDIA_ROOT_PATH]:
    path.mkdir(parents=True, exist_ok=True)


def load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def get_setting(name: str, default: str = "") -> str:
    if name in os.environ:
        return os.environ[name]
    return RUNTIME_ENV.get(name, default)


def get_csv_setting(name: str) -> list[str]:
    value = get_setting(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def load_proxy_networks(values: list[str]) -> tuple:
    networks = []

    for value in values:
        candidate = value.strip()
        if not candidate:
            continue

        try:
            networks.append(ip_network(candidate, strict=False))
        except ValueError as exc:
            raise RuntimeError(
                f"{DEPLOY_CONFIG_PATH.as_posix()}: trusted_proxy_cidrs must contain valid CIDR values."
            ) from exc

    return tuple(networks)


RUNTIME_ENV = load_simple_env(RUNTIME_ENV_FILE)

DEBUG = get_setting("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes", "on"}

SECRET_KEY = get_setting("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-secret-key"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG=false.")

SECRET_KEY_FALLBACKS = get_csv_setting("DJANGO_SECRET_KEY_FALLBACKS")

deploy_config = load_toml(DEPLOY_CONFIG_PATH)

public_base_url = deploy_config.get("public_base_url", "").strip()
additional_allowed_hosts = deploy_config.get("additional_allowed_hosts", [])
additional_csrf_trusted_origins = deploy_config.get("additional_csrf_trusted_origins", [])
trusted_proxy_cidrs = deploy_config.get("trusted_proxy_cidrs", [])

parsed_public_base_url = None
ALLOWED_HOSTS = []
CSRF_TRUSTED_ORIGINS = []

if public_base_url:
    parsed_public_base_url = urlparse(public_base_url)

    if not parsed_public_base_url.scheme or not parsed_public_base_url.netloc:
        raise RuntimeError(
            f"{DEPLOY_CONFIG_PATH.as_posix()}: public_base_url must be a full URL."
        )

    primary_host = parsed_public_base_url.hostname
    if not primary_host:
        raise RuntimeError(
            f"{DEPLOY_CONFIG_PATH.as_posix()}: public_base_url must contain a hostname."
        )

    ALLOWED_HOSTS.append(primary_host)
    CSRF_TRUSTED_ORIGINS.append(
        f"{parsed_public_base_url.scheme}://{parsed_public_base_url.netloc}"
    )

ALLOWED_HOSTS.extend(additional_allowed_hosts)
CSRF_TRUSTED_ORIGINS.extend(additional_csrf_trusted_origins)

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]

is_https_deployment = bool(
    parsed_public_base_url and parsed_public_base_url.scheme.lower() == "https"
)

MYLONITE_TRUSTED_PROXY_CIDRS = load_proxy_networks(trusted_proxy_cidrs)

PANEL_LOGIN_FAILURE_LIMIT = max(
    1,
    int(deploy_config.get("panel_login_failure_limit", 5)),
)
PANEL_LOGIN_FAILURE_WINDOW_SECONDS = max(
    60,
    int(deploy_config.get("panel_login_failure_window_seconds", 900)),
)
PANEL_LOGIN_LOCKOUT_SECONDS = max(
    60,
    int(deploy_config.get("panel_login_lockout_seconds", 900)),
)

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.panel",
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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = STATIC_ROOT_PATH
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = MEDIA_ROOT_PATH

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/dashboard/"
LOGOUT_REDIRECT_URL = "/"

SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if MYLONITE_TRUSTED_PROXY_CIDRS
    else None
)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_SECURE = bool(
    deploy_config.get("secure_cookies", is_https_deployment)
)
CSRF_COOKIE_SECURE = bool(
    deploy_config.get("secure_cookies", is_https_deployment)
)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = bool(
    deploy_config.get("secure_ssl_redirect", is_https_deployment)
)
SECURE_HSTS_SECONDS = max(
    0,
    int(deploy_config.get("secure_hsts_seconds", 0)),
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(
    deploy_config.get("secure_hsts_include_subdomains", False)
)
SECURE_HSTS_PRELOAD = bool(
    deploy_config.get("secure_hsts_preload", False)
)

MYLONITE_CONFIG_ROOT = CONFIG_ROOT
MYLONITE_CONTENT_ROOT = CONTENT_ROOT
MYLONITE_DATA_ROOT = DATA_ROOT
