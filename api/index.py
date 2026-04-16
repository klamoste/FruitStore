import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent / "fruit_store"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from wsgi import application

app = application
