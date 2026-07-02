"""Filesystem utilities for reading and writing `content/config/site.toml`."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .content_schema import SITE_CONFIG_SCHEMA, schema_defaults
from .toml_utils import load_toml_file, render_toml


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in updates.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
            continue
        merged[key] = value
    return merged


def site_config_path(content_root: Path) -> Path:
    return content_root / "config" / "site.toml"


def load_site_config_payload(content_root: Path) -> dict[str, Any]:
    path = site_config_path(content_root)
    payload = load_toml_file(path)
    if not payload:
        payload = load_toml_file(path.with_name(f"{path.name}.example"))

    return _deep_merge(schema_defaults(SITE_CONFIG_SCHEMA), payload)


def write_site_config_payload(content_root: Path, payload: dict[str, Any]) -> None:
    path = site_config_path(content_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_toml(payload), encoding="utf-8")
