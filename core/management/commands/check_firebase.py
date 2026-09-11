from django.core.management.base import BaseCommand
from core.fcm_service import check_firebase_status


class Command(BaseCommand):
    help = "Diagnose and verify Firebase Admin SDK initialization and project configuration safely."

    def handle(self, *args, **options):
        self.stdout.write("Running Firebase diagnostic...")
        diag = check_firebase_status()

        if not diag.get("credentials_file_found"):
            self.stdout.write(self.style.ERROR(
                "✖ Credentials file not found at the configured FIREBASE_CREDENTIALS_PATH."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            "✔ Credentials file verified at FIREBASE_CREDENTIALS_PATH."
        ))

        if not diag.get("sdk_installed"):
            self.stdout.write(self.style.WARNING(
                "⚠ firebase-admin Python package is not yet installed in this environment. Run 'pip install firebase-admin'."
            ))
            return

        if diag.get("initialized"):
            proj = diag.get("project_id") or "Connected"
            self.stdout.write(self.style.SUCCESS(
                f"✔ Firebase Admin SDK initialized successfully! (Project ID: {proj})"
            ))
            self.stdout.write(self.style.NOTICE(
                "ℹ End-to-end FCM delivery requires a real mobile device FCM token. No fake tokens were used or stored."
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"✖ Firebase initialization failed: {diag.get('message')}"
            ))
