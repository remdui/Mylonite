import logging
from datetime import date
from typing import Callable, Protocol, TypeVar

from .content_mappers import map_site_config
from .content_registry import ContentEntityRegistry
from .content_repository import FileSystemContentRepository
from .content_scaffold import sync_content_examples
from mylonite.core.content_conventions import (
    DEFAULT_HOMEPAGE_MAIN_ID,
    ENTITY_TYPE_HOMEPAGE_MAIN,
    ENTITY_TYPE_PERSON,
)
from mylonite.core.content_schema import SITE_CONFIG_SCHEMA, SchemaDefinition, validate_record
from mylonite.core.content_types import (
    ContentStatus,
    HomePageContent,
    PersonProfile,
    SiteConfig,
    SourceInfo,
    ValidationStatus,
)

EntityModel = TypeVar("EntityModel")
logger = logging.getLogger(__name__)


class ContentRepository(Protocol):
    """Protocol for content source backends used by the loader."""
    def load_site_record(self) -> tuple[dict, list[SourceInfo]]: ...

    def load_entity_record(
        self,
        object_id: str,
        *,
        text_filename: str | None = None,
    ) -> tuple[dict, str, list[SourceInfo]]: ...

    def list_entity_ids(self, *, prefix: str = "") -> list[str]: ...


def build_content_status(sources: list[SourceInfo]) -> ContentStatus:
    """Summarize source usage (example/missing files) for UI diagnostics."""
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

    def sync_example_content(self) -> bool:
        """Generate or refresh schema-based local `*.example` content files."""
        if not isinstance(self.repository, FileSystemContentRepository):
            return False

        try:
            sync_content_examples(self.repository.content_root, self.entity_registry)
            return True
        except OSError:
            logger.warning(
                "Unable to sync content examples for %s",
                self.repository.content_root,
                exc_info=True,
            )
            return False

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
        text_filename: str | None = None,
        schema: SchemaDefinition | None = None,
    ) -> EntityModel:
        entry, body, sources = self.repository.load_entity_record(
            object_id,
            text_filename=text_filename,
        )
        self._track_sources(sources)

        payload = dict(entry)

        validated_entry = (
            self._validate(object_id, payload, schema) if schema is not None else payload
        )
        return mapper(object_id, validated_entry, body)

    def load_registered_entity(self, entity_type: str, object_id: str):
        """Load an entity via registry metadata and body-source strategy."""
        definition = self.entity_registry.get(entity_type)
        entry, body, sources = self.repository.load_entity_record(
            object_id,
            text_filename=definition.body_source.text_filename,
        )
        self._track_sources(sources)

        payload = definition.body_source.merge_payload(entry, body)
        validated_entry = (
            self._validate(object_id, payload, definition.schema)
            if definition.schema is not None
            else payload
        )
        return definition.mapper(object_id, validated_entry, body)

    def list_entity_ids(self, *, prefix: str = "") -> list[str]:
        return self.repository.list_entity_ids(prefix=prefix)

    def load_person(self, object_id: str) -> PersonProfile:
        return self.load_registered_entity(ENTITY_TYPE_PERSON, object_id)

    def load_homepage_main(
        self, object_id: str = DEFAULT_HOMEPAGE_MAIN_ID
    ) -> HomePageContent:
        return self.load_registered_entity(ENTITY_TYPE_HOMEPAGE_MAIN, object_id)

    def build_content_status(self) -> ContentStatus:
        return build_content_status(self._sources)

    def build_validation_status(self) -> ValidationStatus:
        return ValidationStatus(
            has_errors=bool(self._validation_errors),
            errors=list(self._validation_errors),
        )

    def current_year(self) -> int:
        return date.today().year
