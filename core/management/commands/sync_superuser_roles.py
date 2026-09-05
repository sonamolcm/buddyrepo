# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Ensures all Django superusers have role="ADMIN" and is_staff=True, and removes accidental CallerProfile rows.'

    def handle(self, *args, **options):
        superusers = User.objects.filter(is_superuser=True)
        if not superusers.exists():
            self.stdout.write(self.style.WARNING("No superusers found in the database."))
            return

        updated_count = 0
        for user in superusers:
            needs_save = False
            if user.role != 'ADMIN':
                self.stdout.write(f"Updating user '{user.username}': role changed from '{user.role}' to 'ADMIN'")
                user.role = 'ADMIN'
                needs_save = True

            if not user.is_staff:
                self.stdout.write(f"Updating user '{user.username}': is_staff set to True")
                user.is_staff = True
                needs_save = True

            if needs_save:
                user.save()
                updated_count += 1

            # Clean up accidental CallerProfile created for superuser
            if hasattr(user, 'caller_profile'):
                user.caller_profile.delete()
                self.stdout.write(self.style.SUCCESS(f"Cleaned up redundant CallerProfile for '{user.username}'"))

        self.stdout.write(self.style.SUCCESS(f"Completed! {updated_count} superuser(s) updated."))
