#!/usr/bin/env python
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent / "fruit_store"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from env_loader import load_env_file

load_env_file(Path(__file__).resolve().parent)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.management import execute_from_command_line


if __name__ == "__main__":
    execute_from_command_line(sys.argv)
