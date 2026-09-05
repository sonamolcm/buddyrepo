# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import Category


INITIAL_CATEGORIES = [
    {"name": "Teacher", "description": "Educator, School/College Teacher, Professor, or Tutor"},
    {"name": "Student", "description": "School, College, or University Student"},
    {"name": "Doctor", "description": "Physician, Medical Specialist, Surgeon, or Clinic Practitioner"},
    {"name": "Engineer", "description": "Civil, Mechanical, Electrical, Chemical, or Industrial Engineer"},
    {"name": "Lawyer", "description": "Advocate, Attorney, Legal Advisor, or Corporate Counsel"},
    {"name": "Business", "description": "Business Owner, Startup Founder, Manager, or Consultant"},
    {"name": "Artist", "description": "Writer, Musician, Content Creator, Painter, or Designer"},
    {"name": "Chef", "description": "Professional Chef, Cook, Baker, or Culinary Specialist"},
    {"name": "Nurse", "description": "Registered Nurse, Healthcare Assistant, or Medical Caregiver"},
    {"name": "Software Developer", "description": "Software Developer, Programmer, QA, Cloud, or IT Specialist"},
    {"name": "Accountant", "description": "Chartered Accountant, Auditor, Bookkeeper, or Financial Analyst"},
    {"name": "Technician", "description": "Hardware, Electrical, Mechanical, or IT Technician"},
    {"name": "Other", "description": "Other profession or independent specialist"},
]


class Command(BaseCommand):
    help = "Seed initial list of profession categories for Callers into the database"

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        for item in INITIAL_CATEGORIES:
            obj, created = Category.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item.get("description", ""),
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created category: {item['name']}"))
            else:
                existing_count += 1
                # If it was inactive, reactivate it if needed
                if not obj.is_active:
                    obj.is_active = True
                    obj.save(update_fields=['is_active', 'updated_at'])
                    self.stdout.write(self.style.WARNING(f"Re-activated category: {item['name']}"))
                else:
                    self.stdout.write(f"Already exists: {item['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Seeded {created_count} new categories ({existing_count} already existed)."
            )
        )
