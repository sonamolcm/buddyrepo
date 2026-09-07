# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import User, ListenerProfile


DEFAULT_LISTENERS = [
    {
        "username": "LISTENER_001",
        "name": "Sarah Jenkins",
        "gender": "Female",
        "language": "English",
        "interests": ["Friendly Chat", "Emotional Support", "Daily Venting"],
        "password": "ListenerPass123!"
    },
    {
        "username": "LISTENER_101",
        "name": "Alex Rivera",
        "gender": "Male",
        "language": "English",
        "interests": ["Career & Motivation", "Friendly Chat", "Self Improvement"],
        "password": "ListenerPass123!"
    },
    {
        "username": "LISTENER_102",
        "name": "Priya Sharma",
        "gender": "Female",
        "language": "English, Hindi",
        "interests": ["Stress & Anxiety", "Daily Venting", "Family & Relationships"],
        "password": "ListenerPass123!"
    },
    {
        "username": "LISTENER_103",
        "name": "Sam Taylor",
        "gender": "Other",
        "language": "English",
        "interests": ["Active Listening", "Relationships", "Casual Conversation"],
        "password": "ListenerPass123!"
    },
    {
        "username": "LISTENER_104",
        "name": "Emma Watson",
        "gender": "Female",
        "language": "English",
        "interests": ["Mindfulness", "Life Advice", "Friendship"],
        "password": "ListenerPass123!"
    },
    {
        "username": "LISTENER_105",
        "name": "David Miller",
        "gender": "Male",
        "language": "English",
        "interests": ["Academic & Studies", "Daily Support", "Motivation"],
        "password": "ListenerPass123!"
    },
]


class Command(BaseCommand):
    help = "Corrects all existing Listener accounts and sets up complete Listener profiles with defaults."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset passwords of standard test accounts (LISTENER_*) to ListenerPass123!'
        )

    def handle(self, *args, **options):
        reset_passwords = options.get('reset_passwords', False)

        self.stdout.write(self.style.NOTICE("🔍 Step 1: Auditing & Correcting Existing Listener Profiles..."))

        # Find all users that are listeners or have a listener profile
        listener_users = list(
            User.objects.filter(role__in=['LISTENER', 'BUDDY']).distinct()
        )
        # Also grab users who have a ListenerProfile but whose role was not LISTENER
        for prof in ListenerProfile.objects.select_related('user').all():
            if prof.user not in listener_users:
                listener_users.append(prof.user)

        corrected_count = 0
        for user in listener_users:
            changed_user = False
            if user.role != 'LISTENER':
                user.role = 'LISTENER'
                changed_user = True
            if not user.is_active:
                user.is_active = True
                changed_user = True
            if not user.is_verified:
                user.is_verified = True
                changed_user = True
            if not user.is_profile_completed:
                user.is_profile_completed = True
                changed_user = True
            if changed_user:
                user.save()

            profile, created = ListenerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'listener_id': user.username,
                    'name': user.first_name or user.username.replace('_', ' ').title(),
                    'language': 'English',
                    'gender': user.gender or 'Other',
                    'interests': ["Friendly Chat", "Active Listening", "Emotional Support"],
                    'is_available': True,
                }
            )

            changed_prof = False
            if not profile.listener_id or profile.listener_id != user.username:
                profile.listener_id = user.username
                changed_prof = True
            if not profile.name:
                profile.name = user.first_name or user.username.replace('_', ' ').title()
                changed_prof = True
            if not profile.language:
                profile.language = 'English'
                changed_prof = True
            if not profile.gender:
                profile.gender = user.gender or 'Other'
                changed_prof = True
            if not profile.interests:
                profile.interests = ["Friendly Chat", "Active Listening", "Emotional Support"]
                changed_prof = True
            if not profile.is_available:
                profile.is_available = True
                changed_prof = True

            if changed_prof:
                profile.save()

            corrected_count += 1
            self.stdout.write(f"   ✔ Verified: [{profile.listener_id}] {profile.name} (Active: {user.is_active}, Available: {profile.is_available})")

        self.stdout.write(self.style.SUCCESS(f"✅ Step 1 Complete: {corrected_count} existing listener profile(s) verified & completed."))

        self.stdout.write(self.style.NOTICE("\n🚀 Step 2: Ensuring Standard Test Listeners Exist (LISTENER_001, LISTENER_101-105)..."))
        created_test_count = 0
        for item in DEFAULT_LISTENERS:
            uname = item["username"]
            pwd = item["password"]
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'role': 'LISTENER',
                    'first_name': item["name"],
                    'gender': item["gender"],
                    'is_active': True,
                    'is_verified': True,
                    'is_profile_completed': True,
                }
            )
            if created:
                user.set_password(pwd)
                user.save()
                created_test_count += 1
                status_str = "Created New"
            else:
                status_str = "Updated Existing"
                if reset_passwords:
                    user.set_password(pwd)
                user.role = 'LISTENER'
                user.is_active = True
                user.is_verified = True
                user.is_profile_completed = True
                user.save()

            prof, _ = ListenerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'listener_id': uname,
                    'name': item["name"],
                    'gender': item["gender"],
                    'language': item["language"],
                    'interests': item["interests"],
                    'is_available': True,
                }
            )
            prof.listener_id = uname
            if not prof.name:
                prof.name = item["name"]
            if not prof.gender:
                prof.gender = item["gender"]
            if not prof.language:
                prof.language = item["language"]
            if not prof.interests:
                prof.interests = item["interests"]
            prof.is_available = True
            prof.save()

            self.stdout.write(self.style.SUCCESS(
                f"   ✔ {status_str}: {uname} | Name: {prof.name} | Lang: {prof.language} | Pwd: {pwd}"
            ))

        self.stdout.write(self.style.SUCCESS("\n🎉 All Listener profiles are 100% complete, verified, and ready!"))
