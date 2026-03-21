"""Schema definitions and validation utilities for content records."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from .content_conventions import DEFAULT_HOMEPAGE_MAIN_ID, DEFAULT_OWNER_ID

_MISSING = object()


@dataclass(frozen=True)
class FieldRule:
    """Validation/parsing/default rule for a single field."""

    name: str
    required: bool = False
    parser: Callable[[Any], Any] | None = None
    default: Any = _MISSING


@dataclass(frozen=True)
class SchemaDefinition:
    """Schema name and ordered field rules for one content record type."""

    schema_name: str
    fields: tuple[FieldRule, ...]


def parse_boolean(value: Any) -> bool:
    """Parse bools from canonical boolean-like string values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ValueError("invalid boolean")


SITE_CONFIG_SCHEMA = SchemaDefinition(
    schema_name="site_config",
    fields=(
        FieldRule("site_title", required=True, parser=str, default="Mylonite"),
        FieldRule(
            "site_url", required=True, parser=str, default="http://localhost:8000"
        ),
        FieldRule("owner_id", required=True, parser=str, default=DEFAULT_OWNER_ID),
        FieldRule("footer_show_generated_by", parser=parse_boolean, default=True),
        FieldRule(
            "footer_repository_url",
            parser=str,
            default="https://github.com/remdui/mylonite",
        ),
        FieldRule("hosting_mode", required=False, parser=str, default="local"),
        FieldRule("public_domain", required=False, parser=str, default=""),
        FieldRule(
            "theme",
            required=False,
            parser=dict,
            default={"name": "default", "custom_theme_allowed": True},
        ),
        FieldRule(
            "install",
            required=False,
            parser=dict,
            default={"setup_wizard_enabled": True, "deferred_setup_allowed": True},
        ),
    ),
)

PERSON_PROFILE_SCHEMA = SchemaDefinition(
    schema_name="person_profile",
    fields=(
        FieldRule("schema_version", parser=int, default=1),
        FieldRule("kind", parser=str, default="identity"),
        FieldRule("type", parser=str, default="person_profile"),
        FieldRule("id", required=True, parser=str, default=DEFAULT_OWNER_ID),
        FieldRule("name", required=False, parser=str, default="Your Name"),
        FieldRule("full_name", required=True, parser=str, default="Your Full Name"),
        FieldRule("display_name", required=False, parser=str, default="Your Name"),
        FieldRule(
            "headline", required=False, parser=str, default="Professional headline"
        ),
        FieldRule(
            "summary",
            required=False,
            parser=str,
            default=(
                "Write a short summary that explains who you are, what you work on, "
                "and what kind of problems or projects interest you."
            ),
        ),
        FieldRule(
            "bio",
            required=False,
            parser=str,
            default=(
                "Write a short first-person bio for the homepage hero section."
            ),
        ),
        FieldRule("profile_image_path", required=False, parser=str, default=""),
    ),
)

HOMEPAGE_CONTENT_SCHEMA = SchemaDefinition(
    schema_name="homepage_content",
    fields=(
        FieldRule("schema_version", parser=int, default=1),
        FieldRule("kind", parser=str, default="content"),
        FieldRule("type", parser=str, default="homepage_main"),
        FieldRule("id", required=True, parser=str, default=DEFAULT_HOMEPAGE_MAIN_ID),
        FieldRule("title", parser=str, default="Homepage Main Content"),
        FieldRule(
            "markdown",
            parser=str,
            default=(
                "Write two or three short paragraphs here for the homepage.\n\n"
                "A good default structure is:\n\n"
                "- who you are\n"
                "- what you work on or are interested in\n"
                "- what kind of projects, roles, or collaborations you are looking for\n\n"
                "Keep it clear, professional, and easy to scan."
            ),
        ),
    ),
)


def schema_defaults(schema: SchemaDefinition) -> dict:
    """Return deep-copied defaults declared by a schema."""
    defaults: dict[str, Any] = {}
    for field in schema.fields:
        if field.default is _MISSING:
            continue
        defaults[field.name] = deepcopy(field.default)
    return defaults


def validate_record(schema: SchemaDefinition, payload: dict) -> tuple[dict, list[str]]:
    """Normalize a payload by schema parsers and collect validation errors."""
    errors: list[str] = []
    normalized: dict = {}

    for field in schema.fields:
        value = payload.get(field.name)
        if value in (None, ""):
            if field.default is not _MISSING:
                normalized[field.name] = deepcopy(field.default)
                continue
            if field.required:
                errors.append(f"{field.name}: required")
            continue

        if field.parser is None:
            normalized[field.name] = value
            continue

        try:
            normalized[field.name] = field.parser(value)
        except (TypeError, ValueError):
            errors.append(f"{field.name}: invalid type")

    return normalized, errors
