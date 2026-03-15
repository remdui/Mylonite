"""Minimal TOML rendering helpers for deterministic local file output."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class _TomlSection:
    key_path: tuple[str, ...]
    values: dict[str, Any]


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


def _walk_toml_sections(
    payload: dict[str, Any],
    *,
    key_path: tuple[str, ...] = (),
) -> tuple[list[tuple[str, Any]], list[_TomlSection]]:
    """Split payload into scalar fields and nested table sections recursively."""
    scalars: list[tuple[str, Any]] = []
    sections: list[_TomlSection] = []

    for key, value in payload.items():
        if isinstance(value, dict):
            section_scalars, nested_sections = _walk_toml_sections(
                value,
                key_path=(*key_path, key),
            )
            sections.append(
                _TomlSection(
                    key_path=(*key_path, key),
                    values={name: item for name, item in section_scalars},
                )
            )
            sections.extend(nested_sections)
            continue

        scalars.append((key, value))

    return scalars, sections


def render_toml(data: dict[str, Any]) -> str:
    """Render deterministic TOML with nested table support."""
    scalar_fields, sections = _walk_toml_sections(data)

    lines: list[str] = [
        f"{key} = {_format_toml_value(value)}" for key, value in scalar_fields
    ]

    for section in sections:
        if lines:
            lines.append("")
        lines.append("[" + ".".join(section.key_path) + "]")
        lines.extend(
            f"{key} = {_format_toml_value(value)}"
            for key, value in section.values.items()
        )

    return "\n".join(lines).rstrip() + "\n"
