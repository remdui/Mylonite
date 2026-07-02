from django.test import SimpleTestCase

from apps.web.view_models import HomeHeroViewModel, HomePageViewModel, LayoutViewModel


class ViewModelTests(SimpleTestCase):
    def test_layout_view_model_maps_to_template_context(self):
        model = LayoutViewModel(
            site_title="Mylonite",
            site_url="https://example.test",
            footer_show_generated_by=True,
            footer_repository_url="",
            owner_full_name="Owner Name",
            content_status={
                "using_example_files": False,
                "example_files": [],
                "missing_files": [],
            },
            current_year=2026,
        )

        context = model.to_context()
        self.assertEqual(context["portfolio_site"]["site_title"], "Mylonite")
        self.assertEqual(context["owner_profile"]["full_name"], "Owner Name")

    def test_home_page_view_model_maps_hero_context(self):
        hero = HomeHeroViewModel(
            display_name="Owner Name",
            headline="Engineer",
            bio="Bio",
            intro_markdown="Intro",
            summary="Summary",
        )
        page = HomePageViewModel(page_title="Home", hero=hero)

        context = page.to_context()
        self.assertEqual(context["page_title"], "Home")
        self.assertEqual(context["home_page"]["hero"]["headline"], "Engineer")
