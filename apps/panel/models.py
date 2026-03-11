from django.conf import settings
from django.db import models
from django.utils import timezone


class SiteSetup(models.Model):
    SINGLETON_PK = 1

    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=SINGLETON_PK,
        editable=False,
    )
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="mylonite_owned_site",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site setup state"
        verbose_name_plural = "Site setup state"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_PK
        return super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        setup, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return setup

    @property
    def is_initialized(self) -> bool:
        return self.owner_id is not None

    def user_is_owner(self, user) -> bool:
        return bool(user and user.is_authenticated and self.owner_id == user.pk)

    def __str__(self) -> str:
        if self.owner_id:
            return f"Mylonite setup (owner={self.owner.username})"
        return "Mylonite setup (uninitialized)"


class LoginThrottle(models.Model):
    key = models.CharField(max_length=255, unique=True)
    failure_count = models.PositiveIntegerField(default=0)
    first_failure_at = models.DateTimeField()
    last_failure_at = models.DateTimeField()
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Login throttle"
        verbose_name_plural = "Login throttles"

    def __str__(self) -> str:
        return f"{self.key} ({self.failure_count} failures)"
