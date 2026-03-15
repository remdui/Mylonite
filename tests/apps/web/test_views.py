from unittest.mock import patch

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse

from mylonite.core.site_config_store import write_site_config_payload


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class WebViewTests(TestCase):
    @staticmethod
    def _create_theme(theme_root: Path, theme_id: str, css: str | None = None) -> None:
        root = theme_root / theme_id
        (root / "static").mkdir(parents=True, exist_ok=True)
        (root / "theme.toml").write_text(
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
        if css is not None:
            css_path = root / "static" / "css" / "site.css"
            css_path.parent.mkdir(parents=True, exist_ok=True)
            css_path.write_text(css, encoding="utf-8")

    @staticmethod
    def _write_site_config(content_root: Path, theme_name: str) -> None:
        write_site_config_payload(
            content_root,
            {
                "site_title": "Site",
                "site_url": "http://localhost:8000",
                "owner_id": "identity.person.owner",
                "footer_show_generated_by": True,
                "footer_repository_url": "",
                "hosting_mode": "local",
                "public_domain": "",
                "theme": {"name": theme_name, "custom_theme_allowed": True},
                "install": {
                    "setup_wizard_enabled": True,
                    "deferred_setup_allowed": True,
                },
            },
        )

    def test_health_returns_ok_payload(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_homepage_renders(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mylonite")

    def test_homepage_uses_context_factory(self):
        expected_context = {
            "portfolio_site": {
                "site_title": "Mylonite",
                "site_url": "https://example.test",
            },
            "owner_profile": {"full_name": "Test Owner"},
            "content_status": {
                "using_example_files": False,
                "example_files": [],
                "missing_files": [],
            },
            "current_year": 2026,
            "home_page": {
                "hero": {
                    "display_name": "Test Owner",
                    "headline": "",
                    "bio": "",
                    "summary": "",
                }
            },
            "page_title": "Home",
        }

        with patch(
            "apps.web.views.WebPageContextFactory.build_page_context",
            return_value=expected_context,
        ):
            response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Owner")

    def test_theme_static_falls_back_to_default_asset(self):
        with TemporaryDirectory() as themes_tmp, TemporaryDirectory() as content_tmp:
            themes_root = Path(themes_tmp)
            content_root = Path(content_tmp)
            self._create_theme(themes_root, "default", css="body { color: red; }\n")
            self._create_theme(themes_root, "ocean")
            self._write_site_config(content_root, theme_name="ocean")

            with self.settings(
                MYLONITE_THEMES_ROOT=themes_root,
                MYLONITE_CONTENT_ROOT=content_root,
            ):
                response = self.client.get(
                    reverse(
                        "theme_static",
                        kwargs={"asset_path": "css/site.css"},
                    )
                )

        self.assertEqual(response.status_code, 200)
        css = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("color: red", css)

    def test_theme_static_merges_default_css_with_theme_overrides(self):
        with TemporaryDirectory() as themes_tmp, TemporaryDirectory() as content_tmp:
            themes_root = Path(themes_tmp)
            content_root = Path(content_tmp)
            self._create_theme(themes_root, "default", css="body { color: red; }\n")
            self._create_theme(themes_root, "ocean", css="body { color: blue; }\n")
            self._write_site_config(content_root, theme_name="ocean")

            with self.settings(
                MYLONITE_THEMES_ROOT=themes_root,
                MYLONITE_CONTENT_ROOT=content_root,
            ):
                response = self.client.get(
                    reverse(
                        "theme_static",
                        kwargs={"asset_path": "css/site.css"},
                    )
                )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Theme overrides (ocean)")
        self.assertContains(response, "color: red")
        self.assertContains(response, "color: blue")

    def test_theme_static_does_not_merge_non_primary_css_assets(self):
        with TemporaryDirectory() as themes_tmp, TemporaryDirectory() as content_tmp:
            themes_root = Path(themes_tmp)
            content_root = Path(content_tmp)
            self._create_theme(themes_root, "default")
            self._create_theme(themes_root, "ocean")

            default_print = themes_root / "default" / "static" / "css" / "print.css"
            default_print.parent.mkdir(parents=True, exist_ok=True)
            default_print.write_text("body { color: red; }\n", encoding="utf-8")

            ocean_print = themes_root / "ocean" / "static" / "css" / "print.css"
            ocean_print.parent.mkdir(parents=True, exist_ok=True)
            ocean_print.write_text("body { color: blue; }\n", encoding="utf-8")

            self._write_site_config(content_root, theme_name="ocean")

            with self.settings(
                MYLONITE_THEMES_ROOT=themes_root,
                MYLONITE_CONTENT_ROOT=content_root,
            ):
                response = self.client.get(
                    reverse(
                        "theme_static",
                        kwargs={"asset_path": "css/print.css"},
                    )
                )

        self.assertEqual(response.status_code, 200)
        css = b"".join(response.streaming_content).decode("utf-8")
        self.assertNotIn("Theme overrides (ocean)", css)
        self.assertNotIn("color: red", css)
        self.assertIn("color: blue", css)
