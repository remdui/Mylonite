"""Schema-driven content scaffold generation for local example files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .content_registry import ContentEntityRegistry, EntityDefinition
from mylonite.core.content_conventions import is_valid_entity_id
from mylonite.core.content_schema import SITE_CONFIG_SCHEMA, schema_defaults
from mylonite.core.toml_utils import render_toml


@dataclass(frozen=True)
class ScaffoldEntityDefinition:
    """Concrete scaffold target for one entity object id."""

    object_id: str
    entry: dict[str, Any]
    text_filename: str | None
    text_content: str | None


def _write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return

    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def _build_entity_scaffold(
    definition: EntityDefinition,
) -> list[ScaffoldEntityDefinition]:
    """Expand one entity definition into one or more scaffold targets."""
    schema = definition.schema
    if schema is None or not definition.example_object_ids:
        return []

    base_entry = schema_defaults(schema)
    if definition.example_entry_overrides:
        base_entry = {**base_entry, **definition.example_entry_overrides}

    entry_defaults, text_content = definition.body_source.split_scaffold(base_entry)

    scaffolds: list[ScaffoldEntityDefinition] = []
    for object_id in definition.example_object_ids:
        if not is_valid_entity_id(object_id):
            raise ValueError(f"invalid entity object_id: {object_id!r}")
        scaffolds.append(
            ScaffoldEntityDefinition(
                object_id=object_id,
                entry={**entry_defaults, "id": object_id},
                text_filename=definition.body_source.text_filename,
                text_content=text_content,
            )
        )

    return scaffolds


def _prune_stale_text_examples(
    entity_root: Path, expected_text_filename: str | None
) -> None:
    """Remove stale generated text examples when body strategy or filename changes."""
    text_root = entity_root / "text"
    if not text_root.exists():
        return

    expected_name = (
        f"{expected_text_filename}.example"
        if expected_text_filename is not None
        else None
    )

    for example_file in text_root.glob("*.example"):
        if expected_name is not None and example_file.name == expected_name:
            continue
        example_file.unlink()


def sync_content_examples(content_root: Path, registry: ContentEntityRegistry) -> None:
    """Generate or update local `*.example` files from schema defaults."""
    site_example = content_root / "config" / "site.toml.example"
    _write_if_changed(site_example, render_toml(schema_defaults(SITE_CONFIG_SCHEMA)))

    for definition in registry.definitions():
        for scaffold in _build_entity_scaffold(definition):
            entity_root = content_root / "entities" / scaffold.object_id
            _write_if_changed(
                entity_root / "entry.toml.example", render_toml(scaffold.entry)
            )

            _prune_stale_text_examples(entity_root, scaffold.text_filename)
            if scaffold.text_filename and scaffold.text_content is not None:
                _write_if_changed(
                    entity_root / "text" / f"{scaffold.text_filename}.example",
                    scaffold.text_content.strip() + "\n",
                )


__all__ = [
    "ScaffoldEntityDefinition",
    "sync_content_examples",
    "_build_entity_scaffold",
]
