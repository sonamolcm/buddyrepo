# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Creates or updates a default Administrator account for the Admin Panel.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='buddy', help='Admin Username')
        parser.add_argument('--password', type=str, default='Buddy@12345', help='Admin Password')
        parser.add_argument('--email', type=str, default='admin@buddy.local', help='Admin Email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        user.role = 'ADMIN'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated password/permissions for"
        self.stdout.write(self.style.SUCCESS(
            f"✅ {action} Admin user: Username='{username}' | Password='{password}'"
        ))
