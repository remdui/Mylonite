from datetime import timedelta
from ipaddress import ip_network

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from apps.panel.models import LoginThrottle, SiteSetup
from apps.panel.services import (
    build_throttle_keys,
    clear_login_throttle,
    get_client_identifier,
    get_login_lockout,
    normalize_username,
    panel_is_initialized,
    register_failed_login_attempt,
    user_is_owner,
)


User = get_user_model()


class PanelServiceStateTests(TestCase):
    def test_panel_is_initialized_and_user_is_owner(self):
        owner = User.objects.create_user(username="owner", password="StrongPassword123!")
        setup = SiteSetup.get_solo()
        setup.owner = owner
        setup.save()

        self.assertTrue(panel_is_initialized())
        self.assertTrue(user_is_owner(owner))

        outsider = User.objects.create_user(username="outsider", password="StrongPassword123!")
        self.assertFalse(user_is_owner(outsider))


class LoginThrottleServiceTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_normalize_username(self):
        self.assertEqual(normalize_username("  Owner.User  "), "owner.user")

    def test_build_throttle_keys_uses_client_and_normalized_user(self):
        request = self.factory.post("/admin/login/", REMOTE_ADDR="127.0.0.1")
        keys = build_throttle_keys(request, "  UserName ")

        self.assertIn("panel-login:client:127.0.0.1", keys)
        self.assertIn("panel-login:user:username", keys)

    @override_settings(MYLONITE_TRUSTED_PROXY_CIDRS=())
    def test_get_client_identifier_ignores_forwarded_headers_when_proxy_untrusted(self):
        request = self.factory.post(
            "/admin/login/",
            REMOTE_ADDR="203.0.113.5",
            HTTP_X_FORWARDED_FOR="198.51.100.11",
        )
        self.assertEqual(get_client_identifier(request), "203.0.113.5")

    @override_settings(MYLONITE_TRUSTED_PROXY_CIDRS=(ip_network("203.0.113.0/24"),))
    def test_get_client_identifier_uses_forwarded_header_when_proxy_trusted(self):
        request = self.factory.post(
            "/admin/login/",
            REMOTE_ADDR="203.0.113.5",
            HTTP_X_FORWARDED_FOR="198.51.100.11, 203.0.113.5",
        )
        self.assertEqual(get_client_identifier(request), "198.51.100.11")

    @override_settings(
        PANEL_LOGIN_FAILURE_LIMIT=2,
        PANEL_LOGIN_FAILURE_WINDOW_SECONDS=900,
        PANEL_LOGIN_LOCKOUT_SECONDS=900,
    )
    def test_register_failed_login_attempt_locks_after_limit(self):
        request = self.factory.post("/admin/login/", REMOTE_ADDR="127.0.0.1")

        register_failed_login_attempt(request, "owner")
        first = get_login_lockout(request, "owner")
        self.assertFalse(first.is_locked)

        register_failed_login_attempt(request, "owner")
        second = get_login_lockout(request, "owner")
        self.assertTrue(second.is_locked)
        self.assertIsNotNone(second.locked_until)

    @override_settings(
        PANEL_LOGIN_FAILURE_LIMIT=5,
        PANEL_LOGIN_FAILURE_WINDOW_SECONDS=60,
        PANEL_LOGIN_LOCKOUT_SECONDS=120,
    )
    def test_failure_window_resets_counter(self):
        request = self.factory.post("/admin/login/", REMOTE_ADDR="127.0.0.1")
        register_failed_login_attempt(request, "owner")

        throttle = LoginThrottle.objects.get(key="panel-login:user:owner")
        throttle.first_failure_at = timezone.now() - timedelta(seconds=61)
        throttle.save(update_fields=["first_failure_at", "updated_at"])

        register_failed_login_attempt(request, "owner")

        throttle.refresh_from_db()
        self.assertEqual(throttle.failure_count, 1)
        self.assertIsNone(throttle.locked_until)

    def test_clear_login_throttle_removes_records(self):
        request = self.factory.post("/admin/login/", REMOTE_ADDR="127.0.0.1")
        register_failed_login_attempt(request, "owner")
        self.assertGreater(LoginThrottle.objects.count(), 0)

        clear_login_throttle(request, "owner")
        self.assertEqual(LoginThrottle.objects.count(), 0)
