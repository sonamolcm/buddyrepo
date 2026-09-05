# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import User, ListenerProfile


class Command(BaseCommand):
    help = 'Creates a Listener account with username, password, and language only (no name or gender).'

    def add_arguments(self, parser):
        parser.add_argument('--username', '--listener_id', dest='username', type=str, default='LISTENER_001', help='Listener Username / ID')
        parser.add_argument('--password', type=str, default='ListenerPass123!', help='Listener password')
        parser.add_argument('--language', type=str, default='English', help='Spoken languages')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        language = options['language']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'role': 'LISTENER',
                'is_active': True,
                'is_verified': True
            }
        )
        user.role = 'LISTENER'
        user.set_password(password)  # Secure PBKDF2 hashing
        user.is_active = True
        user.save()

        profile, _ = ListenerProfile.objects.get_or_create(
            user=user,
            defaults={
                'listener_id': username,
                'language': language,
                'is_available': True
            }
        )
        profile.listener_id = username
        profile.language = language
        profile.is_available = True
        profile.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"✅ {action} Listener: Username={username} | Password={password} | Language={language}"
        ))

