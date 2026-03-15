from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from mylonite.core.build_workflow import BuildInput, build_cache_key
from apps.web.content_entities import FieldBodySourceSpec
from apps.web.content_loader import PortfolioContentLoader
from apps.web.content_registry import ContentEntityRegistry, EntityDefinition
from mylonite.core.content_schema import PERSON_PROFILE_SCHEMA, validate_record
from mylonite.core.content_types import ThemeSettings
from mylonite.core.theme_loader import ThemeResolver


class ArchitectureExtensionTests(SimpleTestCase):
    @staticmethod
    def _create_theme(root: Path, theme_id: str) -> None:
        theme_root = root / theme_id
        (theme_root / "static").mkdir(parents=True)
        (theme_root / "theme.toml").write_text(
            '\n'.join(
                [
                    f'name = "{theme_id.title()}"',
                    f'description = "{theme_id} theme"',
                    'version = "1.0.0"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_entity_registry_can_register_new_entity_type(self):
        registry = ContentEntityRegistry()
        registry.register(
            EntityDefinition(
                entity_type="project",
                mapper=lambda object_id, entry, body: {
                    "id": object_id,
                    "title": entry.get("title", ""),
                    "description": body,
                },
                body_source=FieldBodySourceSpec(
                    field_name="description",
                    filename="description.md",
                ),
            )
        )

        definition = registry.get("project")
        self.assertEqual(definition.body_source.text_filename, "description.md")

    def test_loader_can_use_registered_entity_mapper(self):
        class StubRepository:
            def load_site_record(self):
                return {}, []

            def load_entity_record(
                self, object_id: str, *, text_filename: str | None = None
            ):
                return {"title": "Project A"}, "Project body", []

            def list_entity_ids(self, *, prefix: str = ""):
                return ["project.a"]

        registry = ContentEntityRegistry(definitions={})
        registry.register(
            EntityDefinition(
                entity_type="project",
                mapper=lambda object_id, entry, body: {
                    "id": object_id,
                    "title": entry.get("title", ""),
                    "body": body,
                },
                body_source=FieldBodySourceSpec(
                    field_name="description",
                    filename="description.md",
                ),
            )
        )

        loader = PortfolioContentLoader(
            repository=StubRepository(), entity_registry=registry
        )
        project = loader.load_registered_entity("project", "project.a")

        self.assertEqual(project["id"], "project.a")
        self.assertEqual(project["title"], "Project A")

    def test_theme_resolver_falls_back_to_default_theme(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_theme(root, "default")

            resolved = ThemeResolver(root).resolve(ThemeSettings(name="custom"))

        self.assertEqual(resolved.active_theme.theme_id, "default")
        self.assertEqual(resolved.active_theme.static_dir.name, "static")

    def test_schema_validation_returns_normalized_payload_and_errors(self):
        normalized, errors = validate_record(
            PERSON_PROFILE_SCHEMA,
            {
                "id": "identity.person.owner",
                "full_name": "Owner",
                "profile_image_path": "/media/owner.png",
            },
        )

        self.assertEqual(errors, [])
        self.assertEqual(normalized["full_name"], "Owner")

    def test_build_cache_key_changes_with_theme(self):
        key_a = build_cache_key(
            BuildInput(site_id="site", content_version="1", theme_name="default")
        )
        key_b = build_cache_key(
            BuildInput(site_id="site", content_version="1", theme_name="modern")
        )

        self.assertNotEqual(key_a, key_b)

    def test_loader_validation_status_exposes_site_config_errors(self):
        class StubRepository:
            def load_site_record(self):
                return {"site_title": "Site"}, []

            def load_entity_record(
                self, object_id: str, *, text_filename: str | None = None
            ):
                return {}, "", []

            def list_entity_ids(self, *, prefix: str = ""):
                return []

        loader = PortfolioContentLoader(repository=StubRepository())
        loader.begin_tracking()
        loader.load_site()

        validation_status = loader.build_validation_status()

        self.assertTrue(validation_status.has_errors)
        self.assertTrue(
            any("site_url: required" in error for error in validation_status.errors)
        )
