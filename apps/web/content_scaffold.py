"""Schema-driven content scaffold generation for local example files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .content_registry import ContentEntityRegistry, EntityDefinition
from mylonite.core.content_schema import SITE_CONFIG_SCHEMA, schema_defaults


@dataclass(frozen=True)
class ScaffoldEntityDefinition:
    """Concrete scaffold target for one entity object id."""

    object_id: str
    entry: dict[str, Any]
    text_filename: str | None
    text_content: str | None


def _format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        rendered = ", ".join(_format_toml_value(item) for item in value)
        return f"[{rendered}]"
    raise TypeError(f"Unsupported TOML value type: {type(value)!r}")


def _render_toml(data: dict[str, Any]) -> str:
    """Render a small subset of TOML needed by current schema defaults."""
    scalar_lines: list[str] = []
    nested_lines: list[str] = []

    for key, value in data.items():
        if isinstance(value, dict):
            nested_lines.append(f"[{key}]")
            for nested_key, nested_value in value.items():
                nested_lines.append(
                    f"{nested_key} = {_format_toml_value(nested_value)}"
                )
            nested_lines.append("")
            continue

        scalar_lines.append(f"{key} = {_format_toml_value(value)}")

    lines = scalar_lines
    if nested_lines:
        lines += [""] + nested_lines

    return "\n".join(lines).rstrip() + "\n"


def _write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return
    path.write_text(content, encoding="utf-8")


def _build_entity_scaffold(definition: EntityDefinition) -> list[ScaffoldEntityDefinition]:
    """Expand one entity definition into one or more scaffold targets."""
    schema = definition.schema
    if schema is None or not definition.example_object_ids:
        return []

    base_entry = schema_defaults(schema)
    if definition.example_entry_overrides:
        base_entry = {**base_entry, **definition.example_entry_overrides}

    entry_defaults, text_content = definition.body_source.split_scaffold(base_entry)

    return [
        ScaffoldEntityDefinition(
            object_id=object_id,
            entry={**entry_defaults, "id": object_id},
            text_filename=definition.body_source.text_filename,
            text_content=text_content,
        )
        for object_id in definition.example_object_ids
    ]


def sync_content_examples(content_root: Path, registry: ContentEntityRegistry) -> None:
    """Generate or update local `*.example` files from schema defaults."""
    site_example = content_root / "config" / "site.toml.example"
    _write_if_changed(site_example, _render_toml(schema_defaults(SITE_CONFIG_SCHEMA)))

    for definition in registry.definitions():
        for scaffold in _build_entity_scaffold(definition):
            entity_root = content_root / "entities" / scaffold.object_id
            _write_if_changed(entity_root / "entry.toml.example", _render_toml(scaffold.entry))

            if scaffold.text_filename and scaffold.text_content is not None:
                _write_if_changed(
                    entity_root / "text" / f"{scaffold.text_filename}.example",
                    scaffold.text_content.strip() + "\n",
                )
