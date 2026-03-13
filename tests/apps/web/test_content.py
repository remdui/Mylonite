from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase

from apps.web.content import (
    build_content_status,
    load_portfolio_context,
    resolve_content_file,
)


class ContentLoaderTests(TestCase):
    def test_resolve_content_file_uses_example_fallback(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            target = config_dir / "site.toml"
            fallback = config_dir / "site.toml.example"
            fallback.write_text('site_title = "Example"\n', encoding="utf-8")

            with patch("apps.web.content.CONTENT_ROOT", root):
                resolved, source = resolve_content_file(target)

            self.assertEqual(resolved, fallback)
            self.assertTrue(source["used_example"])
            self.assertFalse(source["missing"])

    def test_build_content_status_tracks_example_and_missing_files(self):
        status = build_content_status(
            [
                {
                    "requested_path": "config/site.toml",
                    "resolved_path": "config/site.toml.example",
                    "used_example": True,
                    "missing": False,
                },
                {
                    "requested_path": "entities/identity.person.owner/entry.toml",
                    "resolved_path": None,
                    "used_example": False,
                    "missing": True,
                },
            ]
        )

        self.assertTrue(status["using_example_files"])
        self.assertEqual(status["example_files"], ["config/site.toml.example"])
        self.assertEqual(
            status["missing_files"],
            ["entities/identity.person.owner/entry.toml"],
        )

    def test_load_portfolio_context_uses_example_files_when_real_files_absent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir(parents=True, exist_ok=True)
            owner_text = root / "entities" / "identity.person.owner" / "text"
            owner_text.mkdir(parents=True, exist_ok=True)

            (root / "config" / "site.toml.example").write_text(
                'site_title = "My Site"\nowner_id = "identity.person.owner"\n',
                encoding="utf-8",
            )
            (
                root / "entities" / "identity.person.owner" / "entry.toml.example"
            ).write_text(
                'id = "identity.person.owner"\nname = "Owner"\nfull_name = "Owner Name"\n',
                encoding="utf-8",
            )
            (owner_text / "website.md.example").write_text(
                "Owner bio from example.",
                encoding="utf-8",
            )

            with patch("apps.web.content.CONTENT_ROOT", root):
                context = load_portfolio_context()

            self.assertEqual(context["portfolio_site"]["site_title"], "My Site")
            self.assertEqual(context["owner_profile"]["full_name"], "Owner Name")
            self.assertTrue(context["content_status"]["using_example_files"])
