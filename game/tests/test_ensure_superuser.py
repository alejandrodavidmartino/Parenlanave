import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()


@pytest.fixture
def superuser_env(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "captain")
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "captain@example.com")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "a-long-test-password")


@pytest.mark.django_db
def test_ensure_superuser_creates_it_from_the_environment(superuser_env):
    call_command("ensure_superuser")

    user = User.objects.get(username="captain")
    assert user.is_superuser
    assert user.check_password("a-long-test-password")


@pytest.mark.django_db
def test_ensure_superuser_twice_does_not_fail_or_change_the_password(superuser_env, monkeypatch):
    call_command("ensure_superuser")
    # A later deploy with a different password must not overwrite the one in use.
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "another-password")

    call_command("ensure_superuser")

    assert User.objects.filter(username="captain").count() == 1
    assert User.objects.get(username="captain").check_password("a-long-test-password")


@pytest.mark.django_db
def test_ensure_superuser_without_username_is_an_error(monkeypatch):
    monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)

    with pytest.raises(CommandError):
        call_command("ensure_superuser")
