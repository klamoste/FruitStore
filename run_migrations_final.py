#!/usr/bin/env python
"""
Direct migration runner script
"""
import os
import sys
from pathlib import Path

# Add the fruit_store directory to Python path
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Setup environment and Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fruit_store.settings')

# Import and setup Django AFTER setting PYTHONPATH
import django
print(f"Django version: {django.get_version()}")
print(f"Project dir: {project_dir}")
print(f"Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test database
from django.db import connection
print("\nTesting database connection...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✓ Database connection successful")
    
    # Check current tables
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        tables = cursor.fetchall()
        if tables:
            print(f"✓ Found {len(tables)} existing tables: {[t[0] for t in tables]}")
        else:
            print("✓ Database is empty - ready for migrations")
except Exception as e:
    print(f"✗ Database test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run migrations
print("\nRunning migrations...")
from django.core.management import call_command
try:
    call_command('migrate', '--noinput', verbosity=2)
    print("✓ Migrations completed")
except Exception as e:
    print(f"✗ Migrations failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create sample data
print("\nCreating sample data...")
try:
    call_command('create_sample_data', verbosity=1)
    print("✓ Sample data created")
except Exception as e:
    print(f"Note: Sample data creation skipped: {e}")

print("\n✅ All done!")
