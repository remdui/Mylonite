from dataclasses import dataclass
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.panel.forms import PanelAuthenticationForm
from apps.panel.forms import OwnerSetupForm

User = get_user_model()


class OwnerSetupFormTests(TestCase):
    def test_save_creates_owner_with_admin_permissions(self):
        form = OwnerSetupForm(
            data={
                "username": "owner",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(User.objects.filter(username="owner").exists())


@dataclass
class DummyLockout:
    is_locked: bool


class PanelAuthenticationFormTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(username="owner", password=self.password)

    def test_locked_user_fails_before_authentication(self):
        request = self.factory.post("/admin/login/")

        with patch(
            "apps.panel.forms.get_login_lockout",
            return_value=DummyLockout(is_locked=True),
        ):
            form = PanelAuthenticationForm(
                request=request,
                data={"username": "owner", "password": "wrong"},
            )
            self.assertFalse(form.is_valid())
            self.assertIn("Too many sign-in attempts", form.non_field_errors()[0])

    def test_failed_auth_registers_failed_attempt(self):
        request = self.factory.post("/admin/login/")

        with patch("apps.panel.forms.register_failed_login_attempt") as register_failed:
            form = PanelAuthenticationForm(
                request=request,
                data={"username": "owner", "password": "wrong"},
            )
            self.assertFalse(form.is_valid())

        register_failed.assert_called_once_with(request, "owner")

    def test_successful_auth_clears_login_throttle(self):
        request = self.factory.post("/admin/login/")

        with patch("apps.panel.forms.clear_login_throttle") as clear_throttle:
            form = PanelAuthenticationForm(
                request=request,
                data={"username": "owner", "password": self.password},
            )
            self.assertTrue(form.is_valid(), form.errors)

        clear_throttle.assert_called_once_with(request, "owner")
