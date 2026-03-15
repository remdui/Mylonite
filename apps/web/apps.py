import logging
import os

from django.apps import AppConfig

from .content_loader import PortfolioContentLoader

logger = logging.getLogger(__name__)
_SYNC_HAS_RUN = False


def _sync_examples_on_startup_enabled() -> bool:
    """Return whether startup sync is enabled via environment configuration."""
    value = os.getenv("MYLONITE_SYNC_CONTENT_EXAMPLES_ON_STARTUP", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


class WebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.web"

    def ready(self) -> None:
        """Run one-time, best-effort local content example synchronization."""
        global _SYNC_HAS_RUN
        if _SYNC_HAS_RUN or not _sync_examples_on_startup_enabled():
            return

        _SYNC_HAS_RUN = True
        synced = PortfolioContentLoader().sync_example_content()
        if synced:
            logger.info("Synchronized schema-driven content examples at startup.")
