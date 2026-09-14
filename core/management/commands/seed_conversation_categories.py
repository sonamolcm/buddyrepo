# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import ConversationCategory

CONVERSATION_CATEGORIES_DATA = [
    {
        "name": "Just Talk",
        "emoji": "❤️",
        "tagline": "I need someone to talk to.",
        "order": 1,
    },
    {
        "name": "Friendly Conversation",
        "emoji": "😊",
        "tagline": "Let's have a pleasant conversation.",
        "order": 2,
    },
    {
        "name": "Advice",
        "emoji": "🧠",
        "tagline": "I need another person's perspective.",
        "order": 3,
    },
    {
        "name": "Career",
        "emoji": "💼",
        "tagline": "Talk to someone experienced in my field.",
        "order": 4,
    },
    {
        "name": "Travel",
        "emoji": "🌍",
        "tagline": "Talk to someone who knows this place.",
        "order": 5,
    },
    {
        "name": "Elder Companion",
        "emoji": "👴",
        "tagline": "Someone to talk to regularly.",
        "order": 6,
    },
    {
        "name": "Student Companion",
        "emoji": "🎓",
        "tagline": "Talk about studies, college and life.",
        "order": 7,
    },
    {
        "name": "Language",
        "emoji": "🗣️",
        "tagline": "Practice English / Hindi / Malayalam / etc.",
        "order": 8,
    },
    {
        "name": "Casual",
        "emoji": "☕",
        "tagline": "Nothing serious — just chat.",
        "order": 9,
    },
]


class Command(BaseCommand):
    help = "Seeds the 9 official conversation categories for GabbyTalk (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for item in CONVERSATION_CATEGORIES_DATA:
            cat, created = ConversationCategory.objects.update_or_create(
                name=item["name"],
                defaults={
                    "emoji": item["emoji"],
                    "tagline": item["tagline"],
                    "order": item["order"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {cat}"))
            else:
                updated_count += 1
                self.stdout.write(f"Updated / verified: {cat}")

        total_active = ConversationCategory.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Seeded conversation categories ({created_count} created, {updated_count} verified). Total active: {total_active}."
            )
        )
