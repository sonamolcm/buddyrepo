# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import User, ListenerProfile, Category, Wallet
from core.sample_data import SAMPLE_CATEGORY_LISTENERS, DEFAULT_LISTENER_CATEGORY_MAP
from core.management.commands.seed_categories import INITIAL_CATEGORIES


DEFAULT_LISTENERS = [
    {
        "username": "LISTENER_001",
        "name": "Sarah Jenkins",
        "gender": "Female",
        "language": "English",
        "interests": ["Friendly Chat", "Emotional Support", "Daily Venting"],
        "password": "ListenerPass123!",
        "category": "Teacher"
    },
    {
        "username": "LISTENER_101",
        "name": "Alex Rivera",
        "gender": "Male",
        "language": "English",
        "interests": ["Career & Motivation", "Friendly Chat", "Self Improvement"],
        "password": "ListenerPass123!",
        "category": "Business"
    },
    {
        "username": "LISTENER_102",
        "name": "Priya Sharma",
        "gender": "Female",
        "language": "English, Hindi",
        "interests": ["Stress & Anxiety", "Daily Venting", "Family & Relationships"],
        "password": "ListenerPass123!",
        "category": "Student"
    },
    {
        "username": "LISTENER_103",
        "name": "Sam Taylor",
        "gender": "Other",
        "language": "English",
        "interests": ["Active Listening", "Relationships", "Casual Conversation"],
        "password": "ListenerPass123!",
        "category": "Artist"
    },
    {
        "username": "LISTENER_104",
        "name": "Emma Watson",
        "gender": "Female",
        "language": "English",
        "interests": ["Mindfulness", "Life Advice", "Friendship"],
        "password": "ListenerPass123!",
        "category": "Engineer"
    },
    {
        "username": "LISTENER_105",
        "name": "David Miller",
        "gender": "Male",
        "language": "English",
        "interests": ["Academic & Studies", "Daily Support", "Motivation"],
        "password": "ListenerPass123!",
        "category": "Software Developer"
    },
]


class Command(BaseCommand):
    help = "Sets up and populates complete Listener profiles across all categories (Teacher, Student, Doctor, Engineer, etc.)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset passwords of listeners to default passwords'
        )

    def handle(self, *args, **options):
        reset_passwords = options.get('reset_passwords', False)

        # Step 0: Ensure categories exist
        self.stdout.write(self.style.NOTICE("📂 Step 0: Ensuring all Profession Categories exist..."))
        cat_map = {}
        for item in INITIAL_CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item.get("description", ""),
                    "is_active": True,
                }
            )
            if not cat.is_active:
                cat.is_active = True
                cat.save(update_fields=['is_active'])
            cat_map[item["name"].lower()] = cat

        self.stdout.write(self.style.SUCCESS(f"✔ Verified {len(cat_map)} active categories."))

        # Step 1: Auditing & Correcting Existing Listener Profiles
        self.stdout.write(self.style.NOTICE("\n🔍 Step 1: Auditing & Correcting Existing Listener Profiles..."))
        listener_users = list(
            User.objects.filter(role__in=['LISTENER', 'BUDDY']).distinct()
        )
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

            profile, _ = ListenerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'listener_id': user.username,
                    'name': user.first_name or user.username.replace('_', ' ').title(),
                    'language': 'English',
                    'gender': user.gender or 'Other',
                    'interests': ["Friendly Chat", "Active Listening", "Emotional Support"],
                    'is_available': True,
                    'is_on_duty': True,
                    'is_verified': True,
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
            if not profile.is_on_duty:
                profile.is_on_duty = True
                changed_prof = True
            if not profile.is_verified:
                profile.is_verified = True
                changed_prof = True

            if changed_prof:
                profile.save()

            Wallet.objects.get_or_create(user=user, defaults={'balance': 50})
            corrected_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Step 1 Complete: {corrected_count} existing listener profile(s) verified."))

        # Step 2: Ensuring Standard Test Listeners Exist with Category Assignments
        self.stdout.write(self.style.NOTICE("\n🚀 Step 2: Ensuring Standard Test Listeners (LISTENER_001, LISTENER_101-105)..."))
        for item in DEFAULT_LISTENERS:
            uname = item["username"]
            pwd = item["password"]
            cat_name = item.get("category") or DEFAULT_LISTENER_CATEGORY_MAP.get(uname)
            cat_obj = cat_map.get(cat_name.lower()) if cat_name else None

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
            if created or reset_passwords:
                user.set_password(pwd)
            user.role = 'LISTENER'
            user.first_name = item["name"]
            user.gender = item["gender"]
            user.is_active = True
            user.is_verified = True
            user.is_profile_completed = True
            user.save()

            prof, _ = ListenerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'listener_id': uname,
                    'name': item["name"],
                    'profession': cat_obj,
                    'gender': item["gender"],
                    'language': item["language"],
                    'interests': item["interests"],
                    'rate_per_second': 3,
                    'rating': 4.9,
                    'is_available': True,
                    'is_on_duty': True,
                    'is_verified': True,
                }
            )
            prof.listener_id = uname
            prof.name = item["name"]
            prof.gender = item["gender"]
            prof.language = item["language"]
            prof.interests = item["interests"]
            if cat_obj and not prof.profession:
                prof.profession = cat_obj
            prof.is_available = True
            prof.is_on_duty = True
            prof.is_verified = True
            prof.save()

            Wallet.objects.get_or_create(user=user, defaults={'balance': 50})
            self.stdout.write(self.style.SUCCESS(
                f"   ✔ {uname}: {prof.name} | Category: {cat_name} | Lang: {prof.language}"
            ))

        # Step 3: Populating Listeners for ALL Categories
        self.stdout.write(self.style.NOTICE("\n🌟 Step 3: Seeding Listeners for All Categories..."))
        total_category_listeners = 0

        for cat_name, listeners in SAMPLE_CATEGORY_LISTENERS.items():
            cat_obj = cat_map.get(cat_name.lower())
            if not cat_obj:
                cat_obj, _ = Category.objects.get_or_create(
                    name=cat_name,
                    defaults={"description": f"{cat_name} professionals and specialists", "is_active": True}
                )
                cat_map[cat_name.lower()] = cat_obj

            self.stdout.write(self.style.NOTICE(f"\n   --- [{cat_name}] ---"))
            for item in listeners:
                uname = item["username"]
                pwd = item.get("password", "ListenerPass123!")

                u, created = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        'role': 'LISTENER',
                        'first_name': item["name"],
                        'gender': item.get("gender", "Other"),
                        'is_active': True,
                        'is_verified': True,
                        'is_profile_completed': True,
                    }
                )
                if created or reset_passwords or not u.has_usable_password():
                    u.set_password(pwd)
                u.role = 'LISTENER'
                u.first_name = item["name"]
                u.gender = item.get("gender", "Other")
                u.is_active = True
                u.is_verified = True
                u.is_profile_completed = True
                u.save()

                rate_sec = item.get("rate_per_second", 3)
                prof, _ = ListenerProfile.objects.get_or_create(
                    user=u,
                    defaults={
                        'listener_id': uname,
                        'name': item["name"],
                        'profession': cat_obj,
                        'gender': item.get("gender", "Other"),
                        'language': item.get("language", "English"),
                        'bio': item.get("bio", ""),
                        'interests': item.get("interests", []),
                        'rate_per_second': rate_sec,
                        'rating': item.get("rating", 4.9),
                        'is_available': True,
                        'is_on_duty': True,
                        'is_verified': True,
                    }
                )
                prof.listener_id = uname
                prof.name = item["name"]
                prof.profession = cat_obj
                prof.gender = item.get("gender", "Other")
                prof.language = item.get("language", "English")
                prof.bio = item.get("bio", "")
                prof.interests = item.get("interests", [])
                prof.rate_per_second = rate_sec
                prof.rating = item.get("rating", 4.9)
                prof.is_available = True
                prof.is_on_duty = True
                prof.is_verified = True
                prof.save()

                Wallet.objects.get_or_create(user=u, defaults={'balance': 50})
                total_category_listeners += 1

                self.stdout.write(self.style.SUCCESS(
                    f"     ✔ {uname}: {prof.name} ({prof.gender}) | Rate: {rate_sec * 60} coins/min | Rating: {prof.rating}"
                ))

        # Final Summary
        self.stdout.write(self.style.NOTICE("\n📊 Category Listener Count Summary:"))
        for cat in Category.objects.filter(is_active=True).order_by('name'):
            count = User.objects.filter(
                Q(listener_profile__profession=cat) | Q(buddy_profile__profession=cat),
                is_active=True
            ).distinct().count()
            self.stdout.write(f"   • {cat.name.ljust(22)}: {count} listener(s)")

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Successfully seeded and verified listeners across all categories! ({total_category_listeners} category listeners ready)"
        ))
