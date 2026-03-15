from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class WebViewTests(TestCase):
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
            "portfolio_site": {"site_title": "Mylonite", "site_url": "https://example.test"},
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
