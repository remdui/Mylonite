from dataclasses import dataclass
from pathlib import Path

from .content_types import ThemeSettings


@dataclass(frozen=True)
class ThemePaths:
    template_dir: Path
    static_dir: Path


class ThemeResolver:
    """Resolves active theme directories; supports user-created themes."""

    def __init__(self, themes_root: Path):
        self.themes_root = themes_root

    def resolve(self, settings: ThemeSettings) -> ThemePaths:
        requested = self.themes_root / settings.name
        default = self.themes_root / "default"

        active = requested if requested.exists() else default

        return ThemePaths(
            template_dir=active / "templates",
            static_dir=active / "static",
        )
