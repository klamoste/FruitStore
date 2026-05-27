"""
ASGI config for fruit_store project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application
from env_loader import load_env_file

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

load_env_file(PROJECT_DIR.parent)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = get_asgi_application()
