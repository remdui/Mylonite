from __future__ import annotations

import fcntl
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from ipaddress import ip_address
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .models import LoginThrottle, SiteSetup


class InitialSetupAlreadyComplete(Exception):
    pass


@dataclass(frozen=True)
class LockoutState:
    is_locked: bool
    locked_until: datetime | None = None


def get_setup_state() -> SiteSetup:
    return SiteSetup.get_solo()


def panel_is_initialized() -> bool:
    return get_setup_state().is_initialized


def user_is_owner(user) -> bool:
    return get_setup_state().user_is_owner(user)


@contextmanager
def owner_setup_lock():
    lock_dir = Path(settings.MYLONITE_DATA_ROOT) / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)

    lock_path = lock_dir / "owner-setup.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def normalize_username(username: str) -> str:
    return username.strip().casefold()


def is_trusted_proxy(remote_addr: str) -> bool:
    if not remote_addr:
        return False

    try:
        remote_ip = ip_address(remote_addr)
    except ValueError:
        return False

    return any(
        remote_ip in network for network in settings.MYLONITE_TRUSTED_PROXY_CIDRS
    )


def get_forwarded_client_ip(request) -> str | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded_for:
        candidate = x_forwarded_for.split(",")[0].strip()
        try:
            ip_address(candidate)
            return candidate
        except ValueError:
            pass

    x_real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
    if x_real_ip:
        try:
            ip_address(x_real_ip)
            return x_real_ip
        except ValueError:
            pass

    return None


def get_client_identifier(request) -> str:
    remote_addr = request.META.get("REMOTE_ADDR", "").strip()

    if is_trusted_proxy(remote_addr):
        forwarded_ip = get_forwarded_client_ip(request)
        if forwarded_ip:
            return forwarded_ip

    return remote_addr or "unknown"


def build_throttle_keys(request, username: str) -> list[str]:
    keys = [f"panel-login:client:{get_client_identifier(request)}"]

    normalized_username = normalize_username(username)
    if normalized_username:
        keys.append(f"panel-login:user:{normalized_username}")

    return keys


def get_login_lockout(request, username: str) -> LockoutState:
    now = timezone.now()
    locked_until = None

    for key in build_throttle_keys(request, username):
        throttle = LoginThrottle.objects.filter(key=key).first()
        if throttle and throttle.locked_until and throttle.locked_until > now:
            if locked_until is None or throttle.locked_until > locked_until:
                locked_until = throttle.locked_until

    return LockoutState(
        is_locked=locked_until is not None,
        locked_until=locked_until,
    )


def register_failed_login_attempt(request, username: str) -> None:
    now = timezone.now()
    window = timedelta(seconds=settings.PANEL_LOGIN_FAILURE_WINDOW_SECONDS)
    lockout = timedelta(seconds=settings.PANEL_LOGIN_LOCKOUT_SECONDS)

    for key in build_throttle_keys(request, username):
        throttle, _ = LoginThrottle.objects.get_or_create(
            key=key,
            defaults={
                "failure_count": 0,
                "first_failure_at": now,
                "last_failure_at": now,
            },
        )

        if now - throttle.first_failure_at > window:
            throttle.failure_count = 0
            throttle.first_failure_at = now
            throttle.locked_until = None

        throttle.failure_count += 1
        throttle.last_failure_at = now

        if throttle.failure_count >= settings.PANEL_LOGIN_FAILURE_LIMIT:
            throttle.locked_until = now + lockout

        throttle.save()


def clear_login_throttle(request, username: str) -> None:
    LoginThrottle.objects.filter(
        key__in=build_throttle_keys(request, username)
    ).delete()
