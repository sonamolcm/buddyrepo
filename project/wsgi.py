"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
import sys

path = '/home/buddy2026/buddy'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'


# pyrefly: ignore [missing-import]
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

