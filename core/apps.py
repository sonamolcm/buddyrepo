# pyrefly: ignore [missing-import]
from django.apps import AppConfig


class BuddieConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'