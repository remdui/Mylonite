from django.test import SimpleTestCase
from django.urls import resolve, reverse

from apps.panel import views as panel_views
from apps.web import views as web_views


class UrlRoutingTests(SimpleTestCase):
    def test_root_routes_to_home(self):
        self.assertEqual(resolve(reverse("home")).func, web_views.home)

    def test_health_routes_to_health_view(self):
        self.assertEqual(resolve(reverse("health")).func, web_views.health)

    def test_theme_static_routes_to_theme_static_view(self):
        self.assertEqual(
            resolve(reverse("theme_static", kwargs={"asset_path": "css/site.css"})).func,
            web_views.theme_static,
        )

    def test_panel_routes_resolve_to_expected_views(self):
        self.assertEqual(
            resolve(reverse("panel:root")).func.view_class, panel_views.AdminRootView
        )
        self.assertEqual(
            resolve(reverse("panel:setup")).func.view_class, panel_views.SetupView
        )
        self.assertEqual(
            resolve(reverse("panel:setup_complete")).func.view_class,
            panel_views.SetupCompleteView,
        )
        self.assertEqual(
            resolve(reverse("panel:login")).func.view_class, panel_views.PanelLoginView
        )
        self.assertEqual(
            resolve(reverse("panel:logout")).func.view_class,
            panel_views.PanelLogoutView,
        )
        self.assertEqual(
            resolve(reverse("panel:dashboard")).func.view_class,
            panel_views.PanelDashboardView,
        )
        self.assertEqual(
            resolve(reverse("panel:settings")).func.view_class,
            panel_views.PanelSettingsView,
        )
