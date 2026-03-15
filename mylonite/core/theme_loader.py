from __future__ import annotations

import logging
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import ClassVar

from .content_types import ThemeSettings
from .site_config_store import load_site_config_payload

logger = logging.getLogger(__name__)

THEME_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
THEME_METADATA_FILENAME = "theme.toml"
DEFAULT_THEME_ID = "default"
REQUIRED_THEME_METADATA_FIELDS = ("name", "description", "version")


@dataclass(frozen=True)
class ThemeMetadata:
    name: str
    description: str
    version: str


@dataclass(frozen=True)
class ThemeDefinition:
    theme_id: str
    root_dir: Path
    static_dir: Path
    metadata: ThemeMetadata
    is_default: bool = False


@dataclass(frozen=True)
class ThemeAsset:
    requested_path: str
    resolved_path: Path
    from_fallback: bool


@dataclass(frozen=True)
class ResolvedTheme:
    requested_theme_id: str
    active_theme: ThemeDefinition
    default_theme: ThemeDefinition
    missing_required_static_files: tuple[str, ...]
    custom_theme_allowed: bool


def _parse_boolean(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return default


def normalize_theme_asset_path(asset_path: str) -> str | None:
    candidate = asset_path.strip().lstrip("/")
    if not candidate:
        return None

    normalized = PurePosixPath(candidate)
    if normalized.is_absolute() or ".." in normalized.parts:
        return None

    path = PurePosixPath(*(part for part in normalized.parts if part not in {"", "."}))
    return path.as_posix() if path.parts else None


def load_active_theme_settings(*, content_root: Path) -> ThemeSettings:
    payload = load_site_config_payload(content_root)
    raw_theme = payload.get("theme", {})
    theme_data = raw_theme if isinstance(raw_theme, dict) else {}

    raw_name = theme_data.get("name", DEFAULT_THEME_ID)
    name = (
        raw_name.strip()
        if isinstance(raw_name, str) and raw_name.strip()
        else DEFAULT_THEME_ID
    )

    custom_theme_allowed = _parse_boolean(
        theme_data.get("custom_theme_allowed", True),
        default=True,
    )

    return ThemeSettings(
        name=name,
        custom_theme_allowed=custom_theme_allowed,
    )


class ThemeResolver:
    """Discovers themes and resolves static assets with default-theme fallback."""

    _discovery_cache: ClassVar[
        dict[str, tuple[tuple[tuple[str, int, int], ...], tuple[ThemeDefinition, ...]]]
    ] = {}
    _warned_selection_fallbacks: ClassVar[set[str]] = set()
    _warned_missing_assets: ClassVar[set[str]] = set()
    _warned_invalid_theme_definitions: ClassVar[set[str]] = set()

    def __init__(self, themes_root: Path):
        self.themes_root = themes_root

    def discover_themes(self) -> list[ThemeDefinition]:
        if not self.themes_root.exists():
            return []

        signature = self._build_discovery_signature()
        cache_key = str(self.themes_root.resolve())
        cached_entry = self._discovery_cache.get(cache_key)
        if cached_entry is not None and cached_entry[0] == signature:
            return list(cached_entry[1])

        themes: list[ThemeDefinition] = []
        for child in sorted(self.themes_root.iterdir(), key=lambda path: path.name):
            if not child.is_dir():
                continue

            theme = self._parse_theme(child)
            if theme is not None:
                themes.append(theme)

        self._discovery_cache[cache_key] = (signature, tuple(themes))
        return themes

    def selectable_themes(
        self,
        *,
        custom_theme_allowed: bool,
        themes: list[ThemeDefinition] | None = None,
    ) -> list[ThemeDefinition]:
        available_themes = themes or self.discover_themes()
        if custom_theme_allowed:
            return available_themes
        return [
            theme for theme in available_themes if theme.theme_id == DEFAULT_THEME_ID
        ]

    def resolve(
        self,
        settings: ThemeSettings,
        *,
        themes: list[ThemeDefinition] | None = None,
    ) -> ResolvedTheme:
        available_themes = themes or self.discover_themes()
        theme_map = {theme.theme_id: theme for theme in available_themes}
        default_theme = theme_map.get(DEFAULT_THEME_ID)
        if default_theme is None:
            raise RuntimeError(
                f"Missing required default theme at {self.themes_root / DEFAULT_THEME_ID}."
            )

        requested_theme_id = (
            settings.name.strip()
            if isinstance(settings.name, str) and settings.name.strip()
            else DEFAULT_THEME_ID
        )
        requested_theme = theme_map.get(requested_theme_id)

        should_force_default = (
            requested_theme_id != DEFAULT_THEME_ID and not settings.custom_theme_allowed
        )
        if requested_theme is None or should_force_default:
            fallback_reason = (
                "custom themes are disabled"
                if should_force_default
                else "theme folder is invalid or missing"
            )
            warning_key = f"{requested_theme_id}:{fallback_reason}"
            if requested_theme_id != DEFAULT_THEME_ID:
                self._warn_selection_fallback_once(
                    warning_key,
                    requested_theme_id=requested_theme_id,
                    fallback_reason=fallback_reason,
                )
            requested_theme = default_theme

        missing_files = ()
        if requested_theme.theme_id != default_theme.theme_id:
            missing_files = self._missing_required_static_files(
                active_theme=requested_theme,
                default_theme=default_theme,
            )
            self._warn_missing_assets_once(requested_theme.theme_id, missing_files)

        return ResolvedTheme(
            requested_theme_id=requested_theme_id,
            active_theme=requested_theme,
            default_theme=default_theme,
            missing_required_static_files=missing_files,
            custom_theme_allowed=settings.custom_theme_allowed,
        )

    def resolve_static_asset(
        self,
        resolved_theme: ResolvedTheme,
        *,
        asset_path: str,
    ) -> ThemeAsset | None:
        normalized_path = normalize_theme_asset_path(asset_path)
        if not normalized_path:
            return None

        active_file = resolved_theme.active_theme.static_dir / normalized_path
        if active_file.is_file():
            return ThemeAsset(
                requested_path=normalized_path,
                resolved_path=active_file,
                from_fallback=False,
            )

        fallback_file = resolved_theme.default_theme.static_dir / normalized_path
        if fallback_file.is_file():
            return ThemeAsset(
                requested_path=normalized_path,
                resolved_path=fallback_file,
                from_fallback=True,
            )

        return None

    def _parse_theme(self, theme_dir: Path) -> ThemeDefinition | None:
        theme_id = theme_dir.name
        if not THEME_ID_PATTERN.fullmatch(theme_id):
            self._warn_invalid_theme_once(
                theme_id,
                "invalid-folder-name",
                "Ignoring theme folder '%s': folder name must match %s.",
                theme_id,
                THEME_ID_PATTERN.pattern,
            )
            return None

        static_dir = theme_dir / "static"
        if not static_dir.is_dir():
            self._warn_invalid_theme_once(
                theme_id,
                "missing-static-directory",
                "Ignoring theme '%s': missing required 'static/' directory.",
                theme_id,
            )
            return None

        metadata_path = theme_dir / THEME_METADATA_FILENAME
        if not metadata_path.is_file():
            self._warn_invalid_theme_once(
                theme_id,
                "missing-theme-metadata",
                "Ignoring theme '%s': missing required '%s'.",
                theme_id,
                THEME_METADATA_FILENAME,
            )
            return None

        try:
            with metadata_path.open("rb") as handle:
                raw_metadata = tomllib.load(handle)
        except (tomllib.TOMLDecodeError, OSError):
            self._warn_invalid_theme_once(
                theme_id,
                "invalid-theme-metadata",
                "Ignoring theme '%s': invalid %s file.",
                theme_id,
                THEME_METADATA_FILENAME,
            )
            return None

        values: dict[str, str] = {}
        for field in REQUIRED_THEME_METADATA_FIELDS:
            value = raw_metadata.get(field)
            if not isinstance(value, str) or not value.strip():
                self._warn_invalid_theme_once(
                    theme_id,
                    f"invalid-theme-metadata-field-{field}",
                    "Ignoring theme '%s': %s must define a non-empty string '%s'.",
                    theme_id,
                    THEME_METADATA_FILENAME,
                    field,
                )
                return None
            values[field] = value.strip()

        metadata = ThemeMetadata(
            name=values["name"],
            description=values["description"],
            version=values["version"],
        )

        return ThemeDefinition(
            theme_id=theme_id,
            root_dir=theme_dir,
            static_dir=static_dir,
            metadata=metadata,
            is_default=(theme_id == DEFAULT_THEME_ID),
        )

    def _missing_required_static_files(
        self,
        *,
        active_theme: ThemeDefinition,
        default_theme: ThemeDefinition,
    ) -> tuple[str, ...]:
        required_files = self._list_static_files(default_theme.static_dir)
        active_files = self._list_static_files(active_theme.static_dir)
        missing = sorted(required_files - active_files)
        return tuple(missing)

    def _list_static_files(self, static_dir: Path) -> set[str]:
        if not static_dir.exists():
            return set()

        return {
            path.relative_to(static_dir).as_posix()
            for path in static_dir.rglob("*")
            if path.is_file()
        }

    def _warn_selection_fallback_once(
        self,
        warning_key: str,
        *,
        requested_theme_id: str,
        fallback_reason: str,
    ) -> None:
        if warning_key in self._warned_selection_fallbacks:
            return

        self._warned_selection_fallbacks.add(warning_key)
        logger.warning(
            "Requested theme '%s' cannot be activated (%s). Falling back to '%s'.",
            requested_theme_id,
            fallback_reason,
            DEFAULT_THEME_ID,
        )

    def _warn_missing_assets_once(
        self, theme_id: str, missing_files: tuple[str, ...]
    ) -> None:
        if not missing_files:
            return

        warning_key = f"{theme_id}:{','.join(missing_files)}"
        if warning_key in self._warned_missing_assets:
            return

        self._warned_missing_assets.add(warning_key)
        logger.warning(
            "Theme '%s' is missing %d required static assets. "
            "Missing files: %s. "
            "The default theme will be used as fallback for those assets.",
            theme_id,
            len(missing_files),
            ", ".join(missing_files),
        )

    def _build_discovery_signature(self) -> tuple[tuple[str, int, int], ...]:
        entries: list[tuple[str, int, int]] = []
        for child in sorted(self.themes_root.iterdir(), key=lambda path: path.name):
            if not child.is_dir():
                continue

            metadata_path = child / THEME_METADATA_FILENAME
            static_dir = child / "static"
            metadata_mtime_ns = (
                int(metadata_path.stat().st_mtime_ns) if metadata_path.exists() else -1
            )
            static_mtime_ns = (
                int(static_dir.stat().st_mtime_ns) if static_dir.exists() else -1
            )
            entries.append((child.name, metadata_mtime_ns, static_mtime_ns))

        return tuple(entries)

    def _warn_invalid_theme_once(
        self,
        theme_id: str,
        reason_key: str,
        message: str,
        *args: object,
    ) -> None:
        warning_key = f"{self.themes_root}:{theme_id}:{reason_key}"
        if warning_key in self._warned_invalid_theme_definitions:
            return

        self._warned_invalid_theme_definitions.add(warning_key)
        logger.warning(message, *args)
