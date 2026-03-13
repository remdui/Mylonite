from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.panel.models import SiteSetup


User = get_user_model()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class PanelViewTests(TestCase):
    def setUp(self):
        self.owner_password = "StrongPassword123!"

    def create_owner_and_initialize(self, username="owner"):
        owner = User.objects.create_user(
            username=username, password=self.owner_password
        )
        setup = SiteSetup.get_solo()
        setup.owner = owner
        setup.save(update_fields=["owner", "updated_at"])
        return owner

    def test_setup_page_accessible_when_uninitialized(self):
        response = self.client.get(reverse("panel:setup"))
        self.assertEqual(response.status_code, 200)

    def test_setup_post_creates_owner_and_redirects_to_setup_complete(self):
        response = self.client.post(
            reverse("panel:setup"),
            {
                "username": "owner",
                "password1": self.owner_password,
                "password2": self.owner_password,
            },
        )

        self.assertRedirects(
            response, reverse("panel:setup_complete"), fetch_redirect_response=False
        )
        owner = User.objects.get(username="owner")
        self.assertTrue(owner.is_superuser)
        self.assertEqual(SiteSetup.get_solo().owner_id, owner.id)

    def test_setup_redirects_to_root_when_already_initialized(self):
        self.create_owner_and_initialize()
        response = self.client.get(reverse("panel:setup"))
        self.assertRedirects(
            response, reverse("panel:root"), fetch_redirect_response=False
        )

    def test_admin_root_redirects_to_login_for_anonymous_initialized(self):
        self.create_owner_and_initialize()
        response = self.client.get(reverse("panel:root"))
        self.assertRedirects(
            response, reverse("panel:login"), fetch_redirect_response=False
        )

    def test_admin_root_redirects_owner_to_dashboard(self):
        owner = self.create_owner_and_initialize()
        self.client.force_login(owner)

        response = self.client.get(reverse("panel:root"))
        self.assertRedirects(
            response, reverse("panel:dashboard"), fetch_redirect_response=False
        )

    def test_dashboard_requires_owner_permission(self):
        self.create_owner_and_initialize()
        user = User.objects.create_user(username="other", password="StrongPassword123!")
        self.client.force_login(user)

        response = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_setup_complete_requires_session_flag(self):
        owner = self.create_owner_and_initialize()
        self.client.force_login(owner)

        response = self.client.get(reverse("panel:setup_complete"))
        self.assertRedirects(
            response, reverse("panel:dashboard"), fetch_redirect_response=False
        )

    def test_setup_complete_renders_with_session_flag(self):
        owner = self.create_owner_and_initialize()
        self.client.force_login(owner)

        session = self.client.session
        session["mylonite_setup_complete"] = True
        session.save()

        response = self.client.get(reverse("panel:setup_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Setup complete")

    def test_login_view_redirects_to_setup_when_uninitialized(self):
        response = self.client.get(reverse("panel:login"))
        self.assertRedirects(
            response, reverse("panel:setup"), fetch_redirect_response=False
        )

    def test_initialized_login_view_is_accessible(self):
        self.create_owner_and_initialize()
        response = self.client.get(reverse("panel:login"))
        self.assertEqual(response.status_code, 200)

    def test_successful_login_redirects_to_dashboard(self):
        self.create_owner_and_initialize()

        response = self.client.post(
            reverse("panel:login"),
            {
                "username": "owner",
                "password": self.owner_password,
            },
        )

        self.assertRedirects(
            response, reverse("panel:dashboard"), fetch_redirect_response=False
        )

    def test_failed_login_throttles_after_configured_attempts(self):
        self.create_owner_and_initialize()

        with self.settings(
            PANEL_LOGIN_FAILURE_LIMIT=2,
            PANEL_LOGIN_FAILURE_WINDOW_SECONDS=900,
            PANEL_LOGIN_LOCKOUT_SECONDS=900,
        ):
            first = self.client.post(
                reverse("panel:login"),
                {"username": "owner", "password": "wrong-password"},
            )
            self.assertEqual(first.status_code, 200)

            second = self.client.post(
                reverse("panel:login"),
                {"username": "owner", "password": "wrong-password"},
            )
            self.assertEqual(second.status_code, 200)

            third = self.client.post(
                reverse("panel:login"),
                {"username": "owner", "password": "wrong-password"},
            )
            self.assertContains(third, "Too many sign-in attempts")
