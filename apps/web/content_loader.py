from datetime import date
from typing import Callable, Protocol, TypeVar

from .content_mappers import map_site_config
from .content_registry import ContentEntityRegistry
from .content_repository import FileSystemContentRepository
from mylonite.core.content_schema import (
    SITE_CONFIG_SCHEMA,
    SchemaDefinition,
    validate_record,
)
from mylonite.core.content_types import (
    ContentStatus,
    PersonProfile,
    SiteConfig,
    SourceInfo,
    ValidationStatus,
)

EntityModel = TypeVar("EntityModel")


class ContentRepository(Protocol):
    def load_site_record(self) -> tuple[dict, list[SourceInfo]]: ...

    def load_entity_record(
        self,
        object_id: str,
        *,
        text_filename: str = "website.md",
    ) -> tuple[dict, str, list[SourceInfo]]: ...

    def list_entity_ids(self, *, prefix: str = "") -> list[str]: ...


def build_content_status(sources: list[SourceInfo]) -> ContentStatus:
    example_files = [
        source.resolved_path
        for source in sources
        if source.used_example and source.resolved_path
    ]
    missing_files = [source.requested_path for source in sources if source.missing]

    return ContentStatus(
        using_example_files=bool(example_files),
        example_files=example_files,
        missing_files=missing_files,
    )


class PortfolioContentLoader:
    """Use-case level content loader with source tracking and entity registry."""

    def __init__(
        self,
        repository: ContentRepository | None = None,
        entity_registry: ContentEntityRegistry | None = None,
    ):
        self.repository = repository or FileSystemContentRepository()
        self.entity_registry = entity_registry or ContentEntityRegistry()
        self._sources: list[SourceInfo] = []
        self._validation_errors: list[str] = []

    def begin_tracking(self) -> None:
        self._sources = []
        self._validation_errors = []

    def _track_sources(self, sources: list[SourceInfo]) -> None:
        self._sources.extend(sources)

    def _validate(self, scope: str, payload: dict, schema: SchemaDefinition) -> dict:
        normalized, errors = validate_record(schema, payload)
        self._validation_errors.extend([f"{scope}: {error}" for error in errors])
        return {**payload, **normalized}

    def load_site(self) -> SiteConfig:
        site_data, site_sources = self.repository.load_site_record()
        self._track_sources(site_sources)
        validated_site_data = self._validate("site", site_data, SITE_CONFIG_SCHEMA)
        return map_site_config(validated_site_data)

    def load_entity(
        self,
        object_id: str,
        mapper: Callable[[str, dict, str], EntityModel],
        *,
        text_filename: str = "website.md",
        schema: SchemaDefinition | None = None,
    ) -> EntityModel:
        entry, body, sources = self.repository.load_entity_record(
            object_id,
            text_filename=text_filename,
        )
        self._track_sources(sources)

        validated_entry = (
            self._validate(object_id, entry, schema) if schema is not None else entry
        )
        return mapper(object_id, validated_entry, body)

    def load_registered_entity(self, entity_type: str, object_id: str):
        definition = self.entity_registry.get(entity_type)
        return self.load_entity(
            object_id,
            definition.mapper,
            text_filename=definition.text_filename,
            schema=definition.schema,
        )

    def list_entity_ids(self, *, prefix: str = "") -> list[str]:
        return self.repository.list_entity_ids(prefix=prefix)

    def load_person(self, object_id: str) -> PersonProfile:
        return self.load_registered_entity("person", object_id)

    def build_content_status(self) -> ContentStatus:
        return build_content_status(self._sources)

    def build_validation_status(self) -> ValidationStatus:
        return ValidationStatus(
            has_errors=bool(self._validation_errors),
            errors=list(self._validation_errors),
        )

    def current_year(self) -> int:
        return date.today().year
