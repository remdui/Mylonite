from unittest.mock import Mock

from django.test import SimpleTestCase

from mylonite.core.content_types import (
    ContentStatus,
    PersonProfile,
    SiteConfig,
    ValidationStatus,
)
from apps.web.page_contexts import WebPageContextFactory


class PageContextBuilderTests(SimpleTestCase):
    def test_build_homepage_context_shapes_page_view_model(self):
        loader = Mock()
        loader.load_site.return_value = SiteConfig(
            site_title="Mylonite",
            site_url="https://example.test",
            owner_id="identity.person.owner",
            footer_show_generated_by=True,
            footer_repository_url="",
        )
        loader.load_person.return_value = PersonProfile(
            id="identity.person.owner",
            name="",
            full_name="Test Owner",
            display_name="Test Owner",
            headline="Engineer",
            summary="Summary",
            bio="Bio",
        )
        loader.build_content_status.return_value = ContentStatus(
            using_example_files=False,
            example_files=[],
            missing_files=[],
        )
        loader.current_year.return_value = 2026
        loader.build_validation_status.return_value = ValidationStatus(
            has_errors=False, errors=[]
        )

        context = WebPageContextFactory(loader=loader).build_homepage_context()

        self.assertEqual(context["page_title"], "Home")
        self.assertEqual(context["home_page"]["hero"]["display_name"], "Test Owner")
        self.assertEqual(context["home_page"]["hero"]["headline"], "Engineer")
        self.assertEqual(context["portfolio_site"]["site_title"], "Mylonite")
        self.assertFalse(context["validation_status"]["has_errors"])
        loader.begin_tracking.assert_called_once_with()


class PageRegistryTests(SimpleTestCase):
    def test_build_page_context_uses_registered_builder(self):
        class StubBuilder:
            page_name = "stub"

            def build(self, shared, loader):
                return {"page_title": "Stub", "owner_name": shared.owner.full_name}

        loader = Mock()
        loader.load_site.return_value = SiteConfig(
            site_title="Mylonite",
            site_url="https://example.test",
            owner_id="identity.person.owner",
            footer_show_generated_by=True,
            footer_repository_url="",
        )
        loader.load_person.return_value = PersonProfile(
            id="identity.person.owner",
            name="",
            full_name="Test Owner",
            display_name="Test Owner",
            headline="Engineer",
            summary="Summary",
            bio="Bio",
        )
        loader.build_content_status.return_value = ContentStatus(
            using_example_files=False,
            example_files=[],
            missing_files=[],
        )
        loader.current_year.return_value = 2026
        loader.build_validation_status.return_value = ValidationStatus(
            has_errors=False, errors=[]
        )

        context = WebPageContextFactory(
            loader=loader,
            builders={"stub": StubBuilder()},
        ).build_page_context("stub")

        self.assertEqual(context["page_title"], "Stub")
        self.assertEqual(context["owner_name"], "Test Owner")
