"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

pa_path = '/home/buddy2026/buddy'
if os.path.exists(pa_path) and pa_path not in sys.path:
    sys.path.insert(0, pa_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# pyrefly: ignore [missing-import]
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

