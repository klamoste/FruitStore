#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fruit_store.settings')
django.setup()

# Test database connection
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)

# Run migrations
from django.core.management import call_command
try:
    call_command('migrate', verbosity=2)
    print("✓ Migrations completed successfully")
except Exception as e:
    print(f"✗ Migrations failed: {e}")
    sys.exit(1)

# Run sample data creation
try:
    call_command('create_sample_data', verbosity=2)
    print("✓ Sample data created successfully")
except Exception as e:
    print(f"✗ Sample data creation failed: {e}")
    sys.exit(1)
