# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import User, ListenerProfile


class Command(BaseCommand):
    help = 'Creates a Listener account with username, password, and language only (no name or gender).'

    def add_arguments(self, parser):
        parser.add_argument('--username', '--listener_id', dest='username', type=str, default='LISTENER_001', help='Listener Username / ID')
        parser.add_argument('--password', type=str, default='ListenerPass123!', help='Listener password')
        parser.add_argument('--name', type=str, default='', help='Listener display name')
        parser.add_argument('--language', type=str, default='English', help='Spoken languages')
        parser.add_argument('--gender', type=str, default='Other', help='Gender')
        parser.add_argument('--interests', type=str, default='Friendly Chat,Emotional Support', help='Comma-separated interests')

    def handle(self, *args, **options):
        username = options['username'].strip()
        password = options['password']
        name = (options['name'] or username.replace('_', ' ').title()).strip()
        language = options['language'].strip()
        gender = options['gender'].strip()
        interests = [i.strip() for i in options['interests'].split(',') if i.strip()]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'role': 'LISTENER',
                'first_name': name,
                'gender': gender,
                'is_active': True,
                'is_verified': True,
                'is_profile_completed': True
            }
        )
        user.role = 'LISTENER'
        user.first_name = name
        user.gender = gender
        user.set_password(password)  # Secure PBKDF2 hashing
        user.is_active = True
        user.is_verified = True
        user.is_profile_completed = True
        user.save()

        profile, _ = ListenerProfile.objects.get_or_create(
            user=user,
            defaults={
                'listener_id': username,
                'name': name,
                'gender': gender,
                'language': language,
                'interests': interests,
                'is_available': True
            }
        )
        profile.listener_id = username
        profile.name = name
        profile.gender = gender
        profile.language = language
        profile.interests = interests
        profile.is_available = True
        profile.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"✅ {action} Listener: Username={username} | Name={name} | Language={language} | Available={profile.is_available}"
        ))

