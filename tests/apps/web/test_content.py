from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase

from apps.web.content_loader import (
    ContentValidationError,
    PortfolioContentLoader,
    build_content_status,
)
from apps.web.content_repository import FileSystemContentRepository, resolve_content_file
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

    def test_loader_tracks_validation_errors_for_registered_entity(self):
        class StubRepository:
            def load_site_record(self):
                return {"site_title": "Site"}, []

            def load_entity_record(
                self, object_id: str, *, text_filename: str | None = None
            ):
                return {"id": object_id, "schema_version": "invalid"}, "Body", []

            def list_entity_ids(self, *, prefix: str = ""):
                return []

        loader = PortfolioContentLoader(repository=StubRepository())
        loader.begin_tracking()
        loader.load_person("identity.person.owner")

        status = loader.build_validation_status()

        self.assertIsInstance(status, ValidationStatus)
        self.assertTrue(status.has_errors)
        self.assertTrue(
            any("schema_version: invalid type" in error for error in status.errors)
        )

    def test_loader_raises_in_strict_validation_mode(self):
        class StubRepository:
            def load_site_record(self):
                return {"site_title": "Site"}, []

            def load_entity_record(
                self, object_id: str, *, text_filename: str | None = None
            ):
                return {"id": object_id, "schema_version": "invalid"}, "Body", []

            def list_entity_ids(self, *, prefix: str = ""):
                return []

        loader = PortfolioContentLoader(
            repository=StubRepository(),
            strict_validation=True,
        )

        loader.begin_tracking()
        with self.assertRaises(ContentValidationError):
            loader.load_person("identity.person.owner")

    def test_loader_generates_examples_from_schema(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("apps.web.content_repository.CONTENT_ROOT", root):
                loader = PortfolioContentLoader()
                loader.sync_example_content()

            site_example = root / "config" / "site.toml.example"
            person_entry_example = (
                root / "entities" / "identity.person.owner" / "entry.toml.example"
            )
            homepage_body_example = (
                root / "entities" / "content.homepage.main" / "text" / "main.md.example"
            )

            self.assertTrue(site_example.exists())
            self.assertTrue(person_entry_example.exists())
            self.assertTrue(homepage_body_example.exists())
            self.assertIn(
                'owner_id = "identity.person.owner"', site_example.read_text()
            )

    def test_loader_regenerates_outdated_examples(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale_file = root / "config" / "site.toml.example"
            stale_file.parent.mkdir(parents=True, exist_ok=True)
            stale_file.write_text('site_title = "Old"\n', encoding="utf-8")

            with patch("apps.web.content_repository.CONTENT_ROOT", root):
                loader = PortfolioContentLoader()
                loader.sync_example_content()

            refreshed = stale_file.read_text(encoding="utf-8")
            self.assertIn('site_url = "http://localhost:8000"', refreshed)
            self.assertIn("footer_show_generated_by = true", refreshed)

    def test_loader_tolerates_unwritable_content_root(self):
        with patch(
            "apps.web.content_loader.sync_content_examples", side_effect=PermissionError
        ):
            loader = PortfolioContentLoader()
            synced = loader.sync_example_content()

        self.assertIsInstance(loader, PortfolioContentLoader)
        self.assertFalse(synced)

    def test_portfolio_content_loader_tracks_sources_across_calls(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir(parents=True, exist_ok=True)
            homepage_text = root / "entities" / "content.homepage.main" / "text"
            homepage_text.mkdir(parents=True, exist_ok=True)

            (root / "config" / "site.toml.example").write_text(
                'site_title = "Loader Site"\nowner_id = "identity.person.owner"\n',
                encoding="utf-8",
            )
            owner_root = root / "entities" / "identity.person.owner"
            owner_root.mkdir(parents=True, exist_ok=True)
            (owner_root / "entry.toml.example").write_text(
                'id = "identity.person.owner"\nfull_name = "Loader Owner"\n',
                encoding="utf-8",
            )
            (
                root / "entities" / "content.homepage.main" / "entry.toml.example"
            ).write_text(
                'id = "content.homepage.main"\ntitle = "Homepage Main Content"\n',
                encoding="utf-8",
            )
            (homepage_text / "main.md.example").write_text(
                "Loader homepage markdown.",
                encoding="utf-8",
            )

            with patch("apps.web.content_repository.CONTENT_ROOT", root):
                loader = PortfolioContentLoader()
                site = loader.load_site()
                owner = loader.load_person(site.owner_id)
                loader.load_homepage_main()
                status = loader.build_content_status()

            self.assertEqual(site.site_title, "Loader Site")
            self.assertEqual(owner.full_name, "Loader Owner")
            self.assertTrue(status.using_example_files)

    def test_repository_rejects_invalid_entity_id(self):
        with TemporaryDirectory() as tmp:
            repository = FileSystemContentRepository(content_root=Path(tmp))

            with self.assertRaises(ValueError):
                repository.load_entity_record("../escape")
