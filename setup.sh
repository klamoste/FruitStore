#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "Fruit Store - Quick Start Setup"
echo "===================================="
echo

cd "$PROJECT_DIR"

echo "Step 1: Installing dependencies..."
python -m pip install -r "$PROJECT_DIR/requirements.txt"
echo "Dependencies installed"
echo

echo "Step 2: Running migrations..."
python manage.py migrate --noinput
echo "Database initialized"
echo

echo "Step 3: Creating sample data..."
python manage.py create_sample_data
echo "Sample categories and products created"
echo

echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput
echo "Static files collected"
echo

echo "===================================="
echo "Setup Complete!"
echo
echo "Test Credentials:"
echo "  Admin:    admin / admin123"
echo "  Customer: testuser / testuser123"
echo
echo "To start the server, run:"
echo "  cd \"$PROJECT_DIR\""
echo "  python manage.py runserver"
echo
echo "Then visit: http://127.0.0.1:8000/"
echo "Admin panel: http://127.0.0.1:8000/admin/"
echo
echo "===================================="
