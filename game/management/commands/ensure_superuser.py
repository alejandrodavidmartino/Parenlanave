import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Create the admin user from the DJANGO_SUPERUSER_* environment variables, "
        "unless it already exists. Safe to run on every deploy."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        if not username:
            raise CommandError("Set DJANGO_SUPERUSER_USERNAME (and _EMAIL, _PASSWORD).")

        # Plain `createsuperuser --noinput` fails when the user exists, which would break
        # every deploy after the first one. Checking first makes the command repeatable,
        # and an existing user's password is never touched.
        if get_user_model().objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists.")
            return

        # Django's own command reads the email and password from the same variables
        # and runs the password validators.
        call_command("createsuperuser", interactive=False)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
