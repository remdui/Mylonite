from dataclasses import dataclass
from typing import Callable, TypeVar

from .content_mappers import map_person_profile
from mylonite.core.content_schema import PERSON_PROFILE_SCHEMA, SchemaDefinition

EntityModel = TypeVar("EntityModel")


@dataclass(frozen=True)
class EntityDefinition:
    entity_type: str
    mapper: Callable[[str, dict, str], EntityModel]
    text_filename: str = "website.md"
    schema: SchemaDefinition | None = None


class ContentEntityRegistry:
    def __init__(self, definitions: dict[str, EntityDefinition] | None = None):
        self._definitions = definitions or {
            "person": EntityDefinition(
                entity_type="person",
                mapper=map_person_profile,
                text_filename="website.md",
                schema=PERSON_PROFILE_SCHEMA,
            )
        }

    def get(self, entity_type: str) -> EntityDefinition:
        return self._definitions[entity_type]

    def register(self, definition: EntityDefinition) -> None:
        self._definitions[definition.entity_type] = definition
