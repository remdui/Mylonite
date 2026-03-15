import tomllib
from pathlib import Path

from django.conf import settings

from mylonite.core.content_types import SourceInfo

CONTENT_ROOT = Path(settings.MYLONITE_CONTENT_ROOT)


def _resolve_content_root(content_root: Path | None) -> Path:
    return content_root or CONTENT_ROOT


def example_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.example")


def build_source_info(
    requested_path: Path,
    resolved_path: Path | None = None,
    *,
    content_root: Path | None = None,
    used_example: bool = False,
) -> SourceInfo:
    root = _resolve_content_root(content_root)
    return SourceInfo(
        requested_path=requested_path.relative_to(root).as_posix(),
        resolved_path=(
            resolved_path.relative_to(root).as_posix() if resolved_path else None
        ),
        used_example=used_example,
        missing=resolved_path is None,
    )


def resolve_content_file(
    path: Path,
    *,
    content_root: Path | None = None,
) -> tuple[Path | None, SourceInfo]:
    root = _resolve_content_root(content_root)
    if path.exists():
        return path, build_source_info(
            path,
            path,
            content_root=root,
            used_example=False,
        )

    fallback = example_path(path)
    if fallback.exists():
        return fallback, build_source_info(
            path,
            fallback,
            content_root=root,
            used_example=True,
        )

    return None, build_source_info(path, content_root=root)


def load_toml_file(
    path: Path,
    *,
    content_root: Path | None = None,
) -> tuple[dict, SourceInfo]:
    root = _resolve_content_root(content_root)
    resolved_path, source = resolve_content_file(path, content_root=root)
    if resolved_path is None:
        return {}, source

    with resolved_path.open("rb") as handle:
        return tomllib.load(handle), source


def load_text_file(
    path: Path,
    *,
    content_root: Path | None = None,
) -> tuple[str, SourceInfo]:
    root = _resolve_content_root(content_root)
    resolved_path, source = resolve_content_file(path, content_root=root)
    if resolved_path is None:
        return "", source

    return resolved_path.read_text(encoding="utf-8").strip(), source


class FileSystemContentRepository:
    """Repository for reading raw content records from filesystem."""

    def __init__(self, content_root: Path | None = None):
        self.content_root = _resolve_content_root(content_root)

    def load_site_record(self) -> tuple[dict, list[SourceInfo]]:
        data, source = load_toml_file(
            self.content_root / "config" / "site.toml",
            content_root=self.content_root,
        )
        return data, [source]

    def load_entity_record(
        self,
        object_id: str,
        *,
        text_filename: str | None = "website.md",
    ) -> tuple[dict, str, list[SourceInfo]]:
        root = self.content_root / "entities" / object_id

        entry, entry_source = load_toml_file(
            root / "entry.toml",
            content_root=self.content_root,
        )
        if text_filename is None:
            return entry, "", [entry_source]

        body, body_source = load_text_file(
            root / "text" / text_filename,
            content_root=self.content_root,
        )

        return entry, body, [entry_source, body_source]

    def list_entity_ids(self, *, prefix: str = "") -> list[str]:
        entities_root = self.content_root / "entities"
        if not entities_root.exists():
            return []

        ids: list[str] = []
        for child in entities_root.iterdir():
            if not child.is_dir():
                continue
            entity_id = child.name
            if prefix and not entity_id.startswith(prefix):
                continue
            ids.append(entity_id)

        return sorted(ids)
