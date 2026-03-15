from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase

from apps.web.content_loader import PortfolioContentLoader, build_content_status
from apps.web.content_repository import resolve_content_file
from mylonite.core.content_types import ContentStatus, SourceInfo, ValidationStatus


class ContentLoaderTests(TestCase):
    def test_resolve_content_file_uses_example_fallback(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            target = config_dir / "site.toml"
            fallback = config_dir / "site.toml.example"
            fallback.write_text('site_title = "Example"\n', encoding="utf-8")

            with patch("apps.web.content_repository.CONTENT_ROOT", root):
                resolved, source = resolve_content_file(target)

            self.assertEqual(resolved, fallback)
            self.assertTrue(source.used_example)
            self.assertFalse(source.missing)

    def test_build_content_status_tracks_example_and_missing_files(self):
        status = build_content_status(
            [
                SourceInfo(
                    requested_path="config/site.toml",
                    resolved_path="config/site.toml.example",
                    used_example=True,
                    missing=False,
                ),
                SourceInfo(
                    requested_path="entities/identity.person.owner/entry.toml",
                    resolved_path=None,
                    used_example=False,
                    missing=True,
                ),
            ]
        )

        self.assertIsInstance(status, ContentStatus)
        self.assertTrue(status.using_example_files)
        self.assertEqual(status.example_files, ["config/site.toml.example"])
        self.assertEqual(
            status.missing_files,
            ["entities/identity.person.owner/entry.toml"],
        )

    def test_begin_tracking_resets_source_state(self):
        loader = PortfolioContentLoader()
        loader._track_sources(
            [
                SourceInfo(
                    requested_path="config/site.toml",
                    resolved_path="config/site.toml.example",
                    used_example=True,
                    missing=False,
                )
            ]
        )

        loader.begin_tracking()

        self.assertEqual(loader.build_content_status().example_files, [])


    def test_load_entity_supports_custom_mapper(self):
        class StubRepository:
            def load_site_record(self):
                return {}, []

            def load_entity_record(self, object_id: str, *, text_filename: str = "website.md"):
                return {"id": object_id, "name": "Custom"}, "Body", []

            def list_entity_ids(self, *, prefix: str = ""):
                return []

        loader = PortfolioContentLoader(repository=StubRepository())

        result = loader.load_entity(
            "entity.custom",
            lambda object_id, entry, body: {
                "object_id": object_id,
                "name": entry.get("name"),
                "body": body,
            },
        )

        self.assertEqual(result["object_id"], "entity.custom")
        self.assertEqual(result["name"], "Custom")
        self.assertEqual(result["body"], "Body")


    def test_loader_tracks_validation_errors_for_registered_entity(self):
        class StubRepository:
            def load_site_record(self):
                return {"site_title": "Site"}, []

            def load_entity_record(self, object_id: str, *, text_filename: str = "website.md"):
                return {"id": object_id}, "Body", []

            def list_entity_ids(self, *, prefix: str = ""):
                return []

        loader = PortfolioContentLoader(repository=StubRepository())
        loader.begin_tracking()
        loader.load_person("identity.person.owner")

        status = loader.build_validation_status()

        self.assertIsInstance(status, ValidationStatus)
        self.assertTrue(status.has_errors)
        self.assertTrue(any("full_name: required" in error for error in status.errors))

    def test_portfolio_content_loader_tracks_sources_across_calls(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir(parents=True, exist_ok=True)
            owner_text = root / "entities" / "identity.person.owner" / "text"
            owner_text.mkdir(parents=True, exist_ok=True)

            (root / "config" / "site.toml.example").write_text(
                'site_title = "Loader Site"\nowner_id = "identity.person.owner"\n',
                encoding="utf-8",
            )
            (root / "entities" / "identity.person.owner" / "entry.toml.example").write_text(
                'id = "identity.person.owner"\nfull_name = "Loader Owner"\n',
                encoding="utf-8",
            )
            (owner_text / "website.md.example").write_text(
                "Loader owner bio.",
                encoding="utf-8",
            )

            with patch("apps.web.content_repository.CONTENT_ROOT", root):
                loader = PortfolioContentLoader()
                site = loader.load_site()
                owner = loader.load_person(site.owner_id)
                status = loader.build_content_status()

            self.assertEqual(site.site_title, "Loader Site")
            self.assertEqual(owner.full_name, "Loader Owner")
            self.assertTrue(status.using_example_files)
