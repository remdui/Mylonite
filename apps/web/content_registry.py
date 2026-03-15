"""Registry for all content entity types handled by the web app.

Each entity definition binds together:
- schema (validation/defaults),
- body storage strategy,
- mapper into a domain object,
- example object IDs for scaffolding.
"""

from dataclasses import dataclass
from typing import Callable, TypeVar

from .content_entities import BodySourceSpec, FieldBodySourceSpec, NoBodySourceSpec
from .content_mappers import map_homepage_content, map_person_profile
from mylonite.core.content_conventions import (
    DEFAULT_HOMEPAGE_MAIN_ID,
    DEFAULT_OWNER_ID,
    ENTITY_TYPE_HOMEPAGE_MAIN,
    ENTITY_TYPE_PERSON,
    HOMEPAGE_MAIN_TEXT_FILENAME,
)
from mylonite.core.content_schema import (
    HOMEPAGE_CONTENT_SCHEMA,
    PERSON_PROFILE_SCHEMA,
    SchemaDefinition,
)

EntityModel = TypeVar("EntityModel")


@dataclass(frozen=True)
class EntityDefinition:
    """Definition for loading/validating/scaffolding one entity type."""

    entity_type: str
    mapper: Callable[[str, dict, str], EntityModel]
    body_source: BodySourceSpec
    schema: SchemaDefinition | None = None
    example_object_ids: tuple[str, ...] = ()
    example_entry_overrides: dict | None = None


class ContentEntityRegistry:
    """Lookup table for entity definitions with sane defaults."""

    def __init__(self, definitions: dict[str, EntityDefinition] | None = None):
        self._definitions = definitions or {
            ENTITY_TYPE_PERSON: EntityDefinition(
                entity_type=ENTITY_TYPE_PERSON,
                mapper=map_person_profile,
                body_source=NoBodySourceSpec(),
                schema=PERSON_PROFILE_SCHEMA,
                example_object_ids=(DEFAULT_OWNER_ID,),
            ),
            ENTITY_TYPE_HOMEPAGE_MAIN: EntityDefinition(
                entity_type=ENTITY_TYPE_HOMEPAGE_MAIN,
                mapper=map_homepage_content,
                body_source=FieldBodySourceSpec(
                    field_name="markdown",
                    filename=HOMEPAGE_MAIN_TEXT_FILENAME,
                ),
                schema=HOMEPAGE_CONTENT_SCHEMA,
                example_object_ids=(DEFAULT_HOMEPAGE_MAIN_ID,),
            ),
        }

    def get(self, entity_type: str) -> EntityDefinition:
        """Return definition for a registered entity type."""
        return self._definitions[entity_type]

    def register(self, definition: EntityDefinition) -> None:
        """Register or replace an entity definition."""
        self._definitions[definition.entity_type] = definition

    def definitions(self) -> list[EntityDefinition]:
        """Return all entity definitions (used for scaffolding)."""
        return list(self._definitions.values())
