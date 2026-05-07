import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR / "fruit_store"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from env_loader import load_env_file

load_env_file(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

app = get_wsgi_application()
