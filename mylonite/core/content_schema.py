from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class FieldRule:
    name: str
    required: bool = False
    parser: Callable[[Any], Any] | None = None


@dataclass(frozen=True)
class SchemaDefinition:
    schema_name: str
    fields: tuple[FieldRule, ...]


SITE_CONFIG_SCHEMA = SchemaDefinition(
    schema_name="site_config",
    fields=(
        FieldRule("site_title", required=True, parser=str),
        FieldRule("site_url", required=True, parser=str),
        FieldRule("owner_id", required=True, parser=str),
        FieldRule("hosting_mode", required=False, parser=str),
        FieldRule("public_domain", required=False, parser=str),
        FieldRule("theme", required=False, parser=dict),
        FieldRule("install", required=False, parser=dict),
    ),
)

PERSON_PROFILE_SCHEMA = SchemaDefinition(
    schema_name="person_profile",
    fields=(
        FieldRule("id", required=True, parser=str),
        FieldRule("full_name", required=True, parser=str),
        FieldRule("display_name", required=False, parser=str),
        FieldRule("headline", required=False, parser=str),
        FieldRule("summary", required=False, parser=str),
        FieldRule("profile_image_path", required=False, parser=str),
    ),
)


def validate_record(schema: SchemaDefinition, payload: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    normalized: dict = {}

    for field in schema.fields:
        value = payload.get(field.name)
        if value in (None, ""):
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
