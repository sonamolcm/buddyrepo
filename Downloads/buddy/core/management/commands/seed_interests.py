# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import Interest


class Command(BaseCommand):
    help = "Seed initial list of user interests into the database"

    def handle(self, *args, **options):
        interests_data = [
            {"name": "Nature", "icon": "🌿"},
            {"name": "Sport", "icon": "⚽"},
            {"name": "Book", "icon": "📚"},
            {"name": "Art", "icon": "🎨"},
            {"name": "Design", "icon": "✨"},
            {"name": "Photography", "icon": "📷"},
            {"name": "Travelling", "icon": "✈️"},
            {"name": "Coffee Lover", "icon": "☕"},
        ]

        count = 0
        for item in interests_data:
            obj, created = Interest.objects.get_or_create(
                name=item["name"],
                defaults={"icon": item["icon"]}
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Created interest: {item['icon']} {item['name']}"))
            else:
                self.stdout.write(f"Already exists: {item['icon']} {item['name']}")

        self.stdout.write(self.style.SUCCESS(f"\nDone! Seeded {count} new interests."))
