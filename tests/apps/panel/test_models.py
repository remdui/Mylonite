from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.panel.models import LoginThrottle, SiteSetup


User = get_user_model()


class SiteSetupModelTests(TestCase):
    def test_get_solo_always_returns_singleton(self):
        first = SiteSetup.get_solo()
        second = SiteSetup.get_solo()

        self.assertEqual(first.pk, SiteSetup.SINGLETON_PK)
        self.assertEqual(second.pk, SiteSetup.SINGLETON_PK)
        self.assertEqual(SiteSetup.objects.count(), 1)

    def test_save_forces_singleton_primary_key(self):
        setup = SiteSetup(id=999)
        setup.save()

        self.assertEqual(setup.pk, SiteSetup.SINGLETON_PK)
        self.assertEqual(SiteSetup.objects.count(), 1)

    def test_is_initialized_and_string_representation(self):
        setup = SiteSetup.get_solo()
        self.assertFalse(setup.is_initialized)
        self.assertEqual(str(setup), "Mylonite setup (uninitialized)")

        owner = User.objects.create_user(username="owner", password="StrongPassword123!")
        setup.owner = owner
        setup.save(update_fields=["owner", "updated_at"])

        self.assertTrue(setup.is_initialized)
        self.assertEqual(str(setup), "Mylonite setup (owner=owner)")


class LoginThrottleModelTests(TestCase):
    def test_string_representation(self):
        throttle = LoginThrottle.objects.create(
            key="panel-login:user:owner",
            failure_count=3,
            first_failure_at=timezone.now(),
            last_failure_at=timezone.now(),
        )

        self.assertEqual(str(throttle), "panel-login:user:owner (3 failures)")
